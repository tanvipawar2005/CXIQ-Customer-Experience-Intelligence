"""
translation_service.py

Converts non-English customer feedback into English before it is passed
through CXIQ's existing English NLP pipeline.

Translation flow:

    English
       |
       +----> No translation required
                    |
                    v
                 CXIQ NLP


    Non-English
       |
       v
    MyMemory
       |
       +---- SUCCESS ---> English ---> CXIQ NLP
       |
       +---- FAILED
                  |
                  v
               Gemini
                  |
                  +---- SUCCESS ---> English ---> CXIQ NLP
                  |
                  +---- FAILED ---> Original text returned with "failed" status


IMPORTANT:

GoogleTranslator is NOT used.

Primary translator:
    MyMemory

Fallback translator:
    Gemini

Gemini translation is only a translation fallback. Sentiment, emotion,
aspect, priority, issue radar, and CX score continue to be calculated by
CXIQ's existing NLP/ML pipeline.

Public function:

    translate_to_english(text, language_code)

Returns:

    (translated_text, status)

Status:
    "not_required"
    "translated"
    "failed"
"""

from __future__ import annotations

import concurrent.futures
import logging
import re
import threading
import time

from typing import Dict, Tuple

from app.services.gemini_service import translate_review


logger = logging.getLogger("cxiq")


# =========================================================
# CONFIGURATION
# =========================================================

MYMEMORY_TIMEOUT_SECONDS = 5.0

# MyMemory (and Gemini as its fallback) are third-party services with their
# own rate limits. During a batch upload, dashboard_service.process_batch
# analyzes many reviews concurrently (bounded thread pool) - most of that
# concurrency is fine (sentiment/aspect/emotion is all local CPU work), but
# firing off many SIMULTANEOUS translation requests is exactly what was
# causing "MyMemory failures followed by Gemini HTTP 429 quota errors" in a
# 15-review batch. This semaphore caps how many translation calls (to
# EITHER provider) are in flight at once, independent of how wide the
# overall batch thread pool is.
MAX_CONCURRENT_TRANSLATIONS = 3
_translation_semaphore = threading.Semaphore(MAX_CONCURRENT_TRANSLATIONS)

# Transient-failure retry policy. Only used for errors that look temporary
# (timeouts, connection resets, HTTP 429/5xx) - not for "this text/language
# genuinely can't be translated" type failures, which retrying wouldn't fix.
MAX_RETRIES = 2
RETRY_BACKOFF_BASE_SECONDS = 0.75


# =========================================================
# LANGUAGE CODES
# =========================================================

MYMEMORY_LANGUAGE_CODES = {
    "hi": "hi-IN",
    "mr": "mr-IN",
    "es": "es-ES",
    "fr": "fr-FR",
    "en": "en-GB",
}


# =========================================================
# HINGLISH / ROMANIZED HINDI-MARATHI NORMALIZATION
# =========================================================

_SLANG_MAP = {
    # Hindi / Hinglish
    "mast": "great",
    "ekdum": "absolutely",
    "bakwas": "terrible",

    "theek": "okay",

    "accha": "good",
    "acha": "good",
    "achha": "good",

    "sahi": "good",

    "kharab": "bad",

    "badiya": "great",

    "jaldi": "quickly",
    "der": "late",

    "paisa": "money",
    "paise": "money",

    "bahut": "very",
    "bohot": "very",
    "bhot": "very",

    # Negation
    "nahi": "not",
    "nahin": "not",
    "nahiin": "not",

    # Auxiliary verbs
    "hai": "is",
    "hain": "are",
    "tha": "was",
    "thi": "was",
    "the": "were",

    # Common filler / grammatical words
    "wala": "",
    "wali": "",
    "yaar": "",

    "bilkul": "absolutely",

    "zyada": "too much",
    "kam": "less",

    # Marathi / Romanized Marathi
    "khup": "very",

    "changla": "good",
    "changli": "good",
    "changle": "good",

    "lavkar": "quickly",

    "pan": "but",

    "sampte": "runs out",

    "aahe": "is",
    "aahet": "are",
}


_WORD_RE = re.compile(r"[A-Za-z']+")


