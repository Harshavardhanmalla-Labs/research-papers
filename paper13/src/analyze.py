#!/usr/bin/env python3
"""
Analyze Paper 13 results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv (seed x recurrence); evaluates H1 to H4 against the thresholds locked
in PAPER13_PROTOCOL.md. Verdicts are computed mechanically; no value is hand-set.
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
REF = 6.0
GRID = [0.0, 1.0, 3.0, 6.0, 12.0]


def _ci(series, seed=0):
    m, lo, hi = bca_ci_mean(list(series), n_boot=10_000, seed=seed)
    return {"mean": round(float(m), 4), "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    ref = df[df.recurrence == REF]
    s = {"n_eval_seeds": int(df["seed"].nunique()), "by_recurrence": {}, "hypotheses": {}}
    for r in GRID:
        sub = df[df.recurrence == r]
        s["by_recurrence"][str(r)] = {
            "reduction": round(sub["reduction"].mean(), 4),
            "exposure_saved": round(sub["exposure_saved"].mean(), 1),
            "false_blocks_per_endpoint_month": round(sub["false_blocks_per_endpoint_month"].mean(), 4),
        }

    # H1: reduction at reference recurrence >= 0.50.
    red = _ci(ref["reduction"], seed=1)
    s["hypotheses"]["H1"] = {
        "statement": "prevention reduces CJI exposure by >=50% at reference recurrence",
        "reduction": red,
        "verdict": "SUPPORTED" if (red["mean"] >= 0.50 and red["ci_lo"] > 0) else (
            "PARTIAL" if red["ci_lo"] > 0 else "NOT_SUPPORTED")}

    # H2: realized reduction does not exceed blockable-exposure share by > 0.03.
    gap = _ci(ref["ceiling_gap"], seed=2)
    s["hypotheses"]["H2"] = {
        "statement": "exposure reduction <= blockable-exposure share + 0.03 (blockability ceiling)",
        "ceiling_gap": gap, "blockable_share": _ci(ref["blockable_share"], seed=21),
        "verdict": "SUPPORTED" if gap["ci_hi"] <= 0.03 else "NOT_SUPPORTED"}

    # H3: absolute exposure saved grows monotonically with recurrence.
    means = [df[df.recurrence == r]["exposure_saved"].mean() for r in GRID]
    monotone = all(means[i + 1] > means[i] for i in range(len(means) - 1))
    hi = df[df.recurrence == 12.0].set_index("seed")["exposure_saved"]
    lo = df[df.recurrence == 1.0].set_index("seed")["exposure_saved"]
    idx = hi.index.intersection(lo.index)
    grow = _ci((hi.loc[idx] - lo.loc[idx]).to_numpy(), seed=3)
    s["hypotheses"]["H3"] = {
        "statement": "absolute exposure saved grows monotonically with recurrence",
        "exposure_saved_by_recurrence": [round(m, 1) for m in means],
        "saved_r12_minus_r1": grow,
        "verdict": "SUPPORTED" if (monotone and grow["ci_lo"] > 0) else "NOT_SUPPORTED"}

    # H4: false blocks do not trend with recurrence (range across grid small vs mean).
    fb = [df[df.recurrence == r]["false_blocks_per_endpoint_month"].mean() for r in GRID]
    fb_mean = float(np.mean(fb))
    fb_range = float(max(fb) - min(fb))
    s["hypotheses"]["H4"] = {
        "statement": "false blocks per endpoint-month are recurrence-independent",
        "false_blocks_by_recurrence": [round(x, 4) for x in fb],
        "range_over_mean": round(fb_range / fb_mean, 4) if fb_mean else 0.0,
        "benefit_cost_ratio_by_recurrence": [
            round(s["by_recurrence"][str(r)]["exposure_saved"] /
                  (s["by_recurrence"][str(r)]["false_blocks_per_endpoint_month"] * 500 * 365 / 30 + 1e-9), 2)
            for r in GRID],
        "verdict": "SUPPORTED" if (fb_range / fb_mean) < 0.10 else "NOT_SUPPORTED"}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(s, f, indent=2)

    print("=" * 60)
    print("CJIS Policy-as-Code (Paper 13) verdicts (seeds 900-924)")
    print("=" * 60)
    for h, r in s["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print("\nreduction by recurrence:", {r: s["by_recurrence"][str(r)]["reduction"] for r in GRID})
    print("false-blocks by recurrence:", s["hypotheses"]["H4"]["false_blocks_by_recurrence"])


if __name__ == "__main__":
    main()
