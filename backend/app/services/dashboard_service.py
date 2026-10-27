"""
dashboard_service.py

Runs batch analysis over an uploaded dataset and aggregates the results into
dashboard-ready statistics.

STORAGE: CXIQ persists datasets/reviews in PostgreSQL when a database is
configured and reachable (see app/db.py, app/services/repository.py). If not,
it transparently falls back to the original in-memory dict — every feature
still works, it just won't survive a restart. `db.db_available()` is checked
once at startup and cached here; all read/write helpers below branch on it.

This dual-mode design means the aggregation logic in this file, plus
intelligence_service.py and trend_service.py, is IDENTICAL either way — both
storage paths hand back plain dicts in the same shape.

Dataset lifecycle:
  1. POST /api/analyze/batch uploads + validates a CSV/Excel file, analyzes
     every row through pipeline_service.analyze_review, and stores the
     resulting analyzed rows (database or in-memory) keyed by a generated
     dataset_id.
  2. GET /api/dashboard?dataset_id=... aggregates those analyzed rows into
     KPI cards, charts, aspect intelligence, emotion analytics, issue
     intelligence, trend analysis, and business insights/recommendations.
  3. GET /api/analyze/batch/{dataset_id}/download streams the analyzed rows
     back out as a CSV.
"""
from __future__ import annotations
import io
import os
import uuid
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.services.pipeline_service import analyze_review
from app.services.cxscore_service import compute_cx_score
from app.services.trend_service import analyze_trends
from app.services.insight_service import dashboard_insights
from app.services.intelligence_service import (
    compute_customer_voice, compute_issue_radar, compute_decision_center,
    compute_emotion_by_aspect, compute_language_breakdown,
)
from app.utils.file_utils import detect_optional_columns, load_dataframe, detect_review_column
from app.db import db_available
from app.services import repository

# Fallback in-memory dataset cache, used only when no database is configured
# or reachable: dataset_id -> {rows, meta}
_DATASETS: Dict[str, Dict] = {}

DEFAULT_DATASET_ID = "sample"

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_CSV_PATH = os.path.join(_BASE_DIR, "data", "sample_customer_reviews.csv")


