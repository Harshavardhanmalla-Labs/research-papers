"""Generate Paper 9 figures from self_traj_results.csv."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_v1"
FIGURES = ROOT / "submission" / "ieee" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(RESULTS / "self_traj_results.csv")
    means = df.groupby(["cell_K", "driver", "scorer", "window"])["p_at_50"].mean().reset_index()

    drivers = ["HygienePrio-full", "EPSS-only", "HRS-only", "CVSS-only", "Random"]
    colors = {"HygienePrio-full": "#1b9e77", "EPSS-only": "#d95f02",
              "HRS-only": "#7570b3", "CVSS-only": "#e7298a", "Random": "#666666"}
    short = {"HygienePrio-full": "HP", "EPSS-only": "EPSS", "HRS-only": "HRS",
             "CVSS-only": "CVSS", "Random": "Rand"}

    # Figure 1: HP-scorer P@50 trajectories under each driver, per K
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8), sharey=True)
    for ax, K in zip(axes, (50, 200)):
        for drv in drivers:
            sub = means[(means.cell_K == K) & (means.scorer == "HygienePrio-full") & (means.driver == drv)]
            sub = sub.sort_values("window")
            ax.plot(sub["window"], sub["p_at_50"], marker="o",
                    color=colors[drv], label=f"T={short[drv]}", linewidth=1.6, markersize=4)
        ax.set_title(f"$K={K}$")
        ax.set_xlabel("Window")
        ax.set_xticks(range(1, 7))
        ax.set_ylim(0, 0.8)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("HP-full P@50")
    axes[1].legend(loc="lower left", fontsize=7, frameon=True, ncol=1)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig1_hp_under_drivers.pdf", bbox_inches="tight")
    plt.close()

    # Figure 2: K=200 W6 heatmap (rows scorer, cols driver)
    K200_w6 = means[(means.cell_K == 200) & (means.window == 6)].pivot(
        index="scorer", columns="driver", values="p_at_50")
    K200_w6 = K200_w6.reindex(drivers, axis=0).reindex(drivers, axis=1)
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    im = ax.imshow(K200_w6.values, cmap="viridis", vmin=0.0, vmax=0.75, aspect="auto")
    ax.set_xticks(range(len(drivers))); ax.set_xticklabels([short[d] for d in drivers], rotation=0)
    ax.set_yticks(range(len(drivers))); ax.set_yticklabels([short[d] for d in drivers])
    ax.set_xlabel("driver method")
    ax.set_ylabel("scorer method")
    for i, sc in enumerate(drivers):
        for j, dr in enumerate(drivers):
            v = K200_w6.iloc[i, j]
            ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                    color="white" if v < 0.35 else "black", fontsize=8)
    plt.colorbar(im, ax=ax, shrink=0.85, label="W6 mean P@50")
    plt.title("$K=200$, $w=6$: P@50 by scorer $\\times$ driver")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_w6_heatmap.pdf", bbox_inches="tight")
    plt.close()
    print(f"Wrote 2 figures to {FIGURES}")


if __name__ == "__main__":
    main()
