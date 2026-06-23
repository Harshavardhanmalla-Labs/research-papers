#!/usr/bin/env python3
"""Figures for Paper 16, from frozen results. Clean publication styling."""

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
TEAL, INDIGO, GREY, AMBER, RED, GREEN = "#0d9488", "#4f46e5", "#94a3b8", "#d97706", "#dc2626", "#16a34a"


def _save(fig, name):
    fig.savefig(FIGDIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.06)
    fig.savefig(FIGDIR / f"{name}.png", bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def _ci(v, seed=0):
    m, lo, hi = bca_ci_mean(list(v), n_boot=5000, seed=seed)
    return m, max(0, m - lo), max(0, hi - m)


def fig1_crossover(df):
    """Rules vs best joint across SDA / CDA / Mixed: the crossover story."""
    conds = ["SDA", "CDA", "Mixed"]
    series = [("Rule-Max (per-feature)", "Rule-Max", GREY),
              ("Mahalanobis (joint)", "Mahalanobis", TEAL)]
    x = np.arange(len(conds)); w = 0.34
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    for i, (lab, det, c) in enumerate(series):
        means, lo, hi = [], [], []
        for cond in conds:
            m, el, eh = _ci(df[(df.condition == cond) & (df.detector == det)]["ap"], seed=hash(det) % 97)
            means.append(m); lo.append(el); hi.append(eh)
        ax.bar(x + (i - 0.5) * w, means, w, label=lab, color=c,
               yerr=[lo, hi], capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.set_xticks(x); ax.set_xticklabels(["Single-channel\nanomaly", "Cross-channel\nanomaly", "Mixture"])
    ax.set_ylabel("Average precision")
    ax.set_ylim(0, 0.95)
    ax.set_title("Rules win the obvious case, joint detection wins the subtle one")
    ax.legend(loc="upper right", framealpha=0.9)
    _save(fig, "fig1_crossover")


def fig2_detectors_cda(df):
    """All detectors on CDA: covariance/density-aware win, axis-aligned and rules fail."""
    order = [("Mahalanobis", TEAL), ("LocalOutlierFactor", GREEN), ("OneClassSVM", AMBER),
             ("IsolationForest", RED), ("Rule-Max", GREY), ("Rule-Count", GREY)]
    labels, means, lo, hi, colors = [], [], [], [], []
    for det, c in order:
        m, el, eh = _ci(df[(df.condition == "CDA") & (df.detector == det)]["ap"], seed=hash(det) % 89)
        labels.append(det); means.append(m); lo.append(el); hi.append(eh); colors.append(c)
    fig, ax = plt.subplots(figsize=(6.0, 3.4), constrained_layout=True)
    ax.bar(range(len(labels)), means, color=colors, width=0.62,
           yerr=[lo, hi], capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Average precision (cross-channel anomaly)")
    ax.set_ylim(0, 0.85)
    ax.set_title("Only covariance- and density-aware detectors see the violation")
    _save(fig, "fig2_detectors_cda")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_crossover(df)
    fig2_detectors_cda(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
