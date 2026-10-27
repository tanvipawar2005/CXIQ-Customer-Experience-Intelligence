"""
aspect_service.py

Aspect-Based Sentiment Analysis (ABSA).

ASPECT EXTRACTION:
RULE-BASED / DOMAIN-VOCABULARY HYBRID.

ASPECT-LEVEL SENTIMENT:
TRAINED, CONTEXT-AWARE CLASSIFIER — TF-IDF (1-3 grams) +
Logistic Regression, trained on the MAMS-ATSA dataset.

GRACEFUL FALLBACK:
If the trained ABSA model is unavailable, aspect-level sentiment falls
back to lexicon-based clause scoring.

Additional linguistic handling:
- ordinary negation
- balanced "neither...nor" neutral constructions
- noise filtering for fallback aspect extraction
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

from app.services.preprocessing import (
    split_sentences,
    split_clauses,
    tokenize,
)

from app.services.sentiment_service import (
    lexicon_score,
    is_balanced_neither_nor,
)

from app.services.absa_model_service import (
    get_absa_model_service,
)

from app.utils.lexicons import (
    DOMAIN_ASPECTS,
    SENTIMENT_LEXICON,
    INTENSIFIERS,
    NEGATIONS,
    EMOTION_LEXICON,
)


# =========================================================
# EMOTION WORDS ARE NEVER PRODUCT ASPECTS
# =========================================================

# Words like "sad", "happy", "disappointed" describe how the reviewer
# feels, not a feature of the product/service. Without this guard the
# fallback heuristic (which just looks at tokens near a sentiment word)
# can pick up a nearby emotion word and mislabel it as an aspect - e.g.
# "neither happy nor sad" incorrectly surfacing "Sad" as an aspect.
_EMOTION_WORDS = {
    word
    for words in EMOTION_LEXICON.values()
    for word in words
}


# =========================================================
# FALLBACK EXTRACTION STOPWORDS
# =========================================================

_STOPWORDS: Set[str] = {
    "the", "a", "an",
    "is", "was", "were", "are",
    "be", "been",

    "it", "its",

    "i", "we", "they", "he", "she",

    "this", "that", "these", "those",

    "to", "of", "in", "on", "for",

    "and", "but", "or",

    # Balanced conjunctions must never become aspects.
    "neither", "nor", "either",

    "with", "very", "so", "too",

    "not", "no",

    "really",

    "as", "at",

    "my", "our", "their",
    "you", "your",

    "have", "has", "had",

    "did", "do", "does",

    "will", "would", "could", "can",

    "just", "also",

    "then", "than",

    "there", "here",

    "which", "who", "what",
    "when", "where", "why", "how",

    "after", "before", "since",
    "during", "until", "within",
    "without",

    "about", "above", "below",
    "between", "through",
    "over", "under",

    "because", "although",
    "though", "while",

    "if", "yet", "still",

    "once", "again", "now",

    "some", "any", "all",

    "more", "most", "other",

    # Generic pronoun-like/noise words
    "nothing", "something",
    "anything", "everything",
    "none",
}


# =========================================================
# DOMAIN VOCABULARY MATCHING
# =========================================================

def _match_domain_aspects(
    clause_lower: str,
    domain: str,
) -> List:

    vocab = DOMAIN_ASPECTS.get(
        domain,
        DOMAIN_ASPECTS["other"],
    )

    matched = []

    for canonical, surface_forms in vocab.items():

        for form in surface_forms:

            if re.search(
                r"\b"
                + re.escape(form)
                + r"\b",
                clause_lower,
            ):

                matched.append(
                    (
                        canonical,
                        form,
                    )
                )

                break

    return matched


# =========================================================
# SENTIMENT LABEL
# =========================================================

def _sentiment_label(
    polarity: float,
) -> str:

    if polarity > 0.15:
        return "positive"

    if polarity < -0.15:
        return "negative"

    return "neutral"


# =========================================================
# VERB DENYLIST
# =========================================================

_VERB_DENYLIST: Set[str] = {
    "received",
    "ordered",
    "bought",
    "purchased",

    "arrived",
    "went",
    "came",
    "got",

    "using",
    "used",

    "bring",
    "brought",

    "gave",
    "given",

    "took",

    "make",
    "made",

    "try",
    "tried",

    "asked",
    "told",
    "said",

    "waited",
    "waiting",

    "paid",
    "pay",

    "charged",
    "deducted",

    "delivered",
    "returned",

    # Important fixes for previous false aspects.
    "became",
    "become",
    "becomes",
    "becoming",

    "felt",
    "feel",
    "feels",

    "seemed",
    "seem",
    "seems",

    "turned",
    "turn",
    "turns",

    "started",
    "start",
    "starts",

    "stopped",
    "stop",
    "stops",

    "worked",
    "works",
    "working",

    "broke",
    "breaks",
    "breaking",

    "died",
    "dies",
    "die",

    "lasted",
    "lasts",
    "lasting",

    "happened",
    "happens",
    "happen",

    "appeared",
    "appears",
    "appear",
}


# =========================================================
# PRONOUN / NOISE DENYLIST
# =========================================================

_PRONOUNS: Set[str] = {
    "everyone",
    "anyone",
    "someone",

    "everybody",
    "anybody",
    "somebody",

    "everything",
    "anything",
    "something",
    "nothing",

    "nobody",
    "none",

    "him",
    "her",
    "them",
    "us",
    "me",

    "myself",
    "yourself",
    "themselves",
}


# =========================================================
# FALLBACK NOUN CANDIDATES
# =========================================================

def _fallback_noun_candidates(
    clause_lower: str,
) -> List[str]:
    """
    When no controlled domain vocabulary matches, guess a candidate
    aspect from nearby tokens around sentiment-bearing words.

    This remains a lightweight heuristic fallback rather than a true
    POS-tagging noun extractor.
    """

    tokens = tokenize(
        clause_lower
    )

    candidates = []

    for idx, tok in enumerate(tokens):

        if tok not in SENTIMENT_LEXICON:
            continue

        # Look around sentiment-bearing words for plausible aspect terms.
        for offset in (
            -1,
            -2,
            1,
            2,
        ):

            j = idx + offset

            if not (
                0 <= j < len(tokens)
            ):
                continue

            candidate = tokens[j]

            if (
                candidate not in _STOPWORDS
                and candidate not in SENTIMENT_LEXICON
                and candidate not in _VERB_DENYLIST
                and candidate not in INTENSIFIERS
                and candidate not in NEGATIONS
                and candidate not in _PRONOUNS
                and candidate not in _EMOTION_WORDS

                and not candidate.endswith(
                    "ly"
                )

                and not candidate.endswith(
                    "ed"
                )

                and not candidate.endswith(
                    "ing"
                )

                and len(candidate) > 2
            ):

                candidates.append(
                    candidate
                )

    return candidates


# =========================================================
# NEGATION CHECK FOR CLAUSE
# =========================================================

def _clause_has_negation(
    clause: str,
) -> bool:

    tokens = tokenize(
        clause
    )

    return any(
        token in NEGATIONS
        or token == "not"

        for token in tokens
    )


# =========================================================
# ASPECT SENTIMENT
# =========================================================

def _calculate_aspect_sentiment(
    sentence: str,
    clause: str,
    surface_form: str,
    absa_model,
):
    """
    Calculate sentiment for one aspect mention.

    Priority:

    1. Explicit balanced "neither...nor" -> Neutral
    2. Trained ABSA model + lexicon blend
    3. Lexicon-only fallback
    """

    # -----------------------------------------------------
    # BALANCED NEITHER...NOR
    # -----------------------------------------------------

    if is_balanced_neither_nor(
        clause
    ):

        return (
            "neutral",
            0.90,
        )

    # -----------------------------------------------------
    # LEXICON
    # -----------------------------------------------------

    lex_pol, _ = lexicon_score(
        clause
    )

    # -----------------------------------------------------
    # TRAINED ABSA MODEL
    # -----------------------------------------------------

    model_result = None

    if absa_model.is_ready():

        model_result = absa_model.predict(
            sentence,
            surface_form,
        )

    if model_result:

        model_polarity = {
            "positive": 1.0,
            "negative": -1.0,
            "neutral": 0.0,
        }[
            model_result["label"]
        ] * model_result["confidence"]

        has_negation = _clause_has_negation(
            clause
        )

        # Explicit negation is strong linguistic evidence.
        # The ABSA model was trained on restaurant data, so the
        # lexicon gets more influence for clear negated expressions.
        if (
            has_negation
            and abs(lex_pol) > 0.05
        ):

            blended_polarity = (
                0.35 * model_polarity
                + 0.65 * lex_pol
            )

        else:

            blended_polarity = (
                0.60 * model_polarity
                + 0.40 * lex_pol
            )

        label = _sentiment_label(
            blended_polarity
        )

        confidence = round(
            min(
                0.5
                + abs(blended_polarity)
                * 0.5,
                0.97,
            ),
            4,
        )

        return (
            label,
            confidence,
        )

    # -----------------------------------------------------
    # LEXICON FALLBACK
    # -----------------------------------------------------

    blended_polarity = lex_pol

    label = _sentiment_label(
        blended_polarity
    )

    confidence = min(
        0.55
        + abs(blended_polarity)
        * 0.45,
        0.97,
    )

    return (
        label,
        confidence,
    )


# =========================================================
# PUBLIC ASPECT EXTRACTION
# =========================================================

def extract_aspects(
    text: str,
    domain: str = "other",
) -> List[Dict]:

    domain = (
        domain
        if domain in DOMAIN_ASPECTS
        else "other"
    )

    aggregated: Dict[
        str,
        Dict,
    ] = {}

    absa_model = (
        get_absa_model_service()
    )

    # =====================================================
    # SENTENCES / CLAUSES
    # =====================================================

    for sentence in split_sentences(
        text
    ):

        for clause in split_clauses(
            sentence
        ):

            clause_lower = (
                clause.lower()
            )

            # =================================================
            # DOMAIN MATCHING
            # =================================================

            if domain == "other":

                # For an unspecified domain, first try every
                # specific domain vocabulary.
                matches = []

                for specific_domain in DOMAIN_ASPECTS:

                    if specific_domain == "other":
                        continue

                    matches = (
                        _match_domain_aspects(
                            clause_lower,
                            specific_domain,
                        )
                    )

                    if matches:
                        break

                # Only use generic vocabulary when no specific
                # domain vocabulary matched.
                if not matches:

                    matches = (
                        _match_domain_aspects(
                            clause_lower,
                            "other",
                        )
                    )

            else:

                matches = (
                    _match_domain_aspects(
                        clause_lower,
                        domain,
                    )
                )

            # =================================================
            # FALLBACK ASPECT EXTRACTION
            # =================================================

            if not matches:

                fallback_candidates = set(
                    _fallback_noun_candidates(
                        clause_lower
                    )
                )

                for candidate in fallback_candidates:

                    # Final defensive check.
                    if (
                        candidate in _STOPWORDS
                        or candidate in _PRONOUNS
                        or candidate in _VERB_DENYLIST
                        or candidate in _EMOTION_WORDS
                    ):
                        continue

                    matches.append(
                        (
                            candidate.capitalize(),
                            candidate,
                        )
                    )

            if not matches:
                continue

            # =================================================
            # SENTIMENT FOR EACH MATCHED ASPECT
            # =================================================

            for (
                canonical,
                surface_form,
            ) in matches:

                label, confidence = (
                    _calculate_aspect_sentiment(
                        sentence=sentence,
                        clause=clause,
                        surface_form=surface_form,
                        absa_model=absa_model,
                    )
                )

                entry = aggregated.setdefault(
                    canonical,
                    {
                        "aspect": canonical,
                        "labels": [],
                        "confidences": [],
                        "mentions": set(),
                    },
                )

                entry[
                    "labels"
                ].append(
                    label
                )

                entry[
                    "confidences"
                ].append(
                    confidence
                )

                entry[
                    "mentions"
                ].add(
                    surface_form
                )

    # =====================================================
    # AGGREGATE MULTIPLE MENTIONS
    # =====================================================

    results = []

    for canonical, data in aggregated.items():

        label_scores: Dict[
            str,
            List[float],
        ] = {}

        for label, confidence in zip(
            data["labels"],
            data["confidences"],
        ):

            label_scores.setdefault(
                label,
                [],
            ).append(
                confidence
            )

        final_label = max(
            label_scores,

            key=lambda current_label: (
                len(
                    label_scores[
                        current_label
                    ]
                ),

                sum(
                    label_scores[
                        current_label
                    ]
                ),
            ),
        )

        final_confidence = round(
            sum(
                label_scores[
                    final_label
                ]
            )
            / len(
                label_scores[
                    final_label
                ]
            ),
            4,
        )

        results.append({
            "aspect": canonical,

            "sentiment": final_label,

            "confidence": final_confidence,

            "mentions": sorted(
                data["mentions"]
            ),
        })

    # =====================================================
    # SORT
    # =====================================================

    results.sort(
        key=lambda result: (
            abs(
                result["confidence"]
                - 0.5
            )
        ),
        reverse=True,
    )

    return results