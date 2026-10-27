"""
sentiment_service.py

Overall sentiment classification.

Model type: PRETRAINED-STYLE CLASSICAL ML (TF-IDF + Logistic Regression),
trained on a bundled labeled dataset at backend/data/training/sentiment_train.csv
the first time the service is used, then cached to disk as a joblib artifact
(backend/app/models/sentiment_lr.joblib).

The trained classifier is blended with a transparent lexicon signal.

Additional linguistic handling covers:
- ordinary negation: "not good", "not bad"
- contractions: "don't like", "didn't enjoy"
- preference verbs: like, enjoy, dislike
- balanced constructions: "neither good nor bad"

Public interface remains unchanged:

    SentimentService.predict(text) -> dict
"""

from __future__ import annotations

import os
import re
import threading
from typing import Dict, List, Tuple

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.services.preprocessing import tokenize, clean_text, split_clauses
from app.utils.lexicons import (
    SENTIMENT_LEXICON,
    INTENSIFIERS,
    NEGATIONS,
    NEGATION_WINDOW,
    EMOTION_LEXICON,
)


# =========================================================
# EMOTION WORDS ARE ALSO SENTIMENT-BEARING
# =========================================================

# "happy", "sad", "angry", "disappointed" etc. live in EMOTION_LEXICON
# rather than SENTIMENT_LEXICON, but they are just as sentiment-bearing.
# Balanced constructions such as "neither happy nor sad" must be
# recognised using this combined vocabulary, not SENTIMENT_LEXICON alone.
_EMOTION_WORDS = {
    word
    for words in EMOTION_LEXICON.values()
    for word in words
}


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "sentiment_lr.joblib",
)

TRAIN_DATA_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    "data",
    "training",
    "sentiment_train.csv",
)

_lock = threading.Lock()


# =========================================================
# COMMON CUSTOMER-PREFERENCE WORDS
# =========================================================

# These may not exist in the compact sentiment lexicon, but they carry
# useful sentiment in customer reviews.

_PREFERENCE_POSITIVE = {
    "like": 0.55,
    "likes": 0.55,
    "liked": 0.55,

    "enjoy": 0.65,
    "enjoys": 0.65,
    "enjoyed": 0.65,

    "prefer": 0.45,
    "prefers": 0.45,
    "preferred": 0.45,
}

_PREFERENCE_NEGATIVE = {
    "dislike": -0.65,
    "dislikes": -0.65,
    "disliked": -0.65,

    # Scarcity / insufficiency expressions common in reviews
    "few": -0.40,
    "limited": -0.50,
    "insufficient": -0.65,
    "scarce": -0.50,
}


# =========================================================
# CONTRACTION NORMALIZATION
# =========================================================

def _normalize_negation_text(text: str) -> str:
    """
    Normalize common English contractions.

    Examples:
        don't   -> do not
        doesn't -> does not
        didn't  -> did not
        isn't   -> is not
        wasn't  -> was not
        can't   -> can not
    """

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

        r"\bwon['’]t\b": "will not",
        r"\bwouldn['’]t\b": "would not",

        r"\bcan['’]t\b": "can not",
        r"\bcannot\b": "can not",

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
# BALANCED NEITHER...NOR
# =========================================================

def _count_sentiment_hits(tokens: List[str]) -> int:

    hits = 0

    for token in tokens:

        if (
            token in SENTIMENT_LEXICON
            or token in _PREFERENCE_POSITIVE
            or token in _PREFERENCE_NEGATIVE
            or token in _EMOTION_WORDS
        ):
            hits += 1

    return hits


def _clause_has_neither_nor_match(clause: str):

    return re.search(
        r"\bneither\b(.{0,80}?)\bnor\b(.{0,80})",
        clause,
    )


def is_balanced_neither_nor(text: str) -> bool:
    """
    Detect balanced constructions such as:

        neither good nor bad
        neither excellent nor terrible
        neither helpful nor useless

    In customer-feedback language these usually indicate a neutral /
    middle evaluation rather than two independent sentiments.

    The function verifies that sentiment-bearing words occur in the
    construction so ordinary uses of "neither...nor" are not
    automatically forced to Neutral.

    It also works at the CLAUSE level: a "neither...nor" evaluation of
    one aspect must not swallow an unrelated clause elsewhere in the
    same review that carries its own independent sentiment (e.g.
    "the camera is neither the best nor the worst, but delivery was
    late and staff were rude" is NOT an overall-neutral review - only
    the camera clause is balanced). If any other clause in the text
    carries its own sentiment-bearing words, the text as a whole is
    not treated as a balanced/neutral construction.
    """

    normalized = _normalize_negation_text(
        text
    ).lower()

    clauses = split_clauses(normalized) or [normalized]

    balanced_clause_found = False

    for clause in clauses:

        match = _clause_has_neither_nor_match(clause)

        if not match:
            continue

        relevant_text = (
            match.group(1)
            + " "
            + match.group(2)
        )

        relevant_tokens = tokenize(relevant_text)

        if _count_sentiment_hits(relevant_tokens) >= 2:
            balanced_clause_found = True

    if not balanced_clause_found:
        return False

    # A balanced clause was found. Now make sure no OTHER clause in the
    # same text carries its own, independent sentiment - otherwise this
    # is a mixed review, not a purely balanced/neutral one.
    for clause in clauses:

        if _clause_has_neither_nor_match(clause):
            continue

        if _count_sentiment_hits(tokenize(clause)) >= 1:
            return False

    return True


