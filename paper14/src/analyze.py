#!/usr/bin/env python3
"""
Analyze Patch Tuesday Triage (Paper 14) results and emit pre-registered verdicts.

Reframed protocol v2: the primary claim is that asset-context weighting drives
disclosure-time emergent-risk prioritization, while the immature day-0 EPSS observation
adds little. Reads primary_results.csv (seed x sigma x method); verdicts are computed
mechanically against the locked thresholds. No value is hand-set.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import bca_ci_mean  # noqa: E402

K_VALUES = [50, 100, 250]
SIGMA_GRID = [0.0, 0.25, 0.50, 0.75, 1.0]
REF_SIGMA = 0.50
RESULTS_DIR = Path(__file__).parent.parent / "results" / "primary_v1"


def _paired(df, a, b, col, sigma, seed=0):
    sub = df[df.sigma == sigma]
    x = sub[sub.method == a].set_index("seed")[col]
    y = sub[sub.method == b].set_index("seed")[col]
    idx = x.index.intersection(y.index)
    d = (x.loc[idx] - y.loc[idx]).to_numpy()
    m, lo, hi = bca_ci_mean(list(d), n_boot=10_000, seed=seed)
    return {"mean": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4), "n": int(len(idx))}


def _mean(df, method, col, sigma, seed=0):
    v = df[(df.sigma == sigma) & (df.method == method)][col]
    m, lo, hi = bca_ci_mean(list(v), n_boot=10_000, seed=seed)
    return {"mean": round(m, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    summary = {"n_eval_seeds": int(df["seed"].nunique()), "ref_sigma": REF_SIGMA,
               "method_means_ref": {}, "hypotheses": {}, "notes": []}

    for m in sorted(df["method"].unique()):
        summary["method_means_ref"][m] = _mean(df, m, "mwp_at_50", REF_SIGMA, seed=1)

    # H1: PTI-full beats context-blind EPSS-day0 by >=5pp MWP@50 at ref sigma.
    h1 = _paired(df, "PTI-full", "EPSS-day0", "mwp_at_50", REF_SIGMA, seed=50)
    summary["hypotheses"]["H1"] = {
        "statement": "context-weighted PTI exceeds context-blind day-0 EPSS by >=5pp (MWP@50, ref sigma)",
        "advantage_pp": round(h1["mean"] * 100, 2), "detail": h1,
        "verdict": "SUPPORTED" if (h1["mean"] >= 0.05 and h1["ci_lo"] > 0) else (
            "PARTIAL" if h1["ci_lo"] > 0 else "NOT_SUPPORTED")}

    # H2: dropping the day-0 observation changes MWP@50 by <=2pp (day-0 EPSS adds little).
    h2 = _paired(df, "PTI-full", "PTI-noObs", "mwp_at_50", REF_SIGMA, seed=2)
    summary["hypotheses"]["H2"] = {
        "statement": "day-0 EPSS observation adds little: |PTI-full - PTI-noObs| <= 2pp (MWP@50)",
        "difference_pp": round(h2["mean"] * 100, 2), "detail": h2,
        "verdict": "SUPPORTED" if abs(h2["mean"]) <= 0.02 else "NOT_SUPPORTED"}

    # H3: removing the context factor erases most of the gain (PTI-noCrit residual over blind <=2pp).
    h3 = _paired(df, "PTI-noCrit", "EPSS-day0", "mwp_at_50", REF_SIGMA, seed=3)
    summary["hypotheses"]["H3"] = {
        "statement": "context drives the gain: context-free predictor residual over blind <= 2pp",
        "residual_pp": round(h3["mean"] * 100, 2), "detail": h3,
        "verdict": "SUPPORTED" if abs(h3["mean"]) <= 0.02 else "NOT_SUPPORTED"}

    # H4: context advantage decays with capacity (K=50 advantage > K=250 advantage).
    a50 = _paired(df, "PTI-full", "EPSS-day0", "mwp_at_50", REF_SIGMA, seed=4)["mean"]
    a250 = _paired(df, "PTI-full", "EPSS-day0", "mwp_at_250", REF_SIGMA, seed=5)["mean"]
    summary["hypotheses"]["H4"] = {
        "statement": "context advantage decays with capacity (adv@K50 > adv@K250)",
        "adv_k50_pp": round(a50 * 100, 2), "adv_k250_pp": round(a250 * 100, 2),
        "verdict": "SUPPORTED" if a50 > a250 else "NOT_SUPPORTED"}

    # Oracle gap context (descriptive): matured-EPSS upper bound vs blind at ref sigma.
    summary["oracle_ref"] = {
        "EPSS-matured-oracle": _mean(df, "EPSS-matured-oracle", "mwp_at_50", REF_SIGMA, seed=6),
        "PTI-full": _mean(df, "PTI-full", "mwp_at_50", REF_SIGMA, seed=7),
        "EPSS-day0": _mean(df, "EPSS-day0", "mwp_at_50", REF_SIGMA, seed=8)}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 62)
    print("Patch Tuesday Triage (Paper 14) pre-registered verdicts (seeds 500-524)")
    print("=" * 62)
    for h, r in summary["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print("\nMWP@50 at ref sigma:",
          {m: summary["method_means_ref"][m]["mean"] for m in
           ["PTI-full", "PTI-noObs", "CAP-day0", "EPSS-matured-oracle", "EPSS-day0", "PTI-noCrit", "CVSS-only"]})


if __name__ == "__main__":
    main()
