"""Paper-table generation tests (Phase 17)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from paper1.reporting.primary_tables import (
    build_ehd_primary,
    build_strategy_comparison_vs_epss,
    generate_all_tables,
)
from paper1.reporting.report_bundle import load_frozen_primary_results


def _frozen(tiny_frozen_dir: Path) -> dict:
    return load_frozen_primary_results(tiny_frozen_dir)


def test_generate_all_tables_writes_csv_md_tex(tiny_frozen_dir, tmp_path):
    frozen = _frozen(tiny_frozen_dir)
    out = tmp_path / "tables"
    written = generate_all_tables(frozen, out, capacity=10)
    expected = {
        "table_primary_metric_summary",
        "table_ehd_primary",
        "table_strategy_comparison_vs_epss",
        "table_ranking_metrics",
        "table_operational_metrics",
        "table_audit_metrics",
        "table_acceptance_checks",
    }
    assert set(written) == expected
    for name, paths in written.items():
        for fmt in ("csv", "md", "tex"):
            p = Path(paths[fmt])
            assert p.exists() and p.stat().st_size > 0, f"{name}.{fmt} missing/empty"


def test_metric_summary_columns(tiny_frozen_dir, tmp_path):
    frozen = _frozen(tiny_frozen_dir)
    written = generate_all_tables(frozen, tmp_path / "t", capacity=10)
    df = pd.read_csv(written["table_primary_metric_summary"]["csv"])
    assert list(df.columns) == ["strategy", "metric", "mean", "std", "count"]


def test_ehd_primary_columns_and_order(tiny_frozen_dir):
    frozen = _frozen(tiny_frozen_dir)
    df = build_ehd_primary(frozen["aggregated_metrics"], frozen["eehda_report"])
    assert {
        "strategy",
        "absolute_EHD_mean",
        "absolute_EHD_std",
        "relative_to_random_mean",
        "relative_to_epss_mean",
        "fraction_of_oracle_mean",
    } <= set(df.columns)
    # Sorted ascending by mean EHD (lower = better first) -> oracle first.
    assert df.iloc[0]["strategy"] == "oracle"
    assert df["absolute_EHD_mean"].is_monotonic_increasing


def test_strategy_comparison_respects_lower_is_better(tiny_frozen_dir):
    frozen = _frozen(tiny_frozen_dir)
    df = build_strategy_comparison_vs_epss(frozen["aggregated_metrics"]).set_index("strategy")
    # oracle is excluded from this table.
    assert "oracle" not in df.index
    # proposed_full has LOWER EHD than epss_only -> better, negative delta.
    pf = df.loc["proposed_full"]
    assert pf["delta_vs_epss"] < 0
    assert pf["interpretation_direction"].startswith("better")
    # random has HIGHER EHD than epss_only here -> worse, positive delta.
    rnd = df.loc["random"]
    assert rnd["delta_vs_epss"] > 0
    assert rnd["interpretation_direction"].startswith("worse")
    # epss_only vs itself is ~equal.
    assert df.loc["epss_only"]["interpretation_direction"].startswith("approximately equal")


def test_acceptance_checks_report_integrity(tiny_frozen_dir, tmp_path):
    frozen = _frozen(tiny_frozen_dir)
    written = generate_all_tables(frozen, tmp_path / "t", capacity=10)
    df = pd.read_csv(written["table_acceptance_checks"]["csv"])
    kv = dict(zip(df["check"], df["value"].astype(str), strict=True))
    assert kv["seed_count"] == "3"
    assert kv["metric_rows"] == "132"  # 3 seeds * 4 strategies * 11 metrics
    assert kv["audit_logs_valid"] == "True"
    assert kv["freeze_verified"] == "True"
    assert kv["capacity"] == "10"


def test_latex_escapes_underscores(tiny_frozen_dir, tmp_path):
    frozen = _frozen(tiny_frozen_dir)
    written = generate_all_tables(frozen, tmp_path / "t", capacity=10)
    tex = Path(written["table_ehd_primary"]["tex"]).read_text(encoding="utf-8")
    assert "\\begin{tabular}" in tex
    # strategy names like 'epss_only' must be escaped for LaTeX.
    assert "epss\\_only" in tex
    assert "epss_only" not in tex.replace("epss\\_only", "")
