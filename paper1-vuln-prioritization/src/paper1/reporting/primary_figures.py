"""Paper-ready figures from frozen primary outputs (Phase 17).

matplotlib only (no seaborn), Agg backend for headless determinism, default
colours, neutral descriptive titles (no paper claims). Each chart is a
separate figure saved as both PNG and PDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

__all__ = [
    "fig_ehd_by_strategy",
    "fig_ehd_distribution_selected",
    "fig_fraction_of_oracle",
    "fig_proposed_vs_epss_by_seed",
    "fig_relative_to_epss",
    "generate_all_figures",
]

_SELECTED = ["random", "epss_only", "proposed_full", "oracle"]


def _save(fig: plt.Figure, directory: Path, name: str) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    png = directory / f"{name}.png"
    pdf = directory / f"{name}.pdf"
    fig.savefig(png, dpi=150, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return [str(png), str(pdf)]


def _ehd_rows(aggregated: pd.DataFrame) -> pd.DataFrame:
    rows = aggregated[aggregated["metric"] == "ehd_absolute"].copy()
    return rows.sort_values("mean").reset_index(drop=True)


def fig_ehd_by_strategy(aggregated: pd.DataFrame, directory: Path) -> list[str]:
    rows = _ehd_rows(aggregated)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(rows))
    ax.bar(x, rows["mean"], yerr=rows["std"].fillna(0.0), capsize=3)
    ax.set_xticks(list(x))
    ax.set_xticklabels(rows["strategy"], rotation=90)
    ax.set_ylabel("Mean absolute EHD (simulated host-days)")
    ax.set_title("Mean absolute EHD by strategy (lower = fewer exploited-host-days)")
    return _save(fig, directory, "fig_ehd_by_strategy")


def fig_fraction_of_oracle(eehda: pd.DataFrame, directory: Path) -> list[str]:
    rows = eehda.sort_values("fraction_of_oracle").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(rows))
    ax.bar(x, rows["fraction_of_oracle"])
    ax.set_xticks(list(x))
    ax.set_xticklabels(rows["strategy"], rotation=90)
    ax.set_ylabel("Fraction of oracle (EEHDA)")
    ax.set_title("EEHDA fraction-of-oracle by strategy (observed values)")
    return _save(fig, directory, "fig_fraction_of_oracle")


def fig_relative_to_epss(eehda: pd.DataFrame, directory: Path) -> list[str]:
    rows = eehda.sort_values("relative_to_epss").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(rows))
    ax.bar(x, rows["relative_to_epss"])
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(rows["strategy"], rotation=90)
    ax.set_ylabel("Relative EHD reduction vs epss_only")
    ax.set_title("EEHDA relative-to-epss_only by strategy (zero = parity)")
    return _save(fig, directory, "fig_relative_to_epss")


def fig_ehd_distribution_selected(per_seed: pd.DataFrame, directory: Path) -> list[str]:
    ehd = per_seed[per_seed["metric"] == "ehd_absolute"]
    present = [s for s in _SELECTED if s in set(ehd["strategy"])]
    data = [
        pd.to_numeric(ehd[ehd["strategy"] == s]["value"], errors="coerce").dropna().to_numpy()
        for s in present
    ]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, tick_labels=present)
    ax.set_ylabel("Absolute EHD (simulated host-days)")
    ax.set_title("EHD distribution across seeds (selected strategies)")
    return _save(fig, directory, "fig_ehd_distribution_selected")


def fig_proposed_vs_epss_by_seed(per_seed: pd.DataFrame, directory: Path) -> list[str]:
    ehd = per_seed[per_seed["metric"] == "ehd_absolute"]
    pf = ehd[ehd["strategy"] == "proposed_full"].set_index("seed")["value"]
    ep = ehd[ehd["strategy"] == "epss_only"].set_index("seed")["value"]
    joined = pd.concat({"proposed_full": pf, "epss_only": ep}, axis=1).dropna()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(joined["epss_only"], joined["proposed_full"])
    lo = float(min(joined.min().min(), 0))
    hi = float(joined.max().max())
    ax.plot([lo, hi], [lo, hi], linewidth=1.0)  # y = x reference
    ax.set_xlabel("epss_only EHD (per seed)")
    ax.set_ylabel("proposed_full EHD (per seed)")
    ax.set_title("Per-seed EHD: proposed_full vs epss_only (y=x reference)")
    return _save(fig, directory, "fig_proposed_vs_epss_by_seed")


def generate_all_figures(
    frozen: dict[str, Any],
    figures_dir: str | Path,
) -> dict[str, list[str]]:
    """Build and write all paper figures; return {figure_name: [png, pdf]}."""
    directory = Path(figures_dir)
    agg = frozen["aggregated_metrics"]
    eehda = frozen["eehda_report"]
    per_seed = frozen["per_seed_metrics"]
    return {
        "fig_ehd_by_strategy": fig_ehd_by_strategy(agg, directory),
        "fig_fraction_of_oracle": fig_fraction_of_oracle(eehda, directory),
        "fig_relative_to_epss": fig_relative_to_epss(eehda, directory),
        "fig_ehd_distribution_selected": fig_ehd_distribution_selected(per_seed, directory),
        "fig_proposed_vs_epss_by_seed": fig_proposed_vs_epss_by_seed(per_seed, directory),
    }
