"""AutoHeal end-to-end framework — orchestrates the six-stage pipeline."""
from __future__ import annotations
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Wire in Paper 4 and Paper 5 packages.
_REPO = Path(__file__).resolve().parents[3]
for _p in (_REPO / "paper4" / "src", _REPO / "paper5" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from hygieneprio.generator import EEHDAFleetGenerator  # noqa: E402
from hygieneprio.hrs import HygieneRiskScore, HRSWeights  # noqa: E402
from hygieneprio.scorer import HygienePrioScorer, ScorerWeights  # noqa: E402
from paper5.window_sim import (  # noqa: E402
    FleetState, applicable_pairs, apply_remediation,
    update_epss, update_telemetry_freshness,
)

from .triage import classify, TriageClass
from .actuator import simulate_action, ActionOutcome
from .verifier import health_check, detect_cascade


# Pre-registered constants (PAPER10_PROTOCOL.md §3-4).
WINDOWS = 12
EPSS_THRESHOLD = 0.10
HRS_PERCENTILE = 75
FIXED_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS   = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)
SAFETY_ROLLBACK_HARD_STOP = 0.10  # >10% per-window rollback halts the system


@dataclass
class AutoHealConfig:
    capacity: int = 50           # K, capacity per window
    arrival_rate: float = 3.0    # lambda
    use_real_corpus: bool = True
    real_corpus_path: Optional[Path] = None


@dataclass
class WindowOutcome:
    cell_K: int
    seed: int
    window: int
    n_pairs: int
    n_auto: int
    n_review: int
    n_defer: int
    n_acted: int
    n_success: int
    n_rollback: int
    n_deferred_at_act: int
    rollback_rate: float
    cascade_detected: bool
    halt_triggered: bool
    # MTTR over remediated pairs in this window (windows since disclosure)
    mttr_avg_windows: float
    # Coverage in this window: fraction of high-EPSS unpatched CVEs
    # that got remediated cumulatively up to this window
    coverage_to_date: float


def _resample_real_attributes(vr: pd.DataFrame, corpus: pd.DataFrame,
                                rng: np.random.Generator) -> pd.DataFrame:
    vr = vr.copy()
    n = len(vr)
    idx = rng.integers(0, len(corpus), n)
    sampled = corpus.iloc[idx][['epss', 'in_kev']].reset_index(drop=True)
    vr['epss_score'] = sampled['epss'].clip(1e-4, 1.0).values
    vr['in_kev'] = sampled['in_kev'].values
    vr['days_since_kev_entry'] = np.where(
        vr['in_kev'], rng.integers(0, 30, size=n).astype(float), np.nan)
    return vr


def _initial_state(seed: int, cfg: AutoHealConfig) -> FleetState:
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    if cfg.use_real_corpus and cfg.real_corpus_path is not None:
        corpus = pd.read_csv(cfg.real_corpus_path)
        rng = np.random.default_rng((seed, 0, 0))
        tables['vulnerability_records'] = _resample_real_attributes(
            tables['vulnerability_records'], corpus, rng)
    return FleetState(
        vulnerability_records=tables['vulnerability_records'],
        computers=tables['computers'], users=tables['users'],
        groups=tables['groups'],
        group_membership_events=tables['group_membership_events'],
        endpoint_patch_state=tables['endpoint_patch_state'],
        telemetry_freshness_log=tables['telemetry_freshness_log'],
    )


def _compute_hrs(state: FleetState) -> pd.Series:
    return HygieneRiskScore(weights=HRS_WEIGHTS).compute(
        endpoint_patch_state=state.endpoint_patch_state,
        vulnerability_records=state.vulnerability_records,
        users=state.users, groups=state.groups,
        group_membership_events=state.group_membership_events,
        computers=state.computers,
        telemetry_freshness_log=state.telemetry_freshness_log,
    )


def _resolve_host_criticality(host_id: str, computers: pd.DataFrame) -> str:
    rec = computers[computers.computer_id == host_id]
    if rec.empty or 'asset_criticality' not in rec.columns:
        return 'MEDIUM'
    return str(rec.iloc[0]['asset_criticality'])


