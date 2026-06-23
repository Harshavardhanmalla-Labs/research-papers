"""Primary result inspection, freeze manifest, and run comparison (Phase 14).

This layer reads primary outputs *from disk* and catches silent pipeline
failures before any seeds are scaled up or any tables are produced. It does
not run the pipeline, call live feeds, or create paper claims. It also
provides a content-addressed freeze manifest so that later tables/figures
consume a verified, immutable snapshot.

Severity model: a report ``passed`` is False if any issue is ``error`` or
``fatal``. Under ``strict``, ``warning`` issues also fail the report.

Documented metrics that may legitimately be NaN (denominator zero) and are
therefore NOT flagged as errors:
  - kev_breach_rate (no KEV-due pairs),
  - capacity_efficiency (no non-censored scheduled pairs),
  - precision_at_k / recall_at_k / ndcg_at_k (no eligible/positive items).
No metric value may be infinite.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict

from paper1 import __framework_version__
from paper1.audit.hash_chain import verify_chain
from paper1.utils.io import atomic_write_json, compute_file_sha256, read_json
from paper1.utils.time import utc_now

__all__ = [
    "InspectionIssue",
    "InspectionReport",
    "compare_primary_runs",
    "freeze_primary_results",
    "inspect_primary_output",
    "summarize_primary_output",
    "validate_audit_logs",
    "validate_eehda_report",
    "validate_primary_metrics",
    "validate_rankings",
    "validate_schedules",
    "verify_freeze_manifest",
]

Severity = Literal["info", "warning", "error", "fatal"]
_BLOCKING: set[str] = {"error", "fatal"}

# Per-(seed, strategy) metric names written by the runner.
_REQUIRED_METRIC_COLUMNS = {"seed", "strategy", "metric", "value"}
_ALLOWED_NAN_METRICS = {
    "kev_breach_rate",
    "capacity_efficiency",
    "precision_at_k",
    "recall_at_k",
    "ndcg_at_k",
}
_STRATEGY_FILES = ("ranking.csv", "schedule_history.csv", "audit_log.jsonl", "metrics.csv")
_EEHDA_COLUMNS = (
    "strategy",
    "absolute",
    "relative_to_random",
    "relative_to_epss",
    "fraction_of_oracle",
)
_FREEZE_NAME = "FREEZE_MANIFEST.json"


class InspectionIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Severity
    code: str
    message: str
    path: str | None = None
    seed: int | None = None
    strategy: str | None = None
    metric: str | None = None


class InspectionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_dir: str
    created_at: datetime
    seed_count: int
    strategy_count: int
    metric_row_count: int
    audit_logs_checked: int
    audit_logs_valid: bool
    issues: list[InspectionIssue]
    passed: bool
    summary: dict[str, Any]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _issue(severity: Severity, code: str, message: str, **kw: Any) -> InspectionIssue:
    return InspectionIssue(severity=severity, code=code, message=message, **kw)


def _seed_dirs(output_dir: Path) -> list[Path]:
    return sorted(p for p in output_dir.glob("seed_*") if p.is_dir())


def _strategy_dirs(seed_dir: Path) -> list[Path]:
    return sorted(p for p in seed_dir.glob("strategy_*") if p.is_dir())


def _strategy_name(strategy_dir: Path) -> str:
    return strategy_dir.name[len("strategy_") :]


def _seed_number(seed_dir: Path) -> int | None:
    try:
        return int(seed_dir.name.split("_")[1])
    except (IndexError, ValueError):
        return None


# ---------------------------------------------------------------------------
# metric-level validation
# ---------------------------------------------------------------------------


def validate_primary_metrics(per_seed_metrics: pd.DataFrame) -> list[InspectionIssue]:
    """Validate the per-seed metric frame (columns, finiteness, sanity)."""
    issues: list[InspectionIssue] = []
    missing = _REQUIRED_METRIC_COLUMNS - set(per_seed_metrics.columns)
    if missing:
        issues.append(
            _issue(
                "fatal",
                "METRIC_MISSING_COLUMNS",
                f"per_seed_metrics missing columns: {sorted(missing)}",
            )
        )
        return issues

    df = per_seed_metrics.copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    for _, row in df.iterrows():
        v = row["value"]
        metric = str(row["metric"])
        seed = int(row["seed"]) if not pd.isna(row["seed"]) else None
        strat = str(row["strategy"])
        if np.isinf(v):
            issues.append(
                _issue(
                    "error",
                    "INFINITE_METRIC",
                    f"metric {metric!r} is infinite ({v})",
                    seed=seed,
                    strategy=strat,
                    metric=metric,
                )
            )
        elif pd.isna(v):
            if metric in _ALLOWED_NAN_METRICS:
                issues.append(
                    _issue(
                        "info",
                        "ALLOWED_NAN",
                        f"metric {metric!r} is NaN (documented allowed case)",
                        seed=seed,
                        strategy=strat,
                        metric=metric,
                    )
                )
            else:
                issues.append(
                    _issue(
                        "error",
                        "UNEXPECTED_NAN",
                        f"metric {metric!r} is NaN but not a documented NaN metric",
                        seed=seed,
                        strategy=strat,
                        metric=metric,
                    )
                )

    # oracle EHD must not exceed random EHD per seed (both present).
    ehd = df[df["metric"] == "ehd_absolute"]
    if not ehd.empty:
        pivot = ehd.pivot_table(index="seed", columns="strategy", values="value", aggfunc="first")
        if "oracle" in pivot.columns and "random" in pivot.columns:
            for seed, r in pivot.iterrows():
                o, rnd = r.get("oracle"), r.get("random")
                if pd.notna(o) and pd.notna(rnd) and o > rnd + 1e-9:
                    issues.append(
                        _issue(
                            "error",
                            "ORACLE_WORSE_THAN_RANDOM",
                            f"oracle EHD {o} > random EHD {rnd} for seed {int(seed)}",
                            seed=int(seed),
                            metric="ehd_absolute",
                        )
                    )
        # proposed_full EHD must be finite.
        if "proposed_full" in pivot.columns:
            for seed, val in pivot["proposed_full"].items():
                if pd.isna(val) or np.isinf(val):
                    issues.append(
                        _issue(
                            "error",
                            "PROPOSED_FULL_NONFINITE",
                            f"proposed_full EHD is non-finite ({val}) for seed {int(seed)}",
                            seed=int(seed),
                            strategy="proposed_full",
                            metric="ehd_absolute",
                        )
                    )
    return issues


def validate_eehda_report(eehda: pd.DataFrame) -> list[InspectionIssue]:
    """Validate the EEHDA report columns and finiteness."""
    issues: list[InspectionIssue] = []
    missing = [c for c in _EEHDA_COLUMNS if c not in eehda.columns]
    if missing:
        issues.append(
            _issue("error", "EEHDA_MISSING_COLUMN", f"eehda_report missing columns: {missing}")
        )
        return issues
    # 'absolute' must be finite; relative_* and fraction_of_oracle may be NaN
    # (zero-denominator, documented) but never infinite.
    for _, row in eehda.iterrows():
        strat = str(row["strategy"])
        absval = pd.to_numeric(row["absolute"], errors="coerce")
        if pd.isna(absval) or np.isinf(absval):
            issues.append(
                _issue(
                    "error",
                    "EEHDA_NONFINITE",
                    f"eehda 'absolute' non-finite ({row['absolute']}) for {strat}",
                    strategy=strat,
                )
            )
        for col in ("relative_to_random", "relative_to_epss", "fraction_of_oracle"):
            val = pd.to_numeric(row[col], errors="coerce")
            if not pd.isna(val) and np.isinf(val):
                issues.append(
                    _issue(
                        "error",
                        "EEHDA_INFINITE",
                        f"eehda {col!r} is infinite for {strat}",
                        strategy=strat,
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# per-seed structural validation
# ---------------------------------------------------------------------------


def validate_rankings(seed_dir: Path) -> list[InspectionIssue]:
    """Check each strategy ranking: no duplicate pair_id, contiguous ranks."""
    issues: list[InspectionIssue] = []
    seed = _seed_number(seed_dir)
    for sdir in _strategy_dirs(seed_dir):
        strat = _strategy_name(sdir)
        ranking_path = sdir / "ranking.csv"
        if not ranking_path.exists():
            continue
        ranking = pd.read_csv(ranking_path)
        if "pair_id" in ranking.columns and ranking["pair_id"].duplicated().any():
            issues.append(
                _issue(
                    "error",
                    "DUPLICATE_PAIR_ID",
                    "ranking has duplicate pair_id values",
                    path=str(ranking_path),
                    seed=seed,
                    strategy=strat,
                )
            )
        if "rank" in ranking.columns and len(ranking):
            ranks = sorted(int(r) for r in ranking["rank"].tolist())
            if ranks != list(range(1, len(ranks) + 1)):
                issues.append(
                    _issue(
                        "error",
                        "NONCONTIGUOUS_RANKS",
                        f"ranks are not contiguous 1..N (n={len(ranks)})",
                        path=str(ranking_path),
                        seed=seed,
                        strategy=strat,
                    )
                )
    return issues


def validate_schedules(seed_dir: Path, capacity: int | None = None) -> list[InspectionIssue]:
    """Check schedule_history pairs are a subset of ranking pairs + capacity."""
    issues: list[InspectionIssue] = []
    seed = _seed_number(seed_dir)
    for sdir in _strategy_dirs(seed_dir):
        strat = _strategy_name(sdir)
        ranking_path = sdir / "ranking.csv"
        sched_path = sdir / "schedule_history.csv"
        if not ranking_path.exists() or not sched_path.exists():
            continue
        ranking = pd.read_csv(ranking_path)
        sched = pd.read_csv(sched_path)
        ranking_ids = set(ranking.get("pair_id", pd.Series(dtype=str)).astype(str))
        sched_ids = set(sched.get("pair_id", pd.Series(dtype=str)).astype(str))
        extra = sched_ids - ranking_ids
        if extra:
            issues.append(
                _issue(
                    "error",
                    "SCHEDULE_PAIR_NOT_IN_RANKING",
                    f"{len(extra)} scheduled pair(s) not present in ranking",
                    path=str(sched_path),
                    seed=seed,
                    strategy=strat,
                )
            )
        n_sched = len(sched)
        if n_sched > len(ranking):
            issues.append(
                _issue(
                    "error",
                    "SCHEDULED_EXCEEDS_PAIRS",
                    f"scheduled {n_sched} > ranked pairs {len(ranking)}",
                    path=str(sched_path),
                    seed=seed,
                    strategy=strat,
                )
            )
        if capacity is not None and n_sched > capacity:
            issues.append(
                _issue(
                    "error",
                    "SCHEDULED_EXCEEDS_CAPACITY",
                    f"scheduled {n_sched} > capacity {capacity}",
                    path=str(sched_path),
                    seed=seed,
                    strategy=strat,
                )
            )
    return issues


def validate_audit_logs(seed_dir: Path) -> list[InspectionIssue]:
    """Verify every strategy audit-log hash chain under a seed directory."""
    issues: list[InspectionIssue] = []
    seed = _seed_number(seed_dir)
    for sdir in _strategy_dirs(seed_dir):
        strat = _strategy_name(sdir)
        log = sdir / "audit_log.jsonl"
        if not log.exists():
            issues.append(
                _issue(
                    "error",
                    "AUDIT_LOG_MISSING",
                    "audit_log.jsonl missing",
                    path=str(log),
                    seed=seed,
                    strategy=strat,
                )
            )
            continue
        ok, problems = verify_chain(log)
        if not ok:
            issues.append(
                _issue(
                    "error",
                    "AUDIT_CHAIN_INVALID",
                    f"hash chain failed: {problems[:2]}",
                    path=str(log),
                    seed=seed,
                    strategy=strat,
                )
            )
    return issues


# ---------------------------------------------------------------------------
# top-level inspection
# ---------------------------------------------------------------------------


def summarize_primary_output(output_dir: str | Path) -> dict[str, Any]:
    """Lightweight structural summary (counts + file presence) of an output."""
    root = Path(output_dir)
    seed_dirs = _seed_dirs(root)
    psm = root / "metrics" / "per_seed_metrics.csv"
    metric_rows = 0
    strategies: set[str] = set()
    seeds: set[int] = set()
    if psm.exists():
        df = pd.read_csv(psm)
        metric_rows = len(df)
        strategies = set(df.get("strategy", pd.Series(dtype=str)).astype(str))
        seeds = {int(s) for s in df.get("seed", pd.Series(dtype=int)).tolist()}
    audit_logs = [
        log for sd in seed_dirs for log in sd.glob("strategy_*/audit_log.jsonl")
    ]
    return {
        "output_dir": str(root),
        "exists": root.exists(),
        "seed_dir_count": len(seed_dirs),
        "seed_count": len(seeds),
        "strategy_count": len(strategies),
        "strategies": sorted(strategies),
        "metric_row_count": metric_rows,
        "audit_log_count": len(audit_logs),
        "has_manifest": (root / "manifest.json").exists(),
        "has_summary": (root / "summary.md").exists(),
        "has_freeze": (root / _FREEZE_NAME).exists(),
    }


def inspect_primary_output(
    output_dir: str | Path,
    strict: bool = True,
    capacity: int | None = None,
) -> InspectionReport:
    """Inspect a primary output directory and return a structured report."""
    root = Path(output_dir)
    issues: list[InspectionIssue] = []

    if not root.exists():
        issues.append(_issue("fatal", "OUTPUT_DIR_MISSING", f"output dir not found: {root}"))
        return _finalize_report(root, issues, strict, 0, 0, 0, 0, False)

    # ---- top-level files --------------------------------------------------
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        issues.append(_issue("fatal", "MANIFEST_MISSING", "manifest.json missing", path=str(manifest_path)))
    psm_path = root / "metrics" / "per_seed_metrics.csv"
    if not psm_path.exists():
        issues.append(_issue("fatal", "METRICS_FILE_MISSING", "metrics/per_seed_metrics.csv missing", path=str(psm_path)))
    for rel, code in (
        ("metrics/aggregated_metrics.csv", "AGGREGATED_MISSING"),
        ("metrics/eehda_report.csv", "EEHDA_MISSING"),
    ):
        if not (root / rel).exists():
            issues.append(_issue("error", code, f"{rel} missing", path=str(root / rel)))
    if not (root / "summary.md").exists():
        issues.append(_issue("warning", "SUMMARY_MISSING", "summary.md missing"))

    # ---- manifest strategies ----------------------------------------------
    manifest_strategies: list[str] = []
    if manifest_path.exists():
        try:
            manifest = read_json(manifest_path)
            manifest_strategies = list(manifest.get("strategies", []))
        except Exception as exc:  # malformed manifest
            issues.append(_issue("error", "MANIFEST_UNREADABLE", f"manifest unreadable: {exc}", path=str(manifest_path)))

    # ---- per-seed metric frame --------------------------------------------
    per_seed = pd.DataFrame()
    if psm_path.exists():
        per_seed = pd.read_csv(psm_path)
        issues.extend(validate_primary_metrics(per_seed))

    # ---- eehda ------------------------------------------------------------
    eehda_path = root / "metrics" / "eehda_report.csv"
    if eehda_path.exists():
        issues.extend(validate_eehda_report(pd.read_csv(eehda_path)))

    # ---- seed directories -------------------------------------------------
    seed_dirs = _seed_dirs(root)
    if not seed_dirs:
        issues.append(_issue("fatal", "NO_SEED_DIRS", "no seed_* directories found"))

    audit_logs_checked = 0
    audit_logs_valid = True
    metric_seeds = (
        {int(s) for s in per_seed["seed"].tolist()} if "seed" in per_seed.columns else set()
    )
    for seed_dir in seed_dirs:
        seed = _seed_number(seed_dir)
        present_strategies = {_strategy_name(d) for d in _strategy_dirs(seed_dir)}
        # required strategy directories + files
        expected = manifest_strategies or sorted(present_strategies)
        for strat in expected:
            sdir = seed_dir / f"strategy_{strat}"
            if not sdir.is_dir():
                issues.append(
                    _issue("error", "MISSING_STRATEGY", f"strategy dir missing: {strat}", seed=seed, strategy=strat)
                )
                continue
            for fname in _STRATEGY_FILES:
                if not (sdir / fname).exists():
                    issues.append(
                        _issue(
                            "error",
                            "STRATEGY_FILE_MISSING",
                            f"{fname} missing for strategy {strat}",
                            path=str(sdir / fname),
                            seed=seed,
                            strategy=strat,
                        )
                    )
        issues.extend(validate_rankings(seed_dir))
        issues.extend(validate_schedules(seed_dir, capacity=capacity))
        audit_issues = validate_audit_logs(seed_dir)
        issues.extend(audit_issues)
        logs = list(seed_dir.glob("strategy_*/audit_log.jsonl"))
        audit_logs_checked += len(logs)
        if any(i.code in ("AUDIT_CHAIN_INVALID", "AUDIT_LOG_MISSING") for i in audit_issues):
            audit_logs_valid = False

        # checkpoint consistency
        ckpt = root / "checkpoints" / f"seed_{seed:03d}.seed_complete.json" if seed is not None else None
        if ckpt is not None and ckpt.exists():
            try:
                payload = read_json(ckpt)
                for p in (payload.get("audit_paths") or {}).values():
                    if not Path(p).exists():
                        issues.append(
                            _issue(
                                "warning",
                                "CHECKPOINT_AUDIT_MISSING",
                                "checkpoint references a missing audit log",
                                path=str(ckpt),
                                seed=seed,
                            )
                        )
                        break
            except Exception as exc:  # malformed checkpoint
                issues.append(_issue("warning", "CHECKPOINT_UNREADABLE", f"checkpoint unreadable: {exc}", path=str(ckpt), seed=seed))

        # seed present in metrics?
        if seed is not None and metric_seeds and seed not in metric_seeds:
            issues.append(
                _issue("error", "SEED_NOT_IN_METRICS", f"seed {seed} has a dir but no metric rows", seed=seed)
            )

    seed_count = len(metric_seeds) if metric_seeds else len(seed_dirs)
    strategy_count = (
        per_seed["strategy"].nunique() if "strategy" in per_seed.columns else 0
    )
    return _finalize_report(
        root,
        issues,
        strict,
        seed_count,
        int(strategy_count),
        len(per_seed),
        audit_logs_checked,
        audit_logs_valid,
    )


def _finalize_report(
    root: Path,
    issues: list[InspectionIssue],
    strict: bool,
    seed_count: int,
    strategy_count: int,
    metric_row_count: int,
    audit_logs_checked: int,
    audit_logs_valid: bool,
) -> InspectionReport:
    by_sev: dict[str, int] = {}
    for i in issues:
        by_sev[i.severity] = by_sev.get(i.severity, 0) + 1
    has_blocking = any(i.severity in _BLOCKING for i in issues)
    has_warning = any(i.severity == "warning" for i in issues)
    passed = (not has_blocking) and (not (strict and has_warning))
    summary = {
        "issue_counts": by_sev,
        "strict": strict,
        "has_blocking": has_blocking,
        "has_warning": has_warning,
    }
    return InspectionReport(
        output_dir=str(root),
        created_at=utc_now(),
        seed_count=seed_count,
        strategy_count=strategy_count,
        metric_row_count=metric_row_count,
        audit_logs_checked=audit_logs_checked,
        audit_logs_valid=audit_logs_valid,
        issues=issues,
        passed=passed,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# freeze manifest
# ---------------------------------------------------------------------------


def _iter_result_files(root: Path) -> list[Path]:
    """Files that constitute the frozen experiment result.

    Excludes the freeze manifest itself and the derived ``report/`` subtree.
    The ``report/`` directory holds regenerable tables/figures produced FROM
    the frozen result (Phase 17); it is not part of the immutable experiment
    artifact, so it neither contributes to nor invalidates the freeze.
    """
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.name == _FREEZE_NAME:
            continue
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] == "report":
            continue
        out.append(p)
    return sorted(out, key=lambda p: p.relative_to(root).as_posix())


def freeze_primary_results(
    output_dir: str | Path,
    freeze_name: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Write a content-addressed FREEZE_MANIFEST.json over the output dir.

    Hashes every file under ``output_dir`` (except the freeze manifest
    itself), in deterministic path order. Refuses to overwrite an existing
    freeze unless ``overwrite=True``. Does not modify any result files.
    """
    root = Path(output_dir)
    if not root.exists():
        raise FileNotFoundError(f"output dir not found: {root}")
    freeze_path = root / _FREEZE_NAME
    if freeze_path.exists() and not overwrite:
        raise FileExistsError(
            f"{_FREEZE_NAME} already exists; pass overwrite=True to replace it"
        )

    files = _iter_result_files(root)
    sha_by_file: dict[str, str] = {}
    total_bytes = 0
    for fp in files:
        rel = fp.relative_to(root).as_posix()
        sha_by_file[rel] = compute_file_sha256(fp)
        total_bytes += fp.stat().st_size

    manifest_rel = "manifest.json"
    manifest_sha = sha_by_file.get(manifest_rel)

    payload = {
        "freeze_name": freeze_name or root.name,
        "created_at": utc_now().isoformat(),
        "output_dir": str(root),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "sha256_by_file": sha_by_file,
        "manifest_sha256": manifest_sha,
        "code_version": __framework_version__,
        "note": "Frozen result artifact. Do not modify after paper tables are generated.",
    }
    atomic_write_json(freeze_path, payload)
    return payload


