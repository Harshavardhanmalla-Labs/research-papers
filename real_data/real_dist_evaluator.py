"""Real-distribution external validity evaluation for Paper 4.

Replaces the synthetic EPSS/KEV distributions in Paper 4's EEHDA generator
with sampled real attribute tuples from the frozen 2020+ CVE corpus
(real_data/processed/cve_corpus_for_sampling.csv).

Same fleet topology (1000 users, 830 hosts), same Paper 4 HygienePrio scorer,
same evaluation seeds. Only the CVE attribute distribution changes.

Outputs:
  real_data/results/real_dist_results.csv
  real_data/results/comparison_summary.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "paper4" / "src"))

from hygieneprio.generator import EEHDAFleetGenerator
from hygieneprio.hrs import HygieneRiskScore, HRSWeights
from hygieneprio.scorer import (
    HygienePrioScorer, ScorerWeights,
    EPSSOnlyScorer, CVSSOnlyScorer, HRSOnlyScorer, RandomScorer,
)
from hygieneprio.metrics import precision_at_k


CORPUS_PATH = REPO / "real_data" / "processed" / "cve_corpus_for_sampling.csv"
EVAL_SEEDS = tuple(range(105, 130))   # match Paper 4 evaluation set
FIXED_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS   = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)
EPSS_THRESHOLD = 0.10
HRS_PERCENTILE = 75
K_VALUES = (50, 100, 250)


def _resample_cve_attributes_real(
    vulnerability_records: pd.DataFrame,
    corpus: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Replace synthetic EPSS/KEV columns with values drawn from the real corpus.

    Keeps the (computer_id, cve_id) topology and the patch_lag_days/patched
    columns intact; only re-samples epss_score and in_kev. Days_since_kev_entry
    is set deterministically from KEV inclusion (uniform 0-30 days for in-KEV
    items, NaN otherwise) — matching Paper 4's fixture convention.
    """
    vr = vulnerability_records.copy()
    n = len(vr)
    idx = rng.integers(0, len(corpus), n)
    sampled = corpus.iloc[idx][['epss', 'in_kev']].reset_index(drop=True)
    vr['epss_score'] = sampled['epss'].clip(1e-4, 1.0).values
    vr['in_kev']     = sampled['in_kev'].values
    vr['days_since_kev_entry'] = np.where(
        vr['in_kev'],
        rng.integers(0, 30, size=n).astype(float),
        np.nan,
    )
    return vr


def _label(pairs: pd.DataFrame, hrs: pd.Series) -> pd.Series:
    if len(pairs) == 0:
        return pd.Series([], dtype=int)
    thr = hrs.quantile(HRS_PERCENTILE / 100.0)
    return ((pairs["epss_score"] > EPSS_THRESHOLD) &
            (pairs["computer_id"].map(hrs) > thr)).astype(int)


def evaluate_seed(seed: int, corpus: pd.DataFrame) -> list[dict]:
    rng = np.random.default_rng(seed)
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    vr_real = _resample_cve_attributes_real(
        tables["vulnerability_records"], corpus, rng,
    )
    tables["vulnerability_records"] = vr_real

    hrs = HygieneRiskScore(weights=HRS_WEIGHTS).compute(**{k: tables[k] for k in (
        "endpoint_patch_state", "vulnerability_records", "users", "groups",
        "group_membership_events", "computers", "telemetry_freshness_log")})

    pairs = vr_real[~vr_real["patched"]].reset_index(drop=True)
    pairs["_label"] = _label(pairs, hrs)

    methods = {
        "HygienePrio-full": HygienePrioScorer(weights=FIXED_WEIGHTS).rank_pairs(pairs, hrs),
        "EPSS-only":        EPSSOnlyScorer().rank_pairs(pairs),
        "HRS-only":         HRSOnlyScorer().rank_pairs(pairs, hrs),
        "CVSS-only":        CVSSOnlyScorer().rank_pairs(pairs),
        "Random":           RandomScorer().rank_pairs(pairs, seed=seed),
    }

    n_pos = int(pairs["_label"].sum())
    rows = []
    for name, ranked in methods.items():
        labels = ranked["_label"].tolist()
        row = {"seed": seed, "method": name, "n_pairs": len(pairs), "n_positives": n_pos}
        for k in K_VALUES:
            row[f"p_at_{k}"] = round(precision_at_k(labels, k), 4)
        rows.append(row)
    return rows


def main() -> None:
    corpus = pd.read_csv(CORPUS_PATH)
    print(f"Loaded real CVE corpus: {len(corpus):,} CVEs "
          f"(KEV: {corpus.in_kev.sum():,}, EPSS>0.10: {(corpus.epss > 0.10).sum():,})")
    print(f"Evaluating on {len(EVAL_SEEDS)} seeds with real CVE attributes...")
    rows = []
    for s in EVAL_SEEDS:
        rows.extend(evaluate_seed(s, corpus))
        print(f"  seed {s}: done", flush=True)
    df = pd.DataFrame(rows)
    out = REPO / "real_data" / "results"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "real_dist_results.csv", index=False)

    # Compare to Paper 4 synthetic results
    synth = pd.read_csv(REPO / "paper4" / "results" / "primary_results_v1" /
                        "primary_results.csv")
    synth_eval = synth[synth.seed.isin(EVAL_SEEDS)]
    comparison = {}
    for m in ["HygienePrio-full", "EPSS-only", "HRS-only", "CVSS-only", "Random"]:
        real_p50  = df[df.method == m].p_at_50.mean()
        synth_p50 = synth_eval[synth_eval.method == m].p_at_50.mean()
        comparison[m] = {
            "real_dist_mean_p50":  round(float(real_p50), 4),
            "synth_mean_p50":      round(float(synth_p50), 4),
            "delta":               round(float(real_p50 - synth_p50), 4),
        }
    hp = comparison["HygienePrio-full"]
    ep = comparison["EPSS-only"]
    summary = {
        "n_seeds": len(EVAL_SEEDS),
        "comparison_by_method": comparison,
        "real_dist_hp_vs_epss_gap_pp": round((hp["real_dist_mean_p50"] - ep["real_dist_mean_p50"]) * 100, 1),
        "synth_hp_vs_epss_gap_pp":     round((hp["synth_mean_p50"]     - ep["synth_mean_p50"])     * 100, 1),
    }
    with open(out / "comparison_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)
    print(f"\nWrote {out}/real_dist_results.csv ({len(df)} rows)")
    print("\n=== HygienePrio Real vs Synthetic ===")
    for m, vals in comparison.items():
        print(f"  {m:18s} real={vals['real_dist_mean_p50']:.3f} synth={vals['synth_mean_p50']:.3f} "
              f"delta={vals['delta']:+.3f}")
    print(f"\nHP vs EPSS Precision@50 gap:")
    print(f"  Synthetic: +{summary['synth_hp_vs_epss_gap_pp']:.1f} pp (Paper 4 headline)")
    print(f"  Real:      +{summary['real_dist_hp_vs_epss_gap_pp']:.1f} pp (external validity)")


if __name__ == "__main__":
    main()
