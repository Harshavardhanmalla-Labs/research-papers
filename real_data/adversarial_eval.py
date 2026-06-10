"""Adversarial best-response simulation for Paper 4.

Setup: a Stackelberg game between defender (HygienePrio) and attacker.

Defender commits to HygienePrio scoring with the calibrated Paper 4 weights.
The attacker observes the defender's scoring rule and, for each (host, CVE)
pair, chooses to "game" a fraction g of the pairs by inflating their EPSS
score in a way that escapes HRS-based co-ranking — e.g., a fast-disclosed
public PoC that drives EPSS up rapidly on hosts that are NOT in the
high-HRS tail.

We measure the defender's Precision@50 as g grows from 0 to 0.30 (i.e.,
0% to 30% of pairs gamed). Compare HygienePrio's degradation curve against
EPSS-only's curve to quantify the adversarial robustness gain hygiene
augmentation provides.

Frozen output:
    real_data/results/adversarial_results.csv
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "paper4" / "src"))

from hygieneprio.generator import EEHDAFleetGenerator
from hygieneprio.hrs import HygieneRiskScore, HRSWeights
from hygieneprio.scorer import (
    HygienePrioScorer, ScorerWeights,
    EPSSOnlyScorer, HRSOnlyScorer,
)
from hygieneprio.metrics import precision_at_k

EVAL_SEEDS = tuple(range(105, 130))
FIXED_WEIGHTS = ScorerWeights(alpha=0.7, beta=0.5, gamma=0.1, delta=0.2)
HRS_WEIGHTS   = HRSWeights(patch_posture=0.5, ad_exposure=0.3, telemetry_freshness=0.2)
EPSS_THRESHOLD = 0.10
HRS_PERCENTILE = 75

# Attacker model: gaming fraction
GAMING_FRACTIONS = (0.00, 0.05, 0.10, 0.15, 0.20, 0.30)
GAMED_EPSS_VALUE = 0.55   # attacker inflates EPSS to a "high-but-plausible" level
# (median real KEV EPSS is 0.55 per Section 12; 0.55 is exactly at the boundary
# where naive EPSS-only ranking will prioritise the gamed pair)


def _label(pairs: pd.DataFrame, hrs: pd.Series, hrs_pct: float = HRS_PERCENTILE) -> pd.Series:
    if len(pairs) == 0:
        return pd.Series([], dtype=int)
    thr = hrs.quantile(hrs_pct / 100.0)
    return ((pairs["epss_score"] > EPSS_THRESHOLD) &
            (pairs["computer_id"].map(hrs) > thr)).astype(int)


def attack_pairs(
    pairs: pd.DataFrame,
    hrs: pd.Series,
    fraction: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Attacker game model.

    Inflate EPSS for `fraction` of (host, CVE) pairs whose hosts are in the
    BOTTOM 50% of the HRS distribution — i.e., attacker preferentially
    games low-hygiene-risk hosts so the inflated EPSS escapes HRS
    co-ranking and breaks HygienePrio's discriminative advantage.

    This is the worst-case attacker against HygienePrio. EPSS-only is hit
    just as hard mechanically (more pairs with high EPSS) but EPSS-only's
    Precision@50 was already mediocre, so the absolute degradation is
    smaller relative to its baseline.
    """
    pairs = pairs.copy()
    hrs_thr = hrs.quantile(0.50)
    candidates_mask = pairs["computer_id"].map(hrs) <= hrs_thr
    candidates = pairs.index[candidates_mask].tolist()
    if not candidates:
        return pairs
    n_attack = int(round(fraction * len(candidates)))
    if n_attack <= 0:
        return pairs
    chosen = rng.choice(candidates, size=min(n_attack, len(candidates)), replace=False)
    pairs.loc[chosen, "epss_score"] = GAMED_EPSS_VALUE
    return pairs


def evaluate_seed(seed: int) -> list[dict]:
    rng = np.random.default_rng(seed * 1000 + 1)
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    hrs = HygieneRiskScore(weights=HRS_WEIGHTS).compute(**{k: tables[k] for k in (
        "endpoint_patch_state", "vulnerability_records", "users", "groups",
        "group_membership_events", "computers", "telemetry_freshness_log")})

    vr = tables["vulnerability_records"]
    base_pairs = vr[~vr["patched"]].reset_index(drop=True)

    rows = []
    for g in GAMING_FRACTIONS:
        attacked = attack_pairs(base_pairs, hrs, g, rng)
        # IMPORTANT: ground-truth label is computed on the *attacked* pairs.
        # The attacker's inflated EPSS makes those pairs satisfy the
        # EPSS > 0.10 ground-truth condition; whether they are HRS-tail
        # positives depends on the HRS threshold (unchanged because attack
        # leaves HRS untouched). So gamed pairs become positives at low
        # HRS hosts only if HRS happens to clear the 75th percentile, which
        # is what makes this a true adversarial test: the attacker has
        # injected fake positives that look real to EPSS but not to HRS.
        attacked["_label"] = _label(attacked, hrs)
        for name, ranked in {
            "HygienePrio-full": HygienePrioScorer(weights=FIXED_WEIGHTS).rank_pairs(attacked, hrs),
            "EPSS-only":        EPSSOnlyScorer().rank_pairs(attacked),
            "HRS-only":         HRSOnlyScorer().rank_pairs(attacked, hrs),
        }.items():
            labels = ranked["_label"].tolist()
            rows.append({
                "seed": seed,
                "gaming_fraction": g,
                "method": name,
                "p_at_50": round(precision_at_k(labels, 50), 4),
                "n_positives": int(sum(labels)),
            })
    return rows


def main() -> None:
    print(f"Adversarial evaluation: {len(GAMING_FRACTIONS)} gaming levels x {len(EVAL_SEEDS)} seeds")
    rows = []
    for s in EVAL_SEEDS:
        rows.extend(evaluate_seed(s))
        print(f"  seed {s}: done", flush=True)
    df = pd.DataFrame(rows)
    out = REPO / "real_data" / "results"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "adversarial_results.csv", index=False)

    summary = df.groupby(['gaming_fraction', 'method'])['p_at_50'].mean().round(4).unstack()
    print(f"\n=== Mean Precision@50 vs Gaming Fraction ===\n{summary.to_string()}")
    print(f"\nWrote {out}/adversarial_results.csv ({len(df)} rows)")


if __name__ == "__main__":
    main()
