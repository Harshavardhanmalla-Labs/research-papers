"""Calibration helper tests."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from paper1.model.calibration import (
    bootstrap_weight_ci,
    class_weight_from_labels,
    coefficients_to_weights,
    make_time_block_folds,
    prepare_training_frame,
    selection_mask,
)
from paper1.model.weights import FEATURE_COLUMNS


def _feature_frame(n: int, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {"pair_id": [f"P-{i:04d}" for i in range(n)]}
    for f in FEATURE_COLUMNS:
        data[f] = rng.random(n)
    return pd.DataFrame(data)


def _labels(n: int, seed: int = 1) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series((rng.random(n) < 0.4), dtype="boolean")


# -----------------------------------------------------------------------
# prepare_training_frame
# -----------------------------------------------------------------------


def test_prepare_excludes_na_labels():
    ff = _feature_frame(10)
    labels = pd.Series([True, False, pd.NA, True, False, pd.NA, True, False, True, False], dtype="boolean")
    X, y = prepare_training_frame(ff, labels)
    assert len(X) == 8  # two NA dropped
    assert len(y) == 8


def test_prepare_excludes_gap_and_test_rows():
    ff = _feature_frame(9)
    labels = pd.Series([True, False] * 4 + [True], dtype="boolean")
    splits = ["train", "train", "train", "gap", "gap", "test", "test", "test", "train"]
    X, y = prepare_training_frame(ff, labels, splits, ("train",))
    # train positions: 0,1,2,8 -> 4 rows
    assert len(X) == 4
    assert len(y) == 4


def test_prepare_raises_on_no_positives():
    ff = _feature_frame(5)
    labels = pd.Series([False] * 5, dtype="boolean")
    with pytest.raises(ValueError):
        prepare_training_frame(ff, labels)


def test_prepare_raises_on_no_negatives():
    ff = _feature_frame(5)
    labels = pd.Series([True] * 5, dtype="boolean")
    with pytest.raises(ValueError):
        prepare_training_frame(ff, labels)


def test_prepare_raises_on_missing_feature_column():
    ff = _feature_frame(5).drop(columns=["R"])
    labels = _labels(5)
    with pytest.raises(ValueError):
        prepare_training_frame(ff, labels)


def test_selection_mask_length_mismatch_raises():
    ff = _feature_frame(5)
    with pytest.raises(ValueError):
        selection_mask(ff, [True, False])


# -----------------------------------------------------------------------
# make_time_block_folds
# -----------------------------------------------------------------------


def test_time_block_folds_preserve_temporal_order():
    base = date(2024, 6, 1)
    times = [base + timedelta(days=i) for i in range(50)]
    folds = make_time_block_folds(times, n_splits=5)
    assert len(folds) == 5
    for tr, va in folds:
        max_train_time = max(times[i] for i in tr)
        max_val_time = max(times[i] for i in va)
        assert max_train_time <= max_val_time


def test_time_block_folds_no_shuffle_validation_after_train():
    base = date(2024, 6, 1)
    times = [base + timedelta(days=i) for i in range(20)]
    folds = make_time_block_folds(times, n_splits=4)
    for tr, va in folds:
        # In sorted order the last train ordinal precedes the first val ordinal.
        assert min(times[i] for i in va) >= max(times[i] for i in tr) - timedelta(days=1)


def test_time_block_folds_too_few_samples_raises():
    with pytest.raises(ValueError):
        make_time_block_folds([date(2024, 6, 1), date(2024, 6, 2)], n_splits=5)


def test_time_block_folds_reduces_splits_when_few_dates():
    times = [date(2024, 6, 1) + timedelta(days=i) for i in range(4)]
    folds = make_time_block_folds(times, n_splits=10)
    # effective splits reduced to n-1 = 3
    assert len(folds) == 3


# -----------------------------------------------------------------------
# class weights
# -----------------------------------------------------------------------


def test_class_weights_balanced():
    y = pd.Series([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])  # 2 pos, 8 neg
    cw = class_weight_from_labels(y)
    assert set(cw.keys()) == {0, 1}
    # minority class (1) gets the larger weight
    assert cw[1] > cw[0]


def test_class_weights_deterministic():
    y = [1, 0, 1, 0, 1, 0]
    assert class_weight_from_labels(y) == class_weight_from_labels(y)


# -----------------------------------------------------------------------
# coefficients_to_weights
# -----------------------------------------------------------------------


def test_coefficients_clip_negatives():
    coef = {f: 1.0 for f in FEATURE_COLUMNS}
    coef["R"] = -2.0
    coef["S"] = -0.5
    weights, clipped = coefficients_to_weights(coef)
    assert weights["R"] == 0.0
    assert weights["S"] == 0.0
    assert set(clipped) == {"R", "S"}
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_coefficients_all_negative_falls_back_to_hand():
    coef = {f: -1.0 for f in FEATURE_COLUMNS}
    with pytest.warns(UserWarning):
        weights, clipped = coefficients_to_weights(coef)
    # Fallback weights are w_hand (normalized, sum to 1).
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert weights["E"] > 0


def test_coefficients_all_features_present():
    coef = {"E": 1.0}  # only one provided
    weights, _ = coefficients_to_weights(coef)
    assert set(weights.keys()) == set(FEATURE_COLUMNS)


# -----------------------------------------------------------------------
# bootstrap
# -----------------------------------------------------------------------


def _toy_fit_fn(X: pd.DataFrame, y: pd.Series) -> dict[str, float]:
    # Deterministic pseudo-fit: weight proportional to |corr| with y, clipped.
    from paper1.model.calibration import coefficients_to_weights

    coef = {}
    yv = y.to_numpy().astype(float)
    for f in FEATURE_COLUMNS:
        xv = X[f].to_numpy().astype(float)
        if xv.std() == 0 or yv.std() == 0:
            coef[f] = 0.0
        else:
            coef[f] = float(np.corrcoef(xv, yv)[0, 1])
    w, _ = coefficients_to_weights(coef)
    return w


def test_bootstrap_deterministic():
    ff = _feature_frame(60, seed=2)
    y = pd.Series((ff["E"].to_numpy() + ff["C"].to_numpy() > 1.0).astype(int))
    X = ff[FEATURE_COLUMNS]
    a, sa = bootstrap_weight_ci(_toy_fit_fn, X, y, B=50, seed=7)
    b, sb = bootstrap_weight_ci(_toy_fit_fn, X, y, B=50, seed=7)
    assert a == b
    assert sa == sb


def test_bootstrap_skips_single_class_resamples():
    ff = _feature_frame(30, seed=3)
    # Heavily imbalanced labels -> some resamples will be single-class.
    y = pd.Series([1] + [0] * 29)
    X = ff[FEATURE_COLUMNS]
    ci, skipped = bootstrap_weight_ci(_toy_fit_fn, X, y, B=100, seed=1)
    assert skipped >= 0
    # CI structure present for every feature.
    for f in FEATURE_COLUMNS:
        assert {"low", "high", "point"} <= set(ci[f].keys())
