#!/usr/bin/env python3
"""
Analyze Paper 15 results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv (seed x overlap); evaluates H1 to H4 against the thresholds locked in
PAPER15_PROTOCOL.md. Verdicts are computed mechanically; no value is hand-set.
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
REF = 0.50
GRID = [0.45, 0.50, 0.55, 0.60, 0.70]


def _ci(series, seed=0):
    m, lo, hi = bca_ci_mean(list(series), n_boot=10_000, seed=seed)
    return {"mean": round(float(m), 4), "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    ref = df[df.overlap == REF]
    s = {"n_eval_seeds": int(df["seed"].nunique()), "by_overlap": {}, "hypotheses": {}}
    for o in GRID:
        sub = df[df.overlap == o]
        s["by_overlap"][str(o)] = {k: round(sub[k].mean(), 4) for k in
                                   ["recall_realtime", "recall_scheduled", "recall_fusion",
                                    "gain_over_best_single", "blind_spot"]}

    # H1: fusion gain over the best single tool >= 0.10 at reference overlap.
    g = _ci(ref["gain_over_best_single"], seed=1)
    s["hypotheses"]["H1"] = {
        "statement": "fusion exceeds the better single tool by >=0.10 recall at reference overlap",
        "gain": g,
        "verdict": "SUPPORTED" if (g["mean"] >= 0.10 and g["ci_lo"] > 0) else (
            "PARTIAL" if g["ci_lo"] > 0 else "NOT_SUPPORTED")}

    # H2: blind spot is a floor on missed vulnerabilities (fusion miss >= blind spot).
    maf = _ci(ref["miss_above_floor"], seed=2)
    s["hypotheses"]["H2"] = {
        "statement": "blind-spot rate is a floor on missed vulnerabilities (fusion miss >= blind spot)",
        "miss_above_floor": maf, "blind_spot": _ci(ref["blind_spot"], seed=21),
        "verdict": "SUPPORTED" if maf["ci_lo"] >= -0.005 else "NOT_SUPPORTED"}

    # H3: fusion gain over the real-time feed equals the scheduled-only-fresh coverage.
    diff = (ref.set_index("seed")["gain_over_realtime"] - ref.set_index("seed")["scheduled_only_fresh"])
    d3 = _ci(diff.to_numpy(), seed=3)
    s["hypotheses"]["H3"] = {
        "statement": "fusion gain over real-time = scheduled-only-fresh coverage",
        "gain_over_realtime": _ci(ref["gain_over_realtime"], seed=31),
        "scheduled_only_fresh": _ci(ref["scheduled_only_fresh"], seed=32),
        "difference": d3,
        "verdict": "SUPPORTED" if abs(d3["mean"]) <= 0.005 and d3["ci_lo"] <= 0 <= d3["ci_hi"]
        else "NOT_SUPPORTED"}

    # H4: gain over best single decreases with overlap.
    means = [df[df.overlap == o]["gain_over_best_single"].mean() for o in GRID]
    monotone = all(means[i + 1] < means[i] for i in range(len(means) - 1))
    lo = df[df.overlap == 0.45].set_index("seed")["gain_over_best_single"]
    hi = df[df.overlap == 0.70].set_index("seed")["gain_over_best_single"]
    idx = lo.index.intersection(hi.index)
    drop = _ci((lo.loc[idx] - hi.loc[idx]).to_numpy(), seed=4)
    s["hypotheses"]["H4"] = {
        "statement": "fusion gain over the best single tool decreases as overlap increases",
        "gain_by_overlap": [round(m, 4) for m in means],
        "drop_low_minus_high_overlap": drop,
        "verdict": "SUPPORTED" if (monotone and drop["ci_lo"] > 0) else "NOT_SUPPORTED"}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(s, f, indent=2)

    print("=" * 60)
    print("Endpoint Telemetry Fusion (Paper 15) verdicts (seeds 1000-1024)")
    print("=" * 60)
    for h, r in s["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print("\ngain by overlap:", s["hypotheses"]["H4"]["gain_by_overlap"])


if __name__ == "__main__":
    main()
