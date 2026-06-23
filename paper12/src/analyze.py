#!/usr/bin/env python3
"""
Analyze Paper 12 results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv (one row per seed); evaluates H1 to H4 against the thresholds locked
in PAPER12_PROTOCOL.md. Verdicts are computed mechanically; no value is hand-set.
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


def _ci(series, seed=0):
    m, lo, hi = bca_ci_mean(list(series), n_boot=10_000, seed=seed)
    return {"mean": round(float(m), 4), "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    s = {"n_eval_seeds": int(len(df)), "summary": {}, "hypotheses": {}}
    for c in ["automatable_fraction", "mttd_auto_annual", "mttd_auto_continuous",
              "reduction_vs_annual", "automatable_exposure_share",
              "days_saved_vs_annual", "days_saved_vs_quarter", "top_quartile_capture"]:
        s["summary"][c] = _ci(df[c], seed=hash(c) % 97)

    # H1: MTTD reduction on automatable controls >= 10x.
    ratio = _ci(df["mttd_auto_ratio"], seed=1)
    s["hypotheses"]["H1"] = {
        "statement": "continuous reduces MTTD on automatable controls by >=10x vs annual",
        "mttd_ratio": ratio,
        "verdict": "SUPPORTED" if ratio["ci_lo"] >= 10 else (
            "PARTIAL" if ratio["mean"] >= 10 else "NOT_SUPPORTED")}

    # H2: realized exposure reduction does not exceed automatable-exposure share by > 0.03.
    gap = _ci(df["ceiling_gap"], seed=2)
    s["hypotheses"]["H2"] = {
        "statement": "exposure reduction <= automatable-exposure share + 0.03 (automatability ceiling)",
        "ceiling_gap": gap,
        "reduction": _ci(df["reduction_vs_annual"], seed=21),
        "ceiling": _ci(df["automatable_exposure_share"], seed=22),
        "verdict": "SUPPORTED" if gap["ci_hi"] <= 0.03 else "NOT_SUPPORTED"}

    # H3: absolute days saved vs quarterly < vs annual (per seed), CI of the difference < 0.
    diff = (df["days_saved_vs_quarter"] - df["days_saved_vs_annual"])
    d3 = _ci(diff, seed=3)
    s["hypotheses"]["H3"] = {
        "statement": "absolute control-days saved is smaller vs quarterly than vs annual",
        "days_saved_annual": _ci(df["days_saved_vs_annual"], seed=31),
        "days_saved_quarter": _ci(df["days_saved_vs_quarter"], seed=32),
        "difference_quarter_minus_annual": d3,
        "verdict": "SUPPORTED" if d3["ci_hi"] < 0 else "NOT_SUPPORTED"}

    # H4: top-drift quartile captures >= 70% of achievable reduction.
    cap = _ci(df["top_quartile_capture"], seed=4)
    s["hypotheses"]["H4"] = {
        "statement": "automating the top-drift quartile captures >=70% of achievable reduction",
        "capture": cap,
        "verdict": "SUPPORTED" if cap["ci_lo"] >= 0.70 else (
            "PARTIAL" if cap["mean"] >= 0.70 else "NOT_SUPPORTED")}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(s, f, indent=2)

    print("=" * 60)
    print("Compliance as Code (Paper 12) verdicts (seeds 800-824)")
    print("=" * 60)
    for h, r in s["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print(f"\nMTTD on automatable controls: annual {s['summary']['mttd_auto_annual']['mean']:.1f}d "
          f"-> continuous {s['summary']['mttd_auto_continuous']['mean']:.1f}d")
    print(f"Exposure reduction {s['summary']['reduction_vs_annual']['mean']:.3f} "
          f"vs ceiling {s['summary']['automatable_exposure_share']['mean']:.3f}")


if __name__ == "__main__":
    main()
