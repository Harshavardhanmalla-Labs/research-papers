"""Tests for the Step-8 primary runner + primary completion gate."""

from __future__ import annotations

import csv
import json
from datetime import date

import pytest

import paper2_runtime.batch_runner as br
from paper2_runtime import primary_gate as pg
from paper2_runtime.batch_runner import (
    run_batch,
)
from paper2_runtime.primary_gate import (
    PRIMARY_COMPLETE_VALID,
    PRIMARY_INCOMPLETE,
    PRIMARY_INVALID_FREEZE,
    PRIMARY_INVALID_ROWS,
    PRIMARY_INVALID_STOP_RULE,
    compute_primary_completion,
)


@pytest.fixture
def fake_full_universe(monkeypatch):
    """Stub the heavy universe + per-(seed,t0) frame builders for fast tests."""
    universe = {
        "nvd_records": [], "kev_added_by_cve": {},
        "epss_by_cve": {f"CVE-2024-{i:04d}": 0.1 + 0.05 * i for i in range(8)},
    }
    cve_features = {
        f"CVE-2024-{i:04d}": {"E": 0.1 + 0.05 * i, "S": 0.5, "R": 0.1} for i in range(8)
    }
    monkeypatch.setattr(br, "_load_full_universe", lambda: universe)
    monkeypatch.setattr(br, "_catalog_match_full", lambda u: cve_features)
    monkeypatch.setattr(br, "FULL_T0_LIST", (date(2024, 6, 1), date(2024, 9, 1)))
    monkeypatch.setattr(br, "FULL_FLEET_SIZE", 8)
    return universe


@pytest.fixture
def isolated_dirs(monkeypatch, tmp_path):
    rd = tmp_path / "results"
    ad = tmp_path / "audit"
    rd.mkdir()
    ad.mkdir()
    monkeypatch.setattr(br, "RESULT_DIR", rd)
    monkeypatch.setattr(br, "AUDIT_DIR", ad)
    monkeypatch.setattr(pg, "RESULT_DIR", rd)
    monkeypatch.setattr(pg, "AUDIT_DIR", ad)
    return rd, ad


# ---------------------------------------------------------------------------
# Runner-side refusals
# ---------------------------------------------------------------------------


def test_primary_refuses_pilot_batch():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-pilot-primary", profile="primary", allow_step8_batch=True)


def test_primary_refuses_non_primary_batch():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-something-else", profile="primary", allow_step8_batch=True)


def test_primary_requires_allow_step8_batch():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-primary-primary", profile="primary", allow_step8_batch=False)


def test_primary_refuses_n_not_30():
    with pytest.raises(PermissionError):
        run_batch(
            batch_id="B-primary-primary", profile="primary", allow_step8_batch=True,
            max_seeds=10,
        )


def test_primary_cli_refuses_pilot_batch():
    rc = br.main(["--batch-id", "B-pilot-primary", "--profile", "primary",
                  "--allow-step8-batch"])
    assert rc == 2


def test_primary_cli_refuses_non_primary_batch():
    rc = br.main(["--batch-id", "B-something", "--profile", "primary",
                  "--allow-step8-batch"])
    assert rc == 2


def test_primary_cli_requires_allow_step8_batch():
    rc = br.main(["--batch-id", "B-primary-primary", "--profile", "primary"])
    assert rc == 2


def test_primary_cli_refuses_max_seeds_not_30():
    rc = br.main(["--batch-id", "B-primary-primary", "--profile", "primary",
                  "--allow-step8-batch", "--max-seeds", "5"])
    assert rc == 2


def test_full_profile_refuses_primary_batch():
    """Step-7 full profile must continue to refuse B-primary-* batches."""
    rc = br.main(["--batch-id", "B-primary-primary", "--full", "--allow-step7-batch"])
    assert rc == 2


