"""
Self-contained bias-corrected and accelerated (BCa) bootstrap confidence interval.

Vendored so this paper's analysis runs standalone with no cross-paper dependency.
See Efron (1987), "Better Bootstrap Confidence Intervals," JASA 82(397):171-185.
"""

from __future__ import annotations

import numpy as np
from scipy import stats as _scipy_stats


def _bca_ci(values, stat_fn, n_boot=10_000, ci=0.95, rng=None):
    if rng is None:
        rng = np.random.default_rng(0)
    values = np.asarray(values, dtype=float)
    n = len(values)
    obs = stat_fn(values)
    boot = np.array([stat_fn(rng.choice(values, size=n, replace=True)) for _ in range(n_boot)])

    prop_less = np.mean(boot < obs)
    if prop_less in (0.0, 1.0):
        a = (1 - ci) / 2
        return (float(np.percentile(boot, a * 100)),
                float(np.percentile(boot, (1 - a) * 100)))

    z0 = _scipy_stats.norm.ppf(prop_less)
    jack = np.array([stat_fn(np.delete(values, i)) for i in range(n)])
    jm = jack.mean()
    num = np.sum((jm - jack) ** 3)
    den = 6 * (np.sum((jm - jack) ** 2) ** 1.5)
    acc = num / den if den != 0 else 0.0

    a = (1 - ci) / 2
    z_a, z_1a = _scipy_stats.norm.ppf(a), _scipy_stats.norm.ppf(1 - a)

    def adj(z):
        numer = z0 + z
        denom = 1.0 - acc * (z0 + z)
        az = z0 + numer / denom if denom != 0 else z0
        return float(_scipy_stats.norm.cdf(az) * 100)

    return (float(np.percentile(boot, adj(z_a))),
            float(np.percentile(boot, adj(z_1a))))


def bca_ci_mean(per_seed_values, n_boot=10_000, ci=0.95, seed=0):
    """Mean and BCa confidence interval. Returns (mean, ci_lower, ci_upper)."""
    arr = np.array(per_seed_values, dtype=float)
    rng = np.random.default_rng(seed)
    lo, hi = _bca_ci(arr, np.mean, n_boot=n_boot, ci=ci, rng=rng)
    return float(np.mean(arr)), lo, hi
