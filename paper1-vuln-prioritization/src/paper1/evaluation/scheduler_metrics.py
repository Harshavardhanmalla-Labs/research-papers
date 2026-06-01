"""Scheduler-derived metrics: feasibility, risk-acceptance rate, POA&M compliance."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from paper1.scheduler.risk_acceptance import review_trigger_fired

__all__ = [
    "deferred_count",
    "escalation_count",
    "poam_review_trigger_compliance",
    "risk_acceptance_rate",
    "scheduled_count",
    "scheduler_feasibility_rate",
]


def _list_len(obj: Any, attr: str, count_attr: str) -> int:
    """Length of a list attribute (object or dict), or a precomputed count."""
    if hasattr(obj, attr):
        return len(getattr(obj, attr))
    if isinstance(obj, Mapping):
        if attr in obj and obj[attr] is not None:
            return len(obj[attr])
        if count_attr in obj and obj[count_attr] is not None:
            return int(obj[count_attr])
    return 0


def scheduled_count(schedule_result: Any) -> int:
    return _list_len(schedule_result, "scheduled", "scheduled_count")


def deferred_count(schedule_result: Any) -> int:
    return _list_len(schedule_result, "deferred", "deferred_count")


def escalation_count(schedule_result: Any) -> int:
    return _list_len(schedule_result, "escalations", "escalation_count")


def _accepted_risk_count(schedule_result: Any) -> int:
    return _list_len(schedule_result, "accepted_risk", "accepted_risk_count")


def _used_capacity(obj: Any) -> int:
    if hasattr(obj, "used_capacity"):
        return int(obj.used_capacity)
    if isinstance(obj, Mapping):
        return int(obj.get("used_capacity", 0))
    return 0


def _capacity(obj: Any) -> int:
    if hasattr(obj, "capacity"):
        return int(obj.capacity)
    if isinstance(obj, Mapping):
        return int(obj.get("capacity", 0))
    return 0


def _iter_results(schedule_results_or_df: Any):
    if isinstance(schedule_results_or_df, pd.DataFrame):
        return [row.to_dict() for _, row in schedule_results_or_df.iterrows()]
    return list(schedule_results_or_df)


def scheduler_feasibility_rate(schedule_results_or_df: Any) -> float:
    """Fraction of windows feasible (no escalations and used_capacity <= capacity)."""
    results = _iter_results(schedule_results_or_df)
    if not results:
        return np.nan
    feasible = 0
    for r in results:
        ok = escalation_count(r) == 0 and _used_capacity(r) <= _capacity(r)
        if ok:
            feasible += 1
    return feasible / len(results)


def risk_acceptance_rate(schedule_results_or_df: Any) -> float:
    """Accepted-risk decisions / total decisions across windows."""
    results = _iter_results(schedule_results_or_df)
    accepted = 0
    total = 0
    for r in results:
        a = _accepted_risk_count(r)
        accepted += a
        total += scheduled_count(r) + deferred_count(r) + a
    if total == 0:
        return np.nan
    return accepted / total


def poam_review_trigger_compliance(
    accepted_risk_records: Sequence[Mapping[str, Any]],
    outcome_state: Mapping[str, Any] | None,
) -> float:
    """Of records whose review trigger fired, fraction reviewed / reopened."""
    fired = []
    for rec in accepted_risk_records:
        if review_trigger_fired(rec, outcome_state):
            fired.append(rec)
    if not fired:
        return np.nan
    complied = sum(
        1
        for rec in fired
        if bool(rec.get("review_completed")) or bool(rec.get("returned_to_open"))
    )
    return complied / len(fired)
