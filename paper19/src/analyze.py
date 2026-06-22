#!/usr/bin/env python3
"""
Analyze Paper 19 results and emit pre-registered hypothesis verdicts.

Reads primary_results.csv; evaluates H1 to H4 against the thresholds locked in
PAPER19_PROTOCOL.md. Verdicts are computed mechanically; no value is hand-set.
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
RETIRE = [7, 14, 30, 60, 120]
PRECISION = [0.80, 0.90, 0.95, 0.99]


def _ci(series, seed=0):
    m, lo, hi = bca_ci_mean(list(series), n_boot=10_000, seed=seed)
    return {"mean": round(float(m), 4), "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)}


def main() -> None:
    df = pd.read_csv(RESULTS_DIR / "primary_results.csv")
    reg = df[df.axis == "regime"]
    ret = df[df.axis == "retire"]
    prec = df[df.axis == "precision"]
    s = {"n_eval_seeds": int(df["seed"].nunique()), "regime": {}, "sweeps": {}, "hypotheses": {}}

    for name in ["continuous", "periodic"]:
        sub = reg[reg.regime == name]
        s["regime"][name] = {"ghost": round(sub["ghost_rate"].mean(), 4),
                             "phantom": round(sub["phantom_rate"].mean(), 4),
                             "total": round(sub["total_error"].mean(), 4)}
    s["sweeps"]["retire"] = {str(r): {"ghost": round(ret[ret.retire == r]["ghost_rate"].mean(), 4),
                                      "phantom": round(ret[ret.retire == r]["phantom_rate"].mean(), 4),
                                      "total": round(ret[ret.retire == r]["total_error"].mean(), 4)}
                             for r in RETIRE}
    s["sweeps"]["precision_total"] = {str(p): round(prec[prec.precision == p]["total_error"].mean(), 4)
                                      for p in PRECISION}

    # H1: continuous reduces total error vs periodic by >=30%.
    cont = reg[reg.regime == "continuous"].set_index("seed")["total_error"]
    per = reg[reg.regime == "periodic"].set_index("seed")["total_error"]
    idx = cont.index.intersection(per.index)
    red = _ci(1.0 - cont.loc[idx].to_numpy() / per.loc[idx].to_numpy(), seed=1)
    s["hypotheses"]["H1"] = {
        "statement": "continuous reconciliation reduces total CMDB error by >=30% vs quarterly",
        "reduction": red,
        "verdict": "SUPPORTED" if (red["mean"] >= 0.30 and red["ci_lo"] > 0) else (
            "PARTIAL" if red["ci_lo"] > 0 else "NOT_SUPPORTED")}

    # H2: ghost falls and phantom rises with retirement threshold; interior minimum.
    ghosts = [s["sweeps"]["retire"][str(r)]["ghost"] for r in RETIRE]
    phantoms = [s["sweeps"]["retire"][str(r)]["phantom"] for r in RETIRE]
    totals = [s["sweeps"]["retire"][str(r)]["total"] for r in RETIRE]
    ghost_falls = all(ghosts[i] >= ghosts[i + 1] - 1e-9 for i in range(len(ghosts) - 1))
    phantom_rises = all(phantoms[i] <= phantoms[i + 1] + 1e-9 for i in range(len(phantoms) - 1))
    interior_min = 0 < int(np.argmin(totals)) < len(totals) - 1
    s["hypotheses"]["H2"] = {
        "statement": "retirement threshold trades ghosts for phantoms; interior total-error minimum",
        "ghost_by_retire": ghosts, "phantom_by_retire": phantoms, "total_by_retire": totals,
        "argmin_retire": RETIRE[int(np.argmin(totals))],
        "verdict": "SUPPORTED" if (ghost_falls and phantom_rises and interior_min) else "NOT_SUPPORTED"}

    # H3: minimum total error falls as matching precision rises (floor ~ 1 - precision).
    pt = [s["sweeps"]["precision_total"][str(p)] for p in PRECISION]
    falls = all(pt[i] > pt[i + 1] for i in range(len(pt) - 1))
    s["hypotheses"]["H3"] = {
        "statement": "total error falls as matching precision rises (matching-precision floor)",
        "total_by_precision": pt,
        "dup_floor_proxy": round(pt[0] - pt[-1], 4),
        "verdict": "SUPPORTED" if falls else "NOT_SUPPORTED"}

    # H4: cost-weighted optimal retirement threshold shifts with the ghost:phantom cost ratio.
    def argmin_weighted(w_ghost, w_phantom):
        per_seed_arg = []
        for seed in df["seed"].unique():
            sub = ret[ret.seed == seed]
            costs = {r: (w_ghost * sub[sub.retire == r]["ghost_rate"].mean()
                         + w_phantom * sub[sub.retire == r]["phantom_rate"].mean()) for r in RETIRE}
            per_seed_arg.append(min(costs, key=costs.get))
        return float(np.mean(per_seed_arg))

    opt_security = argmin_weighted(5.0, 1.0)   # ghosts (security) weighted more
    opt_balanced = argmin_weighted(1.0, 1.0)
    opt_cost = argmin_weighted(1.0, 5.0)       # phantoms (cost) weighted more
    s["hypotheses"]["H4"] = {
        "statement": "optimal retirement threshold shifts with the ghost:phantom cost ratio",
        "mean_optimal_retire": {"security_5to1": round(opt_security, 1),
                                "balanced_1to1": round(opt_balanced, 1),
                                "cost_1to5": round(opt_cost, 1)},
        "verdict": "SUPPORTED" if (opt_security > opt_balanced > opt_cost) else (
            "PARTIAL" if opt_security > opt_cost else "NOT_SUPPORTED")}

    with open(RESULTS_DIR / "hypothesis_summary.json", "w") as f:
        json.dump(s, f, indent=2)

    print("=" * 60)
    print("Self-Healing CMDB (Paper 19) verdicts (seeds 1300-1324)")
    print("=" * 60)
    for h, r in s["hypotheses"].items():
        print(f"{h}: {r['verdict']}  | {r['statement']}")
    print("\nregime:", s["regime"])
    print("H4 optimal retire:", s["hypotheses"]["H4"]["mean_optimal_retire"])


if __name__ == "__main__":
    main()
