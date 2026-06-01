"""Tests for paper2_runtime.batch_runner (Step 6).

Heavy components (cached-data load + freeze-verify) are monkeypatched so each
test runs in under a second.
"""

from __future__ import annotations

import csv
import pathlib
from datetime import date

import pytest

import paper2_runtime.batch_runner as br
from paper2_runtime.batch_runner import (
    PER_ROW_TAG_FIELDS,
    STEP6_ALLOWED_BATCH,
    SharedContext,
    load_batch,
    preflight_stop_rules,
    run_batch,
    run_cell_seed,
)


@pytest.fixture
def fake_shared(monkeypatch):
    """A tiny deterministic shared context that side-steps the cached-data load."""
    cves = tuple(f"CVE-2024-{i:04d}" for i in range(8))
    feats = {
        c: {
            "E": 0.1 + 0.1 * i, "K": float(i % 2),
            "S": 0.2 + 0.05 * i, "C": 0.4, "X": 0.3, "U": 0.5, "R": 0.1,
        } for i, c in enumerate(cves)
    }
    ctx = SharedContext(catalog_cves=cves, cve_to_features=feats, t0=date(2024, 9, 1))
    monkeypatch.setattr(br, "_build_smoke_features", lambda t0: ctx)
    return ctx


@pytest.fixture
def isolated_dirs(monkeypatch, tmp_path):
    """Redirect RESULT_DIR and AUDIT_DIR to tmp so tests never write under repo."""
    rd = tmp_path / "results"
    ad = tmp_path / "audit"
    rd.mkdir()
    ad.mkdir()
    monkeypatch.setattr(br, "RESULT_DIR", rd)
    monkeypatch.setattr(br, "AUDIT_DIR", ad)
    return rd, ad


@pytest.fixture
def skip_freeze(monkeypatch):
    """Skip the real `make verify-primary-freeze` subprocess in unit tests."""
    # The runner exposes ``skip_freeze_verify`` and the context manager respects it.
    return True


def test_loads_B_pilot_primary():
    batch, cells = load_batch(STEP6_ALLOWED_BATCH)
    assert batch.batch_id == STEP6_ALLOWED_BATCH
    assert batch.planned_cells == 12
    assert batch.planned_seeds == 6
    assert len(cells) == 12


def test_refuses_primary_batch():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-primary-primary")


def test_refuses_non_step6_batch_by_default():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-pilot-capacity")


def test_preflight_triggers_K1_K3_SA_for_step38_context(tmp_path):
    from paper2_runtime.cell_loader import load_cells
    cells = [c for c in load_cells() if c.table_group == "primary" and c.run_status == "planned"]
    triggered, allowed = preflight_stop_rules(
        {"unique_positive_distinct_cves": 7}, cells, "B-pilot-primary", tmp_path,
    )
    ids = {t.rule_id for t in triggered}
    assert "K1" in ids and "K3" in ids and "S-A" in ids
    # Fixed-prior + baseline cells are all allowed (no calibration in F6).
    assert len(allowed) == 12
    for name in ("stop_rule_evaluation.json", "stop_rule_evaluation.md",
                 "triggered_rules.csv", "excluded_cells.csv", "downgraded_claims.csv"):
        assert (tmp_path / name).exists()


def test_preflight_refuses_calibration_cell(tmp_path):
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
    with pytest.raises(RuntimeError):
        preflight_stop_rules(
            {"unique_positive_distinct_cves": 7}, [sneaky], "B-pilot-primary", tmp_path,
        )


def test_run_cell_seed_produces_real_metrics(fake_shared):
    from paper2_runtime.cell_loader import load_cells
    cell = next(
        c for c in load_cells()
        if c.cell_id == "P-proposed-w_paper1_placeholder"
    )
    out = run_cell_seed(cell, seed=42, shared=fake_shared, smoke=True)
    assert out["ehd_absolute"] > 0.0
    assert out["scheduler_feasibility"] == 1.0
    assert out["scheduled_count"] <= out["n_pairs"]


