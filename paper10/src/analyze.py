"""Analyse Paper 10 AutoHeal results: H1-H4 outcomes + LaTeX tables."""
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
    df = pd.read_csv(RESULTS / "autoheal_results.csv")
    print(f"Loaded {len(df)} rows.")

    autoheal = df[df.strategy == "AutoHeal"]
    human    = df[df.strategy == "Human-in-loop"]
    fixed    = df[df.strategy == "Fixed-policy"]

    # H1 — Coverage at end of W6 at K in {50, 100}
    h1_cells = {}
    h1_supported = True
    for K in [50, 100]:
        cell = autoheal[(autoheal.cell_K == K) & (autoheal.window == 6)]
        cov_mean = float(cell.coverage_to_date.mean())
        h1_cells[K] = round(cov_mean, 4)
        if cov_mean < 0.80:
            h1_supported = False

    # H2 — rollback rate <= 5% at every (cell, seed, window)
    h2_failures = autoheal[autoheal.rollback_rate > 0.05]
    h2_supported = len(h2_failures) == 0
    h2_max_rate = float(autoheal.rollback_rate.max())

    # H3 — MTTR reduction (cell-mean ratio <= 0.5) at K in {50, 100}
    h3_cells = {}
    h3_supported = True
    for K in [50, 100]:
        ah_mttr = float(autoheal[autoheal.cell_K == K].mttr_avg_windows.mean())
        # Human-in-loop's cell_K column is hard-coded to 30; pull all
        hi_mttr = float(human.mttr_avg_windows.mean())
        ratio = ah_mttr / hi_mttr if hi_mttr > 0 else float("inf")
        h3_cells[K] = {"ah_mttr": round(ah_mttr, 3),
                       "hi_mttr": round(hi_mttr, 3),
                       "ratio": round(ratio, 3)}
        if ratio > 0.5:
            h3_supported = False

    # H4 — per-window coverage dominance fraction >= 0.80 at K in {50, 100}
    h4_cells = {}
    h4_supported = True
    for K in [50, 100]:
        ah_K = autoheal[autoheal.cell_K == K]
        hi_K = human  # cell_K=30 unique
        # Match by (seed, window) and compare coverage
        dom_pairs = 0
        tot_pairs = 0
        for s in sorted(ah_K.seed.unique()):
            ah_s = ah_K[ah_K.seed == s].drop_duplicates("window").set_index("window")["coverage_to_date"]
            hi_s = hi_K[hi_K.seed == s].drop_duplicates("window").set_index("window")["coverage_to_date"]
            for w in ah_s.index:
                if w in hi_s.index:
                    tot_pairs += 1
                    if float(ah_s.loc[w]) > float(hi_s.loc[w]):
                        dom_pairs += 1
        frac = (dom_pairs / tot_pairs) if tot_pairs else 0.0
        h4_cells[K] = {"dom": dom_pairs, "tot": tot_pairs, "frac": round(frac, 4)}
        if frac < 0.80:
            h4_supported = False

    # Halt counts
    halt_count = int(autoheal.halt_triggered.sum())
    cascade_count = int(autoheal.cascade_detected.sum())

    summary = {
        "n_rows": int(len(df)),
        "H1_coverage": {"supported": h1_supported, "cell_means_W6": h1_cells},
        "H2_safety":   {"supported": h2_supported,
                        "max_rollback_rate": round(h2_max_rate, 4),
                        "n_failures": int(len(h2_failures))},
        "H3_mttr_reduction": {"supported": h3_supported, "cells": h3_cells},
        "H4_dominance": {"supported": h4_supported, "cells": h4_cells},
        "halt_triggered_total":    halt_count,
        "cascade_detected_total":  cascade_count,
    }
    with open(RESULTS / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # tab_hypotheses
    h1 = "Supported" if h1_supported else f"Rejected (W6 cov K=50/100 = {h1_cells[50]:.2f}/{h1_cells[100]:.2f})"
    h2 = "Supported" if h2_supported else f"Rejected ({len(h2_failures)} fails; max {h2_max_rate*100:.1f}\\%)"
    if h3_supported:
        h3 = "Supported"
    else:
        ratios = ", ".join(f"K{K}={h3_cells[K]['ratio']:.2f}" for K in (50, 100))
        h3 = f"Rejected ({ratios})"
    if h4_supported:
        h4 = "Supported"
    else:
        fracs = ", ".join(f"K{K}={h4_cells[K]['frac']*100:.0f}\\%" for K in (50, 100))
        h4 = f"Rejected ({fracs})"

    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Pre-registered hypothesis outcomes.}",
        "  \\label{tab:hypotheses}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{@{}p{0.5cm}p{4.0cm}p{3.0cm}@{}}",
        "    \\toprule",
        "    \\textbf{ID} & \\textbf{Decision rule} & \\textbf{Outcome} \\\\",
        "    \\midrule",
        f"    H1 & Coverage $\\geq 0.80$ at W6, $K\\in\\{{50,100\\}}$ & {h1} \\\\",
        f"    H2 & Rollback rate $\\leq 5\\%$ everywhere & {h2} \\\\",
        f"    H3 & MTTR ratio $\\leq 0.5$ vs.\\ HIL, $K\\in\\{{50,100\\}}$ & {h3} \\\\",
        f"    H4 & Coverage dominance $\\geq 80\\%$, $K\\leq 100$ & {h4} \\\\",
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_hypotheses.tex").write_text("\n".join(lines) + "\n")

    # tab_summary: per-K W12 means
    lines = [
        "\\begin{table}[!t]",
        "  \\caption{Cell-mean outcomes at W12 by strategy and capacity.}",
        "  \\label{tab:summary}",
        "  \\centering",
        "  \\small",
        "  \\setlength{\\tabcolsep}{3pt}",
        "  \\begin{tabular}{@{}lcccc@{}}",
        "    \\toprule",
        "    \\textbf{Strategy/K} & \\textbf{Cov} & \\textbf{Rb \\%} & \\textbf{MTTR} & \\textbf{Halts} \\\\",
        "    \\midrule",
    ]
    for strat in ("AutoHeal", "Fixed-policy"):
        for K in [50, 100, 200]:
            sub = df[(df.strategy == strat) & (df.cell_K == K) & (df.window == 12)]
            ah_all = df[(df.strategy == strat) & (df.cell_K == K)]
            n_halts = int(ah_all.halt_triggered.sum())
            cov   = float(sub.coverage_to_date.mean())
            rb    = float(ah_all.rollback_rate.mean()) * 100
            mttr  = float(ah_all.mttr_avg_windows.mean())
            lines.append(f"    {strat} $K{{=}}{K}$ & {cov:.3f} & {rb:.2f} & {mttr:.2f} & {n_halts} \\\\")
    sub = human[human.window == 12]
    cov_h  = float(sub.coverage_to_date.mean())
    rb_h   = float(human.rollback_rate.mean()) * 100
    mttr_h = float(human.mttr_avg_windows.mean())
    lines.append(f"    Human-in-loop & {cov_h:.3f} & {rb_h:.2f} & {mttr_h:.2f} & 0 \\\\")
    lines += [
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    (TABLES / "tab_summary.tex").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