def normalize_hinglish(text: str) -> str:
    """
    Best-effort normalization for common Hindi/Marathi words
    written using Latin characters.

    Example:

        "battery bahut acchi hai but speaker kharab hai"

    becomes approximately:

        "battery very good is but speaker bad is"

    This is intentionally lightweight. Gemini remains available as
    the fallback if MyMemory cannot translate code-mixed text.
    """

    def _replace(match: re.Match) -> str:

        word = match.group(0)

        replacement = _SLANG_MAP.get(
            word.lower()
        )

        if replacement is not None:
            return replacement

        return word

    normalized = _WORD_RE.sub(
        _replace,
        text,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    return normalized or text


# =========================================================
# TRANSLATION CACHE
# =========================================================

_cache: Dict[
    Tuple[str, str],
    Tuple[str, str],
] = {}

_cache_lock = threading.Lock()


# =========================================================
# MYMEMORY
# =========================================================

def _translate_with_mymemory(
    text: str,
    source: str,
) -> str:
    """
    Translate using MyMemory.

    MyMemory is CXIQ's PRIMARY translation provider.

    GoogleTranslator is intentionally not used.
    """

    from deep_translator import MyMemoryTranslator

    source_code = MYMEMORY_LANGUAGE_CODES.get(
        source,
        source,
    )

    translator = MyMemoryTranslator(
        source=source_code,
        target="en-GB",
    )

    result = translator.translate(text)

    if not result or not result.strip():
        raise ValueError(
            "MyMemory returned an empty translation."
        )

    return result.strip()


# =========================================================
# TRANSLATION QUALITY CHECK
# =========================================================

def _translation_looks_valid(
    original: str,
    translated: str,
) -> bool:
    """
    Perform lightweight sanity checks.

    This is NOT a language classifier.

    It only rejects obviously unusable translation responses such as:
    - empty strings
    - extremely short output for a normal review
    - responses that contain no alphabetic characters
    """

    if not translated:
        return False

    translated = translated.strip()

    if not translated:
        return False

    if len(original.strip()) >= 15 and len(translated) < 3:
        return False

    if not re.search(
        r"[A-Za-z]",
        translated,
    ):
        return False

    return True


# =========================================================
# TRANSIENT-FAILURE RETRY
# =========================================================

_TRANSIENT_MARKERS = (
    "429",
    "too many requests",
    "rate limit",
    "quota",
    "timeout",
    "timed out",
    "temporarily unavailable",
    "connection",
    "reset by peer",
    "503",
    "502",
    "500",
)


def _is_transient_error(exc: Exception) -> bool:
    """
    Best-effort check for whether an error looks temporary (rate limit,
    timeout, connection blip, transient 5xx) rather than a permanent
    failure (e.g. an unsupported language pair, or a genuinely malformed
    request). Only transient-looking errors are retried - retrying a
    permanent failure would just waste time and requests.
    """

    message = str(exc).lower()

    return any(marker in message for marker in _TRANSIENT_MARKERS)


def _call_with_retry(fn, *args, provider: str, **kwargs):
    """
    Call a translation provider function, retrying with a short backoff
    when the failure looks transient. This is what turns "one MyMemory
    hiccup instantly falls through to Gemini, which then also gets
    rate-limited" into "wait a moment and try the same provider again
    first" - reducing how often a busy batch upload has to lean on the
    fallback provider at all.
    """

    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):

        try:
            return fn(*args, **kwargs)

        except Exception as exc:  # noqa: BLE001 - genuinely provider-agnostic

            last_error = exc

            if (
                attempt < MAX_RETRIES
                and _is_transient_error(exc)
            ):
                backoff = RETRY_BACKOFF_BASE_SECONDS * (2 ** attempt)

                logger.info(
                    "Translation: %s attempt %d looked transient (%s), "
                    "retrying in %.2fs.",
                    provider,
                    attempt + 1,
                    exc,
                    backoff,
                )

                time.sleep(backoff)
                continue

            raise

    raise last_error  # pragma: no cover - loop always returns or raises


# =========================================================
# PUBLIC TRANSLATION FUNCTION
# =========================================================

