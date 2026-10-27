"""
gemini_service.py

OPTIONAL generative-AI layer for CXIQ.

Gemini is NEVER used as the main sentiment, aspect, emotion, or priority
classifier. Those results are produced by CXIQ's ML/NLP pipeline.

Gemini is used only for:

1. Business-summary generation
2. Ask CXIQ natural-language answers
3. Translation fallback when MyMemory translation fails

If Gemini is unavailable, the rest of CXIQ continues working normally.
"""

from __future__ import annotations

import json
import re
from typing import Dict

import httpx

from app.config import settings


GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/{model}:generateContent"
)


# =========================================================
# SECRET REDACTION
# =========================================================

def _redact_secret(message: str) -> str:
    """
    Strip the Gemini API key out of any string before it is logged or
    included in an exception message.

    SECURITY: httpx (and other HTTP clients) can embed the *request URL*
    in raised-exception messages (connection errors, timeouts, etc). The
    API key used to be passed as a `?key=...` query parameter, so those
    exception messages - and anything that logged them - could leak the
    real key into application logs. The key is now sent via the
    `x-goog-api-key` header instead (see `_generate_text`), which keeps
    it out of the URL entirely; this redaction is kept as a second,
    defense-in-depth layer in case the key ever appears in a message
    for any other reason.
    """

    message = message or ""

    api_key = settings.GEMINI_API_KEY

    if api_key:
        message = message.replace(api_key, "***REDACTED***")

    # Also catch a `key=...` query-param pattern generically, in case a
    # differently-configured key or a third-party library re-introduces
    # it into a URL somewhere.
    message = re.sub(
        r"([?&]key=)[^&\s]+",
        r"\1***REDACTED***",
        message,
    )

    return message


# =========================================================
# CONFIGURATION
# =========================================================

def is_configured() -> bool:
    """Return True only when Gemini is enabled and fully configured."""
    return bool(
        settings.GEMINI_ENABLED
        and settings.GEMINI_API_KEY
        and settings.GEMINI_MODEL
    )


# =========================================================
# COMMON GEMINI REQUEST
# =========================================================

def _generate_text(prompt: str, timeout: float = 8.0) -> str:
    """
    Send a prompt to Gemini and return generated plain text.

    Raises an exception if:
    - Gemini is not configured
    - request fails
    - Gemini returns a non-200 response
    - response contains no usable text

    Keeping the actual API request here prevents duplicate Gemini
    request logic across summary, Q&A, and translation.
    """

    if not is_configured():
        raise RuntimeError("Gemini is not configured.")

    url = GEMINI_ENDPOINT.format(
        model=settings.GEMINI_MODEL,
    )

    # SECURITY: the API key is sent as a request header, never as a
    # `?key=...` query parameter - this keeps it out of the request URL,
    # which is what HTTP client libraries (httpx included) tend to embed
    # verbatim in connection/timeout exception messages and access logs.
    headers = {
        "x-goog-api-key": settings.GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload, headers=headers)

    except Exception as exc:

        # Never let a raw httpx exception (which can include request
        # details) propagate with a potentially key-bearing message.
        raise RuntimeError(
            f"Gemini request failed: {_redact_secret(str(exc))}"
        ) from None

    if response.status_code != 200:
        detail = response.text[:500] if response.text else ""
        raise RuntimeError(
            f"Gemini returned HTTP {response.status_code}: {_redact_secret(detail)}"
        )

    data = response.json()

    candidates = data.get("candidates", [])

    if not candidates:
        raise ValueError("Gemini response contains no candidates.")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])

    if not parts:
        raise ValueError("Gemini response contains no content parts.")

    text = (parts[0].get("text") or "").strip()

    if not text:
        raise ValueError("Gemini returned an empty response.")

    return text


# =========================================================
# BUSINESS SUMMARY
# =========================================================

def _build_prompt(structured_input: Dict) -> str:
    return (
        "You are a customer experience analytics assistant. Based ONLY on the "
        "structured analysis data below (do not invent numbers), write a concise "
        "management-friendly summary in 2-3 sentences explaining what the data "
        "shows and why it matters. Do NOT include a numbered action list or "
        "recommendations - those are generated and displayed separately by the "
        "application. Structured data:\n\n"
        f"{json.dumps(structured_input, indent=2)}\n\n"
        "Respond in plain text, no markdown headers, no numbered list."
    )


