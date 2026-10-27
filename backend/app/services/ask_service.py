"""
ask_service.py

"Ask CXIQ" — a small natural-language Q&A box on the dashboard.

HONEST DESIGN: this never sends raw reviews to an LLM and never lets an LLM
invent statistics. The flow is always:

    Dashboard (real, already-computed statistics)
              |
              v
    Rule-based answer (always computed, always available)
              |
              v
    Optional Gemini rewrite (only rephrases the same grounded facts into a
    more natural sentence — see gemini_service.answer_dashboard_question)

If Gemini is not configured, or fails for any reason, the rule-based answer
is what the user sees. Either way, every fact in the answer traces back to
the dashboard's real analyzed data.
"""
from __future__ import annotations
from typing import Dict

from app.services import gemini_service


def _build_context(dashboard: Dict) -> Dict:
    aspect_summary = dashboard.get("aspect_summary", [])
    top_negative = sorted(aspect_summary, key=lambda a: -a["negative"])[:3]

    return {
        "total_reviews": dashboard["total_reviews"],
        "cx_score": dashboard["kpis"]["cx_score"],
        "cx_label": dashboard["kpis"]["cx_label"],
        "positive_pct": dashboard["kpis"]["positive_pct"],
        "negative_pct": dashboard["kpis"]["negative_pct"],
        "high_critical_issues": dashboard["kpis"]["high_critical_issues"],
        "top_negative_aspects": [a["aspect"] for a in top_negative if a["negative"] > 0],
        "issue_radar": [
            {"aspect": i["aspect"], "level": i["level"], "mentions": i["mentions"], "negative_pct": i["negative_pct"]}
            for i in dashboard.get("issue_radar", [])[:3]
        ],
        "decision_center": [
            {"issue": c["issue"], "level": c["level"]} for c in dashboard.get("decision_center", [])
        ],
        "language_breakdown": dashboard.get("language_breakdown", []),
    }


def _rule_based_answer(question: str, ctx: Dict) -> str:
    q = question.lower()

    if any(kw in q for kw in ("why", "unhappy", "dissatisf")) and "language" not in q:
        if ctx["top_negative_aspects"]:
            aspects = ", ".join(a.lower() for a in ctx["top_negative_aspects"])
            return f"Customer dissatisfaction is primarily associated with {aspects}."
        return "There isn't a dominant source of dissatisfaction in the current data."

    if any(kw in q for kw in ("biggest problem", "main issue", "top issue", "worst")) and "language" not in q:
        if ctx["issue_radar"]:
            top = ctx["issue_radar"][0]
            return (
                f"{top['aspect']} is the biggest problem right now — {top['mentions']} mentions, "
                f"{top['negative_pct']}% negative, flagged as {top['level']} risk."
            )
        return "No significant issue stands out above the others right now."

    if "language" in q and any(kw in q for kw in ("negative", "worst", "unhappy", "lowest")):
        if ctx["language_breakdown"]:
            worst = max(ctx["language_breakdown"], key=lambda l: l["negative_pct"])
            return f"{worst['language']} has the highest negative sentiment at {worst['negative_pct']}%."
        return "Language-level data isn't available for this dataset."

    if "language" in q and any(kw in q for kw in ("best", "positive", "highest")):
        if ctx["language_breakdown"]:
            best = max(ctx["language_breakdown"], key=lambda l: l["positive_pct"])
            return f"{best['language']} has the highest positive sentiment at {best['positive_pct']}%."
        return "Language-level data isn't available for this dataset."

    if any(kw in q for kw in ("fix first", "should we", "recommend", "priorit")):
        if ctx["decision_center"]:
            top = ctx["decision_center"][0]
            return f"{top['issue']} should be addressed first — it's currently flagged as {top['level']} priority."
        return "No urgent priority issues are flagged in the current data."

    if any(kw in q for kw in ("cx score", "customer experience score", "how are we doing", "overall")):
        return (
            f"The current Customer Experience Score is {ctx['cx_score']}/100 ({ctx['cx_label']}), "
            f"based on {ctx['total_reviews']} analyzed reviews with {ctx['negative_pct']}% negative feedback."
        )

    # generic fallback: a grounded summary
    top_aspect = ctx["top_negative_aspects"][0] if ctx["top_negative_aspects"] else "no single aspect"
    return (
        f"Across {ctx['total_reviews']} analyzed reviews, the CX Score is {ctx['cx_score']}/100 "
        f"({ctx['cx_label']}), with {ctx['negative_pct']}% negative feedback and "
        f"{ctx['high_critical_issues']} high/critical-priority issue(s). "
        f"The most discussed concern is {top_aspect}."
    )


def answer_question(question: str, dashboard: Dict) -> Dict:
    question = (question or "").strip()
    if not question:
        return {"answer": "Please enter a question about your customer feedback.", "source": "validation"}

    ctx = _build_context(dashboard)
    fallback_answer = _rule_based_answer(question, ctx)

    if gemini_service.is_configured():
        return gemini_service.answer_dashboard_question(question, ctx, fallback_answer)
    return {"answer": fallback_answer, "source": "rule_based"}
