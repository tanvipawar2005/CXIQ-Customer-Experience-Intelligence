"""
emotion_service.py

MODEL TYPE:
Rule-based emotion detection using emotion lexicons, negation awareness,
and the already-computed overall sentiment as a secondary signal.

Emotion labels:

    Joy
    Love
    Anger
    Sadness
    Fear
    Surprise

If no meaningful emotion evidence exists, Neutral is returned.

Important:
Overall sentiment is a secondary signal only. It must not create a strong
emotion prediction that contradicts explicit negated language.
"""

from __future__ import annotations

import re
from typing import Dict

from app.services.preprocessing import tokenize
from app.services.sentiment_service import is_balanced_neither_nor
from app.utils.lexicons import (
    EMOTION_LEXICON,
    NEGATIONS,
    NEGATION_WINDOW,
)


# =========================================================
# WORD -> EMOTION LOOKUP
# =========================================================

_WORD_TO_EMOTION = {}

for emotion, words in EMOTION_LEXICON.items():

    for word in words:

        _WORD_TO_EMOTION[
            word
        ] = emotion


# =========================================================
# NEGATED EMOTION MAPPING
# =========================================================

_OPPOSITE = {
    "Joy": "Sadness",
    "Love": "Sadness",
    "Anger": "Joy",
    "Sadness": "Joy",
    "Fear": "Joy",
    "Surprise": "Surprise",
}


# =========================================================
# COMMON PREFERENCE EXPRESSIONS
# =========================================================

# These are not necessarily "emotion words", but in customer feedback
# they are useful supporting evidence.

_POSITIVE_PREFERENCE = {
    "like",
    "liked",
    "likes",
    "enjoy",
    "enjoyed",
    "enjoys",
}


_NEGATIVE_PREFERENCE = {
    "dislike",
    "disliked",
    "dislikes",
    "hate",
    "hated",
}


# =========================================================
# CONTRACTION NORMALIZATION
# =========================================================

def _normalize_negations(
    text: str,
) -> str:

    text = text or ""

    replacements = {
        r"\bdon['’]t\b": "do not",
        r"\bdoesn['’]t\b": "does not",
        r"\bdidn['’]t\b": "did not",

        r"\bisn['’]t\b": "is not",
        r"\baren['’]t\b": "are not",

        r"\bwasn['’]t\b": "was not",
        r"\bweren['’]t\b": "were not",

        r"\bhasn['’]t\b": "has not",
        r"\bhaven['’]t\b": "have not",
        r"\bhadn['’]t\b": "had not",

        r"\bcan['’]t\b": "can not",
        r"\bcannot\b": "can not",

        r"\bwon['’]t\b": "will not",

        r"\bwouldn['’]t\b": "would not",
        r"\bcouldn['’]t\b": "could not",
        r"\bshouldn['’]t\b": "should not",
    }

    for pattern, replacement in replacements.items():

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    return text


# =========================================================
# NEGATION CHECK
# =========================================================

def _is_negated(
    tokens,
    index: int,
) -> bool:

    start = max(
        0,
        index - NEGATION_WINDOW,
    )

    return any(
        tokens[j] in NEGATIONS
        or tokens[j] == "not"

        for j in range(
            start,
            index,
        )
    )


# =========================================================
# MAIN FUNCTION
# =========================================================

def detect_emotion(
    text: str,
    overall_sentiment: Dict | None = None,
) -> Dict:

    # =====================================================
    # EXPLICIT BALANCED NEUTRAL CONSTRUCTION
    # =====================================================

    # "neither happy nor sad" would otherwise count as one Joy hit and
    # one Sadness hit; a tie is resolved arbitrarily by dict order,
    # which can produce a confident (and wrong) emotion label. When the
    # text is a genuine balanced "neither...nor" evaluation, treat the
    # emotion as Neutral rather than guessing between the two poles.
    if is_balanced_neither_nor(text):

        return {
            "label": "Neutral",

            "confidence": 0.85,

            "distribution": {
                emotion: round(
                    1 / len(EMOTION_LEXICON),
                    4,
                )

                for emotion in EMOTION_LEXICON
            },
        }

    normalized = _normalize_negations(
        text
    )

    tokens = tokenize(
        normalized
    )

    counts = {
        emotion: 0.0
        for emotion
        in EMOTION_LEXICON
    }

    explicit_hits = 0

    # =====================================================
    # EXPLICIT EMOTION WORDS
    # =====================================================

    for i, tok in enumerate(tokens):

        emotion = _WORD_TO_EMOTION.get(
            tok
        )

        if emotion is None:
            continue

        negated = _is_negated(
            tokens,
            i,
        )

        target = (
            _OPPOSITE.get(
                emotion,
                emotion,
            )
            if negated
            else emotion
        )

        counts[target] += 1.0

        explicit_hits += 1

    # =====================================================
    # PREFERENCE EXPRESSIONS
    # =====================================================

    preference_hits = 0

    for i, tok in enumerate(tokens):

        # ---------------------------------------------
        # like / enjoy
        # ---------------------------------------------

        if tok in _POSITIVE_PREFERENCE:

            negated = _is_negated(
                tokens,
                i,
            )

            if negated:

                counts["Sadness"] += 0.85

            else:

                counts["Joy"] += 0.70

            preference_hits += 1

        # ---------------------------------------------
        # dislike / hate
        # ---------------------------------------------

        elif tok in _NEGATIVE_PREFERENCE:

            negated = _is_negated(
                tokens,
                i,
            )

            if negated:

                counts["Joy"] += 0.60

            else:

                counts["Anger"] += 0.85

            preference_hits += 1

    # =====================================================
    # SECONDARY OVERALL-SENTIMENT SIGNAL
    # =====================================================

    total_direct_hits = (
        explicit_hits
        + preference_hits
    )

    if overall_sentiment is not None:

        sentiment_label = overall_sentiment.get(
            "label"
        )

        sentiment_confidence = float(
            overall_sentiment.get(
                "confidence",
                0.5,
            )
        )

        # If there is NO direct emotion/preference evidence,
        # overall sentiment can provide only a weak emotional hint.
        if total_direct_hits == 0:

            if sentiment_label == "negative":

                counts["Sadness"] += (
                    sentiment_confidence * 0.55
                )

            elif sentiment_label == "positive":

                counts["Joy"] += (
                    sentiment_confidence * 0.55
                )

        # If there is exactly one direct signal, overall sentiment
        # may support it, but should not dominate it.
        elif total_direct_hits == 1:

            if sentiment_label == "negative":

                counts["Sadness"] += (
                    sentiment_confidence * 0.30
                )

            elif sentiment_label == "positive":

                counts["Joy"] += (
                    sentiment_confidence * 0.30
                )

    # =====================================================
    # DISTRIBUTION
    # =====================================================

    total = sum(
        counts.values()
    )

    if total == 0:

        return {
            "label": "Neutral",

            "confidence": 0.55,

            "distribution": {
                emotion: round(
                    1 / len(
                        EMOTION_LEXICON
                    ),
                    4,
                )

                for emotion
                in EMOTION_LEXICON
            },
        }

    distribution = {
        emotion: round(
            value / total,
            4,
        )

        for emotion, value
        in counts.items()
    }

    top_emotion = max(
        distribution,
        key=distribution.get,
    )

    confidence = min(
        0.5
        + distribution[top_emotion]
        * 0.5,
        0.97,
    )

    confidence = round(
        confidence,
        4,
    )

    return {
        "label": top_emotion,

        "confidence": confidence,

        "distribution": distribution,
    }