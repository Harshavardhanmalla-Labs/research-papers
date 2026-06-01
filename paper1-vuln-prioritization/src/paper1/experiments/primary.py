"""Primary experiment runner skeleton with guardrails (Phase 12).

This module provides the *infrastructure* for the primary experiment cell
(10,000-host fleet, capacity ratio 0.01, 30 seeds) but deliberately does
NOT run that workload. Phase 12 ships only:

  - a validated :class:`PrimaryRunConfig` with hard guardrails,
  - a runtime / compute estimate,
  - input validation (no live fetch, local snapshots, supported strategies),
  - the primary output layout + checkpoint/resume helpers, and
  - a tiny, guardrailed *dry-run* that reuses the Phase 11 smoke per-seed
    pipeline (:func:`paper1.experiments.smoke.run_smoke_seed`).

Phase 13 enables *controlled* non-dry-run execution behind two locks: the
config must set ``confirm_full_run=true`` AND the caller must pass an
explicit ``confirm`` plus an explicit ``max_seeds`` (it never defaults to
all seeds). Runs larger than three seeds require ``allow_large_run``.
Nothing here calls a live feed or fabricates results, and there is no
default full 30-seed entry point.
"""

from __future__ import annotations

import hashlib
import time
import warnings as _warnings
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, model_validator

from paper1 import __framework_version__
from paper1.evaluation.eehda import eehda_report
from paper1.evaluation.metrics import aggregate_metrics
from paper1.evaluation.statistical_tests import validate_per_seed_metric_frame
from paper1.experiments.common import (
    ExperimentManifest,
    collect_artifact_versions,
    dataframe_to_parquet_or_csv,
    ensure_result_dirs,
    stable_config_sha,
    validate_audit_logs,
    write_manifest,
)
from paper1.experiments.smoke import run_smoke_seed
from paper1.model.strategies import STRATEGY_NAMES
from paper1.utils.config import load_yaml
from paper1.utils.io import atomic_write_json, read_json
from paper1.utils.time import utc_now

__all__ = [
    "PrimaryRunConfig",
    "checkpoint_exists",
    "checkpoint_path",
    "clear_checkpoint",
    "estimate_primary_runtime",
    "load_primary_config",
    "make_primary_output_layout",
    "plan_primary_run",
    "read_checkpoint",
    "run_primary_confirmed",
    "run_primary_dryrun",
    "run_primary_experiment",
    "validate_primary_inputs",
    "write_checkpoint",
]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURES = _REPO_ROOT / "data" / "fixtures"
_SNAPSHOTS = _REPO_ROOT / "data" / "snapshots"
_REQUIRED_FIXTURES = ("vulnerabilities_toy.json", "kev_toy.json", "poc_toy.csv")

# Heuristic pairs-per-host band observed on the toy fixtures (~2.1/host); used
# only for the compute *estimate*, not for any result.
_PAIRS_PER_HOST_LOW = 1.5
_PAIRS_PER_HOST_HIGH = 2.7

_DEFAULT_CONFIG = _REPO_ROOT / "configs" / "primary_dryrun.yaml"


