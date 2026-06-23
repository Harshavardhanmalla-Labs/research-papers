"""Generate Paper 6 figures from sweep_results.csv.

Figures produced:
  fig1_slope_heatmap.pdf — 5x4 heatmap of EPSS-only decay slope (K x lambda)
  fig2_w6_retention.pdf  — 5x4 heatmap of HygienePrio-full W6 P@50 (K x lambda)
  fig3_corner_traj.pdf   — P@50 trajectories at 4 corner cells (K, lambda extremes)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_sweep_v1"
FIGURES = ROOT / "submission" / "ieee" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    summary = pd.read_csv(RESULTS / "cell_summary.csv")
    sweep = pd.read_csv(RESULTS / "sweep_results.csv")

    Ks = sorted(summary.cell_K.unique())
    lams = sorted(summary.cell_lambda.unique())

    # ------------------------------------------------------------------
    # Figure 1: EPSS-only decay slope heatmap
    # ------------------------------------------------------------------
    ep = summary[summary.method == "EPSS-only"].pivot(
        index="cell_lambda", columns="cell_K", values="slope_mean")
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    im = ax.imshow(ep.values, cmap="RdBu", vmin=-0.06, vmax=0.06, aspect="auto")
    ax.set_xticks(range(len(Ks))); ax.set_xticklabels([str(k) for k in Ks])
    ax.set_yticks(range(len(lams))); ax.set_yticklabels([f"{int(l)}" for l in lams])
    ax.set_xlabel("Capacity $K$ (pairs/window)")
    ax.set_ylabel(r"Arrival rate $\lambda$")
    for i, lam in enumerate(lams):
        for j, K in enumerate(Ks):
            val = ep.loc[lam, K]
            ax.text(j, i, f"{val:+.3f}", ha="center", va="center",
                    color="white" if abs(val) > 0.03 else "black", fontsize=8)
    cb = plt.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("EPSS-only decay slope (P@50 / window)")
    plt.title("EPSS-only decay slope across $(K, \\lambda)$")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig1_slope_heatmap.pdf", bbox_inches="tight")
    plt.close()

    # ------------------------------------------------------------------
    # Figure 2: HygienePrio-full W6 retention heatmap
    # ------------------------------------------------------------------
    hp = summary[summary.method == "HygienePrio-full"].pivot(
        index="cell_lambda", columns="cell_K", values="w6_mean")
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    im = ax.imshow(hp.values, cmap="viridis", vmin=0.0, vmax=0.65, aspect="auto")
    ax.set_xticks(range(len(Ks))); ax.set_xticklabels([str(k) for k in Ks])
    ax.set_yticks(range(len(lams))); ax.set_yticklabels([f"{int(l)}" for l in lams])
    ax.set_xlabel("Capacity $K$ (pairs/window)")
    ax.set_ylabel(r"Arrival rate $\lambda$")
    for i, lam in enumerate(lams):
        for j, K in enumerate(Ks):
            val = hp.loc[lam, K]
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    color="white" if val < 0.35 else "black", fontsize=8)
    cb = plt.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("HygienePrio-full W6 mean P@50")
    plt.title("HygienePrio-full W6 retention across $(K, \\lambda)$")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_w6_retention.pdf", bbox_inches="tight")
    plt.close()

    # ------------------------------------------------------------------
    # Figure 3: Corner-cell trajectories
    # Cells: (K=10, lambda=12) replenish-dominated; (K=200, lambda=1) drain-dominated;
    #        (K=10, lambda=1) low-throughput; (K=200, lambda=12) high-throughput.
    # ------------------------------------------------------------------
    corners = [(10, 1.0), (10, 12.0), (200, 1.0), (200, 12.0)]
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.4), sharey=True, sharex=True)
    methods = ["HygienePrio-full", "EPSS-only", "HRS-only", "CVSS-only", "Random"]
    colors = {"HygienePrio-full": "#1b9e77", "EPSS-only": "#d95f02",
              "HRS-only": "#7570b3", "CVSS-only": "#e7298a", "Random": "#666666"}

    for ax, (K, lam) in zip(axes.flat, corners):
        for m in methods:
            cell = sweep[(sweep.cell_K == K) & (sweep.cell_lambda == lam) & (sweep.method == m)]
            mean_per_w = cell.groupby("window")["p_at_50"].mean()
            ax.plot(mean_per_w.index, mean_per_w.values, marker="o",
                    label=m, color=colors[m], linewidth=1.6, markersize=4)
        ax.set_title(f"$K={K}$, $\\lambda={int(lam)}$", fontsize=10)
        ax.set_ylim(0, 0.70)
        ax.set_xticks(range(1, 7))
        ax.grid(True, alpha=0.3)
    axes[1, 0].set_xlabel("Window")
    axes[1, 1].set_xlabel("Window")
    axes[0, 0].set_ylabel("Mean P@50")
    axes[1, 0].set_ylabel("Mean P@50")
    axes[0, 0].legend(loc="upper right", fontsize=7, frameon=True)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig3_corner_traj.pdf", bbox_inches="tight")
    plt.close()

    print(f"Wrote 3 figures to {FIGURES}")


if __name__ == "__main__":
    main()
