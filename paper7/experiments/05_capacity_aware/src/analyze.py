"""Analyse Paper 12 cap-aware results: H1-H4 + LaTeX tables."""
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
    df = pd.read_csv(RESULTS / "cap_aware_results.csv")
    cp = pd.read_csv(RESULTS / "changepoint_log.csv")

    means = df.groupby(["cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy").reset_index()
    means["d_cap_fix"] = means["cap_aware"] - means["fixed"]
    means["d_cap_lag1"] = means["cap_aware"] - means["lag1"]
    means["d_cap_ad05"] = means["cap_aware"] - means["adaptive05"]
    means["d_cap_gated"] = means["cap_aware"] - means["gated"]
    means.to_csv(RESULTS / "cell_window_means.csv", index=False)

    # H1: feasibility region
    k200 = means[(means.cell_K == 200) & (means.window >= 2)]
    worst_k200 = float(k200["d_cap_fix"].min())
    cm_k50 = float(means[(means.cell_K == 50) & (means.window >= 2)]["d_cap_lag1"].mean())
    cm_k100 = float(means[(means.cell_K == 100) & (means.window >= 2)]["d_cap_lag1"].mean())
    H1 = bool((worst_k200 >= -0.01) and (cm_k50 >= -0.02) and (cm_k100 >= -0.02))

    # H2: cap >= adaptive05 within +0.01 noise
    h2_sub = means[means.window >= 2]
    h2_fail = h2_sub[h2_sub["d_cap_ad05"] < -0.01]
    H2 = bool(len(h2_fail) == 0)

    # H3: fire fraction monotone non-decreasing in K (Spearman >= 0.8)
    fire = cp[cp.window >= 2].groupby("cell_K")["fire_capaware"].mean()
    fire_05 = cp[cp.window >= 2].groupby("cell_K")["fire_adaptive05"].mean()
    rho_h3, p_h3 = spearmanr(fire.index, fire.values)
    H3 = bool(rho_h3 >= 0.8)

    # H4: cap_aware K=200 cell-mean >= gated by 0.01
    cap_k200 = float(k200["cap_aware"].mean())
    gated_k200 = float(k200["gated"].mean())
    H4 = bool((cap_k200 - gated_k200) >= 0.01)

    summary = {
        "n_rows": int(len(df)),
        "H1_feasibility": {"supported": H1, "worst_K200_dcapfix": worst_k200,
                           "cellmean_K50_dcaplag1": cm_k50,
                           "cellmean_K100_dcaplag1": cm_k100},
        "H2_cap_ge_adaptive05": {"supported": H2, "n_failures": int(len(h2_fail)),
                                  "failures": h2_fail[["cell_K","window","d_cap_ad05"]].to_dict("records")},
        "H3_fire_monotone_in_K": {"supported": H3, "rho": float(rho_h3), "p": float(p_h3),
                                    "fire_capaware_per_K": fire.round(3).to_dict(),
                                    "fire_adaptive05_per_K": fire_05.round(3).to_dict()},
        "H4_cap_beats_gated_K200": {"supported": H4, "cap_K200_mean": cap_k200,
                                      "gated_K200_mean": gated_k200,
                                      "delta": cap_k200 - gated_k200},
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # tab_main
    lines = [
        "\\begin{table*}[!t]",
        "  \\caption{Mean P@50 across 25 evaluation seeds per (K, window) for all six strategies. CP\\textsubscript{cap} marks whether the capacity-aware detector fired at the window using $\\tau_K$.}",
        "  \\label{tab:main}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{cc c cccccc cc}",
        "    \\toprule",
        "    $K$ & W & CP$_{\\text{cap}}$ & fixed & lag1 & ad05 & cap & gated & offline & $\\Delta_{\\text{cap-fix}}$ & $\\Delta_{\\text{cap-lag1}}$ \\\\",
        "    \\midrule",
    ]
    cp_idx = cp.set_index(["cell_K", "window"])
    for K in [50, 100, 200]:
        sub = means[means.cell_K == K].sort_values("window")
        for _, r in sub.iterrows():
            cp_row = cp_idx.loc[(int(r["cell_K"]), int(r["window"]))]
            fired = "$\\bullet$" if cp_row["fire_capaware"] else "$\\circ$"
            lines.append(
                f"    {int(r['cell_K'])} & {int(r['window'])} & {fired} & "
                f"{r['fixed']:.3f} & {r['lag1']:.3f} & {r['adaptive05']:.3f} & "
                f"{r['cap_aware']:.3f} & {r['gated']:.3f} & {r['offline']:.3f} & "
                f"{r['d_cap_fix']:+.3f} & {r['d_cap_lag1']:+.3f} \\\\"
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
        "  \\begin{tabular}{@{}p{0.5cm}p{4.7cm}p{2.1cm}@{}}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & joint feasibility region reached & " + ("Supported" if H1 else "Rejected") + " \\\\",
        f"    H2 & cap $\\geq$ adaptive05 within $+0.01$ & " + ("Supported" if H2 else f"Rejected ({len(h2_fail)})") + " \\\\",
        f"    H3 & Spearman$(K,$ fire$)\\geq +0.8$ & " + ("Supported" if H3 else f"Rejected ($\\rho={rho_h3:.2f}$)") + " \\\\",
        f"    H4 & cap $\\geq$ gated by $+0.01$ at $K=200$ & " + ("Supported" if H4 else f"Rejected ($\\Delta={cap_k200-gated_k200:+.3f}$)") + " \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
