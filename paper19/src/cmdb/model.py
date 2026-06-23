"""
Paper 19: two-sided CMDB error under reconciliation.

Each asset has an exponential lifetime; a discovery scan every reconciliation cadence observes a
live asset with observability probability. A CMDB record is created on first observation and
retired after the retirement threshold of non-observation; each observation matches to the existing
record with the matching precision, otherwise creates a duplicate. We measure the ghost rate
(live assets with no record) and the phantom rate (records with no live asset, including
duplicates) by per-asset Monte Carlo. All constants are pre-registered in PAPER19_PROTOCOL.md.
"""

from __future__ import annotations

import numpy as np

# Pre-registered constants (PAPER19_PROTOCOL.md section 3).
MEAN_LIFETIME = 365.0
QUIET_FRACTION = 0.30          # fraction of assets that are intermittently observable
OBS_NORMAL = 0.90              # per-scan observability of a normal asset
OBS_QUIET = 0.15               # per-scan observability of a quiet asset
N_ASSETS = 2500                # Monte Carlo assets per seed
PERIODIC_CADENCE = 90
CONTINUOUS_CADENCE = 1
REF_RETIRE = 30
REF_PRECISION = 0.95
RETIRE_GRID = [7, 14, 30, 60, 120]
PRECISION_GRID = [0.80, 0.90, 0.95, 0.99]
EVALUATION_SEEDS = list(range(1300, 1325))


def _simulate_asset(rng, cadence, retire, precision):
    """One asset's timeline. Returns (alive_days, ghost_days, phantom_record_days)."""
    death = rng.exponential(MEAN_LIFETIME)
    p_obs = OBS_QUIET if rng.random() < QUIET_FRACTION else OBS_NORMAL
    last_scan = death + retire + 2 * cadence
    scans = np.arange(cadence, last_scan + cadence, cadence)
    observed = (scans <= death) & (rng.random(len(scans)) < p_obs)   # observed only while alive

    # Primary record: active intervals; duplicates self-heal at the next observation (next scan
    # that re-matches), so a duplicate persists about one inter-observation interval, cadence/p_obs.
    primary_intervals = []      # (create_time, retire_time)
    dup_days = 0.0
    rec_open = None
    last_match = None
    for i, s in enumerate(scans):
        if observed[i]:
            if rec_open is None:
                rec_open = s; last_match = s              # create / re-create primary record
            elif rng.random() < precision:
                last_match = s                            # match success: refresh primary
            else:
                dup_days += cadence / p_obs               # match failure: duplicate until next obs
        if rec_open is not None and (s - last_match) > retire:
            primary_intervals.append((rec_open, last_match + retire))
            rec_open = None; last_match = None
    if rec_open is not None:
        primary_intervals.append((rec_open, last_match + retire))

    # Ghost days: alive time [0, death] with no active primary record.
    covered = 0.0
    for (a, b) in primary_intervals:
        lo, hi = max(0.0, a), min(death, b)
        if hi > lo:
            covered += (hi - lo)
    ghost_days = max(0.0, death - covered)

    # Phantom record-days: primary record time after death (record outlives asset) + duplicates.
    phantom_days = dup_days
    for (a, b) in primary_intervals:
        if b > death:
            phantom_days += (b - max(a, death))
    return death, ghost_days, phantom_days


def evaluate_cell(seed: int, cadence: int, retire: int, precision: float) -> dict:
    rng = np.random.default_rng((seed, cadence, retire, int(precision * 100)))
    alive = ghost = phantom = 0.0
    for _ in range(N_ASSETS):
        a, g, p = _simulate_asset(rng, cadence, retire, precision)
        alive += a; ghost += g; phantom += p
    ghost_rate = ghost / alive
    phantom_rate = phantom / alive
    return {"ghost_rate": ghost_rate, "phantom_rate": phantom_rate,
            "total_error": ghost_rate + phantom_rate}


def evaluate_seed(seed: int) -> list[dict]:
    rows = []
    # Reference: continuous vs periodic at reference retire/precision.
    for name, cad in [("continuous", CONTINUOUS_CADENCE), ("periodic", PERIODIC_CADENCE)]:
        c = evaluate_cell(seed, cad, REF_RETIRE, REF_PRECISION)
        rows.append({"seed": seed, "axis": "regime", "regime": name, **c})
    # Retirement-threshold sweep (continuous, reference precision) for the tradeoff frontier.
    for r in RETIRE_GRID:
        c = evaluate_cell(seed, CONTINUOUS_CADENCE, r, REF_PRECISION)
        rows.append({"seed": seed, "axis": "retire", "retire": r, **c})
    # Matching-precision sweep (continuous, reference retire) for the floor.
    for pm in PRECISION_GRID:
        c = evaluate_cell(seed, CONTINUOUS_CADENCE, REF_RETIRE, pm)
        rows.append({"seed": seed, "axis": "precision", "precision": pm, **c})
    return rows
