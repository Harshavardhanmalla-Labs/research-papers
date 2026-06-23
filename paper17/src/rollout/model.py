"""
Paper 17: ring rollout of script-based endpoint enforcement.

A faulty enforcement script harms every endpoint it has reached when it is detected. A rollout
configuration is a sequence of cumulative deployment fractions ending at 1.0; after each non-final
stage a fault is detected with the canary detection probability and the campaign halts. We estimate
the expected blast radius (fraction of the fleet harmed) by Monte Carlo over faulty campaigns, and
report the convergence cost (soak periods) for each configuration. All constants are pre-registered
in PAPER17_PROTOCOL.md and fixed.
"""

from __future__ import annotations

import numpy as np

# Pre-registered constants (PAPER17_PROTOCOL.md section 3).
FLEET = 10000
FAULT_RATE = 0.05
TRIALS = 4000                       # Monte Carlo faulty campaigns per seed
REF_DETECT = 0.80
EVALUATION_SEEDS = list(range(1100, 1125))

CONFIGS = {
    "big-bang": [1.00],
    "2-ring":   [0.05, 1.00],
    "4-ring":   [0.01, 0.10, 0.50, 1.00],
    "6-ring":   [0.005, 0.02, 0.08, 0.25, 0.60, 1.00],
}
REF_CONFIG = "4-ring"
DETECT_GRID = [0.2, 0.5, 0.8, 0.95]


def expected_blast(cum_fractions, p_detect: float, rng: np.random.Generator,
                   trials: int = TRIALS) -> float:
    """Monte Carlo expected blast radius (fraction of fleet harmed) for a faulty campaign."""
    cum = np.asarray(cum_fractions, dtype=float)
    n_stages = len(cum)
    blasts = np.empty(trials)
    for t in range(trials):
        blast = 1.0                       # never detected before full deployment
        for i in range(n_stages - 1):     # can detect after each non-final stage
            if rng.random() < p_detect:
                blast = cum[i]
                break
        blasts[t] = blast
    return float(blasts.mean())


def convergence_cost(cum_fractions) -> int:
    """Soak periods to full deployment = number of inter-ring stages."""
    return len(cum_fractions) - 1


def evaluate_seed(seed: int) -> list[dict]:
    rows = []
    # Configuration sweep at the reference detection probability.
    for name, cfg in CONFIGS.items():
        rng = np.random.default_rng((seed, hash(name) % 9973, 17))
        eb = expected_blast(cfg, REF_DETECT, rng)
        rows.append({"seed": seed, "axis": "config", "config": name,
                     "p_detect": REF_DETECT, "n_rings": len(cfg),
                     "expected_blast": eb, "convergence_cost": convergence_cost(cfg)})
    # Detection-probability sweep for the reference (four-ring) configuration.
    for p in DETECT_GRID:
        rng = np.random.default_rng((seed, int(p * 100), 18))
        eb = expected_blast(CONFIGS[REF_CONFIG], p, rng)
        rows.append({"seed": seed, "axis": "detect", "config": REF_CONFIG,
                     "p_detect": p, "n_rings": len(CONFIGS[REF_CONFIG]),
                     "expected_blast": eb,
                     "convergence_cost": convergence_cost(CONFIGS[REF_CONFIG])})
    return rows
