"""Analyse Paper 10 adaptive results: hypothesis outcomes + LaTeX tables."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "primary_v1"
TABLES = ROOT / "submission" / "ieee" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(RESULTS / "adaptive_results.csv")
    cp = pd.read_csv(RESULTS / "changepoint_log.csv")
    print(f"Loaded {len(df)} P@50 rows; {len(cp)} change-point rows.")

    means = df.groupby(["cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy").reset_index()
    means["d_ad_fix"] = means["adaptive"] - means["fixed"]
    means["d_ad_lag1"] = means["adaptive"] - means["lag1"]
    means["d_ad_gated"] = means["adaptive"] - means["gated"]
    means["d_off_fix"] = means["offline"] - means["fixed"]
    means["rho_adapt"] = np.where(
        means["d_off_fix"] > 0.01, means["d_ad_fix"] / means["d_off_fix"], np.nan)
    means.to_csv(RESULTS / "cell_window_means.csv", index=False)

    # H1: at K=200, adaptive >= fixed at every w>=2 (delta >= -0.01)
    k200 = means[(means.cell_K == 200) & (means.window >= 2)]
    h1_fail = k200[k200["d_ad_fix"] < -0.01]
    H1 = bool(len(h1_fail) == 0)

    # H2: at K in {50,100}, |adaptive - lag1| <= 0.02 at every w>=2
    mod = means[(means.cell_K.isin([50, 100])) & (means.window >= 2)]
    h2_fail = mod[mod["d_ad_lag1"].abs() > 0.02]
    H2 = bool(len(h2_fail) == 0)

    # H3: change-point firing fraction monotone in K (Spearman >= 0.8)
    fire = cp[cp.window >= 2].groupby("cell_K")["cp_fired"].mean()
    rho_h3, p_h3 = spearmanr(fire.index, fire.values)
    H3 = bool(rho_h3 >= 0.8)

    # H4: at K=200, adaptive cell-mean >= gated cell-mean
    k200_cm = means[(means.cell_K == 200) & (means.window >= 2)]
    adaptive_cm = k200_cm["adaptive"].mean()
    gated_cm = k200_cm["gated"].mean()
    H4 = bool(adaptive_cm >= gated_cm)

    # Aggregate recovery ratios
    rho_per_cell = means[means.window >= 2].groupby("cell_K")[
        ["d_ad_fix", "d_ad_lag1", "rho_adapt"]].mean()
    fire_frac = fire.to_dict()

    summary = {
        "n_rows": int(len(df)),
        "H1_adaptive_no_hazard_K200": {"supported": H1, "n_failures": int(len(h1_fail)),
                                         "failures": h1_fail[["cell_K", "window", "d_ad_fix"]].to_dict("records")},
        "H2_adaptive_matches_lag1_modK": {"supported": H2, "n_failures": int(len(h2_fail)),
                                            "failures": h2_fail[["cell_K", "window", "d_ad_lag1"]].to_dict("records")},
        "H3_fire_monotone_in_K": {"supported": H3, "spearman_rho": float(rho_h3), "p": float(p_h3),
                                    "fire_frac_per_K": fire_frac},
        "H4_adaptive_beats_gated_K200": {"supported": H4,
                                           "adaptive_cell_mean": float(adaptive_cm),
                                           "gated_cell_mean": float(gated_cm),
                                           "delta": float(adaptive_cm - gated_cm)},
        "fire_fractions": fire_frac,
        "cell_means_round": rho_per_cell.round(3).to_dict(),
        "cell_window_means": means.round(4).to_dict("records"),
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # tab_main: per (K, window) all 5 strategies
    lines = [
        "\\begin{table*}[!t]",
        "  \\caption{Mean P@50 per (capacity $K$, window) for all five strategies. The change-point fire decision per (K, window) is shown by the bullet ($\\bullet$ = fired).}",
        "  \\label{tab:main}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{5pt}",
        "  \\begin{tabular}{cccc ccccc c}",
        "    \\toprule",
        "    $K$ & W & CP & $\\Delta_w$ & fixed & lag1 & adaptive & gated & offline & $\\rho_{\\mathrm{adapt}}$ \\\\",
        "    \\midrule",
    ]
    cp_idx = cp.set_index(["cell_K", "window"])
    for K in [50, 100, 200]:
        sub = means[means.cell_K == K].sort_values("window")
        for _, r in sub.iterrows():
            cp_row = cp_idx.loc[(int(r["cell_K"]), int(r["window"]))]
            fired = "$\\bullet$" if cp_row["cp_fired"] else "$\\circ$"
            delta = cp_row["cp_delta"]
            rho_s = f"{r['rho_adapt']:.2f}" if pd.notna(r['rho_adapt']) else "---"
            lines.append(
                f"    {int(r['cell_K'])} & {int(r['window'])} & {fired} & ${delta:+.3f}$ & "
                f"{r['fixed']:.3f} & {r['lag1']:.3f} & {r['adaptive']:.3f} & "
                f"{r['gated']:.3f} & {r['offline']:.3f} & {rho_s} \\\\"
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
        "  \\begin{tabular}{@{}p{0.5cm}p{4.9cm}p{1.9cm}@{}}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & adaptive $\\geq$ fixed at every $w\\geq 2$, $K=200$ (within $-0.01$) & {'Supported' if H1 else f'Rejected ({len(h1_fail)})'} \\\\",
        f"    H2 & $|$adaptive $-$ lag1$|\\leq 0.02$, $K\\in\\{{50,100\\}}$ & {'Supported' if H2 else f'Rejected ({len(h2_fail)})'} \\\\",
        f"    H3 & fire fraction Spearman$(K,\\cdot)\\geq +0.8$ & " + ("Supported" if H3 else f"Rejected ($\\rho={rho_h3:.2f}$)") + " \\\\",
        f"    H4 & adaptive cell-mean $\\geq$ gated cell-mean at $K=200$ & " + ("Supported" if H4 else f"Rejected ($\\Delta={adaptive_cm-gated_cm:+.3f}$)") + " \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps({k: v for k, v in summary.items() if k != "cell_window_means"},
                     indent=2, default=float))


if __name__ == "__main__":
    main()