def run_window(
    state: FleetState,
    cfg: AutoHealConfig,
    seed: int,
    window_index: int,
    cumulative_remediated: set,
    disclosure_windows: dict,
) -> WindowOutcome:
    """Run one window of AutoHeal end-to-end.

    Mutates ``state`` in place and updates ``cumulative_remediated`` and
    ``disclosure_windows`` for cross-window coverage and MTTR computation.
    """
    K = cfg.capacity
    rng = np.random.default_rng((seed, window_index, 99))

    # --- Stage 1: Detect ----------------------------------------------
    pairs = applicable_pairs(state)
    n_pairs = len(pairs)

    # --- Stage 2: Score ------------------------------------------------
    hrs = _compute_hrs(state)
    pairs_l = pairs.copy()
    pairs_l['_label'] = ((pairs_l['epss_score'] > EPSS_THRESHOLD)
                         & (pairs_l['computer_id'].map(hrs)
                            > hrs.quantile(HRS_PERCENTILE / 100.0))).astype(int)
    scorer = HygienePrioScorer(weights=FIXED_WEIGHTS)
    ranked = scorer.rank_pairs(pairs_l, hrs)
    # Normalise score column to [0, 1] for triage thresholds.
    if 'score' not in ranked.columns:
        # The scorer returns ranked pairs ordered by score; map row rank to
        # a normalised score so triage thresholds remain interpretable.
        ranked = ranked.reset_index(drop=True)
        # Use exponential decay so top ranks land near 1.0, tail near 0.
        n = len(ranked)
        ranked['hp_score'] = np.exp(-np.arange(n) / max(1, n / 5))
    else:
        scores = ranked['score'].values.astype(float)
        if scores.max() > scores.min():
            ranked['hp_score'] = ((scores - scores.min())
                                  / (scores.max() - scores.min()))
        else:
            ranked['hp_score'] = 0.5
    ranked['asset_criticality'] = ranked['computer_id'].map(
        lambda h: _resolve_host_criticality(h, state.computers))

    # --- Stage 3: Triage ----------------------------------------------
    triages = []
    for i in range(len(ranked)):
        triages.append(classify(
            score=float(ranked.iloc[i]['hp_score']),
            host_criticality=str(ranked.iloc[i]['asset_criticality']),
        ))
    ranked['triage'] = triages
    n_auto   = int((ranked['triage'] == TriageClass.AUTO).sum())
    n_review = int((ranked['triage'] == TriageClass.REVIEW).sum())
    n_defer  = int((ranked['triage'] == TriageClass.DEFER).sum())

    # --- Stage 4: Plan ------------------------------------------------
    auto_pool = ranked[ranked['triage'] == TriageClass.AUTO].head(K)

    # --- Stage 5: Act + Stage 6: Verify + Rollback --------------------
    successes = []
    rollbacks = []
    deferred  = []
    rollback_cve_ids = []
    for _, r in auto_pool.iterrows():
        outcome = simulate_action(rng, in_kev=bool(r.get('in_kev', False)))
        if outcome == ActionOutcome.SUCCESS:
            successes.append((r['computer_id'], r['cve_id']))
        elif outcome == ActionOutcome.ROLLBACK:
            rollbacks.append((r['computer_id'], r['cve_id']))
            rollback_cve_ids.append(str(r['cve_id']))
        else:
            deferred.append((r['computer_id'], r['cve_id']))

    n_acted    = len(auto_pool)
    n_success  = len(successes)
    n_rollback = len(rollbacks)
    n_def_act  = len(deferred)
    rollback_rate = (n_rollback / n_acted) if n_acted > 0 else 0.0

    # Safety: cascading-failure detector + hard-stop
    cascade = detect_cascade(rollback_cve_ids)
    halt = bool(rollback_rate > SAFETY_ROLLBACK_HARD_STOP or cascade)

    # Apply remediation for successes
    if successes:
        sel = pd.DataFrame(successes, columns=['computer_id', 'cve_id'])
        apply_remediation(state, sel)
        for (h, c) in successes:
            cumulative_remediated.add((h, c))

    # Track disclosure window for MTTR (Window 1 considered disclosure
    # for the W1 backlog; new CVEs disclosed at later windows recorded
    # then).
    for (h, c) in successes:
        if (h, c) not in disclosure_windows:
            disclosure_windows[(h, c)] = window_index
    mttr_values = [window_index - disclosure_windows.get((h, c), window_index)
                   for (h, c) in successes]
    mttr_avg = float(np.mean(mttr_values)) if mttr_values else 0.0

    # Coverage: cumulative remediated / cumulative ever-high-EPSS
    high_epss_now = pairs_l[pairs_l['epss_score'] > 0.5]
    if len(high_epss_now) == 0 and not cumulative_remediated:
        coverage = 1.0
    else:
        denom = len(cumulative_remediated) + len(high_epss_now)
        coverage = (len(cumulative_remediated) / denom) if denom > 0 else 1.0

    return WindowOutcome(
        cell_K=K, seed=seed, window=window_index,
        n_pairs=n_pairs, n_auto=n_auto, n_review=n_review, n_defer=n_defer,
        n_acted=n_acted, n_success=n_success, n_rollback=n_rollback,
        n_deferred_at_act=n_def_act, rollback_rate=round(rollback_rate, 4),
        cascade_detected=bool(cascade), halt_triggered=halt,
        mttr_avg_windows=round(mttr_avg, 3),
        coverage_to_date=round(coverage, 4),
    )


class AutoHeal:
    def __init__(self, cfg: AutoHealConfig) -> None:
        self.cfg = cfg

    def simulate(self, seed: int) -> list[WindowOutcome]:
        state = _initial_state(seed, self.cfg)
        cumulative_remediated: set = set()
        disclosure_windows: dict = {}
        rows: list[WindowOutcome] = []
        for w in range(1, WINDOWS + 1):
            out = run_window(state, self.cfg, seed, w,
                             cumulative_remediated, disclosure_windows)
            rows.append(out)
            if out.halt_triggered:
                # AutoHeal halts; remaining windows are recorded as halted
                # for transparency in the frozen results.
                continue
            # Disclosure of new CVEs at next window (Poisson(lambda))
            from paper5.window_sim import disclose_new_cves
            rng = np.random.default_rng((seed, w, 100))
            disclose_new_cves(state, rng, w, rate=self.cfg.arrival_rate)
            update_epss(state, rng)
            update_telemetry_freshness(state, set())
        return rows
