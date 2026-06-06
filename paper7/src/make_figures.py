"""Generate Paper 7 figures from online_calib_results.csv."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_v1"
FIGURES = ROOT / "submission" / "ieee" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(RESULTS / "online_calib_results.csv")
    Ks = [50, 100, 200]
    strategies = ["fixed", "online", "offline"]
    colors = {"fixed": "#666666", "online": "#1b9e77", "offline": "#d95f02"}

    # Trajectory figure: 1x3 grid, one per K
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.6), sharey=True)
    for ax, K in zip(axes, Ks):
        for strat in strategies:
            cell = df[(df.cell_K == K) & (df.strategy == strat)]
            mean_per_w = cell.groupby("window")["p_at_50"].mean()
            ax.plot(mean_per_w.index, mean_per_w.values, marker="o",
                    color=colors[strat], label=strat, linewidth=1.6, markersize=4)
        ax.set_title(f"$K={K}$", fontsize=10)
        ax.set_xlabel("Window")
        ax.set_xticks(range(1, 7))
        ax.set_ylim(0, 0.85)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Mean P@50")
    axes[0].legend(loc="lower left", fontsize=8, frameon=True)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig1_strategy_trajectories.pdf", bbox_inches="tight")
    plt.close()

    # Recovery-ratio bar chart per (K, window)
    means = df.groupby(["cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy")
    means["delta_on_fix"] = means["online"] - means["fixed"]
    means["delta_off_fix"] = means["offline"] - means["fixed"]

    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    xpos = []
    bar_lab = []
    on_vals = []
    off_vals = []
    for K in Ks:
        for w in range(2, 7):
            xpos.append(f"K{K}\nW{w}")
            on_vals.append(means.loc[(K, w), "delta_on_fix"])
            off_vals.append(means.loc[(K, w), "delta_off_fix"])
    x = list(range(len(xpos)))
    w = 0.4
    ax.bar([i - w/2 for i in x], on_vals, width=w, color="#1b9e77", label="online $-$ fixed")
    ax.bar([i + w/2 for i in x], off_vals, width=w, color="#d95f02", label="offline $-$ fixed")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(xpos, fontsize=7)
    ax.set_ylabel(r"$\Delta$ P@50 vs fixed")
    ax.legend(loc="upper right", fontsize=8, frameon=True)
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_gain_bars.pdf", bbox_inches="tight")
    plt.close()
    print(f"Wrote 2 figures to {FIGURES}")


if __name__ == "__main__":
    main()
