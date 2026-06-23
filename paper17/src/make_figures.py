#!/usr/bin/env python3
"""Figures for Paper 17, from frozen results. Clean publication styling."""

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
CONFIGS = ["big-bang", "2-ring", "4-ring", "6-ring"]
DETECT = [0.2, 0.5, 0.8, 0.95]

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


def fig1_config(df):
    cfg = df[df.axis == "config"]
    blast = [cfg[cfg.config == c]["expected_blast"].mean() for c in CONFIGS]
    cost = [int(cfg[cfg.config == c]["convergence_cost"].iloc[0]) for c in CONFIGS]
    colors = [RED, AMBER, TEAL, INDIGO]
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    ax.bar(CONFIGS, blast, color=colors, width=0.6)
    ax.set_yscale("log")
    ax.set_ylabel("Expected blast radius (fraction of fleet, log)")
    ax.set_title("Finer staging cuts blast radius (cost: soak periods)")
    for i, (b, c) in enumerate(zip(blast, cost)):
        ax.text(i, b * 1.35, f"{b:.3f}", ha="center", fontsize=9, color="#334155")
        ax.text(i, min(blast) * 0.55, f"+{c} soak", ha="center", fontsize=8.5, color="#64748b")
    ax.set_ylim(min(blast) * 0.35, 2.0)
    _save(fig, "fig1_config")


def fig2_detect(df):
    det = df[df.axis == "detect"]
    means, lo, hi = [], [], []
    for p in DETECT:
        v = det[det.p_detect == p]["expected_blast"]
        m, l, h = bca_ci_mean(list(v), n_boot=5000, seed=int(p * 100))
        means.append(m); lo.append(max(0, m - l)); hi.append(max(0, h - m))
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    ax.errorbar(DETECT, means, yerr=[lo, hi], marker="o", color=TEAL, capsize=4,
                linewidth=2, markersize=7)
    ax.axhline(1.0, color=RED, linestyle="--", linewidth=1.2, label="Big-bang blast radius")
    ax.set_xlabel("Canary detection probability per ring")
    ax.set_ylabel("Expected blast radius (four-ring)")
    ax.set_title("Containment depends on canary observability")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", framealpha=0.9)
    _save(fig, "fig2_detect")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_config(df)
    fig2_detect(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
