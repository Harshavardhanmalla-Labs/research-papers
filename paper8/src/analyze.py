"""Analyse Paper 9 self_traj_results.csv: trajectory effects + hypotheses."""
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
    df = pd.read_csv(RESULTS / "self_traj_results.csv")
    print(f"Loaded {len(df)} rows.")

    # Per-(K, driver, scorer, window) cell mean
    means = df.groupby(["cell_K", "driver", "scorer", "window"])["p_at_50"].mean().reset_index()
    means.to_csv(RESULTS / "cell_means.csv", index=False)

    # W6 grid: rows=scorer, cols=driver, per K
    K200_w6 = means[(means.cell_K == 200) & (means.window == 6)].pivot(
        index="scorer", columns="driver", values="p_at_50")
    K50_w6 = means[(means.cell_K == 50) & (means.window == 6)].pivot(
        index="scorer", columns="driver", values="p_at_50")

    print("=== K=50 W6 P@50 grid (rows=scorer, cols=driver) ===")
    print(K50_w6.round(3))
    print()
    print("=== K=200 W6 P@50 grid (rows=scorer, cols=driver) ===")
    print(K200_w6.round(3))

    # Trajectory effect per scorer (W6 P@50 max - min across drivers)
    traj_K50 = (K50_w6.max(axis=1) - K50_w6.min(axis=1)).round(3)
    traj_K200 = (K200_w6.max(axis=1) - K200_w6.min(axis=1)).round(3)

    # H1: HP-full W6 on T_{m'} within 0.05 of T_{HP} for at least one m'
    hp_w6_K200 = K200_w6.loc["HygienePrio-full"]
    hp_self_K200 = float(hp_w6_K200["HygienePrio-full"])
    hp_other_K200 = {k: float(v) for k, v in hp_w6_K200.items() if k != "HygienePrio-full"}
    h1_within = {k: abs(v - hp_self_K200) <= 0.05 for k, v in hp_other_K200.items()}
    H1 = any(h1_within.values())

    # H2: EPSS W6 on T_EPSS < EPSS W6 on T_HP at K=50
    epss_w6_K50_T_epss = float(K50_w6.loc["EPSS-only", "EPSS-only"])
    epss_w6_K50_T_hp = float(K50_w6.loc["EPSS-only", "HygienePrio-full"])
    H2 = epss_w6_K50_T_epss < epss_w6_K50_T_hp

    # H3: per-pair dominance HP > EPSS under T_EPSS
    def per_pair_dom(K: int, driver: str) -> float:
        sub = df[(df.cell_K == K) & (df.driver == driver)]
        # group by (seed, window), check if HP > EPSS
        pivot = sub.pivot_table(index=["seed", "window"], columns="scorer",
                                 values="p_at_50", aggfunc="first")
        return float((pivot["HygienePrio-full"] > pivot["EPSS-only"]).mean())

    dom_K50_Tepss = per_pair_dom(50, "EPSS-only")
    dom_K200_Tepss = per_pair_dom(200, "EPSS-only")
    H3 = (dom_K50_Tepss >= 0.75) and (dom_K200_Tepss >= 0.50)

    # Also compute dominance across all (K, driver) for the table
    dom_table = {}
    for K in (50, 200):
        for d in ("HygienePrio-full", "EPSS-only", "HRS-only", "CVSS-only", "Random"):
            dom_table[(K, d)] = per_pair_dom(K, d)

    summary = {
        "n_rows": int(len(df)),
        "H1_collapse_intrinsic": {
            "supported": bool(H1),
            "HP_W6_T_HP_K200": hp_self_K200,
            "HP_W6_T_other_K200": hp_other_K200,
            "within_005_per_driver": h1_within,
        },
        "H2_EPSS_self_decay_K50": {
            "supported": bool(H2),
            "EPSS_W6_T_EPSS_K50": epss_w6_K50_T_epss,
            "EPSS_W6_T_HP_K50": epss_w6_K50_T_hp,
        },
        "H3_HP_dominates_under_T_EPSS": {
            "supported": bool(H3),
            "dom_K50_T_EPSS": dom_K50_Tepss,
            "dom_K200_T_EPSS": dom_K200_Tepss,
        },
        "W6_trajectory_effect_per_scorer_K50": traj_K50.to_dict(),
        "W6_trajectory_effect_per_scorer_K200": traj_K200.to_dict(),
        "HP_per_pair_dominance_table": {f"K{k}__{d}": v for (k, d), v in dom_table.items()},
        "W6_grid_K50": K50_w6.round(4).to_dict(),
        "W6_grid_K200": K200_w6.round(4).to_dict(),
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # LaTeX table 1: W6 grids (K=50 and K=200 stacked)
    drivers = ["HygienePrio-full", "EPSS-only", "HRS-only", "CVSS-only", "Random"]
    short = {"HygienePrio-full": "HP", "EPSS-only": "EPSS", "HRS-only": "HRS",
             "CVSS-only": "CVSS", "Random": "Rand"}
    lines = [
        "\\begin{table*}[!t]",
        "  \\caption{Window-6 mean P@50 per (scoring method, driving method) cell. Rows = scoring method, columns = trajectory-driving method. Diagonals (italics) are each method's self-trajectory P@50; HP-full column shows the Papers~5--8 baseline.}",
        "  \\label{tab:w6grid}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{5pt}",
        "  \\begin{tabular}{l " + "c" * len(drivers) + " c}",
        "    \\toprule",
        "    \\textbf{scorer} \\textbackslash{} \\textbf{driver}",
        "    & " + " & ".join(short[d] for d in drivers) + " & range \\\\",
        "    \\midrule",
        "    \\multicolumn{" + str(len(drivers) + 2) + "}{l}{\\textit{K = 50}} \\\\",
    ]
    for s in drivers:
        row_vals = K50_w6.loc[s]
        rng = row_vals.max() - row_vals.min()
        cells = []
        for d in drivers:
            v = float(row_vals[d])
            cells.append(f"\\textit{{{v:.3f}}}" if d == s else f"{v:.3f}")
        lines.append(f"    {short[s]} & " + " & ".join(cells) + f" & {rng:.3f} \\\\")
    lines.append("    \\midrule")
    lines.append("    \\multicolumn{" + str(len(drivers) + 2) + "}{l}{\\textit{K = 200}} \\\\")
    for s in drivers:
        row_vals = K200_w6.loc[s]
        rng = row_vals.max() - row_vals.min()
        cells = []
        for d in drivers:
            v = float(row_vals[d])
            cells.append(f"\\textit{{{v:.3f}}}" if d == s else f"{v:.3f}")
        lines.append(f"    {short[s]} & " + " & ".join(cells) + f" & {rng:.3f} \\\\")
    lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table*}"]
    (TABLES / "tab_w6grid.tex").write_text("\n".join(lines) + "\n")

    # LaTeX table 2: HP per-pair dominance over EPSS across (K, driver)
    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Per-pair dominance fraction $\\Pr[\\mathrm{HP}>\\mathrm{EPSS}]$ over 150 (seed, window) pairs per (K, driver).}",
        "  \\label{tab:dom}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{5pt}",
        "  \\begin{tabular}{lcc}",
        "    \\toprule",
        "    driver & $K=50$ & $K=200$ \\\\",
        "    \\midrule",
    ]
    for d in drivers:
        v50 = dom_table[(50, d)]
        v200 = dom_table[(200, d)]
        lines.append(f"    {short[d]} & {v50:.3f} & {v200:.3f} \\\\")
    lines += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}"]
    (TABLES / "tab_dom.tex").write_text("\n".join(lines) + "\n")

    # LaTeX table 3: hypothesis outcomes
    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Pre-registered hypothesis outcomes.}",
        "  \\label{tab:hypotheses}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{@{}p{0.5cm}p{4.8cm}p{2.2cm}@{}}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & HP W6 collapse at $K=200$ within $\\pm 0.05$ on $\\geq 1$ non-HP driver & {'Supported' if H1 else 'Rejected'} \\\\",
        f"    H2 & EPSS W6 on $T_{{\\mathrm{{EPSS}}}}<$ on $T_{{\\mathrm{{HP}}}}$ at $K=50$ & {'Supported' if H2 else 'Rejected'} \\\\",
        f"    H3 & $\\Pr[\\mathrm{{HP}}>\\mathrm{{EPSS}}]\\geq\\{{0.75,0.50\\}}$ under $T_{{\\mathrm{{EPSS}}}}$ & {'Supported' if H3 else 'Rejected'} \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("W6_grid_K50", "W6_grid_K200")},
                     indent=2, default=float))


if __name__ == "__main__":
    main()
