"""
Paper 18: latent failover-defect decay and chaos-testing recovery confidence.

Each failover mode accumulates latent defects as a Poisson process; a validation clears them.
Annual drills validate every mode yearly; continuous chaos validates the covered modes far more
often. A disaster strikes a random mode, and failover succeeds if that mode is healthy at the
disaster time. We measure recovery success at a random disaster time versus at drill time. All
constants are pre-registered in PAPER18_PROTOCOL.md and fixed.
"""

from __future__ import annotations

import numpy as np

# Pre-registered constants (PAPER18_PROTOCOL.md section 3).
N_MODES = 12
N_FRAGILE = 4
FRAGILE_RATE = 3.0          # latent defects per year (fragile modes)
ROBUST_RATE = 0.3           # latent defects per year (robust modes)
HORIZON_DAYS = 3650         # 10 years for a stable estimate
ANNUAL = 365
REF_CHAOS_CADENCE = 7
REF_COVERAGE = 0.70
COVERAGE_GRID = [0.3, 0.5, 0.7, 0.9]
CADENCE_GRID = [1, 7, 30, 90]
EVALUATION_SEEDS = list(range(1200, 1225))


def _mode_rates(rng):
    rates = np.full(N_MODES, ROBUST_RATE)
    frag = rng.choice(N_MODES, size=N_FRAGILE, replace=False)
    rates[frag] = FRAGILE_RATE
    return rates


def _validation_times(cadence: int) -> np.ndarray:
    return np.arange(cadence, HORIZON_DAYS + cadence, cadence, dtype=float)


def _frac_defective(defects: np.ndarray, cadence: int) -> float:
    """Fraction of the horizon a mode is in a latent-defect state, computed as the union of
    defective intervals. A mode is defective from the first defect after a validation until the
    next validation; defects within one window share a single clearing time (no double counting).
    """
    if len(defects) == 0:
        return 0.0
    vt = _validation_times(cadence)
    clear = vt[np.searchsorted(vt, defects, side="left")]   # next validation at or after defect
    order = np.argsort(clear, kind="mergesort")
    clear_s, def_s = clear[order], defects[order]
    total, i, n = 0.0, 0, len(clear_s)
    while i < n:
        j = i
        while j < n and clear_s[j] == clear_s[i]:
            j += 1
        total += clear_s[i] - def_s[i:j].min()              # window: earliest defect to validation
        i = j
    return min(total, HORIZON_DAYS) / HORIZON_DAYS


def evaluate_seed(seed: int) -> list[dict]:
    rng = np.random.default_rng((seed, 18))
    rates = _mode_rates(rng)
    # Generate each mode's latent-defect timeline ONCE; reuse across all regimes so that only the
    # validation schedule differs between comparisons.
    defects = []
    for m in range(N_MODES):
        mr = np.random.default_rng((seed, m, 7))
        n = mr.poisson(rates[m] / 365.0 * HORIZON_DAYS)
        defects.append(np.sort(mr.uniform(0, HORIZON_DAYS, n)))

    order = np.argsort(-rates)              # most fragile modes first (chaos covers these first)
    rows = []

    def at_random_recovery(coverage: float, chaos_cadence: int) -> float:
        n_cov = int(round(coverage * N_MODES))
        covered = set(order[:n_cov].tolist())
        fd = [_frac_defective(defects[m], chaos_cadence if m in covered else ANNUAL)
              for m in range(N_MODES)]
        return 1.0 - float(np.mean(fd))

    annual_fd = [_frac_defective(defects[m], ANNUAL) for m in range(N_MODES)]
    rec_random_annual = 1.0 - float(np.mean(annual_fd))
    rec_random_chaos = at_random_recovery(REF_COVERAGE, REF_CHAOS_CADENCE)
    # H2 ceiling: gain if covered modes were perfectly fresh (zero defective time).
    n_cov = int(round(REF_COVERAGE * N_MODES))
    covered = set(order[:n_cov].tolist())
    fd_ceiling = [0.0 if m in covered else annual_fd[m] for m in range(N_MODES)]
    gain_ceiling = (1.0 - float(np.mean(fd_ceiling))) - rec_random_annual
    rows.append({"seed": seed, "axis": "reference",
                 "rec_random_annual": rec_random_annual,
                 "rec_random_chaos": rec_random_chaos,
                 "gain": rec_random_chaos - rec_random_annual,
                 "gain_ceiling": gain_ceiling,
                 "ceiling_gap": (rec_random_chaos - rec_random_annual) - gain_ceiling,
                 "drill_illusion_annual": 1.0 - rec_random_annual})

    for c in COVERAGE_GRID:
        rr = at_random_recovery(c, REF_CHAOS_CADENCE)
        rows.append({"seed": seed, "axis": "coverage", "coverage": c,
                     "rec_random_chaos": rr, "gain": rr - rec_random_annual})

    for cad in CADENCE_GRID:
        rr = at_random_recovery(REF_COVERAGE, cad)
        rows.append({"seed": seed, "axis": "cadence", "cadence": cad,
                     "rec_random_chaos": rr, "gain": rr - rec_random_annual})

    # Drill-illusion sweep: no chaos, vary the drill interval for all modes.
    for interval in [365, 180, 90, 30]:
        at_random = 1.0 - float(np.mean([_frac_defective(defects[m], interval)
                                         for m in range(N_MODES)]))
        rows.append({"seed": seed, "axis": "drill_interval", "interval": interval,
                     "rec_random": at_random, "rec_drill": 1.0, "illusion": 1.0 - at_random})
    return rows
