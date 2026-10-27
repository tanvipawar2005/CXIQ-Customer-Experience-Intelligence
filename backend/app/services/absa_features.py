"""
absa_features.py

Shared feature-extraction logic for the context-aware aspect-sentiment
model. Used by BOTH scripts/train_absa_model.py (training) and
absa_model_service.py (live inference) so the exact same feature
construction happens in both places — a classic and easy-to-miss source of
bugs is computing features slightly differently at train vs. serve time.

See scripts/train_absa_model.py for the full rationale behind using a local
context window instead of whole-sentence bag-of-words.
"""
from __future__ import annotations
import re
from typing import Optional

WINDOW_SIZE = 6  # words of context on each side of the aspect term

_WORD_RE = re.compile(r"\S+")

# Contrastive/coordinating boundary words: a context window should not cross
# these, because they typically mark a shift to a DIFFERENT aspect's
# sentiment ("camera is great BUT battery drains fast" — words on the far
# side of "but" don't describe the battery). Without this constraint, short
# multi-aspect sentences can leak one aspect's sentiment words into another
# aspect's window. This boundary list applies uniformly to every aspect and
# every sentence — it is a general linguistic constraint, not tuned to any
# specific example.
_BOUNDARY_WORDS = {
    "but", "however", "although", "though", "yet", "while", "whereas",
    "nevertheless", "except", "unless",
}
_CLAUSE_END_PUNCT = (",", ";", ".", "!", "?", ":")


def _is_boundary_word(word: str) -> bool:
    return word.strip(".,;:!?").lower() in _BOUNDARY_WORDS


def build_context_window(
    sentence: str,
    aspect_term: str,
    from_idx: Optional[int] = None,
    to_idx: Optional[int] = None,
    window: int = WINDOW_SIZE,
) -> str:
    """
    Extracts up to `window` words before and after the aspect term — but
    never crossing a contrastive boundary word (but/however/although/...)
    or clause-ending punctuation — and returns them as a single string with
    the aspect term repeated at the front, so the model always has a clear
    signal of which aspect this example is about.

    If from_idx/to_idx aren't provided, the aspect term's first
    case-insensitive occurrence in the sentence is located automatically
    (used at inference time, where we don't already have offsets the way
    the training data provides them).
    """
    if from_idx is None or to_idx is None:
        match = re.search(re.escape(aspect_term), sentence, re.IGNORECASE)
        if match:
            from_idx, to_idx = match.start(), match.end()
        else:
            from_idx, to_idx = 0, len(aspect_term)

    matches = list(_WORD_RE.finditer(sentence))
    aspect_word_indices = [
        i for i, m in enumerate(matches)
        if not (m.end() <= from_idx or m.start() >= to_idx)
    ]
    if not aspect_word_indices:
        return f"{aspect_term.lower()} | {sentence.lower()}"

    # expand left, stopping at a boundary word or just past clause-ending punctuation
    start = aspect_word_indices[0]
    i = start - 1
    steps = 0
    while i >= 0 and steps < window:
        w = matches[i].group(0)
        if _is_boundary_word(w):
            break
        start = i
        steps += 1
        if w.rstrip().endswith(_CLAUSE_END_PUNCT):
            break
        i -= 1

    # expand right, stopping at a boundary word or just past clause-ending punctuation
    end = aspect_word_indices[-1] + 1
    i = end
    steps = 0
    while i < len(matches) and steps < window:
        w = matches[i].group(0)
        if _is_boundary_word(w):
            break
        end = i + 1
        steps += 1
        if w.rstrip().endswith(_CLAUSE_END_PUNCT):
            break
        i += 1

    window_words = [matches[j].group(0) for j in range(start, end)]
    window_text = " ".join(window_words).lower()
    return f"{aspect_term.lower()} | {window_text}"
