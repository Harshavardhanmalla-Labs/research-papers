"""Primary experiment runner skeleton tests (Phase 12).

These prove the guardrails hold and that the full primary workload is NOT
run. Only a tiny, guardrailed dry-run executes (reusing the smoke pipeline).
Nothing here asserts a research finding.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml
from pydantic import ValidationError

from paper1.audit.hash_chain import verify_chain
from paper1.experiments.common import load_manifest
from paper1.experiments.primary import (
    _DEFAULT_CONFIG,
    PrimaryRunConfig,
    checkpoint_exists,
    checkpoint_path,
    clear_checkpoint,
    estimate_primary_runtime,
    load_primary_config,
    make_primary_output_layout,
    read_checkpoint,
    run_primary_dryrun,
    run_primary_experiment,
    write_checkpoint,
)

CAPACITY = 2  # max(capacity_min=1, int(250 * 0.01))


def _raw() -> dict:
    return yaml.safe_load(Path(_DEFAULT_CONFIG).read_text(encoding="utf-8"))


def _write_config(tmp_path: Path, *, output_name="out", **overrides) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cfg = _raw()
    cfg.update(overrides)
    cfg["output_dir"] = str(tmp_path / output_name)
    cfg_path = tmp_path / f"primary_{output_name}.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return cfg_path


# ---------------------------------------------------------------------------
# config validation + guardrails
# ---------------------------------------------------------------------------


def test_load_primary_config_validates_dryrun_yaml():
    config = load_primary_config(_DEFAULT_CONFIG)
    assert config.config_name == "primary_dryrun_v1"
    assert config.dry_run is True
    assert config.capacity == CAPACITY
    assert "gbt_comparator" not in config.strategies
    assert "gbt_comparator" in config.excluded_strategies


def test_dry_run_false_without_confirm_raises():
    with pytest.raises(ValidationError):
        PrimaryRunConfig(**{**_raw(), "dry_run": False, "confirm_full_run": False})


def test_too_many_seeds_without_confirm_raises():
    with pytest.raises(ValidationError):
        PrimaryRunConfig(**{**_raw(), "seeds": [1, 2, 3], "confirm_full_run": False})


def test_fleet_at_primary_target_without_confirm_raises():
    with pytest.raises(ValidationError):
        PrimaryRunConfig(**{**_raw(), "fleet_size": 10000, "confirm_full_run": False})


def test_gbt_comparator_without_artifact_raises():
    with pytest.raises(ValidationError):
        PrimaryRunConfig(
            **{
                **_raw(),
                "strategies": [*_raw()["strategies"], "gbt_comparator"],
                "excluded_strategies": [],
            }
        )


def test_allow_live_fetch_true_raises():
    with pytest.raises(ValidationError):
        PrimaryRunConfig(**{**_raw(), "allow_live_fetch": True})


def test_gbt_comparator_with_artifact_is_allowed():
    config = PrimaryRunConfig(
        **{
            **_raw(),
            "strategies": [*_raw()["strategies"], "gbt_comparator"],
            "excluded_strategies": [],
            "gbt_model_artifact": "models/gbt_toy.txt",
        }
    )
    assert "gbt_comparator" in config.strategies


# ---------------------------------------------------------------------------
# estimate + layout + checkpoints
# ---------------------------------------------------------------------------


def test_estimate_primary_runtime_keys():
    est = estimate_primary_runtime(load_primary_config(_DEFAULT_CONFIG))
    expected = {
        "seed_count",
        "fleet_size",
        "strategy_count",
        "capacity_per_window",
        "estimated_pair_count_range",
        "estimated_windows",
        "estimated_scheduler_invocations",
        "estimated_output_files",
        "dry_run",
        "warnings",
    }
    assert expected <= set(est)
    assert est["estimated_windows"] == 3  # Jun/Jul/Aug month-starts
    assert len(est["estimated_pair_count_range"]) == 2


def test_make_primary_output_layout_creates_dirs(tmp_path):
    cfg = _write_config(tmp_path)
    config = load_primary_config(cfg)
    layout = make_primary_output_layout(config)
    assert Path(layout["root"]).is_dir()
    assert Path(layout["checkpoints"]).is_dir()
    assert Path(layout["metrics"]).is_dir()


def test_checkpoint_roundtrip(tmp_path):
    make_primary_output_layout(load_primary_config(_write_config(tmp_path)))
    out = tmp_path / "out"
    path = checkpoint_path(out, seed=1, stage="seed_complete")
    assert not checkpoint_exists(path)
    write_checkpoint(path, {"seed": 1, "done": True})
    assert checkpoint_exists(path)
    assert read_checkpoint(path)["seed"] == 1
    clear_checkpoint(path)
    assert not checkpoint_exists(path)


# ---------------------------------------------------------------------------
# dry-run execution
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def dryrun(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("primary_dryrun")
    cfg_path = tmp_path / "primary.yaml"
    raw = yaml.safe_load(Path(_DEFAULT_CONFIG).read_text(encoding="utf-8"))
    raw["output_dir"] = str(tmp_path / "out")
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    summary = run_primary_dryrun(cfg_path, max_seeds=1)
    return {"summary": summary, "output_dir": Path(summary["output_dir"])}


def test_run_primary_dryrun_completes(dryrun):
    s = dryrun["summary"]
    assert s["dry_run"] is True
    assert s["fleet_size"] == 250
    assert s["seeds"] == [1]
    assert s["strategy_count"] == 13
    assert s["capacity"] == CAPACITY
    assert s["pair_count_min"] > CAPACITY
    assert s["audit_logs_valid"] is True
    assert "runtime_estimate" in s


def test_dryrun_manifest_exists(dryrun):
    manifest = load_manifest(dryrun["output_dir"] / "manifest.json")
    assert manifest.config_name == "primary_dryrun_v1"
    assert len(manifest.config_sha) == 64
    assert manifest.seeds == [1]


def test_dryrun_per_seed_metrics_exists(dryrun):
    df = pd.read_csv(dryrun["output_dir"] / "metrics" / "per_seed_metrics.csv")
    assert {"seed", "strategy", "metric", "value"} <= set(df.columns)
    assert df["seed"].nunique() == 1


def test_dryrun_audit_logs_verify(dryrun):
    out = dryrun["output_dir"]
    seed_dir = out / "seed_001"
    audit_logs = list(seed_dir.glob("strategy_*/audit_log.jsonl"))
    assert audit_logs  # at least one strategy ran
    for log in audit_logs:
        ok, issues = verify_chain(log)
        assert ok, f"{log} failed: {issues[:3]}"


def test_dryrun_scheduled_within_capacity(dryrun):
    df = pd.read_csv(dryrun["output_dir"] / "metrics" / "per_seed_metrics.csv")
    scheduled = df[df["metric"] == "scheduled_count"]["value"]
    assert (scheduled <= CAPACITY).all()


def test_dryrun_writes_checkpoint(dryrun):
    ckpt = dryrun["output_dir"] / "checkpoints" / "seed_001.seed_complete.json"
    assert ckpt.exists()


# ---------------------------------------------------------------------------
# full-run is intentionally disabled
# ---------------------------------------------------------------------------


def test_run_primary_experiment_dryrun_routes_to_dryrun(tmp_path):
    cfg = _write_config(tmp_path)  # dry_run=True
    summary = run_primary_experiment(cfg)
    assert summary["dry_run"] is True


def test_non_dry_without_confirm_raises_runtimeerror(tmp_path):
    # confirm_full_run=True makes the config constructable; the function-level
    # confirm=False then refuses to run.
    cfg = _write_config(tmp_path, dry_run=False, confirm_full_run=True)
    with pytest.raises(RuntimeError):
        run_primary_experiment(cfg, confirm=False)


def test_non_dry_with_confirm_requires_explicit_max_seeds(tmp_path):
    # Phase 13: a confirmed non-dry run executes a *controlled* cell, but it
    # still refuses to default to all seeds -- an explicit max_seeds is
    # required, so confirm=True without max_seeds raises RuntimeError.
    cfg = _write_config(tmp_path, dry_run=False, confirm_full_run=True)
    with pytest.raises(RuntimeError):
        run_primary_experiment(cfg, confirm=True)


# ---------------------------------------------------------------------------
# no live feeds
# ---------------------------------------------------------------------------


def test_dryrun_does_not_call_live_feeds(tmp_path, monkeypatch):
    def _boom(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("live feed fetch attempted during primary dry-run")

    monkeypatch.setattr("paper1.feeds.kev_client.fetch_kev_catalog", _boom)
    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window", _boom)
    monkeypatch.setattr("paper1.feeds.poc_client.fetch_poc_index", _boom)
    monkeypatch.setattr("paper1.feeds.epss_client.fetch_epss_csv", _boom)
    monkeypatch.setattr("paper1.feeds.base.BaseFeedClient.fetch", _boom)

    cfg = _write_config(tmp_path, output_name="nolive")
    summary = run_primary_dryrun(cfg, max_seeds=1)
    assert summary["audit_logs_valid"] is True
    assert summary["pair_count_min"] > 0


# ---------------------------------------------------------------------------
# smoke runner still importable / usable alongside primary
# ---------------------------------------------------------------------------


def test_smoke_runner_still_available():
    from paper1.experiments.smoke import run_smoke_experiment, run_smoke_seed

    assert callable(run_smoke_experiment)
    assert callable(run_smoke_seed)
