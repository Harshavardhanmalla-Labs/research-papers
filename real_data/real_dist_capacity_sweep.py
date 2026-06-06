"""Real-distribution version of Paper 6's (K, lambda) sweep.

Replaces synthetic EPSS/KEV with real-corpus sampling in Paper 6's
multi-window simulator. Captures whether Paper 6's K=200 collapse and
96.0% per-pair persistence findings hold under real CVE attribute
distributions.

Smaller grid than Paper 6 for tractability: K in {50, 100, 200},
lambda in {1, 3, 12}. 9 cells x 5 methods x 25 seeds x 6 windows =
6,750 rows.

Output:
    real_data/results/real_dist_capacity_sweep.csv
    real_data/results/real_dist_capacity_summary.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "paper5" / "src"))
sys.path.insert(0, str(REPO / "paper4" / "src"))

from paper5.window_sim import (
    FleetState, applicable_pairs, apply_remediation,
    disclose_new_cves as _orig_disclose,
    update_epss, update_telemetry_freshness,
)
from paper5 import window_sim as ws
from hygieneprio.generator import EEHDAFleetGenerator
from hygieneprio.hrs import HygieneRiskScore, HRSWeights
from hygieneprio.scorer import (
    HygienePrioScorer, ScorerWeights,
    EPSSOnlyScorer, CVSSOnlyScorer, HRSOnlyScorer, RandomScorer,
)
from hygieneprio.metrics import precision_at_k


CORPUS_PATH = REPO / "real_data" / "processed" / "cve_corpus_for_sampling.csv"
CAP_GRID = (50, 100, 200)
LAM_GRID = (1.0, 3.0, 12.0)
N_WINDOWS = 6
EPSS_THRESHOLD = 0.10
HRS_PERCENTILE = 75
EVAL_SEEDS = tuple(range(105, 130))
FIXED_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS   = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)

# Real corpus loaded once
_corpus = pd.read_csv(CORPUS_PATH)


def _resample_cve_real(vr: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    vr = vr.copy()
    n = len(vr)
    idx = rng.integers(0, len(_corpus), n)
    sampled = _corpus.iloc[idx][['epss', 'in_kev']].reset_index(drop=True)
    vr['epss_score'] = sampled['epss'].clip(1e-4, 1.0).values
    vr['in_kev']     = sampled['in_kev'].values
    vr['days_since_kev_entry'] = np.where(
        vr['in_kev'],
        rng.integers(0, 30, size=n).astype(float),
        np.nan,
    )
    return vr


def _disclose_new_cves_real(
    state: FleetState,
    rng: np.random.Generator,
    window_index: int,
    *,
    rate: float,
) -> None:
    """Real-distribution replacement for window_sim.disclose_new_cves.

    Draws Poisson(rate) new (host, CVE) rows but samples EPSS/KEV from
    the real public corpus instead of the synthetic Beta-mix fixture.
    Other steps (CVE id, CVSS, patched=False) match the original.
    """
    n_new = int(rng.poisson(rate))
    if n_new == 0:
        return

    host_ids = state.computers["computer_id"].sample(
        n=n_new, replace=True, random_state=rng.integers(0, 2**31 - 1)
    ).values
    sampled = _corpus.iloc[rng.integers(0, len(_corpus), n_new)].reset_index(drop=True)
    epss = sampled['epss'].clip(1e-4, 1.0).values
    in_kev = sampled['in_kev'].values
    kev_days = np.where(in_kev, rng.integers(0, 30, size=n_new).astype(float), np.nan)

    # CVSS: keep the synthetic Beta sampling — real CVSS isn't in the corpus
    cats = rng.choice([0, 1, 2, 3], size=n_new, p=[0.20, 0.35, 0.35, 0.10])
    cvss = np.where(cats == 0, rng.uniform(2.0, 4.0, n_new),
            np.where(cats == 1, rng.uniform(4.0, 7.0, n_new),
            np.where(cats == 2, rng.uniform(7.0, 9.0, n_new),
                                rng.uniform(9.0, 10.0, n_new))))

    base = state.vulnerability_records["cve_id"].nunique() + 1
    cve_ids = [f"CVE-W{window_index:02d}-R{base + i:06d}" for i in range(n_new)]
    new_rows = pd.DataFrame({
        "computer_id": host_ids,
        "cve_id": cve_ids,
        "epss_score": np.round(epss, 4),
        "cvss_base_score": np.round(cvss, 1),
        "in_kev": in_kev,
        "days_since_kev_entry": kev_days,
        "patch_lag_days": np.nan,
        "patched": False,
    })
    state.vulnerability_records = pd.concat(
        [state.vulnerability_records, new_rows], ignore_index=True
    )
    # rebuild patch state via the original helper
    state.endpoint_patch_state = ws._recompute_patch_state(state.vulnerability_records)


def _initial_state_real(seed: int) -> FleetState:
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    rng = np.random.default_rng((seed, 0, 0))
    tables["vulnerability_records"] = _resample_cve_real(
        tables["vulnerability_records"], rng,
    )
    return FleetState(
        vulnerability_records=tables["vulnerability_records"],
        computers=tables["computers"], users=tables["users"],
        groups=tables["groups"],
        group_membership_events=tables["group_membership_events"],
        endpoint_patch_state=tables["endpoint_patch_state"],
        telemetry_freshness_log=tables["telemetry_freshness_log"],
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


def _label(pairs: pd.DataFrame, hrs: pd.Series) -> pd.Series:
    if len(pairs) == 0:
        return pd.Series([], dtype=int)
    thr = hrs.quantile(HRS_PERCENTILE / 100.0)
    return ((pairs["epss_score"] > EPSS_THRESHOLD) &
            (pairs["computer_id"].map(hrs) > thr)).astype(int)


def _advance_real(state, top_k_pairs, *, w, seed, lam):
    rng = np.random.default_rng((seed, w, 0))
    acted = apply_remediation(state, top_k_pairs)
    _disclose_new_cves_real(state, rng, w, rate=lam)
    update_epss(state, rng)
    update_telemetry_freshness(state, acted)


def simulate_cell_seed(K: int, lam: float, seed: int) -> list[dict]:
    state = _initial_state_real(seed)
    rows = []
    for w in range(1, N_WINDOWS + 1):
        pairs = applicable_pairs(state)
        hrs   = _compute_hrs(state)
        pairs_labeled = pairs.copy()
        pairs_labeled["_label"] = _label(pairs_labeled, hrs)

        ranked = {
            "HygienePrio-full": HygienePrioScorer(weights=FIXED_WEIGHTS).rank_pairs(pairs_labeled, hrs),
            "EPSS-only":        EPSSOnlyScorer().rank_pairs(pairs_labeled),
            "HRS-only":         HRSOnlyScorer().rank_pairs(pairs_labeled, hrs),
            "CVSS-only":        CVSSOnlyScorer().rank_pairs(pairs_labeled),
            "Random":           RandomScorer().rank_pairs(pairs_labeled, seed=seed * 100 + w),
        }
        n_pos = int(pairs_labeled["_label"].sum())
        for name, r in ranked.items():
            labels = r["_label"].tolist()
            row = {"cell_K": K, "cell_lambda": lam, "seed": seed, "window": w,
                   "method": name, "n_pairs": len(pairs), "n_positives": n_pos}
            for k in (50, 100, 250):
                row[f"p_at_{k}"] = round(precision_at_k(labels, k), 4)
            rows.append(row)
        if w < N_WINDOWS:
            hp_top = ranked["HygienePrio-full"].head(K)
            _advance_real(state, hp_top, w=w, seed=seed, lam=lam)
    return rows


def main() -> None:
    print(f"Real-distribution capacity sweep: {len(CAP_GRID)}x{len(LAM_GRID)} cells "
          f"x {len(EVAL_SEEDS)} seeds x {N_WINDOWS} windows x 5 methods")
    all_rows = []
    cells = [(K, lam) for K in CAP_GRID for lam in LAM_GRID]
    for i, (K, lam) in enumerate(cells, 1):
        print(f"[{i}/{len(cells)}] K={K} lambda={lam}", flush=True)
        for s in EVAL_SEEDS:
            all_rows.extend(simulate_cell_seed(K, lam, s))
    df = pd.DataFrame(all_rows)
    out = REPO / "real_data" / "results"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "real_dist_capacity_sweep.csv", index=False)

    # Summary: HP-vs-EPSS per-pair persistence + W6 cell means
    summary = {"n_rows": len(df), "cell_means_W6": {}, "persistence": {}}
    for K, lam in cells:
        cell = df[(df.cell_K == K) & (df.cell_lambda == lam)]
        w6   = cell[cell.window == 6]
        m    = w6.groupby("method")["p_at_50"].mean().round(4).to_dict()
        summary["cell_means_W6"][f"K{K}_L{int(lam)}"] = m

        # Per-pair persistence: HP > EPSS fraction
        n_dom = n_tot = 0
        for s in cell.seed.unique():
            ss = cell[cell.seed == s]
            for wi in range(1, N_WINDOWS + 1):
                hp = ss[(ss.method == "HygienePrio-full") & (ss.window == wi)]["p_at_50"]
                ep = ss[(ss.method == "EPSS-only")        & (ss.window == wi)]["p_at_50"]
                if len(hp) and len(ep):
                    n_tot += 1
                    if hp.values[0] > ep.values[0]:
                        n_dom += 1
        summary["persistence"][f"K{K}_L{int(lam)}"] = round(n_dom/n_tot, 3) if n_tot else None
    overall_dom = overall_tot = 0
    for (K, lam) in cells:
        cell = df[(df.cell_K == K) & (df.cell_lambda == lam)]
        for s in cell.seed.unique():
            ss = cell[cell.seed == s]
            for wi in range(1, N_WINDOWS + 1):
                hp = ss[(ss.method == "HygienePrio-full") & (ss.window == wi)]["p_at_50"]
                ep = ss[(ss.method == "EPSS-only")        & (ss.window == wi)]["p_at_50"]
                if len(hp) and len(ep):
                    overall_tot += 1
                    if hp.values[0] > ep.values[0]:
                        overall_dom += 1
    summary["overall_persistence"] = round(overall_dom/overall_tot, 3) if overall_tot else None

    with open(out / "real_dist_capacity_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {len(df)} rows + summary")
    print(f"\nOverall HP > EPSS persistence (real dist): {summary['overall_persistence']*100:.1f}%")
    print(f"  Synthetic Paper 6 baseline: 96.0%")
    print(f"\nHP-full W6 P@50 per cell:")
    for k, m in summary["cell_means_W6"].items():
        print(f"  {k}: HP={m.get('HygienePrio-full', None):.3f}  EPSS={m.get('EPSS-only', None):.3f}  "
              f"HRS={m.get('HRS-only', None):.3f}")


if __name__ == "__main__":
    main()
