"""Statistical analysis helpers.

Pure, deterministic functions for paired comparison of per-seed metric
results: bootstrap confidence intervals (percentile and BCa), the
Wilcoxon signed-rank paired test, Holm-Bonferroni family-wise
correction, paired effect sizes, and a minimum-detectable-effect helper.

These functions only *compute* statistics. Interpretation of
significance (and the direction of "better", which differs by metric)
belongs to the reporting layer, not here.
"""

from __future__ import annotations

import warnings as _warnings
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
import scipy.stats as _sps
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import TTestPower

from paper1.utils.seeds import make_rng

__all__ = [
    "StatTestResult",
    "bootstrap_ci",
    "bootstrap_ci_bca",
    "clean_numeric_array",
    "compare_many_to_baseline",
    "compare_to_baseline",
    "holm_bonferroni",
    "minimum_detectable_effect",
    "paired_arrays",
    "paired_bootstrap_ci",
    "paired_cohens_d",
    "paired_mean_difference",
    "relative_difference",
    "validate_per_seed_metric_frame",
    "wilcoxon_signed_rank",
]


@dataclass(frozen=True)
class StatTestResult:
    comparison_name: str
    metric_name: str
    baseline_strategy: str
    candidate_strategy: str
    n_pairs: int
    baseline_mean: float
    candidate_mean: float
    mean_difference: float
    relative_difference: float
    effect_size_paired_d: float
    wilcoxon_statistic: float
    p_value: float
    method: str
    p_value_adjusted: float | None = None
    reject_null: bool | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    notes: str = ""


# ---------------------------------------------------------------------------
# A. cleaning
# ---------------------------------------------------------------------------


def clean_numeric_array(values: Any, dropna: bool = True) -> np.ndarray:
    """Coerce to a float ndarray, optionally dropping NaN; raise if empty."""
    arr = pd.Series(list(values)).astype("float64").to_numpy()
    if dropna:
        arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        raise ValueError("no numeric values remain after cleaning")
    return arr


# ---------------------------------------------------------------------------
# B. paired alignment
# ---------------------------------------------------------------------------


def paired_arrays(
    df: pd.DataFrame,
    metric_name: str,
    baseline_strategy: str,
    candidate_strategy: str,
    seed_col: str = "seed",
    strategy_col: str = "strategy",
    metric_col: str = "metric",
    value_col: str = "value",
) -> tuple[np.ndarray, np.ndarray, list[Any]]:
    """Return (baseline_values, candidate_values, paired_seeds) aligned by seed."""
    sub = df[df[metric_col] == metric_name]
    if sub.empty:
        raise ValueError(f"no rows for metric {metric_name!r}")
    pivot = sub.pivot_table(
        index=seed_col, columns=strategy_col, values=value_col, aggfunc="first"
    )
    for strat in (baseline_strategy, candidate_strategy):
        if strat not in pivot.columns:
            raise ValueError(f"strategy {strat!r} not present for metric {metric_name!r}")
    both = pivot[[baseline_strategy, candidate_strategy]].dropna()
    dropped = len(pivot) - len(both)
    if dropped > 0:
        _warnings.warn(
            f"dropped {dropped} seed(s) missing either {baseline_strategy!r} or "
            f"{candidate_strategy!r} for metric {metric_name!r}",
            stacklevel=2,
        )
    if len(both) < 2:
        raise ValueError(
            f"need >=2 paired seeds; got {len(both)} for {candidate_strategy} vs "
            f"{baseline_strategy} on {metric_name}"
        )
    seeds = list(both.index)
    return (
        both[baseline_strategy].to_numpy(dtype=float),
        both[candidate_strategy].to_numpy(dtype=float),
        seeds,
    )


# ---------------------------------------------------------------------------
# C-E. difference / effect size
# ---------------------------------------------------------------------------


def paired_mean_difference(candidate: Any, baseline: Any) -> float:
    c = np.asarray(candidate, dtype=float)
    b = np.asarray(baseline, dtype=float)
    if c.shape != b.shape:
        raise ValueError("candidate and baseline must have equal shape")
    return float(np.mean(c - b))


def relative_difference(candidate_mean: float, baseline_mean: float) -> float:
    if baseline_mean == 0:
        return np.nan
    return (candidate_mean - baseline_mean) / abs(baseline_mean)


def paired_cohens_d(candidate: Any, baseline: Any) -> float:
    c = np.asarray(candidate, dtype=float)
    b = np.asarray(baseline, dtype=float)
    if c.shape != b.shape:
        raise ValueError("candidate and baseline must have equal shape")
    diff = c - b
    sd = float(np.std(diff, ddof=1)) if diff.size > 1 else 0.0
    mean_diff = float(np.mean(diff))
    if sd == 0.0:
        return 0.0 if mean_diff == 0.0 else np.inf * np.sign(mean_diff)
    return mean_diff / sd


