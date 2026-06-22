"""
Paper 15: fusing a real-time and a scheduled endpoint feed for vulnerability visibility.

Each asset is covered by the real-time feed, the scheduled feed, both, or neither. The real-time
feed is always fresh where it covers; the scheduled feed is fresh a fraction of the time. A
current vulnerability is detected by a feed if it covers the asset and is fresh. We measure
detection recall for the real-time feed alone, the scheduled feed alone, and their fusion
(freshest-wins union), across an overlap sweep. All constants are pre-registered in
PAPER15_PROTOCOL.md and fixed.
"""

from __future__ import annotations

import numpy as np

# Pre-registered constants (PAPER15_PROTOCOL.md section 3).
N_ASSETS = 5000
COV_REALTIME = 0.75          # marginal coverage of the real-time feed
COV_SCHEDULED = 0.70         # marginal coverage of the scheduled feed
SCHED_FRESH = 0.60           # fraction of scheduled-feed reports that are fresh
VULN_PREVALENCE = 0.30
OVERLAP_GRID = [0.45, 0.50, 0.55, 0.60, 0.70]   # P(both tools)
REF_OVERLAP = 0.50
EVALUATION_SEEDS = list(range(1000, 1025))


def _class_probs(p_both: float):
    """Probabilities for {both, realtime_only, scheduled_only, neither}."""
    rt_only = COV_REALTIME - p_both
    sc_only = COV_SCHEDULED - p_both
    neither = 1.0 - (p_both + rt_only + sc_only)
    return p_both, rt_only, sc_only, neither


def evaluate_seed_overlap(seed: int, p_both: float) -> dict:
    rng = np.random.default_rng((seed, int(p_both * 100), 15))
    both, rt_only, sc_only, neither = _class_probs(p_both)
    klass = rng.choice([0, 1, 2, 3], size=N_ASSETS, p=[both, rt_only, sc_only, neither])
    covered_rt = (klass == 0) | (klass == 1)
    covered_sc = (klass == 0) | (klass == 2)
    sched_fresh = covered_sc & (rng.random(N_ASSETS) < SCHED_FRESH)

    # Restrict to assets carrying a true current vulnerability (recall is over these).
    has_vuln = rng.random(N_ASSETS) < VULN_PREVALENCE
    v = has_vuln
    n_v = int(v.sum())
    if n_v == 0:
        return {}

    det_rt = covered_rt & v
    det_sc = sched_fresh & v
    det_fusion = (covered_rt | sched_fresh) & v

    recall_rt = det_rt.sum() / n_v
    recall_sc = det_sc.sum() / n_v
    recall_fusion = det_fusion.sum() / n_v
    coverage_union = ((covered_rt | covered_sc) & v).sum() / n_v
    blind_spot = 1.0 - coverage_union
    # Fusion gain over the real-time feed = scheduled-only-and-fresh coverage of vuln assets.
    sched_only_fresh = ((klass == 2) & sched_fresh & v).sum() / n_v

    return {
        "seed": seed, "overlap": p_both,
        "recall_realtime": recall_rt, "recall_scheduled": recall_sc,
        "recall_fusion": recall_fusion,
        "gain_over_best_single": recall_fusion - max(recall_rt, recall_sc),
        "gain_over_realtime": recall_fusion - recall_rt,
        "scheduled_only_fresh": sched_only_fresh,
        "coverage_union": coverage_union, "blind_spot": blind_spot,
        "fusion_miss": 1.0 - recall_fusion,
        "miss_above_floor": (1.0 - recall_fusion) - blind_spot,
    }


def evaluate_seed(seed: int) -> list[dict]:
    return [evaluate_seed_overlap(seed, p) for p in OVERLAP_GRID]
