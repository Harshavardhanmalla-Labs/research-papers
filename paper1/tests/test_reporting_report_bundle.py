"""Report bundle tests (Phase 17): freeze-gated, frozen-only loading."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from paper1.reporting.report_bundle import (
    generate_primary_report_bundle,
    load_frozen_primary_results,
)


def test_load_requires_freeze_manifest(tmp_path):
    # A metrics dir with no FREEZE_MANIFEST.json must be refused.
    root = tmp_path / "unfrozen"
    (root / "metrics").mkdir(parents=True)
    pd.DataFrame({"seed": [1], "strategy": ["x"], "metric": ["m"], "value": [1.0]}).to_csv(
        root / "metrics" / "per_seed_metrics.csv", index=False
    )
    with pytest.raises(RuntimeError):
        load_frozen_primary_results(root)


def test_load_fails_when_freeze_does_not_verify(tiny_frozen_dir):
    # Mutate a frozen file so verification fails; loading must refuse.
    (tiny_frozen_dir / "summary.md").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        load_frozen_primary_results(tiny_frozen_dir)


def test_generate_bundle_writes_all_outputs(tiny_frozen_dir, tmp_path):
    report_dir = tmp_path / "report"
    paper_dir = tmp_path / "paper"
    manifest = generate_primary_report_bundle(
        tiny_frozen_dir, report_dir=report_dir, paper_dir=paper_dir, capacity=10
    )
    # report manifest + summary written
    assert (report_dir / "report_manifest.json").exists()
    assert (report_dir / "summary.md").exists()
    # tables + figures present in report tree
    assert (report_dir / "tables").is_dir()
    assert (report_dir / "figures").is_dir()
    assert len(manifest["table_files"]) == 7
    assert len(manifest["figure_files"]) == 5
    # mirrored into paper/ tree
    assert (paper_dir / "tables").is_dir()
    assert (paper_dir / "figures").is_dir()
    assert (paper_dir / "report" / "summary.md").exists()


def test_report_manifest_lists_existing_files(tiny_frozen_dir, tmp_path):
    report_dir = tmp_path / "report"
    generate_primary_report_bundle(
        tiny_frozen_dir, report_dir=report_dir, paper_dir=tmp_path / "paper", capacity=10
    )
    disk = json.loads((report_dir / "report_manifest.json").read_text(encoding="utf-8"))
    assert disk["row_counts"]["seeds"] == 3
    assert disk["row_counts"]["strategies"] == 4
    assert disk["row_counts"]["metric_rows"] == 132
    assert len(disk["freeze_manifest_sha"]) == 64
    # Every referenced table/figure file must actually exist.
    for entry in disk["table_files"].values():
        for path in entry.values():
            assert Path(path).exists()
    for paths in disk["figure_files"].values():
        for path in paths:
            assert Path(path).exists()


def test_bundle_reads_only_frozen_metric_frames(tmp_path):
    # Build a frozen output that has NO raw seed/strategy directories at all;
    # the bundle must still succeed, proving it reads only the metric frames.
    from tests.conftest import build_tiny_frozen_output

    root = build_tiny_frozen_output(tmp_path / "frozen_nostrat", seeds=(1, 2), capacity=10)
    assert not list(root.glob("seed_*"))  # no raw strategy files exist
    manifest = generate_primary_report_bundle(
        root, report_dir=tmp_path / "rep", paper_dir=tmp_path / "pap", capacity=10
    )
    assert manifest["row_counts"]["seeds"] == 2
    assert len(manifest["table_files"]) == 7


def test_report_dir_excluded_from_freeze(tiny_frozen_dir):
    # Writing the report inside the frozen dir must not break re-verification,
    # because the derived report/ subtree is excluded from the freeze set.
    from paper1.experiments.inspect import verify_freeze_manifest

    assert verify_freeze_manifest(tiny_frozen_dir) is True
    generate_primary_report_bundle(
        tiny_frozen_dir,
        report_dir=tiny_frozen_dir / "report",
        paper_dir=tiny_frozen_dir.parent / "paper_out",
        capacity=10,
    )
    assert (tiny_frozen_dir / "report").is_dir()
    assert verify_freeze_manifest(tiny_frozen_dir) is True
