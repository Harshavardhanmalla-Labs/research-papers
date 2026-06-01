"""Operational constraint predicates for the scheduler.

All predicates accept ``pair_row`` as a mapping (dict) with keys
``pair_id, cve_id, host_id, host_role, group_id, dependency_group`` and
operate against the running list of already-scheduled pair metadata
dicts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "ConstraintResult",
    "all_constraints_satisfied",
    "check_dependency",
    "check_domain_controller_staging",
    "check_group_cap",
    "dc_first_succeeded",
    "dependency_satisfied",
    "group_cap_violated",
]

# Reason codes
ALLOWED = "ALLOWED"
GROUP_CAP_REACHED = "GROUP_CAP_REACHED"
DEPENDENCY_PENDING = "DEPENDENCY_PENDING"
DC_STAGED_ROLLOUT_AWAIT_FIRST = "DC_STAGED_ROLLOUT_AWAIT_FIRST"


@dataclass(frozen=True)
class ConstraintResult:
    allowed: bool
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


def _group_key(row: Mapping[str, Any]) -> str:
    gid = row.get("group_id")
    if gid:
        return str(gid)
    role = row.get("host_role")
    return str(role) if role else "ungrouped"


# ---------------------------------------------------------------------------
# Group caps
# ---------------------------------------------------------------------------


def check_group_cap(
    scheduled: Sequence[Mapping[str, Any]],
    pair_row: Mapping[str, Any],
    group_caps: Mapping[str, int] | None,
) -> ConstraintResult:
    """Return a ConstraintResult for the per-group capacity constraint."""
    if not group_caps:
        return ConstraintResult(True, ALLOWED, {"group_caps": "none"})
    key = _group_key(pair_row)
    cap = group_caps.get(key)
    if cap is None:
        return ConstraintResult(True, ALLOWED, {"group_key": key, "cap": None})
    count = sum(1 for s in scheduled if _group_key(s) == key)
    if count >= cap:
        return ConstraintResult(
            False, GROUP_CAP_REACHED, {"group_key": key, "cap": cap, "count": count}
        )
    return ConstraintResult(True, ALLOWED, {"group_key": key, "cap": cap, "count": count})


def group_cap_violated(
    scheduled: Sequence[Mapping[str, Any]],
    pair_row: Mapping[str, Any],
    group_caps: Mapping[str, int] | None,
) -> bool:
    return not check_group_cap(scheduled, pair_row, group_caps).allowed


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


def check_dependency(
    pair_row: Mapping[str, Any],
    scheduled: Sequence[Mapping[str, Any]],
    dependency_state: Mapping[str, bool] | None = None,
) -> ConstraintResult:
    """Return a ConstraintResult for the dependency-group prerequisite."""
    dep = pair_row.get("dependency_group")
    if not dep:
        return ConstraintResult(True, ALLOWED, {"dependency_group": None})
    if dependency_state is not None and dep in dependency_state:
        if dependency_state[dep]:
            return ConstraintResult(True, ALLOWED, {"dependency_group": dep, "ready": True})
        return ConstraintResult(
            False, DEPENDENCY_PENDING, {"dependency_group": dep, "ready": False}
        )
    # No state info: allow, but warn so the omission is visible downstream.
    return ConstraintResult(
        True,
        ALLOWED,
        {
            "dependency_group": dep,
            "warning": "dependency_state_missing",
            "scheduled_count": len(scheduled),
        },
    )


def dependency_satisfied(
    pair_row: Mapping[str, Any],
    scheduled: Sequence[Mapping[str, Any]],
    dependency_state: Mapping[str, bool] | None = None,
) -> bool:
    return check_dependency(pair_row, scheduled, dependency_state).allowed


# ---------------------------------------------------------------------------
# Domain-controller staged rollout
# ---------------------------------------------------------------------------


def dc_first_succeeded(
    pair_row: Mapping[str, Any],
    outcome_state: Mapping[str, bool] | None,
) -> bool:
    """Whether the first DC in this pair's group has remediated successfully."""
    if not outcome_state:
        return False
    return bool(outcome_state.get(_group_key(pair_row), False))


def check_domain_controller_staging(
    pair_row: Mapping[str, Any],
    scheduled: Sequence[Mapping[str, Any]],
    outcome_state: Mapping[str, bool] | None = None,
) -> ConstraintResult:
    """First DC in a group may be scheduled; later DCs await first success."""
    if pair_row.get("host_role") != "domain_controller":
        return ConstraintResult(True, ALLOWED, {"role": pair_row.get("host_role")})
    key = _group_key(pair_row)
    dc_already = sum(
        1
        for s in scheduled
        if s.get("host_role") == "domain_controller" and _group_key(s) == key
    )
    if dc_already == 0:
        return ConstraintResult(True, ALLOWED, {"group_key": key, "first_dc": True})
    if dc_first_succeeded(pair_row, outcome_state):
        return ConstraintResult(
            True, ALLOWED, {"group_key": key, "first_dc_success": True}
        )
    return ConstraintResult(
        False,
        DC_STAGED_ROLLOUT_AWAIT_FIRST,
        {"group_key": key, "dc_already_scheduled": dc_already},
    )


# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------


def all_constraints_satisfied(
    pair_row: Mapping[str, Any],
    scheduled: Sequence[Mapping[str, Any]],
    group_caps: Mapping[str, int] | None = None,
    dependency_state: Mapping[str, bool] | None = None,
    outcome_state: Mapping[str, bool] | None = None,
) -> ConstraintResult:
    """Evaluate group cap, dependency, and DC staging; first failure wins."""
    for result in (
        check_group_cap(scheduled, pair_row, group_caps),
        check_dependency(pair_row, scheduled, dependency_state),
        check_domain_controller_staging(pair_row, scheduled, outcome_state),
    ):
        if not result.allowed:
            return result
    return ConstraintResult(True, ALLOWED, {})