def load_sample_dataframe() -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Reads the bundled sample CSV and detects its review column. Shared by
    the startup preload (main.py) and POST /api/datasets/sample, so there's
    a single source of truth for "how do we load the sample dataset"."""
    if not os.path.exists(SAMPLE_CSV_PATH):
        return None, None
    with open(SAMPLE_CSV_PATH, "rb") as f:
        content = f.read()
    df = load_dataframe("sample_customer_reviews.csv", content)
    review_col = detect_review_column(df)
    return df, review_col


def _row_to_record(raw_row: Dict, analysis: Dict) -> Dict:
    neg_aspects = [a["aspect"] for a in analysis["aspects"] if a["sentiment"] == "negative"]
    pos_aspects = [a["aspect"] for a in analysis["aspects"] if a["sentiment"] == "positive"]
    return {
        "review": analysis["original_text"],
        "analyzed_text": analysis["analyzed_text"],
        "language": analysis["detected_language"],
        "language_code": analysis["language_code"],
        "translation_status": analysis["translation_status"],
        "overall_sentiment": analysis["overall_sentiment"]["label"],
        "sentiment_confidence": analysis["overall_sentiment"]["confidence"],
        "emotion": analysis["emotion"]["label"],
        "emotion_confidence": analysis["emotion"]["confidence"],
        "priority": analysis["priority"]["label"],
        "priority_score": analysis["priority"]["score"],
        "reliable": analysis["reliable"],
        "detected_aspects": [a["aspect"] for a in analysis["aspects"]],
        "aspect_sentiments": {a["aspect"]: a["sentiment"] for a in analysis["aspects"]},
        "negative_aspects": neg_aspects,
        "positive_aspects": pos_aspects,
        "rating": raw_row.get("rating"),
        "date": raw_row.get("date"),
        "product": raw_row.get("product"),
        "category": raw_row.get("category"),
        "customer_id": raw_row.get("customer_id"),
    }


def process_batch(
    df: pd.DataFrame,
    review_column: str,
    domain: str,
    dataset_id: Optional[str] = None,
    max_rows: int = 20000,
    max_workers: int = 8,
    filename: Optional[str] = None,
    user_id: Optional[int] = None,
    is_sample: bool = False,
) -> Dict:
    """
    Analyzes every row through the same pipeline used for single-feedback
    analysis. Rows are processed concurrently (bounded thread pool) rather
    than one at a time: most of the per-row cost for non-English text is
    waiting on the translation call (network I/O), so concurrency is what
    keeps a large, multilingual batch from taking minutes instead of
    seconds. Pure-English batches see little difference either way since
    there's no network wait to overlap.
    """
    dataset_id = dataset_id or str(uuid.uuid4())
    optional_cols = detect_optional_columns(df)

    df = df.head(max_rows).copy()
    df[review_column] = df[review_column].astype(str)

    work_items = []
    skipped = 0
    for _, row in df.iterrows():
        text = str(row.get(review_column, "")).strip()
        if not text or text.lower() == "nan" or len(text) < 2:
            skipped += 1
            continue
        raw_extra = {
            "rating": row.get(optional_cols["rating"]) if optional_cols["rating"] else None,
            "date": row.get(optional_cols["date"]) if optional_cols["date"] else None,
            "product": row.get(optional_cols["product"]) if optional_cols["product"] else None,
            "category": row.get(optional_cols["category"]) if optional_cols["category"] else None,
            "customer_id": row.get(optional_cols["customer_id"]) if optional_cols["customer_id"] else None,
        }
        try:
            rating_val = float(raw_extra["rating"]) if raw_extra["rating"] not in (None, "") and str(raw_extra["rating"]).lower() != "nan" else None
        except (TypeError, ValueError):
            rating_val = None
        work_items.append((text, raw_extra, rating_val))

    def _process_one(item):
        text, raw_extra, rating_val = item
        analysis = analyze_review(text, domain=domain, rating=rating_val)
        return _row_to_record(raw_extra, analysis)

    analyzed_rows: List[Dict] = []
    if work_items:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            analyzed_rows = list(executor.map(_process_one, work_items))

    if db_available():
        repository.create_dataset(
            dataset_id=dataset_id, domain=domain, review_column=review_column,
            columns_detected=optional_cols, total_records=int(len(df)),
            filename=filename, user_id=user_id, is_sample=is_sample,
        )
        if analyzed_rows:
            repository.bulk_insert_reviews(dataset_id, analyzed_rows)
    else:
        _DATASETS[dataset_id] = {
            "rows": analyzed_rows,
            "domain": domain,
            "review_column": review_column,
            "columns_detected": optional_cols,
            "total_records": int(len(df)),
        }

    return {
        "dataset_id": dataset_id,
        "total_records": int(len(df)),
        "processed_records": len(analyzed_rows),
        "skipped_records": skipped,
        "review_column": review_column,
        "columns_detected": optional_cols,
        "download_ready": True,
    }


def get_dataset(dataset_id: str) -> Optional[Dict]:
    if db_available():
        rows = repository.get_dataset_rows(dataset_id)

        if rows is None:
            return None

        meta = repository.get_dataset_meta(dataset_id)

        return {
            "rows": rows,
            "domain": (
                meta.get("domain", "other")
                if meta
                else "other"
            ),
        }

    return _DATASETS.get(dataset_id)


def get_available_languages(dataset_id: str) -> List[str]:
    dataset = get_dataset(dataset_id)
    if not dataset:
        return []
    return sorted({r["language"] for r in dataset["rows"]})


def _empty_dashboard(
    dataset_id: str, total_reviews: int, available_languages: List[str],
    language_breakdown: List[Dict], message: str,
    translation_health: Optional[Dict] = None,
) -> Dict:
    """A degraded-but-still-fully-shaped dashboard payload, used whenever
    there's nothing analyzable to aggregate (empty selection, or every row
    in the selection failed translation). BUG FIX: this used to return a
    partial dict (missing `kpis`, `sentiment_distribution`, etc.), which
    crashed the frontend with a blank error screen the moment someone
    picked a language filter where every review happened to be
    translation-unreliable — every field the Dashboard page reads is
    included here (zeroed out) so it always renders a clean empty state
    instead."""
    return {
        "dataset_id": dataset_id,
        "total_reviews": total_reviews,
        "available_languages": available_languages,
        "active_language_filter": "All",
        "message": message,
        "kpis": {
            "reviews_analyzed": 0, "positive_pct": 0, "neutral_pct": 0, "negative_pct": 0,
            "cx_score": 0, "cx_label": "Needs Attention", "high_critical_issues": 0,
        },
        "cx_score_components": {},
        "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
        "sentiment_by_category": None,
        "aspect_summary": [],
        "emotion_distribution": {},
        "priority_distribution": {"Low": 0, "Medium": 0, "High": 0, "Critical": 0},
        "recurring_problems": [],
        "trends": {"available": False, "message": message},
        "business_insights": [],
        "recommendations": [],
        "avg_rating": None,
        "customer_voice": [],
        "issue_radar": [],
        "decision_center": [],
        "language_breakdown": language_breakdown,
        "translation_health": translation_health or {
            "non_english_reviews": 0, "translated_successfully": 0,
            "success_rate_pct": None, "unreliable_reviews": 0,
        },
    }


def build_dashboard(dataset_id: str, language: Optional[str] = None) -> Dict:
    dataset = get_dataset(dataset_id)
    if not dataset:
        return None

    all_rows = dataset["rows"]
    domain = dataset.get("domain", "other")
    # Language CX Comparison always reflects the FULL dataset regardless of
    # the active filter, since its purpose is comparing languages against
    # each other — filtering it down to one language would make it trivial.
    language_breakdown = compute_language_breakdown(all_rows) if all_rows else []
    available_languages = sorted({r["language"] for r in all_rows})

    rows = all_rows
    if language and language.lower() != "all":
        rows = [r for r in all_rows if r["language"] == language]

    total = len(rows)
    if total == 0:
        return _empty_dashboard(
            dataset_id, total_reviews=0, available_languages=available_languages,
            language_breakdown=language_breakdown,
            message="No analyzable reviews found for this selection.",
        )

    # HONEST AGGREGATION: rows where translation failed and couldn't be
    # reliably analyzed (see pipeline_service.analyze_review) are excluded
    # from every statistic below, so a batch of failed translations can
    # never dilute or skew real sentiment/aspect/CX signal with placeholder
    # neutral values. They're still counted in `total_reviews` (something
    # was uploaded and attempted) and surfaced separately via
    # `translation_health`, never silently folded into the "real" numbers.
    analyzable_rows = [r for r in rows if r.get("reliable", True)]
    if not analyzable_rows:
        non_english_rows = [r for r in rows if r.get("language_code") not in (None, "en")]
        return _empty_dashboard(
            dataset_id, total_reviews=total, available_languages=available_languages,
            language_breakdown=language_breakdown,
            message="None of the reviews in this selection could be reliably analyzed "
                    "(translation was unavailable for all of them). See translation_health for details.",
            translation_health={
                "non_english_reviews": len(non_english_rows),
                "translated_successfully": 0,
                "success_rate_pct": 0.0 if non_english_rows else None,
                "unreliable_reviews": len(rows),
            },
        )

    sentiment_counts = Counter(r["overall_sentiment"] for r in analyzable_rows)
    emotion_counts = Counter(r["emotion"] for r in analyzable_rows)
    priority_counts = Counter(r["priority"] for r in analyzable_rows)

    # aspect intelligence
    aspect_sentiment_tally: Dict[str, Counter] = defaultdict(Counter)
    for r in analyzable_rows:
        for aspect, sentiment in r["aspect_sentiments"].items():
            aspect_sentiment_tally[aspect][sentiment] += 1

    aspect_summary = []
    aspect_sentiment_counts_global = Counter()
    for aspect, tally in aspect_sentiment_tally.items():
        mentions = sum(tally.values())
        positive_ratio = tally.get("positive", 0) / mentions if mentions else 0
        aspect_summary.append({
            "aspect": aspect,
            "mentions": mentions,
            "positive": tally.get("positive", 0),
            "neutral": tally.get("neutral", 0),
            "negative": tally.get("negative", 0),
            "positive_ratio": round(positive_ratio, 3),
        })
        for k, v in tally.items():
            aspect_sentiment_counts_global[k] += v
    aspect_summary.sort(key=lambda a: -a["mentions"])

    # rating average, if present
    ratings = [float(r["rating"]) for r in analyzable_rows if r.get("rating") not in (None, "") and str(r.get("rating")).lower() != "nan"]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    cx = compute_cx_score(
        sentiment_counts=dict(sentiment_counts),
        aspect_sentiment_counts=dict(aspect_sentiment_counts_global),
        priority_counts=dict(priority_counts),
        avg_rating=avg_rating,
    )

    trends = analyze_trends(analyzable_rows)

    # top recurring problems: most frequent negative aspects
    recurring_problems = [
        {"aspect": a["aspect"], "negative_mentions": a["negative"]}
        for a in sorted(aspect_summary, key=lambda a: -a["negative"]) if a["negative"] > 0
    ][:6]

    insights = dashboard_insights(
        sentiment_counts=dict(sentiment_counts),
        aspect_summary=aspect_summary,
        priority_counts=dict(priority_counts),
        emotion_counts=dict(emotion_counts),
        emerging_issues=trends["emerging_issues"],
    )

    # Advanced intelligence zones — all computed from the same real rows,
    # nothing hardcoded or fabricated.
    customer_voice = compute_customer_voice(aspect_summary)
    issue_radar = compute_issue_radar(aspect_summary, analyzable_rows, trends["emerging_issues"])
    emotion_by_aspect = compute_emotion_by_aspect(analyzable_rows)
    decision_center = compute_decision_center(issue_radar, analyzable_rows, emotion_by_aspect, domain=domain)

    # Translation health: lets an operator see, at a glance, whether the
    # translation backend is actually reachable in their deployment (rather
    # than silently falling back to original-text analysis for every
    # non-English review). Not shown as a big feature — just a small,
    # honest diagnostic.
    non_english_rows = [r for r in rows if r.get("language_code") not in (None, "en")]
    translated_ok = sum(1 for r in non_english_rows if r.get("translation_status") == "translated")
    unreliable_count = sum(1 for r in rows if not r.get("reliable", True))
    translation_health = {
        "non_english_reviews": len(non_english_rows),
        "translated_successfully": translated_ok,
        "success_rate_pct": round(100 * translated_ok / len(non_english_rows), 1) if non_english_rows else None,
        "unreliable_reviews": unreliable_count,
    }

    # sentiment by category/product, if available
    by_category = None
    cat_rows = [r for r in analyzable_rows if r.get("category")]
    if cat_rows:
        cat_df = pd.DataFrame(cat_rows)
        grp = cat_df.groupby("category")["overall_sentiment"].value_counts(normalize=True).unstack(fill_value=0)
        by_category = [
            {
                "category": cat,
                "positive": round(float(row.get("positive", 0)) * 100, 1),
                "neutral": round(float(row.get("neutral", 0)) * 100, 1),
                "negative": round(float(row.get("negative", 0)) * 100, 1),
            }
            for cat, row in grp.iterrows()
        ]

    return {
        "dataset_id": dataset_id,
        "total_reviews": total,
        "available_languages": available_languages,
        "active_language_filter": language or "All",
        "kpis": {
            "reviews_analyzed": len(analyzable_rows),
            "positive_pct": round(100 * sentiment_counts.get("positive", 0) / len(analyzable_rows), 1),
            "neutral_pct": round(100 * sentiment_counts.get("neutral", 0) / len(analyzable_rows), 1),
            "negative_pct": round(100 * sentiment_counts.get("negative", 0) / len(analyzable_rows), 1),
            "cx_score": cx["score"],
            "cx_label": cx["label"],
            "high_critical_issues": priority_counts.get("High", 0) + priority_counts.get("Critical", 0),
        },
        "cx_score_components": cx["components"],
        "sentiment_distribution": {
            "positive": sentiment_counts.get("positive", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "negative": sentiment_counts.get("negative", 0),
        },
        "sentiment_by_category": by_category,
        "aspect_summary": aspect_summary,
        "emotion_distribution": dict(emotion_counts),
        "priority_distribution": {
            "Low": priority_counts.get("Low", 0),
            "Medium": priority_counts.get("Medium", 0),
            "High": priority_counts.get("High", 0),
            "Critical": priority_counts.get("Critical", 0),
        },
        "recurring_problems": recurring_problems,
        "trends": trends,
        "business_insights": insights["business_insights"],
        "recommendations": insights["recommendations"],
        "avg_rating": avg_rating,
        "customer_voice": customer_voice,
        "issue_radar": issue_radar,
        "decision_center": decision_center,
        "language_breakdown": language_breakdown,
        "translation_health": translation_health,
    }


def _analysis_update_fields(analysis: Dict) -> Dict:
    """Extracts just the analysis-derived fields (everything EXCEPT the
    original review text and the optional raw columns like rating/date/
    product/category/customer_id, which must never change on a retry)."""
    neg_aspects = [a["aspect"] for a in analysis["aspects"] if a["sentiment"] == "negative"]
    pos_aspects = [a["aspect"] for a in analysis["aspects"] if a["sentiment"] == "positive"]
    return {
        "analyzed_text": analysis["analyzed_text"],
        "language": analysis["detected_language"],
        "language_code": analysis["language_code"],
        "translation_status": analysis["translation_status"],
        "overall_sentiment": analysis["overall_sentiment"]["label"],
        "sentiment_confidence": analysis["overall_sentiment"]["confidence"],
        "emotion": analysis["emotion"]["label"],
        "emotion_confidence": analysis["emotion"]["confidence"],
        "priority": analysis["priority"]["label"],
        "priority_score": analysis["priority"]["score"],
        "reliable": analysis["reliable"],
        "detected_aspects": [a["aspect"] for a in analysis["aspects"]],
        "aspect_sentiments": {a["aspect"]: a["sentiment"] for a in analysis["aspects"]},
        "negative_aspects": neg_aspects,
        "positive_aspects": pos_aspects,
    }


def retry_failed_translations(dataset_id: str, max_workers: int = 4) -> Optional[Dict]:
    """
    Re-runs translation + analysis ONLY for the rows in a saved dataset
    that could not be reliably analyzed the first time (translation
    failed), and updates their stored analyses in place. Reviews that
    were already reliably analyzed are left untouched - this is a
    targeted retry, not a full re-upload/re-analysis of the dataset.

    Returns None if the dataset doesn't exist, otherwise a summary dict.
    """
    dataset = get_dataset(dataset_id)
    if not dataset:
        return None

    domain = dataset.get("domain", "other")
    rows = dataset["rows"]

    failed_indices = [
        i for i, r in enumerate(rows) if not r.get("reliable", True)
    ]

    if not failed_indices:
        return {
            "dataset_id": dataset_id,
            "attempted": 0,
            "now_reliable": 0,
            "still_unreliable": 0,
        }

    def _retry_one(i):
        row = rows[i]
        try:
            rating_val = float(row["rating"]) if row.get("rating") not in (None, "") else None
        except (TypeError, ValueError):
            rating_val = None
        analysis = analyze_review(row["review"], domain=domain, rating=rating_val)
        return i, analysis

    retried: List[Tuple[int, Dict]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, analysis in executor.map(_retry_one, failed_indices):
            retried.append((i, analysis))

    now_reliable = 0
    use_db = db_available()

    for i, analysis in retried:
        update_fields = _analysis_update_fields(analysis)
        if analysis["reliable"]:
            now_reliable += 1

        # Update the in-memory copy we already have (used for the
        # summary below, and as the source of truth in no-DB mode).
        rows[i].update(update_fields)

        if use_db:
            review_id = rows[i].get("id")
            if review_id is not None:
                repository.update_review_analysis(review_id, update_fields)

    return {
        "dataset_id": dataset_id,
        "attempted": len(failed_indices),
        "now_reliable": now_reliable,
        "still_unreliable": len(failed_indices) - now_reliable,
    }


def export_csv(dataset_id: str) -> Optional[bytes]:
    dataset = get_dataset(dataset_id)
    if not dataset:
        return None
    rows = dataset["rows"]
    out_rows = []
    for r in rows:
        out_rows.append({
            "review": r["review"],
            "language": r.get("language"),
            "translation_status": r.get("translation_status"),
            "reliable": r.get("reliable", True),
            "overall_sentiment": r["overall_sentiment"],
            "sentiment_confidence": r["sentiment_confidence"],
            "emotion": r["emotion"],
            "emotion_confidence": r["emotion_confidence"],
            "priority": r["priority"],
            "detected_aspects": "; ".join(r["detected_aspects"]),
            "aspect_sentiments": "; ".join(f"{k}:{v}" for k, v in r["aspect_sentiments"].items()),
            "rating": r.get("rating"),
            "date": r.get("date"),
            "product": r.get("product"),
            "category": r.get("category"),
        })
    df = pd.DataFrame(out_rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")
