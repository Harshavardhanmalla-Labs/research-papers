"""Scheduler-metric tests."""

from __future__ import annotations

import numpy as np
import pytest

from paper1.evaluation.scheduler_metrics import (
    deferred_count,
    escalation_count,
    poam_review_trigger_compliance,
    risk_acceptance_rate,
    scheduled_count,
    scheduler_feasibility_rate,
)


def _result(scheduled=0, deferred=0, accepted=0, escalations=0, used=0, capacity=10):
    return {
        "scheduled": list(range(scheduled)),
        "deferred": list(range(deferred)),
        "accepted_risk": list(range(accepted)),
        "escalations": list(range(escalations)),
        "used_capacity": used,
        "capacity": capacity,
    }


# -----------------------------------------------------------------------
# feasibility
# -----------------------------------------------------------------------


def test_feasibility_all_feasible():
    results = [_result(used=5, capacity=10), _result(used=10, capacity=10)]
    assert scheduler_feasibility_rate(results) == 1.0


def test_feasibility_one_infeasible_via_escalation():
    results = [_result(used=5, capacity=10), _result(escalations=1, used=5, capacity=10)]
    assert scheduler_feasibility_rate(results) == pytest.approx(0.5)


def test_feasibility_used_exceeds_capacity_infeasible():
    results = [_result(used=11, capacity=10)]
    assert scheduler_feasibility_rate(results) == 0.0


def test_feasibility_empty_nan():
    assert np.isnan(scheduler_feasibility_rate([]))


# -----------------------------------------------------------------------
# risk acceptance rate
# -----------------------------------------------------------------------


def test_risk_acceptance_rate_hand_computed():
    # window: 6 scheduled, 2 deferred, 2 accepted -> total 10, accepted 2 -> 0.2
    results = [_result(scheduled=6, deferred=2, accepted=2)]
    assert risk_acceptance_rate(results) == pytest.approx(0.2)


def test_risk_acceptance_rate_zero_denominator_nan():
    assert np.isnan(risk_acceptance_rate([_result()]))


# -----------------------------------------------------------------------
# POA&M compliance
# -----------------------------------------------------------------------


def test_poam_compliance_with_fired_trigger():
    records = [
        {"pair_id": "p1", "cve_id": "CVE-2024-0001",
         "risk_acceptance_review_trigger": "KEV_ADDED", "review_completed": True},
        {"pair_id": "p2", "cve_id": "CVE-2024-0002",
         "risk_acceptance_review_trigger": "KEV_ADDED", "review_completed": False},
        {"pair_id": "p3", "cve_id": "CVE-2024-0003",
         "risk_acceptance_review_trigger": "KEV_ADDED"},  # trigger not fired
    ]
    outcome_state = {
        "CVE-2024-0001": {"kev_added": True},
        "CVE-2024-0002": {"kev_added": True},
        "CVE-2024-0003": {"kev_added": False},
    }
    # fired: p1, p2; complied: p1 -> 1/2
    assert poam_review_trigger_compliance(records, outcome_state) == pytest.approx(0.5)


def test_poam_compliance_no_fired_nan():
    records = [{"pair_id": "p1", "cve_id": "CVE-2024-0001",
                "risk_acceptance_review_trigger": "KEV_ADDED"}]
    assert np.isnan(poam_review_trigger_compliance(records, {"CVE-2024-0001": {"kev_added": False}}))


# -----------------------------------------------------------------------
# counts
# -----------------------------------------------------------------------


def test_count_helpers_dict():
    r = _result(scheduled=3, deferred=2, escalations=1)
    assert scheduled_count(r) == 3
    assert deferred_count(r) == 2
    assert escalation_count(r) == 1


def test_count_helpers_object():
    from dataclasses import dataclass, field

    @dataclass
    class _R:
        scheduled: list = field(default_factory=lambda: [1, 2])
        deferred: list = field(default_factory=lambda: [1])
        escalations: list = field(default_factory=list)

    r = _R()
    assert scheduled_count(r) == 2
    assert deferred_count(r) == 1
    assert escalation_count(r) == 0
