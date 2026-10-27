"""
absa_model_service.py

Live inference wrapper around the trained context-aware aspect-sentiment
model (see scripts/train_absa_model.py for how it was trained, and
docs/absa_model_evaluation.md for its real, measured test-set metrics).

GRACEFUL DEGRADATION: if the trained model file isn't present (e.g. a fresh
clone where scripts/train_absa_model.py hasn't been run), this service
reports itself as unavailable and aspect_service.py falls back to the
original lexicon-based clause scoring — the app still works, it just uses
the less context-aware method until the model is trained.
"""
from __future__ import annotations
import os
import threading
from typing import Dict, Optional

import joblib

from app.services.absa_features import build_context_window

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "absa_context_lr.joblib")

_lock = threading.Lock()


class AbsaModelService:
    _instance: Optional["AbsaModelService"] = None

    def __init__(self):
        self.pipeline = None
        self.labels = None
        if os.path.exists(MODEL_PATH):
            try:
                bundle = joblib.load(MODEL_PATH)
                self.pipeline = bundle["pipeline"]
                self.labels = bundle["labels"]
            except Exception:
                self.pipeline = None

    @classmethod
    def get_instance(cls) -> "AbsaModelService":
        with _lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def is_ready(self) -> bool:
        return self.pipeline is not None

    def predict(self, sentence: str, aspect_term: str) -> Optional[Dict]:
        """Returns {"label", "confidence", "scores"} for how the given
        aspect term is discussed in `sentence`, using its real surrounding
        context — or None if the model isn't trained/loaded, in which case
        the caller should fall back to the lexicon-based approach."""
        if not self.is_ready():
            return None
        feature_text = build_context_window(sentence, aspect_term)
        proba = self.pipeline.predict_proba([feature_text])[0]
        classes = list(self.pipeline.classes_)
        scores = {cls: float(p) for cls, p in zip(classes, proba)}
        label = max(scores, key=scores.get)
        return {
            "label": label,
            "confidence": round(scores[label], 4),
            "scores": {k: round(v, 4) for k, v in scores.items()},
        }


def get_absa_model_service() -> AbsaModelService:
    return AbsaModelService.get_instance()
