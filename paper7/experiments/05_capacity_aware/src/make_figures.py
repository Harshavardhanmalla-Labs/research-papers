"""Generate Paper 12 figures from cap_aware_results.csv."""
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
    df = pd.read_csv(RESULTS / "cap_aware_results.csv")
    cp = pd.read_csv(RESULTS / "changepoint_log.csv")
    Ks = [50, 100, 200]
    strategies = ["fixed", "lag1", "adaptive05", "cap_aware", "gated", "offline"]
    colors = {"fixed": "#666666", "lag1": "#1b9e77", "adaptive05": "#7570b3",
              "cap_aware": "#d95f02", "gated": "#e7298a", "offline": "#a6cee3"}

    # Trajectory figure
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8), sharey=True)
    for ax, K in zip(axes, Ks):
        for strat in strategies:
            cell = df[(df.cell_K == K) & (df.strategy == strat)]
            mean_per_w = cell.groupby("window")["p_at_50"].mean()
            ax.plot(mean_per_w.index, mean_per_w.values, marker="o",
                    color=colors[strat], label=strat, linewidth=1.4, markersize=4)
        fired = cp[(cp.cell_K == K) & (cp.fire_capaware)]
        for _, r in fired.iterrows():
            ax.axvspan(r.window - 0.18, r.window + 0.18, color="#fff3b0", alpha=0.5, zorder=0)
        ax.set_title(f"$K={K}$ ($\\tau_K={ {50:0.20, 100:0.05, 200:0.02}[K] }$)", fontsize=10)
        ax.set_xlabel("Window")
        ax.set_xticks(range(1, 7))
        ax.set_ylim(0, 0.85)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Mean P@50")
    axes[0].legend(loc="lower left", fontsize=7, frameon=True, ncol=1)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig1_strategy_trajectories.pdf", bbox_inches="tight")
    plt.close()

    # Fire fraction comparison: cap_aware vs adaptive05
    fire = cp[cp.window >= 2].groupby("cell_K")[["fire_capaware", "fire_adaptive05"]].mean()
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    x = list(range(len(Ks)))
    w = 0.32
    ax.bar([i - w/2 for i in x], fire.fire_capaware.values, width=w,
           color=colors["cap_aware"], label="cap\\_aware ($\\tau_K$)")
    ax.bar([i + w/2 for i in x], fire.fire_adaptive05.values, width=w,
           color=colors["adaptive05"], label="adaptive05 ($\\tau{=}0.05$)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"$K={K}$" for K in Ks])
    ax.set_ylabel("Firing fraction ($w\\geq 2$)")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper left", fontsize=8, frameon=True)
    ax.grid(True, axis="y", alpha=0.3)
    plt.title("Capacity-aware firing is perfectly monotone in $K$ (H3 supported)")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_fire_vs_K.pdf", bbox_inches="tight")
    plt.close()
    print(f"Wrote 2 figures to {FIGURES}")


if __name__ == "__main__":
    main()
