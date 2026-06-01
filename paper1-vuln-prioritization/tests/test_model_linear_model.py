"""Linear weight-calibration tests."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from paper1.model.linear_model import (
    CalibrationResult,
    fit_weights_linear,
    fit_weights_logit,
    load_calibration_result,
    register_calibrated_weights,
    save_calibration_result,
)
from paper1.model.scoring import score_pairs_linear
from paper1.model.weights import FEATURE_COLUMNS, get_weights


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def _toy(n: int = 200, seed: int = 0, na_fraction: float = 0.1):
    """Feature frame + labels correlated with E/C/X and inverse R, plus splits.

    Returns (feature_frame, labels, split_series, decision_times).
    """
    rng = np.random.default_rng(seed)
    data: dict[str, list | np.ndarray] = {"pair_id": [f"P-{i:05d}" for i in range(n)]}
    for f in FEATURE_COLUMNS:
        data[f] = rng.random(n)
    ff = pd.DataFrame(data)

    z = (
        2.0 * ff["E"].to_numpy()
        + 1.5 * ff["C"].to_numpy()
        + 1.0 * ff["X"].to_numpy()
        - 1.5 * ff["R"].to_numpy()
        - 1.0
    )
    probs = _sigmoid(z)
    raw_labels = (rng.random(n) < probs).astype(bool)

    labels = pd.Series(raw_labels, dtype="boolean")
    # Censor a fraction.
    na_idx = rng.choice(n, size=int(na_fraction * n), replace=False)
    for i in na_idx:
        labels.iloc[int(i)] = pd.NA

    # Decision times spread over a range, then split by chronological position.
    base = date(2024, 6, 1)
    decision_times = [base + timedelta(days=int(i * 1)) for i in range(n)]
    order = np.argsort([t.toordinal() for t in decision_times])
    splits = [""] * n
    train_cut = int(0.6 * n)
    gap_cut = int(0.7 * n)
    for rank, pos in enumerate(order):
        if rank < train_cut:
            splits[pos] = "train"
        elif rank < gap_cut:
            splits[pos] = "gap"
        else:
            splits[pos] = "test"
    return ff, labels, pd.Series(splits), decision_times


def _train_nonNA_count(labels, splits) -> int:
    return sum(
        1
        for lab, sp in zip(list(labels), list(splits), strict=True)
        if sp == "train" and not pd.isna(lab)
    )


# -----------------------------------------------------------------------
# logit
# -----------------------------------------------------------------------


def test_fit_logit_returns_all_feature_columns():
    ff, labels, splits, times = _toy()
    res = fit_weights_logit(ff, labels, times, splits, seed=0)
    assert set(res.weights.keys()) == set(FEATURE_COLUMNS)
    assert abs(sum(res.weights.values()) - 1.0) < 1e-9


def test_fit_logit_deterministic_under_seed():
    ff, labels, splits, times = _toy()
    a = fit_weights_logit(ff, labels, times, splits, seed=0)
    b = fit_weights_logit(ff, labels, times, splits, seed=0)
    assert a.weights == b.weights
    assert a.selected_hyperparameter == b.selected_hyperparameter


def test_fit_logit_uses_only_train_rows():
    ff, labels, splits, times = _toy()
    res = fit_weights_logit(ff, labels, times, splits, seed=0)
    assert res.train_size == _train_nonNA_count(labels, splits)


def test_fit_logit_selects_hyperparameter_from_grid():
    ff, labels, splits, times = _toy()
    grid = (0.01, 0.1, 1.0, 10.0)
    res = fit_weights_logit(ff, labels, times, splits, C_grid=grid, seed=0)
    assert res.selected_hyperparameter in grid


def test_fit_logit_excludes_censored_labels():
    ff, labels, splits, times = _toy(na_fraction=0.2)
    res = fit_weights_logit(ff, labels, times, splits, seed=0)
    # positive + negative counts must equal train_size (no NA included)
    assert res.positive_count + res.negative_count == res.train_size


def test_fit_logit_clips_negative_r_coefficient():
    # Labels are inversely related to R, so the R coefficient should be
    # negative and therefore clipped to a zero weight.
    ff, labels, splits, times = _toy(seed=3)
    res = fit_weights_logit(ff, labels, times, splits, seed=0)
    assert res.weights["R"] == 0.0
    assert "R" in res.clipped_features


# -----------------------------------------------------------------------
# ridge
# -----------------------------------------------------------------------


def test_fit_linear_returns_all_feature_columns():
    ff, labels, splits, times = _toy()
    res = fit_weights_linear(ff, labels, times, splits, seed=0)
    assert set(res.weights.keys()) == set(FEATURE_COLUMNS)
    assert res.model_type == "ridge"


def test_fit_linear_deterministic():
    ff, labels, splits, times = _toy()
    a = fit_weights_linear(ff, labels, times, splits, seed=0)
    b = fit_weights_linear(ff, labels, times, splits, seed=0)
    assert a.weights == b.weights


# -----------------------------------------------------------------------
# artifact roundtrip + registration
# -----------------------------------------------------------------------


def test_save_load_roundtrip_stable(tmp_path):
    ff, labels, splits, times = _toy()
    res = fit_weights_logit(ff, labels, times, splits, seed=0)
    p = tmp_path / "calib.json"
    save_calibration_result(res, p)
    loaded = load_calibration_result(p)
    assert isinstance(loaded, CalibrationResult)
    assert loaded.weights == res.weights
    assert loaded.model_dump(mode="json") == res.model_dump(mode="json")


def test_register_calibrated_weights_makes_get_weights_work():
    ff, labels, splits, times = _toy()
    res = fit_weights_logit(ff, labels, times, splits, seed=0)
    register_calibrated_weights(res, "w_logit_calibrated")
    w = get_weights("w_logit_calibrated")
    assert abs(sum(w.values()) - 1.0) < 1e-9
    # Placeholders must still exist after registration.
    assert get_weights("w_logit_placeholder") is not None


def test_calibrated_weights_score_pairs_without_nan():
    ff, labels, splits, times = _toy()
    res = fit_weights_logit(ff, labels, times, splits, seed=0)
    register_calibrated_weights(res, "w_logit_calibrated_2")
    scored = score_pairs_linear(ff, get_weights("w_logit_calibrated_2"))
    assert not scored["priority_score"].isna().any()


# -----------------------------------------------------------------------
# robustness
# -----------------------------------------------------------------------


def test_one_class_validation_fold_handled_with_warning():
    # Construct data where an early temporal fold is all-negative.
    ff, labels, splits, times = _toy(n=120, seed=9)
    # Force the earliest 20 train labels (by time) to negative to create a
    # single-class fold; this should warn, not crash.
    lab = labels.copy()
    order = np.argsort([t.toordinal() for t in times])
    forced = 0
    for pos in order:
        if splits.iloc[pos] == "train" and not pd.isna(lab.iloc[pos]):
            lab.iloc[pos] = False
            forced += 1
            if forced >= 20:
                break
    with pytest.warns(UserWarning):
        res = fit_weights_logit(ff, lab, times, splits, seed=0)
    assert set(res.weights.keys()) == set(FEATURE_COLUMNS)


def test_compute_ci_populates_weight_ci():
    ff, labels, splits, times = _toy()
    res = fit_weights_logit(
        ff, labels, times, splits, seed=0, compute_ci=True, bootstrap_B=20
    )
    assert res.weight_ci is not None
    for f in FEATURE_COLUMNS:
        assert {"low", "high", "point"} <= set(res.weight_ci[f].keys())