# =========================================================
# SENTIMENT WEIGHT
# =========================================================

def _sentiment_weight(token: str):
    """
    Return the sentiment weight for a token.
    """

    if token in SENTIMENT_LEXICON:
        return SENTIMENT_LEXICON[token]

    if token in _PREFERENCE_POSITIVE:
        return _PREFERENCE_POSITIVE[token]

    if token in _PREFERENCE_NEGATIVE:
        return _PREFERENCE_NEGATIVE[token]

    return None


# =========================================================
# NEGATION DETECTION
# =========================================================

def _is_negated(
    tokens: List[str],
    index: int,
) -> bool:
    """
    Check whether a sentiment-bearing token is affected by a recent
    negation.
    """

    start = max(
        0,
        index - NEGATION_WINDOW,
    )

    for j in range(start, index):

        if (
            tokens[j] in NEGATIONS
            or tokens[j] == "not"
        ):
            return True

    return False


# =========================================================
# LEXICON SCORE
# =========================================================

def lexicon_score(
    text: str,
) -> Tuple[float, List[Dict]]:
    """
    Return:
        (
            aggregate polarity in [-1, 1],
            token-level contributions
        )

    Examples:
        good       -> positive
        bad        -> negative
        not good   -> negative
        not bad    -> positive
        like       -> positive
        don't like -> negative
    """

    # Balanced neutral construction must be handled before independent
    # positive/negative words are scored.
    if is_balanced_neither_nor(text):

        return 0.0, [{
            "token": "neither...nor",
            "weight": 0.0,
            "negated": True,
        }]

    normalized = _normalize_negation_text(
        text
    )

    tokens = tokenize(
        normalized
    )

    contributions = []

    total = 0.0
    count = 0

    for i, tok in enumerate(tokens):

        # Negation words are operators, not sentiment-bearing words.
        if (
            tok in NEGATIONS
            or tok == "not"
        ):
            continue

        weight = _sentiment_weight(
            tok
        )

        if weight is None:
            continue

        scale = 1.0

        # -------------------------------------------------
        # Intensifiers
        # -------------------------------------------------

        for back in range(
            1,
            NEGATION_WINDOW + 1,
        ):

            j = i - back

            if j < 0:
                break

            previous = tokens[j]

            if previous in INTENSIFIERS:
                scale *= INTENSIFIERS[previous]

        # -------------------------------------------------
        # Negation
        # -------------------------------------------------

        negated = _is_negated(
            tokens,
            i,
        )

        final_weight = (
            weight
            * scale
            * (-1 if negated else 1)
        )

        final_weight = max(
            -1.0,
            min(
                1.0,
                final_weight,
            ),
        )

        total += final_weight
        count += 1

        contributions.append({
            "token": tok,
            "weight": round(
                final_weight,
                3,
            ),
            "negated": negated,
        })

    if count == 0:
        return 0.0, contributions

    avg = total / count

    avg = max(
        -1.0,
        min(
            1.0,
            avg,
        ),
    )

    return avg, contributions


# =========================================================
# CLEAR NEGATED SENTIMENT
# =========================================================

def _has_clear_negated_sentiment(
    contributions: List[Dict],
) -> bool:
    """
    True when an actual sentiment-bearing expression was explicitly
    negated.

    Examples:
        not good
        not bad
        don't like
        didn't enjoy
    """

    return any(
        item.get(
            "negated",
            False,
        )
        for item in contributions
    )


# =========================================================
# SENTIMENT SERVICE
# =========================================================

