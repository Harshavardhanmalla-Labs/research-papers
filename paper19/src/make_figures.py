#!/usr/bin/env python3
"""Figures for Paper 19, from frozen results. Clean publication styling."""

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
RETIRE = [7, 14, 30, 60, 120]

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


def fig1_regime(df):
    reg = df[df.axis == "regime"]
    names = ["periodic", "continuous"]
    ghost = [reg[reg.regime == n]["ghost_rate"].mean() for n in names]
    phantom = [reg[reg.regime == n]["phantom_rate"].mean() for n in names]
    labels = ["Quarterly\nreconciliation", "Continuous\nself-healing"]
    fig, ax = plt.subplots(figsize=(5.2, 3.4), constrained_layout=True)
    ax.bar(labels, ghost, color=RED, width=0.55, label="Ghost (security)")
    ax.bar(labels, phantom, bottom=ghost, color=AMBER, width=0.55, label="Phantom (cost)")
    for i, (g, p) in enumerate(zip(ghost, phantom)):
        ax.text(i, g + p + 0.012, f"{g + p:.2f}", ha="center", fontsize=9, color="#334155")
    ax.set_ylabel("CMDB error rate (fraction of fleet)")
    ax.set_title("Self-healing cuts total CMDB error 78%")
    ax.legend(loc="upper right", framealpha=0.9)
    _save(fig, "fig1_regime")


def fig2_tradeoff(df):
    ret = df[df.axis == "retire"]
    ghost = [ret[ret.retire == r]["ghost_rate"].mean() for r in RETIRE]
    phantom = [ret[ret.retire == r]["phantom_rate"].mean() for r in RETIRE]
    total = [ret[ret.retire == r]["total_error"].mean() for r in RETIRE]
    fig, ax = plt.subplots(figsize=(5.8, 3.4), constrained_layout=True)
    ax.plot(RETIRE, ghost, marker="o", color=RED, linewidth=1.8, markersize=6, label="Ghost (security)")
    ax.plot(RETIRE, phantom, marker="s", color=AMBER, linewidth=1.8, markersize=6, label="Phantom (cost)")
    ax.plot(RETIRE, total, marker="D", color=TEAL, linewidth=2.2, markersize=6, label="Total error")
    amin = int(np.argmin(total))
    ax.scatter([RETIRE[amin]], [total[amin]], s=120, facecolors="none",
               edgecolors=TEAL, linewidths=2, zorder=5)
    ax.annotate("balanced optimum", xy=(RETIRE[amin], total[amin]),
                xytext=(RETIRE[amin] + 18, total[amin] + 0.06), fontsize=8.5, color=TEAL,
                arrowprops=dict(arrowstyle="->", color=TEAL, lw=1))
    ax.set_xlabel("Retirement threshold (days unseen)")
    ax.set_ylabel("Error rate (fraction of fleet)")
    ax.set_title("Retirement aggressiveness trades ghosts for phantoms")
    ax.set_xticks(RETIRE)
    ax.legend(loc="upper left", framealpha=0.9)
    _save(fig, "fig2_tradeoff")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_regime(df)
    fig2_tradeoff(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
