"""Tests for the Step-6 CLI: scripts/paper2_run_pilot_batch.py."""

from __future__ import annotations

import importlib.util
import pathlib

import paper2_runtime.batch_runner as br
from paper2_runtime.batch_runner import STEP6_ALLOWED_BATCH


def _load_script():
    p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "paper2_run_pilot_batch.py"
    spec = importlib.util.spec_from_file_location("p2_pilot_cli", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_exits_2_on_no_smoke(monkeypatch):
    # We invoke br.main directly because the script just delegates.
    rc = br.main(["--no-smoke"])
    assert rc == 2


def test_script_exits_2_on_non_step6_batch():
    rc = br.main(["--batch-id", "B-pilot-capacity"])
    assert rc == 2


def test_script_exits_2_on_primary_batch():
    rc = br.main(["--batch-id", "B-primary-primary"])
    assert rc == 2


def test_script_runs_smoke_for_B_pilot_primary(monkeypatch, tmp_path):
    """End-to-end CLI invocation with heavy components stubbed."""
    from datetime import date

    from paper2_runtime.batch_runner import SharedContext
    cves = tuple(f"CVE-2024-{i:04d}" for i in range(4))
    feats = {c: {"E": 0.1, "K": 0.0, "S": 0.5, "C": 0.4, "X": 0.3, "U": 0.5, "R": 0.1} for c in cves}
    ctx = SharedContext(catalog_cves=cves, cve_to_features=feats, t0=date(2024, 9, 1))
    monkeypatch.setattr(br, "_build_smoke_features", lambda t0: ctx)
    monkeypatch.setattr(br, "RESULT_DIR", tmp_path / "results")
    monkeypatch.setattr(br, "AUDIT_DIR", tmp_path / "audit")
    (tmp_path / "results").mkdir()
    (tmp_path / "audit").mkdir()
    # ``skip_freeze_verify`` isn't a CLI flag; we use max-cells=2 max-seeds=1 to
    # keep wall-clock tiny, and monkeypatch the verify subprocess to a no-op OK.
    from paper2_runtime.freeze_invariant import FreezeCheck
    monkeypatch.setattr(
        "paper2_runtime.freeze_invariant.run_verify_primary_freeze",
        lambda python=".venv/bin/python": FreezeCheck(0, "OK (monkeypatched)", "OK"),
    )
    rc = br.main(["--batch-id", STEP6_ALLOWED_BATCH, "--smoke",
                  "--max-cells", "2", "--max-seeds", "1", "--force"])
    assert rc == 0
    # batch_summary.json exists in the redirected RESULT_DIR.
    assert (tmp_path / "results" / STEP6_ALLOWED_BATCH / "batch_summary.json").exists()


def test_script_file_present_and_loadable():
    mod = _load_script()
    assert hasattr(mod, "main")


def test_script_refuses_allow_non_step6_in_smoke_run():
    """Even with `--allow-non-step6-batch` the runner still refuses primary batches."""
    rc = br.main(["--batch-id", "B-primary-primary", "--allow-non-step6-batch"])
    assert rc == 2
