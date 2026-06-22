#!/usr/bin/env python3
"""
Analyze CAP-G (Paper 11) results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv + homogeneous_control.csv, computes per-method means with
BCa 95% CIs, evaluates H1-H4 and the RQ5 ablation against the thresholds locked in
PAPER11_PROTOCOL.md §3/§8, and writes hypothesis_summary.json + cell_means.csv.

Verdicts are computed mechanically from the frozen data, no value is hand-entered.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from capg.metrics import bca_ci_mean  # noqa: E402

K_VALUES = [50, 100, 250]
RESULTS_DIR = Path(__file__).parent.parent / "results" / "primary_v1"

# Pre-registered thresholds (§3, §8).
H1_THRESHOLD = 0.05      # mean Δ MWP@K over K must reach this
H1_NULL = 0.02           # below this across all K -> declared null
H3_TOLERANCE = 0.01      # homogeneous advantage must stay within this
H4_TOLERANCE = 0.01      # CAP-G Pblind may exceed HygienePrio by at most this


def _mean_ci(values, seed=0):
    m, lo, hi = bca_ci_mean(list(values), n_boot=10_000, seed=seed)
    return {"mean": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}


def _paired_delta_ci(df, method_a, method_b, col, seed=0):
    """Per-seed paired difference (method_a - method_b) on `col`, with BCa CI."""
    a = df[df.method == method_a].set_index("seed")[col]
    b = df[df.method == method_b].set_index("seed")[col]
    common = a.index.intersection(b.index)
    deltas = (a.loc[common] - b.loc[common]).to_numpy()
    m, lo, hi = bca_ci_mean(list(deltas), n_boot=10_000, seed=seed)
    return {"mean": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
            "n": int(len(common))}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    df_hom = pd.read_csv(RESULTS_DIR / "homogeneous_control.csv")

    methods = df["method"].unique().tolist()
    summary = {"n_eval_seeds": int(df["seed"].nunique()), "methods": methods,
               "cell_means": {}, "hypotheses": {}, "ablation": {}, "notes": []}

    # --- Per-method cell means (MWP, Pblind, CWER, NDCG) with CIs ---
    cell_rows = []
    for method in methods:
        sub = df[df.method == method]
        summary["cell_means"][method] = {}
        for k in K_VALUES:
            for metric in ["mwp", "pblind", "cwer", "ndcg"]:
                col = f"{metric}_at_{k}"
                ci = _mean_ci(sub[col], seed=k)
                summary["cell_means"][method][col] = ci
                cell_rows.append({"method": method, "k": k, "metric": metric, **ci})
    pd.DataFrame(cell_rows).to_csv(RESULTS_DIR / "cell_means.csv", index=False)

    CAPG, HP = "CAP-G-full", "HygienePrio"

    # --- H1: mean MWP@K advantage >= 5pp averaged over K ---
    deltas_by_k = {k: _paired_delta_ci(df, CAPG, HP, f"mwp_at_{k}", seed=k)
                   for k in K_VALUES}
    mean_delta = float(np.mean([deltas_by_k[k]["mean"] for k in K_VALUES]))
    all_below_null = all(deltas_by_k[k]["mean"] < H1_NULL for k in K_VALUES)
    h1_supported = (mean_delta >= H1_THRESHOLD) and all(
        deltas_by_k[k]["ci_lo"] > 0 for k in K_VALUES)
    summary["hypotheses"]["H1"] = {
        "statement": "CAP-G-full MWP@K exceeds HygienePrio by >=5pp averaged over K",
        "delta_by_k": deltas_by_k,
        "mean_delta_pp": round(mean_delta * 100, 2),
        "threshold_pp": H1_THRESHOLD * 100,
        "verdict": "SUPPORTED" if h1_supported else (
            "NULL" if all_below_null else "PARTIAL"),
    }

    # --- H2: advantage decreases monotonically in K ---
    d = [deltas_by_k[k]["mean"] for k in K_VALUES]
    h2_mono = d[0] > d[1] > d[2]
    summary["hypotheses"]["H2"] = {
        "statement": "MWP@K advantage decreases monotonically in K (d50>d100>d250)",
        "delta_50": round(d[0], 4), "delta_100": round(d[1], 4),
        "delta_250": round(d[2], 4),
        "verdict": "SUPPORTED" if h2_mono else "NOT_SUPPORTED",
    }

    # --- H3: homogeneous-fleet advantage collapses to within 1pp at K=50 ---
    hom_delta = _paired_delta_ci(df_hom, CAPG, HP, "mwp_at_50", seed=50)
    h3_supported = abs(hom_delta["mean"]) <= H3_TOLERANCE
    summary["hypotheses"]["H3"] = {
        "statement": "On a homogeneous fleet, |MWP@50 advantage| <= 1pp (mechanism test)",
        "homogeneous_delta_50": hom_delta,
        "het_delta_50": deltas_by_k[50],
        "verdict": "SUPPORTED" if h3_supported else "FALSIFIED",
    }

    # --- H4: CAP-G does not beat HygienePrio on context-blind P@50 ---
    blind_delta = _paired_delta_ci(df, CAPG, HP, "pblind_at_50", seed=51)
    h4_supported = blind_delta["mean"] <= H4_TOLERANCE
    summary["hypotheses"]["H4"] = {
        "statement": "CAP-G context-blind P@50 <= HygienePrio + 1pp (honest tradeoff)",
        "blind_delta_50": blind_delta,
        "verdict": "SUPPORTED" if h4_supported else "VIOLATED_INVESTIGATE",
    }
    if not h4_supported:
        summary["notes"].append(
            "H4 violation: CAP-G beats HygienePrio on BOTH metrics. Per protocol §8, "
            "audit MCTP ground-truth construction for circularity before reporting H1.")

    # --- RQ5 ablation: marginal contribution of each context dimension at MWP@50 ---
    for abl, dim in [("CAP-G-noCrit", "criticality"),
                     ("CAP-G-noZone", "zone"),
                     ("CAP-G-noSens", "sensitivity")]:
        if abl in methods:
            drop = _paired_delta_ci(df, CAPG, abl, "mwp_at_50", seed=60)
            summary["ablation"][dim] = {"mwp50_drop_when_removed": drop}
    if summary["ablation"]:
        ranked = sorted(summary["ablation"].items(),
                        key=lambda kv: kv[1]["mwp50_drop_when_removed"]["mean"],
                        reverse=True)
        summary["ablation"]["largest_marginal_contribution"] = ranked[0][0]

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # --- Console report ---
    print("=" * 64)
    print("CAP-G (Paper 11), pre-registered hypothesis verdicts")
    print("=" * 64)
    for h, rec in summary["hypotheses"].items():
        print(f"{h}: {rec['verdict']}")
        print(f"    {rec['statement']}")
    if summary["ablation"]:
        print(f"Largest context contribution: "
              f"{summary['ablation'].get('largest_marginal_contribution')}")
    for n in summary["notes"]:
        print(f"NOTE: {n}")
    print(f"\nWrote hypothesis_summary.json + cell_means.csv to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
