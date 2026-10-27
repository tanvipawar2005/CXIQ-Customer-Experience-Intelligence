"""
tests/test_issue_fixes.py

Focused regression tests for the fixes made in response to the client's
bug report (see project README changelog). These are not a full test
suite for CXIQ - they specifically target the five reported issues so a
future change doesn't silently reintroduce them.

Run with:
    pytest tests/test_issue_fixes.py -v
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.services.pipeline_service import analyze_review
from app.services import translation_service as ts
from app.services.intelligence_service import compute_language_breakdown
from app.services.trend_service import analyze_trends


# =========================================================
# ISSUE 1 - balanced "neither X nor Y" sentences
# =========================================================

class TestBalancedNeitherNor:

    def test_neutral_sentence_is_truly_neutral(self):
        """The exact sentence from the bug report must come back neutral
        across sentiment, emotion, aspects, and priority - not the
        previous (Positive/Joy/'Sad' aspect) result."""
        result = analyze_review(
            "I am neither happy nor sad with the phone",
            domain="electronics",
        )

        assert result["overall_sentiment"]["label"] == "neutral"
        assert result["emotion"]["label"] == "Neutral"
        assert "Sad" not in [a["aspect"] for a in result["aspects"]]
        assert result["priority"]["label"] == "Low"

    def test_ordinary_positive_review_unaffected(self):
        result = analyze_review(
            "This phone is excellent, I love the camera and battery life",
            domain="electronics",
        )
        assert result["overall_sentiment"]["label"] == "positive"

    def test_ordinary_negative_review_unaffected(self):
        result = analyze_review(
            "This is the worst product I have ever bought, totally broken",
            domain="electronics",
        )
        assert result["overall_sentiment"]["label"] == "negative"

    def test_mixed_aspect_review(self):
        """Battery praised, camera criticized - both aspects should be
        detected with the correct, independent sentiment."""
        result = analyze_review(
            "The battery is excellent but the camera is disappointing",
            domain="electronics",
        )
        aspect_sentiment = {a["aspect"]: a["sentiment"] for a in result["aspects"]}
        assert aspect_sentiment.get("Battery") == "positive"
        assert aspect_sentiment.get("Camera") == "negative"

    def test_balanced_clause_does_not_swallow_unrelated_negative_clause(self):
        """A 'neither best nor worst' clause about ONE aspect must not
        force the whole multi-clause review (including an unrelated
        negative clause) to neutral."""
        result = analyze_review(
            "The camera is neither the best nor the worst, but delivery "
            "was late and the staff were rude",
            domain="electronics",
        )
        assert result["overall_sentiment"]["label"] == "negative"

    def test_emotion_words_are_never_guessed_aspects(self):
        result = analyze_review(
            "I felt neither excited nor disappointed by the unboxing",
            domain="electronics",
        )
        aspects = [a["aspect"] for a in result["aspects"]]
        assert "Excited" not in aspects
        assert "Disappointed" not in aspects


# =========================================================
# ISSUE 2 - translation retry / failure handling
# =========================================================

class TestTranslationReliability:

    def test_transient_failure_is_retried_and_succeeds(self, monkeypatch):
        calls = {"n": 0}

        def flaky_mymemory(text, source):
            calls["n"] += 1
            if calls["n"] < 2:
                raise TimeoutError("Read timed out")
            return "a valid translated sentence"

        monkeypatch.setattr(ts, "_translate_with_mymemory", flaky_mymemory)
        monkeypatch.setattr(ts, "MAX_RETRIES", 2)
        monkeypatch.setattr(ts, "RETRY_BACKOFF_BASE_SECONDS", 0.01)

        text, status = ts.translate_to_english("un texte unique de test", "fr")

        assert status == "translated"
        assert calls["n"] == 2

    def test_permanent_failure_is_not_cached(self, monkeypatch):
        def always_fails(text, source):
            raise ValueError("unsupported language pair")

        def gemini_always_fails(text, lang):
            raise ValueError("unsupported language pair")

        monkeypatch.setattr(ts, "_translate_with_mymemory", always_fails)
        monkeypatch.setattr(ts, "translate_review", gemini_always_fails)

        unique_text = "une phrase de test jamais vue avant xyz987"
        text, status = ts.translate_to_english(unique_text, "fr")

        assert status == "failed"
        assert ("fr", unique_text) not in ts._cache

    def test_unreliable_review_marked_and_excluded_from_confident_result(self, monkeypatch):
        """When translation genuinely fails, analyze_review must return a
        low-confidence neutral result explicitly marked unreliable -
        never a confident guess built on untranslated text."""
        import app.services.pipeline_service as pipeline_service

        monkeypatch.setattr(
            pipeline_service,
            "detect_language",
            lambda text: {"code": "hi", "name": "Hindi", "is_supported": True, "is_code_mixed": False},
        )
        monkeypatch.setattr(
            pipeline_service,
            "translate_to_english",
            lambda text, lang: (text, "failed"),
        )

        result = analyze_review("kuch bhi likh do yahan", domain="electronics")

        assert result["reliable"] is False
        assert result["overall_sentiment"]["label"] == "neutral"


# =========================================================
# ISSUE 3 - dashboard numbers for a language with no reliable data
# =========================================================

class TestLanguageBreakdown:

    def test_language_with_zero_reliable_rows_reports_no_data(self):
        rows = [
            {
                "language": "English", "overall_sentiment": "positive", "priority": "Low",
                "reliable": True, "aspect_sentiments": {"Battery": "positive"},
                "negative_aspects": [], "rating": 5,
            },
            {
                "language": "French", "overall_sentiment": "neutral", "priority": "Low",
                "reliable": False, "aspect_sentiments": {}, "negative_aspects": [], "rating": None,
            },
            {
                "language": "French", "overall_sentiment": "neutral", "priority": "Low",
                "reliable": False, "aspect_sentiments": {}, "negative_aspects": [], "rating": None,
            },
        ]

        breakdown = {row["language"]: row for row in compute_language_breakdown(rows)}

        french = breakdown["French"]
        assert french["status"] == "no_reliable_analyses"
        assert french["cx_score"] is None
        assert french["positive_pct"] is None
        assert french["reviews"] == 2
        assert french["unreliable_count"] == 2

        english = breakdown["English"]
        assert english["status"] == "ok"
        assert english["cx_score"] is not None


# =========================================================
# ISSUE 4 - small-sample trend claims
# =========================================================

class TestTrendMinimumData:

    def test_thin_monthly_data_is_flagged_insufficient(self):
        rows = [
            {"date": "2026-01-05", "overall_sentiment": "negative", "negative_aspects": ["Battery"]},
            {"date": "2026-02-05", "overall_sentiment": "negative", "negative_aspects": ["Battery"]},
            {"date": "2026-03-05", "overall_sentiment": "negative", "negative_aspects": ["Battery"]},
        ]
        result = analyze_trends(rows)

        assert result["emerging_issues"] == []
        assert result["forecast"]["available"] is False

    def test_larger_dataset_still_produces_genuine_trend(self):
        rows = []
        for month, battery_negatives in [("2026-01", 1), ("2026-02", 3), ("2026-03", 5)]:
            for i in range(6):
                neg = ["Battery"] if i < battery_negatives else []
                rows.append({
                    "date": f"{month}-{10 + i:02d}",
                    "overall_sentiment": "negative" if neg else "positive",
                    "negative_aspects": neg,
                })

        result = analyze_trends(rows)

        assert result["forecast"]["available"] is True
        aspects = [issue["aspect"] for issue in result["emerging_issues"]]
        assert "Battery" in aspects


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