def test_calibration_strategy_cell_rejected_by_preflight():
    """Step-8 preflight still refuses calibration / learned cells via _calibration_cells."""
    from paper2_runtime.cell_loader import Cell
    sneaky = Cell(
        cell_id="X-calib", table_group="primary", claim_id="CLM-B1",
        inference_family_id="B1", strategy="proposed_calibrated", weight_vector="w_learned",
        capacity_ratio="0.01", blackout_policy="primary", approver_policy="A",
        label_source="label_a_kev_only", epss_era="v3",
        catalog_strictness="cpe_exact_existing31", ablation="full",
        n_seeds="30", t0_window_set="monthly_18_2023_09_to_2025_02",
        reuse_of_cell_id="", run_status="planned", rationale="forbidden",
        primary_metric="ehd_absolute", secondary_metrics="", diagnostic_metrics="",
    )
    import pathlib
    import tempfile  # noqa: E401

    from paper2_runtime.batch_runner import preflight_stop_rules
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(RuntimeError):
            preflight_stop_rules(
                {"unique_positive_distinct_cves": 7}, [sneaky],
                "B-primary-primary", pathlib.Path(td),
            )


# ---------------------------------------------------------------------------
# Primary runner end-to-end (heavy components stubbed)
# ---------------------------------------------------------------------------


def test_primary_runner_writes_outputs(fake_full_universe, isolated_dirs):
    rd, ad = isolated_dirs
    result = run_batch(
        batch_id="B-primary-primary", profile="primary", allow_step8_batch=True,
        max_cells=2, max_seeds=30,  # 30 enforced; harness fixture cuts heavy paths
        force=True, skip_freeze_verify=True,
    )
    assert result["cells_completed"] == 2
    assert result["seed_runs_completed"] == 60  # 2 cells x 30 seeds
    assert result["freeze_status"] == "OK"
    csv_path = rd / "B-primary-primary" / "per_seed_metrics.csv"
    assert csv_path.exists()


# ---------------------------------------------------------------------------
# Primary completion gate
# ---------------------------------------------------------------------------


def _write_primary_batch(tmp_path, batch_id, *, wallclock, seed_runs, cells_completed=12,
                        freeze_status="OK", stop_rules=None,
                        witness="abc", missing_witness_rows=0,
                        forbidden_strategy=None):
    bdir = tmp_path / "results" / batch_id
    adir = tmp_path / "audit" / batch_id
    bdir.mkdir(parents=True, exist_ok=True)
    adir.mkdir(parents=True, exist_ok=True)
    (bdir / "batch_summary.json").write_text(json.dumps({
        "schema_version": 1, "batch_id": batch_id,
        "wallclock_seconds_total": wallclock,
        "seed_runs_completed": seed_runs,
        "per_seed_run_seconds_mean": wallclock / max(1, seed_runs),
        "cells_completed": cells_completed,
        "freeze_witness_id": witness,
    }))
    (adir / "freeze_invariant_result.json").write_text(json.dumps({
        "status": freeze_status,
    }))
    (bdir / "stop_rule_evaluation.json").write_text(json.dumps({
        "triggered_rules": [{"rule_id": r} for r in (stop_rules or ["K1", "S-A", "K3"])],
    }))
    csv_path = bdir / "per_seed_metrics.csv"
    fields = list(br.PER_ROW_TAG_FIELDS)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        rows = max(1, seed_runs)
        for i in range(rows):
            row = {f: "" for f in fields}
            row["batch_id"] = batch_id
            row["cell_id"] = f"cell-{i}"
            row["seed"] = i + 1
            row["freeze_witness_id"] = "" if i < missing_witness_rows else witness
            row["strategy"] = forbidden_strategy or "epss_only"
            row["weight_vector"] = "na"
            row["metric"] = "ehd_absolute"
            row["value"] = "100.0"
            w.writerow(row)


def test_gate_returns_valid_when_all_clean(tmp_path, isolated_dirs):
    _, _ = isolated_dirs
    for bid, sr in (
        ("B-primary-primary", 360), ("B-primary-capacity", 450),
        ("B-primary-blackout", 270), ("B-primary-ablation", 360),
    ):
        _write_primary_batch(tmp_path, bid, wallclock=600.0, seed_runs=sr)
    completion = compute_primary_completion(tmp_path / "results", tmp_path / "audit")
    assert completion["status"] == PRIMARY_COMPLETE_VALID
    assert completion["primary_batches_completed"] == 4
    assert completion["total_seed_runs_completed"] == 1440


def test_gate_returns_incomplete_if_missing(tmp_path, isolated_dirs):
    for bid, sr in (("B-primary-primary", 360), ("B-primary-capacity", 450)):
        _write_primary_batch(tmp_path, bid, wallclock=600.0, seed_runs=sr)
    completion = compute_primary_completion(tmp_path / "results", tmp_path / "audit")
    assert completion["status"] == PRIMARY_INCOMPLETE


