"""Compliance / operational-efficacy metrics: KEV deadlines, capacity efficiency."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from paper1.evaluation.metrics import is_censored, is_positive, to_day_number

__all__ = [
    "capacity_efficiency",
    "kev_deadline_breach_rate",
    "kev_remediation_latency",
]


def _remediated_map(schedule_history: pd.DataFrame, remediated_col: str) -> dict[str, Any]:
    if schedule_history is None or schedule_history.empty:
        return {}
    col = remediated_col
    if col not in schedule_history.columns:
        if "effective_remediation_time" in schedule_history.columns:
            col = "effective_remediation_time"
        elif "remediated_at" in schedule_history.columns:
            col = "remediated_at"
        else:
            raise ValueError(f"schedule_history missing remediation column {remediated_col!r}")
    return {str(r["pair_id"]): r[col] for _, r in schedule_history.iterrows()}


def kev_deadline_breach_rate(
    schedule_history: pd.DataFrame,
    kev_pairs: pd.DataFrame,
    due_date_col: str = "kev_due_date",
    remediated_col: str = "remediated_at",
) -> float:
    """Fraction of KEV pairs (with a due date) not remediated by the deadline."""
    if "pair_id" not in kev_pairs.columns or due_date_col not in kev_pairs.columns:
        raise ValueError(f"kev_pairs must have 'pair_id' and {due_date_col!r} columns")
    rem = _remediated_map(schedule_history, remediated_col)
    denom = 0
    breaches = 0
    for _, kp in kev_pairs.iterrows():
        due = kp[due_date_col]
        if is_censored(due):
            continue
        denom += 1
        r = rem.get(str(kp["pair_id"]))
        if r is None:
            breaches += 1
        elif to_day_number(r) > to_day_number(due):
            breaches += 1
    if denom == 0:
        return np.nan
    return breaches / denom


def kev_remediation_latency(
    schedule_history: pd.DataFrame,
    kev_pairs: pd.DataFrame,
    criticality_frame: pd.DataFrame | None = None,
    criticality_threshold: float = 0.7,
    added_col: str = "kev_date_added",
    remediated_col: str = "remediated_at",
) -> dict[str, Any]:
    """Median / p95 / count of days from KEV addition to remediation.

    When ``criticality_frame`` (pair_id + criticality_score) is provided,
    only pairs with criticality above the threshold are counted.
    """
    if "pair_id" not in kev_pairs.columns or added_col not in kev_pairs.columns:
        raise ValueError(f"kev_pairs must have 'pair_id' and {added_col!r} columns")
    rem = _remediated_map(schedule_history, remediated_col)

    allowed: set[str] | None = None
    if criticality_frame is not None:
        if "pair_id" not in criticality_frame.columns or "criticality_score" not in criticality_frame.columns:
            raise ValueError("criticality_frame must have 'pair_id' and 'criticality_score'")
        allowed = {
            str(r["pair_id"])
            for _, r in criticality_frame.iterrows()
            if float(r["criticality_score"]) > criticality_threshold
        }

    latencies: list[float] = []
    for _, kp in kev_pairs.iterrows():
        pid = str(kp["pair_id"])
        if allowed is not None and pid not in allowed:
            continue
        added = kp[added_col]
        r = rem.get(pid)
        if is_censored(added) or r is None:
            continue
        lat = to_day_number(r) - to_day_number(added)
        if lat >= 0:
            latencies.append(lat)
    if not latencies:
        return {"median_days": np.nan, "p95_days": np.nan, "count": 0}
    return {
        "median_days": float(np.median(latencies)),
        "p95_days": float(np.percentile(latencies, 95)),
        "count": len(latencies),
    }


def capacity_efficiency(
    scheduled_pairs: pd.DataFrame,
    labels: pd.DataFrame,
    label_col: str = "label",
) -> float:
    """Fraction of scheduled (non-censored) pairs that are positives."""
    if "pair_id" not in scheduled_pairs.columns:
        raise ValueError("scheduled_pairs must have 'pair_id' column")
    if "pair_id" not in labels.columns or label_col not in labels.columns:
        raise ValueError(f"labels must have 'pair_id' and {label_col!r} columns")
    lab = {str(p): v for p, v in zip(labels["pair_id"], labels[label_col], strict=True)}
    denom = 0
    pos = 0
    for pid in scheduled_pairs["pair_id"]:
        v = lab.get(str(pid), pd.NA)
        if is_censored(v):
            continue
        denom += 1
        if is_positive(v):
            pos += 1
    if denom == 0:
        return np.nan
    return pos / denom
