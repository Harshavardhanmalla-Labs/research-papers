"""Tests for paper2_runtime.pilot_gate (Step 7)."""

from __future__ import annotations

import json

from paper2_runtime import pilot_gate as pg
from paper2_runtime.pilot_gate import (
    FALLBACK,
    PROCEED,
    STOP_DATA_OR_CACHE_FAILURE,
    STOP_FREEZE_OR_AUDIT_FAILURE,
    STOP_STOP_RULE_FAILURE,
    compute_pilot_gate,
    write_pilot_gate_decision,
)


def _write_batch_summary(tmp_path, batch_id, *, wallclock, seed_runs, witness="abc",
                        cells_completed=12, freeze_status="OK", stop_rules=None):
    batch_dir = tmp_path / "results" / batch_id
    audit_dir = tmp_path / "audit" / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "batch_summary.json").write_text(json.dumps({
        "schema_version": 1, "batch_id": batch_id,
        "wallclock_seconds_total": wallclock,
        "seed_runs_completed": seed_runs,
        "per_seed_run_seconds_mean": wallclock / max(1, seed_runs),
        "cells_completed": cells_completed,
        "freeze_witness_id": witness,
    }))
    (audit_dir / "freeze_invariant_result.json").write_text(json.dumps({
        "status": freeze_status,
    }))
    (batch_dir / "stop_rule_evaluation.json").write_text(json.dumps({
        "triggered_rules": [{"rule_id": r} for r in (stop_rules or ["K1", "S-A", "K3"])],
    }))


def _redirect_dirs(monkeypatch, tmp_path):
    monkeypatch.setattr(pg, "RESULT_DIR", tmp_path / "results")
    monkeypatch.setattr(pg, "AUDIT_DIR", tmp_path / "audit")


def test_proceed_decision_when_projection_fits(tmp_path, monkeypatch):
    _redirect_dirs(monkeypatch, tmp_path)
    # Total pilot wallclock 800s / 288 seed-runs = 2.78s/sr -> projected primary ~ 1.1h
    for bid, sr in (("B-pilot-primary", 72), ("B-pilot-capacity", 90),
                    ("B-pilot-blackout", 54), ("B-pilot-ablation", 72)):
        _write_batch_summary(tmp_path, bid, wallclock=200.0, seed_runs=sr)
    decision = compute_pilot_gate()
    assert decision["decision"] == PROCEED
    assert decision["pilot_batches_completed"] == 4
    assert decision["pilot_seed_runs_completed"] == 288


def test_fallback_when_projection_too_long(tmp_path, monkeypatch):
    _redirect_dirs(monkeypatch, tmp_path)
    # 200 s/seed-run -> projected primary 80h -> FALLBACK
    for bid, sr in (("B-pilot-primary", 72), ("B-pilot-capacity", 90),
                    ("B-pilot-blackout", 54), ("B-pilot-ablation", 72)):
        _write_batch_summary(tmp_path, bid, wallclock=sr * 200.0, seed_runs=sr)
    decision = compute_pilot_gate()
    assert decision["decision"] == FALLBACK


def test_stop_on_freeze_failure(tmp_path, monkeypatch):
    _redirect_dirs(monkeypatch, tmp_path)
    for bid, sr in (("B-pilot-primary", 72), ("B-pilot-capacity", 90),
                    ("B-pilot-blackout", 54), ("B-pilot-ablation", 72)):
        _write_batch_summary(tmp_path, bid, wallclock=100.0, seed_runs=sr,
                             freeze_status=("FAIL" if bid == "B-pilot-blackout" else "OK"))
    decision = compute_pilot_gate()
    assert decision["decision"] == STOP_FREEZE_OR_AUDIT_FAILURE


def test_stop_on_K5_K6_hard_halt(tmp_path, monkeypatch):
    _redirect_dirs(monkeypatch, tmp_path)
    for bid, sr in (("B-pilot-primary", 72), ("B-pilot-capacity", 90),
                    ("B-pilot-blackout", 54), ("B-pilot-ablation", 72)):
        rules = ["K1", "K3", "K6"] if bid == "B-pilot-primary" else ["K1", "K3"]
        _write_batch_summary(tmp_path, bid, wallclock=100.0, seed_runs=sr, stop_rules=rules)
    decision = compute_pilot_gate()
    assert decision["decision"] == STOP_STOP_RULE_FAILURE


def test_stop_on_missing_batch_summary(tmp_path, monkeypatch):
    _redirect_dirs(monkeypatch, tmp_path)
    # Only 3 of 4 batches present.
    for bid, sr in (("B-pilot-primary", 72), ("B-pilot-capacity", 90), ("B-pilot-blackout", 54)):
        _write_batch_summary(tmp_path, bid, wallclock=100.0, seed_runs=sr)
    decision = compute_pilot_gate()
    assert decision["decision"] == STOP_DATA_OR_CACHE_FAILURE


def test_write_pilot_gate_decision_creates_both_files(tmp_path, monkeypatch):
    _redirect_dirs(monkeypatch, tmp_path)
    for bid, sr in (("B-pilot-primary", 72), ("B-pilot-capacity", 90),
                    ("B-pilot-blackout", 54), ("B-pilot-ablation", 72)):
        _write_batch_summary(tmp_path, bid, wallclock=200.0, seed_runs=sr)
    decision = compute_pilot_gate()
    j, m = write_pilot_gate_decision(
        decision, out_json=tmp_path / "decision.json", out_md=tmp_path / "decision.md",
    )
    assert j.exists()
    assert m.exists()
    payload = json.loads(j.read_text())
    assert payload["decision"] == PROCEED
