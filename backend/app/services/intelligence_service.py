"""
intelligence_service.py

Builds the advanced dashboard intelligence zones using results CXIQ
already computes.

This service does NOT introduce a new ML model. It combines existing
per-review analytical outputs into explainable dashboard intelligence.

Main sections:
    1. Customer Voice Intelligence
    2. CX Issue Radar
    3. Emotion by Aspect
    4. Decision Center
    5. Language CX Comparison

CX ISSUE RADAR
--------------

Base risk score:

    risk =
        frequency_share
        x negativity_ratio
        x avg_severity
        x recency_boost

Where:

    frequency_share =
        aspect mentions / maximum aspect mentions in the dataset

    negativity_ratio =
        negative mentions / total mentions for the aspect

    avg_severity =
        average complaint-priority score among negative reviews
        mentioning the aspect

    recency_boost =
        1.0 normally, up to 1.5 when trend analysis detects
        an increasing negative trend

The base risk formula is preserved.

The final risk LEVEL additionally requires minimum evidence and
negativity thresholds. This prevents a frequently mentioned but
mixed-sentiment aspect from becoming Critical simply because it
has high volume relative to the rest of the batch.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List


# =========================================================
# CUSTOMER VOICE INTELLIGENCE
# =========================================================

def compute_customer_voice(
    aspect_summary: List[Dict],
) -> List[Dict]:
    """
    Summarise what customers talk about and the sentiment health of
    each aspect.

    NOTE:
    This is a sentiment-health status, not the same thing as the
    calculated CX Issue Radar risk.

    Customer Voice answers:
        "How positively/negatively do customers talk about this?"

    Issue Radar answers:
        "How operationally important/risky is this issue considering
        volume, negativity, severity and trend?"
    """

    matrix = []

    for aspect in sorted(
        aspect_summary,
        key=lambda x: -x["mentions"],
    ):

        positive_ratio = aspect.get(
            "positive_ratio",
            0.0,
        )

        # -------------------------------------------------
        # SENTIMENT HEALTH STATUS
        # -------------------------------------------------

        if positive_ratio >= 0.70:
            status = "Low"

        elif positive_ratio >= 0.50:
            status = "Medium"

        elif positive_ratio >= 0.30:
            status = "High"

        else:
            status = "Critical"

        matrix.append({
            **aspect,

            # Kept for frontend backward compatibility.
            "risk": status,

            # More accurate conceptual name.
            "sentiment_status": status,
        })

    return matrix


# =========================================================
# CX ISSUE RADAR
# =========================================================

def compute_issue_radar(
    aspect_summary: List[Dict],
    rows: List[Dict],
    emerging_issues: List[Dict],
) -> List[Dict]:
    """
    Calculate explainable operational risk for each negatively
    mentioned aspect.

    Risk score:

        frequency_share
        x negativity_ratio
        x average severity
        x recency boost

    Final levels also require absolute negativity/evidence thresholds.

    This prevents situations such as:

        Packaging
        9 mentions
        44% negative

    being labelled Critical simply because Packaging is one of the
    most frequently discussed aspects.
    """

    # Only aspects with at least one negative mention are candidates.
    candidates = [
        aspect
        for aspect in aspect_summary
        if aspect.get("negative", 0) > 0
        and aspect.get("mentions", 0) > 0
    ]

    if not candidates:
        return []

    # =====================================================
    # MAXIMUM VOLUME
    # =====================================================

    max_mentions = max(
        aspect["mentions"]
        for aspect in candidates
    ) or 1

    # =====================================================
    # EMERGING ISSUE LOOKUP
    # =====================================================

    emerging_lookup = {
        issue["aspect"]: issue["increase_pp"]
        for issue in emerging_issues
        if issue.get("aspect")
    }

    radar = []

    # =====================================================
    # CALCULATE RAW RISK
    # =====================================================

    for aspect in candidates:

        mentions = aspect["mentions"]

        negative_mentions = aspect.get(
            "negative",
            0,
        )

        # -------------------------------------------------
        # Frequency
        # -------------------------------------------------

        frequency_share = (
            mentions / max_mentions
        )

        # -------------------------------------------------
        # Negativity
        # -------------------------------------------------

        negativity_ratio = (
            negative_mentions / mentions
        )

        # -------------------------------------------------
        # Severity
        # -------------------------------------------------

        severities = [
            row["priority_score"]
            for row in rows
            if (
                aspect["aspect"]
                in row.get(
                    "negative_aspects",
                    [],
                )
            )
        ]

        if severities:

            avg_severity = (
                sum(severities)
                / len(severities)
            )

        else:

            # Conservative fallback.
            avg_severity = 0.25

        # -------------------------------------------------
        # Trend / Recency
        # -------------------------------------------------

        increase_pp = emerging_lookup.get(
            aspect["aspect"]
        )

        recency_boost = (
            1.0
            + min(
                max(
                    (increase_pp or 0)
                    / 100,
                    0.0,
                ),
                0.5,
            )
        )

        # -------------------------------------------------
        # Final raw risk score
        # -------------------------------------------------

        risk_score = round(
            frequency_share
            * negativity_ratio
            * avg_severity
            * recency_boost,
            4,
        )

        radar.append({
            "aspect": aspect["aspect"],

            "risk_score": risk_score,

            "mentions": mentions,

            "negative_mentions": negative_mentions,

            "negative_pct": round(
                negativity_ratio * 100,
                1,
            ),

            "avg_severity": round(
                avg_severity,
                4,
            ),

            "frequency_share": round(
                frequency_share,
                4,
            ),

            "trend_increase_pp": increase_pp,
        })

    # =====================================================
    # SORT BY RISK
    # =====================================================

    radar.sort(
        key=lambda item: -item[
            "risk_score"
        ]
    )

    top_score = (
        radar[0]["risk_score"]
        if radar
        else 0.0
    )

    # Avoid divide-by-zero.
    if top_score <= 0:
        top_score = 1.0

    # =====================================================
    # ASSIGN LEVELS
    # =====================================================

    for issue in radar:

        score = issue["risk_score"]

        mentions = issue["mentions"]

        negative_mentions = issue[
            "negative_mentions"
        ]

        negative_ratio = (
            issue["negative_pct"]
            / 100
        )

        normalized = (
            score / top_score
        )

        issue["normalized_risk"] = round(
            normalized,
            4,
        )

        # -------------------------------------------------
        # CRITICAL
        # -------------------------------------------------
        #
        # Requires:
        #   - enough mentions
        #   - enough actual negative mentions
        #   - at least 70% negativity
        #   - meaningful absolute risk
        #   - meaningful relative risk
        #
        # Therefore:
        #
        #   9 mentions / 44% negative
        #
        # cannot become Critical simply because of volume.
        # -------------------------------------------------

        if (
            mentions >= 4
            and negative_mentions >= 3
            and negative_ratio >= 0.70
            and score >= 0.25
            and normalized >= 0.50
        ):

            issue["level"] = "Critical"

        # -------------------------------------------------
        # HIGH
        # -------------------------------------------------

        elif (
            mentions >= 3
            and negative_mentions >= 2
            and negative_ratio >= 0.50
            and score >= 0.12
            and normalized >= 0.25
        ):

            issue["level"] = "High"

        # -------------------------------------------------
        # MEDIUM
        # -------------------------------------------------

        elif (
            negative_mentions >= 1
            and score > 0
        ):

            issue["level"] = "Medium"

        # -------------------------------------------------
        # LOW
        # -------------------------------------------------

        else:

            issue["level"] = "Low"

    # Keep dashboard compact.
    return radar[:6]


# =========================================================
# DOMINANT EMOTION BY NEGATIVE ASPECT
# =========================================================

def compute_emotion_by_aspect(
    rows: List[Dict],
) -> Dict[str, str]:
    """
    Find the dominant emotion among reviews where each aspect was
    mentioned negatively.

    Used as supporting evidence in the Decision Center.
    """

    tally: Dict[
        str,
        Counter,
    ] = {}

    for row in rows:

        for aspect in row.get(
            "negative_aspects",
            [],
        ):

            tally.setdefault(
                aspect,
                Counter(),
            )[
                row.get(
                    "emotion",
                    "Neutral",
                )
            ] += 1

    return {
        aspect: counter.most_common(
            1
        )[0][0]

        for aspect, counter
        in tally.items()

        if counter
    }


# =========================================================
# ACTION TEMPLATES
# =========================================================
# =========================================================
# DOMAIN-AWARE DECISION CENTER ACTIONS
# =========================================================

_DOMAIN_ACTIONS = {

    # -----------------------------------------------------
    # HOTEL
    # -----------------------------------------------------
    "hotel": {
        "Cleanliness": {
            "Housekeeping Team":
                "Review cleaning standards and inspect recurring cleanliness complaints.",
            "Hotel Operations":
                "Audit housekeeping checks and resolve repeated cleanliness gaps.",
            "CX Team":
                "Monitor cleanliness complaints and guest feedback trends.",
        },

        "Room": {
            "Housekeeping Team":
                "Inspect room-condition complaints and improve room preparation checks.",
            "Maintenance Team":
                "Investigate room facilities and repair recurring room-related problems.",
            "CX Team":
                "Track room complaints and identify frequently reported problems.",
        },

        "Connectivity": {
            "IT / Technical Team":
                "Investigate Wi-Fi speed, coverage, stability, and recurring connectivity failures.",
            "Hotel Operations":
                "Verify connectivity quality across rooms and common guest areas.",
            "CX Team":
                "Monitor connectivity complaints and flag recurring Wi-Fi issues.",
        },

        "Food": {
            "Food & Beverage Team":
                "Review food quality, variety, availability, and recurring guest complaints.",
            "Kitchen Team":
                "Investigate food-related feedback and improve identified problem areas.",
            "CX Team":
                "Track food feedback and identify repeated dissatisfaction patterns.",
        },

        "Taste": {
            "Kitchen Team":
                "Review taste-related complaints and investigate consistency in food preparation.",
            "Food & Beverage Team":
                "Evaluate guest feedback about food quality and menu satisfaction.",
            "CX Team":
                "Monitor recurring taste complaints and guest sentiment.",
        },

        "Staff": {
            "Hotel Operations":
                "Review staff-related complaints and identify service or training gaps.",
            "Guest Services":
                "Improve guest interactions and response quality where complaints recur.",
            "CX Team":
                "Monitor staff feedback and flag recurring service concerns.",
        },

        "Service": {
            "Guest Services":
                "Investigate slow or unsatisfactory service experiences reported by guests.",
            "Hotel Operations":
                "Review service workflows and address recurring response delays.",
            "CX Team":
                "Monitor service complaints and identify recurring experience gaps.",
        },

        "Comfort": {
            "Hotel Operations":
                "Review guest comfort complaints and identify common causes.",
            "Maintenance Team":
                "Inspect facilities that may be affecting guest comfort.",
            "CX Team":
                "Track comfort-related feedback and recurring dissatisfaction.",
        },

        "Location": {
            "Guest Services":
                "Review location-related concerns and improve guidance provided to guests.",
            "Hotel Operations":
                "Identify operational improvements that can reduce location-related inconvenience.",
            "CX Team":
                "Monitor location feedback and recurring guest concerns.",
        },

        "Booking": {
            "Reservations Team":
                "Review booking complaints and simplify reservation handling.",
            "Front Desk":
                "Investigate booking discrepancies affecting arriving guests.",
            "CX Team":
                "Monitor recurring reservation problems.",
        },

        "Payment": {
            "Front Desk / Billing":
                "Investigate payment and billing complaints and resolve recurring issues.",
            "Hotel Operations":
                "Review payment processes for delays, errors, or unclear charges.",
            "CX Team":
                "Track payment-related complaints and escalation patterns.",
        },

        "Price": {
            "Revenue Management":
                "Review pricing complaints and perceived value concerns.",
            "Hotel Management":
                "Evaluate whether pricing aligns with the guest experience being delivered.",
            "CX Team":
                "Monitor price and value-related sentiment.",
        },

        "Safety": {
            "Security Team":
                "Investigate reported safety concerns and take corrective action.",
            "Hotel Operations":
                "Review operational procedures related to guest safety.",
            "CX Team":
                "Track safety-related complaints and recurring concerns.",
        },
    },

    # -----------------------------------------------------
    # ELECTRONICS
    # -----------------------------------------------------
    "electronics": {
        "Battery": {
            "Product Team":
                "Investigate battery-life complaints and recurring power-related issues.",
            "Engineering Team":
                "Review battery performance and possible technical causes.",
            "CX Team":
                "Monitor battery complaints and repeat failure patterns.",
        },

        "Camera": {
            "Product Team":
                "Review camera-quality complaints and affected product scenarios.",
            "Engineering Team":
                "Investigate recurring camera performance problems.",
            "CX Team":
                "Monitor camera-related dissatisfaction.",
        },

        "Display": {
            "Product Team":
                "Review display-quality complaints and recurring customer concerns.",
            "Engineering Team":
                "Investigate display defects and technical performance issues.",
            "CX Team":
                "Track display complaints and repeat mentions.",
        },

        "Performance": {
            "Engineering Team":
                "Investigate performance, speed, lag, and stability complaints.",
            "Product Team":
                "Review product-performance expectations against customer feedback.",
            "CX Team":
                "Monitor recurring performance complaints.",
        },

        "Software": {
            "Software Engineering":
                "Investigate software bugs, crashes, and usability problems.",
            "Product Team":
                "Review recurring software complaints and prioritize improvements.",
            "CX Team":
                "Track software-related dissatisfaction.",
        },

        "Connectivity": {
            "Engineering Team":
                "Investigate network, Wi-Fi, Bluetooth, and connectivity complaints.",
            "Technical Support":
                "Prepare troubleshooting guidance for recurring connectivity issues.",
            "CX Team":
                "Monitor connectivity complaints and repeat failures.",
        },
    },

    # -----------------------------------------------------
    # E-COMMERCE
    # -----------------------------------------------------
    "ecommerce": {
        "Delivery": {
            "Logistics Team":
                "Investigate delivery delays and recurring fulfilment problems.",
            "Customer Support":
                "Improve handling of delayed or failed deliveries.",
            "CX Team":
                "Monitor delivery complaints and recurring delay patterns.",
        },

        "Packaging": {
            "Fulfilment Team":
                "Review packaging quality and recurring damage complaints.",
            "Warehouse Operations":
                "Inspect packing procedures and handling standards.",
            "CX Team":
                "Monitor packaging-related complaints.",
        },

        "Product Quality": {
            "Product Quality Team":
                "Investigate recurring product-quality complaints.",
            "Seller / Vendor Management":
                "Review suppliers associated with repeated quality problems.",
            "CX Team":
                "Track product-quality dissatisfaction.",
        },

        "Customer Support": {
            "Customer Support":
                "Review support complaints and improve response quality.",
            "Support Operations":
                "Investigate response delays and recurring service gaps.",
            "CX Team":
                "Monitor customer-support sentiment.",
        },

        "Return": {
            "Returns Team":
                "Review recurring return-process complaints and reduce friction.",
            "Customer Support":
                "Improve assistance for customers requesting returns.",
            "CX Team":
                "Track return-related dissatisfaction.",
        },

        "Refund": {
            "Refund / Payments Team":
                "Investigate refund delays and recurring refund problems.",
            "Customer Support":
                "Improve communication and escalation for pending refunds.",
            "CX Team":
                "Monitor refund complaints.",
        },
    },

    # -----------------------------------------------------
    # RESTAURANT
    # -----------------------------------------------------
    "restaurant": {
        "Food": {
            "Kitchen Team":
                "Investigate recurring food-quality complaints.",
            "Restaurant Operations":
                "Review food consistency and service delivery.",
            "CX Team":
                "Monitor food-related dissatisfaction.",
        },

        "Taste": {
            "Kitchen Team":
                "Review taste complaints and food-preparation consistency.",
            "Head Chef / Kitchen Management":
                "Investigate recurring taste and recipe concerns.",
            "CX Team":
                "Monitor taste-related feedback.",
        },

        "Service": {
            "Restaurant Operations":
                "Investigate slow or unsatisfactory service experiences.",
            "Service Team":
                "Review service procedures and response times.",
            "CX Team":
                "Monitor recurring service complaints.",
        },

        "Staff": {
            "Restaurant Management":
                "Review staff-related complaints and identify training needs.",
            "Service Team":
                "Improve customer interactions and response quality.",
            "CX Team":
                "Monitor staff-related customer feedback.",
        },

        "Cleanliness": {
            "Restaurant Operations":
                "Investigate cleanliness complaints and strengthen hygiene checks.",
            "Cleaning / Hygiene Team":
                "Review cleaning procedures and recurring hygiene concerns.",
            "CX Team":
                "Monitor cleanliness-related feedback.",
        },

        "Waiting Time": {
            "Restaurant Operations":
                "Investigate long waiting times and service bottlenecks.",
            "Front-of-House Team":
                "Improve queue and table-management processes.",
            "CX Team":
                "Monitor waiting-time complaints.",
        },
    },

    # -----------------------------------------------------
    # TRAVEL
    # -----------------------------------------------------
    "travel": {
        "Punctuality": {
            "Operations Team":
                "Investigate delays and recurring punctuality problems.",
            "Service Operations":
                "Review processes contributing to delays.",
            "CX Team":
                "Monitor punctuality complaints.",
        },

        "Booking": {
            "Reservations Team":
                "Investigate booking difficulties and recurring reservation problems.",
            "Customer Support":
                "Improve assistance for booking-related issues.",
            "CX Team":
                "Monitor booking complaints.",
        },

        "Luggage": {
            "Baggage Operations":
                "Investigate luggage handling complaints and recurring failures.",
            "Customer Support":
                "Improve support for luggage-related incidents.",
            "CX Team":
                "Track luggage complaints.",
        },

        "Comfort": {
            "Operations Team":
                "Review comfort complaints and identify improvement opportunities.",
            "Service Team":
                "Address recurring customer comfort concerns.",
            "CX Team":
                "Monitor comfort-related feedback.",
        },

        "Safety": {
            "Safety / Security Team":
                "Investigate safety concerns and recurring incidents.",
            "Operations Team":
                "Review procedures related to customer safety.",
            "CX Team":
                "Monitor safety-related feedback.",
        },
    },
}


# =========================================================
# GENERIC FALLBACK ACTIONS
# =========================================================

def _get_decision_actions(
    domain: str,
    aspect: str,
) -> Dict[str, str]:
    """
    Return domain-aware recommended owners/actions.

    If CXIQ does not have a specific domain+aspect mapping,
    fall back to generic Operations / Support / CX actions.
    """

    normalized_domain = (domain or "other").strip().lower()

    domain_actions = _DOMAIN_ACTIONS.get(
        normalized_domain,
        {},
    )

    if aspect in domain_actions:
        return domain_actions[aspect]

    aspect_lower = aspect.lower()

    return {
        "Operations Team":
            f"Investigate recurring {aspect_lower} complaints and identify the underlying operational causes.",

        "Customer Support":
            f"Create a response workflow for customers reporting {aspect_lower} problems.",

        "CX Team":
            f"Monitor {aspect_lower} complaints and flag repeated negative patterns.",
    }

# =========================================================
# EXPLAIN WHY AN ISSUE HAS ITS LEVEL
# =========================================================

def _build_issue_explanation(
    issue: Dict,
) -> str:
    """
    Build an explanation that reflects the actual evidence instead
    of always claiming both volume and negativity are high.
    """

    mentions = issue.get(
        "mentions",
        0,
    )

    negative_pct = issue.get(
        "negative_pct",
        0.0,
    )

    trend = issue.get(
        "trend_increase_pp"
    )

    parts = []

    # -----------------------------------------------------
    # Volume description
    # -----------------------------------------------------

    if mentions >= 6:

        parts.append(
            "High mention volume"
        )

    elif mentions >= 3:

        parts.append(
            "Repeated customer mentions"
        )

    else:

        parts.append(
            "Limited but relevant customer mentions"
        )

    # -----------------------------------------------------
    # Negativity description
    # -----------------------------------------------------

    if negative_pct >= 70:

        parts.append(
            "high negativity"
        )

    elif negative_pct >= 50:

        parts.append(
            "moderate-to-high negativity"
        )

    elif negative_pct >= 30:

        parts.append(
            "mixed sentiment with a meaningful negative share"
        )

    else:

        parts.append(
            "a smaller negative share"
        )

    # -----------------------------------------------------
    # Trend
    # -----------------------------------------------------

    if trend and trend > 0:

        parts.append(
            "an increasing negative trend"
        )

    return (
        " + ".join(parts)
        + " determine this CX risk level."
    )


# =========================================================
# DECISION CENTER
# =========================================================

def compute_decision_center(
    issue_radar: List[Dict],
    rows: List[Dict],
    emotion_by_aspect: Dict[str, str],
    domain: str = "other",
    top_n: int = 3,
) -> List[Dict]:
    """
    Create evidence-based Decision Center cards from the highest
    calculated CX risks.
    """

    cards = []

    for issue in issue_radar[
        :top_n
    ]:

        aspect = issue["aspect"]

        dominant_emotion = (
            emotion_by_aspect.get(
                aspect,
                "Neutral",
            )
        )

        # -------------------------------------------------
        # High/Critical complaint count
        # -------------------------------------------------

        high_priority_count = sum(

            1
            for row in rows

            if (
                aspect
                in row.get(
                    "negative_aspects",
                    [],
                )

                and row.get(
                    "priority"
                )
                in (
                    "High",
                    "Critical",
                )
            )
        )

        # -------------------------------------------------
        # Evidence
        # -------------------------------------------------

        evidence = [
            f"{issue['mentions']} mentions",

            (
                f"{issue['negative_pct']}% "
                f"negative"
            ),

            (
                "Dominant emotion: "
                f"{dominant_emotion}"
            ),
        ]

        if issue.get(
            "trend_increase_pp"
        ):

            evidence.append(
                "+"
                f"{issue['trend_increase_pp']} "
                "point increase over the period"
            )

        evidence.append(
            f"{high_priority_count} "
            "high/critical-priority complaint(s)"
        )

        # -------------------------------------------------
        # Accurate explanation
        # -------------------------------------------------

        why = _build_issue_explanation(
            issue
        )

        # -------------------------------------------------
        # Card
        # -------------------------------------------------

        cards.append({

            "issue": aspect,

            "level": issue[
                "level"
            ],

            "evidence": evidence,

            "actions": _get_decision_actions(
                domain,
                aspect,
            ),

            "why": why,
        })

    return cards


# =========================================================
# LANGUAGE CX COMPARISON
# =========================================================

def compute_language_breakdown(
    rows: List[Dict],
) -> List[Dict]:
    """
    Language CX Comparison table.

    Shows:
        - review count
        - positive %
        - neutral %
        - negative %
        - top negative aspect
        - CX score
        - unreliable translation count

    Sentiment/aspect/CX calculations use reliable rows only.
    """

    from app.services.cxscore_service import (
        compute_cx_score,
    )

    by_lang: Dict[
        str,
        List[Dict],
    ] = {}

    # =====================================================
    # GROUP BY LANGUAGE
    # =====================================================

    for row in rows:

        language = row.get(
            "language",
            "English",
        )

        by_lang.setdefault(
            language,
            [],
        ).append(
            row
        )

    breakdown = []

    # =====================================================
    # CALCULATE EACH LANGUAGE
    # =====================================================

    for language, lang_rows in by_lang.items():

        total = len(
            lang_rows
        )

        unreliable_count = sum(

            1
            for row in lang_rows

            if not row.get(
                "reliable",
                True,
            )
        )

        # -------------------------------------------------
        # Reliable rows only
        # -------------------------------------------------

        reliable_rows = [

            row
            for row in lang_rows

            if row.get(
                "reliable",
                True,
            )
        ]

        # BUG FIX: this used to fall back to ALL rows (including
        # translation-failed placeholder rows) whenever a language had
        # zero reliable rows, which produced misleading output such as
        # "French: 100% Neutral" with a real-looking CX Score computed
        # entirely from placeholder neutral results. When there are no
        # reliable rows for a language, `basis` stays empty on purpose -
        # no sentiment percentage or CX Score is calculated for it, and
        # the caller marks it as "No reliable analyses" instead.
        basis = reliable_rows

        basis_total = len(
            basis
        )

        has_reliable_data = (
            basis_total > 0
        )

        # -------------------------------------------------
        # Sentiment counts
        # -------------------------------------------------

        sentiment_counts = Counter(

            row[
                "overall_sentiment"
            ]

            for row in basis
        )

        # -------------------------------------------------
        # Priority counts
        # -------------------------------------------------

        priority_counts = Counter(

            row[
                "priority"
            ]

            for row in basis
        )

        # -------------------------------------------------
        # Negative aspects
        # -------------------------------------------------

        negative_aspect_counts = (
            Counter()
        )

        for row in basis:

            negative_aspect_counts.update(
                row.get(
                    "negative_aspects",
                    [],
                )
            )

        if negative_aspect_counts:

            top_negative_aspect = (
                negative_aspect_counts
                .most_common(1)[0][0]
            )

        else:

            top_negative_aspect = None

        # -------------------------------------------------
        # Aspect sentiment counts
        # -------------------------------------------------

        aspect_sentiment_counts = (
            Counter()
        )

        for row in basis:

            for sentiment in (
                row.get(
                    "aspect_sentiments",
                    {},
                ).values()
            ):

                aspect_sentiment_counts[
                    sentiment
                ] += 1

        # -------------------------------------------------
        # Ratings
        # -------------------------------------------------

        ratings = []

        for row in basis:

            rating = row.get(
                "rating"
            )

            if (
                rating in (
                    None,
                    "",
                )
                or str(
                    rating
                ).lower()
                == "nan"
            ):

                continue

            try:

                ratings.append(
                    float(
                        rating
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

        if ratings:

            avg_rating = round(
                sum(ratings)
                / len(ratings),
                2,
            )

        else:

            avg_rating = None

        # -------------------------------------------------
        # CX Score
        # -------------------------------------------------

        # Only computed when there is at least one reliably-analyzed
        # row for this language - otherwise there is no real signal to
        # score, and showing a number here would be misleading.
        if has_reliable_data:

            cx = compute_cx_score(

                sentiment_counts=dict(
                    sentiment_counts
                ),

                aspect_sentiment_counts=dict(
                    aspect_sentiment_counts
                ),

                priority_counts=dict(
                    priority_counts
                ),

                avg_rating=avg_rating,
            )

            cx_score = cx["score"]

        else:

            cx_score = None

        # -------------------------------------------------
        # Result
        # -------------------------------------------------

        breakdown.append({

            "language":
                language,

            "reviews":
                total,

            "reliably_analyzed":
                basis_total,

            "status":
                "ok"
                if has_reliable_data
                else "no_reliable_analyses",

            "positive_pct":
                round(
                    100
                    * sentiment_counts.get(
                        "positive",
                        0,
                    )
                    / basis_total,
                    1,
                )
                if has_reliable_data
                else None,

            "neutral_pct":
                round(
                    100
                    * sentiment_counts.get(
                        "neutral",
                        0,
                    )
                    / basis_total,
                    1,
                )
                if has_reliable_data
                else None,

            "negative_pct":
                round(
                    100
                    * sentiment_counts.get(
                        "negative",
                        0,
                    )
                    / basis_total,
                    1,
                )
                if has_reliable_data
                else None,

            "top_negative_aspect":
                top_negative_aspect
                if has_reliable_data
                else None,

            "cx_score":
                cx_score,

            "unreliable_count":
                unreliable_count,

            "unreliable_pct":
                round(
                    100
                    * unreliable_count
                    / total,
                    1,
                )
                if total
                else 0,
        })

    # =====================================================
    # SORT
    # =====================================================

    breakdown.sort(
        key=lambda item: -item[
            "reviews"
        ]
    )

    return breakdown