# ---------------------------------------------------------------------------
# F. Wilcoxon
# ---------------------------------------------------------------------------


def wilcoxon_signed_rank(
    candidate: Any, baseline: Any, alternative: str = "two-sided"
) -> tuple[float, float]:
    c = np.asarray(candidate, dtype=float)
    b = np.asarray(baseline, dtype=float)
    if c.shape != b.shape:
        raise ValueError("candidate and baseline must have equal shape")
    diff = c - b
    if np.allclose(diff, 0.0):
        # All-zero differences: Wilcoxon is undefined; report no effect.
        return 0.0, 1.0
    with _warnings.catch_warnings():
        _warnings.simplefilter("ignore")
        res = _sps.wilcoxon(c, b, zero_method="wilcox", alternative=alternative)
    return float(res.statistic), float(res.pvalue)


# ---------------------------------------------------------------------------
# G. Holm-Bonferroni
# ---------------------------------------------------------------------------


def holm_bonferroni(
    p_values: dict[str, float], alpha: float = 0.05
) -> dict[str, dict[str, Any]]:
    """Holm-Bonferroni adjust a dict of {comparison: p_value}."""
    if not p_values:
        return {}
    keys = list(p_values.keys())
    pvals = [float(p_values[k]) for k in keys]
    reject, p_adj, _, _ = multipletests(pvals, alpha=alpha, method="holm")
    return {
        k: {
            "p_value": pvals[i],
            "p_value_adjusted": float(p_adj[i]),
            "reject_null": bool(reject[i]),
            "alpha": alpha,
        }
        for i, k in enumerate(keys)
    }


# ---------------------------------------------------------------------------
# H-J. bootstrap
# ---------------------------------------------------------------------------


