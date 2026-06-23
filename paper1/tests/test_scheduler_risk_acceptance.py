"""Risk-acceptance / POA&M pathway tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import pytest

from paper1.scheduler.risk_acceptance import (
    accept_risk,
    reawaken_expired_acceptances,
    review_trigger_fired,
    validate_risk_acceptance_payload,
)

NOW = datetime(2025, 6, 10, 12, 0, tzinfo=UTC)


@dataclass
class _Approval:
    risk_acceptance: dict[str, Any] | None


def _payload(**overrides):
    base = {
        "risk_acceptance_reason": "deferred under policy",
        "risk_acceptance_compensating_controls": ["network_isolation"],
        "risk_acceptance_expiration_date": date(2025, 9, 8),
        "risk_acceptance_review_trigger": "KEV_ADDED",
        "risk_acceptance_approver_id": "approver:A",
    }
    base.update(overrides)
    return base


def _row():
    return {"pair_id": "H-1:CVE-2024-0001", "cve_id": "CVE-2024-0001", "host_id": "H-1"}


def test_validate_payload_ok():
    validate_risk_acceptance_payload(_payload())


def test_validate_missing_reason_fails():
    bad = _payload()
    del bad["risk_acceptance_reason"]
    with pytest.raises(ValueError):
        validate_risk_acceptance_payload(bad)


def test_accept_risk_builds_record():
    rec = accept_risk(_row(), _Approval(_payload()), NOW)
    assert rec["pair_id"] == "H-1:CVE-2024-0001"
    assert rec["risk_acceptance_review_trigger"] == "KEV_ADDED"
    assert "accepted_at" in rec


def test_accept_risk_without_payload_raises():
    with pytest.raises(ValueError):
        accept_risk(_row(), _Approval(None), NOW)


def test_reawaken_on_expiration():
    rec = {**_row(), **_payload(risk_acceptance_expiration_date=date(2025, 6, 1))}
    out = reawaken_expired_acceptances([rec], NOW)
    assert len(out) == 1


def test_no_reawaken_before_expiration():
    rec = {**_row(), **_payload(risk_acceptance_expiration_date=date(2025, 12, 1))}
    out = reawaken_expired_acceptances([rec], NOW)
    assert out == []


def test_kev_added_trigger_fires():
    rec = {**_row(), **_payload(risk_acceptance_review_trigger="KEV_ADDED")}
    outcome_state = {"CVE-2024-0001": {"kev_added": True}}
    assert review_trigger_fired(rec, outcome_state)


def test_kev_added_trigger_not_fired_without_outcome():
    rec = {**_row(), **_payload(risk_acceptance_review_trigger="KEV_ADDED")}
    assert not review_trigger_fired(rec, None)
    assert not review_trigger_fired(rec, {"CVE-2024-0001": {"kev_added": False}})


def test_epss_trigger_fires():
    rec = {**_row(), **_payload(risk_acceptance_review_trigger="EPSS_PERCENTILE_CROSSED")}
    state = {"CVE-2024-0001": {"percentile_crossed": True}}
    assert review_trigger_fired(rec, None, state)


def test_expiration_trigger_not_fired_via_review():
    rec = {**_row(), **_payload(risk_acceptance_review_trigger="EXPIRATION_DATE")}
    assert not review_trigger_fired(rec, {"CVE-2024-0001": {"kev_added": True}})
