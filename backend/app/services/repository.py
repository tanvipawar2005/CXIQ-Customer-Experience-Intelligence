"""
repository.py

Database access layer for datasets/reviews/users. Every read function
returns plain dicts in EXACTLY the same shape the old in-memory `_DATASETS`
dict used — this is deliberate, so dashboard_service.py, intelligence_
service.py, and trend_service.py needed almost no changes when the storage
backend switched from a Python dict to PostgreSQL.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from sqlalchemy import select, delete

from app.db import get_session
from app.models_db import User, Dataset, Review


def _review_to_dict(r: Review) -> Dict:
    return {
        "id": r.id,
        "review": r.review,
        "analyzed_text": r.analyzed_text,
        "language": r.language,
        "language_code": r.language_code,
        "translation_status": r.translation_status,
        "overall_sentiment": r.overall_sentiment,
        "sentiment_confidence": r.sentiment_confidence,
        "emotion": r.emotion,
        "emotion_confidence": r.emotion_confidence,
        "priority": r.priority,
        "priority_score": r.priority_score,
        "reliable": r.reliable if r.reliable is not None else True,
        "detected_aspects": r.detected_aspects or [],
        "aspect_sentiments": r.aspect_sentiments or {},
        "negative_aspects": r.negative_aspects or [],
        "positive_aspects": r.positive_aspects or [],
        "rating": r.rating,
        "date": r.date,
        "product": r.product,
        "category": r.category,
        "customer_id": r.customer_id,
    }


def dataset_exists(dataset_id: str) -> bool:
    with get_session() as session:
        return session.get(Dataset, dataset_id) is not None


def create_dataset(
    dataset_id: str,
    domain: str,
    review_column: str,
    columns_detected: Dict,
    total_records: int,
    filename: Optional[str] = None,
    user_id: Optional[int] = None,
    is_sample: bool = False,
) -> None:
    with get_session() as session:
        existing = session.get(Dataset, dataset_id)
        if existing:
            # Re-upload with the same id (e.g. re-seeding "sample"): clear old rows first.
            session.execute(delete(Review).where(Review.dataset_id == dataset_id))
            session.delete(existing)
            session.flush()
        ds = Dataset(
            id=dataset_id, user_id=user_id, filename=filename, domain=domain,
            review_column=review_column, columns_detected=columns_detected,
            total_records=total_records, is_sample=is_sample,
        )
        session.add(ds)


def bulk_insert_reviews(dataset_id: str, rows: List[Dict]) -> None:
    with get_session() as session:
        objects = [
            Review(
                dataset_id=dataset_id,
                review=r["review"],
                analyzed_text=r.get("analyzed_text"),
                language=r.get("language"),
                language_code=r.get("language_code"),
                translation_status=r.get("translation_status"),
                overall_sentiment=r["overall_sentiment"],
                sentiment_confidence=r["sentiment_confidence"],
                emotion=r["emotion"],
                emotion_confidence=r["emotion_confidence"],
                priority=r["priority"],
                priority_score=r["priority_score"],
                reliable=r.get("reliable", True),
                detected_aspects=r.get("detected_aspects") or [],
                aspect_sentiments=r.get("aspect_sentiments") or {},
                negative_aspects=r.get("negative_aspects") or [],
                positive_aspects=r.get("positive_aspects") or [],
                rating=_safe_float(r.get("rating")),
                date=_safe_str(r.get("date")),
                product=_safe_str(r.get("product")),
                category=_safe_str(r.get("category")),
                customer_id=_safe_str(r.get("customer_id")),
            )
            for r in rows
        ]
        session.bulk_save_objects(objects)


def _safe_float(v):
    try:
        if v in (None, "") or str(v).lower() == "nan":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_str(v):
    if v is None:
        return None
    s = str(v)
    return None if s.lower() == "nan" else s


def update_review_analysis(review_id: int, analysis_fields: Dict) -> bool:
    """
    Overwrites the analysis-derived fields of a single already-stored
    review row (used by the "retry failed translations" flow: the
    original `review` text and any optional columns - rating, date,
    product, category, customer_id - are left untouched; only the
    translation/sentiment/aspect/emotion/priority outputs are replaced
    with a freshly re-run analysis).
    """
    with get_session() as session:
        row = session.get(Review, review_id)
        if not row:
            return False
        for key, value in analysis_fields.items():
            setattr(row, key, value)
        return True


def get_dataset_meta(dataset_id: str) -> Optional[Dict]:
    with get_session() as session:
        ds = session.get(Dataset, dataset_id)
        if not ds:
            return None
        return {
            "id": ds.id,
            "user_id": ds.user_id,
            "filename": ds.filename,
            "domain": ds.domain,
            "review_column": ds.review_column,
            "columns_detected": ds.columns_detected or {},
            "total_records": ds.total_records,
            "is_sample": bool(ds.is_sample),
            "created_at": ds.created_at.isoformat() if ds.created_at else None,
        }


def get_dataset_rows(dataset_id: str) -> Optional[List[Dict]]:
    with get_session() as session:
        ds = session.get(Dataset, dataset_id)
        if not ds:
            return None
        rows = session.execute(
            select(Review).where(Review.dataset_id == dataset_id)
        ).scalars().all()
        return [_review_to_dict(r) for r in rows]


def list_datasets_for_user(user_id: int) -> List[Dict]:
    with get_session() as session:
        rows = session.execute(
            select(Dataset).where(Dataset.user_id == user_id).order_by(Dataset.created_at.desc())
        ).scalars().all()
        return [
            {
                "dataset_id": d.id,
                "filename": d.filename,
                "domain": d.domain,
                "total_records": d.total_records,
                "is_sample": bool(d.is_sample),
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in rows
        ]


def get_user_sample_dataset_id(user_id: int) -> Optional[str]:
    """Returns the dataset_id of this user's own copy of the sample dataset,
    if they've already created one (POST /api/datasets/sample is idempotent
    — we never want to create a second copy on repeat clicks)."""
    with get_session() as session:
        ds = session.execute(
            select(Dataset)
            .where(Dataset.user_id == user_id, Dataset.is_sample.is_(True))
            .order_by(Dataset.created_at.desc())
        ).scalars().first()
        return ds.id if ds else None


def clone_dataset_for_user(
    source_dataset_id: str,
    new_dataset_id: str,
    user_id: int,
    filename: Optional[str] = None,
    is_sample: bool = False,
) -> bool:
    """Copies an already-analyzed dataset's metadata + rows to a new
    dataset owned by `user_id`, WITHOUT re-running the ML/translation
    pipeline. Used for "Try Sample Dataset" so every user gets their own
    private, isolated copy of the bundled sample without paying the cost
    (or translation-service dependency) of re-analyzing it from scratch.
    Returns False if the source dataset doesn't exist."""
    with get_session() as session:
        source = session.get(Dataset, source_dataset_id)
        if not source:
            return False
        source_reviews = session.execute(
            select(Review).where(Review.dataset_id == source_dataset_id)
        ).scalars().all()

        new_ds = Dataset(
            id=new_dataset_id,
            user_id=user_id,
            filename=filename or source.filename,
            domain=source.domain,
            review_column=source.review_column,
            columns_detected=source.columns_detected,
            total_records=source.total_records,
            is_sample=is_sample,
        )
        session.add(new_ds)

        clones = [
            Review(
                dataset_id=new_dataset_id,
                review=r.review,
                analyzed_text=r.analyzed_text,
                language=r.language,
                language_code=r.language_code,
                translation_status=r.translation_status,
                overall_sentiment=r.overall_sentiment,
                sentiment_confidence=r.sentiment_confidence,
                emotion=r.emotion,
                emotion_confidence=r.emotion_confidence,
                priority=r.priority,
                priority_score=r.priority_score,
                reliable=r.reliable,
                detected_aspects=r.detected_aspects,
                aspect_sentiments=r.aspect_sentiments,
                negative_aspects=r.negative_aspects,
                positive_aspects=r.positive_aspects,
                rating=r.rating,
                date=r.date,
                product=r.product,
                category=r.category,
                customer_id=r.customer_id,
            )
            for r in source_reviews
        ]
        if clones:
            session.bulk_save_objects(clones)
        return True


def get_or_create_user(clerk_user_id: str, email: Optional[str] = None) -> int:
    with get_session() as session:
        user = session.execute(
            select(User).where(User.clerk_user_id == clerk_user_id)
        ).scalar_one_or_none()
        if user:
            if email and user.email != email:
                user.email = email
            return user.id
        user = User(clerk_user_id=clerk_user_id, email=email)
        session.add(user)
        session.flush()
        return user.id
