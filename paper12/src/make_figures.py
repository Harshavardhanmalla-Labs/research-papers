#!/usr/bin/env python3
"""Figures for Paper 12, from frozen results. Clean publication styling."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import bca_ci_mean  # noqa: E402

RESULTS = Path(__file__).parent.parent / "results" / "primary_v1"
FIGDIR = Path(__file__).parent.parent / "submission" / "ieee" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 11,
    "axes.labelsize": 10, "legend.fontsize": 8.5, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "figure.dpi": 150, "savefig.dpi": 200, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
})
TEAL, INDIGO, GREY, AMBER = "#0d9488", "#4f46e5", "#94a3b8", "#d97706"


def _save(fig, name):
    fig.savefig(FIGDIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.06)
    fig.savefig(FIGDIR / f"{name}.png", bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def _ci(v, seed=0):
    m, lo, hi = bca_ci_mean(list(v), n_boot=5000, seed=seed)
    return m, max(0, m - lo), max(0, hi - m)


def fig1_ceiling(df):
    """The automatability ceiling: realized reduction vs the automatable-share ceiling,
    with the non-automatable floor."""
    red, rl, rh = _ci(df["reduction_vs_annual"], seed=1)
    ceil, cl, ch = _ci(df["automatable_exposure_share"], seed=2)
    fig, ax = plt.subplots(figsize=(5.4, 3.4), constrained_layout=True)
    bars = ["Realized continuous\nreduction", "Automatable-share\nceiling"]
    vals = [red, ceil]; errs = [[rl, cl], [rh, ch]]
    ax.bar(bars, vals, color=[TEAL, INDIGO], width=0.55,
           yerr=errs, capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.axhline(1.0, color="#cbd5e1", linewidth=1)
    ax.text(1.0, ceil + 0.03, f"{ceil:.2f}", ha="center", fontsize=9, color="#334155")
    ax.text(0.0, red + 0.03, f"{red:.2f}", ha="center", fontsize=9, color="#334155")
    ax.set_ylabel("Fraction of annual exposure removed")
    ax.set_ylim(0, 1.0)
    ax.set_title("Exposure reduction is capped by automatability")
    # shade the non-automatable floor region
    ax.axhspan(ceil, 1.0, color=GREY, alpha=0.12)
    ax.text(0.5, (ceil + 1.0) / 2, "non-automatable floor", ha="center", va="center",
            fontsize=8.5, color="#64748b", style="italic")
    _save(fig, "fig1_ceiling")


def fig2_mttd_cadence(df):
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.2), constrained_layout=True)
    # (a) MTTD on automatable controls, log scale
    a = df["mttd_auto_annual"].mean(); c = df["mttd_auto_continuous"].mean()
    axes[0].bar(["Annual\nassessment", "Continuous\nas code"], [a, c], color=[GREY, TEAL], width=0.55)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Mean time to detect (days, log)")
    axes[0].set_title(f"Detection on automatable\ncontrols ({a/c:.0f}x faster)")
    for i, v in enumerate([a, c]):
        axes[0].text(i, v * 1.25, f"{v:.0f}d", ha="center", fontsize=9, color="#334155")
    # (b) absolute control-days saved: diminishing returns vs cadence
    sa, ela, eha = _ci(df["days_saved_vs_annual"], seed=3)
    sq, elq, ehq = _ci(df["days_saved_vs_quarter"], seed=4)
    axes[1].bar(["over annual", "over quarterly"], [sa, sq], color=[INDIGO, AMBER], width=0.55,
                yerr=[[ela, elq], [eha, ehq]], capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    axes[1].set_ylabel("Control-days saved (per fleet, 2 yr)")
    axes[1].set_title("Diminishing returns as the\nmanual cadence tightens")
    _save(fig, "fig2_mttd_cadence")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_ceiling(df)
    fig2_mttd_cadence(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
