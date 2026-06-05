"""Analyse Paper 6 sweep_results.csv: per-cell means, decay slopes,
Spearman correlations for H1/H2, H3 critical ratio, H4 retention check.

Outputs:
  - results/primary_sweep_v1/cell_summary.csv : per-cell-per-method aggregates
  - results/primary_sweep_v1/hypothesis_summary.json : H1-H4 outcomes
  - submission/ieee/tables/tab_w6_retention.tex
  - submission/ieee/tables/tab_decay_slopes.tex
  - submission/ieee/tables/tab_hypotheses.tex
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_sweep_v1"
TABLES = ROOT / "submission" / "ieee" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def bootstrap_ci(x: np.ndarray, n: int = 10_000, ci: float = 0.95, seed: int = 0):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [(1 - ci) / 2 * 100, (1 + ci) / 2 * 100])
    return float(x.mean()), float(lo), float(hi)


def per_seed_slopes(df: pd.DataFrame) -> pd.DataFrame:
    """Return cell_K, cell_lambda, method, seed, slope for P@50 over windows 1..6."""
    rows = []
    g = df.groupby(["cell_K", "cell_lambda", "method", "seed"])
    for (K, lam, m, s), sub in g:
        sub = sub.sort_values("window")
        x = sub["window"].values.astype(float)
        y = sub["p_at_50"].values.astype(float)
        # OLS slope: beta = cov(x,y) / var(x)
        beta = np.polyfit(x, y, 1)[0]
        rows.append({"cell_K": K, "cell_lambda": lam, "method": m, "seed": s, "slope": beta})
    return pd.DataFrame(rows)


def main() -> None:
    df = pd.read_csv(RESULTS / "sweep_results.csv")
    print(f"Loaded {len(df)} rows.")

    # ----------------------------------------------------------------
    # Cell summary: per-cell-per-method mean and bootstrap CI for P@50 at W1, W6
    # and mean decay slope.
    # ----------------------------------------------------------------
    slopes = per_seed_slopes(df)
    summary_rows = []
    cells = sorted(df[["cell_K", "cell_lambda"]].drop_duplicates().itertuples(index=False))
    methods = sorted(df["method"].unique())
    for K, lam in cells:
        for m in methods:
            cell = df[(df.cell_K == K) & (df.cell_lambda == lam) & (df.method == m)]
            w1 = cell[cell.window == 1]["p_at_50"].values
            w6 = cell[cell.window == 6]["p_at_50"].values
            sl = slopes[(slopes.cell_K == K) & (slopes.cell_lambda == lam) & (slopes.method == m)]["slope"].values
            row = {
                "cell_K": K, "cell_lambda": lam, "method": m,
                "w1_mean": w1.mean(), "w6_mean": w6.mean(),
                "slope_mean": sl.mean(),
            }
            row["w1_ci_lo"], row["w1_ci_hi"] = bootstrap_ci(w1)[1:]
            row["w6_ci_lo"], row["w6_ci_hi"] = bootstrap_ci(w6)[1:]
            row["slope_ci_lo"], row["slope_ci_hi"] = bootstrap_ci(sl, seed=42)[1:]
            summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(RESULTS / "cell_summary.csv", index=False)

    # ----------------------------------------------------------------
    # H1: Spearman(K, slope) at each fixed lambda for EPSS-only
    # H2: Spearman(lambda, slope) at each fixed K for EPSS-only
    # ----------------------------------------------------------------
    epss = summary[summary.method == "EPSS-only"]
    H1 = {}
    for lam in sorted(epss.cell_lambda.unique()):
        sub = epss[epss.cell_lambda == lam].sort_values("cell_K")
        rho, p = spearmanr(sub.cell_K, sub.slope_mean)
        H1[float(lam)] = {"rho": float(rho), "p": float(p),
                          "supported": bool(rho <= -0.8)}
    H1_supported_all = all(v["supported"] for v in H1.values())

    H2 = {}
    for K in sorted(epss.cell_K.unique()):
        sub = epss[epss.cell_K == K].sort_values("cell_lambda")
        rho, p = spearmanr(sub.cell_lambda, sub.slope_mean)
        H2[int(K)] = {"rho": float(rho), "p": float(p),
                      "supported": bool(rho >= 0.8)}
    H2_supported_all = all(v["supported"] for v in H2.values())

    # ----------------------------------------------------------------
    # H3: Find cells where slope >= -0.01; report min K/lambda among those
    # ----------------------------------------------------------------
    steady = epss[epss.slope_mean >= -0.01].copy()
    steady["K_over_lambda"] = steady.cell_K / steady.cell_lambda
    if len(steady):
        h3_min_ratio = float(steady["K_over_lambda"].min())
        h3_cells = steady[["cell_K", "cell_lambda", "slope_mean"]].to_dict("records")
    else:
        h3_min_ratio = None
        h3_cells = []

    # Also report which cells DO satisfy slope ≥ -0.01 vs do not
    # Critical ratio framing: at the minimum K/lambda among steady cells.

    # ----------------------------------------------------------------
    # H4: HygienePrio-full W6 mean >= 0.40 at all 20 cells
    # ----------------------------------------------------------------
    hp = summary[summary.method == "HygienePrio-full"]
    hp_w6_min = float(hp.w6_mean.min())
    hp_w6_min_cell = hp.loc[hp.w6_mean.idxmin(), ["cell_K", "cell_lambda"]].to_dict()
    H4_supported = bool(hp_w6_min >= 0.40)
    H4_failures = hp[hp.w6_mean < 0.40][["cell_K", "cell_lambda", "w6_mean"]].to_dict("records")

    # ----------------------------------------------------------------
    # Per-cell-pair persistence: fraction of (seed, cell) pairs where
    # HP-full > EPSS-only at every window
    # ----------------------------------------------------------------
    persist_rows = []
    for K, lam in cells:
        sub = df[(df.cell_K == K) & (df.cell_lambda == lam)]
        n_dom = 0
        n_tot = 0
        for s in sub.seed.unique():
            ss = sub[sub.seed == s]
            hp_w = ss[ss.method == "HygienePrio-full"].sort_values("window")["p_at_50"].values
            ep_w = ss[ss.method == "EPSS-only"].sort_values("window")["p_at_50"].values
            for wi in range(6):
                n_tot += 1
                if hp_w[wi] > ep_w[wi]:
                    n_dom += 1
        persist_rows.append({"cell_K": K, "cell_lambda": lam,
                             "dom_pairs": n_dom, "total_pairs": n_tot,
                             "dom_frac": n_dom / n_tot})
    persistence = pd.DataFrame(persist_rows)
    persistence.to_csv(RESULTS / "persistence.csv", index=False)
    persist_min = float(persistence["dom_frac"].min())
    persist_total_dom = int(persistence["dom_pairs"].sum())
    persist_total = int(persistence["total_pairs"].sum())

    # ----------------------------------------------------------------
    # Persist results
    # ----------------------------------------------------------------
    out = {
        "n_rows": len(df),
        "n_cells": len(cells),
        "n_seeds": int(df.seed.nunique()),
        "H1": {"per_lambda": H1, "supported_all_lambdas": H1_supported_all},
        "H2": {"per_K": H2, "supported_all_Ks": H2_supported_all},
        "H3": {"min_K_over_lambda_steady": h3_min_ratio, "steady_cells": h3_cells},
        "H4": {"hp_w6_min": hp_w6_min, "hp_w6_min_cell": hp_w6_min_cell,
               "supported": H4_supported, "failures": H4_failures},
        "persistence": {"min_cell_frac": persist_min,
                        "total_dom": persist_total_dom,
                        "total_pairs": persist_total,
                        "overall_frac": persist_total_dom / persist_total},
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(out, f, indent=2, default=float)

    # ----------------------------------------------------------------
    # LaTeX tables
    # ----------------------------------------------------------------

    # tab_w6_retention.tex: HP-full vs EPSS-only mean P@50 at W6, per cell
    hp_grid = summary[summary.method == "HygienePrio-full"].pivot(
        index="cell_lambda", columns="cell_K", values="w6_mean")
    ep_grid = summary[summary.method == "EPSS-only"].pivot(
        index="cell_lambda", columns="cell_K", values="w6_mean")

    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Window-6 mean P@50 for HygienePrio-full (top) and EPSS-only (bottom), per cell.}",
        "  \\label{tab:w6}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{l" + "c" * len(hp_grid.columns) + "}",
        "    \\toprule",
        "    & \\multicolumn{" + str(len(hp_grid.columns)) + "}{c}{Capacity $K$} \\\\",
        "    \\cmidrule(lr){2-" + str(1 + len(hp_grid.columns)) + "}",
        "    $\\lambda$ & " + " & ".join(f"{int(c)}" for c in hp_grid.columns) + " \\\\",
        "    \\midrule",
        "    \\multicolumn{" + str(1 + len(hp_grid.columns)) + "}{l}{\\textit{HygienePrio-full}} \\\\",
    ]
    for lam in sorted(hp_grid.index):
        row = " & ".join(f"{hp_grid.loc[lam, c]:.3f}" for c in hp_grid.columns)
        lines.append(f"    {lam:.0f} & {row} \\\\")
    lines.append("    \\midrule")
    lines.append("    \\multicolumn{" + str(1 + len(hp_grid.columns)) + "}{l}{\\textit{EPSS-only}} \\\\")
    for lam in sorted(ep_grid.index):
        row = " & ".join(f"{ep_grid.loc[lam, c]:.3f}" for c in ep_grid.columns)
        lines.append(f"    {lam:.0f} & {row} \\\\")
    lines += [
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_w6_retention.tex").write_text("\n".join(lines) + "\n")

    # tab_decay_slopes.tex: mean P@50 decay slope per cell, EPSS-only
    ep_slope = summary[summary.method == "EPSS-only"].pivot(
        index="cell_lambda", columns="cell_K", values="slope_mean")
    hp_slope = summary[summary.method == "HygienePrio-full"].pivot(
        index="cell_lambda", columns="cell_K", values="slope_mean")

    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Mean P@50 decay slope (per window) for EPSS-only (top) and HygienePrio-full (bottom). Negative = decay; near zero = steady.}",
        "  \\label{tab:slopes}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{l" + "c" * len(ep_slope.columns) + "}",
        "    \\toprule",
        "    & \\multicolumn{" + str(len(ep_slope.columns)) + "}{c}{Capacity $K$} \\\\",
        "    \\cmidrule(lr){2-" + str(1 + len(ep_slope.columns)) + "}",
        "    $\\lambda$ & " + " & ".join(f"{int(c)}" for c in ep_slope.columns) + " \\\\",
        "    \\midrule",
        "    \\multicolumn{" + str(1 + len(ep_slope.columns)) + "}{l}{\\textit{EPSS-only}} \\\\",
    ]
    for lam in sorted(ep_slope.index):
        row = " & ".join(f"{ep_slope.loc[lam, c]:+.3f}" for c in ep_slope.columns)
        lines.append(f"    {lam:.0f} & {row} \\\\")
    lines.append("    \\midrule")
    lines.append("    \\multicolumn{" + str(1 + len(ep_slope.columns)) + "}{l}{\\textit{HygienePrio-full}} \\\\")
    for lam in sorted(hp_slope.index):
        row = " & ".join(f"{hp_slope.loc[lam, c]:+.3f}" for c in hp_slope.columns)
        lines.append(f"    {lam:.0f} & {row} \\\\")
    lines += [
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_decay_slopes.tex").write_text("\n".join(lines) + "\n")

    # tab_hypotheses.tex
    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Pre-registered hypothesis outcomes.}",
        "  \\label{tab:hypotheses}",
        "  \\centering",
        "  \\small",
        "  \\begin{tabular}{lll}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & Spearman$(K, \\text{{slope}})\\leq -0.8$, $\\forall\\lambda$ & {'Supported' if H1_supported_all else 'Rejected'} \\\\",
        f"    H2 & Spearman$(\\lambda, \\text{{slope}})\\geq +0.8$, $\\forall K$ & {'Supported' if H2_supported_all else 'Rejected'} \\\\",
        f"    H3 & Critical $K/\\lambda$ (descriptive) & $\\min K/\\lambda = " + (f"{h3_min_ratio:.2f}$" if h3_min_ratio is not None else "n/a$") + " \\\\",
        f"    H4 & HP-full W6 $\\geq 0.40$, all cells & {'Supported' if H4_supported else 'Rejected'} (min $= " + f"{hp_w6_min:.3f}$)" + " \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    # Print summary to stdout for paper drafting
    print(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