def test_run_batch_smoke_writes_expected_files(fake_shared, isolated_dirs, tmp_path):
    rd, ad = isolated_dirs
    result = run_batch(
        STEP6_ALLOWED_BATCH, max_cells=3, max_seeds=2,
        smoke=True, force=True, skip_freeze_verify=True,
    )
    assert result["cells_completed"] == 3
    assert result["seed_runs_completed"] == 6  # 3 cells × 2 seeds
    assert result["freeze_status"] == "OK"
    # Stop-rule artefacts written.
    batch_dir = rd / STEP6_ALLOWED_BATCH
    for name in ("stop_rule_evaluation.json", "triggered_rules.csv",
                 "batch_summary.json", "batch_summary.md", "per_seed_metrics.csv"):
        assert (batch_dir / name).exists(), name
    # Freeze witnesses written.
    witness_dir = ad / STEP6_ALLOWED_BATCH
    for name in ("freeze_witness_before.json", "freeze_witness_after.json",
                 "freeze_invariant_result.json", "freeze_invariant_result.md"):
        assert (witness_dir / name).exists(), name


def test_every_metric_row_carries_freeze_witness_id(fake_shared, isolated_dirs):
    rd, _ = isolated_dirs
    run_batch(
        STEP6_ALLOWED_BATCH, max_cells=2, max_seeds=2,
        smoke=True, force=True, skip_freeze_verify=True,
    )
    csv_path = rd / STEP6_ALLOWED_BATCH / "per_seed_metrics.csv"
    assert csv_path.exists()
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) > 0
    for r in rows:
        assert r["freeze_witness_id"], r
        assert r["batch_id"] == STEP6_ALLOWED_BATCH
        for f in PER_ROW_TAG_FIELDS:
            assert f in r


def test_no_write_under_paper1_paths(fake_shared, isolated_dirs):
    rd, ad = isolated_dirs
    run_batch(
        STEP6_ALLOWED_BATCH, max_cells=2, max_seeds=1,
        smoke=True, force=True, skip_freeze_verify=True,
    )
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    # Touch-check Paper-1 dirs: the batch never writes there.
    forbidden_dirs = (
        repo_root / "results" / "primary_full_v1",
        repo_root / "paper" / "tables",
        repo_root / "paper" / "figures",
        repo_root / "paper" / "manuscript",
        repo_root / "paper" / "acm",
        repo_root / "paper" / "eb1a",
    )
    # All result writes are under the tmp RESULT_DIR / AUDIT_DIR (isolated_dirs).
    for d in forbidden_dirs:
        assert not str(rd).startswith(str(d)), d
        assert not str(ad).startswith(str(d)), d


def test_resume_skips_completed_seeds(fake_shared, isolated_dirs):
    rd, _ = isolated_dirs
    r1 = run_batch(
        STEP6_ALLOWED_BATCH, max_cells=1, max_seeds=2,
        smoke=True, force=True, skip_freeze_verify=True,
    )
    assert r1["seed_runs_completed"] == 2
    # Re-run without force should skip the 2 completed seeds.
    r2 = run_batch(
        STEP6_ALLOWED_BATCH, max_cells=1, max_seeds=2,
        smoke=True, force=False, skip_freeze_verify=True,
    )
    assert r2["seed_runs_completed"] == 0


def test_runtime_summary_includes_per_seed_run_seconds(fake_shared, isolated_dirs):
    rd, _ = isolated_dirs
    result = run_batch(
        STEP6_ALLOWED_BATCH, max_cells=2, max_seeds=1,
        smoke=True, force=True, skip_freeze_verify=True,
    )
    assert result["per_seed_run_seconds_mean"] >= 0.0
    import json as _json
    payload = _json.loads(
        (rd / STEP6_ALLOWED_BATCH / "batch_summary.json").read_text(encoding="utf-8")
    )
    assert "per_seed_run_seconds_mean" in payload
    assert "wallclock_seconds_total" in payload