def generate_business_summary(
    structured_input: Dict,
    fallback: Dict,
) -> Dict:
    """
    Generate the management-friendly CXIQ summary.

    If Gemini is unavailable or fails, return the existing rule-based
    insight_service output.
    """

    if not is_configured():
        return {
            **fallback,
            "source": "rule_based_fallback",
        }

    try:
        prompt = _build_prompt(structured_input)

        text = _generate_text(
            prompt,
            timeout=8.0,
        )

        return {
            "business_insight": text,
            "business_insights": [text],
            "recommendations": fallback.get(
                "recommendations",
                [],
            ),
            "source": "gemini",
        }

    except Exception as exc:
        return {
            **fallback,
            "source": "rule_based_fallback",
            "gemini_error": str(exc),
        }


# =========================================================
# ASK CXIQ
# =========================================================

def _build_qa_prompt(
    question: str,
    structured_stats: Dict,
) -> str:

    return (
        "You are a customer experience analytics assistant embedded in a dashboard. "
        "Answer the manager's question below using ONLY the structured statistics "
        "provided (do not invent numbers or facts not present in the data). "
        "Answer in 2-4 concise sentences, in plain business language, no markdown.\n\n"
        f"Question: {question}\n\n"
        "Structured dashboard statistics:\n"
        f"{json.dumps(structured_stats, indent=2)}"
    )


def answer_dashboard_question(
    question: str,
    structured_stats: Dict,
    fallback_answer: str,
) -> Dict:
    """
    Used by Ask CXIQ.

    Gemini only converts existing dashboard statistics into a natural-language
    answer. It does not independently calculate CX statistics.
    """

    if not is_configured():
        return {
            "answer": fallback_answer,
            "source": "rule_based",
        }

    try:

        prompt = _build_qa_prompt(
            question,
            structured_stats,
        )

        text = _generate_text(
            prompt,
            timeout=8.0,
        )

        return {
            "answer": text,
            "source": "gemini",
        }

    except Exception as exc:

        return {
            "answer": fallback_answer,
            "source": "rule_based",
            "gemini_error": str(exc),
        }


# =========================================================
# TRANSLATION FALLBACK
# =========================================================

LANGUAGE_NAMES = {
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
    "fr": "French",
    "hi-en": "Hindi-English / Marathi-English code-mixed text",
}


def _build_translation_prompt(
    text: str,
    language_code: str,
) -> str:
    """
    Create a strict translation-only prompt.

    Gemini must translate the review without performing sentiment,
    emotion, aspect, or priority analysis.
    """

    language_name = LANGUAGE_NAMES.get(
        language_code,
        language_code,
    )

    return (
        f"Translate the following customer review from {language_name} "
        "into natural English.\n\n"

        "Important rules:\n"
        "1. Return ONLY the English translation.\n"
        "2. Do not explain the translation.\n"
        "3. Do not summarize the review.\n"
        "4. Do not add information.\n"
        "5. Preserve the customer's original meaning.\n"
        "6. Preserve positive, negative, neutral, and mixed sentiment.\n"
        "7. Preserve negation exactly. For example, do not change "
        "'not good' into 'good' or 'not bad' into 'bad'.\n"
        "8. Preserve complaints, praise, contrast, and intensity.\n"
        "9. Preserve product names, brand names, model numbers, "
        "prices, and technical terms.\n"
        "10. If the review is code-mixed, translate its complete "
        "meaning into natural English.\n\n"

        "Customer review:\n"
        f"{text}"
    )


def translate_review(
    text: str,
    language_code: str,
) -> str:
    """
    Translate a customer review using Gemini.

    IMPORTANT:
    This function is intended only as the FALLBACK translator when
    MyMemory fails.

    It does not perform sentiment/aspect/emotion classification.
    """

    text = (text or "").strip()

    if not text:
        return text

    prompt = _build_translation_prompt(
        text,
        language_code,
    )

    translated = _generate_text(
        prompt,
        timeout=8.0,
    )

    translated = translated.strip()

    # Gemini occasionally surrounds short output with quotes.
    # Remove only matching outer quotes.
    if (
        len(translated) >= 2
        and translated[0] == translated[-1]
        and translated[0] in ('"', "'")
    ):
        translated = translated[1:-1].strip()

    if not translated:
        raise ValueError(
            "Gemini returned an empty translation."
        )

    return translated