def verify_freeze_manifest(
    output_dir: str | Path,
    ignore: list[str] | None = None,
) -> bool:
    """Recompute hashes and verify the on-disk output matches the freeze.

    Returns False if any frozen file is missing/changed, or if an extra
    (non-ignored) file appears after the freeze.
    """
    root = Path(output_dir)
    freeze_path = root / _FREEZE_NAME
    if not freeze_path.exists():
        return False
    payload = read_json(freeze_path)
    recorded: dict[str, str] = payload.get("sha256_by_file", {})
    ignore_set = set(ignore or [])

    # Every recorded file must exist and match.
    for rel, sha in recorded.items():
        fp = root / rel
        if not fp.exists():
            return False
        if compute_file_sha256(fp) != sha:
            return False

    # No unexpected extra files (excluding the freeze manifest + ignore list).
    for fp in _iter_result_files(root):
        rel = fp.relative_to(root).as_posix()
        if rel in recorded or rel in ignore_set:
            continue
        return False
    return True


# ---------------------------------------------------------------------------
# run comparison
# ---------------------------------------------------------------------------


def _load_per_seed(output_dir: Path) -> pd.DataFrame:
    psm = output_dir / "metrics" / "per_seed_metrics.csv"
    if not psm.exists():
        return pd.DataFrame(columns=["seed", "strategy", "metric", "value"])
    return pd.read_csv(psm)


