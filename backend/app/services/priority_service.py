"""
priority_service.py

MODEL TYPE: RULE-BASED SIGNAL AGGREGATION (explainable by design).

Combines several transparent signals into a 0-1 severity score, then maps
that score onto Low / Medium / High / Critical using configurable thresholds
(see app/config.py). Every contributing signal is returned as a plain-English
reason so the UI can show *why* a priority was assigned.

Signals used:
  - overall sentiment (negative sentiment raises severity)
  - number / proportion of negative aspects
  - presence of high-severity complaint phrases (utils/lexicons.COMPLAINT_TERMS)
  - repeated-issue language ("again", "still", "every time" ...)
  - provided star rating, if available (1-5 scale)
"""
from __future__ import annotations
from typing import Dict, List, Optional

from app.utils.lexicons import COMPLAINT_TERMS, REPEAT_INDICATORS
from app.config import settings


def _complaint_term_signal(text_lower: str) -> (float, List[str]):
    hits = []
    max_weight = 0.0
    for term, weight in COMPLAINT_TERMS.items():
        if term in text_lower:
            hits.append(term)
            max_weight = max(max_weight, weight)
    return max_weight, hits


def _repeat_signal(text_lower: str) -> bool:
    return any(term in text_lower for term in REPEAT_INDICATORS)


def predict_priority(
    text: str,
    overall_sentiment: Dict,
    aspects: List[Dict],
    rating: Optional[float] = None,
) -> Dict:
    text_lower = text.lower()
    reasons: List[str] = []
    score = 0.0

    # 1. overall sentiment signal
    if overall_sentiment["label"] == "negative":
        sentiment_contribution = 0.30 * overall_sentiment["confidence"]
        score += sentiment_contribution
        reasons.append(f"Overall sentiment is negative ({round(overall_sentiment['confidence']*100)}% confidence).")

    # 2. negative aspect ratio
    if aspects:
        negative_aspects = [a for a in aspects if a["sentiment"] == "negative"]
        ratio = len(negative_aspects) / len(aspects)
        if negative_aspects:
            score += 0.25 * ratio
            names = ", ".join(a["aspect"] for a in negative_aspects[:3])
            reasons.append(f"{len(negative_aspects)} of {len(aspects)} detected aspect(s) are negative ({names}).")

    # 3. complaint severity terms
    complaint_weight, hits = _complaint_term_signal(text_lower)
    if hits:
        score += 0.35 * complaint_weight
        reasons.append(f"Contains high-severity complaint language: {', '.join(hits[:3])}.")

    # 4. repeated-issue indicators
    if _repeat_signal(text_lower):
        score += 0.10
        reasons.append("Language suggests this is a recurring / repeated issue.")

    # 5. rating signal, if provided
    if rating is not None:
        try:
            rating = float(rating)
            if rating <= 2:
                score += 0.20
                reasons.append(f"Low star rating provided ({rating}/5).")
            elif rating >= 4:
                score -= 0.15
        except (TypeError, ValueError):
            pass

    score = max(0.0, min(1.0, score))

    thresholds = settings.PRIORITY_THRESHOLDS
    if score >= thresholds["critical"]:
        label = "Critical"
    elif score >= thresholds["high"]:
        label = "High"
    elif score >= thresholds["medium"]:
        label = "Medium"
    else:
        label = "Low"

    if not reasons:
        reasons.append("No strong complaint or negative-sentiment signals detected.")

    return {
        "label": label,
        "score": round(score, 4),
        "reasons": reasons,
    }
