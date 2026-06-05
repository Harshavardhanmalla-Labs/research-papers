"""Analyse Paper 7 online_calib_results.csv: per-cell-per-window means,
hypothesis outcomes H1-H3, LaTeX tables.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_v1"
TABLES = ROOT / "submission" / "ieee" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def bootstrap_ci(x: np.ndarray, n: int = 10_000, ci: float = 0.95, seed: int = 0):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [(1 - ci) / 2 * 100, (1 + ci) / 2 * 100])
    return float(x.mean()), float(lo), float(hi)


def main() -> None:
    df = pd.read_csv(RESULTS / "online_calib_results.csv")
    print(f"Loaded {len(df)} rows.")

    # Cell-mean per (cell_K, window, strategy)
    grp = df.groupby(["cell_K", "window", "strategy"])["p_at_50"]
    means = grp.mean().unstack("strategy").reset_index()
    print(means.to_string())

    # Wide view for easy comparison
    means_csv = means.copy()
    means_csv.to_csv(RESULTS / "cell_window_means.csv", index=False)

    # H1: online - fixed >= -0.01 at every (cell, window)
    means["delta_on_fix"] = means["online"] - means["fixed"]
    h1_failures = means[means["delta_on_fix"] < -0.01]
    h1_supported = len(h1_failures) == 0

    # H2: online - offline <= +0.01 at every (cell, window)
    means["delta_on_off"] = means["online"] - means["offline"]
    h2_failures = means[means["delta_on_off"] > 0.01]
    h2_supported = len(h2_failures) == 0

    # H3: At K in {100, 200}, online recovers >= 50% of (offline-fixed)
    # AND absolute online gain >= 5pp for at least one w in {4,5,6}
    means["delta_off_fix"] = means["offline"] - means["fixed"]
    means["rho"] = np.where(
        means["delta_off_fix"] > 0.01,
        means["delta_on_fix"] / means["delta_off_fix"],
        np.nan,
    )
    high_K_late = means[(means.cell_K.isin([100, 200])) & (means.window.isin([4, 5, 6]))]
    h3_qualifying = high_K_late[
        (high_K_late["delta_on_fix"] >= 0.05)
        & (high_K_late["delta_off_fix"] > 0.01)
        & (high_K_late["rho"] >= 0.5)
    ]
    h3_supported = len(h3_qualifying) > 0

    # Aggregate recovery ratio per cell (mean of rho over w >= 2)
    rho_per_cell = means[means.window >= 2].groupby("cell_K")["rho"].mean()

    # Persist results
    summary = {
        "n_rows": int(len(df)),
        "H1": {
            "supported": bool(h1_supported),
            "n_failures": int(len(h1_failures)),
            "failures": h1_failures.to_dict("records"),
        },
        "H2": {
            "supported": bool(h2_supported),
            "n_failures": int(len(h2_failures)),
            "failures": h2_failures.to_dict("records"),
        },
        "H3": {
            "supported": bool(h3_supported),
            "qualifying_cells": h3_qualifying.to_dict("records"),
        },
        "recovery_ratio_per_cell_w2plus": rho_per_cell.round(3).to_dict(),
        "cell_window_means": means[["cell_K", "window", "fixed", "online", "offline",
                                     "delta_on_fix", "delta_off_fix", "rho"]].round(4).to_dict("records"),
    }

    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # LaTeX table 1: per (K, window) fixed/online/offline + deltas
    lines = [
        "\\begin{table*}[!t]",
        "  \\caption{Mean P@50 across 25 evaluation seeds per (capacity $K$, window) for each calibration strategy, with the online-vs-fixed gain and online recovery ratio of the offline ceiling.}",
        "  \\label{tab:main}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{6pt}",
        "  \\begin{tabular}{cc ccc cc c}",
        "    \\toprule",
        "    $K$ & Window & fixed & online & offline & $\\Delta_{\\mathrm{on\\!-\\!fix}}$ & $\\Delta_{\\mathrm{off\\!-\\!fix}}$ & $\\rho$ \\\\",
        "    \\midrule",
    ]
    for K in [50, 100, 200]:
        sub = means[means.cell_K == K].sort_values("window")
        for _, r in sub.iterrows():
            rho_str = f"{r['rho']:.2f}" if pd.notna(r['rho']) else "---"
            lines.append(
                f"    {int(r['cell_K'])} & {int(r['window'])} & "
                f"{r['fixed']:.3f} & {r['online']:.3f} & {r['offline']:.3f} & "
                f"{r['delta_on_fix']:+.3f} & {r['delta_off_fix']:+.3f} & {rho_str} \\\\"
            )
        lines.append("    \\midrule")
    lines = lines[:-1]  # drop trailing midrule
    lines += [
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table*}",
    ]
    (TABLES / "tab_main.tex").write_text("\n".join(lines) + "\n")

    # LaTeX table 2: hypothesis outcomes
    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Pre-registered hypothesis outcomes.}",
        "  \\label{tab:hypotheses}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{@{}p{0.5cm}p{4.8cm}p{2.3cm}@{}}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & online $\\geq$ fixed (within $0.01$) at every cell-window & {'Supported' if h1_supported else f'Rejected ({len(h1_failures)} fails)'} \\\\",
        f"    H2 & online $\\leq$ offline (within $0.01$) at every cell-window & {'Supported' if h2_supported else f'Rejected ({len(h2_failures)} fails)'} \\\\",
        f"    H3 & online recovers $\\geq 50\\%$ of gap at $K\\in\\{{100,200\\}}$, $w\\in\\{{4,5,6\\}}$ & {'Supported' if h3_supported else 'Rejected'} \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
