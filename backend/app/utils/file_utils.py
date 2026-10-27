from __future__ import annotations
import io
from typing import Dict, Optional, Tuple

import pandas as pd

REVIEW_COLUMN_CANDIDATES = ["review", "text", "review_text", "feedback", "comment", "comments", "review_body"]
OPTIONAL_COLUMNS = ["rating", "date", "product", "category", "customer_id"]


class FileParsingError(Exception):
    pass


def load_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    lower = filename.lower()
    try:
        if lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif lower.endswith(".xlsx") or lower.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise FileParsingError("Unsupported file type. Please upload a .csv or .xlsx file.")
    except FileParsingError:
        raise
    except Exception as exc:
        raise FileParsingError(f"Could not parse the uploaded file: {exc}")

    if df.empty:
        raise FileParsingError("The uploaded file contains no rows.")

    return df


def detect_review_column(df: pd.DataFrame) -> Optional[str]:
    normalized = {c.lower().strip(): c for c in df.columns}
    for candidate in REVIEW_COLUMN_CANDIDATES:
        if candidate in normalized:
            return normalized[candidate]

    # fallback: pick the string column with the highest average text length
    best_col, best_len = None, 0
    for col in df.columns:
        if df[col].dtype == object:
            avg_len = df[col].dropna().astype(str).str.len().mean() or 0
            if avg_len > best_len and avg_len > 15:
                best_col, best_len = col, avg_len
    return best_col


def detect_optional_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    normalized = {c.lower().strip(): c for c in df.columns}
    detected = {}
    for opt in OPTIONAL_COLUMNS:
        detected[opt] = normalized.get(opt)
    return detected
