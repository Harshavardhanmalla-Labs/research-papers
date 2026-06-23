"""Five-phase capacity-constrained scheduler.

Phases: (1) KEV-deadline override, (2) reawaken expired/triggered risk
acceptances, (3) greedy fill under blackout + constraints + approval,
(4) patch-bundle expansion, (5) summary. Every decision is recorded as a
hash-chained AuditDecisionRecord. No remediation is performed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from paper1 import __framework_version__
from paper1.audit.hash_chain import AuditLogger
from paper1.scheduler.approver import BaseApproverPolicy
from paper1.scheduler.blackout import blackout_active
from paper1.scheduler.constraints import (
    all_constraints_satisfied,
    check_domain_controller_staging,
    check_group_cap,
)
from paper1.scheduler.risk_acceptance import (
    accept_risk,
    reawaken_expired_acceptances,
    review_trigger_fired,
)
from paper1.utils.time import ensure_utc

__all__ = [
    "DeferredPair",
    "ScheduleResult",
    "ScheduledPair",
    "add_business_days",
    "schedule_window",
]

FRAMEWORK_VERSION = __framework_version__
KEV_OVERRIDE_HOURS = 48

_REQUIRED_COLUMNS = ["pair_id", "cve_id", "host_id", "priority_score", "rank", "strategy_name"]
_OPTIONAL_COLUMNS = [
    "host_role",
    "group_id",
    "kev_due_date",
    "complexity_score",
    "bundle_group",
    "dependency_group",
]


@dataclass(frozen=True)
class DeferredPair:
    pair_id: str
    cve_id: str
    host_id: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScheduledPair:
    pair_id: str
    cve_id: str
    host_id: str
    scheduled_reason: str
    approval_decision: str
    scheduled_at: datetime
    effective_remediation_time: datetime


@dataclass(frozen=True)
class ScheduleResult:
    window_id: str
    strategy_name: str
    scheduled: list[ScheduledPair]
    deferred: list[DeferredPair]
    accepted_risk: list[dict[str, Any]]
    escalations: list[dict[str, Any]]
    capacity: int
    used_capacity: int
    audit_log_path: str
    created_at: datetime


def add_business_days(dt: datetime, n: int) -> datetime:
    """Advance `dt` by `n` business days (Mon-Fri); holidays ignored."""
    if n <= 0:
        return dt
    cur = dt
    added = 0
    while added < n:
        cur = cur + timedelta(days=1)
        if cur.weekday() < 5:
            added += 1
    return cur


def _parse_due(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _kev_override(row: Mapping[str, Any], now: datetime) -> bool:
    due = _parse_due(row.get("kev_due_date"))
    if due is None:
        return False
    deadline = datetime.combine(due, datetime.max.time(), tzinfo=now.tzinfo)
    return deadline <= now + timedelta(hours=KEV_OVERRIDE_HOURS)


def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def _normalize_rows(ranked_queue: pd.DataFrame) -> list[dict[str, Any]]:
    """Sorted (rank, pair_id) list of plain dicts with optional-column defaults."""
    ordered = ranked_queue.sort_values(["rank", "pair_id"]).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for _, r in ordered.iterrows():
        row: dict[str, Any] = {
            "pair_id": str(r["pair_id"]),
            "cve_id": str(r["cve_id"]),
            "host_id": str(r["host_id"]),
            "priority_score": float(r["priority_score"]),
            "rank": int(r["rank"]),
            "strategy_name": str(r["strategy_name"]),
        }
        warnings: list[str] = []
        for col, default in (
            ("host_role", "unknown"),
            ("group_id", None),
            ("kev_due_date", None),
            ("complexity_score", 0.0),
            ("bundle_group", None),
            ("dependency_group", None),
        ):
            if col in ordered.columns and not _is_missing(r[col]):
                row[col] = r[col]
            else:
                row[col] = default
                if col in ("host_role", "complexity_score"):
                    warnings.append(f"missing:{col}")
        row["_warnings"] = warnings
        rows.append(row)
    return rows


def schedule_window(
    ranked_queue: pd.DataFrame,
    capacity: int,
    now: datetime,
    blackout_config: Mapping[str, Any],
    approver_policy: BaseApproverPolicy,
    audit_logger: AuditLogger,
    group_caps: Mapping[str, int] | None = None,
    dependency_state: Mapping[str, bool] | None = None,
    outcome_state: Mapping[str, bool] | None = None,
    bundle_map: Mapping[str, Sequence[str]] | None = None,
    accepted_risk_records: Sequence[Mapping[str, Any]] | None = None,
    seed: int = 0,
) -> ScheduleResult:
    """Schedule a maintenance window. See module docstring for phases."""
    if not isinstance(capacity, int) or capacity <= 0:
        raise ValueError(f"capacity must be a positive int; got {capacity!r}")
    missing_cols = set(_REQUIRED_COLUMNS) - set(ranked_queue.columns)
    if missing_cols:
        raise ValueError(f"ranked_queue missing required columns: {sorted(missing_cols)}")
    ensure_utc(now)

    rows = _normalize_rows(ranked_queue)
    by_id = {r["pair_id"]: r for r in rows}
    strategy_name = rows[0]["strategy_name"] if rows else str(
        ranked_queue["strategy_name"].iloc[0] if len(ranked_queue) else "unknown"
    )
    window_id = f"W-{now.strftime('%Y%m%d')}"

    weights_version = str(ranked_queue.attrs.get("weights_version", "unknown"))
    data_feed_versions = dict(ranked_queue.attrs.get("data_feed_versions", {}))

    scheduled: list[ScheduledPair] = []
    scheduled_meta: list[dict[str, Any]] = []
    scheduled_ids: set[str] = set()
    deferred: list[DeferredPair] = []
    accepted_risk: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    used = 0
    counter = 0

    def _emit(decision_type: str, pair_id: str, **extra: Any) -> None:
        nonlocal counter
        counter += 1
        audit_logger.append(
            record_id=f"ADR-{window_id}-{counter:06d}",
            pair_id=pair_id,
            window_id=window_id,
            decision_type=decision_type,
            weights_version=weights_version,
            data_feed_versions=data_feed_versions,
            framework_version=FRAMEWORK_VERSION,
            created_at=now,
            **extra,
        )

    def _do_schedule(row: dict[str, Any], reason: str, approval_decision: str, delay_days: int) -> None:
        nonlocal used
        eff = add_business_days(now, delay_days)
        scheduled.append(
            ScheduledPair(
                pair_id=row["pair_id"],
                cve_id=row["cve_id"],
                host_id=row["host_id"],
                scheduled_reason=reason,
                approval_decision=approval_decision,
                scheduled_at=now,
                effective_remediation_time=eff,
            )
        )
        scheduled_meta.append(row)
        scheduled_ids.add(row["pair_id"])
        used += 1
        _emit(
            "schedule",
            row["pair_id"],
            approver_id=approver_policy.approver_id,
            approver_decision=approval_decision,
            approver_comments=reason,
        )

    def _do_defer(row: dict[str, Any], reason: str, details: dict[str, Any] | None = None) -> None:
        deferred.append(
            DeferredPair(row["pair_id"], row["cve_id"], row["host_id"], reason, details or {})
        )
        _emit("defer", row["pair_id"], approver_comments=reason)

    def _do_accept_risk(row: dict[str, Any], approval: Any) -> None:
        record = accept_risk(row, approval, now)
        accepted_risk.append(record)
        _emit(
            "accept_risk",
            row["pair_id"],
            approver_id=approval.approver_id,
            approver_decision="accepted_risk",
            risk_acceptance_reason=record["risk_acceptance_reason"],
            risk_acceptance_compensating_controls=record["risk_acceptance_compensating_controls"],
            risk_acceptance_expiration_date=record["risk_acceptance_expiration_date"],
            risk_acceptance_review_trigger=record["risk_acceptance_review_trigger"],
            risk_acceptance_approver_id=record["risk_acceptance_approver_id"],
        )

    # ---- Phase 1: KEV deadline override ---------------------------------
    for row in rows:
        if row["pair_id"] in scheduled_ids:
            continue
        if not _kev_override(row, now):
            continue
        # KEV overrides respect group cap + DC staging, but bypass blackout.
        cap_res = check_group_cap(scheduled_meta, row, group_caps)
        dc_res = check_domain_controller_staging(row, scheduled_meta, outcome_state)
        if not cap_res.allowed:
            escalations.append({"pair_id": row["pair_id"], "reason": cap_res.reason})
            _do_defer(row, cap_res.reason or "GROUP_CAP_REACHED", cap_res.details)
            continue
        if not dc_res.allowed:
            escalations.append({"pair_id": row["pair_id"], "reason": dc_res.reason})
            _do_defer(row, dc_res.reason or "DC_STAGED_ROLLOUT_AWAIT_FIRST", dc_res.details)
            continue
        if used >= capacity:
            escalations.append({"pair_id": row["pair_id"], "reason": "CAPACITY_EXHAUSTED_KEV"})
            _do_defer(row, "CAPACITY_EXHAUSTED_KEV", {})
            continue
        _do_schedule(row, "KEV_DEADLINE_OVERRIDE", "approved", 0)

    # ---- Phase 2: reawaken expired / triggered risk acceptances ---------
    if accepted_risk_records:
        expired = {r["pair_id"]: r for r in reawaken_expired_acceptances(accepted_risk_records, now)}
        for rec in accepted_risk_records:
            fired = review_trigger_fired(rec, (outcome_state and {
                rec.get("cve_id"): {"kev_added": bool(outcome_state.get(rec.get("cve_id"), False))}
            }) or None)
            if rec["pair_id"] in expired or fired:
                pid = rec["pair_id"]
                row = by_id.get(pid, {
                    "pair_id": pid, "cve_id": rec.get("cve_id", ""), "host_id": rec.get("host_id", "")
                })
                deferred.append(
                    DeferredPair(pid, row.get("cve_id", ""), row.get("host_id", ""),
                                 "REAWAKENED_FROM_RISK_ACCEPTANCE",
                                 {"expired": pid in expired, "trigger_fired": bool(fired)})
                )
                _emit("defer", pid, approver_comments="REAWAKENED_FROM_RISK_ACCEPTANCE")

    # ---- Phase 3: greedy fill -------------------------------------------
    for row in rows:
        if used >= capacity:
            break
        if row["pair_id"] in scheduled_ids:
            continue
        bd = blackout_active(row, blackout_config, now)
        if bd.blocked:
            _do_defer(row, bd.reason or "BLACKOUT", bd.details)
            continue
        cres = all_constraints_satisfied(
            row, scheduled_meta, group_caps, dependency_state, outcome_state
        )
        if not cres.allowed:
            _do_defer(row, cres.reason or "CONSTRAINT", cres.details)
            continue
        approval = approver_policy.approve(row, now)
        if approval.decision == "approved":
            _do_schedule(row, approval.reason, "approved", approval.delay_days)
        elif approval.decision == "deferred":
            _do_defer(row, approval.reason, {"delay_days": approval.delay_days})
        else:  # accepted_risk
            _do_accept_risk(row, approval)

    # ---- Phase 4: bundle expansion --------------------------------------
    # A bundled patch ships in the same KB/maintenance action as its
    # already-approved anchor, so it rides the anchor's approved window:
    # blackout and per-pair approval are bypassed, but hard constraints
    # (group caps, dependency, DC staging) and capacity still apply. A
    # partner previously deferred (e.g., by blackout) is rescued from the
    # deferred list.
    if bundle_map:
        for s_row in list(scheduled_meta):
            bg = s_row.get("bundle_group")
            if not bg or bg not in bundle_map:
                continue
            for related_id in sorted(bundle_map[bg]):
                if used >= capacity:
                    break
                if related_id in scheduled_ids:
                    continue
                related = by_id.get(related_id)
                if related is None:
                    continue
                if not all_constraints_satisfied(
                    related, scheduled_meta, group_caps, dependency_state, outcome_state
                ).allowed:
                    continue
                _do_schedule(related, f"BUNDLE_WITH_{s_row['pair_id']}", "approved", 0)
                if any(d.pair_id == related_id for d in deferred):
                    deferred[:] = [d for d in deferred if d.pair_id != related_id]

    # ---- Phase 5: summary -----------------------------------------------
    _emit(
        "schedule",
        f"WINDOW:{window_id}",
        approver_decision="summary",
        approver_comments=(
            f"scheduled={len(scheduled)} deferred={len(deferred)} "
            f"accepted_risk={len(accepted_risk)} escalations={len(escalations)} "
            f"used={used}/{capacity} strategy={strategy_name}"
        ),
    )

    return ScheduleResult(
        window_id=window_id,
        strategy_name=strategy_name,
        scheduled=scheduled,
        deferred=deferred,
        accepted_risk=accepted_risk,
        escalations=escalations,
        capacity=capacity,
        used_capacity=used,
        audit_log_path=str(Path(audit_logger.path)),
        created_at=now,
    )
