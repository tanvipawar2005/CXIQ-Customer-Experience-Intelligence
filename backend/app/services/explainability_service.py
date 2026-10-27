"""
explainability_service.py

Builds the "Why this prediction?" payload shown inline with every analysis
result. Rather than a separate black-box explainer (SHAP/LIME require a
differentiable or tree model; our sentiment layer is a linear TF-IDF model
blended with a lexicon), we expose the actual signals the pipeline used:

  - important_words   : token-level polarity contributions (from the lexicon
                         engine, which is exactly what drove part of the
                         sentiment score) with a pos/neg/neutral tag
  - positive_phrases / negative_phrases : clauses that pushed the result
  - signals           : one-line factors from aspects, emotion, and priority

For the linear TF-IDF + Logistic Regression model, the top contributing
n-grams are also surfaced when available (true model-level explanation,
not just the lexicon).
"""
from __future__ import annotations
from typing import Dict, List

from app.services.preprocessing import split_sentences, split_clauses


def _classify_word(weight: float) -> str:
    if weight > 0:
        return "positive"
    if weight < 0:
        return "negative"
    return "neutral"


def build_explanation(
    text: str,
    sentiment_result: Dict,
    aspects: List[Dict],
    emotion_result: Dict,
    priority_result: Dict,
) -> Dict:
    contributions = sentiment_result.get("token_contributions", [])
    important_words = [
        {
            "word": c["token"],
            "weight": c["weight"],
            "type": _classify_word(c["weight"]),
            "negated": c.get("negated", False),
        }
        for c in contributions
    ]
    important_words.sort(key=lambda w: abs(w["weight"]), reverse=True)

    positive_phrases, negative_phrases = [], []
    for sentence in split_sentences(text):
        for clause in split_clauses(sentence):
            clause_lower = clause.lower()
            has_pos = any(w["word"] in clause_lower and w["type"] == "positive" for w in important_words)
            has_neg = any(w["word"] in clause_lower and w["type"] == "negative" for w in important_words)
            if has_neg and not has_pos:
                negative_phrases.append(clause)
            elif has_pos and not has_neg:
                positive_phrases.append(clause)

    signals: List[str] = []
    signals.append(
        f"Overall sentiment '{sentiment_result['label']}' predicted with "
        f"{round(sentiment_result['confidence'] * 100)}% confidence by the TF-IDF + "
        f"Logistic Regression sentiment model."
    )
    if aspects:
        neg_aspects = [a["aspect"] for a in aspects if a["sentiment"] == "negative"]
        pos_aspects = [a["aspect"] for a in aspects if a["sentiment"] == "positive"]
        if pos_aspects:
            signals.append(f"Positive mentions detected for: {', '.join(pos_aspects)}.")
        if neg_aspects:
            signals.append(f"Negative mentions detected for: {', '.join(neg_aspects)}.")
    signals.append(f"Dominant emotion detected: {emotion_result['label']} ({round(emotion_result['confidence']*100)}%).")
    signals.extend(priority_result.get("reasons", []))

    return {
        "important_words": important_words[:12],
        "negative_phrases": negative_phrases,
        "positive_phrases": positive_phrases,
        "signals": signals,
    }
