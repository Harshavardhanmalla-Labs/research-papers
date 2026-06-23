"""
Patch Tuesday Intelligence (Paper 14): maturation/observation model, predictive
scorer, and per-seed evaluation.

Re-uses the Paper-11 government context layer (capg.context) and the Paper-4 EEHDA
generator. The real corpus EPSS is treated as the matured value at horizon H; the
day-0 observation is a sigma-noisy, biased-low draw from it (PAPER14_PROTOCOL.md
sections 4 and 5). Ground-truth labels are fixed across methods.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
for _p in (Path(__file__).resolve().parents[1],):  # vendored hygieneprio + capg
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from hygieneprio.generator import EEHDAFleetGenerator  # noqa: E402
from capg.context import assign_context, asset_context_score, ContextWeights  # noqa: E402
from capg.metrics import precision_at_k, ndcg_at_k  # noqa: E402

# Pre-registered constants (PAPER14_PROTOCOL.md).
K_VALUES = [50, 100, 250]
EVALUATION_SEEDS = list(range(500, 525))           # 25 seeds (fresh, uninspected; reframed protocol v2)
DEV_SEEDS = [300, 400]                              # development only, excluded from eval
SIGMA_GRID = [0.0, 0.25, 0.50, 0.75, 1.0]          # day-0 EPSS noise sweep
REF_SIGMA = 0.50                                   # reference noise for H1/H3
BIAS_B = 0.75                                       # day-0 downward bias (logit), known to predictor
TAU = 1.0                                           # CVSS severity-correlate noise (logit)
P_KEV_OBS = 0.3                                     # fraction of matured KEV visible at T0
KEV_BONUS = 2.0                                     # logit bonus when KEV is observed at T0
RHO = 8.0                                           # context emphasis (Paper 11)
EPSS_GATE = 0.10                                    # matured high-risk threshold
CONTEXT_PCTL = 75                                   # ACS percentile for the target
REAL_CORPUS = Path(__file__).resolve().parents[2] / "data" / "cve_corpus_for_sampling.csv"  # vendored


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _resample_matured(vr: pd.DataFrame, corpus: pd.DataFrame,
                      rng: np.random.Generator) -> pd.DataFrame:
    """Matured EPSS/KEV from the real corpus (epss_mat, kev_mat)."""
    vr = vr.copy()
    n = len(vr)
    idx = rng.integers(0, len(corpus), n)
    sampled = corpus.iloc[idx][["epss", "in_kev"]].reset_index(drop=True)
    vr["epss_mat"] = np.clip(sampled["epss"].to_numpy(dtype=float), 1e-4, 1.0)
    vr["kev_mat"] = sampled["in_kev"].to_numpy().astype(bool)
    return vr


def add_observations(vr: pd.DataFrame, sigma: float,
                     rng: np.random.Generator) -> pd.DataFrame:
    """Add day-0 observation columns at noise level sigma (protocol section 4)."""
    vr = vr.copy()
    n = len(vr)
    lm = _logit(vr["epss_mat"].to_numpy())
    vr["epss_obs"] = np.clip(
        _sigmoid(lm - BIAS_B + rng.normal(0, sigma, n)), 1e-4, 1.0)
    vr["cvss_stable"] = 10.0 * _sigmoid(lm + rng.normal(0, TAU, n))
    vr["kev_obs"] = vr["kev_mat"].to_numpy() & (rng.random(n) < P_KEV_OBS)
    return vr


def build_fleet(seed: int, corpus: pd.DataFrame):
    """Construct one government fleet with matured EPSS/KEV and ACS. Returns
    (pairs_with_matured, acs)."""
    tables = EEHDAFleetGenerator(seed=seed).generate_all()
    rng = np.random.default_rng((seed, 14))
    pairs = _resample_matured(tables["vulnerability_records"], corpus, rng)
    pairs = pairs.reset_index(drop=True)
    computers_ctx = assign_context(tables["computers"], seed)
    acs = asset_context_score(computers_ctx, ContextWeights(0.5, 0.3, 0.2))
    # Fixed Mission-Critical Emergent True Positive target.
    acs_thr = acs.quantile(CONTEXT_PCTL / 100.0)
    host_acs = pairs["computer_id"].map(acs)
    pairs["_mcetp"] = (
        ((pairs["epss_mat"] > EPSS_GATE) | pairs["kev_mat"]) & (host_acs > acs_thr)
    ).astype(int).to_numpy()
    return pairs, acs


def _rank_by(pairs: pd.DataFrame, key: np.ndarray) -> pd.DataFrame:
    df = pairs.copy()
    df["_key"] = key
    return df.sort_values("_key", ascending=False, kind="mergesort").reset_index(drop=True)


def _fused_risk_logit(pairs: pd.DataFrame, sigma: float, *, use_obs: bool) -> np.ndarray:
    """Precision-weighted fusion of the de-biased day-0 EPSS observation and the stable
    CVSS severity correlate, in logit space (PAPER14_PROTOCOL.md section 5).

    The de-biased observation is an unbiased estimate of logit(epss_mat) with variance
    sigma^2; the CVSS correlate has variance tau^2. The inverse-variance weight lambda
    puts all mass on the observation as sigma -> 0 (so PTI collapses to context-aware
    day-0 EPSS) and shifts toward the stable signal as the day-0 signal degrades.
    A positive KEV-at-disclosure observation adds a fixed logit bonus.
    """
    obs_debiased = _logit(pairs["epss_obs"].to_numpy()) + BIAS_B          # ~ logit(epss_mat)+N(0,sigma)
    stable = _logit(np.clip(pairs["cvss_stable"].to_numpy() / 10.0, 1e-6, 1 - 1e-6))
    ko = pairs["kev_obs"].to_numpy().astype(float)

    if not use_obs:
        mu = stable + KEV_BONUS * ko
        return mu
    if sigma <= 1e-9:
        lam = 1.0                                                          # day-0 signal is exact
    else:
        p_obs, p_stable = 1.0 / sigma**2, 1.0 / TAU**2
        lam = p_obs / (p_obs + p_stable)
    return lam * obs_debiased + (1.0 - lam) * stable + KEV_BONUS * ko


def rank_method(pairs: pd.DataFrame, acs: pd.Series, method: str, sigma: float,
                rng: np.random.Generator) -> pd.DataFrame:
    """Return pairs ranked by the given method (PAPER14_PROTOCOL.md section 5)."""
    host_acs = pairs["computer_id"].map(acs).fillna(0.0).to_numpy()
    ctx = 1.0 + RHO * host_acs
    eo = pairs["epss_obs"].to_numpy()
    em = pairs["epss_mat"].to_numpy()
    cv = pairs["cvss_stable"].to_numpy() / 10.0

    if method == "EPSS-day0":
        key = eo
    elif method == "CAP-day0":
        key = eo * ctx
    elif method == "EPSS-matured-oracle":
        key = em * ctx
    elif method == "CVSS-only":
        key = cv
    elif method == "Random":
        key = rng.random(len(pairs))
    elif method == "Context-only":
        key = host_acs
    elif method == "PTI-full":
        key = _sigmoid(_fused_risk_logit(pairs, sigma, use_obs=True)) * ctx
    elif method == "PTI-noObs":
        key = _sigmoid(_fused_risk_logit(pairs, sigma, use_obs=False)) * ctx
    elif method == "PTI-noCrit":
        key = _sigmoid(_fused_risk_logit(pairs, sigma, use_obs=True))   # rho = 0
    else:
        raise ValueError(f"unknown method {method}")
    return _rank_by(pairs, key)


METHODS = ["EPSS-day0", "CAP-day0", "EPSS-matured-oracle", "CVSS-only", "Random",
           "Context-only", "PTI-full", "PTI-noObs", "PTI-noCrit"]


def evaluate_seed(seed: int, corpus: pd.DataFrame) -> list[dict]:
    """Evaluate all methods across the sigma sweep for one seed."""
    pairs0, acs = build_fleet(seed, corpus)
    n_mcetp = int(pairs0["_mcetp"].sum())
    rows = []
    for sigma in SIGMA_GRID:
        obs_rng = np.random.default_rng((seed, int(sigma * 1000), 41))
        pairs = add_observations(pairs0, sigma, obs_rng)
        for mi, method in enumerate(METHODS):
            rank_rng = np.random.default_rng((seed, int(sigma * 1000), mi))
            ranked = rank_method(pairs, acs, method, sigma, rank_rng)
            labels = ranked["_mcetp"].tolist()
            row = {"seed": seed, "sigma": sigma, "method": method, "n_mcetp": n_mcetp}
            for k in K_VALUES:
                row[f"mwp_at_{k}"] = round(precision_at_k(labels, k), 4)
                row[f"ndcg_at_{k}"] = round(ndcg_at_k(labels, k), 4)
            rows.append(row)
    return rows
