"""LightGBM reference comparator tests."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from paper1.model.gbt_comparator import (
    GBTResult,
    fit_gbt,
    load_gbt_config,
    load_gbt_result,
    predict_gbt,
    rank_pairs_gbt,
    save_gbt_result,
)
from paper1.model.strategies import rank_pairs
from paper1.model.weights import FEATURE_COLUMNS


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def _toy(n: int = 300, seed: int = 0, na_fraction: float = 0.1):
    rng = np.random.default_rng(seed)
    data: dict[str, list | np.ndarray] = {
        "pair_id": [f"P-{i:05d}" for i in range(n)],
        "cve_id": [f"CVE-2024-{1000 + (i % 50):04d}" for i in range(n)],
        "host_id": [f"H-{i:05d}" for i in range(n)],
    }
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
    labels = pd.Series((rng.random(n) < _sigmoid(z)).astype(bool), dtype="boolean")
    na_idx = rng.choice(n, size=int(na_fraction * n), replace=False)
    for i in na_idx:
        labels.iloc[int(i)] = pd.NA

    base = date(2024, 6, 1)
    times = [base + timedelta(days=i) for i in range(n)]
    order = np.argsort([t.toordinal() for t in times])
    splits = [""] * n
    for rank, pos in enumerate(order):
        if rank < int(0.6 * n):
            splits[pos] = "train"
        elif rank < int(0.7 * n):
            splits[pos] = "gap"
        else:
            splits[pos] = "test"
    return ff, labels, pd.Series(splits), times


def _train_nonNA_count(labels, splits) -> int:
    return sum(
        1
        for lab, sp in zip(list(labels), list(splits), strict=True)
        if sp == "train" and not pd.isna(lab)
    )


def _pair_frame(ff: pd.DataFrame) -> pd.DataFrame:
    return ff[["pair_id", "cve_id", "host_id"]].copy()


# -----------------------------------------------------------------------
# config
# -----------------------------------------------------------------------


def test_load_gbt_config_validates():
    cfg = load_gbt_config()
    assert cfg["implementation"] == "lightgbm"
    assert list(cfg["feature_set"]) == list(FEATURE_COLUMNS)
    assert cfg["objective"] == "binary"


def test_load_gbt_config_bad_feature_set_fails(tmp_path):
    import yaml

    cfg = load_gbt_config()
    cfg["feature_set"] = ["E", "K"]  # wrong
    p = tmp_path / "bad_gbt.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError):
        load_gbt_config(p)


def test_load_gbt_config_missing_key_fails(tmp_path):
    import yaml

    cfg = load_gbt_config()
    del cfg["objective"]
    p = tmp_path / "bad_gbt.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError):
        load_gbt_config(p)


def test_load_gbt_config_wrong_implementation_fails(tmp_path):
    import yaml

    cfg = load_gbt_config()
    cfg["implementation"] = "xgboost"
    p = tmp_path / "bad_gbt.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError):
        load_gbt_config(p)


# -----------------------------------------------------------------------
# fit
# -----------------------------------------------------------------------


def test_fit_gbt_returns_model_and_result():
    ff, labels, splits, times = _toy()
    model, result = fit_gbt(ff, labels, times, splits, seed=0)
    assert isinstance(result, GBTResult)
    assert result.model_type == "lightgbm"
    assert result.feature_columns == list(FEATURE_COLUMNS)
    assert result.selected_iteration >= 1


def test_fit_gbt_deterministic_under_seed():
    ff, labels, splits, times = _toy()
    m1, r1 = fit_gbt(ff, labels, times, splits, seed=0)
    m2, r2 = fit_gbt(ff, labels, times, splits, seed=0)
    p1 = predict_gbt(m1, ff)
    p2 = predict_gbt(m2, ff)
    assert np.allclose(p1.to_numpy(), p2.to_numpy())
    assert r1.selected_iteration == r2.selected_iteration


def test_fit_gbt_uses_only_train_rows():
    ff, labels, splits, times = _toy()
    _, result = fit_gbt(ff, labels, times, splits, seed=0)
    assert result.train_size == _train_nonNA_count(labels, splits)


def test_fit_gbt_excludes_censored_labels():
    ff, labels, splits, times = _toy(na_fraction=0.2)
    _, result = fit_gbt(ff, labels, times, splits, seed=0)
    assert result.positive_count + result.negative_count == result.train_size


def test_fit_gbt_one_class_validation_warns_not_crash():
    ff, labels, splits, times = _toy(n=150, seed=4)
    lab = labels.copy()
    # Force the latest-by-time training rows (the validation block) to a
    # single class so early stopping cannot run.
    order = np.argsort([t.toordinal() for t in times])
    train_positions = [pos for pos in order if splits.iloc[pos] == "train"]
    n_val = max(1, int(round(0.2 * len(train_positions))))
    for pos in train_positions[-n_val:]:
        lab.iloc[pos] = False
    with pytest.warns(UserWarning):
        model, result = fit_gbt(ff, lab, times, splits, seed=0)
    assert result.feature_columns == list(FEATURE_COLUMNS)


# -----------------------------------------------------------------------
# predict + rank
# -----------------------------------------------------------------------


def test_predict_gbt_in_unit_interval():
    ff, labels, splits, times = _toy()
    model, _ = fit_gbt(ff, labels, times, splits, seed=0)
    preds = predict_gbt(model, ff)
    assert (preds >= 0.0).all() and (preds <= 1.0).all()
    assert not preds.isna().any()


def test_predict_gbt_index_aligns():
    ff, labels, splits, times = _toy()
    model, _ = fit_gbt(ff, labels, times, splits, seed=0)
    subset = ff.iloc[10:20]
    preds = predict_gbt(model, subset)
    assert list(preds.index) == list(subset.index)


def test_predict_gbt_missing_feature_raises():
    ff, labels, splits, times = _toy()
    model, _ = fit_gbt(ff, labels, times, splits, seed=0)
    with pytest.raises(ValueError):
        predict_gbt(model, ff.drop(columns=["R"]))


def test_rank_pairs_gbt_contiguous_and_sorted():
    ff, labels, splits, times = _toy()
    model, _ = fit_gbt(ff, labels, times, splits, seed=0)
    out = rank_pairs_gbt(_pair_frame(ff), ff, model)
    assert out["rank"].tolist() == list(range(1, len(ff) + 1))
    assert not out["pair_id"].duplicated().any()
    assert out["strategy_name"].iloc[0] == "gbt_comparator"
    # scores monotonically non-increasing by rank
    scores = out["priority_score"].to_numpy()
    assert (np.diff(scores) <= 1e-12).all()


# -----------------------------------------------------------------------
# strategy integration
# -----------------------------------------------------------------------


def test_strategy_gbt_with_model_returns_ranking():
    ff, labels, splits, times = _toy()
    model, _ = fit_gbt(ff, labels, times, splits, seed=0)
    out = rank_pairs("gbt_comparator", _pair_frame(ff), ff, gbt_model=model)
    assert len(out) == len(ff)
    assert out["rank"].tolist() == list(range(1, len(ff) + 1))
    assert out["strategy_name"].iloc[0] == "gbt_comparator"


def test_strategy_gbt_without_model_raises():
    ff, labels, splits, times = _toy()
    with pytest.raises(ValueError):
        rank_pairs("gbt_comparator", _pair_frame(ff), ff)


# -----------------------------------------------------------------------
# artifact roundtrip + leakage
# -----------------------------------------------------------------------


def test_save_load_gbt_result_roundtrip(tmp_path):
    ff, labels, splits, times = _toy()
    _, result = fit_gbt(ff, labels, times, splits, seed=0)
    p = tmp_path / "gbt.json"
    save_gbt_result(result, p)
    loaded = load_gbt_result(p)
    assert isinstance(loaded, GBTResult)
    assert loaded.model_dump(mode="json") == result.model_dump(mode="json")


def test_no_future_leakage_test_rows_excluded():
    ff, labels, splits, times = _toy()
    # Deliberately ensure test rows carry labels; train_size must still
    # equal only the train, non-NA count.
    lab = labels.copy()
    for i in range(len(lab)):
        if splits.iloc[i] == "test" and pd.isna(lab.iloc[i]):
            lab.iloc[i] = True
    _, result = fit_gbt(ff, lab, times, splits, seed=0)
    assert result.train_size == _train_nonNA_count(lab, splits)
