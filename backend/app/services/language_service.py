"""
language_service.py

Detects the language of a customer review.

CXIQ supports:
    English
    Hindi
    Marathi
    Spanish
    French
    Hinglish

DESIGN
------
Language detection determines whether translation to English is required.
CXIQ does not use separate sentiment models for each language.

Detection strategy:

1. Hinglish:
   Latin-script Hindi/Marathi markers.

2. Devanagari:
   Hindi and Marathi share the same script, so script detection alone
   cannot distinguish them.

   Marathi-specific lexical/orthographic markers are checked first.
   langdetect is then used as supporting evidence.

3. Latin-script text:
   langdetect is used for English / Spanish / French with confidence
   protection.

This remains language detection, not multilingual sentiment analysis.
"""

from __future__ import annotations

import logging
import re
import threading
from typing import Dict

from langdetect import (
    detect_langs,
    DetectorFactory,
    LangDetectException,
)


logger = logging.getLogger("cxiq")

DetectorFactory.seed = 0

# =========================================================
# THREAD SAFETY
# =========================================================
#
# `langdetect` is NOT thread-safe: its internal n-gram detector shares
# mutable state across calls, so when multiple threads call
# detect_langs() at the same time (exactly what happens during a batch
# upload - dashboard_service.process_batch analyzes rows concurrently
# on a ThreadPoolExecutor), results become corrupted and unpredictable
# - e.g. a French or Spanish review coming back as "af", "ca", or even
# "pl" with ~100% confidence, for every row in the batch, varying by
# run. A single process-wide lock serializes just the detect_langs()
# call itself (a few milliseconds) so concurrent batch analysis stays
# fast everywhere else while never corrupting language detection.
_LANGDETECT_LOCK = threading.Lock()


# =========================================================
# CONFIGURATION
# =========================================================

MIN_CONFIDENCE = 0.55

MIN_CHARS_FOR_DETECTION = 8


SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
    "fr": "French",
}


# =========================================================
# HINGLISH MARKERS
# =========================================================

HINGLISH_MARKERS = {
    "hai",
    "hain",
    "tha",
    "thi",

    "nahi",
    "nahin",
    "nahiin",

    "bahut",
    "bohot",
    "bhot",

    "mast",
    "ekdum",
    "bakwas",

    "accha",
    "acha",
    "theek",
    "sahi",

    "kharab",
    "badiya",

    "jaldi",

    "paisa",
    "paise",

    "wala",
    "wali",

    "kyun",
    "kaise",
    "kya",

    "yaar",
    "bilkul",

    "hoti",
    "hota",

    "raha",
    "rahi",

    "karte",
    "karta",
    "karti",

    "zyada",

    # Marathi transliteration
    "sampte",
    "khup",
    "aahe",
    "aahet",

    "changla",
    "changli",
    "changle",

    "lavkar",
}


# =========================================================
# MARATHI DEVANAGARI MARKERS
# =========================================================

# Hindi and Marathi share Devanagari, so these markers help distinguish
# short Marathi customer reviews from Hindi ones.

MARATHI_MARKERS = {
    "आहे",
    "आहेत",
    "होते",
    "होता",
    "होती",

    "खूप",

    "चांगला",
    "चांगली",
    "चांगले",
    "चांगलीच",

    "वाईट",

    "नाही",

    "योग्य",

    "किंमत",
    "किमतीत",
    "किमतीमध्ये",

    "उत्पादनाची",
    "उत्पादनाचे",
    "उत्पादन",

    "गुणवत्ता",

    "वाटते",
    "वाटला",
    "वाटली",

    "झाली",
    "झाले",
    "झाला",

    "उशिरा",

    "मदत",
    "करणारा",
    "करणारी",

    "अजिबात",

    "विशेष",

    "काही",

    "पॅकेजिंग",
    "डिलिव्हरी",
}


# Stronger markers that are particularly useful for Marathi.

STRONG_MARATHI_MARKERS = {
    "आहे",
    "आहेत",
    "खूप",
    "वाईट",
    "योग्य",
    "किंमत",
    "किमतीत",
    "उत्पादनाची",
    "वाटते",
    "झाली",
    "उशिरा",
    "अजिबात",
    "करणारा",
    "करणारी",
}


# =========================================================
# REGEX
# =========================================================

_WORD_RE = re.compile(
    r"[A-Za-z']+"
)

_DEVANAGARI_RE = re.compile(
    r"[\u0900-\u097F]"
)

_DEVANAGARI_WORD_RE = re.compile(
    r"[\u0900-\u097F]+"
)


# =========================================================
# HELPERS
# =========================================================

def _hinglish_hits(
    text: str,
) -> int:

    tokens = {
        token.lower()
        for token
        in _WORD_RE.findall(text)
    }

    return len(
        tokens
        & HINGLISH_MARKERS
    )


def _contains_devanagari(
    text: str,
) -> bool:

    return bool(
        _DEVANAGARI_RE.search(
            text
        )
    )


def _marathi_marker_score(
    text: str,
) -> int:
    """
    Calculate lightweight Marathi lexical evidence.

    Strong markers count more heavily.
    """

    words = set(
        _DEVANAGARI_WORD_RE.findall(
            text
        )
    )

    score = 0

    for word in words:

        if word in STRONG_MARATHI_MARKERS:
            score += 2

        elif word in MARATHI_MARKERS:
            score += 1

    return score


