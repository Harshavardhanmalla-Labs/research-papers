"""Approver policy tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from paper1.scheduler.approver import (
    ApproverPolicyA,
    ApproverPolicyB,
    make_approver,
)
from paper1.scheduler.risk_acceptance import validate_risk_acceptance_payload

NOW = datetime(2025, 6, 10, 10, 0, tzinfo=UTC)


def _row(pair_id, role="member_server", complexity=0.3, kev_due=None):
    return {
        "pair_id": pair_id,
        "cve_id": "CVE-2024-0001",
        "host_id": "H",
        "host_role": role,
        "complexity_score": complexity,
        "kev_due_date": kev_due,
    }


# -----------------------------------------------------------------------
# Policy A
# -----------------------------------------------------------------------


def test_policy_a_low_complexity_approved():
    pol = make_approver("A", seed=0)
    d = pol.approve(_row("P1", complexity=0.5), NOW)
    assert d.decision == "approved"
    assert d.delay_days == 0
    assert d.reason == "LOW_COMPLEXITY_APPROVED"


def test_policy_a_kev_override_approved():
    pol = make_approver("A", seed=0)
    d = pol.approve(_row("P2", complexity=0.9, kev_due=date(2025, 6, 10)), NOW)
    assert d.decision == "approved"
    assert d.reason == "KEV_OVERRIDE_APPROVED"


def test_policy_a_high_complexity_deterministic():
    pol = make_approver("A", seed=0)
    a = pol.approve(_row("P3", complexity=0.9), NOW)
    b = make_approver("A", seed=0).approve(_row("P3", complexity=0.9), NOW)
    assert a.decision == b.decision
    assert a.reason == b.reason
    assert a.decision in {"approved", "deferred", "accepted_risk"}


def test_policy_a_high_complexity_mix_over_pairs():
    pol = make_approver("A", seed=0)
    decisions = {pol.approve(_row(f"P-{i}", complexity=0.9), NOW).decision for i in range(50)}
    # With 50 high-complexity pairs the dominant outcome should be approval.
    assert "approved" in decisions


def test_policy_a_forced_accepted_risk_has_required_fields():
    # elevated_approval_probability=0 pushes most high-complexity pairs to
    # the accepted_risk branch.
    pol = ApproverPolicyA(seed=0, config={"rho_senior": 0.7, "elevated_approval_probability": 0.0})
    found = None
    for i in range(50):
        d = pol.approve(_row(f"PA-{i}", complexity=0.9), NOW)
        if d.decision == "accepted_risk":
            found = d
            break
    assert found is not None
    validate_risk_acceptance_payload(found.risk_acceptance)


# -----------------------------------------------------------------------
# Policy B
# -----------------------------------------------------------------------


def test_policy_b_low_complexity_delay_one():
    pol = make_approver("B", seed=0)
    d = pol.approve(_row("Q1", complexity=0.5), NOW)
    assert d.decision == "approved"
    assert d.delay_days == 1


def test_policy_b_high_complexity_delay_five():
    pol = make_approver("B", seed=0)
    d = pol.approve(_row("Q2", role="member_server", complexity=0.9), NOW)
    assert d.decision == "approved"
    assert d.delay_days == 5


def test_policy_b_restricted_delay_ten_or_accepted_risk():
    pol = make_approver("B", seed=0)
    d = pol.approve(_row("Q3", role="restricted_zone_system", complexity=0.9), NOW)
    assert (d.decision == "approved" and d.delay_days == 10) or d.decision == "accepted_risk"


def test_policy_b_restricted_forced_accepted_risk_fields():
    pol = ApproverPolicyB(
        seed=0,
        config={
            "rho_senior": 0.7,
            "high_complexity_cab_cadence_business_days": 5,
            "restricted_zone_additional_delay_business_days": 5,
            "risk_acceptance_probability_high_complexity_restricted": 1.0,
        },
    )
    d = pol.approve(_row("Q4", role="restricted_zone_system", complexity=0.9), NOW)
    assert d.decision == "accepted_risk"
    validate_risk_acceptance_payload(d.risk_acceptance)


def test_policy_b_kev_override():
    pol = make_approver("B", seed=0)
    d = pol.approve(_row("Q5", complexity=0.9, kev_due=date(2025, 6, 10)), NOW)
    assert d.reason == "KEV_OVERRIDE_APPROVED"


# -----------------------------------------------------------------------
# determinism + errors
# -----------------------------------------------------------------------


def test_same_seed_same_decisions():
    a = make_approver("A", seed=5)
    b = make_approver("A", seed=5)
    for i in range(20):
        row = _row(f"R-{i}", complexity=0.9)
        assert a.approve(row, NOW).decision == b.approve(row, NOW).decision


def test_make_approver_unknown_raises():
    with pytest.raises(ValueError):
        make_approver("Z", seed=0)
