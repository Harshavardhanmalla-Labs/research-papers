#!/usr/bin/env python3
"""
Analyze Paper 17 results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv; evaluates H1 to H4 against the thresholds locked in
PAPER17_PROTOCOL.md. Verdicts are computed mechanically; no value is hand-set.
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
CONFIGS = ["big-bang", "2-ring", "4-ring", "6-ring"]
DETECT = [0.2, 0.5, 0.8, 0.95]


def _ci(series, seed=0):
    m, lo, hi = bca_ci_mean(list(series), n_boot=10_000, seed=seed)
    return {"mean": round(float(m), 4), "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    cfgdf = df[df.axis == "config"]
    detdf = df[df.axis == "detect"]
    s = {"n_eval_seeds": int(df["seed"].nunique()), "by_config": {}, "by_detect": {},
         "hypotheses": {}}

    for c in CONFIGS:
        sub = cfgdf[cfgdf.config == c]
        s["by_config"][c] = {"expected_blast": round(sub["expected_blast"].mean(), 4),
                             "convergence_cost": int(sub["convergence_cost"].iloc[0])}
    for p in DETECT:
        sub = detdf[detdf.p_detect == p]
        s["by_detect"][str(p)] = round(sub["expected_blast"].mean(), 4)

    # H1: four-ring reduces expected blast radius by >=80% vs big-bang (blast_bigbang = 1.0).
    red = _ci(1.0 - cfgdf[cfgdf.config == "4-ring"]["expected_blast"], seed=1)
    s["hypotheses"]["H1"] = {
        "statement": "four-ring rollout reduces expected blast radius by >=80% vs big-bang",
        "reduction": red,
        "verdict": "SUPPORTED" if (red["mean"] >= 0.80 and red["ci_lo"] > 0) else (
            "PARTIAL" if red["ci_lo"] > 0 else "NOT_SUPPORTED")}

    # H2: convergence cost equals the number of inter-ring stages (deterministic).
    exact = all(s["by_config"][c]["convergence_cost"] == n for c, n in
                [("big-bang", 0), ("2-ring", 1), ("4-ring", 3), ("6-ring", 5)])
    s["hypotheses"]["H2"] = {
        "statement": "convergence cost = number of inter-ring stages (0,1,3,5)",
        "convergence_costs": {c: s["by_config"][c]["convergence_cost"] for c in CONFIGS},
        "verdict": "SUPPORTED" if exact else "NOT_SUPPORTED"}

    # H3: expected blast radius rises as detection probability falls.
    blasts = [s["by_detect"][str(p)] for p in DETECT]   # p ascending
    monotone = all(blasts[i] > blasts[i + 1] for i in range(len(blasts) - 1))
    s["hypotheses"]["H3"] = {
        "statement": "expected blast radius rises monotonically as detection probability falls",
        "blast_by_detect_ascending_p": blasts,
        "verdict": "SUPPORTED" if monotone else "NOT_SUPPORTED"}

    # H4: more rings reduce blast (monotone) with diminishing marginal reduction.
    eb = [s["by_config"][c]["expected_blast"] for c in CONFIGS]   # bigbang..6-ring
    monotone_down = all(eb[i] > eb[i + 1] for i in range(len(eb) - 1))
    # marginal reduction per added ring (relative to big-bang) should diminish
    reductions = [1.0 - x for x in eb]                  # cumulative reduction
    marginals = [reductions[i + 1] - reductions[i] for i in range(len(reductions) - 1)]
    diminishing = all(marginals[i] >= marginals[i + 1] - 1e-6 for i in range(len(marginals) - 1))
    s["hypotheses"]["H4"] = {
        "statement": "finer ring staging reduces blast radius with diminishing marginal returns",
        "expected_blast_by_config": eb, "marginal_reductions": [round(m, 4) for m in marginals],
        "verdict": "SUPPORTED" if (monotone_down and diminishing) else "NOT_SUPPORTED"}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(s, f, indent=2)

    print("=" * 60)
    print("Ring Rollout Blast Radius (Paper 17) verdicts (seeds 1100-1124)")
    print("=" * 60)
    for h, r in s["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print("\nblast by config:", {c: s["by_config"][c]["expected_blast"] for c in CONFIGS})
    print("blast by detect:", s["by_detect"])


if __name__ == "__main__":
    main()
