"""Generate Paper 10 figures from adaptive_results.csv + changepoint_log.csv."""
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
    df = pd.read_csv(RESULTS / "adaptive_results.csv")
    cp = pd.read_csv(RESULTS / "changepoint_log.csv")
    Ks = [50, 100, 200]
    strategies = ["fixed", "lag1", "adaptive", "gated", "offline"]
    colors = {"fixed": "#666666", "lag1": "#1b9e77",
              "adaptive": "#d95f02", "gated": "#7570b3", "offline": "#e7298a"}

    # Trajectory figure
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
    for ax, K in zip(axes, Ks):
        for strat in strategies:
            cell = df[(df.cell_K == K) & (df.strategy == strat)]
            mean_per_w = cell.groupby("window")["p_at_50"].mean()
            ax.plot(mean_per_w.index, mean_per_w.values, marker="o",
                    color=colors[strat], label=strat, linewidth=1.4, markersize=4)
        # Annotate fire windows
        fired = cp[(cp.cell_K == K) & (cp.cp_fired)]
        for _, r in fired.iterrows():
            ax.axvspan(r.window - 0.18, r.window + 0.18, color="#fff3b0", alpha=0.6, zorder=0)
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

    # Fire-fraction + cell-mean delta vs fixed and vs lag1
    means = df.groupby(["cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy")
    means["d_ad_fix"] = means["adaptive"] - means["fixed"]
    means["d_ad_lag1"] = means["adaptive"] - means["lag1"]
    cellm = means[means.index.get_level_values("window") >= 2].groupby("cell_K")[["d_ad_fix", "d_ad_lag1"]].mean()
    fire = cp[cp.window >= 2].groupby("cell_K")["cp_fired"].mean()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.6))
    x = list(range(len(Ks)))
    w = 0.32
    ax1.bar([i - w/2 for i in x], cellm["d_ad_fix"].values, width=w,
            color=colors["adaptive"], label=r"$\Delta_{\mathrm{ad}-\mathrm{fix}}$")
    ax1.bar([i + w/2 for i in x], cellm["d_ad_lag1"].values, width=w,
            color=colors["lag1"], label=r"$\Delta_{\mathrm{ad}-\mathrm{lag1}}$")
    ax1.axhline(0, color="black", linewidth=0.7)
    ax1.set_xticks(x); ax1.set_xticklabels([f"$K={K}$" for K in Ks])
    ax1.set_ylabel("Cell-mean delta (P@50)")
    ax1.legend(loc="upper right", fontsize=8, frameon=True)
    ax1.grid(True, axis="y", alpha=0.3)

    ax2.bar(x, [fire.loc[K] for K in Ks], color="#888888")
    ax2.set_xticks(x); ax2.set_xticklabels([f"$K={K}$" for K in Ks])
    ax2.set_ylabel("Fire fraction ($w\\geq 2$)")
    ax2.set_ylim(0, 1.0)
    ax2.grid(True, axis="y", alpha=0.3)
    for i, K in enumerate(Ks):
        ax2.text(i, fire.loc[K] + 0.03, f"{fire.loc[K]:.0%}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_deltas_fires.pdf", bbox_inches="tight")
    plt.close()
    print(f"Wrote 2 figures to {FIGURES}")


if __name__ == "__main__":
    main()
