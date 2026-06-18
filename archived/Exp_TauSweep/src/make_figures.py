"""Generate Paper 11 figures from tau_sweep_results.csv."""
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
    pt = pd.read_csv(RESULTS / "per_tau_summary.csv")
    df = pd.read_csv(RESULTS / "tau_sweep_results.csv")

    # Pareto curve: K=50 cost vs K=200 hazard, per tau
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    ax.scatter(pt["cellmean_K50_dadlag1"], pt["worst_K200_dadfix"],
               s=80, c="#1b9e77", zorder=3)
    for _, r in pt.iterrows():
        ax.annotate(f"$\\tau$={r['tau']}", (r["cellmean_K50_dadlag1"], r["worst_K200_dadfix"]),
                    xytext=(6, 4), textcoords="offset points", fontsize=8)
    # Feasible region: K=50 >= -0.02 AND K=200 >= -0.01
    ax.axvline(-0.02, color="#d95f02", linestyle="--", linewidth=1, alpha=0.7,
               label="Paper 10 K=50 tolerance ($-0.02$)")
    ax.axhline(-0.01, color="#7570b3", linestyle="--", linewidth=1, alpha=0.7,
               label="Paper 10 K=200 tolerance ($-0.01$)")
    ax.fill_between([-0.02, 0.01], -0.01, 0.01, color="#b2df8a", alpha=0.25,
                    label="Joint feasible region")
    ax.set_xlim(-0.07, 0.005)
    ax.set_ylim(-0.02, 0.01)
    ax.set_xlabel(r"Cell-mean $\Delta_{\mathrm{ad-lag1}}$ at $K=50$")
    ax.set_ylabel(r"Worst per-window $\Delta_{\mathrm{ad-fix}}$ at $K=200$")
    ax.legend(loc="lower right", fontsize=8, frameon=True)
    ax.grid(True, alpha=0.3)
    plt.title(r"Pareto curve over $\tau$ vs joint feasibility region")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig1_pareto.pdf", bbox_inches="tight")
    plt.close()

    # Fire fraction per K vs tau
    taus = sorted(pt.tau.unique())
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    for K, col in zip([50, 100, 200], ["#1b9e77", "#7570b3", "#d95f02"]):
        ax.plot(taus, [pt[pt.tau == t][f"fire_K{K}"].iloc[0] for t in taus],
                marker="o", color=col, label=f"K={K}", linewidth=1.6)
    ax.set_xlabel(r"$\tau$")
    ax.set_ylabel("Firing fraction ($w\\geq 2$)")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="lower left", fontsize=8, frameon=True)
    ax.grid(True, alpha=0.3)
    plt.title(r"Firing fraction decreases with $\tau$ (H4 sign rejected)")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_fire_vs_tau.pdf", bbox_inches="tight")
    plt.close()
    print(f"Wrote 2 figures to {FIGURES}")


if __name__ == "__main__":
    main()
