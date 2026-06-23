"""Shared metric helpers and per-seed aggregation.

Phase 9 aggregation is intentionally simple: mean / std / count. Bootstrap
confidence intervals and statistical tests arrive in Phase 10.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

__all__ = [
    "aggregate_metrics",
    "is_censored",
    "is_positive",
    "normalize_labels",
    "to_day_number",
    "validate_metric_frame",
]


def is_censored(value: Any) -> bool:
    """True if a label value is missing / censored (None or pd.NA / NaN)."""
    if value is None or value is pd.NA:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def is_positive(value: Any) -> bool:
    """True if a label value is a (non-censored) positive."""
    if is_censored(value):
        return False
    return bool(value)


def to_day_number(value: date | datetime | str) -> float:
    """Convert a date/datetime/ISO-string to a fractional day number."""
    if isinstance(value, datetime):
        frac = (
            value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1e6
        ) / 86400.0
        return float(value.toordinal()) + frac
    if isinstance(value, date):
        return float(value.toordinal())
    if isinstance(value, str):
        s = value.replace("Z", "+00:00")
        try:
            return to_day_number(datetime.fromisoformat(s))
        except ValueError:
            return float(date.fromisoformat(value[:10]).toordinal())
    raise TypeError(f"cannot convert to day number: {value!r} ({type(value).__name__})")


def normalize_labels(labels: pd.Series | pd.DataFrame, label_col: str = "label") -> dict[str, Any]:
    """Return a {pair_id: label_value} mapping from a Series or DataFrame."""
    if isinstance(labels, pd.Series):
        return {str(k): v for k, v in labels.items()}
    if isinstance(labels, pd.DataFrame):
        if "pair_id" not in labels.columns:
            raise ValueError("labels DataFrame missing 'pair_id' column")
        if label_col not in labels.columns:
            raise ValueError(f"labels DataFrame missing {label_col!r} column")
        return {str(pid): v for pid, v in zip(labels["pair_id"], labels[label_col], strict=True)}
    raise TypeError(f"unsupported labels type: {type(labels).__name__}")


def validate_metric_frame(df: pd.DataFrame) -> None:
    """Raise if the per-seed metric frame is missing required columns."""
    required = {"strategy", "metric", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"metric frame missing required columns: {sorted(missing)}")


def aggregate_metrics(per_seed_metric_rows: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    """Aggregate per-seed rows to mean / std / count per (strategy, metric)."""
    df = (
        per_seed_metric_rows
        if isinstance(per_seed_metric_rows, pd.DataFrame)
        else pd.DataFrame(per_seed_metric_rows)
    )
    validate_metric_frame(df)
    out = (
        df.groupby(["strategy", "metric"])["value"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .sort_values(["strategy", "metric"])
        .reset_index(drop=True)
    )
    return out
