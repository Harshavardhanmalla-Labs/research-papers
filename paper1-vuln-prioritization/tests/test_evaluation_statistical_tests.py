"""Statistical analysis helper tests (Phase 10).

These tests exercise *computation only*. They do not assert that any
strategy is "significantly better" -- significance interpretation and the
direction of "better" (metric-dependent) belong to the reporting layer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from paper1.evaluation.statistical_tests import (
    StatTestResult,
    bootstrap_ci,
    bootstrap_ci_bca,
    clean_numeric_array,
    compare_many_to_baseline,
    compare_to_baseline,
    holm_bonferroni,
    minimum_detectable_effect,
    paired_arrays,
    paired_bootstrap_ci,
    paired_cohens_d,
    paired_mean_difference,
    relative_difference,
    validate_per_seed_metric_frame,
    wilcoxon_signed_rank,
)


def _toy_frame(n_seeds: int = 10) -> pd.DataFrame:
    """Per-seed metric frame.

    Metric is ``eehda_absolute`` (expected exploited-host-days; lower is
    better). For each seed s in 1..n_seeds:
        random        = 100 + s
        epss_only     =  60 + s
        proposed_full =  40 + s   (consistently below epss_only)
    So proposed_full < epss_only < random for every paired seed.
    """
    rows: list[dict] = []
    for s in range(1, n_seeds + 1):
        rows.append({"seed": s, "strategy": "random", "metric": "eehda_absolute", "value": 100.0 + s})
        rows.append({"seed": s, "strategy": "epss_only", "metric": "eehda_absolute", "value": 60.0 + s})
        rows.append({"seed": s, "strategy": "proposed_full", "metric": "eehda_absolute", "value": 40.0 + s})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# A. clean_numeric_array
# ---------------------------------------------------------------------------


def test_clean_numeric_array_drops_nan():
    out = clean_numeric_array([1.0, np.nan, 3.0])
    assert out.tolist() == [1.0, 3.0]


def test_clean_numeric_array_keeps_nan_when_disabled():
    out = clean_numeric_array([1.0, np.nan, 3.0], dropna=False)
    assert out.size == 3
    assert np.isnan(out[1])


def test_clean_numeric_array_raises_on_empty():
    with pytest.raises(ValueError):
        clean_numeric_array([np.nan, np.nan])
    with pytest.raises(ValueError):
        clean_numeric_array([])


# ---------------------------------------------------------------------------
# B. paired_arrays
# ---------------------------------------------------------------------------


def test_paired_arrays_aligns_by_seed():
    df = _toy_frame()
    base, cand, seeds = paired_arrays(df, "eehda_absolute", "epss_only", "proposed_full")
    assert len(seeds) == 10
    assert base.shape == cand.shape == (10,)
    # epss_only is 60+s, proposed_full is 40+s -> candidate strictly lower.
    assert np.all(cand < base)


def test_paired_arrays_drops_unmatched_seed_with_warning():
    df = _toy_frame()
    # Remove proposed_full for seed 10 -> that seed cannot be paired.
    df = df[~((df["seed"] == 10) & (df["strategy"] == "proposed_full"))]
    with pytest.warns(UserWarning):
        base, cand, seeds = paired_arrays(df, "eehda_absolute", "epss_only", "proposed_full")
    assert 10 not in seeds
    assert len(seeds) == 9


def test_paired_arrays_raises_below_two_pairs():
    df = _toy_frame(n_seeds=1)
    with pytest.raises(ValueError):
        paired_arrays(df, "eehda_absolute", "epss_only", "proposed_full")


def test_paired_arrays_raises_for_missing_strategy():
    df = _toy_frame()
    with pytest.raises(ValueError):
        paired_arrays(df, "eehda_absolute", "epss_only", "does_not_exist")


# ---------------------------------------------------------------------------
# C-E. difference / effect size
# ---------------------------------------------------------------------------


def test_paired_mean_difference():
    cand = np.array([1.0, 2.0, 3.0])
    base = np.array([0.0, 0.0, 0.0])
    assert paired_mean_difference(cand, base) == pytest.approx(2.0)


def test_relative_difference_zero_baseline_is_nan():
    assert np.isnan(relative_difference(5.0, 0.0))


def test_relative_difference_basic():
    assert relative_difference(120.0, 100.0) == pytest.approx(0.2)
    # Uses abs(baseline) in the denominator.
    assert relative_difference(-80.0, -100.0) == pytest.approx(0.2)


def test_paired_cohens_d_hand_computed():
    # diffs = [1, 2, 3] -> mean 2, sample std (ddof=1) = 1 -> d = 2.
    cand = np.array([1.0, 2.0, 3.0])
    base = np.array([0.0, 0.0, 0.0])
    assert paired_cohens_d(cand, base) == pytest.approx(2.0)


def test_paired_cohens_d_zero_diff_is_zero():
    x = np.array([5.0, 5.0, 5.0])
    assert paired_cohens_d(x, x) == 0.0


def test_paired_cohens_d_constant_nonzero_diff_is_inf():
    cand = np.array([3.0, 3.0, 3.0])
    base = np.array([1.0, 1.0, 1.0])
    d = paired_cohens_d(cand, base)
    assert np.isinf(d) and d > 0
    # Negative constant difference -> -inf.
    d2 = paired_cohens_d(base, cand)
    assert np.isinf(d2) and d2 < 0


# ---------------------------------------------------------------------------
# F. Wilcoxon
# ---------------------------------------------------------------------------


def test_wilcoxon_all_zero_diffs_returns_p_one():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    stat, p = wilcoxon_signed_rank(x, x)
    assert stat == 0.0
    assert p == 1.0


def test_wilcoxon_consistent_difference_small_p():
    df = _toy_frame()
    base, cand, _ = paired_arrays(df, "eehda_absolute", "epss_only", "proposed_full")
    _, p = wilcoxon_signed_rank(cand, base)
    # 10 consistently-signed differences -> the test should be confident.
    assert p < 0.05


# ---------------------------------------------------------------------------
# G. Holm-Bonferroni
# ---------------------------------------------------------------------------


def test_holm_bonferroni_orders_and_adjusts():
    pvals = {"a": 0.001, "b": 0.04, "c": 0.20}
    out = holm_bonferroni(pvals, alpha=0.05)
    assert set(out) == {"a", "b", "c"}
    # Adjusted p-values are non-decreasing in the sorted-by-raw order.
    assert out["a"]["p_value_adjusted"] <= out["b"]["p_value_adjusted"]
    assert out["b"]["p_value_adjusted"] <= out["c"]["p_value_adjusted"]
    # Smallest raw p, multiplied by m=3, stays below alpha.
    assert out["a"]["p_value_adjusted"] == pytest.approx(0.003)
    assert out["a"]["reject_null"] is True


def test_holm_bonferroni_empty():
    assert holm_bonferroni({}) == {}


# ---------------------------------------------------------------------------
# H-J. bootstrap
# ---------------------------------------------------------------------------


def test_bootstrap_ci_deterministic_and_brackets_mean():
    rng = np.random.default_rng(0)
    values = rng.normal(10.0, 2.0, size=200)
    lo1, hi1 = bootstrap_ci(values, seed=7)
    lo2, hi2 = bootstrap_ci(values, seed=7)
    assert (lo1, hi1) == (lo2, hi2)
    assert lo1 < float(np.mean(values)) < hi1


def test_bootstrap_ci_different_seed_differs():
    rng = np.random.default_rng(1)
    values = rng.normal(0.0, 1.0, size=100)
    a = bootstrap_ci(values, seed=1)
    b = bootstrap_ci(values, seed=2)
    assert a != b


def test_bootstrap_ci_bca_deterministic_and_finite():
    rng = np.random.default_rng(2)
    values = rng.normal(5.0, 1.0, size=150)
    lo1, hi1 = bootstrap_ci_bca(values, seed=3, B=500)
    lo2, hi2 = bootstrap_ci_bca(values, seed=3, B=500)
    assert (lo1, hi1) == (lo2, hi2)
    assert np.isfinite(lo1) and np.isfinite(hi1)
    assert lo1 < hi1


def test_bootstrap_ci_bca_degenerate_falls_back_with_warning():
    # All-identical values -> BCa acceleration is undefined; fall back.
    values = np.full(50, 3.0)
    with pytest.warns(UserWarning):
        lo, hi = bootstrap_ci_bca(values, seed=0, B=200)
    assert lo == hi == pytest.approx(3.0)


def test_paired_bootstrap_ci_resamples_pairs():
    df = _toy_frame()
    base, cand, _ = paired_arrays(df, "eehda_absolute", "epss_only", "proposed_full")
    lo, hi = paired_bootstrap_ci(cand, base, seed=5)
    # Mean paired difference is a constant -20 (40+s vs 60+s) for all seeds,
    # so every resample yields exactly -20 -> degenerate CI at -20.
    assert lo == pytest.approx(-20.0)
    assert hi == pytest.approx(-20.0)


# ---------------------------------------------------------------------------
# K-L. comparisons
# ---------------------------------------------------------------------------


def test_compare_to_baseline_fields():
    df = _toy_frame()
    res = compare_to_baseline(df, "eehda_absolute", "epss_only", "proposed_full", seed=0)
    assert isinstance(res, StatTestResult)
    assert res.baseline_strategy == "epss_only"
    assert res.candidate_strategy == "proposed_full"
    assert res.n_pairs == 10
    assert res.baseline_mean == pytest.approx(65.5)  # mean of 60+s, s=1..10
    assert res.candidate_mean == pytest.approx(45.5)  # mean of 40+s
    assert res.mean_difference == pytest.approx(-20.0)
    assert res.p_value < 0.05
    assert res.ci_low is not None and res.ci_high is not None


def test_compare_many_to_baseline_adjusts_p_values():
    df = _toy_frame()
    out = compare_many_to_baseline(
        df, "eehda_absolute", "random", ["epss_only", "proposed_full"], seed=0
    )
    assert isinstance(out, pd.DataFrame)
    assert len(out) == 2
    assert {"p_value", "p_value_adjusted", "reject_null", "family_alpha"} <= set(out.columns)
    # Adjusted p-values must be >= raw p-values.
    assert (out["p_value_adjusted"] >= out["p_value"]).all()


# ---------------------------------------------------------------------------
# M. minimum detectable effect
# ---------------------------------------------------------------------------


def test_minimum_detectable_effect_decreases_with_n():
    small = minimum_detectable_effect(10)
    large = minimum_detectable_effect(100)
    assert small > large > 0


def test_minimum_detectable_effect_raises_for_tiny_n():
    with pytest.raises(ValueError):
        minimum_detectable_effect(2)


# ---------------------------------------------------------------------------
# N. validation
# ---------------------------------------------------------------------------


def test_validate_per_seed_metric_frame_accepts_valid():
    df = _toy_frame()
    validate_per_seed_metric_frame(df)  # must not raise


def test_validate_per_seed_metric_frame_raises_on_missing_column():
    df = _toy_frame().drop(columns=["value"])
    with pytest.raises(ValueError):
        validate_per_seed_metric_frame(df)


def test_validate_per_seed_metric_frame_raises_on_duplicate():
    df = _toy_frame()
    dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        validate_per_seed_metric_frame(dup)


def test_validate_per_seed_metric_frame_raises_on_nonnumeric_value():
    df = pd.DataFrame(
        {
            "seed": [1, 2],
            "strategy": ["proposed_full", "proposed_full"],
            "metric": ["eehda_absolute", "eehda_absolute"],
            "value": ["not_a_number", "still_not"],  # object dtype from the start
        }
    )
    with pytest.raises(ValueError):
        validate_per_seed_metric_frame(df)
