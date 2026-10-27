"""
models_db.py

Three tables — deliberately minimal, matching exactly what CXIQ already
computes and uses in memory today:

  users     — one row per person who has signed in via Clerk. Optional:
              CXIQ works fully in guest mode with no rows here at all.
  datasets  — one row per uploaded batch (or the preloaded "sample" dataset).
              Tracks which user uploaded it (nullable — guests can upload
              too, they just won't see it again in a personal list).
  reviews   — one row per analyzed review. This is the big table; each row
              holds the exact same fields the in-memory pipeline already
              produces (sentiment, aspects, emotion, priority, language,
              translation info, etc.) so almost none of the existing
              aggregation code (dashboard_service, intelligence_service,
              trend_service) needed to change — it just reads rows from the
              database instead of a Python dict.
"""
from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship

from app.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    datasets = relationship("Dataset", back_populates="user")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True)  # uuid4 string, or "sample"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=True)
    domain = Column(String(64), nullable=True)
    review_column = Column(String(128), nullable=True)
    columns_detected = Column(JSON, nullable=True)
    total_records = Column(Integer, default=0)
    # True for a user's personal copy of the bundled sample dataset (created
    # via POST /api/datasets/sample), so "My Datasets" can badge it clearly
    # and the endpoint can be idempotent (reuse instead of duplicating).
    is_sample = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="datasets")
    reviews = relationship("Review", back_populates="dataset", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(String(64), ForeignKey("datasets.id"), nullable=False, index=True)

    review = Column(Text, nullable=False)              # original text
    analyzed_text = Column(Text, nullable=True)         # English text actually analyzed
    language = Column(String(32), nullable=True)
    language_code = Column(String(16), nullable=True)
    translation_status = Column(String(16), nullable=True)

    overall_sentiment = Column(String(16), nullable=True)
    sentiment_confidence = Column(Float, nullable=True)
    emotion = Column(String(16), nullable=True)
    emotion_confidence = Column(Float, nullable=True)
    priority = Column(String(16), nullable=True)
    priority_score = Column(Float, nullable=True)
    reliable = Column(Boolean, default=True)  # False when translation failed and text couldn't be reliably analyzed

    detected_aspects = Column(JSON, nullable=True)      # list[str]
    aspect_sentiments = Column(JSON, nullable=True)     # {aspect: sentiment}
    negative_aspects = Column(JSON, nullable=True)       # list[str]
    positive_aspects = Column(JSON, nullable=True)       # list[str]

    rating = Column(Float, nullable=True)
    date = Column(String(32), nullable=True)            # kept as text; parsed on read (matches original CSV flexibility)
    product = Column(String(255), nullable=True)
    category = Column(String(128), nullable=True)
    customer_id = Column(String(128), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    dataset = relationship("Dataset", back_populates="reviews")
