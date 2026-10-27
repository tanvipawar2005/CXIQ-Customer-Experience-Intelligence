"""
insight_service.py

Rule-based business-insight and recommended-action generation. This layer
always runs (it costs nothing and never fails), and its output is used
directly whenever Gemini is not configured or unavailable — see
services/gemini_service.py. When Gemini *is* configured, these rule-based
insights are still computed and passed to Gemini as grounding context so the
generated language stays anchored to real analysis rather than hallucinating.
"""
from __future__ import annotations
from typing import Dict, List


def single_review_insight(sentiment: Dict, aspects: List[Dict], emotion: Dict, priority: Dict) -> Dict:
    neg_aspects = [a["aspect"] for a in aspects if a["sentiment"] == "negative"]
    pos_aspects = [a["aspect"] for a in aspects if a["sentiment"] == "positive"]

    if pos_aspects and neg_aspects:
        insight = (
            f"Customers may appreciate the {', '.join(pos_aspects).lower()} but experience "
            f"dissatisfaction due to {', '.join(neg_aspects).lower()}."
        )
    elif neg_aspects:
        insight = f"This feedback highlights dissatisfaction primarily around {', '.join(neg_aspects).lower()}."
    elif pos_aspects:
        insight = f"This feedback reflects a positive experience, particularly around {', '.join(pos_aspects).lower()}."
    else:
        insight = f"This feedback expresses an overall {sentiment['label']} sentiment without a strongly specific aspect."

    recommendations: List[str] = []
    for aspect in neg_aspects[:3]:
        recommendations.append(f"Investigate recurring {aspect.lower()}-related complaints.")
    if priority["label"] in ("High", "Critical"):
        recommendations.append("Escalate this case for prompt follow-up given its priority level.")
    if emotion["label"] in ("Anger", "Sadness", "Fear") and emotion["confidence"] > 0.6:
        recommendations.append(f"Consider a personalised response given the detected {emotion['label'].lower()} tone.")
    if not recommendations:
        recommendations.append("No immediate action required; continue monitoring similar feedback.")

    return {"business_insight": insight, "recommendations": recommendations}


def dashboard_insights(
    sentiment_counts: Dict[str, int],
    aspect_summary: List[Dict],
    priority_counts: Dict[str, int],
    emotion_counts: Dict[str, int],
    emerging_issues: List[Dict],
) -> Dict:
    total = sum(sentiment_counts.values()) or 1
    negative_pct = round(100 * sentiment_counts.get("negative", 0) / total, 1)

    weakest = sorted(aspect_summary, key=lambda a: a["positive_ratio"])[:3]
    strongest = sorted(aspect_summary, key=lambda a: -a["positive_ratio"])[:3]

    insights: List[str] = []
    if weakest:
        weak_names = ", ".join(a["aspect"].lower() for a in weakest if a["positive_ratio"] < 0.6)
        if weak_names:
            insights.append(f"Customer dissatisfaction is primarily associated with {weak_names}.")
    if strongest:
        strong_names = ", ".join(a["aspect"].lower() for a in strongest if a["positive_ratio"] > 0.7)
        if strong_names:
            insights.append(f"Customers consistently respond positively to {strong_names}.")
    if negative_pct > 40:
        insights.append(f"{negative_pct}% of analyzed feedback is negative, which is above a healthy baseline.")
    critical = priority_counts.get("Critical", 0)
    high = priority_counts.get("High", 0)
    if critical or high:
        insights.append(f"{critical} critical and {high} high-priority issues require attention.")
    if emerging_issues:
        top = emerging_issues[0]
        insights.append(f"'{top['aspect']}' complaints are trending upward and may need proactive investigation.")
    if not insights:
        insights.append("Overall customer experience signals are stable with no dominant issue area.")

    recommendations: List[str] = []
    for a in weakest:
        if a["positive_ratio"] < 0.6:
            recommendations.append(f"Review and improve {a['aspect'].lower()} based on recurring negative feedback.")
    if critical:
        recommendations.append("Prioritise resolution of critical-severity complaints immediately.")
    if emerging_issues:
        recommendations.append(f"Set up monitoring for the emerging '{emerging_issues[0]['aspect']}' issue trend.")
    if not recommendations:
        recommendations.append("Maintain current service levels and continue periodic feedback monitoring.")

    return {"business_insights": insights, "recommendations": recommendations[:6]}
