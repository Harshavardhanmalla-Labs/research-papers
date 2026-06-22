#!/usr/bin/env python3
"""
Figures for Patch Tuesday Triage (Paper 14), from frozen results. Clean publication
styling: constrained layout, no overlapping text. PDF + PNG to submission/ieee/figures/.
"""

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
SIGMA_GRID = [0.0, 0.25, 0.50, 0.75, 1.0]
REF_SIGMA = 0.50
K_VALUES = [50, 100, 250]

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


def fig1_methods(df):
    ref = df[df.sigma == REF_SIGMA]
    order = [("Context-weighted triage", "PTI-full", TEAL),
             ("Severity + KEV only", "PTI-noObs", TEAL),
             ("Matured-EPSS oracle", "EPSS-matured-oracle", AMBER),
             ("Day-0 EPSS (blind)", "EPSS-day0", GREY),
             ("Context off", "PTI-noCrit", RED)]
    labels, means, lo, hi, colors = [], [], [], [], []
    for lab, key, c in order:
        m, el, eh = _ci(ref[ref.method == key]["mwp_at_50"], seed=hash(key) % 97)
        labels.append(lab); means.append(m); lo.append(el); hi.append(eh); colors.append(c)
    fig, ax = plt.subplots(figsize=(6.0, 3.4), constrained_layout=True)
    ax.bar(range(len(labels)), means, color=colors, width=0.62,
           yerr=[lo, hi], capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel("Mission-weighted precision (MWP@50)")
    ax.set_ylim(0, 0.36)
    ax.set_title("Disclosure-time triage at moderate signal noise")
    for i, m in enumerate(means):
        ax.text(i, m + 0.008, f"{m:.2f}", ha="center", fontsize=8.5, color="#334155")
    _save(fig, "fig1_methods")


def fig2_noise(df):
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    adv, lo, hi = [], [], []
    for s in SIGMA_GRID:
        sub = df[df.sigma == s]
        a = sub[sub.method == "PTI-full"].set_index("seed")["mwp_at_50"]
        b = sub[sub.method == "EPSS-day0"].set_index("seed")["mwp_at_50"]
        idx = a.index.intersection(b.index)
        m, el, eh = _ci((a.loc[idx] - b.loc[idx]) * 100, seed=int(s * 100))
        adv.append(m); lo.append(el); hi.append(eh)
    ax.axhline(0, color="#cbd5e1", linewidth=1, zorder=0)
    ax.errorbar(SIGMA_GRID, adv, yerr=[lo, hi], marker="o", color=TEAL,
                capsize=4, linewidth=2, markersize=7)
    ax.set_xlabel("Day-0 EPSS observation noise (sigma)")
    ax.set_ylabel("Context advantage over blind (points)")
    ax.set_ylim(0, max(adv) + 2)
    ax.set_title("Context advantage holds regardless of exploit-signal quality")
    _save(fig, "fig2_noise")


def fig3_capacity(df):
    ref = df[df.sigma == REF_SIGMA]
    fig, ax = plt.subplots(figsize=(5.6, 3.4), constrained_layout=True)
    for lab, key, c in [("Context-weighted triage", "PTI-full", TEAL),
                        ("Day-0 EPSS (blind)", "EPSS-day0", GREY)]:
        means, lo, hi = [], [], []
        for k in K_VALUES:
            m, el, eh = _ci(ref[ref.method == key][f"mwp_at_{k}"], seed=k)
            means.append(m); lo.append(el); hi.append(eh)
        ax.errorbar(K_VALUES, means, yerr=[lo, hi], marker="o", color=c, capsize=4,
                    linewidth=2, markersize=7, label=lab)
    ax.set_xticks(K_VALUES); ax.set_xlim(35, 265)
    ax.set_xlabel("Remediation capacity per window")
    ax.set_ylabel("Mission-weighted precision (MWP@K)")
    ax.set_title("Advantage is largest where capacity is scarce")
    ax.legend(loc="upper right", framealpha=0.9)
    _save(fig, "fig3_capacity")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    fig1_methods(df)
    fig2_noise(df)
    fig3_capacity(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
