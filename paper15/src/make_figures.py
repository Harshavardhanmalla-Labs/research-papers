#!/usr/bin/env python3
"""Figures for Paper 15, from frozen results. Clean publication styling."""

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
GRID = [0.45, 0.50, 0.55, 0.60, 0.70]
REF = 0.50

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


def fig1_regimes(df):
    ref = df[df.overlap == REF]
    series = [("Real-time feed", "recall_realtime", GREY),
              ("Scheduled feed", "recall_scheduled", AMBER),
              ("Fusion", "recall_fusion", TEAL)]
    labels, means, lo, hi, colors = [], [], [], [], []
    for lab, col, c in series:
        m, el, eh = _ci(ref[col], seed=hash(col) % 97)
        labels.append(lab); means.append(m); lo.append(el); hi.append(eh); colors.append(c)
    union = ref["coverage_union"].mean()
    fig, ax = plt.subplots(figsize=(5.4, 3.4), constrained_layout=True)
    ax.bar(labels, means, color=colors, width=0.58,
           yerr=[lo, hi], capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.axhline(union, color=INDIGO, linestyle="--", linewidth=1.2,
               label=f"Coverage union ({union:.2f})")
    ax.axhspan(union, 1.0, color=GREY, alpha=0.12)
    ax.text(1.0, (union + 1.0) / 2, "blind-spot floor", ha="center", va="center",
            fontsize=8.5, color="#64748b", style="italic")
    for i, m in enumerate(means):
        ax.text(i, m + 0.02, f"{m:.2f}", ha="center", fontsize=9, color="#334155")
    ax.set_ylabel("Current-vulnerability detection recall")
    ax.set_ylim(0, 1.0)
    ax.set_title("Fusion recovers freshness and coverage at once")
    ax.legend(loc="lower left", framealpha=0.9)
    _save(fig, "fig1_regimes")


def fig2_overlap(df):
    gain, glo, ghi, blind = [], [], [], []
    for o in GRID:
        sub = df[df.overlap == o]
        m, el, eh = _ci(sub["gain_over_best_single"], seed=int(o * 100))
        gain.append(m); glo.append(el); ghi.append(eh)
        blind.append(sub["blind_spot"].mean())
    fig, ax1 = plt.subplots(figsize=(5.8, 3.4), constrained_layout=True)
    l1 = ax1.errorbar(GRID, gain, yerr=[glo, ghi], marker="o", color=TEAL, capsize=4,
                      linewidth=2, markersize=7, label="Fusion gain over best single tool")
    ax1.set_xlabel("Coverage overlap between the two tools (P[both])")
    ax1.set_ylabel("Fusion recall gain", color=TEAL)
    ax1.tick_params(axis="y", labelcolor=TEAL)
    ax1.set_ylim(0, 0.18)
    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    l2 = ax2.plot(GRID, blind, marker="s", color=RED, linestyle="--", markersize=6,
                  linewidth=1.8, label="Blind-spot rate")
    ax2.set_ylabel("Blind-spot rate", color=RED)
    ax2.tick_params(axis="y", labelcolor=RED)
    ax2.set_ylim(0, 0.30); ax2.grid(False)
    ax1.set_title("More overlap means less fusion gain and more blind spots")
    lns = [l1] + l2
    ax1.legend(lns, [x.get_label() for x in lns], loc="upper center", framealpha=0.9)
    _save(fig, "fig2_overlap")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_regimes(df)
    fig2_overlap(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