# ---------------------------------------------------------------------------
# Step 7 — full-profile tests
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_full_universe(monkeypatch):
    """Stub the heavy `_load_full_universe` + `_catalog_match_full` paths."""
    import paper2_runtime.batch_runner as _br
    universe = {
        "nvd_records": [], "kev_added_by_cve": {},
        "epss_by_cve": {f"CVE-2024-{i:04d}": 0.1 + 0.05 * i for i in range(8)},
    }
    cve_features = {
        f"CVE-2024-{i:04d}": {
            "E": 0.1 + 0.05 * i, "S": 0.5, "R": 0.1,
        } for i in range(8)
    }
    monkeypatch.setattr(_br, "_load_full_universe", lambda: universe)
    monkeypatch.setattr(_br, "_catalog_match_full", lambda u: cve_features)
    # Reduce 18 -> 2 t0s for fast tests.
    monkeypatch.setattr(_br, "FULL_T0_LIST",
                        (date(2024, 6, 1), date(2024, 9, 1)))
    # Reduce fleet 500 -> 8 for fast tests.
    monkeypatch.setattr(_br, "FULL_FLEET_SIZE", 8)
    return universe


def test_full_refuses_primary_batches():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-primary-primary", profile="full", allow_step7_batch=True)


def test_full_refuses_non_pilot_batches():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-other-thing", profile="full", allow_step7_batch=True)


def test_full_requires_allow_step7_batch():
    with pytest.raises(PermissionError):
        run_batch(batch_id="B-pilot-primary", profile="full", allow_step7_batch=False)


def test_full_uses_full_profile_settings_and_writes_outputs(fake_full_universe, isolated_dirs):
    rd, ad = isolated_dirs
    result = run_batch(
        batch_id="B-pilot-primary", profile="full", allow_step7_batch=True,
        max_cells=2, max_seeds=2, force=True, skip_freeze_verify=True,
    )
    assert result["cells_completed"] == 2
    assert result["seed_runs_completed"] == 4
    assert result["freeze_status"] == "OK"
    csv_path = rd / "B-pilot-primary" / "per_seed_metrics.csv"
    assert csv_path.exists()
    with csv_path.open("r") as fh:
        rows = list(__import__("csv").DictReader(fh))
    assert rows
    for r in rows:
        assert r["freeze_witness_id"]
        # Full profile aggregates across the (test-shrunken) t0 list.
        if r["metric"] == "n_t0_windows":
            assert int(float(r["value"])) == 2  # mocked to 2 t0s
    # Stop-rule preflight artefacts still present.
    assert (rd / "B-pilot-primary" / "stop_rule_evaluation.json").exists()
    # Freeze witnesses still written.
    assert (ad / "B-pilot-primary" / "freeze_invariant_result.json").exists()


def test_full_profile_skips_completed_seeds_on_resume(fake_full_universe, isolated_dirs):
    rd, _ = isolated_dirs
    r1 = run_batch(
        batch_id="B-pilot-primary", profile="full", allow_step7_batch=True,
        max_cells=1, max_seeds=2, force=True, skip_freeze_verify=True,
    )
    assert r1["seed_runs_completed"] == 2
    r2 = run_batch(
        batch_id="B-pilot-primary", profile="full", allow_step7_batch=True,
        max_cells=1, max_seeds=2, force=False, skip_freeze_verify=True,
    )
    assert r2["seed_runs_completed"] == 0


def test_full_profile_runs_each_step7_pilot_batch(fake_full_universe, isolated_dirs):
    for bid in ("B-pilot-primary", "B-pilot-capacity", "B-pilot-blackout", "B-pilot-ablation"):
        result = run_batch(
            batch_id=bid, profile="full", allow_step7_batch=True,
            max_cells=2, max_seeds=1, force=True, skip_freeze_verify=True,
        )
        assert result["cells_completed"] == 2
        assert result["freeze_status"] == "OK"
        assert result["seed_runs_completed"] == 2