def bootstrap_ci(
    values: Any,
    statistic: Callable[[np.ndarray], float] = np.mean,
    B: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
    method: str = "percentile",
) -> tuple[float, float]:
    """Percentile bootstrap CI for a 1-D statistic (deterministic)."""
    arr = clean_numeric_array(values)
    if arr.size < 2:
        raise ValueError("need >=2 values for a bootstrap CI")
    rng = make_rng(seed)
    n = arr.size
    stats = np.empty(B, dtype=float)
    for i in range(B):
        idx = rng.integers(0, n, n)
        stats[i] = float(statistic(arr[idx]))
    lo = float(np.percentile(stats, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(stats, 100.0 * (1.0 - alpha / 2.0)))
    return lo, hi


def bootstrap_ci_bca(
    values: Any,
    statistic: Callable[..., float] = np.mean,
    B: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    """BCa bootstrap CI via scipy; falls back to percentile on degeneracy."""
    arr = clean_numeric_array(values)
    if arr.size < 2:
        raise ValueError("need >=2 values for a bootstrap CI")
    try:
        with _warnings.catch_warnings():
            _warnings.simplefilter("ignore")
            res = _sps.bootstrap(
                (arr,),
                statistic,
                n_resamples=B,
                confidence_level=1.0 - alpha,
                method="BCa",
                random_state=make_rng(seed),
            )
        lo = float(res.confidence_interval.low)
        hi = float(res.confidence_interval.high)
        if not (np.isfinite(lo) and np.isfinite(hi)):
            raise ValueError("non-finite BCa interval")
        return lo, hi
    except Exception as exc:  # degenerate data fallback to percentile
        _warnings.warn(
            f"BCa bootstrap failed ({exc}); falling back to percentile", stacklevel=2
        )
        return bootstrap_ci(values, statistic, B=B, alpha=alpha, seed=seed)


def paired_bootstrap_ci(
    candidate: Any,
    baseline: Any,
    statistic: Callable[[np.ndarray, np.ndarray], float] = paired_mean_difference,
    B: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
    method: str = "percentile",
) -> tuple[float, float]:
    """Percentile CI for a paired statistic; rows are resampled together."""
    c = np.asarray(candidate, dtype=float)
    b = np.asarray(baseline, dtype=float)
    if c.shape != b.shape:
        raise ValueError("candidate and baseline must have equal length")
    keep = ~(np.isnan(c) | np.isnan(b))
    c, b = c[keep], b[keep]
    if c.size < 2:
        raise ValueError("need >=2 paired observations for a bootstrap CI")
    rng = make_rng(seed)
    n = c.size
    stats = np.empty(B, dtype=float)
    for i in range(B):
        idx = rng.integers(0, n, n)
        stats[i] = float(statistic(c[idx], b[idx]))
    lo = float(np.percentile(stats, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(stats, 100.0 * (1.0 - alpha / 2.0)))
    return lo, hi


# ---------------------------------------------------------------------------
# K-L. comparisons
# ---------------------------------------------------------------------------


def compare_to_baseline(
    df: pd.DataFrame,
    metric_name: str,
    baseline_strategy: str,
    candidate_strategy: str,
    alpha: float = 0.05,
    B: int = 1000,
    seed: int = 0,
    alternative: str = "two-sided",
    **paired_kwargs: Any,
) -> StatTestResult:
    """Paired comparison of one candidate against a baseline on one metric."""
    base, cand, seeds = paired_arrays(
        df, metric_name, baseline_strategy, candidate_strategy, **paired_kwargs
    )
    base_mean = float(np.mean(base))
    cand_mean = float(np.mean(cand))
    mdiff = paired_mean_difference(cand, base)
    rdiff = relative_difference(cand_mean, base_mean)
    d = paired_cohens_d(cand, base)
    w_stat, p = wilcoxon_signed_rank(cand, base, alternative=alternative)
    ci_low, ci_high = paired_bootstrap_ci(cand, base, B=B, alpha=alpha, seed=seed)
    return StatTestResult(
        comparison_name=f"{candidate_strategy}_vs_{baseline_strategy}",
        metric_name=metric_name,
        baseline_strategy=baseline_strategy,
        candidate_strategy=candidate_strategy,
        n_pairs=len(seeds),
        baseline_mean=base_mean,
        candidate_mean=cand_mean,
        mean_difference=mdiff,
        relative_difference=rdiff,
        effect_size_paired_d=d,
        wilcoxon_statistic=w_stat,
        p_value=p,
        method="wilcoxon+percentile_bootstrap",
        ci_low=ci_low,
        ci_high=ci_high,
        notes=f"alternative={alternative}; bootstrap B={B}",
    )


def compare_many_to_baseline(
    df: pd.DataFrame,
    metric_name: str,
    baseline_strategy: str,
    candidate_strategies: Sequence[str],
    alpha: float = 0.05,
    B: int = 1000,
    seed: int = 0,
    alternative: str = "two-sided",
    **paired_kwargs: Any,
) -> pd.DataFrame:
    """Compare several candidates to a baseline; Holm-Bonferroni across them."""
    results: list[StatTestResult] = []
    for cand in candidate_strategies:
        results.append(
            compare_to_baseline(
                df, metric_name, baseline_strategy, cand,
                alpha=alpha, B=B, seed=seed, alternative=alternative, **paired_kwargs,
            )
        )
    p_map = {r.comparison_name: r.p_value for r in results}
    holm = holm_bonferroni(p_map, alpha=alpha)
    rows: list[dict[str, Any]] = []
    for r in results:
        row = asdict(r)
        adj = holm[r.comparison_name]
        row["p_value_adjusted"] = adj["p_value_adjusted"]
        row["reject_null"] = adj["reject_null"]
        row["family_alpha"] = alpha
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# M. power
# ---------------------------------------------------------------------------


def minimum_detectable_effect(
    n_pairs: int, alpha: float = 0.05, power: float = 0.80, two_sided: bool = True
) -> float:
    """Approximate standardized paired effect size detectable at given power.

    Uses a paired (one-sample) t-test power model (statsmodels TTestPower).
    The result is the standardized mean difference (Cohen's d on the
    paired differences); it is an approximation suitable for planning.
    """
    if n_pairs < 3:
        raise ValueError("need n_pairs >= 3 for a meaningful MDE")
    alternative = "two-sided" if two_sided else "larger"
    es = TTestPower().solve_power(
        effect_size=None, nobs=n_pairs, alpha=alpha, power=power, alternative=alternative
    )
    return float(es)


# ---------------------------------------------------------------------------
# N. validation
# ---------------------------------------------------------------------------


def validate_per_seed_metric_frame(df: pd.DataFrame) -> None:
    """Validate a per-seed metric frame for downstream statistical analysis."""
    required = ["seed", "strategy", "metric", "value"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"metric frame missing required columns: {missing}")
    for col in ("seed", "strategy", "metric"):
        if df[col].isna().any():
            raise ValueError(f"column {col!r} contains null values")
    try:
        pd.to_numeric(df["value"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"'value' column is not numeric: {exc}") from exc

    optional_cells = [c for c in ("cell_id", "label", "approver_policy", "capacity_ratio") if c in df.columns]
    key_cols = ["seed", "strategy", "metric", *optional_cells]
    if df.duplicated(subset=key_cols).any():
        dupes = df[df.duplicated(subset=key_cols, keep=False)]
        raise ValueError(
            f"duplicate rows for key {key_cols}; example seeds: "
            f"{sorted(dupes['seed'].unique())[:5]}"
        )
