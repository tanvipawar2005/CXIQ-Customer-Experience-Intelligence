"""
cxscore_service.py

Customer Experience Score (0-100) — a single transparent number that
summarises how customers feel overall, calculated from real analytical
signals only. Never randomly generated.

FORMULA
-------
CX Score = 100 * (
      W_sentiment      * sentiment_health
    + W_aspect_health  * aspect_health
    + W_rating         * rating_health
) - (100 * W_priority_penalty * priority_penalty)

Where:
  sentiment_health  = (positive_count - negative_count + total) / (2 * total)
                       -> 1.0 if all positive, 0.0 if all negative, 0.5 if balanced
  aspect_health      = positive_aspect_mentions / total_aspect_mentions (0.5 if no aspects)
  rating_health      = (avg_rating - 1) / 4   (only included if rating data exists;
                        otherwise its weight is redistributed to sentiment)
  priority_penalty   = (high_count + 2 * critical_count) / total_reviews, capped at 1.0

Weights (app/config.py -> CX_SCORE_WEIGHTS):
  sentiment: 0.45, aspect_health: 0.25, priority_penalty: 0.20, rating: 0.10

Bands (app/config.py -> CX_SCORE_BANDS):
  80-100 Excellent | 65-79 Good | 50-64 Needs Attention | 0-49 Critical
"""
from __future__ import annotations
from typing import Dict, List, Optional

from app.config import settings


def score_label(score: float) -> str:
    for low, high, label in settings.CX_SCORE_BANDS:
        if low <= score <= high:
            return label
    return "Critical"


def compute_cx_score(
    sentiment_counts: Dict[str, int],
    aspect_sentiment_counts: Dict[str, int],
    priority_counts: Dict[str, int],
    avg_rating: Optional[float] = None,
) -> Dict:
    total_reviews = sum(sentiment_counts.values()) or 1
    pos = sentiment_counts.get("positive", 0)
    neg = sentiment_counts.get("negative", 0)
    sentiment_health = (pos - neg + total_reviews) / (2 * total_reviews)

    total_aspect_mentions = sum(aspect_sentiment_counts.values())
    if total_aspect_mentions > 0:
        aspect_health = aspect_sentiment_counts.get("positive", 0) / total_aspect_mentions
    else:
        aspect_health = 0.5  # neutral default when no aspects detected

    high = priority_counts.get("High", 0)
    critical = priority_counts.get("Critical", 0)
    priority_penalty = min(1.0, (high + 2 * critical) / total_reviews)

    weights = dict(settings.CX_SCORE_WEIGHTS)
    if avg_rating is None:
        # redistribute the rating weight into sentiment when no rating data exists
        weights["sentiment"] += weights["rating"]
        weights["rating"] = 0.0
        rating_health = 0.0
    else:
        rating_health = max(0.0, min(1.0, (avg_rating - 1) / 4))

    raw = (
        weights["sentiment"] * sentiment_health
        + weights["aspect_health"] * aspect_health
        + weights["rating"] * rating_health
    ) * 100
    raw -= weights["priority_penalty"] * 100 * priority_penalty

    score = round(max(0.0, min(100.0, raw)), 1)
    return {
        "score": score,
        "label": score_label(score),
        "components": {
            "sentiment_health": round(sentiment_health, 3),
            "aspect_health": round(aspect_health, 3),
            "priority_penalty": round(priority_penalty, 3),
            "rating_health": round(rating_health, 3) if avg_rating is not None else None,
        },
    }
