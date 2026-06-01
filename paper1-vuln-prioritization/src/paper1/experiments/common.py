"""Shared experiment-runner helpers (Phase 11).

Result-directory layout, a provenance manifest, a parquet-or-CSV writer,
config / fixture hashing, and lightweight output validators. These are
used by the end-to-end *smoke* runner (``paper1.experiments.smoke``) and
will be reused by the primary / robustness / sensitivity runners in later
phases. Nothing here calls a live feed or fabricates results.
"""

from __future__ import annotations

import warnings as _warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict

from paper1 import __framework_version__, __version__
from paper1.audit.hash_chain import verify_chain
from paper1.utils.io import atomic_write_json, compute_file_sha256, read_json

__all__ = [
    "ExperimentManifest",
    "collect_artifact_versions",
    "dataframe_to_parquet_or_csv",
    "ensure_result_dirs",
    "load_manifest",
    "stable_config_sha",
    "validate_audit_logs",
    "validate_strategy_outputs",
    "write_manifest",
]

# Repo root: .../src/paper1/experiments/common.py -> parents[3].
_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURES = _REPO_ROOT / "data" / "fixtures"
_CONFIGS = _REPO_ROOT / "configs"

# Configs and fixtures whose hashes pin a smoke run's provenance.
_PROVENANCE_CONFIGS = (
    "blackout_primary.yaml",
    "approver_policy_a.yaml",
    "identity_ad_entra.yaml",
)
_PROVENANCE_FIXTURES = (
    "vulnerabilities_toy.json",
    "kev_toy.json",
    "poc_toy.csv",
)


class ExperimentManifest(BaseModel):
    """Provenance record written alongside every experiment's outputs."""

    model_config = ConfigDict(extra="forbid")

    config_name: str
    config_sha: str
    code_version: str
    created_at: datetime
    seeds: list[int]
    strategies: list[str]
    output_dir: str
    artifact_versions: dict[str, Any]
    notes: str = ""


def ensure_result_dirs(output_dir: str | Path) -> Path:
    """Create ``output_dir`` and its ``metrics/`` subdir; return the root."""
    root = Path(output_dir)
    (root / "metrics").mkdir(parents=True, exist_ok=True)
    return root


def write_manifest(path: str | Path, manifest: ExperimentManifest) -> None:
    """Write a manifest as pretty JSON (atomic)."""
    atomic_write_json(path, manifest.model_dump(mode="json"))


def load_manifest(path: str | Path) -> ExperimentManifest:
    """Load a manifest written by :func:`write_manifest`."""
    return ExperimentManifest(**read_json(path))


def dataframe_to_parquet_or_csv(df: pd.DataFrame, path: str | Path) -> Path:
    """Write a DataFrame, preferring parquet when an engine is available.

    - If ``path`` ends in ``.csv`` the frame is written as CSV verbatim
      (the documented smoke layout uses ``.csv`` filenames).
    - Otherwise a parquet write is attempted at ``path`` (suffix forced to
      ``.parquet``); if no parquet engine is installed it falls back to a
      sibling ``.csv`` file with a warning.

    Returns the path actually written.
    """
    p = Path(path)
    if p.suffix == ".csv":
        df.to_csv(p, index=False)
        return p
    parquet_path = p.with_suffix(".parquet")
    try:
        df.to_parquet(parquet_path, index=False)
        return parquet_path
    except Exception as exc:  # parquet engine missing / unsupported dtype
        csv_path = p.with_suffix(".csv")
        _warnings.warn(
            f"parquet unavailable ({exc}); wrote CSV instead: {csv_path}",
            stacklevel=2,
        )
        df.to_csv(csv_path, index=False)
        return csv_path


def stable_config_sha(config_path: str | Path) -> str:
    """SHA-256 of the on-disk config bytes (stable across runs)."""
    return compute_file_sha256(config_path)


def collect_artifact_versions() -> dict[str, Any]:
    """Collect code / config / fixture versions for the manifest."""
    config_hashes: dict[str, str] = {}
    for name in _PROVENANCE_CONFIGS:
        fp = _CONFIGS / name
        if fp.exists():
            config_hashes[name] = compute_file_sha256(fp)
    fixture_hashes: dict[str, str] = {}
    for name in _PROVENANCE_FIXTURES:
        fp = _FIXTURES / name
        if fp.exists():
            fixture_hashes[name] = compute_file_sha256(fp)
    return {
        "package_version": __version__,
        "framework_version": __framework_version__,
        "config_hashes": config_hashes,
        "fixture_hashes": fixture_hashes,
    }


def validate_strategy_outputs(
    rankings_by_strategy: dict[str, pd.DataFrame],
    expected_pair_count: int,
) -> None:
    """Fail loudly if any ranking is malformed.

    Checks, for every strategy: the ranking has the expected pair count,
    contains no duplicate ``pair_id``, and exposes ``rank`` /
    ``priority_score`` columns.
    """
    if not rankings_by_strategy:
        raise ValueError("no strategy rankings to validate")
    for name, df in rankings_by_strategy.items():
        for col in ("pair_id", "rank", "priority_score"):
            if col not in df.columns:
                raise ValueError(f"strategy {name!r} ranking missing column {col!r}")
        if len(df) != expected_pair_count:
            raise ValueError(
                f"strategy {name!r} has {len(df)} rows; expected {expected_pair_count}"
            )
        if df["pair_id"].duplicated().any():
            raise ValueError(f"strategy {name!r} ranking has duplicate pair_id values")


def validate_audit_logs(audit_log_paths: dict[str, str | Path]) -> bool:
    """Verify each audit log's hash chain; raise on the first failure.

    Returns ``True`` when all chains verify.
    """
    if not audit_log_paths:
        raise ValueError("no audit logs to validate")
    for name, path in audit_log_paths.items():
        ok, issues = verify_chain(path)
        if not ok:
            raise ValueError(
                f"audit log for {name!r} failed hash-chain verification: {issues[:3]}"
            )
    return True
