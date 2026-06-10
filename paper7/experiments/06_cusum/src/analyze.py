"""Analyse Paper 13 CUSUM results: H1-H4 + LaTeX tables."""
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
    df = pd.read_csv(RESULTS / "cusum_results.csv")
    cp = pd.read_csv(RESULTS / "changepoint_log.csv")

    means = df.groupby(["cell_K", "window", "strategy"])["p_at_50"].mean().unstack("strategy").reset_index()
    means["d_cu_fix"] = means["cusum"] - means["fixed"]
    means["d_cu_lag1"] = means["cusum"] - means["lag1"]
    means["d_cu_cap"] = means["cusum"] - means["cap_aware"]
    means["d_cu_gated"] = means["cusum"] - means["gated"]
    means.to_csv(RESULTS / "cell_window_means.csv", index=False)

    # H1: feasibility region
    k200 = means[(means.cell_K == 200) & (means.window >= 2)]
    worst_k200 = float(k200["d_cu_fix"].min())
    cm_k50 = float(means[(means.cell_K == 50) & (means.window >= 2)]["d_cu_lag1"].mean())
    cm_k100 = float(means[(means.cell_K == 100) & (means.window >= 2)]["d_cu_lag1"].mean())
    H1 = bool((worst_k200 >= -0.01) and (cm_k50 >= -0.02) and (cm_k100 >= -0.02))

    # H2: cusum K=200 cell mean >= gated K=200 + 0.01
    cusum_k200 = float(k200["cusum"].mean())
    gated_k200 = float(k200["gated"].mean())
    H2 = bool((cusum_k200 - gated_k200) >= 0.01)

    # H3: cusum K=200 fire fraction < cap_aware K=200 fire fraction
    fire_cu_k200 = float(cp[(cp.cell_K == 200) & (cp.window >= 2)]["fire_cusum"].mean())
    fire_cap_k200 = float(cp[(cp.cell_K == 200) & (cp.window >= 2)]["fire_cap"].mean())
    H3 = bool(fire_cu_k200 < fire_cap_k200)

    # H4: cusum K=200 cell mean >= cap_aware K=200 cell mean - 0.01
    cap_k200 = float(k200["cap_aware"].mean())
    H4 = bool((cusum_k200 - cap_k200) >= -0.01)

    fire_cu_per_K = cp[cp.window >= 2].groupby("cell_K")["fire_cusum"].mean().round(3).to_dict()
    fire_cap_per_K = cp[cp.window >= 2].groupby("cell_K")["fire_cap"].mean().round(3).to_dict()

    summary = {
        "n_rows": int(len(df)),
        "H1_feasibility": {"supported": H1, "worst_K200_dcufix": worst_k200,
                           "cellmean_K50_dculag1": cm_k50, "cellmean_K100_dculag1": cm_k100},
        "H2_cusum_beats_gated_K200": {"supported": H2, "cusum_K200": cusum_k200,
                                       "gated_K200": gated_k200, "delta": cusum_k200 - gated_k200},
        "H3_cusum_fires_less_than_cap_K200": {"supported": H3,
                                                "cusum_fire_K200": fire_cu_k200,
                                                "cap_fire_K200": fire_cap_k200},
        "H4_cusum_ge_cap_within_noise": {"supported": H4, "cusum_K200": cusum_k200,
                                          "cap_K200": cap_k200, "delta": cusum_k200 - cap_k200},
        "fire_cusum_per_K": fire_cu_per_K,
        "fire_cap_per_K": fire_cap_per_K,
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # tab_main
    lines = [
        "\\begin{table*}[!t]",
        "  \\caption{Mean P@50 across 25 evaluation seeds per (K, window) for all six strategies. CP$_{\\mathrm{cusum}}$ marks whether CUSUM fired at the window.}",
        "  \\label{tab:main}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{cc c cccccc cc}",
        "    \\toprule",
        "    $K$ & W & CP$_{\\text{cu}}$ & fixed & lag1 & cap & cusum & gated & offline & $\\Delta_{\\text{cu-gated}}$ & $\\Delta_{\\text{cu-cap}}$ \\\\",
        "    \\midrule",
    ]
    cp_idx = cp.set_index(["cell_K", "window"])
    for K in [50, 100, 200]:
        sub = means[means.cell_K == K].sort_values("window")
        for _, r in sub.iterrows():
            cp_row = cp_idx.loc[(int(r["cell_K"]), int(r["window"]))]
            fired = "$\\bullet$" if cp_row["fire_cusum"] else "$\\circ$"
            d_cu_gated = r["cusum"] - r["gated"]
            d_cu_cap = r["cusum"] - r["cap_aware"]
            lines.append(
                f"    {int(r['cell_K'])} & {int(r['window'])} & {fired} & "
                f"{r['fixed']:.3f} & {r['lag1']:.3f} & {r['cap_aware']:.3f} & "
                f"{r['cusum']:.3f} & {r['gated']:.3f} & {r['offline']:.3f} & "
                f"{d_cu_gated:+.3f} & {d_cu_cap:+.3f} \\\\"
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
        f"    H2 & cusum $\\geq$ gated $+0.01$ at $K=200$ & " + ("Supported" if H2 else f"Rejected ($\\Delta={cusum_k200-gated_k200:+.3f}$)") + " \\\\",
        f"    H3 & cusum fires less than cap\\_aware at $K=200$ & " + ("Supported" if H3 else "Rejected") + " \\\\",
        f"    H4 & cusum $\\geq$ cap\\_aware $-0.01$ at $K=200$ & " + ("Supported" if H4 else f"Rejected ($\\Delta={cusum_k200-cap_k200:+.3f}$)") + " \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
