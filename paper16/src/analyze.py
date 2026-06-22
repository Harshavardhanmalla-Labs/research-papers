#!/usr/bin/env python3
"""
Analyze Paper 16 results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv (seed x condition x detector); evaluates H1 to H4 against the
thresholds locked in PAPER16_PROTOCOL.md. Verdicts are computed mechanically from the frozen
data; no value is hand-set.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import bca_ci_mean  # noqa: E402

RESULTS_DIR = Path(__file__).parent.parent / "results" / "primary_v1"
RULES = ["Rule-Max", "Rule-Count"]
JOINT = ["Mahalanobis", "IsolationForest", "OneClassSVM", "LocalOutlierFactor"]


def _mean(df, cond, det, seed=0):
    v = df[(df.condition == cond) & (df.detector == det)]["ap"]
    m, lo, hi = bca_ci_mean(list(v), n_boot=10_000, seed=seed)
    return {"mean": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}


def _paired(df, cond, det_a, det_b, seed=0):
    a = df[(df.condition == cond) & (df.detector == det_a)].set_index("seed")["ap"]
    b = df[(df.condition == cond) & (df.detector == det_b)].set_index("seed")["ap"]
    idx = a.index.intersection(b.index)
    m, lo, hi = bca_ci_mean(list((a.loc[idx] - b.loc[idx]).to_numpy()), n_boot=10_000, seed=seed)
    return {"mean": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4), "n": int(len(idx))}


def _best(df, cond, dets, seed=0):
    means = {d: _mean(df, cond, d, seed)["mean"] for d in dets}
    return max(means, key=means.get)


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    summary = {"n_eval_seeds": int(df["seed"].nunique()),
               "cell_means": {}, "hypotheses": {}}

    for cond in ["SDA", "CDA", "Mixed"]:
        summary["cell_means"][cond] = {d: _mean(df, cond, d, seed=1)["mean"]
                                       for d in RULES + JOINT}

    # H1: best joint beats best rule on CDA by >= 0.10.
    bj_cda, br_cda = _best(df, "CDA", JOINT, 1), _best(df, "CDA", RULES, 1)
    h1 = _paired(df, "CDA", bj_cda, br_cda, seed=1)
    summary["hypotheses"]["H1"] = {
        "statement": "best joint detector beats best rule on cross-dimensional anomalies by >=0.10 AP",
        "best_joint": bj_cda, "best_rule": br_cda, "delta": h1,
        "verdict": "SUPPORTED" if (h1["mean"] >= 0.10 and h1["ci_lo"] > 0) else (
            "PARTIAL" if h1["ci_lo"] > 0 else "NOT_SUPPORTED")}

    # H2: on SDA, rule not beaten by joint by more than 0.05.
    bj_sda, br_sda = _best(df, "SDA", JOINT, 2), _best(df, "SDA", RULES, 2)
    h2 = _paired(df, "SDA", bj_sda, br_sda, seed=2)
    summary["hypotheses"]["H2"] = {
        "statement": "on single-dimension anomalies, joint advantage over rule <= 0.05 AP",
        "best_joint": bj_sda, "best_rule": br_sda, "joint_minus_rule": h2,
        "verdict": "SUPPORTED" if h2["mean"] <= 0.05 else "NOT_SUPPORTED"}

    # H3: on CDA, best joint beats the structure-blind Rule-Count with CI excluding 0.
    h3 = _paired(df, "CDA", bj_cda, "Rule-Count", seed=3)
    summary["hypotheses"]["H3"] = {
        "statement": "cross-dimensional gain needs joint modeling (best joint > Rule-Count, CDA)",
        "delta_vs_rulecount": h3,
        "verdict": "SUPPORTED" if h3["ci_lo"] > 0 else "NOT_SUPPORTED"}

    # H4: on Mixed, best joint beats best rule, by less than the CDA-only margin.
    bj_mix, br_mix = _best(df, "Mixed", JOINT, 4), _best(df, "Mixed", RULES, 4)
    h4 = _paired(df, "Mixed", bj_mix, br_mix, seed=4)
    summary["hypotheses"]["H4"] = {
        "statement": "on a mixture, best joint beats best rule but by less than the CDA-only margin",
        "best_joint": bj_mix, "best_rule": br_mix, "delta": h4,
        "cda_margin": h1["mean"],
        "verdict": "SUPPORTED" if (h4["ci_lo"] > 0 and h4["mean"] < h1["mean"]) else (
            "PARTIAL" if h4["ci_lo"] > 0 else "NOT_SUPPORTED")}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 60)
    print("Hygiene Anomaly Detection (Paper 16) verdicts (seeds 700-724)")
    print("=" * 60)
    for h, r in summary["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print("\nCDA: best joint", bj_cda, summary['cell_means']['CDA'][bj_cda],
          "| best rule", br_cda, summary['cell_means']['CDA'][br_cda])
    print("SDA: best rule", br_sda, summary['cell_means']['SDA'][br_sda])


if __name__ == "__main__":
    main()
