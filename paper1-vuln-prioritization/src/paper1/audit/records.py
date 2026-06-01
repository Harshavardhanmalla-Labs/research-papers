"""Convenience constructors for common AuditDecisionRecord shapes.

Phase 1 keeps this thin; richer per-decision-type builders arrive with
the scheduler (Phase 6).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from paper1.utils.time import utc_now

__all__ = ["build_schedule_record", "build_score_record"]


def build_score_record(
    *,
    record_id: str,
    pair_id: str,
    window_id: str,
    priority_score: float,
    feature_values: dict[str, float],
    feature_contributions: dict[str, float],
    weights_version: str,
    data_feed_versions: dict[str, str],
    framework_version: str,
    imputations_applied: list[dict[str, Any]] | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build kwargs for a `decision_type='score'` audit record."""
    return {
        "record_id": record_id,
        "pair_id": pair_id,
        "window_id": window_id,
        "decision_type": "score",
        "priority_score": priority_score,
        "feature_values": feature_values,
        "feature_contributions": feature_contributions,
        "weights_version": weights_version,
        "data_feed_versions": data_feed_versions,
        "imputations_applied": imputations_applied,
        "framework_version": framework_version,
        "created_at": created_at or utc_now(),
    }


def build_schedule_record(
    *,
    record_id: str,
    pair_id: str,
    window_id: str,
    weights_version: str,
    data_feed_versions: dict[str, str],
    framework_version: str,
    approver_id: str | None = None,
    approver_decision: str | None = None,
    approver_comments: str | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build kwargs for a `decision_type='schedule'` audit record."""
    return {
        "record_id": record_id,
        "pair_id": pair_id,
        "window_id": window_id,
        "decision_type": "schedule",
        "weights_version": weights_version,
        "data_feed_versions": data_feed_versions,
        "approver_id": approver_id,
        "approver_decision": approver_decision,
        "approver_comments": approver_comments,
        "framework_version": framework_version,
        "created_at": created_at or utc_now(),
    }


# Re-export the model so callers can `from paper1.audit.records import AuditDecisionRecord`
__all__.append("AuditDecisionRecord")
