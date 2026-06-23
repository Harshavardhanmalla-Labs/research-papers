"""Calibration helpers: training-frame prep, time-block folds, weight extraction.

These helpers are model-agnostic. The actual logistic / ridge fitting lives
in ``paper1.model.linear_model``. All randomness flows through the project's
deterministic seed utilities; there is no global random state.
"""

from __future__ import annotations

import warnings as _warnings
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_class_weight

from paper1.model.weights import FEATURE_COLUMNS, get_weights, normalize_weights
from paper1.utils.seeds import make_rng

__all__ = [
    "bootstrap_weight_ci",
    "class_weight_from_labels",
    "coefficients_to_weights",
    "make_time_block_folds",
    "prepare_training_frame",
    "selection_mask",
]


def _to_ordinal(value: Any) -> int:
    if isinstance(value, datetime):
        return value.toordinal()
    if isinstance(value, date):
        return value.toordinal()
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, str):
        return date.fromisoformat(value[:10]).toordinal()
    raise TypeError(f"cannot order decision time {value!r} ({type(value).__name__})")


def _is_na(v: Any) -> bool:
    if v is None or v is pd.NA:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def selection_mask(
    feature_frame: pd.DataFrame,
    label_series: pd.Series | list,
    split_series: pd.Series | list | None = None,
    allowed_splits: tuple[str, ...] = ("train",),
) -> np.ndarray:
    """Boolean mask selecting non-censored rows in the allowed split(s)."""
    n = len(feature_frame)
    labels = list(label_series)
    if len(labels) != n:
        raise ValueError(f"label_series length {len(labels)} != feature_frame {n}")
    mask = np.array([not _is_na(v) for v in labels], dtype=bool)
    if split_series is not None:
        splits = list(split_series)
        if len(splits) != n:
            raise ValueError(f"split_series length {len(splits)} != feature_frame {n}")
        allowed = set(allowed_splits)
        split_mask = np.array([s in allowed for s in splits], dtype=bool)
        mask = mask & split_mask
    return mask


def prepare_training_frame(
    feature_frame: pd.DataFrame,
    label_series: pd.Series | list,
    split_series: pd.Series | list | None = None,
    allowed_splits: tuple[str, ...] = ("train",),
) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) for fitting: feature columns + int 0/1 labels.

    Censored (pd.NA) labels are dropped; if ``split_series`` is given,
    only rows in ``allowed_splits`` are kept. Raises if features contain
    NaN or if either class is absent after selection.
    """
    missing = set(FEATURE_COLUMNS) - set(feature_frame.columns)
    if missing:
        raise ValueError(f"feature_frame missing feature columns: {sorted(missing)}")

    mask = selection_mask(feature_frame, label_series, split_series, allowed_splits)
    df = feature_frame.reset_index(drop=True)
    labels = pd.Series(list(label_series))

    X = df.loc[mask, FEATURE_COLUMNS].reset_index(drop=True)
    if X.isna().any().any():
        nan_cols = [c for c in FEATURE_COLUMNS if X[c].isna().any()]
        raise ValueError(f"training features contain NaN in columns: {nan_cols}")

    y_raw = labels[mask]
    y = y_raw.astype("boolean").astype("int64").reset_index(drop=True)

    if int((y == 1).sum()) == 0:
        raise ValueError("no positive labels in training selection")
    if int((y == 0).sum()) == 0:
        raise ValueError("no negative labels in training selection")
    return X, y


def make_time_block_folds(
    decision_times: list | pd.Series,
    n_splits: int = 5,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Temporal CV folds (no shuffling); validation block is later than train.

    Positions index into ``decision_times`` order. When there are too few
    samples for ``n_splits`` folds, the split count is reduced; fewer than
    3 samples raises a clear error.
    """
    times = list(decision_times)
    n = len(times)
    if n < 3:
        raise ValueError(f"need at least 3 samples for time-block folds; got {n}")
    ordinals = np.array([_to_ordinal(t) for t in times])
    order = np.argsort(ordinals, kind="stable")  # positions sorted by time
    effective = min(n_splits, n - 1)
    if effective < 2:
        raise ValueError(
            f"cannot form >=2 temporal folds from {n} samples with n_splits={n_splits}"
        )
    tss = TimeSeriesSplit(n_splits=effective)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for tr_sorted, va_sorted in tss.split(order):
        folds.append((order[tr_sorted], order[va_sorted]))
    return folds


