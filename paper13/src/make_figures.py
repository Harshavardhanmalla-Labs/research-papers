#!/usr/bin/env python3
"""Figures for Paper 13, from frozen results. Clean publication styling."""

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
GRID = [0.0, 1.0, 3.0, 6.0, 12.0]

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


def fig1_reduction_vs_recurrence(df):
    red, rlo, rhi, share = [], [], [], []
    for r in GRID:
        sub = df[df.recurrence == r]
        m, el, eh = _ci(sub["reduction"] * 100, seed=int(r))
        red.append(m); rlo.append(el); rhi.append(eh)
        share.append(sub["blockable_share"].mean() * 100)
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    ax.plot(GRID, share, marker="s", color=GREY, linestyle="--", markersize=6,
            linewidth=1.4, label="Blockable-share ceiling")
    ax.errorbar(GRID, red, yerr=[rlo, rhi], marker="o", color=TEAL, capsize=4,
                linewidth=2, markersize=7, label="Exposure reduction")
    ax.axhline(50, color=AMBER, linestyle=":", linewidth=1, label="H1 threshold (50%)")
    ax.set_xlabel("Violation recurrence rate (per endpoint per year)")
    ax.set_ylabel("Exposure reduction vs detection (%)")
    ax.set_title("Prevention's advantage grows with recurrence")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", framealpha=0.9)
    _save(fig, "fig1_reduction_vs_recurrence")


def fig2_benefit_cost(df):
    saved, fb = [], []
    for r in GRID:
        sub = df[df.recurrence == r]
        saved.append(sub["exposure_saved"].mean())
        fb.append(sub["false_blocks_per_endpoint_month"].mean())
    fig, ax1 = plt.subplots(figsize=(5.8, 3.4), constrained_layout=True)
    l1 = ax1.plot(GRID, saved, marker="o", color=TEAL, linewidth=2, markersize=7,
                  label="Security benefit (control-days saved)")
    ax1.set_xlabel("Violation recurrence rate (per endpoint per year)")
    ax1.set_ylabel("Control-days saved (per fleet-year)", color=TEAL)
    ax1.tick_params(axis="y", labelcolor=TEAL)
    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    l2 = ax2.plot(GRID, fb, marker="s", color=AMBER, linewidth=2, markersize=6,
                  linestyle="--", label="Operational cost (false blocks)")
    ax2.set_ylabel("False blocks per endpoint-month", color=AMBER)
    ax2.tick_params(axis="y", labelcolor=AMBER)
    ax2.set_ylim(0, max(fb) * 2.2)
    ax2.grid(False)
    ax1.set_title("Benefit grows with recurrence; cost stays fixed")
    lns = l1 + l2
    ax1.legend(lns, [x.get_label() for x in lns], loc="upper left", framealpha=0.9)
    _save(fig, "fig2_benefit_cost")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_reduction_vs_recurrence(df)
    fig2_benefit_cost(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
