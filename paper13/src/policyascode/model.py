"""
Paper 13: CJIS policy-as-code, prevention versus detection.

A fleet of CJI-handling endpoints experiences blockable control violations (arriving as
configuration changes, interceptable by a guardrail and recurring) and emergent violations
(not change-driven, not blockable). We compare a detective regime (detect within a cadence and
auto-remediate every occurrence) against a preventive regime (block blockable violations at
change time, with an imperfect guardrail recall and a false-block cost on benign changes). All
constants are pre-registered in PAPER13_PROTOCOL.md and fixed.
"""

from __future__ import annotations

import numpy as np

# Pre-registered constants (PAPER13_PROTOCOL.md section 3).
N_ENDPOINTS = 500
HORIZON_DAYS = 365
EMERGENT_RATE = 2.0          # emergent violations per endpoint per year (not blockable)
BENIGN_RATE = 180.0          # benign config changes per endpoint per year
BLOCK_RECALL = 0.95          # fraction of blockable violations the guardrail intercepts
FALSE_POS = 0.02             # fraction of benign changes wrongly blocked
DETECT_CADENCE = 1.0
MTTR_DAYS = 1.0
RECURRENCE_GRID = [0.0, 1.0, 3.0, 6.0, 12.0]   # blockable-violation recurrences per year
REF_RECURRENCE = 6.0
EVALUATION_SEEDS = list(range(900, 925))


def _poisson_times(rate_per_year: float, rng: np.random.Generator) -> np.ndarray:
    if rate_per_year <= 0:
        return np.array([])
    lam = rate_per_year / 365.0
    times, t = [], 0.0
    while True:
        t += rng.exponential(1.0 / lam)
        if t >= HORIZON_DAYS:
            break
        times.append(t)
    return np.array(times)


def _noncompliant_days(violation_times: np.ndarray) -> float:
    """Detect each violation at the next daily check, remediate MTTR later; absorb overlaps."""
    nc, t_clear = 0.0, 0.0
    for d in np.sort(violation_times):
        if d < t_clear:
            continue
        det = np.ceil(d / DETECT_CADENCE) * DETECT_CADENCE
        remediated = det + MTTR_DAYS
        nc += (remediated - d)
        t_clear = remediated
    return nc


def evaluate_seed_recurrence(seed: int, recurrence: float) -> dict:
    rng = np.random.default_rng((seed, int(recurrence * 100), 13))
    exp_detect = 0.0
    exp_prevent = 0.0
    exp_blockable_detect = 0.0
    false_blocks = 0
    for e in range(N_ENDPOINTS):
        er = np.random.default_rng((seed, e, 1))
        blockable = _poisson_times(recurrence, er)
        emergent = _poisson_times(EMERGENT_RATE, er)

        # Detective: all violations detected and remediated, every occurrence.
        d_all = _noncompliant_days(np.concatenate([blockable, emergent]))
        d_block = _noncompliant_days(blockable)
        exp_detect += d_all
        exp_blockable_detect += d_block

        # Preventive: guardrail blocks each blockable violation with recall; misses slip through.
        if len(blockable):
            slipped = blockable[er.random(len(blockable)) > BLOCK_RECALL]
        else:
            slipped = blockable
        exp_prevent += _noncompliant_days(np.concatenate([slipped, emergent]))

        # False-block cost on benign changes.
        n_benign = len(_poisson_times(BENIGN_RATE, er))
        false_blocks += int(er.binomial(n_benign, FALSE_POS)) if n_benign else 0

    reduction = (exp_detect - exp_prevent) / exp_detect if exp_detect else 0.0
    blockable_share = exp_blockable_detect / exp_detect if exp_detect else 0.0
    endpoint_months = N_ENDPOINTS * (HORIZON_DAYS / 30.0)
    return {
        "seed": seed, "recurrence": recurrence,
        "exposure_detect": exp_detect, "exposure_prevent": exp_prevent,
        "exposure_saved": exp_detect - exp_prevent,
        "reduction": reduction,
        "blockable_share": blockable_share,
        "ceiling_gap": reduction - blockable_share,
        "false_blocks_per_endpoint_month": false_blocks / endpoint_months,
    }


def evaluate_seed(seed: int) -> list[dict]:
    return [evaluate_seed_recurrence(seed, r) for r in RECURRENCE_GRID]
