"""Controlled primary execution tests (Phase 13).

These prove that controlled (non-dry-run) execution is locked behind an
explicit confirm + explicit max_seeds, that >3 seeds need allow_large_run,
that checkpoints resume, and that no live feeds are touched. Tiny temporary
configs (small fleet, few strategies/seeds) keep runtime low. The full
30-seed workload is NEVER run here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml
from pydantic import ValidationError

from paper1.audit.hash_chain import verify_chain
from paper1.experiments.primary import (
    PrimaryRunConfig,
    checkpoint_path,
    load_primary_config,
    plan_primary_run,
    run_primary_confirmed,
    run_primary_experiment,
)

_TEMPLATE = Path("configs/primary_full_template.yaml")
_DRYRUN = Path("configs/primary_dryrun.yaml")
_FAST_STRATEGIES = ["random", "epss_only", "proposed_full", "oracle"]
_METRICS_PER_STRATEGY = 11


def _template_raw() -> dict:
    return yaml.safe_load(_TEMPLATE.read_text(encoding="utf-8"))


def _tiny_config(tmp_path: Path, *, seeds, output_name="out", **overrides) -> PrimaryRunConfig:
    """Build a tiny non-dry controlled config (small fleet, few strategies)."""
    raw = _template_raw()
    raw.update(
        {
            "fleet_size": 60,
            "seeds": list(seeds),
            "strategies": list(_FAST_STRATEGIES),
            "excluded_strategies": [],
            "output_dir": str(tmp_path / output_name),
        }
    )
    raw.update(overrides)
    return PrimaryRunConfig(**raw)


# ---------------------------------------------------------------------------
# template config + plan
# ---------------------------------------------------------------------------


def test_full_template_loads_because_confirm_true():
    config = load_primary_config(_TEMPLATE)
    assert config.config_name == "primary_full_template_v1"
    assert config.dry_run is False
    assert config.confirm_full_run is True
    assert len(config.seeds) == 30
    assert config.capacity == 100  # max(1, int(10000 * 0.01))


def test_full_template_without_confirm_would_not_load(tmp_path):
    raw = _template_raw()
    raw["confirm_full_run"] = False
    raw["output_dir"] = str(tmp_path / "x")
    with pytest.raises(ValidationError):
        PrimaryRunConfig(**raw)


def test_plan_primary_run_creates_no_dirs(tmp_path):
    raw = _template_raw()
    out = tmp_path / "would_not_exist"
    raw["output_dir"] = str(out)
    cfg_path = tmp_path / "plan.yaml"
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    plan = plan_primary_run(cfg_path, max_seeds=2)
    assert plan["executed"] is False
    assert plan["seeds_would_run"] == [1, 2]
    assert not out.exists()  # plan must not create result dirs


# ---------------------------------------------------------------------------
# confirm + max-seeds locks
# ---------------------------------------------------------------------------


def test_non_dry_without_confirm_raises_runtimeerror(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1])
    cfg_path = tmp_path / "c.yaml"
    cfg_path.write_text(cfg.model_dump_json(), encoding="utf-8")
    with pytest.raises(RuntimeError):
        run_primary_experiment(cfg_path, confirm=False)


def test_confirmed_without_max_seeds_raises(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1, 2])
    with pytest.raises(RuntimeError):
        run_primary_confirmed(cfg, max_seeds=None)


def test_confirmed_max_seeds_must_be_positive(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1, 2])
    with pytest.raises(ValueError):
        run_primary_confirmed(cfg, max_seeds=0)


def test_confirmed_one_seed_runs(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1, 2, 3], output_name="one")
    s = run_primary_confirmed(cfg, max_seeds=1)
    assert s["dry_run"] is False
    assert s["seeds_run"] == [1]
    assert s["seeds_requested"] == [1, 2, 3]
    assert s["audit_logs_valid"] is True
    df = pd.read_csv(Path(s["output_dir"]) / "metrics" / "per_seed_metrics.csv")
    assert df["seed"].nunique() == 1


def test_confirmed_two_seeds_runs(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1, 2, 3], output_name="two")
    s = run_primary_confirmed(cfg, max_seeds=2)
    assert s["seeds_run"] == [1, 2]
    df = pd.read_csv(Path(s["output_dir"]) / "metrics" / "per_seed_metrics.csv")
    assert df["seed"].nunique() == 2
    # per-seed rows == seeds_run * strategies * metrics_per_strategy
    assert len(df) == 2 * len(_FAST_STRATEGIES) * _METRICS_PER_STRATEGY


def test_max_seeds_over_three_without_allow_large_raises(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1, 2, 3, 4])
    with pytest.raises(RuntimeError):
        run_primary_confirmed(cfg, max_seeds=4, allow_large_run=False)


def test_max_seeds_over_three_with_allow_large_runs(tmp_path):
    # Tiny fleet keeps this fast; this exercises the allow_large_run path
    # WITHOUT running the real large workload.
    cfg = _tiny_config(tmp_path, seeds=[1, 2, 3, 4], output_name="four")
    s = run_primary_confirmed(cfg, max_seeds=4, allow_large_run=True)
    assert s["seeds_run"] == [1, 2, 3, 4]
    assert s["audit_logs_valid"] is True


def test_extra_confirm_large_run_config_flag_allows_large(tmp_path):
    cfg = _tiny_config(
        tmp_path, seeds=[1, 2, 3, 4], output_name="cfgflag", extra_confirm_large_run=True
    )
    s = run_primary_confirmed(cfg, max_seeds=4, allow_large_run=False)
    assert s["seeds_run"] == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# checkpoint / resume
# ---------------------------------------------------------------------------


def test_checkpoint_resume_skips_completed_seed(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1, 2], output_name="resume")
    first = run_primary_confirmed(cfg, max_seeds=2)
    assert first["seeds_skipped_from_checkpoint"] == 0
    # Second run with the same output dir resumes both seeds from checkpoint.
    second = run_primary_confirmed(cfg, max_seeds=2)
    assert second["seeds_skipped_from_checkpoint"] == 2
    assert second["seeds_run"] == [1, 2]


def test_checkpoint_without_outputs_triggers_rerun(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1], output_name="missing")
    s = run_primary_confirmed(cfg, max_seeds=1)
    out = Path(s["output_dir"])
    # Delete the seed's audit logs but keep the checkpoint -> must re-run.
    for log in (out / "seed_001").glob("strategy_*/audit_log.jsonl"):
        log.unlink()
    assert checkpoint_path(out, 1, "seed_complete").exists()
    with pytest.warns(UserWarning):
        s2 = run_primary_confirmed(cfg, max_seeds=1)
    assert s2["seeds_skipped_from_checkpoint"] == 0  # was re-run, not skipped
    assert s2["audit_logs_valid"] is True


# ---------------------------------------------------------------------------
# guardrails that must still hold
# ---------------------------------------------------------------------------


def test_allow_live_fetch_true_still_fails(tmp_path):
    raw = _template_raw()
    raw["allow_live_fetch"] = True
    raw["output_dir"] = str(tmp_path / "x")
    with pytest.raises(ValidationError):
        PrimaryRunConfig(**raw)


def test_gbt_comparator_without_artifact_still_fails(tmp_path):
    raw = _template_raw()
    raw["strategies"] = [*raw["strategies"], "gbt_comparator"]
    raw["excluded_strategies"] = []
    raw["output_dir"] = str(tmp_path / "x")
    with pytest.raises(ValidationError):
        PrimaryRunConfig(**raw)


def test_capacity_respected_in_controlled_run(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1], output_name="cap")
    s = run_primary_confirmed(cfg, max_seeds=1)
    df = pd.read_csv(Path(s["output_dir"]) / "metrics" / "per_seed_metrics.csv")
    scheduled = df[df["metric"] == "scheduled_count"]["value"]
    assert (scheduled <= cfg.capacity).all()


def test_controlled_audit_logs_verify(tmp_path):
    cfg = _tiny_config(tmp_path, seeds=[1], output_name="audit")
    s = run_primary_confirmed(cfg, max_seeds=1)
    logs = list((Path(s["output_dir"]) / "seed_001").glob("strategy_*/audit_log.jsonl"))
    assert logs
    for log in logs:
        ok, issues = verify_chain(log)
        assert ok, f"{log} failed: {issues[:3]}"


# ---------------------------------------------------------------------------
# no live feeds
# ---------------------------------------------------------------------------


def test_controlled_run_does_not_call_live_feeds(tmp_path, monkeypatch):
    def _boom(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("live feed fetch attempted during controlled run")

    monkeypatch.setattr("paper1.feeds.kev_client.fetch_kev_catalog", _boom)
    monkeypatch.setattr("paper1.feeds.nvd_client.fetch_nvd_window", _boom)
    monkeypatch.setattr("paper1.feeds.poc_client.fetch_poc_index", _boom)
    monkeypatch.setattr("paper1.feeds.epss_client.fetch_epss_csv", _boom)
    monkeypatch.setattr("paper1.feeds.base.BaseFeedClient.fetch", _boom)

    cfg = _tiny_config(tmp_path, seeds=[1], output_name="nolive")
    s = run_primary_confirmed(cfg, max_seeds=1)
    assert s["audit_logs_valid"] is True
    assert s["pair_count_min"] > 0
