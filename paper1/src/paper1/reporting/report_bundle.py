"""Report bundle: load frozen primary results, emit tables + figures (Phase 17).

Reads ONLY the frozen artifact (after verifying its freeze manifest), never
raw/unfrozen intermediate files. Produces tables and figures plus a
``report_manifest.json`` describing exactly what was generated. No
interpretation or paper claims are produced here.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from paper1 import __framework_version__
from paper1.experiments.inspect import verify_freeze_manifest
from paper1.reporting.primary_figures import generate_all_figures
from paper1.reporting.primary_tables import generate_all_tables
from paper1.utils.io import atomic_write_json, read_json
from paper1.utils.time import utc_now

__all__ = [
    "generate_primary_report_bundle",
    "load_frozen_primary_results",
]

_FREEZE_NAME = "FREEZE_MANIFEST.json"


def load_frozen_primary_results(output_dir: str | Path = "results/primary_full_v1") -> dict[str, Any]:
    """Load the frozen primary metric frames after verifying the freeze.

    Raises if there is no freeze manifest or it does not verify. Loads only
    the aggregate metric frames + manifest + summary; it does NOT read the
    raw per-strategy ranking/schedule/audit files.
    """
    root = Path(output_dir)
    if not root.exists():
        raise FileNotFoundError(f"primary output dir not found: {root}")
    if not (root / _FREEZE_NAME).exists():
        raise RuntimeError(
            f"no {_FREEZE_NAME} in {root}; freeze the output before generating a report"
        )
    if not verify_freeze_manifest(root):
        raise RuntimeError(
            f"freeze verification failed for {root}; refusing to generate a report "
            "from an unverified artifact"
        )

    metrics = root / "metrics"
    frozen: dict[str, Any] = {
        "output_dir": str(root),
        "freeze_verified": True,
        "per_seed_metrics": pd.read_csv(metrics / "per_seed_metrics.csv"),
        "aggregated_metrics": pd.read_csv(metrics / "aggregated_metrics.csv"),
        "eehda_report": pd.read_csv(metrics / "eehda_report.csv"),
        "manifest": read_json(root / "manifest.json"),
    }
    summary_path = root / "summary.md"
    frozen["summary"] = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
    return frozen


def _copy_outputs(generated: dict[str, Any], src_dir: Path, dst_dir: Path) -> None:
    """Copy already-written files from src_dir into dst_dir (flat mirror)."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for entry in generated.values():
        paths = entry.values() if isinstance(entry, dict) else entry
        for p in paths:
            shutil.copy2(p, dst_dir / Path(p).name)


def _collect_warnings(frozen: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    eehda = frozen["eehda_report"]
    if "fraction_of_oracle" in eehda.columns:
        frac = pd.to_numeric(eehda["fraction_of_oracle"], errors="coerce").dropna()
        if ((frac < 0.0) | (frac > 1.0)).any():
            warnings.append(
                "some fraction_of_oracle values fall outside [0, 1]; reported as observed"
            )
    per_seed = frozen["per_seed_metrics"]
    values = pd.to_numeric(per_seed["value"], errors="coerce")
    nan_metrics = sorted(set(per_seed.loc[values.isna(), "metric"]))
    if nan_metrics:
        warnings.append(f"NaN values present in metrics: {nan_metrics} (documented allowed cases)")
    warnings.append(
        "capacity in acceptance table is the configured value passed to the reporter "
        "(the runner does not persist capacity into the frozen artifact)."
    )
    return warnings


def generate_primary_report_bundle(
    output_dir: str | Path = "results/primary_full_v1",
    report_dir: str | Path | None = None,
    paper_dir: str | Path = "paper",
    capacity: int | None = 100,
) -> dict[str, Any]:
    """Generate all tables + figures + a report manifest from the frozen output."""
    root = Path(output_dir)
    frozen = load_frozen_primary_results(root)  # verifies freeze

    report_root = Path(report_dir) if report_dir is not None else root / "report"
    tables_dir = report_root / "tables"
    figures_dir = report_root / "figures"
    paper_root = Path(paper_dir)

    table_files = generate_all_tables(frozen, tables_dir, capacity=capacity)
    figure_files = generate_all_figures(frozen, figures_dir)

    # Mirror into the paper/ tree.
    _copy_outputs(table_files, tables_dir, paper_root / "tables")
    _copy_outputs(figure_files, figures_dir, paper_root / "figures")

    freeze_sha = hashlib.sha256(
        (root / _FREEZE_NAME).read_bytes()
    ).hexdigest()
    per_seed = frozen["per_seed_metrics"]
    row_counts = {
        "metric_rows": len(per_seed),
        "seeds": int(per_seed["seed"].nunique()),
        "strategies": int(per_seed["strategy"].nunique()),
    }
    warnings = _collect_warnings(frozen)

    manifest = {
        "source_output_dir": str(root),
        "freeze_manifest_sha": freeze_sha,
        "generated_at": utc_now().isoformat(),
        "code_version": __framework_version__,
        "table_files": table_files,
        "figure_files": figure_files,
        "row_counts": row_counts,
        "warnings": warnings,
        "note": (
            "Tables/figures generated from the FROZEN primary artifact only. "
            "Interpretation belongs in Phase 18; these are not paper claims."
        ),
    }

    report_root.mkdir(parents=True, exist_ok=True)
    _write_report_summary(report_root / "summary.md", frozen, table_files, figure_files, capacity)
    atomic_write_json(report_root / "report_manifest.json", manifest)

    # Mirror summary + manifest into paper/report/ as well.
    paper_report = paper_root / "report"
    paper_report.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report_root / "summary.md", paper_report / "summary.md")
    shutil.copy2(report_root / "report_manifest.json", paper_report / "report_manifest.json")

    manifest["report_dir"] = str(report_root)
    manifest["paper_dir"] = str(paper_root)
    return manifest


def _write_report_summary(
    path: Path,
    frozen: dict[str, Any],
    table_files: dict[str, Any],
    figure_files: dict[str, Any],
    capacity: int | None,
) -> None:
    per_seed = frozen["per_seed_metrics"]
    values = pd.to_numeric(per_seed["value"], errors="coerce")
    sched = values[per_seed["metric"] == "scheduled_count"]
    lines: list[str] = []
    lines.append("# Primary report bundle (generated from frozen artifact)")
    lines.append("")
    lines.append(
        "**Generated from the FROZEN primary outputs only. Not a paper claim; "
        "interpretation belongs in Phase 18.**"
    )
    lines.append("")
    lines.append(f"- source: `{frozen['output_dir']}` (freeze verified: {frozen['freeze_verified']})")
    lines.append(f"- seeds: {per_seed['seed'].nunique()}")
    lines.append(f"- strategies: {per_seed['strategy'].nunique()}")
    lines.append(f"- metric rows: {len(per_seed)}")
    lines.append(f"- NaN values: {int(values.isna().sum())}")
    lines.append(f"- infinite values: {int(np.isinf(values).sum())}")
    if len(sched):
        lines.append(f"- max scheduled_count: {sched.max():.0f} (capacity {capacity})")
    lines.append("")
    lines.append(f"## Tables ({len(table_files)})")
    lines.append("")
    for name in sorted(table_files):
        lines.append(f"- `{name}` (csv/md/tex)")
    lines.append("")
    lines.append(f"## Figures ({len(figure_files)})")
    lines.append("")
    for name in sorted(figure_files):
        lines.append(f"- `{name}` (png/pdf)")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