def translate_to_english(
    text: str,
    language_code: str,
) -> Tuple[str, str]:
    """
    Translate customer feedback into English.

    Translation order:

        1. English -> no translation
        2. MyMemory
        3. Gemini fallback

    Returns:

        (translated_text, status)

    status:

        "not_required"
            English review.

        "translated"
            MyMemory or Gemini translated successfully.

        "failed"
            Both providers failed.
            Original text is returned.
    """

    # -----------------------------------------------------
    # Clean input
    # -----------------------------------------------------

    text = (text or "").strip()

    language_code = (
        language_code or "en"
    ).strip().lower()

    if not text:
        return text, "not_required"

    # -----------------------------------------------------
    # English
    # -----------------------------------------------------

    if language_code == "en":
        return text, "not_required"

    # -----------------------------------------------------
    # Cache
    # -----------------------------------------------------

    cache_key = (
        language_code,
        text,
    )

    with _cache_lock:
        cached = _cache.get(
            cache_key
        )

    if cached is not None:

        logger.debug(
            "Translation cache hit for language '%s'.",
            language_code,
        )

        return cached

    # -----------------------------------------------------
    # Prepare source
    # -----------------------------------------------------

    working_text = text
    source = language_code

    if language_code == "hi-en":

        working_text = normalize_hinglish(
            text
        )

        source = "hi"

    result: Tuple[str, str] = (
        text,
        "failed",
    )

    # A single semaphore-guarded "slot" covers BOTH providers for this
    # review, since MyMemory and Gemini are tried one after another for
    # the same request - this bounds how many translation requests (to
    # either service) are in flight across the whole batch at once.
    with _translation_semaphore:

        # =================================================
        # 1. MYMEMORY
        # =================================================

        try:

            logger.info(
                "Translation: trying MyMemory for '%s'.",
                language_code,
            )

            def _mymemory_call():

                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=1
                ) as executor:

                    future = executor.submit(
                        _translate_with_mymemory,
                        working_text,
                        source,
                    )

                    return future.result(
                        timeout=MYMEMORY_TIMEOUT_SECONDS
                    )

            translated = _call_with_retry(
                _mymemory_call,
                provider="MyMemory",
            )

            if not _translation_looks_valid(
                working_text,
                translated,
            ):
                raise ValueError(
                    "MyMemory returned an unusable translation."
                )

            result = (
                translated,
                "translated",
            )

            logger.info(
                "Translation: MyMemory succeeded for '%s'.",
                language_code,
            )

        except Exception as mymemory_error:

            logger.warning(
                "Translation: MyMemory failed for '%s': %s",
                language_code,
                mymemory_error,
            )

            # =============================================
            # 2. GEMINI FALLBACK
            # =============================================

            try:

                logger.info(
                    "Translation: falling back to Gemini for '%s'.",
                    language_code,
                )

                translated = _call_with_retry(
                    translate_review,
                    working_text,
                    language_code,
                    provider="Gemini",
                )

                if not _translation_looks_valid(
                    working_text,
                    translated,
                ):
                    raise ValueError(
                        "Gemini returned an unusable translation."
                    )

                result = (
                    translated,
                    "translated",
                )

                logger.info(
                    "Translation: Gemini succeeded for '%s'.",
                    language_code,
                )

            except Exception as gemini_error:

                logger.error(
                    "Translation: both MyMemory and Gemini failed "
                    "for '%s'. MyMemory=%s | Gemini=%s",
                    language_code,
                    mymemory_error,
                    gemini_error,
                )

                result = (
                    text,
                    "failed",
                )

    # -----------------------------------------------------
    # Cache result
    # -----------------------------------------------------

    # IMPORTANT: only SUCCESSFUL translations are cached. A "failed"
    # result used to be cached permanently, which meant a purely
    # transient hiccup (a timeout, a momentary rate limit) would
    # silently and permanently mark that exact review text as
    # untranslatable for the rest of the process's lifetime - even a
    # manual retry a minute later would just hit the stale cached
    # failure instead of actually trying again. Only caching successes
    # keeps the cache purely as a speed optimization, never as a
    # permanent record of a temporary problem.
    if result[1] != "failed":

        with _cache_lock:
            _cache[cache_key] = result

    return result