"""Core five-phase scheduler tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from paper1.audit.hash_chain import AuditLogger
from paper1.scheduler.approver import ApproverPolicyA, ApproverPolicyB, make_approver
from paper1.scheduler.blackout import load_blackout_config
from paper1.scheduler.scheduler import schedule_window

PRIMARY = load_blackout_config("primary")
# Tuesday 20:00 UTC: after business hours, not a CAB day, not Saturday.
TUE_EVENING = datetime(2025, 6, 10, 20, 0, tzinfo=UTC)
# Tuesday 10:00 UTC: within business hours (kiosk/public blackout active).
TUE_BUSINESS = datetime(2025, 6, 10, 10, 0, tzinfo=UTC)


def _queue(specs: list[dict]) -> pd.DataFrame:
    rows = []
    for i, s in enumerate(specs):
        rows.append(
            {
                "pair_id": s["pair_id"],
                "cve_id": s.get("cve_id", f"CVE-2024-{1000 + i:04d}"),
                "host_id": s.get("host_id", f"H-{i}"),
                "priority_score": s.get("priority_score", 1.0 - 0.001 * i),
                "rank": s.get("rank", i + 1),
                "strategy_name": s.get("strategy_name", "proposed_full"),
                "host_role": s.get("host_role", "standard_workstation"),
                "group_id": s.get("group_id"),
                "kev_due_date": s.get("kev_due_date"),
                "complexity_score": s.get("complexity_score", 0.3),
                "bundle_group": s.get("bundle_group"),
                "dependency_group": s.get("dependency_group"),
            }
        )
    columns = [
        "pair_id", "cve_id", "host_id", "priority_score", "rank", "strategy_name",
        "host_role", "group_id", "kev_due_date", "complexity_score",
        "bundle_group", "dependency_group",
    ]
    return pd.DataFrame(rows, columns=columns)


def _logger(tmp_path: Path, name="audit.jsonl") -> AuditLogger:
    return AuditLogger(tmp_path / name)


def _policy_a():
    return make_approver("A", seed=0)


# -----------------------------------------------------------------------
# basics
# -----------------------------------------------------------------------


def test_empty_queue_returns_empty_with_summary(tmp_path):
    q = _queue([])
    logger = _logger(tmp_path)
    res = schedule_window(q, capacity=5, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=logger)
    assert res.scheduled == []
    assert res.used_capacity == 0
    ok, _ = logger.verify_chain()
    assert ok
    # Summary record was emitted.
    assert sum(1 for _ in logger.iter_records()) == 1


def test_capacity_respected(tmp_path):
    q = _queue([{"pair_id": f"H-{i}:CVE-2024-{1000+i:04d}"} for i in range(10)])
    res = schedule_window(q, capacity=3, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path))
    assert res.used_capacity == 3
    assert len(res.scheduled) == 3


def test_no_duplicate_scheduled(tmp_path):
    q = _queue([{"pair_id": f"H-{i}:CVE-2024-{1000+i:04d}"} for i in range(5)])
    res = schedule_window(q, capacity=5, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path))
    ids = [s.pair_id for s in res.scheduled]
    assert len(ids) == len(set(ids))


def test_capacity_must_be_positive(tmp_path):
    with pytest.raises(ValueError):
        schedule_window(_queue([{"pair_id": "H:CVE-2024-0001"}]), capacity=0, now=TUE_EVENING,
                        blackout_config=PRIMARY, approver_policy=_policy_a(),
                        audit_logger=_logger(tmp_path))


def test_missing_required_column_raises(tmp_path):
    q = _queue([{"pair_id": "H:CVE-2024-0001"}]).drop(columns=["rank"])
    with pytest.raises(ValueError):
        schedule_window(q, capacity=5, now=TUE_EVENING, blackout_config=PRIMARY,
                        approver_policy=_policy_a(), audit_logger=_logger(tmp_path))


# -----------------------------------------------------------------------
# KEV override
# -----------------------------------------------------------------------


def test_kev_override_scheduled_before_rank(tmp_path):
    q = _queue([
        {"pair_id": "H-1:CVE-2024-1001", "rank": 1, "complexity_score": 0.2},
        {"pair_id": "H-2:CVE-2024-1002", "rank": 2, "kev_due_date": date(2025, 6, 10)},
    ])
    res = schedule_window(q, capacity=1, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path))
    scheduled_ids = {s.pair_id for s in res.scheduled}
    assert scheduled_ids == {"H-2:CVE-2024-1002"}  # KEV pair wins the single slot


def test_kev_override_bypasses_blackout(tmp_path):
    q = _queue([
        {"pair_id": "H-1:CVE-2024-1001", "host_role": "kiosk",
         "kev_due_date": date(2025, 6, 10)},
    ])
    res = schedule_window(q, capacity=5, now=TUE_BUSINESS, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path))
    assert {s.pair_id for s in res.scheduled} == {"H-1:CVE-2024-1001"}
    assert res.scheduled[0].scheduled_reason == "KEV_DEADLINE_OVERRIDE"


# -----------------------------------------------------------------------
# blackout / constraints in greedy phase
# -----------------------------------------------------------------------


def test_blackout_blocks_non_kev_pair(tmp_path):
    q = _queue([{"pair_id": "H-1:CVE-2024-1001", "host_role": "kiosk"}])
    res = schedule_window(q, capacity=5, now=TUE_BUSINESS, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path))
    assert res.scheduled == []
    assert any(d.reason == "KIOSK_BUSINESS_HOURS" for d in res.deferred)


def test_group_cap_defers(tmp_path):
    q = _queue([
        {"pair_id": "H-1:CVE-2024-1001", "host_role": "member_server", "group_id": "G1"},
        {"pair_id": "H-2:CVE-2024-1002", "host_role": "member_server", "group_id": "G1"},
    ])
    res = schedule_window(q, capacity=5, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path),
                          group_caps={"G1": 1})
    assert res.used_capacity == 1
    assert any(d.reason == "GROUP_CAP_REACHED" for d in res.deferred)


def test_dc_staged_rollout_blocks_second_dc(tmp_path):
    q = _queue([
        {"pair_id": "H-1:CVE-2024-1001", "host_role": "domain_controller", "group_id": "DCG"},
        {"pair_id": "H-2:CVE-2024-1002", "host_role": "domain_controller", "group_id": "DCG"},
    ])
    res = schedule_window(q, capacity=5, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path))
    assert res.used_capacity == 1
    assert any(d.reason == "DC_STAGED_ROLLOUT_AWAIT_FIRST" for d in res.deferred)


# -----------------------------------------------------------------------
# approver policies
# -----------------------------------------------------------------------


def test_policy_a_low_complexity_scheduled(tmp_path):
    q = _queue([{"pair_id": "H-1:CVE-2024-1001", "complexity_score": 0.4}])
    res = schedule_window(q, capacity=5, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=ApproverPolicyA(seed=0), audit_logger=_logger(tmp_path))
    assert len(res.scheduled) == 1
    assert res.scheduled[0].approval_decision == "approved"


def test_policy_b_delay_in_effective_time(tmp_path):
    q = _queue([{"pair_id": "H-1:CVE-2024-1001", "complexity_score": 0.4}])
    res = schedule_window(q, capacity=5, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=ApproverPolicyB(seed=0, config={"low_complexity_delay_business_days": 1}),
                          audit_logger=_logger(tmp_path))
    s = res.scheduled[0]
    assert s.effective_remediation_time > s.scheduled_at


def test_accepted_risk_audited(tmp_path):
    # Force accepted_risk via elevated_approval_probability=0 on high-complexity.
    pol = ApproverPolicyA(seed=0, config={"rho_senior": 0.7, "elevated_approval_probability": 0.0})
    q = _queue([{"pair_id": f"H-{i}:CVE-2024-{2000+i:04d}", "complexity_score": 0.9} for i in range(10)])
    logger = _logger(tmp_path)
    res = schedule_window(q, capacity=10, now=TUE_EVENING, blackout_config=PRIMARY,
                          approver_policy=pol, audit_logger=logger)
    assert len(res.accepted_risk) >= 1
    accept_records = [r for r in logger.iter_records() if r.decision_type == "accept_risk"]
    assert len(accept_records) == len(res.accepted_risk)


# -----------------------------------------------------------------------
# bundle expansion
# -----------------------------------------------------------------------


def test_bundle_expansion_schedules_related(tmp_path):
    # H-2 is a kiosk that greedy defers under business-hours blackout; the
    # bundle anchor H-1 (a standard workstation, not blacked out) pulls it
    # into the same approved window via bundle expansion.
    q = _queue([
        {"pair_id": "H-1:CVE-2024-1001", "rank": 1, "bundle_group": "B1",
         "complexity_score": 0.2, "host_role": "standard_workstation"},
        {"pair_id": "H-2:CVE-2024-1002", "rank": 50, "bundle_group": "B1",
         "complexity_score": 0.2, "host_role": "kiosk"},
    ])
    bundle_map = {"B1": ["H-1:CVE-2024-1001", "H-2:CVE-2024-1002"]}
    res = schedule_window(q, capacity=5, now=TUE_BUSINESS, blackout_config=PRIMARY,
                          approver_policy=_policy_a(), audit_logger=_logger(tmp_path),
                          bundle_map=bundle_map)
    scheduled_ids = {s.pair_id for s in res.scheduled}
    assert "H-2:CVE-2024-1002" in scheduled_ids
    bundle_reason = [s for s in res.scheduled if s.scheduled_reason.startswith("BUNDLE_WITH_")]
    assert bundle_reason
    # H-2 should no longer be listed as deferred (it was rescued).
    assert "H-2:CVE-2024-1002" not in {d.pair_id for d in res.deferred}


# -----------------------------------------------------------------------
# determinism
# -----------------------------------------------------------------------


def test_deterministic_same_seed(tmp_path):
    q = _queue([{"pair_id": f"H-{i}:CVE-2024-{1000+i:04d}", "complexity_score": 0.9} for i in range(15)])
    r1 = schedule_window(q, capacity=10, now=TUE_EVENING, blackout_config=PRIMARY,
                         approver_policy=ApproverPolicyA(seed=3),
                         audit_logger=_logger(tmp_path, "a.jsonl"), seed=3)
    r2 = schedule_window(q, capacity=10, now=TUE_EVENING, blackout_config=PRIMARY,
                         approver_policy=ApproverPolicyA(seed=3),
                         audit_logger=_logger(tmp_path, "b.jsonl"), seed=3)
    assert [s.pair_id for s in r1.scheduled] == [s.pair_id for s in r2.scheduled]
    assert [d.pair_id for d in r1.deferred] == [d.pair_id for d in r2.deferred]
