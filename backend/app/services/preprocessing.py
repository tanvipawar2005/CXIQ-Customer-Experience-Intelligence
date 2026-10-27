"""
preprocessing.py

Lightweight, dependency-free text preprocessing. We deliberately avoid heavy
NLP toolkits (spaCy / transformers) for this layer so the pipeline starts
instantly and runs anywhere, including CPU-only, offline environments.
"""
import re
from typing import List

_WORD_RE = re.compile(r"[A-Za-z']+")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_SPLIT_RE = re.compile(r"\s*(?:,|;|\bbut\b|\bhowever\b|\balthough\b|\byet\b|\bwhile\b|\band\b)\s*", re.IGNORECASE)


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]


def split_sentences(text: str) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    parts = _SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def split_clauses(sentence: str) -> List[str]:
    """Split a sentence into smaller clauses at contrast/coordination
    boundaries (but/however/and/,/;). This is what lets us separate
    'camera is great but battery is bad' into two aspect-bearing clauses."""
    parts = _CLAUSE_SPLIT_RE.split(sentence)
    return [p.strip() for p in parts if p.strip()]


def truncate_for_processing(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
