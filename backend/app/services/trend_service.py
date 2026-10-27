"""
trend_service.py

Time-based trend analysis and emerging-issue detection.

Approach:
- Parse common customer-review date formats safely.
- Bucket analyzed rows by month.
- Calculate sentiment distribution per month.
- Track negative aspect mentions over time.
- Detect emerging issues using percentage-point increase + positive slope.
- Produce a simple transparent two-period linear trend projection.

The forecasting logic is intentionally lightweight and explainable.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.config import settings


# =========================================================
# DATE PARSING
# =========================================================

def _parse_date(value):
    """
    Parse common dataset date formats safely.

    Supported examples:
        2026-09-19
        19-09-2026
        19/09/2026
        2026/09/19
        19 Sep 2026
        Sep 19 2026

    Returns pandas.Timestamp or NaT.
    """

    if value is None:
        return pd.NaT

    text = str(value).strip()

    if not text:
        return pd.NaT

    # -----------------------------------------------------
    # Explicit known formats first
    # -----------------------------------------------------

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%Y.%m.%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d %Y",
        "%B %d %Y",
    ]

    for fmt in formats:

        try:
            return pd.to_datetime(
                text,
                format=fmt,
                errors="raise",
            )

        except (ValueError, TypeError):
            continue

    # -----------------------------------------------------
    # Flexible fallback
    # -----------------------------------------------------

    try:
        return pd.to_datetime(
            text,
            errors="coerce",
            dayfirst=True,
        )

    except Exception:
        return pd.NaT


# =========================================================
# BUILD TIME SERIES DATAFRAME
# =========================================================

def build_time_series(
    analyzed_rows: List[Dict],
) -> Optional[pd.DataFrame]:

    rows_with_date = [
        row
        for row in analyzed_rows
        if row.get("date")
    ]

    if len(rows_with_date) < 2:
        return None

    df = pd.DataFrame(
        rows_with_date
    )

    # Parse each date safely instead of relying on pandas'
    # automatic ambiguous date interpretation.
    df["date"] = df["date"].apply(
        _parse_date
    )

    df = df.dropna(
        subset=["date"]
    )

    if df.empty:
        return None

    # -----------------------------------------------------
    # Month bucket
    # -----------------------------------------------------

    df["month"] = (
        df["date"]
        .dt.to_period("M")
        .astype(str)
    )

    return df


# =========================================================
# SENTIMENT OVER TIME
# =========================================================

def sentiment_over_time(
    df: pd.DataFrame,
) -> List[Dict]:

    grouped = (
        df.groupby("month")["overall_sentiment"]
        .value_counts(normalize=True)
        .unstack(fill_value=0)
    )

    grouped = grouped.sort_index()

    result = []

    for month, row in grouped.iterrows():

        result.append({
            "month": month,

            "positive": round(
                float(
                    row.get("positive", 0)
                ) * 100,
                1,
            ),

            "neutral": round(
                float(
                    row.get("neutral", 0)
                ) * 100,
                1,
            ),

            "negative": round(
                float(
                    row.get("negative", 0)
                ) * 100,
                1,
            ),
        })

    return result


# =========================================================
# MINIMUM-DATA CHECK
# =========================================================

def _trend_data_sufficiency(
    df: pd.DataFrame,
    months: List[str],
) -> Dict:
    """
    Decide whether there is enough evidence to present emerging-issue /
    forecast claims with confidence, and explain why not when there
    isn't.

    Having 3+ distinct months (MIN_TIME_BUCKETS_FOR_TREND) is not, on
    its own, enough - a month with only one or two reviews can swing
    from 0% to 100% on a single review, which would otherwise get
    presented as a confident "emerging issue" or feed a "forecast" off
    essentially no evidence. This additionally requires every month
    bucket to carry a minimum number of reviews.
    """

    if len(months) < settings.MIN_TIME_BUCKETS_FOR_TREND:

        return {
            "sufficient": False,
            "reason": (
                f"Only {len(months)} distinct time period(s) of dated "
                f"data are available; at least "
                f"{settings.MIN_TIME_BUCKETS_FOR_TREND} are needed."
            ),
        }

    reviews_per_month = df.groupby("month").size()

    thin_months = [
        month
        for month in months
        if reviews_per_month.get(month, 0)
        < settings.MIN_REVIEWS_PER_MONTH_FOR_TREND
    ]

    if thin_months:

        return {
            "sufficient": False,
            "reason": (
                "Some months in this dataset have too few reviews "
                f"(fewer than {settings.MIN_REVIEWS_PER_MONTH_FOR_TREND}) "
                "to calculate a reliable percentage - a single review "
                "can otherwise swing a month from 0% to 100%. Months "
                f"with too little data: {', '.join(thin_months)}."
            ),
        }

    return {
        "sufficient": True,
        "reason": None,
    }


# =========================================================
# EMERGING ISSUES
# =========================================================

def detect_emerging_issues(
    df: pd.DataFrame,
) -> List[Dict]:

    months = sorted(
        df["month"].unique()
    )

    if (
        len(months)
        < settings.MIN_TIME_BUCKETS_FOR_TREND
    ):
        return []

    # -----------------------------------------------------
    # Expand negative aspects
    # -----------------------------------------------------

    exploded = df.explode(
        "negative_aspects"
    )

    exploded = exploded.dropna(
        subset=["negative_aspects"]
    )

    if exploded.empty:
        return []

    # -----------------------------------------------------
    # Number of reviews per month
    # -----------------------------------------------------

    total_per_month = (
        df.groupby("month").size()
    )

    # -----------------------------------------------------
    # Negative aspect mentions per month
    # -----------------------------------------------------

    issue_counts = (
        exploded
        .groupby(
            [
                "month",
                "negative_aspects",
            ]
        )
        .size()
        .unstack(fill_value=0)
    )

    issue_counts = issue_counts.reindex(
        months,
        fill_value=0,
    )

    # -----------------------------------------------------
    # Convert counts to percentage of reviews
    # -----------------------------------------------------

    issue_share = (
        issue_counts.div(
            total_per_month.reindex(
                months,
                fill_value=1,
            ),
            axis=0,
        )
        * 100
    )

    emerging = []

    x = np.arange(
        len(months)
    )

    # -----------------------------------------------------
    # Evaluate every aspect
    # -----------------------------------------------------

    for aspect in issue_share.columns:

        series = (
            issue_share[
                aspect
            ].values
        )

        if len(series) < 2:
            continue

        first = series[0]
        last = series[-1]

        increase = (
            last - first
        )

        # Linear slope gives us the overall direction.
        slope = (
            np.polyfit(
                x,
                series,
                1,
            )[0]
            if len(series) > 1
            else 0
        )

        if (
            increase
            >= settings.EMERGING_ISSUE_MIN_INCREASE_PP
            and slope > 0
        ):

            emerging.append({
                "aspect": aspect,

                "monthly_share": [
                    {
                        "month": month,
                        "share_pct": round(
                            float(share),
                            1,
                        ),
                    }
                    for month, share
                    in zip(
                        months,
                        series,
                    )
                ],

                "increase_pp": round(
                    float(increase),
                    1,
                ),
            })

    emerging.sort(
        key=lambda item: -item["increase_pp"]
    )

    return emerging


# =========================================================
# NEGATIVE SENTIMENT FORECAST
# =========================================================

def forecast_negative_trend(
    sentiment_series: List[Dict],
    sufficiency: Optional[Dict] = None,
) -> Dict:
    """
    Fit a simple straight-line trend to monthly negative
    sentiment percentages and project the next two months.

    This is a trend projection, not a sophisticated
    forecasting model.
    """

    insufficient_reason = None

    if (
        len(sentiment_series)
        < settings.MIN_TIME_BUCKETS_FOR_TREND
    ):
        insufficient_reason = (
            "Insufficient historical data for forecasting."
        )

    elif sufficiency is not None and not sufficiency.get("sufficient", True):
        insufficient_reason = (
            "Insufficient historical data for a reliable forecast. "
            + (sufficiency.get("reason") or "")
        ).strip()

    if insufficient_reason:

        return {
            "available": False,

            "message": insufficient_reason,

            "projected": [],

            "change_pct": None,
        }

    negatives = [
        item["negative"]
        for item in sentiment_series
    ]

    x = np.arange(
        len(negatives)
    )

    slope, intercept = np.polyfit(
        x,
        negatives,
        1,
    )

    future_x = [
        len(negatives),
        len(negatives) + 1,
    ]

    projected_vals = [
        max(
            0.0,
            min(
                100.0,
                slope * xi + intercept,
            ),
        )
        for xi in future_x
    ]

    # -----------------------------------------------------
    # Future month labels
    # -----------------------------------------------------

    try:

        last_period = pd.Period(
            sentiment_series[-1]["month"],
            freq="M",
        )

        projected_months = [
            str(last_period + 1),
            str(last_period + 2),
        ]

    except Exception:

        projected_months = [
            "Next period",
            "Following period",
        ]

    return {
        "available": True,

        "message": None,

        "projected": [
            {
                "month": month,
                "negative": round(
                    value,
                    1,
                ),
            }
            for month, value
            in zip(
                projected_months,
                projected_vals,
            )
        ],

        "change_pct": round(
            projected_vals[-1]
            - negatives[-1],
            1,
        ),
    }


# =========================================================
# MAIN TREND ANALYSIS
# =========================================================

def analyze_trends(
    analyzed_rows: List[Dict],
) -> Dict:

    df = build_time_series(
        analyzed_rows
    )

    if df is None:

        return {
            "available": False,

            "message":
                "Not enough historical data for trend detection. "
                "Include a 'date' column with at least a few distinct "
                "dates to unlock trend analysis.",

            "sentiment_over_time": [],

            "emerging_issues": [],

            "emerging_issues_message":
                "Not enough historical data for trend detection.",

            "forecast": {
                "available": False,

                "message":
                    "Insufficient historical data for forecasting.",

                "projected": [],

                "change_pct": None,
            },
        }

    months = sorted(
        df["month"].unique()
    )

    sentiment_series = (
        sentiment_over_time(
            df
        )
    )

    sufficiency = _trend_data_sufficiency(
        df,
        months,
    )

    return {
        "available": True,

        "message":
            None
            if sufficiency["sufficient"]
            else (
                "Trend and forecast data is shown with reduced "
                "confidence: " + sufficiency["reason"]
            ),

        "sentiment_over_time":
            sentiment_series,

        "emerging_issues":
            detect_emerging_issues(df)
            if sufficiency["sufficient"]
            else [],

        "emerging_issues_message":
            None
            if sufficiency["sufficient"]
            else (
                "Not enough reviews per time period to reliably "
                "detect emerging issues. " + sufficiency["reason"]
            ),

        "forecast":
            forecast_negative_trend(
                sentiment_series,
                sufficiency=sufficiency,
            ),
    }