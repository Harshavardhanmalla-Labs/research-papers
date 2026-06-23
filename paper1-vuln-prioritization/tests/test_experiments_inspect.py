"""Primary result inspector / freeze / compare tests (Phase 14).

Tiny controlled primary outputs (small fleet, 4 strategies, 1-2 seeds) are
generated once, then copied and *mutated* to exercise each failure path.
Nothing here interprets results as findings.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from paper1.experiments.inspect import (
    compare_primary_runs,
    freeze_primary_results,
    inspect_primary_output,
    verify_freeze_manifest,
)
from paper1.experiments.primary import PrimaryRunConfig, run_primary_confirmed

_TEMPLATE = Path("configs/primary_full_template.yaml")
_FAST_STRATEGIES = ["random", "epss_only", "proposed_full", "oracle"]


def _tiny_cfg(seeds) -> PrimaryRunConfig:
    raw = yaml.safe_load(_TEMPLATE.read_text(encoding="utf-8"))
    raw.update(
        {
            "fleet_size": 60,
            "seeds": list(seeds),
            "strategies": list(_FAST_STRATEGIES),
            "excluded_strategies": [],
        }
    )
    return PrimaryRunConfig(**raw)


def _codes(report) -> set[str]:
    return {i.code for i in report.issues}


def _fresh(src: Path, tmp_path: Path) -> Path:
    dst = tmp_path / "out"
    shutil.copytree(src, dst)
    return dst


@pytest.fixture(scope="module")
def valid_dir(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("valid1") / "out1"
    run_primary_confirmed(_tiny_cfg([1]), max_seeds=1, out_override=str(out))
    return out


@pytest.fixture(scope="module")
def valid_dir_2seed(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("valid2") / "out2"
    run_primary_confirmed(_tiny_cfg([1, 2]), max_seeds=2, out_override=str(out))
    return out


# ---------------------------------------------------------------------------
# valid output
# ---------------------------------------------------------------------------


def test_inspect_passes_on_valid_output(valid_dir):
    report = inspect_primary_output(valid_dir, strict=True)
    assert report.passed is True
    assert report.audit_logs_valid is True
    assert report.seed_count == 1
    assert report.strategy_count == len(_FAST_STRATEGIES)
    assert not [i for i in report.issues if i.severity in ("error", "fatal")]


# ---------------------------------------------------------------------------
# structural failures
# ---------------------------------------------------------------------------


def test_missing_manifest_is_fatal(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    (d / "manifest.json").unlink()
    report = inspect_primary_output(d, strict=True)
    assert report.passed is False
    assert "MANIFEST_MISSING" in _codes(report)


def test_broken_audit_log_is_error(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    log = next((d / "seed_001").glob("strategy_*/audit_log.jsonl"))
    with log.open("a", encoding="utf-8") as fh:
        fh.write("this-is-not-valid-json\n")
    report = inspect_primary_output(d, strict=True)
    assert report.passed is False
    assert report.audit_logs_valid is False
    assert "AUDIT_CHAIN_INVALID" in _codes(report)


def test_duplicate_pair_id_is_error(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    rp = d / "seed_001" / "strategy_random" / "ranking.csv"
    df = pd.read_csv(rp)
    pd.concat([df, df.iloc[[0]]], ignore_index=True).to_csv(rp, index=False)
    report = inspect_primary_output(d, strict=True)
    assert "DUPLICATE_PAIR_ID" in _codes(report)
    assert report.passed is False


def test_noncontiguous_ranks_is_error(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    rp = d / "seed_001" / "strategy_random" / "ranking.csv"
    df = pd.read_csv(rp)
    df.loc[0, "rank"] = 999999
    df.to_csv(rp, index=False)
    report = inspect_primary_output(d, strict=True)
    assert "NONCONTIGUOUS_RANKS" in _codes(report)


def test_schedule_pair_not_in_ranking_is_error(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    sp = d / "seed_001" / "strategy_random" / "schedule_history.csv"
    df = pd.read_csv(sp)
    bogus = df.iloc[[0]].copy()
    bogus.loc[bogus.index[0], "pair_id"] = "BOGUS-HOST:CVE-2024-9999"
    pd.concat([df, bogus], ignore_index=True).to_csv(sp, index=False)
    report = inspect_primary_output(d, strict=True)
    assert "SCHEDULE_PAIR_NOT_IN_RANKING" in _codes(report)


# ---------------------------------------------------------------------------
# metric failures
# ---------------------------------------------------------------------------


def test_infinite_metric_is_error(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    mp = d / "metrics" / "per_seed_metrics.csv"
    df = pd.read_csv(mp)
    idx = df.index[df["metric"] == "ehd_absolute"][0]
    df.loc[idx, "value"] = np.inf
    df.to_csv(mp, index=False)
    report = inspect_primary_output(d, strict=True)
    assert "INFINITE_METRIC" in _codes(report)
    assert report.passed is False


def test_allowed_nan_does_not_fail(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    mp = d / "metrics" / "per_seed_metrics.csv"
    df = pd.read_csv(mp)
    idx = df.index[df["metric"] == "kev_breach_rate"][0]
    df.loc[idx, "value"] = np.nan
    df.to_csv(mp, index=False)
    report = inspect_primary_output(d, strict=True)
    assert "UNEXPECTED_NAN" not in _codes(report)
    assert report.passed is True


def test_oracle_worse_than_random_is_error(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    mp = d / "metrics" / "per_seed_metrics.csv"
    df = pd.read_csv(mp)
    mask = (df["metric"] == "ehd_absolute") & (df["strategy"] == "oracle")
    df.loc[mask, "value"] = 1e12
    df.to_csv(mp, index=False)
    report = inspect_primary_output(d, strict=True)
    assert "ORACLE_WORSE_THAN_RANDOM" in _codes(report)
    assert report.passed is False


# ---------------------------------------------------------------------------
# freeze manifest
# ---------------------------------------------------------------------------


def test_freeze_writes_manifest(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    payload = freeze_primary_results(d)
    assert (d / "FREEZE_MANIFEST.json").exists()
    assert payload["file_count"] > 0
    assert payload["manifest_sha256"]


def test_freeze_refuses_overwrite_without_flag(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    freeze_primary_results(d)
    with pytest.raises(FileExistsError):
        freeze_primary_results(d)
    # overwrite=True succeeds
    freeze_primary_results(d, overwrite=True)


def test_verify_freeze_passes_immediately(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    freeze_primary_results(d)
    assert verify_freeze_manifest(d) is True


def test_verify_freeze_fails_after_mutation(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    freeze_primary_results(d)
    summary = d / "summary.md"
    summary.write_text(summary.read_text(encoding="utf-8") + "\nmutated\n", encoding="utf-8")
    assert verify_freeze_manifest(d) is False


def test_verify_freeze_fails_on_extra_file_unless_ignored(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    freeze_primary_results(d)
    extra = d / "metrics" / "EXTRA_NOTE.txt"
    extra.write_text("added after freeze", encoding="utf-8")
    assert verify_freeze_manifest(d) is False
    assert verify_freeze_manifest(d, ignore=["metrics/EXTRA_NOTE.txt"]) is True


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


def test_compare_identical_outputs_is_deterministic(valid_dir, tmp_path):
    a = _fresh(valid_dir, tmp_path / "a")
    b = _fresh(valid_dir, tmp_path / "b")
    cmp = compare_primary_runs(a, b)
    assert cmp["common_seeds"] == [1]
    assert cmp["deterministic_common_seed_metrics_equal"] is True
    assert cmp["differences"]["n_differing_rows_common_seeds"] == 0


def test_compare_different_seed_sets(valid_dir, valid_dir_2seed):
    cmp = compare_primary_runs(valid_dir, valid_dir_2seed)
    assert cmp["seeds_a"] == [1]
    assert cmp["seeds_b"] == [1, 2]
    assert cmp["common_seeds"] == [1]
    assert cmp["seeds_only_b"] == [2]
    # The shared seed (1) is deterministic across the two runs.
    assert cmp["deterministic_common_seed_metrics_equal"] is True
    assert cmp["audit_valid_a"] is True
    assert cmp["audit_valid_b"] is True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _load_cli():
    spec = importlib.util.spec_from_file_location(
        "inspect_cli", "scripts/inspect_primary_results.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_exits_nonzero_on_invalid_strict(valid_dir, tmp_path):
    d = _fresh(valid_dir, tmp_path)
    (d / "manifest.json").unlink()  # make it invalid
    cli = _load_cli()
    assert cli.main(["--output", str(d), "--strict"]) != 0


def test_cli_exits_zero_on_valid(valid_dir):
    cli = _load_cli()
    assert cli.main(["--output", str(valid_dir), "--strict"]) == 0


def test_cli_missing_dir_exits_nonzero(tmp_path):
    cli = _load_cli()
    assert cli.main(["--output", str(tmp_path / "nope"), "--strict"]) != 0