class PrimaryRunConfig(BaseModel):
    """Validated primary-runner configuration with hard guardrails."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_name: str
    seed_master: int
    seeds: list[int]
    max_seeds_allowed_without_confirm: int
    fleet_size: int
    primary_target_fleet_size: int
    capacity_ratio: float
    capacity_min: int
    label: str
    approver_policy: str
    identity_config: str
    blackout_config: str
    t0_start: str
    t0_end: str
    H_days: int
    evaluation_end_days: int
    data_window_start: str
    data_window_end: str
    strategies: list[str]
    excluded_strategies: list[str] = []
    output_dir: str
    dry_run: bool
    require_local_snapshots: bool
    allow_live_fetch: bool
    confirm_full_run: bool
    checkpointing: bool
    # Optional extras (not in the dry-run yaml; defaulted).
    gbt_model_artifact: str | None = None
    schedule_now: str = "2025-06-03T20:00:00Z"
    train_split_months: int = 4
    # Extra opt-in for >3-seed controlled runs (function arg can also enable it).
    extra_confirm_large_run: bool = False

    @property
    def capacity(self) -> int:
        """Per-window capacity = max(capacity_min, floor(fleet_size * ratio))."""
        return max(self.capacity_min, int(self.fleet_size * self.capacity_ratio))

    @model_validator(mode="after")
    def _check_guardrails(self) -> PrimaryRunConfig:
        if self.allow_live_fetch:
            raise ValueError("allow_live_fetch must be false in Phase 12 (no live feeds)")
        if not self.dry_run and not self.confirm_full_run:
            raise ValueError(
                "non-dry-run primary requires confirm_full_run=true (refusing to run)"
            )
        if (
            len(self.seeds) > self.max_seeds_allowed_without_confirm
            and not self.confirm_full_run
        ):
            raise ValueError(
                f"{len(self.seeds)} seeds exceeds "
                f"max_seeds_allowed_without_confirm="
                f"{self.max_seeds_allowed_without_confirm}; set confirm_full_run=true"
            )
        if self.fleet_size >= self.primary_target_fleet_size and not self.confirm_full_run:
            raise ValueError(
                f"fleet_size {self.fleet_size} reaches primary_target_fleet_size "
                f"{self.primary_target_fleet_size}; set confirm_full_run=true"
            )
        if "gbt_comparator" in self.strategies and not self.gbt_model_artifact:
            raise ValueError(
                "gbt_comparator cannot be included without a fitted gbt_model_artifact"
            )
        overlap = set(self.strategies) & set(self.excluded_strategies)
        if overlap:
            raise ValueError(f"excluded strategies present in strategies: {sorted(overlap)}")
        unknown = [s for s in self.strategies if s not in STRATEGY_NAMES]
        if unknown:
            raise ValueError(f"unknown strategies: {unknown}")
        if self.label not in ("A", "B"):
            raise ValueError(f"label must be 'A' or 'B'; got {self.label!r}")
        return self


def load_primary_config(path: str | Path) -> PrimaryRunConfig:
    """Load and validate a primary-runner config from YAML."""
    payload = load_yaml(path)
    if not isinstance(payload, dict):
        raise ValueError("primary config must be a top-level mapping")
    return PrimaryRunConfig(**payload)


def estimate_primary_runtime(config: PrimaryRunConfig) -> dict[str, Any]:
    """Estimate compute footprint (heuristic; no workload is executed)."""
    seed_count = len(config.seeds)
    strategy_count = len([s for s in config.strategies if s != "gbt_comparator"])
    windows = pd.date_range(config.t0_start, config.t0_end, freq="MS")
    n_windows = max(1, len(windows))
    pair_low = int(config.fleet_size * _PAIRS_PER_HOST_LOW)
    pair_high = int(config.fleet_size * _PAIRS_PER_HOST_HIGH)
    scheduler_invocations = seed_count * strategy_count * n_windows
    # Per seed: 3 shared frames + 4 files per strategy; plus 5 top-level files.
    output_files = seed_count * (3 + 4 * strategy_count) + 5

    warnings: list[str] = []
    if config.dry_run:
        warnings.append(
            "dry-run executes a single t0 window and is seed-capped; this estimate "
            "reflects the *configured* scope, not what the dry-run actually runs."
        )
    if config.fleet_size < config.primary_target_fleet_size:
        warnings.append(
            f"dry-run fleet_size {config.fleet_size} is far below the primary target "
            f"{config.primary_target_fleet_size}; runtime will scale roughly linearly."
        )
    if config.capacity <= 5:
        warnings.append(
            f"capacity={config.capacity} is small; most pairs will be deferred "
            "(expected for a small dry-run fleet)."
        )

    return {
        "seed_count": seed_count,
        "fleet_size": config.fleet_size,
        "strategy_count": strategy_count,
        "capacity_per_window": config.capacity,
        "estimated_pair_count_range": [pair_low, pair_high],
        "estimated_windows": n_windows,
        "estimated_scheduler_invocations": scheduler_invocations,
        "estimated_output_files": output_files,
        "dry_run": config.dry_run,
        "warnings": warnings,
    }


def _is_safe_output_dir(output_dir: str | Path) -> bool:
    p = Path(output_dir)
    if str(output_dir).strip() in ("", "/", "~"):
        return False
    resolved = p.expanduser().resolve()
    # Refuse the filesystem root and the user's home root directly.
    if resolved == resolved.anchor and resolved.parent == resolved:
        return False
    if resolved == Path.home().resolve():
        return False
    return True


def validate_primary_inputs(config: PrimaryRunConfig) -> None:
    """Validate runtime preconditions; raise loudly on any problem."""
    if config.allow_live_fetch:
        raise ValueError("allow_live_fetch must be false in Phase 12 (no live feeds)")
    if config.require_local_snapshots and not _SNAPSHOTS.exists():
        raise ValueError(
            f"require_local_snapshots=true but no local snapshots at {_SNAPSHOTS}"
        )
    if config.dry_run:
        missing = [f for f in _REQUIRED_FIXTURES if not (_FIXTURES / f).exists()]
        if missing:
            raise ValueError(f"dry-run requires toy fixtures; missing: {missing}")
    if not _is_safe_output_dir(config.output_dir):
        raise ValueError(f"unsafe output_dir: {config.output_dir!r}")
    unknown = [s for s in config.strategies if s not in STRATEGY_NAMES]
    if unknown:
        raise ValueError(f"unknown strategies: {unknown}")
    overlap = set(config.strategies) & set(config.excluded_strategies)
    if overlap:
        raise ValueError(f"excluded strategies present in strategies: {sorted(overlap)}")
    if "gbt_comparator" in config.strategies and not config.gbt_model_artifact:
        raise ValueError("gbt_comparator requires a fitted gbt_model_artifact")


def make_primary_output_layout(config: PrimaryRunConfig) -> dict[str, str]:
    """Create the primary output directory tree; return key paths."""
    root = ensure_result_dirs(config.output_dir)
    checkpoints = root / "checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    metrics = root / "metrics"
    metrics.mkdir(parents=True, exist_ok=True)
    return {
        "root": str(root),
        "checkpoints": str(checkpoints),
        "metrics": str(metrics),
    }


# ---------------------------------------------------------------------------
# checkpoint / resume helpers
# ---------------------------------------------------------------------------


def checkpoint_path(output_dir: str | Path, seed: int, stage: str) -> Path:
    """Deterministic checkpoint path for a (seed, stage)."""
    return Path(output_dir) / "checkpoints" / f"seed_{seed:03d}.{stage}.json"


def write_checkpoint(path: str | Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


def read_checkpoint(path: str | Path) -> dict[str, Any]:
    return read_json(path)


def checkpoint_exists(path: str | Path) -> bool:
    return Path(path).exists()


def clear_checkpoint(path: str | Path) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()


# ---------------------------------------------------------------------------
# dry-run
# ---------------------------------------------------------------------------


def _smoke_compatible_config(
    config: PrimaryRunConfig,
    seeds: list[int],
    output_dir: str | Path,
) -> dict[str, Any]:
    """Adapt a PrimaryRunConfig to the smoke runner's config dict shape.

    gbt_comparator is dropped (it needs a fitted model that the dry-run does
    not supply); all other configured strategies pass through.
    """
    strategies = [s for s in config.strategies if s != "gbt_comparator"]
    return {
        "config_name": config.config_name,
        "seed_master": config.seed_master,
        "seeds": list(seeds),
        "fleet_size": config.fleet_size,
        "t0": config.t0_start,
        "H_days": config.H_days,
        "data_window_start": config.data_window_start,
        "data_window_end": config.data_window_end,
        "evaluation_end_days": config.evaluation_end_days,
        "schedule_now": config.schedule_now,
        "capacity": config.capacity,
        "label": config.label,
        "strategies": strategies,
        "approver_policy": config.approver_policy,
        "blackout_config": config.blackout_config,
        "identity_config": config.identity_config,
        "output_dir": str(output_dir),
        "train_split_months": config.train_split_months,
    }


def _write_primary_summary(
    path: Path,
    config: PrimaryRunConfig,
    seeds_run: list[int],
    per_seed: pd.DataFrame,
    pair_counts: list[int],
    estimate: dict[str, Any],
    *,
    dry_run: bool,
    seeds_skipped: int = 0,
) -> None:
    lines: list[str] = []
    kind = "DRY-RUN" if dry_run else "CONTROLLED-RUN"
    lines.append(f"# Primary {kind} summary: {config.config_name}")
    lines.append("")
    if dry_run:
        lines.append(
            "**Dry-run infrastructure only — NOT a paper result.** Toy fixtures, "
            "deterministic seeds, no live feeds."
        )
    else:
        lines.append(
            "**Controlled primary execution — NOT a final paper result** unless "
            "ALL pre-registered seeds complete and the outputs are frozen. "
            "Deterministic seeds, no live feeds."
        )
    lines.append("")
    lines.append(f"- seeds run: {seeds_run}")
    if not dry_run:
        lines.append(f"- seeds requested: {config.seeds}")
        lines.append(f"- seeds skipped (resumed from checkpoint): {seeds_skipped}")
    lines.append(f"- fleet_size: {config.fleet_size} (primary target: {config.primary_target_fleet_size})")
    lines.append(f"- capacity/window: {config.capacity} (ratio {config.capacity_ratio})")
    lines.append(f"- strategies: {estimate['strategy_count']}")
    lines.append(f"- pairs per seed: min={min(pair_counts)} max={max(pair_counts)}")
    lines.append("")
    lines.append("## Configured-scope compute estimate (not executed)")
    lines.append("")
    for key in (
        "seed_count",
        "strategy_count",
        "estimated_windows",
        "estimated_scheduler_invocations",
        "estimated_output_files",
        "estimated_pair_count_range",
    ):
        lines.append(f"- {key}: {estimate[key]}")
    lines.append("")
    lines.append("## Mean EHD by strategy (dry-run; simulated)")
    lines.append("")
    ehd = (
        per_seed[per_seed["metric"] == "ehd_absolute"]
        .groupby("strategy")["value"]
        .mean()
        .sort_values()
    )
    lines.append("| strategy | mean EHD |")
    lines.append("| --- | --- |")
    for strat, val in ehd.items():
        lines.append(f"| {strat} | {val:.2f} |")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _checkpoint_outputs_present(payload: dict[str, Any]) -> bool:
    """True if every audit-log file referenced by a checkpoint still exists."""
    paths = payload.get("audit_paths") or {}
    if not paths:
        return False
    return all(Path(p).exists() for p in paths.values())


def _execute_primary_seeds(
    config: PrimaryRunConfig,
    config_sha: str,
    seeds_run: list[int],
    output_dir: Path,
    *,
    dry_run: bool,
    manifest_notes: str,
) -> dict[str, Any]:
    """Shared per-seed execution + aggregation for dry-run and confirmed runs.

    Reuses the Phase 11 smoke per-seed pipeline. Completed seeds are resumed
    from their checkpoint; a checkpoint whose output files are missing is
    re-run (with a warning) rather than trusted.
    """
    start = time.monotonic()
    estimate = estimate_primary_runtime(config)
    strategies_run = [s for s in config.strategies if s != "gbt_comparator"]

    manifest = ExperimentManifest(
        config_name=config.config_name,
        config_sha=config_sha,
        code_version=__framework_version__,
        created_at=utc_now(),
        seeds=seeds_run,
        strategies=strategies_run,
        output_dir=str(output_dir),
        artifact_versions=collect_artifact_versions(),
        notes=manifest_notes,
    )
    write_manifest(output_dir / "manifest.json", manifest)

    smoke_cfg = _smoke_compatible_config(config, seeds_run, output_dir)

    all_rows: list[dict[str, Any]] = []
    pair_counts: list[int] = []
    audit_all: dict[str, str] = {}
    seeds_skipped = 0
    for seed in seeds_run:
        ckpt = checkpoint_path(output_dir, seed, "seed_complete")
        payload: dict[str, Any] | None = None
        if config.checkpointing and checkpoint_exists(ckpt):
            candidate = read_checkpoint(ckpt)
            if _checkpoint_outputs_present(candidate):
                payload = candidate
                seeds_skipped += 1
            else:
                _warnings.warn(
                    f"checkpoint for seed {seed} exists but its output files are "
                    "missing; re-running this seed",
                    stacklevel=2,
                )
        if payload is None:
            res = run_smoke_seed(int(seed), smoke_cfg, output_dir)
            payload = {
                "seed": res["seed"],
                "pair_count": res["pair_count"],
                "metric_rows": res["metric_rows"],
                "audit_paths": res["audit_paths"],
                "completed_at": utc_now().isoformat(),
            }
            if config.checkpointing:
                write_checkpoint(ckpt, payload)
        all_rows.extend(payload["metric_rows"])
        pair_counts.append(int(payload["pair_count"]))
        for strat, p in payload["audit_paths"].items():
            audit_all[f"seed{int(payload['seed']):03d}:{strat}"] = p

    per_seed = pd.DataFrame(all_rows, columns=["seed", "strategy", "metric", "value"])
    validate_per_seed_metric_frame(per_seed)
    aggregated = aggregate_metrics(per_seed)
    ehd_mean = (
        per_seed[per_seed["metric"] == "ehd_absolute"]
        .groupby("strategy")["value"]
        .mean()
        .to_dict()
    )
    eehda = eehda_report(ehd_mean)

    metrics_dir = output_dir / "metrics"
    dataframe_to_parquet_or_csv(per_seed, metrics_dir / "per_seed_metrics.csv")
    dataframe_to_parquet_or_csv(aggregated, metrics_dir / "aggregated_metrics.csv")
    dataframe_to_parquet_or_csv(eehda, metrics_dir / "eehda_report.csv")
    _write_primary_summary(
        output_dir / "summary.md",
        config,
        seeds_run,
        per_seed,
        pair_counts,
        estimate,
        dry_run=dry_run,
        seeds_skipped=seeds_skipped,
    )

    audit_logs_valid = validate_audit_logs(audit_all)
    runtime_seconds = time.monotonic() - start

    return {
        "output_dir": str(output_dir),
        "fleet_size": config.fleet_size,
        "seeds_run": seeds_run,
        "seed_count": len(seeds_run),
        "strategy_count": len(strategies_run),
        "strategies": strategies_run,
        "capacity": config.capacity,
        "pair_count_min": int(min(pair_counts)),
        "pair_count_max": int(max(pair_counts)),
        "metric_rows": len(per_seed),
        "audit_logs_valid": bool(audit_logs_valid),
        "seeds_skipped_from_checkpoint": seeds_skipped,
        "runtime_seconds": runtime_seconds,
        "estimate": estimate,
    }


def run_primary_dryrun(
    config_path: str | Path = _DEFAULT_CONFIG,
    max_seeds: int = 1,
    out_override: str | None = None,
) -> dict[str, Any]:
    """Run the guardrailed primary *dry-run* (reuses the smoke pipeline).

    Forces ``dry_run=True``, caps seeds at ``max_seeds``, writes outputs in
    the primary layout, and returns a compact summary. No live feeds.
    """
    config = load_primary_config(config_path)
    # Force dry-run and apply an output override (model_copy does not re-run
    # validators in pydantic v2, matching the audit-logger pattern).
    updates: dict[str, Any] = {"dry_run": True}
    if out_override is not None:
        updates["output_dir"] = out_override
    config = config.model_copy(update=updates)

    validate_primary_inputs(config)
    make_primary_output_layout(config)
    output_dir = Path(config.output_dir)
    seeds_run = list(config.seeds)[: max(1, int(max_seeds))]

    core = _execute_primary_seeds(
        config,
        stable_config_sha(config_path),
        seeds_run,
        output_dir,
        dry_run=True,
        manifest_notes=(
            "Primary DRY-RUN on toy fixtures; guardrailed skeleton, NOT a paper "
            "result."
        ),
    )
    return {
        "config_name": config.config_name,
        "output_dir": core["output_dir"],
        "dry_run": True,
        "fleet_size": core["fleet_size"],
        "seeds": core["seeds_run"],
        "seed_count": core["seed_count"],
        "strategy_count": core["strategy_count"],
        "strategies": core["strategies"],
        "capacity": core["capacity"],
        "pair_count_min": core["pair_count_min"],
        "pair_count_max": core["pair_count_max"],
        "metric_rows": core["metric_rows"],
        "audit_logs_valid": core["audit_logs_valid"],
        "runtime_estimate": core["estimate"],
    }


def run_primary_confirmed(
    config: PrimaryRunConfig,
    max_seeds: int | None = None,
    out_override: str | None = None,
    allow_large_run: bool = False,
) -> dict[str, Any]:
    """Execute a *controlled* (non-dry-run) primary cell behind hard locks.

    Requires: a non-dry-run config with ``confirm_full_run=true`` and an
    explicit positive ``max_seeds`` (never defaults to all seeds). Runs of
    more than three seeds require ``allow_large_run`` (or the config's
    ``extra_confirm_large_run``); a 30-seed run requires ``allow_large_run``.
    """
    validate_primary_inputs(config)
    if config.dry_run:
        raise RuntimeError("run_primary_confirmed requires a non-dry-run config")
    if not config.confirm_full_run:
        raise RuntimeError("controlled primary run requires confirm_full_run=true")
    if config.allow_live_fetch:
        raise RuntimeError("allow_live_fetch must be false (no live feeds)")
    if max_seeds is None:
        raise RuntimeError(
            "controlled primary run requires an explicit max_seeds "
            "(it never defaults to running all seeds)"
        )
    if not isinstance(max_seeds, int) or max_seeds <= 0:
        raise ValueError(f"max_seeds must be a positive int; got {max_seeds!r}")
    if max_seeds > 3 and not (allow_large_run or config.extra_confirm_large_run):
        raise RuntimeError(
            f"max_seeds={max_seeds} (>3) requires allow_large_run=True "
            "(or config.extra_confirm_large_run=true)"
        )
    if max_seeds >= 30 and not allow_large_run:
        raise RuntimeError(
            "a 30-seed controlled run requires allow_large_run=True explicitly"
        )

    if out_override is not None:
        config = config.model_copy(update={"output_dir": out_override})

    make_primary_output_layout(config)
    output_dir = Path(config.output_dir)
    seeds_run = list(config.seeds)[:max_seeds]
    config_sha = hashlib.sha256(config.model_dump_json().encode("utf-8")).hexdigest()

    core = _execute_primary_seeds(
        config,
        config_sha,
        seeds_run,
        output_dir,
        dry_run=False,
        manifest_notes=(
            "Controlled primary execution (Phase 13). NOT a final paper result "
            "unless all pre-registered seeds complete and outputs are frozen."
        ),
    )
    return {
        "config_name": config.config_name,
        "output_dir": core["output_dir"],
        "dry_run": False,
        "seeds_requested": list(config.seeds),
        "seeds_run": core["seeds_run"],
        "seeds_skipped_from_checkpoint": core["seeds_skipped_from_checkpoint"],
        "fleet_size": core["fleet_size"],
        "capacity": core["capacity"],
        "strategies": core["strategies"],
        "strategy_count": core["strategy_count"],
        "pair_count_min": core["pair_count_min"],
        "pair_count_max": core["pair_count_max"],
        "metric_rows": core["metric_rows"],
        "audit_logs_valid": core["audit_logs_valid"],
        "runtime_seconds": core["runtime_seconds"],
        "note": (
            "Controlled primary execution; interpret only after the planned "
            "seed count completes."
        ),
    }


def plan_primary_run(
    config_path: str | Path = _DEFAULT_CONFIG,
    max_seeds: int | None = None,
) -> dict[str, Any]:
    """Result-free plan: validate guardrails + estimate; execute nothing.

    Creates no directories and runs no pipeline; it only reports what a run
    *would* do.
    """
    config = load_primary_config(config_path)
    validate_primary_inputs(config)
    estimate = estimate_primary_runtime(config)

    if config.dry_run:
        eff = max(1, max_seeds if max_seeds is not None else config.max_seeds_allowed_without_confirm)
        seeds_would_run = list(config.seeds)[:eff]
    elif max_seeds is not None:
        seeds_would_run = list(config.seeds)[:max_seeds]
    else:
        # Non-dry plan with no max_seeds: a confirmed run would REQUIRE an
        # explicit max_seeds, so report the full requested set as the ceiling.
        seeds_would_run = list(config.seeds)

    root = Path(config.output_dir)
    output_subdirs = [
        str(root / "checkpoints"),
        str(root / "metrics"),
        *[str(root / f"seed_{s:03d}") for s in seeds_would_run],
    ]
    guardrails = {
        "dry_run": config.dry_run,
        "confirm_full_run": config.confirm_full_run,
        "allow_live_fetch": config.allow_live_fetch,
        "max_seeds_allowed_without_confirm": config.max_seeds_allowed_without_confirm,
        "confirmed_run_requires_explicit_max_seeds": not config.dry_run,
        "large_run_requires_allow_large_run": bool(
            max_seeds is not None and max_seeds > 3
        ),
        "gbt_requires_artifact": "gbt_comparator" in config.strategies,
    }
    return {
        "config_name": config.config_name,
        "dry_run": config.dry_run,
        "fleet_size": config.fleet_size,
        "capacity": config.capacity,
        "seeds_requested": list(config.seeds),
        "seeds_would_run": seeds_would_run,
        "seed_count_would_run": len(seeds_would_run),
        "strategy_count": len([s for s in config.strategies if s != "gbt_comparator"]),
        "output_dir": str(root),
        "output_subdirs": output_subdirs,
        "estimate": estimate,
        "guardrails": guardrails,
        "executed": False,
    }


def run_primary_experiment(
    config_path: str | Path = _DEFAULT_CONFIG,
    confirm: bool = False,
    max_seeds: int | None = None,
    allow_large_run: bool = False,
    out_override: str | None = None,
) -> dict[str, Any]:
    """Entry point for the primary experiment.

    Phase 13 behaviour:
      - dry-run configs route to :func:`run_primary_dryrun`;
      - a non-dry-run config without ``confirm`` raises ``RuntimeError``;
      - a non-dry-run config WITH ``confirm`` runs a *controlled* cell via
        :func:`run_primary_confirmed` (which still requires an explicit
        ``max_seeds`` and, beyond three seeds, ``allow_large_run``).
    """
    config = load_primary_config(config_path)
    if config.dry_run:
        cap = max_seeds if max_seeds is not None else max(
            1, config.max_seeds_allowed_without_confirm
        )
        return run_primary_dryrun(config_path, max_seeds=cap, out_override=out_override)
    if not confirm:
        raise RuntimeError(
            "refusing to run a non-dry-run primary without confirm=True"
        )
    return run_primary_confirmed(
        config,
        max_seeds=max_seeds,
        out_override=out_override,
        allow_large_run=allow_large_run,
    )
