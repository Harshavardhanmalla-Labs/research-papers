"""End-to-end smoke experiment runner tests (Phase 11).

These verify that the full pipeline wires together and produces the
documented artifacts on bundled toy fixtures -- they do NOT assert any
research finding. The only ordering checked (oracle EHD <= random EHD)
is a sanity property of the simulated metric, not a paper result.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from paper1.audit.hash_chain import verify_chain
from paper1.experiments.common import load_manifest
from paper1.experiments.smoke import (
    _DEFAULT_CONFIG,
    _load_smoke_config,
    run_smoke_experiment,
    run_smoke_seed,
)

EXPECTED_STRATEGIES = ["random", "epss_only", "kev_first", "proposed_full", "oracle"]
CAPACITY = 20


def _write_config(tmp_path: Path, *, seeds=(1, 2), output_name="out") -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cfg = dict(_load_smoke_config(_DEFAULT_CONFIG))
    cfg["seeds"] = list(seeds)
    cfg["output_dir"] = str(tmp_path / output_name)
    cfg_path = tmp_path / f"experiment_smoke_{output_name}.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return cfg_path


@pytest.fixture(scope="module")
def experiment(tmp_path_factory):
    """Run the smoke experiment once (2 seeds) and expose its outputs."""
    tmp_path = tmp_path_factory.mktemp("smoke_exp")
    cfg_path = _write_config(tmp_path, seeds=(1, 2))
    summary = run_smoke_experiment(cfg_path)
    return {
        "summary": summary,
        "output_dir": Path(summary["output_dir"]),
        "config": _load_smoke_config(cfg_path),
        "config_path": cfg_path,
    }


# ---------------------------------------------------------------------------
# seed-level + experiment-level completion
# ---------------------------------------------------------------------------


def test_run_smoke_seed_completes(tmp_path):
    config = _load_smoke_config(_DEFAULT_CONFIG)
    res = run_smoke_seed(1, config, tmp_path)
    assert res["pair_count"] > CAPACITY  # capacity actually binds
    assert res["strategy_count"] == len(EXPECTED_STRATEGIES)
    # 11 metrics per strategy.
    assert len(res["metric_rows"]) == len(EXPECTED_STRATEGIES) * 11
    assert set(res["audit_paths"]) == set(EXPECTED_STRATEGIES)


def test_run_smoke_experiment_completes(experiment):
    s = experiment["summary"]
    assert s["seed_count"] == 2
    assert s["strategy_count"] == len(EXPECTED_STRATEGIES)
    assert s["pair_count_min"] > CAPACITY
    assert s["metric_rows"] == 2 * len(EXPECTED_STRATEGIES) * 11
    assert s["audit_logs_valid"] is True


# ---------------------------------------------------------------------------
# output artifacts
# ---------------------------------------------------------------------------


def test_output_directories_exist(experiment):
    out = experiment["output_dir"]
    assert (out / "manifest.json").exists()
    assert (out / "summary.md").exists()
    assert (out / "metrics" / "per_seed_metrics.csv").exists()
    assert (out / "metrics" / "aggregated_metrics.csv").exists()
    assert (out / "metrics" / "eehda_report.csv").exists()
    for seed in (1, 2):
        seed_dir = out / f"seed_{seed:03d}"
        assert (seed_dir / "pairs.csv").exists()
        assert (seed_dir / "features.csv").exists()
        assert (seed_dir / "labels.csv").exists()
        for strat in EXPECTED_STRATEGIES:
            sd = seed_dir / f"strategy_{strat}"
            assert (sd / "ranking.csv").exists()
            assert (sd / "schedule_history.csv").exists()
            assert (sd / "audit_log.jsonl").exists()
            assert (sd / "metrics.csv").exists()


def test_manifest_has_config_sha(experiment):
    manifest = load_manifest(experiment["output_dir"] / "manifest.json")
    assert manifest.config_sha
    assert len(manifest.config_sha) == 64  # SHA-256 hex
    assert manifest.config_name == "experiment_smoke_v1"
    assert manifest.seeds == [1, 2]
    assert "fixture_hashes" in manifest.artifact_versions


def test_per_seed_metrics_has_expected_strategies(experiment):
    df = pd.read_csv(experiment["output_dir"] / "metrics" / "per_seed_metrics.csv")
    assert {"seed", "strategy", "metric", "value"} <= set(df.columns)
    assert set(df["strategy"].unique()) == set(EXPECTED_STRATEGIES)
    assert "ehd_absolute" in set(df["metric"].unique())


# ---------------------------------------------------------------------------
# invariants
# ---------------------------------------------------------------------------


def test_every_strategy_audit_log_verifies(experiment):
    out = experiment["output_dir"]
    for seed in (1, 2):
        for strat in EXPECTED_STRATEGIES:
            log = out / f"seed_{seed:03d}" / f"strategy_{strat}" / "audit_log.jsonl"
            ok, issues = verify_chain(log)
            assert ok, f"{log} failed: {issues[:3]}"


def test_scheduled_count_within_capacity(experiment):
    df = pd.read_csv(experiment["output_dir"] / "metrics" / "per_seed_metrics.csv")
    scheduled = df[df["metric"] == "scheduled_count"]["value"]
    assert (scheduled <= CAPACITY).all()
    assert (scheduled > 0).any()


def test_rankings_have_no_duplicate_pair_id(experiment):
    out = experiment["output_dir"]
    for seed in (1, 2):
        for strat in EXPECTED_STRATEGIES:
            ranking = pd.read_csv(
                out / f"seed_{seed:03d}" / f"strategy_{strat}" / "ranking.csv"
            )
            assert not ranking["pair_id"].duplicated().any()


def test_oracle_ehd_not_worse_than_random(experiment):
    df = pd.read_csv(experiment["output_dir"] / "metrics" / "per_seed_metrics.csv")
    ehd = df[df["metric"] == "ehd_absolute"]
    mean_ehd = ehd.groupby("strategy")["value"].mean()
    # Oracle prioritizes the positives, so it should never accrue MORE
    # simulated exploited-host-days than random under capacity pressure.
    assert mean_ehd["oracle"] <= mean_ehd["random"] + 1e-9


def test_eehda_report_has_all_reporting_forms(experiment):
    eehda = pd.read_csv(experiment["output_dir"] / "metrics" / "eehda_report.csv")
    assert {
        "relative_to_random",
        "relative_to_epss",
        "fraction_of_oracle",
    } <= set(eehda.columns)
    assert set(eehda["strategy"]) == set(EXPECTED_STRATEGIES)


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


def test_repeated_run_is_deterministic(tmp_path):
    cfg_a = _write_config(tmp_path, seeds=(1, 2), output_name="a")
    cfg_b = _write_config(tmp_path, seeds=(1, 2), output_name="b")
    run_smoke_experiment(cfg_a)
    run_smoke_experiment(cfg_b)
    a = (
        pd.read_csv(tmp_path / "a" / "metrics" / "per_seed_metrics.csv")
        .sort_values(["seed", "strategy", "metric"])
        .reset_index(drop=True)
    )
    b = (
        pd.read_csv(tmp_path / "b" / "metrics" / "per_seed_metrics.csv")
        .sort_values(["seed", "strategy", "metric"])
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(a, b)


# ---------------------------------------------------------------------------
# no live feeds
# ---------------------------------------------------------------------------


def test_smoke_does_not_call_live_feeds(tmp_path, monkeypatch):
    """Patch every feed fetch entrypoint to explode; the run must still pass."""

    def _boom(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("live feed fetch attempted during smoke experiment")

    monkeypatch.setattr("paper1.feeds.kev_client.fetch_kev_catalog", _boom)
    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window", _boom)
    monkeypatch.setattr("paper1.feeds.poc_client.fetch_poc_index", _boom)
    monkeypatch.setattr("paper1.feeds.epss_client.fetch_epss_csv", _boom)
    monkeypatch.setattr("paper1.feeds.base.BaseFeedClient.fetch", _boom)

    cfg_path = _write_config(tmp_path, seeds=(1,), output_name="nolive")
    summary = run_smoke_experiment(cfg_path)
    assert summary["audit_logs_valid"] is True
    assert summary["pair_count_min"] > 0
