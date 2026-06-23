#!/usr/bin/env python3
"""
Analyze Paper 18 results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv; evaluates H1 to H4 against the thresholds locked in
PAPER18_PROTOCOL.md. Verdicts are computed mechanically; no value is hand-set.
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
COVERAGE = [0.3, 0.5, 0.7, 0.9]
CADENCE = [1, 7, 30, 90]
INTERVALS = [365, 180, 90, 30]


def _ci(series, seed=0):
    m, lo, hi = bca_ci_mean(list(series), n_boot=10_000, seed=seed)
    return {"mean": round(float(m), 4), "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    ref = df[df.axis == "reference"]
    s = {"n_eval_seeds": int(df["seed"].nunique()), "reference": {}, "sweeps": {}, "hypotheses": {}}
    s["reference"] = {"rec_random_annual": _ci(ref["rec_random_annual"], 9),
                      "rec_random_chaos": _ci(ref["rec_random_chaos"], 10),
                      "gain": _ci(ref["gain"], 11)}
    s["sweeps"]["coverage_gain"] = {str(c): round(df[(df.axis == "coverage") & (df.coverage == c)]["gain"].mean(), 4) for c in COVERAGE}
    s["sweeps"]["cadence_gain"] = {str(c): round(df[(df.axis == "cadence") & (df.cadence == c)]["gain"].mean(), 4) for c in CADENCE}
    s["sweeps"]["drill_illusion"] = {str(i): round(df[(df.axis == "drill_interval") & (df.interval == i)]["illusion"].mean(), 4) for i in INTERVALS}

    # H1: chaos raises at-random recovery by >= 0.10 at reference.
    g = _ci(ref["gain"], seed=1)
    s["hypotheses"]["H1"] = {
        "statement": "continuous chaos raises at-random recovery by >=0.10 vs annual drills",
        "gain": g,
        "verdict": "SUPPORTED" if (g["mean"] >= 0.10 and g["ci_lo"] > 0) else (
            "PARTIAL" if g["ci_lo"] > 0 else "NOT_SUPPORTED")}

    # H2: realized gain <= perfect-freshness coverage ceiling; and gain rises with coverage.
    gap = _ci(ref["ceiling_gap"], seed=2)
    cov_gains = [s["sweeps"]["coverage_gain"][str(c)] for c in COVERAGE]
    cov_monotone = all(cov_gains[i] < cov_gains[i + 1] for i in range(len(cov_gains) - 1))
    s["hypotheses"]["H2"] = {
        "statement": "gain is bounded by the coverage ceiling and rises with coverage",
        "ceiling_gap": gap, "coverage_gains": cov_gains,
        "verdict": "SUPPORTED" if (gap["ci_hi"] <= 0.005 and cov_monotone) else "NOT_SUPPORTED"}

    # H3: gain saturates as cadence tightens (diminishing marginal gain per tightening step).
    cad_gain = [s["sweeps"]["cadence_gain"][str(c)] for c in [90, 30, 7, 1]]  # loose -> tight
    marg = [cad_gain[i + 1] - cad_gain[i] for i in range(len(cad_gain) - 1)]
    diminishing = all(marg[i] >= marg[i + 1] - 1e-6 for i in range(len(marg) - 1)) and all(m >= -1e-6 for m in marg)
    s["hypotheses"]["H3"] = {
        "statement": "gain saturates as chaos cadence tightens (diminishing marginal gain)",
        "gain_by_cadence_loose_to_tight": cad_gain, "marginal_gains": [round(m, 4) for m in marg],
        "verdict": "SUPPORTED" if diminishing else "NOT_SUPPORTED"}

    # H4: drill illusion (at-drill minus at-random) grows with the drill interval.
    illus = [s["sweeps"]["drill_illusion"][str(i)] for i in [30, 90, 180, 365]]  # short -> long
    grows = all(illus[i] < illus[i + 1] for i in range(len(illus) - 1))
    annual_illusion = _ci(ref["drill_illusion_annual"], seed=4)
    s["hypotheses"]["H4"] = {
        "statement": "the drill illusion grows with the drill interval (annual overstates recovery)",
        "illusion_short_to_long": illus, "annual_illusion": annual_illusion,
        "verdict": "SUPPORTED" if grows else "NOT_SUPPORTED"}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(s, f, indent=2)

    print("=" * 60)
    print("Drill Illusion / Chaos Testing (Paper 18) verdicts (seeds 1200-1224)")
    print("=" * 60)
    for h, r in s["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print(f"\nReference recovery: annual {s['reference']['rec_random_annual']['mean']:.3f} -> "
          f"chaos {s['reference']['rec_random_chaos']['mean']:.3f}")
    print("Drill illusion by interval:", s["sweeps"]["drill_illusion"])


if __name__ == "__main__":
    main()
