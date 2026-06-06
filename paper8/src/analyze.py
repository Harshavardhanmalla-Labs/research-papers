"""Analyse Paper 8 multi-history results: hypothesis outcomes + LaTeX tables."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_v1"
TABLES = ROOT / "submission" / "ieee" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(RESULTS / "multi_history_results.csv")
    print(f"Loaded {len(df)} rows.")

    means = df.groupby(["cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy").reset_index()
    means.to_csv(RESULTS / "cell_window_means.csv", index=False)

    # Compute deltas
    means["d_ewma_fix"] = means["ewma3"] - means["fixed"]
    means["d_ewma_lag1"] = means["ewma3"] - means["lag1"]
    means["d_ewma_trail"] = means["ewma3"] - means["trail3"]
    means["d_off_fix"] = means["offline"] - means["fixed"]
    means["rho_ewma"] = np.where(
        means["d_off_fix"] > 0.01, means["d_ewma_fix"] / means["d_off_fix"], np.nan)
    means["d_lag1_fix"] = means["lag1"] - means["fixed"]
    means["rho_lag1"] = np.where(
        means["d_off_fix"] > 0.01, means["d_lag1_fix"] / means["d_off_fix"], np.nan)

    # H1: at K=200, ewma3 >= fixed at every w>=2 (delta >= -0.01)
    k200 = means[(means.cell_K == 200) & (means.window >= 2)]
    h1_fail = k200[k200["d_ewma_fix"] < -0.01]
    H1 = bool(len(h1_fail) == 0)

    # H2: at K in {50,100}, |ewma3 - lag1| <= 0.02 at every w>=2
    mod = means[(means.cell_K.isin([50, 100])) & (means.window >= 2)]
    h2_fail = mod[mod["d_ewma_lag1"].abs() > 0.02]
    H2 = bool(len(h2_fail) == 0)

    # H3: |ewma3 - trail3| <= 0.02 everywhere
    h3_fail = means[(means.window >= 2) & (means["d_ewma_trail"].abs() > 0.02)]
    H3 = bool(len(h3_fail) == 0)

    # H4: K=200 cell-mean rho_ewma across w>=2 >= 0.5
    rho_k200 = means[(means.cell_K == 200) & (means.window >= 2)]["rho_ewma"].mean()
    H4 = bool(rho_k200 >= 0.5)

    rho_per_cell = means[means.window >= 2].groupby("cell_K")[["rho_ewma", "rho_lag1"]].mean()

    summary = {
        "n_rows": int(len(df)),
        "H1_ewma_no_hazard_K200": {"supported": H1, "n_failures": int(len(h1_fail)),
                                    "failures": h1_fail.to_dict("records")},
        "H2_ewma_matches_lag1_modK": {"supported": H2, "n_failures": int(len(h2_fail)),
                                       "failures": h2_fail.to_dict("records")},
        "H3_ewma_matches_trail3": {"supported": H3, "n_failures": int(len(h3_fail)),
                                    "failures": h3_fail.to_dict("records")},
        "H4_ewma_recovery_K200": {"supported": H4, "rho_K200_mean": float(rho_k200)},
        "recovery_per_cell": rho_per_cell.round(3).to_dict(),
        "cell_window_means": means.round(4).to_dict("records"),
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # tab_main: per (K, window) all 5 strategies
    lines = [
        "\\begin{table*}[!t]",
        "  \\caption{Mean P@50 per (capacity $K$, window) for all five calibration strategies. EWMA and trail3 are the multi-history smoothers introduced in this paper; offline is the Paper~7 ceiling.}",
        "  \\label{tab:main}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{5pt}",
        "  \\begin{tabular}{cc ccccc cc}",
        "    \\toprule",
        "    $K$ & W & fixed & lag1 & trail3 & ewma3 & offline & $\\Delta_{\\mathrm{ewma\\!-\\!fix}}$ & $\\rho_{\\mathrm{ewma}}$ \\\\",
        "    \\midrule",
    ]
    for K in [50, 100, 200]:
        sub = means[means.cell_K == K].sort_values("window")
        for _, r in sub.iterrows():
            rho_str = f"{r['rho_ewma']:.2f}" if pd.notna(r['rho_ewma']) else "---"
            lines.append(
                f"    {int(r['cell_K'])} & {int(r['window'])} & "
                f"{r['fixed']:.3f} & {r['lag1']:.3f} & {r['trail3']:.3f} & "
                f"{r['ewma3']:.3f} & {r['offline']:.3f} & "
                f"{r['d_ewma_fix']:+.3f} & {rho_str} \\\\"
            )
        lines.append("    \\midrule")
    lines = lines[:-1]
    lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table*}"]
    (TABLES / "tab_main.tex").write_text("\n".join(lines) + "\n")

    # tab_hypotheses
    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Pre-registered hypothesis outcomes.}",
        "  \\label{tab:hypotheses}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{@{}p{0.5cm}p{5.0cm}p{1.8cm}@{}}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & EWMA-3 $\\geq$ fixed at every $w\\geq 2$, $K=200$ (within $-0.01$) & {'Supported' if H1 else f'Rejected ({len(h1_fail)})'} \\\\",
        f"    H2 & $|$EWMA-3 $-$ lag1$|\\leq 0.02$, $K\\in\\{{50,100\\}}$ & {'Supported' if H2 else f'Rejected ({len(h2_fail)})'} \\\\",
        f"    H3 & $|$EWMA-3 $-$ trail3$|\\leq 0.02$ everywhere & {'Supported' if H3 else f'Rejected ({len(h3_fail)})'} \\\\",
        f"    H4 & $\\bar\\rho^{{\\mathrm{{ewma}}}}_{{K=200}}\\geq 0.5$ & {'Supported' if H4 else f'Rejected ({rho_k200:.2f})'} \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps({k: v for k, v in summary.items() if k not in ("cell_window_means",)},
                     indent=2, default=float))


if __name__ == "__main__":
    main()
