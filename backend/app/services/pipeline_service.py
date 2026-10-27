"""
pipeline_service.py

Orchestrates the full per-review pipeline:

  feedback -> language detection -> translation/normalization (if needed) ->
  overall sentiment -> aspect extraction -> aspect-level sentiment ->
  emotion detection -> complaint priority -> explainability ->
  business insight -> recommendations

Used by both the single-feedback endpoint and the batch dataset endpoint, so
the two modes are guaranteed to produce consistent, comparable results.

MULTILINGUAL DESIGN: CXIQ detects the review's language and, if it isn't
English, translates/normalizes it to English before running the existing
sentiment/ABSA/emotion/priority engine. This is a translation-based
multilingual architecture, not a native multilingual model — see
language_service.py and translation_service.py for the honest reasoning.
Both the original text and the analyzed (English) text are preserved.
"""
from __future__ import annotations
from typing import Dict, Optional

from app.services.sentiment_service import get_sentiment_service
from app.services.aspect_service import extract_aspects
from app.services.emotion_service import detect_emotion
from app.services.priority_service import predict_priority
from app.services.explainability_service import build_explanation
from app.services.insight_service import single_review_insight
from app.services.preprocessing import clean_text, truncate_for_processing
from app.services.language_service import detect_language
from app.services.translation_service import translate_to_english


def analyze_review(text: str, domain: str = "other", rating: Optional[float] = None) -> Dict:
    original_text = truncate_for_processing(clean_text(text))

    lang_info = detect_language(original_text)
    translated_text, translation_status = translate_to_english(original_text, lang_info["code"])

    # HONEST FAILURE HANDLING: if the text isn't English and translation
    # failed, we genuinely do not have reliable input for an English-only
    # NLP engine. Running the sentiment model on untranslated Hindi/Marathi
    # text anyway produces meaningless (and sometimes confidently WRONG)
    # output, because the model is scoring character/n-gram noise it was
    # never trained on. Rather than silently returning that as a normal
    # result, CXIQ returns a clearly-marked "unreliable" result: a neutral,
    # low-confidence sentiment, no guessed aspects, and an explicit note —
    # never a confident positive/negative built on a guess.
    translation_unreliable = translation_status == "failed" and lang_info["code"] != "en"

    analysis_text = translated_text if not translation_unreliable else original_text

    sentiment_svc = get_sentiment_service()

    if translation_unreliable:
        overall_sentiment = {
            "label": "neutral",
            "confidence": 0.3,
            "scores": {"positive": 0.3, "neutral": 0.4, "negative": 0.3},
        }
        aspects = []
        emotion = {"label": "Neutral", "confidence": 0.3, "distribution": {}}
        priority = {
            "label": "Low",
            "score": 0.0,
            "reasons": [
                f"Translation from {lang_info['name']} was unavailable, so priority could not be "
                f"reliably assessed from the review text alone."
            ],
        }
        explanation = {
            "important_words": [],
            "negative_phrases": [],
            "positive_phrases": [],
            "signals": [
                f"Could not translate this {lang_info['name']} review to English (translation service "
                f"unavailable or the request failed). Rather than guess, CXIQ is reporting this result "
                f"as low-confidence/neutral instead of a potentially wrong prediction."
            ],
        }
        business_insight = (
            f"This review is in {lang_info['name']} and could not be translated for analysis. "
            f"Please retry once translation is available, or have it reviewed manually."
        )
        recommendations = ["Retry analysis once translation service connectivity is restored."]
    else:
        overall_sentiment = sentiment_svc.predict(analysis_text)
        aspects = extract_aspects(analysis_text, domain)
        emotion = detect_emotion(analysis_text, overall_sentiment=overall_sentiment)
        priority = predict_priority(analysis_text, overall_sentiment, aspects, rating)
        explanation = build_explanation(analysis_text, overall_sentiment, aspects, emotion, priority)
        insight = single_review_insight(overall_sentiment, aspects, emotion, priority)
        business_insight = insight["business_insight"]
        recommendations = insight["recommendations"]

    return {
        "text": analysis_text,
        "original_text": original_text,
        "analyzed_text": analysis_text,
        "detected_language": lang_info["name"],
        "language_code": lang_info["code"],
        "is_code_mixed": lang_info["is_code_mixed"],
        "translated_text": translated_text,
        "translation_status": translation_status,
        "reliable": not translation_unreliable,
        "domain": domain,
        "overall_sentiment": overall_sentiment,
        "aspects": aspects,
        "emotion": emotion,
        "priority": priority,
        "explanation": explanation,
        "business_insight": business_insight,
        "recommendations": recommendations,
    }