def _safe_detect_candidates(
    text: str,
):
    """
    Run langdetect safely.

    Wrapped in _LANGDETECT_LOCK because langdetect is not thread-safe -
    see the comment on _LANGDETECT_LOCK above. Without this lock, this
    function silently returns wrong results (not an exception) when
    called concurrently, which is far more dangerous than a crash.
    """

    try:

        with _LANGDETECT_LOCK:
            return detect_langs(
                text
            )

    except LangDetectException:

        return []


def _candidate_probability(
    candidates,
    language_code: str,
) -> float:

    for candidate in candidates:

        if candidate.lang == language_code:
            return float(
                candidate.prob
            )

    return 0.0


# =========================================================
# DEVANAGARI DETECTION
# =========================================================

def _detect_devanagari_language(
    text: str,
    candidates,
) -> str:
    """
    Distinguish Hindi and Marathi.

    Both use Devanagari, therefore script detection alone is not enough.

    Marathi lexical evidence is checked first. langdetect probabilities
    provide secondary evidence.
    """

    marathi_score = (
        _marathi_marker_score(
            text
        )
    )

    hi_probability = (
        _candidate_probability(
            candidates,
            "hi",
        )
    )

    mr_probability = (
        _candidate_probability(
            candidates,
            "mr",
        )
    )

    # -----------------------------------------------------
    # Strong Marathi lexical evidence
    # -----------------------------------------------------

    if marathi_score >= 2:

        return "mr"

    # -----------------------------------------------------
    # langdetect strongly prefers Marathi
    # -----------------------------------------------------

    if (
        mr_probability >= MIN_CONFIDENCE
        and mr_probability > hi_probability
    ):

        return "mr"

    # -----------------------------------------------------
    # langdetect supports Hindi
    # -----------------------------------------------------

    if hi_probability >= MIN_CONFIDENCE:

        return "hi"

    # -----------------------------------------------------
    # Weak Marathi evidence
    # -----------------------------------------------------

    if marathi_score >= 1:

        return "mr"

    # -----------------------------------------------------
    # Conservative fallback
    # -----------------------------------------------------
    #
    # CXIQ currently supports Hindi and Marathi for Devanagari reviews.
    # If no Marathi evidence exists, Hindi is the safer default for a
    # short Devanagari customer review.
    # -----------------------------------------------------

    return "hi"


# =========================================================
# LATIN-SCRIPT DETECTION
# =========================================================

def _detect_latin_language(
    text: str,
    candidates,
) -> str:
    """
    Detect English / Spanish / French.

    Unlike the previous implementation, this does NOT simply search the
    candidate list for any supported language and promote a weak
    second-place candidate.
    """

    if not candidates:

        return "en"

    top = candidates[0]

    # -----------------------------------------------------
    # Top result is supported
    # -----------------------------------------------------

    if top.lang in (
        "en",
        "es",
        "fr",
    ):

        # English can safely remain English.
        if top.lang == "en":

            return "en"

        # Spanish/French require minimum confidence.
        if top.prob >= MIN_CONFIDENCE:

            return top.lang

        return "en"

    # -----------------------------------------------------
    # Top result unsupported
    # -----------------------------------------------------
    #
    # Do not automatically promote a lower supported candidate.
    # That behaviour was one cause of incorrect classifications.
    # -----------------------------------------------------

    logger.info(
        (
            "Language detection: unsupported top candidate "
            "%s %.2f for %r; defaulting to English."
        ),
        top.lang,
        top.prob,
        text[:60],
    )

    return "en"


# =========================================================
# PUBLIC LANGUAGE DETECTOR
# =========================================================

def detect_language(
    text: str,
) -> Dict:
    """
    Returns:

        {
            "code":
                "en" | "hi" | "mr" |
                "es" | "fr" | "hi-en",

            "name":
                "English" | "Hindi" |
                "Marathi" | "Spanish" |
                "French" | "Hinglish",

            "is_supported": bool,

            "is_code_mixed": bool
        }
    """

    text = (
        text or ""
    ).strip()

    # =====================================================
    # EMPTY INPUT
    # =====================================================

    if not text:

        return {
            "code": "en",
            "name": "English",
            "is_supported": True,
            "is_code_mixed": False,
        }

    # =====================================================
    # HINGLISH
    # =====================================================

    hinglish_hits = (
        _hinglish_hits(
            text
        )
    )

    if hinglish_hits >= 2:

        return {
            "code": "hi-en",
            "name": "Hinglish",
            "is_supported": True,
            "is_code_mixed": True,
        }

    # =====================================================
    # VERY SHORT TEXT
    # =====================================================

    if (
        len(text)
        < MIN_CHARS_FOR_DETECTION
    ):

        # If it contains Devanagari, don't incorrectly force it to English.
        if _contains_devanagari(
            text
        ):

            code = (
                _detect_devanagari_language(
                    text,
                    [],
                )
            )

        else:

            code = "en"

    # =====================================================
    # NORMAL DETECTION
    # =====================================================

    else:

        candidates = (
            _safe_detect_candidates(
                text
            )
        )

        # -------------------------------------------------
        # Hindi / Marathi
        # -------------------------------------------------

        if _contains_devanagari(
            text
        ):

            code = (
                _detect_devanagari_language(
                    text,
                    candidates,
                )
            )

        # -------------------------------------------------
        # English / Spanish / French
        # -------------------------------------------------

        else:

            code = (
                _detect_latin_language(
                    text,
                    candidates,
                )
            )

    # =====================================================
    # RESULT
    # =====================================================

    name = SUPPORTED_LANGUAGES.get(
        code,
        "English",
    )

    return {
        "code": code,
        "name": name,
        "is_supported": True,
        "is_code_mixed": False,
    }