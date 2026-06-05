"""Generate Paper 8 figures from multi_history_results.csv."""
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
    df = pd.read_csv(RESULTS / "multi_history_results.csv")
    Ks = [50, 100, 200]
    strategies = ["fixed", "lag1", "trail3", "ewma3", "offline"]
    colors = {"fixed": "#666666", "lag1": "#1b9e77", "trail3": "#7570b3",
              "ewma3": "#d95f02", "offline": "#e7298a"}

    # Trajectory figure
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
    for ax, K in zip(axes, Ks):
        for strat in strategies:
            cell = df[(df.cell_K == K) & (df.strategy == strat)]
            mean_per_w = cell.groupby("window")["p_at_50"].mean()
            ax.plot(mean_per_w.index, mean_per_w.values, marker="o",
                    color=colors[strat], label=strat, linewidth=1.4, markersize=4)
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

    # Recovery ratio bar chart per K (lag1 vs ewma3 vs trail3)
    means = df.groupby(["cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy")
    means["d_off_fix"] = means["offline"] - means["fixed"]
    for s in ("lag1", "trail3", "ewma3"):
        means[f"rho_{s}"] = (means[s] - means["fixed"]) / means["d_off_fix"]
    rho_per_cell = means[means.index.get_level_values("window") >= 2].groupby("cell_K")[
        ["rho_lag1", "rho_trail3", "rho_ewma3"]].mean()
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    x = list(range(len(Ks)))
    w = 0.25
    ax.bar([i - w for i in x], rho_per_cell["rho_lag1"].values, width=w,
           color=colors["lag1"], label="lag1")
    ax.bar(x, rho_per_cell["rho_trail3"].values, width=w,
           color=colors["trail3"], label="trail3")
    ax.bar([i + w for i in x], rho_per_cell["rho_ewma3"].values, width=w,
           color=colors["ewma3"], label="ewma3")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(0.5, color="black", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"$K={K}$" for K in Ks])
    ax.set_ylabel(r"$\bar\rho$ (recovery ratio, $w\geq 2$)")
    ax.legend(loc="lower left", fontsize=8, frameon=True)
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_recovery_ratio.pdf", bbox_inches="tight")
    plt.close()
    print(f"Wrote 2 figures to {FIGURES}")


if __name__ == "__main__":
    main()
