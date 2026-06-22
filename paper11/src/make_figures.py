#!/usr/bin/env python3
"""
Generate Paper 11 figures from frozen results. Clean publication styling:
constrained layout, no overlapping text, descriptive self-contained captions.

Outputs PDF + PNG to submission/ieee/figures/. Reads only the frozen CSV/JSON in
results/primary_v1/; no re-simulation.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from capg.metrics import bca_ci_mean  # noqa: E402

RESULTS = Path(__file__).parent.parent / "results" / "primary_v1"
FIGDIR = Path(__file__).parent.parent / "submission" / "ieee" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)
K_VALUES = [50, 100, 250]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "legend.fontsize": 8.5, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "figure.dpi": 150, "savefig.dpi": 200,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
})
TEAL, INDIGO, GREY, AMBER = "#0d9488", "#4f46e5", "#94a3b8", "#d97706"


def _save(fig, name):
    fig.savefig(FIGDIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.06)
    fig.savefig(FIGDIR / f"{name}.png", bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def _ci(series, seed=0):
    m, lo, hi = bca_ci_mean(list(series), n_boot=5000, seed=seed)
    return m, max(0.0, m - lo), max(0.0, hi - m)


def fig1_mwp_by_k(df):
    methods = [("CAP-G", "CAP-G-full", TEAL),
               ("Hygiene-augmented", "HygienePrio", INDIGO),
               ("EPSS only", "EPSS-only", GREY)]
    x = np.arange(len(K_VALUES)); w = 0.25
    fig, ax = plt.subplots(figsize=(5.4, 3.3), constrained_layout=True)
    for i, (label, key, color) in enumerate(methods):
        means, lo, hi = [], [], []
        for k in K_VALUES:
            m, el, eh = _ci(df[df.method == key][f"mwp_at_{k}"], seed=k)
            means.append(m); lo.append(el); hi.append(eh)
        ax.bar(x + (i - 1) * w, means, w, label=label, color=color,
               yerr=[lo, hi], capsize=3, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.set_xticks(x); ax.set_xticklabels([f"K = {k}" for k in K_VALUES])
    ax.set_ylabel("Mission-weighted precision (MWP@K)")
    ax.set_xlabel("Remediation capacity per window")
    ax.set_ylim(0, 0.42)
    ax.set_title("Mission precision under remediation capacity")
    ax.legend(loc="upper right", framealpha=0.9)
    _save(fig, "fig1_mwp_by_k")


def fig2_advantage_decay(df, df_hom):
    fig, ax = plt.subplots(figsize=(5.4, 3.3), constrained_layout=True)
    het, lo, hi, hom = [], [], [], []
    for k in K_VALUES:
        a = df[df.method == "CAP-G-full"].set_index("seed")[f"mwp_at_{k}"]
        b = df[df.method == "HygienePrio"].set_index("seed")[f"mwp_at_{k}"]
        idx = a.index.intersection(b.index)
        m, el, eh = _ci((a.loc[idx] - b.loc[idx]) * 100, seed=k)
        het.append(m); lo.append(el); hi.append(eh)
        ha = df_hom[df_hom.method == "CAP-G-full"].set_index("seed")[f"mwp_at_{k}"]
        hb = df_hom[df_hom.method == "HygienePrio"].set_index("seed")[f"mwp_at_{k}"]
        hidx = ha.index.intersection(hb.index)
        hom.append(float((ha.loc[hidx] - hb.loc[hidx]).mean()) * 100)
    ax.axhline(0, color="#cbd5e1", linewidth=1, zorder=0)
    ax.errorbar(K_VALUES, het, yerr=[lo, hi], marker="o", color=TEAL, capsize=4,
                linewidth=2, markersize=7, label="Heterogeneous fleet", zorder=3)
    ax.plot(K_VALUES, hom, marker="s", color=GREY, linestyle="--", markersize=6,
            linewidth=1.6, label="Homogeneous control", zorder=2)
    ax.set_xticks(K_VALUES); ax.set_xlim(35, 265)
    ax.set_xlabel("Remediation capacity per window")
    ax.set_ylabel("MWP advantage over baseline (points)")
    ax.set_title("Context advantage concentrates at scarce capacity")
    ax.legend(loc="upper right", framealpha=0.9)
    _save(fig, "fig2_advantage_decay")


def fig3_ablation(summary):
    dims = [("Asset\ncriticality", "criticality"), ("Network\nzone", "zone"),
            ("Data\nsensitivity", "sensitivity")]
    abl = summary["ablation"]
    vals, lo, hi = [], [], []
    for _, key in dims:
        d = abl[key]["mwp50_drop_when_removed"]
        vals.append(-d["mean"] * 100)            # change when removed
        lo.append(abs((-d["mean"] + d["ci_hi"]) * 100))
        hi.append(abs((d["ci_lo"] - d["mean"]) * -100))
    colors = [TEAL if v < 0 else GREY for v in vals]
    fig, ax = plt.subplots(figsize=(5.0, 3.3), constrained_layout=True)
    ax.axhline(0, color="#94a3b8", linewidth=1, zorder=0)
    ax.bar([d[0] for d in dims], vals, color=colors, width=0.6,
           yerr=[lo, hi], capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.set_ylabel("Change in MWP@50 when removed (points)")
    ax.set_title("Asset criticality is the load-bearing dimension")
    _save(fig, "fig3_ablation")


def fig4_ndcg(df):
    methods = [("CAP-G", "CAP-G-full", TEAL),
               ("Hygiene-augmented", "HygienePrio", INDIGO),
               ("EPSS only", "EPSS-only", GREY)]
    fig, ax = plt.subplots(figsize=(5.0, 3.3), constrained_layout=True)
    labels, means, lo, hi, colors = [], [], [], [], []
    for label, key, color in methods:
        m, el, eh = _ci(df[df.method == key]["ndcg_at_50"], seed=7)
        labels.append(label); means.append(m); lo.append(el); hi.append(eh); colors.append(color)
    ax.bar(labels, means, color=colors, width=0.6,
           yerr=[lo, hi], capsize=4, error_kw={"elinewidth": 1, "alpha": 0.7})
    ax.set_ylabel("NDCG@50 (rank-weighted mission precision)")
    ax.set_ylim(0, 0.72)
    ax.set_title("Rank quality at triage capacity")
    for i, m in enumerate(means):
        ax.text(i, m + 0.02, f"{m:.2f}", ha="center", fontsize=9, color="#334155")
    _save(fig, "fig4_ndcg")


def main():
    df = pd.read_csv(RESULTS / "primary_results.csv")
    df_hom = pd.read_csv(RESULTS / "homogeneous_control.csv")
    summary = json.load(open(RESULTS / "hypothesis_summary.json"))
    fig1_mwp_by_k(df)
    fig2_advantage_decay(df, df_hom)
    fig3_ablation(summary)
    fig4_ndcg(df)
    print("wrote figures:", sorted(p.name for p in FIGDIR.glob("*.pdf")))


if __name__ == "__main__":
    main()
