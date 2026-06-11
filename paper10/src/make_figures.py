"""Generate Paper 10 figures from the frozen results CSV.

Produces submission/ieee/figures/fig2_coverage.pdf: mean coverage-to-date
vs window (1-12) for AutoHeal / Fixed-policy / Human-in-loop at
K=50 and K=100 (two panels), 25-seed means.

Usage (from paper10/):
    python3 src/make_figures.py
"""

import csv
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "results", "primary_v1", "autoheal_results.csv")
OUT = os.path.join(HERE, "..", "submission", "ieee", "figures", "fig2_coverage.pdf")

STRATEGIES = ["AutoHeal", "Fixed-policy", "Human-in-loop"]
STYLES = {
    "AutoHeal": dict(color="tab:blue", linestyle="-", marker="o"),
    "Fixed-policy": dict(color="tab:orange", linestyle="--", marker="s"),
    "Human-in-loop": dict(color="tab:green", linestyle=":", marker="^"),
}


def main() -> None:
    data = defaultdict(list)  # (K, strategy, window) -> [coverage]
    with open(CSV, newline="") as fh:
        for row in csv.DictReader(fh):
            key = (row["cell_K"], row["strategy"], int(row["window"]))
            data[key].append(float(row["coverage_to_date"]))

    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.9), sharey=True)
    windows = list(range(1, 13))
    for ax, K in zip(axes, ["50", "100"]):
        for strat in STRATEGIES:
            # Human-in-loop runs at fixed K_human=30 and its rows are
            # recorded under cell_K=30 regardless of the capacity cell.
            cell = "30" if strat == "Human-in-loop" else K
            ys = [sum(data[(cell, strat, w)]) / len(data[(cell, strat, w)])
                  for w in windows]
            ax.plot(windows, ys, label=strat, markersize=2.2,
                    linewidth=1.0, **STYLES[strat])
        ax.axhline(0.80, color="gray", linestyle=(0, (1, 2)), linewidth=0.8)
        ax.axvline(6, color="gray", linestyle=(0, (1, 2)), linewidth=0.6)
        ax.set_title(f"$K={K}$", fontsize=7)
        ax.set_xlabel("Window", fontsize=7)
        ax.set_xticks([1, 3, 6, 9, 12])
        ax.tick_params(labelsize=6)
        ax.set_ylim(0.0, 1.05)
    axes[0].set_ylabel("Mean coverage-to-date", fontsize=7)
    axes[0].legend(fontsize=5.5, loc="lower right", frameon=False)
    fig.tight_layout(pad=0.3)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