class SentimentService:

    _instance = None

    def __init__(self):

        self.pipeline: Pipeline | None = None

        self._load_or_train()

    @classmethod
    def get_instance(
        cls,
    ) -> "SentimentService":

        with _lock:

            if cls._instance is None:
                cls._instance = cls()

        return cls._instance

    # -----------------------------------------------------
    # Load existing model or train
    # -----------------------------------------------------

    def _load_or_train(self):

        if os.path.exists(
            MODEL_PATH
        ):

            try:

                self.pipeline = joblib.load(
                    MODEL_PATH
                )

                return

            except Exception:
                pass

        self._train()

    # -----------------------------------------------------
    # Train model
    # -----------------------------------------------------

    def _train(self):

        if not os.path.exists(
            TRAIN_DATA_PATH
        ):

            self.pipeline = None
            return

        df = pd.read_csv(
            TRAIN_DATA_PATH
        )

        df = df.dropna(
            subset=[
                "text",
                "label",
            ]
        )

        pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=8000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    C=4.0,
                    class_weight="balanced",
                ),
            ),
        ])

        pipeline.fit(
            df["text"].astype(str),
            df["label"].astype(str),
        )

        os.makedirs(
            os.path.dirname(
                MODEL_PATH
            ),
            exist_ok=True,
        )

        joblib.dump(
            pipeline,
            MODEL_PATH,
        )

        self.pipeline = pipeline

    # -----------------------------------------------------
    # Model ready?
    # -----------------------------------------------------

    def is_ready(self) -> bool:

        return self.pipeline is not None

    # -----------------------------------------------------
    # Predict
    # -----------------------------------------------------

    def predict(
        self,
        text: str,
    ) -> Dict:

        original_text = (
            text or ""
        ).strip()

        cleaned_text = clean_text(
            original_text
        )

        lex_pol, contributions = lexicon_score(
            original_text
        )

        # =================================================
        # EXPLICIT BALANCED NEUTRAL CONSTRUCTION
        # =================================================

        # The trained bag-of-ngrams model can easily choose Positive
        # because of "good" or Negative because of "bad".
        # Grammatically, however, "neither good nor bad" is neutral.
        if is_balanced_neither_nor(
            original_text
        ):

            return {
                "label": "neutral",

                "confidence": 0.90,

                "scores": {
                    "positive": 0.05,
                    "neutral": 0.90,
                    "negative": 0.05,
                },

                "lexicon_polarity": 0.0,

                "token_contributions": contributions,
            }

        clear_negation = (
            _has_clear_negated_sentiment(
                contributions
            )
        )

        # =================================================
        # ML + LEXICON
        # =================================================

        if self.pipeline is not None:

            proba = self.pipeline.predict_proba(
                [cleaned_text]
            )[0]

            classes = list(
                self.pipeline.classes_
            )

            ml_scores = {
                cls: float(probability)
                for cls, probability
                in zip(classes, proba)
            }

            for label_name in (
                "positive",
                "neutral",
                "negative",
            ):

                ml_scores.setdefault(
                    label_name,
                    0.0,
                )

            blend = dict(
                ml_scores
            )

            # ---------------------------------------------
            # Lexicon strength
            # ---------------------------------------------

            if clear_negation:

                # Explicit linguistic negation deserves more influence
                # than ordinary isolated lexicon words.
                lex_strength = min(
                    0.75
                    + abs(lex_pol) * 0.45,
                    1.15,
                )

            else:

                lex_strength = min(
                    abs(lex_pol) * 1.8,
                    1.0,
                )

            # ---------------------------------------------
            # Apply lexicon evidence
            # ---------------------------------------------

            if lex_pol > 0.1:

                blend["positive"] += (
                    lex_strength
                )

                blend["negative"] *= (
                    1
                    - min(
                        0.65 * lex_strength,
                        0.85,
                    )
                )

            elif lex_pol < -0.1:

                blend["negative"] += (
                    lex_strength
                )

                blend["positive"] *= (
                    1
                    - min(
                        0.65 * lex_strength,
                        0.85,
                    )
                )

            else:

                blend["neutral"] += 0.10

            # ---------------------------------------------
            # Normalize
            # ---------------------------------------------

            total = sum(
                blend.values()
            ) or 1.0

            blend = {
                key: value / total
                for key, value
                in blend.items()
            }

            label = max(
                blend,
                key=blend.get,
            )

            confidence = blend[
                label
            ]

            scores = blend

        # =================================================
        # PURE LEXICON FALLBACK
        # =================================================

        else:

            if lex_pol > 0.15:

                label = "positive"

                confidence = min(
                    0.55
                    + lex_pol / 2,
                    0.97,
                )

            elif lex_pol < -0.15:

                label = "negative"

                confidence = min(
                    0.55
                    + abs(lex_pol) / 2,
                    0.97,
                )

            else:

                label = "neutral"
                confidence = 0.55

            scores = {
                "positive": 0.0,
                "neutral": 0.0,
                "negative": 0.0,
            }

            scores[
                label
            ] = confidence

            remaining = (
                1 - confidence
            ) / 2

            for key in scores:

                if key != label:
                    scores[key] = remaining

        # =================================================
        # RESULT
        # =================================================

        return {
            "label": label,

            "confidence": round(
                float(confidence),
                4,
            ),

            "scores": {
                key: round(
                    float(value),
                    4,
                )
                for key, value
                in scores.items()
            },

            "lexicon_polarity": round(
                lex_pol,
                4,
            ),

            "token_contributions": contributions,
        }


def get_sentiment_service() -> SentimentService:

    return SentimentService.get_instance()