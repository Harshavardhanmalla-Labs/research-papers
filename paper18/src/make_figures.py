#!/usr/bin/env python3
"""Figures for Paper 18, from frozen results. Clean publication styling."""

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
INTERVALS = [365, 180, 90, 30]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 11,
    "axes.labelsize": 10, "legend.fontsize": 8.5, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "figure.dpi": 150, "savefig.dpi": 200, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
})
TEAL, INDIGO, GREY, AMBER, RED = "#0d9488", "#4f46e5", "#94a3b8", "#d97706", "#dc2626"


def _save(fig, name):
    fig.savefig(FIGDIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.06)
    fig.savefig(FIGDIR / f"{name}.png", bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def _ci(v, seed=0):
    m, lo, hi = bca_ci_mean(list(v), n_boot=5000, seed=seed)
    return m, max(0, m - lo), max(0, hi - m)


def fig1_confidence(df):
    ref = df[df.axis == "reference"]
    a_drill = 1.0
    a_annual, ela, eha = _ci(ref["rec_random_annual"], seed=1)
    a_chaos, elc, ehc = _ci(ref["rec_random_chaos"], seed=2)
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    labels = ["At annual drill\n(what teams see)", "At random disaster\n(annual drills)",
              "At random disaster\n(continuous chaos)"]
    vals = [a_drill, a_annual, a_chaos]
    errs = [[0, ela, elc], [0, eha, ehc]]
    colors = [GREY, RED, TEAL]
    ax.bar(labels, vals, color=colors, width=0.6, yerr=errs, capsize=4,
           error_kw={"elinewidth": 1, "alpha": 0.7})
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=9, color="#334155")
    ax.annotate("", xy=(1, a_annual), xytext=(0, a_drill),
                arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.2))
    ax.text(0.5, (a_drill + a_annual) / 2 + 0.02, "drill illusion\n0.31", ha="center",
            fontsize=8.5, color=RED, style="italic")
    ax.set_ylabel("Recovery success probability")
    ax.set_ylim(0, 1.08)
    ax.set_title("A passing drill overstates real recovery confidence")
    _save(fig, "fig1_confidence")


def fig2_illusion(df):
    di = df[df.axis == "drill_interval"]
    means, lo, hi = [], [], []
    for i in INTERVALS:
        m, el, eh = _ci(di[di.interval == i]["illusion"], seed=i)
        means.append(m); lo.append(el); hi.append(eh)
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    ax.errorbar(INTERVALS, means, yerr=[lo, hi], marker="o", color=RED, capsize=4,
                linewidth=2, markersize=7)
    ax.set_xlabel("Drill interval (days)")
    ax.set_ylabel("Drill illusion (at-drill minus at-random)")
    ax.set_title("The illusion grows with the drill interval")
    ax.set_xticks(INTERVALS)
    ax.set_ylim(0, 0.36)
    _save(fig, "fig2_illusion")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_confidence(df)
    fig2_illusion(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