def test_gate_returns_invalid_freeze(tmp_path, isolated_dirs):
    for bid, sr in (
        ("B-primary-primary", 360), ("B-primary-capacity", 450),
        ("B-primary-blackout", 270), ("B-primary-ablation", 360),
    ):
        _write_primary_batch(
            tmp_path, bid, wallclock=600.0, seed_runs=sr,
            freeze_status=("FAIL" if bid == "B-primary-ablation" else "OK"),
        )
    completion = compute_primary_completion(tmp_path / "results", tmp_path / "audit")
    assert completion["status"] == PRIMARY_INVALID_FREEZE


def test_gate_returns_invalid_rows_if_witness_missing(tmp_path, isolated_dirs):
    for bid, sr in (
        ("B-primary-primary", 360), ("B-primary-capacity", 450),
        ("B-primary-blackout", 270), ("B-primary-ablation", 360),
    ):
        _write_primary_batch(
            tmp_path, bid, wallclock=600.0, seed_runs=sr,
            missing_witness_rows=(5 if bid == "B-primary-blackout" else 0),
        )
    completion = compute_primary_completion(tmp_path / "results", tmp_path / "audit")
    assert completion["status"] == PRIMARY_INVALID_ROWS


def test_gate_returns_invalid_stop_rule_on_K5_K6(tmp_path, isolated_dirs):
    for bid, sr in (
        ("B-primary-primary", 360), ("B-primary-capacity", 450),
        ("B-primary-blackout", 270), ("B-primary-ablation", 360),
    ):
        rules = ["K1", "K3", "K6"] if bid == "B-primary-primary" else ["K1", "K3"]
        _write_primary_batch(tmp_path, bid, wallclock=600.0, seed_runs=sr, stop_rules=rules)
    completion = compute_primary_completion(tmp_path / "results", tmp_path / "audit")
    assert completion["status"] == PRIMARY_INVALID_STOP_RULE


def test_gate_rejects_calibration_strategy_in_metric_rows(tmp_path, isolated_dirs):
    for bid, sr in (
        ("B-primary-primary", 360), ("B-primary-capacity", 450),
        ("B-primary-blackout", 270), ("B-primary-ablation", 360),
    ):
        forbid = "proposed_calibrated" if bid == "B-primary-capacity" else None
        _write_primary_batch(
            tmp_path, bid, wallclock=600.0, seed_runs=sr, forbidden_strategy=forbid,
        )
    completion = compute_primary_completion(tmp_path / "results", tmp_path / "audit")
    assert completion["status"] == PRIMARY_INVALID_STOP_RULE


def test_status_makefile_target_does_not_launch_runs():
    """The paper2-primary-status target is shell-only and never invokes the runner."""
    import pathlib
    mk = pathlib.Path(__file__).resolve().parents[1] / "Makefile"
    text = mk.read_text(encoding="utf-8")
    assert "paper2-primary-status:" in text
    # The target's recipe must NOT call `paper2_run_primary_batch.py`.
    chunk = text.split("paper2-primary-status:")[1].split("\n\n")[0]
    assert "paper2_run_primary_batch.py" not in chunk


def test_no_writes_under_paper1_paths(tmp_path, isolated_dirs):
    """compute_primary_completion + write_primary_completion never touch Paper-1 paths."""
    _, _ = isolated_dirs
    for bid, sr in (
        ("B-primary-primary", 360), ("B-primary-capacity", 450),
        ("B-primary-blackout", 270), ("B-primary-ablation", 360),
    ):
        _write_primary_batch(tmp_path, bid, wallclock=600.0, seed_runs=sr)
    completion = compute_primary_completion(tmp_path / "results", tmp_path / "audit")
    j, m = pg.write_primary_completion(
        completion, out_json=tmp_path / "p.json", out_md=tmp_path / "p.md",
    )
    assert j.exists()
    assert m.exists()
    # Sanity: writes are only under tmp_path.
    import pathlib
    repo = pathlib.Path(__file__).resolve().parents[1]
    for forbidden in ("results/primary_full_v1", "paper/tables", "paper/figures",
                       "paper/manuscript", "paper/acm", "paper/eb1a"):
        assert not (repo / forbidden / "p.json").exists()
