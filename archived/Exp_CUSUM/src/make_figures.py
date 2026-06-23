"""Generate Paper 13 figures."""
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
    df = pd.read_csv(RESULTS / "cusum_results.csv")
    cp = pd.read_csv(RESULTS / "changepoint_log.csv")
    Ks = [50, 100, 200]
    strategies = ["fixed", "lag1", "cap_aware", "cusum", "gated", "offline"]
    colors = {"fixed": "#666666", "lag1": "#1b9e77", "cap_aware": "#7570b3",
              "cusum": "#d95f02", "gated": "#e7298a", "offline": "#a6cee3"}

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8), sharey=True)
    for ax, K in zip(axes, Ks):
        for strat in strategies:
            cell = df[(df.cell_K == K) & (df.strategy == strat)]
            mean_per_w = cell.groupby("window")["p_at_50"].mean()
            ax.plot(mean_per_w.index, mean_per_w.values, marker="o",
                    color=colors[strat], label=strat, linewidth=1.4, markersize=4)
        fired = cp[(cp.cell_K == K) & (cp.fire_cusum)]
        for _, r in fired.iterrows():
            ax.axvspan(r.window - 0.18, r.window + 0.18, color="#fff3b0", alpha=0.5, zorder=0)
        ax.set_title(f"$K={K}$", fontsize=10)
        ax.set_xlabel("Window")
        ax.set_xticks(range(1, 7))
        ax.set_ylim(0, 0.85)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Mean P@50")
    axes[0].legend(loc="lower left", fontsize=7, frameon=True, ncol=1)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig1_strategy_trajectories.pdf", bbox_inches="tight")
    plt.close()

    # K=200 detail: cusum vs cap_aware vs gated
    fig, ax = plt.subplots(figsize=(4.8, 2.8))
    cell200 = df[df.cell_K == 200]
    for strat in ["cusum", "cap_aware", "gated", "lag1", "fixed"]:
        mean_per_w = cell200[cell200.strategy == strat].groupby("window")["p_at_50"].mean()
        ax.plot(mean_per_w.index, mean_per_w.values, marker="o",
                color=colors[strat], label=strat, linewidth=1.8, markersize=5)
    fired = cp[(cp.cell_K == 200) & (cp.fire_cusum)]
    for _, r in fired.iterrows():
        ax.axvspan(r.window - 0.18, r.window + 0.18, color="#fff3b0", alpha=0.5, zorder=0)
    ax.set_title("$K=200$ detail: CUSUM beats gated at W4 and W5")
    ax.set_xlabel("Window")
    ax.set_ylabel("Mean P@50")
    ax.set_xticks(range(1, 7))
    ax.set_ylim(0, 0.85)
    ax.legend(loc="upper right", fontsize=8, frameon=True)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_k200_detail.pdf", bbox_inches="tight")
    plt.close()

    print(f"Wrote 2 figures to {FIGURES}")


if __name__ == "__main__":
    main()
