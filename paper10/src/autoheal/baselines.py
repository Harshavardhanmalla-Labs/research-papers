"""Baselines for AutoHeal comparison: human-in-loop + fixed-policy.

Both run the same fleet simulation but bypass parts of AutoHeal's
pipeline. Their roles in the pre-registered hypotheses:
  - Human-in-loop: provides the MTTR reduction baseline (H3) and the
    per-pair dominance comparator (H4).
  - Fixed-policy: provides a no-recalibration comparison.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .framework import (
    _initial_state, _compute_hrs, FIXED_WEIGHTS, HRS_WEIGHTS,
    EPSS_THRESHOLD, HRS_PERCENTILE, WINDOWS, WindowOutcome, AutoHealConfig,
)
from .actuator import simulate_action, ActionOutcome

_REPO = Path(__file__).resolve().parents[3]
for _p in (_REPO / "paper4" / "src", _REPO / "paper5" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from hygieneprio.scorer import HygienePrioScorer  # noqa: E402
from paper5.window_sim import (  # noqa: E402
    applicable_pairs, apply_remediation, update_epss,
    update_telemetry_freshness, disclose_new_cves,
)


# Human-in-loop fixed capacity per Verizon DBIR 43-day MTTR baseline.
HUMAN_CAPACITY = 30


def simulate_human_in_loop(seed: int, cfg: AutoHealConfig) -> list[WindowOutcome]:
    """Human-in-loop baseline: all pairs are REVIEWED, then K_human remediated
    in order of HygienePrio score. No triage classes, no
    auto-rollback safety; humans accept whatever the action returns.
    """
    state = _initial_state(seed, cfg)
    cumulative: set = set()
    disclosure: dict = {}
    rows = []
    for w in range(1, WINDOWS + 1):
        rng = np.random.default_rng((seed, w, 50))
        pairs = applicable_pairs(state)
        n_pairs = len(pairs)
        hrs = _compute_hrs(state)
        pairs_l = pairs.copy()
        pairs_l['_label'] = ((pairs_l['epss_score'] > EPSS_THRESHOLD)
                             & (pairs_l['computer_id'].map(hrs)
                                > hrs.quantile(HRS_PERCENTILE / 100.0))).astype(int)
        ranked = HygienePrioScorer(weights=FIXED_WEIGHTS).rank_pairs(pairs_l, hrs)
        top = ranked.head(HUMAN_CAPACITY)

        successes, rollbacks, deferred = [], [], []
        for _, r in top.iterrows():
            o = simulate_action(rng)
            if o == ActionOutcome.SUCCESS:
                successes.append((r['computer_id'], r['cve_id']))
            elif o == ActionOutcome.ROLLBACK:
                rollbacks.append((r['computer_id'], r['cve_id']))
            else:
                deferred.append((r['computer_id'], r['cve_id']))

        if successes:
            sel = pd.DataFrame(successes, columns=['computer_id', 'cve_id'])
            apply_remediation(state, sel)
            for k in successes:
                cumulative.add(k)
        for k in successes:
            if k not in disclosure:
                disclosure[k] = w
        mttr = [w - disclosure.get(k, w) for k in successes]
        mttr_avg = float(np.mean(mttr)) if mttr else 0.0

        high_epss_now = pairs_l[pairs_l['epss_score'] > 0.5]
        denom = len(cumulative) + len(high_epss_now)
        coverage = (len(cumulative) / denom) if denom > 0 else 1.0
        rb_rate = (len(rollbacks) / len(top)) if len(top) > 0 else 0.0

        rows.append(WindowOutcome(
            cell_K=HUMAN_CAPACITY, seed=seed, window=w,
            n_pairs=n_pairs,
            n_auto=0, n_review=len(top), n_defer=n_pairs - len(top),
            n_acted=len(top), n_success=len(successes), n_rollback=len(rollbacks),
            n_deferred_at_act=len(deferred), rollback_rate=round(rb_rate, 4),
            cascade_detected=False, halt_triggered=False,
            mttr_avg_windows=round(mttr_avg, 3),
            coverage_to_date=round(coverage, 4),
        ))

        if w < WINDOWS:
            disclose_new_cves(state, rng, w, rate=cfg.arrival_rate)
            update_epss(state, rng)
            update_telemetry_freshness(state, set())
    return rows


def simulate_fixed_policy(seed: int, cfg: AutoHealConfig) -> list[WindowOutcome]:
    """Fixed-policy baseline: AutoHeal architecture but without the
    triage step — all top-K pairs by HygienePrio score get acted on
    directly. No triage, no rollback escalation.
    """
    state = _initial_state(seed, cfg)
    cumulative: set = set()
    disclosure: dict = {}
    rows = []
    K = cfg.capacity
    for w in range(1, WINDOWS + 1):
        rng = np.random.default_rng((seed, w, 60))
        pairs = applicable_pairs(state)
        n_pairs = len(pairs)
        hrs = _compute_hrs(state)
        pairs_l = pairs.copy()
        pairs_l['_label'] = ((pairs_l['epss_score'] > EPSS_THRESHOLD)
                             & (pairs_l['computer_id'].map(hrs)
                                > hrs.quantile(HRS_PERCENTILE / 100.0))).astype(int)
        ranked = HygienePrioScorer(weights=FIXED_WEIGHTS).rank_pairs(pairs_l, hrs)
        top = ranked.head(K)

        successes, rollbacks, deferred = [], [], []
        for _, r in top.iterrows():
            o = simulate_action(rng)
            if o == ActionOutcome.SUCCESS:
                successes.append((r['computer_id'], r['cve_id']))
            elif o == ActionOutcome.ROLLBACK:
                rollbacks.append((r['computer_id'], r['cve_id']))
            else:
                deferred.append((r['computer_id'], r['cve_id']))

        if successes:
            sel = pd.DataFrame(successes, columns=['computer_id', 'cve_id'])
            apply_remediation(state, sel)
            for k in successes:
                cumulative.add(k)
        for k in successes:
            if k not in disclosure:
                disclosure[k] = w
        mttr = [w - disclosure.get(k, w) for k in successes]
        mttr_avg = float(np.mean(mttr)) if mttr else 0.0

        high_epss_now = pairs_l[pairs_l['epss_score'] > 0.5]
        denom = len(cumulative) + len(high_epss_now)
        coverage = (len(cumulative) / denom) if denom > 0 else 1.0
        rb_rate = (len(rollbacks) / len(top)) if len(top) > 0 else 0.0

        rows.append(WindowOutcome(
            cell_K=K, seed=seed, window=w,
            n_pairs=n_pairs,
            n_auto=len(top), n_review=0, n_defer=n_pairs - len(top),
            n_acted=len(top), n_success=len(successes), n_rollback=len(rollbacks),
            n_deferred_at_act=len(deferred), rollback_rate=round(rb_rate, 4),
            cascade_detected=False, halt_triggered=False,
            mttr_avg_windows=round(mttr_avg, 3),
            coverage_to_date=round(coverage, 4),
        ))

        if w < WINDOWS:
            disclose_new_cves(state, rng, w, rate=cfg.arrival_rate)
            update_epss(state, rng)
            update_telemetry_freshness(state, set())
    return rows
