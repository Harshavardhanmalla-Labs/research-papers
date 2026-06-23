"""Risk-acceptance / POA&M pathway.

Records the operational practice of consciously accepting residual risk
under documented compensating controls and a review trigger. This is a
*recording* pathway only; it does not constitute or assert compliance.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

__all__ = [
    "REQUIRED_RISK_FIELDS",
    "accept_risk",
    "reawaken_expired_acceptances",
    "review_trigger_fired",
    "validate_risk_acceptance_payload",
]

REQUIRED_RISK_FIELDS = (
    "risk_acceptance_reason",
    "risk_acceptance_compensating_controls",
    "risk_acceptance_expiration_date",
    "risk_acceptance_review_trigger",
    "risk_acceptance_approver_id",
)


def validate_risk_acceptance_payload(payload: Mapping[str, Any]) -> None:
    """Raise ValueError if any required risk-acceptance field is missing/empty."""
    for key in REQUIRED_RISK_FIELDS:
        if key not in payload or payload[key] in (None, ""):
            raise ValueError(f"risk acceptance payload missing required field: {key}")


def _to_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise ValueError(f"cannot parse expiration date: {value!r}")


def accept_risk(
    pair_row: Mapping[str, Any],
    approval_decision: Any,
    now: datetime,
) -> dict[str, Any]:
    """Build an accepted-risk record from an ApprovalDecision."""
    payload = getattr(approval_decision, "risk_acceptance", None)
    if payload is None:
        raise ValueError("approval_decision carries no risk_acceptance payload")
    validate_risk_acceptance_payload(payload)
    record = {
        "pair_id": pair_row["pair_id"],
        "cve_id": pair_row.get("cve_id"),
        "host_id": pair_row.get("host_id"),
        "accepted_at": now.isoformat().replace("+00:00", "Z"),
        **dict(payload),
    }
    return record


def reawaken_expired_acceptances(
    accepted_risk_records: Sequence[Mapping[str, Any]],
    now: datetime,
) -> list[dict[str, Any]]:
    """Return records whose acceptance expired on or before `now`."""
    today = now.date()
    out: list[dict[str, Any]] = []
    for rec in accepted_risk_records:
        exp = rec.get("risk_acceptance_expiration_date")
        if exp is None:
            continue
        if _to_date(exp) <= today:
            out.append(dict(rec))
    return out


def review_trigger_fired(
    record: Mapping[str, Any],
    outcome_state: Mapping[str, Any] | None,
    exploit_signal_state: Mapping[str, Any] | None = None,
) -> bool:
    """Whether a record's review trigger has fired (excluding expiration)."""
    trigger = record.get("risk_acceptance_review_trigger")
    cve = record.get("cve_id")
    if trigger == "KEV_ADDED":
        if outcome_state and cve in outcome_state:
            return bool(outcome_state[cve].get("kev_added", False))
        return False
    if trigger == "EPSS_PERCENTILE_CROSSED":
        if exploit_signal_state and cve in exploit_signal_state:
            return bool(exploit_signal_state[cve].get("percentile_crossed", False))
        return False
    # EXPIRATION_DATE and unknown triggers are not "fired" here; expiry is
    # handled by reawaken_expired_acceptances.
    return False