def class_weight_from_labels(y: pd.Series | np.ndarray | list) -> dict[int, float]:
    """Balanced class weights as a {0: w0, 1: w1} dict (deterministic)."""
    arr = np.asarray(list(y))
    classes = np.unique(arr)
    if set(classes.tolist()) - {0, 1}:
        raise ValueError(f"labels must be 0/1; got classes {classes.tolist()}")
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=arr)
    return {int(c): float(w) for c, w in zip(classes, weights, strict=True)}


def coefficients_to_weights(
    coef: dict[str, float],
    clip_negative: bool = True,
    normalize: bool = True,
) -> tuple[dict[str, float], list[str]]:
    """Convert model coefficients to a scoring weight vector.

    Returns ``(weights, clipped_features)``. Negative coefficients are
    clipped to zero (default). If every coefficient is non-positive, the
    weights fall back to ``w_hand`` with a warning. R remains a positive
    weight; the scoring formula subtracts it.
    """
    raw = {f: float(coef.get(f, 0.0)) for f in FEATURE_COLUMNS}
    clipped: list[str] = []
    if clip_negative:
        for f in FEATURE_COLUMNS:
            if raw[f] < 0.0:
                clipped.append(f)
                raw[f] = 0.0

    if sum(raw.values()) <= 0.0:
        _warnings.warn(
            "all coefficients non-positive after clipping; falling back to w_hand",
            stacklevel=2,
        )
        return get_weights("w_hand"), sorted(clipped)

    weights = normalize_weights(raw) if normalize else raw
    return weights, sorted(clipped)


def bootstrap_weight_ci(
    fit_fn: Callable[[pd.DataFrame, pd.Series], dict[str, float]],
    X: pd.DataFrame,
    y: pd.Series,
    B: int = 200,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[dict[str, dict[str, float]], int]:
    """Bootstrap per-feature weight confidence intervals.

    Returns ``(ci, n_skipped)`` where ``ci[feature]`` has ``low``/``high``/
    ``point`` keys. Resamples whose labels collapse to a single class are
    skipped and counted. Deterministic given ``seed``.
    """
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0, 1)")
    rng = make_rng(seed)
    n = len(X)
    point = fit_fn(X.reset_index(drop=True), y.reset_index(drop=True))

    samples: dict[str, list[float]] = {f: [] for f in FEATURE_COLUMNS}
    skipped = 0
    y_arr = y.to_numpy()
    for _ in range(B):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_arr[idx])) < 2:
            skipped += 1
            continue
        Xb = X.iloc[idx].reset_index(drop=True)
        yb = y.iloc[idx].reset_index(drop=True)
        w = fit_fn(Xb, yb)
        for f in FEATURE_COLUMNS:
            samples[f].append(float(w.get(f, 0.0)))

    lo_q = 100.0 * (alpha / 2.0)
    hi_q = 100.0 * (1.0 - alpha / 2.0)
    ci: dict[str, dict[str, float]] = {}
    for f in FEATURE_COLUMNS:
        vals = samples[f]
        if vals:
            ci[f] = {
                "low": float(np.percentile(vals, lo_q)),
                "high": float(np.percentile(vals, hi_q)),
                "point": float(point.get(f, 0.0)),
            }
        else:
            ci[f] = {"low": float("nan"), "high": float("nan"), "point": float(point.get(f, 0.0))}
    return ci, skipped
