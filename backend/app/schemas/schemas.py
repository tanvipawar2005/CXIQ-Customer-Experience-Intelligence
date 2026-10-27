from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

VALID_DOMAINS = {"electronics", "ecommerce", "restaurant", "hotel", "travel", "other"}


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    domain: Optional[str] = Field(default="other")
    rating: Optional[float] = None

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Feedback text cannot be empty.")
        return v

    @field_validator("domain")
    @classmethod
    def domain_valid(cls, v: Optional[str]) -> str:
        if not v:
            return "other"
        v_norm = v.strip().lower()
        return v_norm if v_norm in VALID_DOMAINS else "other"


class SentimentResult(BaseModel):
    label: str
    confidence: float
    scores: Dict[str, float]


class AspectResult(BaseModel):
    aspect: str
    sentiment: str
    confidence: float
    mentions: List[str] = []


class EmotionResult(BaseModel):
    label: str
    confidence: float
    distribution: Dict[str, float]


class PriorityResult(BaseModel):
    label: str
    score: float
    reasons: List[str]


class ExplanationResult(BaseModel):
    important_words: List[Dict[str, Any]]
    negative_phrases: List[str]
    positive_phrases: List[str]
    signals: List[str]


class AnalyzeResponse(BaseModel):
    text: str
    original_text: str
    detected_language: str
    language_code: str
    is_code_mixed: bool
    translated_text: str
    translation_status: str
    reliable: bool
    domain: str
    overall_sentiment: SentimentResult
    aspects: List[AspectResult]
    emotion: EmotionResult
    priority: PriorityResult
    explanation: ExplanationResult
    business_insight: str
    recommendations: List[str]
    customer_experience_score: Optional[float] = None


class CompareEntry(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    label: Optional[str] = None


class CompareRequest(BaseModel):
    entries: List[CompareEntry] = Field(..., min_length=2, max_length=6)
    domain: Optional[str] = Field(default="other")

    @field_validator("domain")
    @classmethod
    def domain_valid(cls, v: Optional[str]) -> str:
        if not v:
            return "other"
        v_norm = v.strip().lower()
        return v_norm if v_norm in VALID_DOMAINS else "other"


class CompareResultItem(BaseModel):
    label: Optional[str]
    original_text: str
    detected_language: str
    translated_text: str
    translation_status: str
    overall_sentiment: str
    confidence: float
    emotion: str
    priority: str
    main_aspect: Optional[str]
    cx_score: float


class AskRequest(BaseModel):
    dataset_id: str = "sample"
    question: str = Field(..., min_length=1, max_length=300)


class AskResponse(BaseModel):
    answer: str
    source: str


class BatchAnalyzeSummary(BaseModel):
    dataset_id: str
    total_records: int
    processed_records: int
    skipped_records: int
    review_column: str
    columns_detected: Dict[str, Optional[str]]
    download_ready: bool


class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: Dict[str, bool]