def _audit_valid_from_metrics(df: pd.DataFrame) -> bool:
    rows = df[df["metric"] == "audit_hash_chain_valid"] if "metric" in df.columns else df
    if rows.empty:
        return False
    return bool((pd.to_numeric(rows["value"], errors="coerce") == 1.0).all())


def compare_primary_runs(
    output_dir_a: str | Path,
    output_dir_b: str | Path,
    tolerance: float = 1e-9,
) -> dict[str, Any]:
    """Compare two primary outputs (e.g. one-seed vs three-seed, or reruns)."""
    a_dir, b_dir = Path(output_dir_a), Path(output_dir_b)
    a, b = _load_per_seed(a_dir), _load_per_seed(b_dir)

    seeds_a = sorted({int(s) for s in a.get("seed", pd.Series(dtype=int)).tolist()})
    seeds_b = sorted({int(s) for s in b.get("seed", pd.Series(dtype=int)).tolist()})
    common = sorted(set(seeds_a) & set(seeds_b))
    strategies_a = sorted(a.get("strategy", pd.Series(dtype=str)).astype(str).unique())
    strategies_b = sorted(b.get("strategy", pd.Series(dtype=str)).astype(str).unique())

    # Determinism on common seeds: align on (seed, strategy, metric).
    key = ["seed", "strategy", "metric"]
    deterministic = True
    n_diff = 0
    max_abs_diff = 0.0
    if common and all(k in a.columns for k in [*key, "value"]) and all(
        k in b.columns for k in [*key, "value"]
    ):
        ac = a[a["seed"].isin(common)].copy()
        bc = b[b["seed"].isin(common)].copy()
        merged = ac.merge(bc, on=key, how="outer", suffixes=("_a", "_b"))
        va = pd.to_numeric(merged["value_a"], errors="coerce").to_numpy()
        vb = pd.to_numeric(merged["value_b"], errors="coerce").to_numpy()
        both_nan = np.isnan(va) & np.isnan(vb)
        close = np.isclose(va, vb, rtol=0.0, atol=tolerance, equal_nan=False) | both_nan
        n_diff = int((~close).sum())
        finite_diffs = np.abs(va - vb)[~both_nan & ~np.isnan(va) & ~np.isnan(vb)]
        max_abs_diff = float(finite_diffs.max()) if finite_diffs.size else 0.0
        deterministic = n_diff == 0

    return {
        "output_dir_a": str(a_dir),
        "output_dir_b": str(b_dir),
        "seeds_a": seeds_a,
        "seeds_b": seeds_b,
        "common_seeds": common,
        "seeds_only_a": sorted(set(seeds_a) - set(seeds_b)),
        "seeds_only_b": sorted(set(seeds_b) - set(seeds_a)),
        "metric_row_count_a": len(a),
        "metric_row_count_b": len(b),
        "strategies_a": strategies_a,
        "strategies_b": strategies_b,
        "audit_valid_a": _audit_valid_from_metrics(a),
        "audit_valid_b": _audit_valid_from_metrics(b),
        "deterministic_common_seed_metrics_equal": bool(deterministic),
        "differences": {
            "n_differing_rows_common_seeds": n_diff,
            "max_abs_diff_common_seeds": max_abs_diff,
        },
    }
