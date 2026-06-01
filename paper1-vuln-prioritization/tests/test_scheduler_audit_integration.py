"""Scheduler audit hash-chain integration tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pandas as pd

from paper1.audit.hash_chain import AuditLogger, verify_chain
from paper1.scheduler.approver import ApproverPolicyA
from paper1.scheduler.blackout import load_blackout_config
from paper1.scheduler.scheduler import schedule_window

PRIMARY = load_blackout_config("primary")
NOW = datetime(2025, 6, 10, 20, 0, tzinfo=UTC)


def _queue(n: int) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append(
            {
                "pair_id": f"H-{i}:CVE-2024-{1000 + i:04d}",
                "cve_id": f"CVE-2024-{1000 + i:04d}",
                "host_id": f"H-{i}",
                "priority_score": 1.0 - 0.001 * i,
                "rank": i + 1,
                "strategy_name": "proposed_full",
                "host_role": "standard_workstation",
                "group_id": None,
                "kev_due_date": None,
                "complexity_score": 0.3,
                "bundle_group": None,
                "dependency_group": None,
            }
        )
    return pd.DataFrame(rows)


def test_audit_chain_valid_after_scheduling(tmp_path):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    schedule_window(_queue(8), capacity=5, now=NOW, blackout_config=PRIMARY,
                    approver_policy=ApproverPolicyA(seed=0), audit_logger=logger)
    ok, issues = logger.verify_chain()
    assert ok, issues


def test_tampering_breaks_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path)
    schedule_window(_queue(5), capacity=5, now=NOW, blackout_config=PRIMARY,
                    approver_policy=ApproverPolicyA(seed=0), audit_logger=logger)
    lines = path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["pair_id"] = "TAMPERED"
    lines[0] = json.dumps(first, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, issues = verify_chain(path)
    assert not ok
    assert issues


def test_every_decision_has_audit_record(tmp_path):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    res = schedule_window(_queue(6), capacity=3, now=NOW, blackout_config=PRIMARY,
                          approver_policy=ApproverPolicyA(seed=0), audit_logger=logger)
    records = list(logger.iter_records())
    schedule_records = [r for r in records if r.decision_type == "schedule" and not r.pair_id.startswith("WINDOW:")]
    # Each scheduled pair has a schedule record.
    assert len(schedule_records) == len(res.scheduled)
    # A window summary record exists.
    assert any(r.pair_id.startswith("WINDOW:") for r in records)


def test_audit_records_carry_provenance_fields(tmp_path):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    schedule_window(_queue(3), capacity=3, now=NOW, blackout_config=PRIMARY,
                    approver_policy=ApproverPolicyA(seed=0), audit_logger=logger)
    for r in logger.iter_records():
        assert r.framework_version
        assert r.weights_version == "unknown"  # attrs not set on this toy queue
        assert isinstance(r.data_feed_versions, dict)
