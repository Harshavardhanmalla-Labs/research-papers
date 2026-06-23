"""Linear weight calibration: L2 logistic and L2 ridge regression.

Training uses only the ``train`` split (Phase 4), only non-censored
labels, and temporal cross-validation (Phase 6 calibration helpers) to
select the regularization strength. Coefficients are converted to a
non-negative, normalized scoring weight vector; negative coefficients
are clipped to zero (documented design choice for Phase 6).
"""

from __future__ import annotations

import warnings as _warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, field_validator
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score

from paper1.model.calibration import (
    bootstrap_weight_ci,
    coefficients_to_weights,
    make_time_block_folds,
    prepare_training_frame,
    selection_mask,
)
from paper1.model.weights import (
    FEATURE_COLUMNS,
)
from paper1.model.weights import (
    register_calibrated_weights as _register_calibrated_weights,
)
from paper1.utils.io import atomic_write_json, read_json

__all__ = [
    "CalibrationResult",
    "fit_weights_linear",
    "fit_weights_logit",
    "load_calibration_result",
    "register_calibrated_weights",
    "save_calibration_result",
]

CV_METRIC = "average_precision"


class CalibrationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    model_type: Literal["logit", "ridge"]
    label_name: str
    selected_hyperparameter: float
    weights: dict[str, float]
    raw_coefficients: dict[str, float]
    clipped_features: list[str]
    cv_scores: dict[str, float]
    cv_metric: str
    train_size: int
    positive_count: int
    negative_count: int
    skipped_bootstrap_samples: int = 0
    weight_ci: dict[str, dict[str, float]] | None = None
    seed: int
    feature_columns: list[str]
    created_at: datetime
    notes: str = ""

    @field_validator("created_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None or v.utcoffset().total_seconds() != 0:
            raise ValueError("created_at must be timezone-aware UTC")
        return v


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _filtered_times(
    feature_frame: pd.DataFrame,
    label_series: pd.Series | list,
    decision_times: list | pd.Series | None,
    split_series: pd.Series | list | None,
) -> list:
    """Decision times for the selected training rows, aligned to X order."""
    mask = selection_mask(feature_frame, label_series, split_series, ("train",))
    n = len(feature_frame)
    if decision_times is None:
        times = list(range(n))
    else:
        times = list(decision_times)
        if len(times) != n:
            raise ValueError("decision_times length must match feature_frame")
    return [times[i] for i in range(n) if mask[i]]


def _cv_select(
    X: pd.DataFrame,
    y: pd.Series,
    times: list,
    grid: tuple[float, ...],
    n_splits: int,
    fit_one,
    score_one,
) -> tuple[float, dict[str, float]]:
    """Select a hyperparameter by mean temporal-CV score; returns (best, scores)."""
    folds = make_time_block_folds(times, n_splits=n_splits)
    cv_scores: dict[str, float] = {}
    for hp in grid:
        fold_scores: list[float] = []
        for tr, va in folds:
            ytr = y.iloc[tr]
            yva = y.iloc[va]
            if len(np.unique(yva.to_numpy())) < 2 or len(np.unique(ytr.to_numpy())) < 2:
                _warnings.warn(
                    f"skipping CV fold with single-class data at hp={hp}",
                    stacklevel=2,
                )
                continue
            model = fit_one(hp, X.iloc[tr], ytr)
            scores = score_one(model, X.iloc[va])
            fold_scores.append(float(average_precision_score(yva.to_numpy(), scores)))
        cv_scores[str(hp)] = float(np.mean(fold_scores)) if fold_scores else float("nan")

    valid = {k: v for k, v in cv_scores.items() if not np.isnan(v)}
    if valid:
        best_key = max(valid, key=lambda k: valid[k])
        best = float(best_key)
    else:
        # No fold yielded a valid score; fall back to the middle of the grid.
        best = float(grid[len(grid) // 2])
        _warnings.warn(
            "no valid CV folds; falling back to mid-grid hyperparameter", stacklevel=2
        )
    return best, cv_scores


def fit_weights_logit(
    feature_frame: pd.DataFrame,
    label_series: pd.Series | list,
    decision_times: list | pd.Series | None = None,
    split_series: pd.Series | list | None = None,
    C_grid: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0),
    n_splits: int = 5,
    seed: int = 0,
    label_name: str = "A",
    compute_ci: bool = False,
    bootstrap_B: int = 200,
) -> CalibrationResult:
    """Calibrate weights via L2-regularized logistic regression on the train split."""
    X, y = prepare_training_frame(feature_frame, label_series, split_series, ("train",))
    times = _filtered_times(feature_frame, label_series, decision_times, split_series)

    def fit_one(C: float, Xt: pd.DataFrame, yt: pd.Series) -> LogisticRegression:
        # L2 is the solver default; the explicit penalty= argument was
        # deprecated in scikit-learn 1.8, so it is omitted here.
        return LogisticRegression(
            C=C,
            solver="liblinear",
            class_weight="balanced",
            max_iter=1000,
            random_state=seed,
        ).fit(Xt[FEATURE_COLUMNS], yt)

    def score_one(model: LogisticRegression, Xv: pd.DataFrame) -> np.ndarray:
        return model.predict_proba(Xv[FEATURE_COLUMNS])[:, 1]

    best_C, cv_scores = _cv_select(X, y, times, C_grid, n_splits, fit_one, score_one)

    final = fit_one(best_C, X, y)
    raw = {f: float(final.coef_[0][i]) for i, f in enumerate(FEATURE_COLUMNS)}
    weights, clipped = coefficients_to_weights(raw, clip_negative=True, normalize=True)

    weight_ci = None
    skipped = 0
    if compute_ci:
        def _fit_fn(Xb: pd.DataFrame, yb: pd.Series) -> dict[str, float]:
            m = fit_one(best_C, Xb, yb)
            r = {f: float(m.coef_[0][i]) for i, f in enumerate(FEATURE_COLUMNS)}
            w, _ = coefficients_to_weights(r)
            return w

        weight_ci, skipped = bootstrap_weight_ci(_fit_fn, X, y, B=bootstrap_B, seed=seed)

    return CalibrationResult(
        model_type="logit",
        label_name=label_name,
        selected_hyperparameter=best_C,
        weights=weights,
        raw_coefficients=raw,
        clipped_features=clipped,
        cv_scores=cv_scores,
        cv_metric=CV_METRIC,
        train_size=len(X),
        positive_count=int((y == 1).sum()),
        negative_count=int((y == 0).sum()),
        skipped_bootstrap_samples=int(skipped),
        weight_ci=weight_ci,
        seed=seed,
        feature_columns=list(FEATURE_COLUMNS),
        created_at=_utc_now(),
        notes=(
            "L2 logistic regression, class_weight=balanced, liblinear. "
            "Negative coefficients clipped to zero; R weight reflects label "
            "association, not operational cost."
        ),
    )


def fit_weights_linear(
    feature_frame: pd.DataFrame,
    label_series: pd.Series | list,
    decision_times: list | pd.Series | None = None,
    split_series: pd.Series | list | None = None,
    alpha_grid: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0),
    n_splits: int = 5,
    seed: int = 0,
    label_name: str = "A",
    compute_ci: bool = False,
    bootstrap_B: int = 200,
) -> CalibrationResult:
    """Calibrate weights via L2-regularized ridge regression on the train split."""
    X, y = prepare_training_frame(feature_frame, label_series, split_series, ("train",))
    times = _filtered_times(feature_frame, label_series, decision_times, split_series)

    def fit_one(alpha: float, Xt: pd.DataFrame, yt: pd.Series) -> Ridge:
        return Ridge(alpha=alpha, random_state=seed).fit(
            Xt[FEATURE_COLUMNS], yt.astype(float)
        )

    def score_one(model: Ridge, Xv: pd.DataFrame) -> np.ndarray:
        return model.predict(Xv[FEATURE_COLUMNS])

    best_alpha, cv_scores = _cv_select(
        X, y, times, alpha_grid, n_splits, fit_one, score_one
    )

    final = fit_one(best_alpha, X, y)
    raw = {f: float(final.coef_[i]) for i, f in enumerate(FEATURE_COLUMNS)}
    weights, clipped = coefficients_to_weights(raw, clip_negative=True, normalize=True)

    weight_ci = None
    skipped = 0
    if compute_ci:
        def _fit_fn(Xb: pd.DataFrame, yb: pd.Series) -> dict[str, float]:
            m = fit_one(best_alpha, Xb, yb)
            r = {f: float(m.coef_[i]) for i, f in enumerate(FEATURE_COLUMNS)}
            w, _ = coefficients_to_weights(r)
            return w

        weight_ci, skipped = bootstrap_weight_ci(_fit_fn, X, y, B=bootstrap_B, seed=seed)

    return CalibrationResult(
        model_type="ridge",
        label_name=label_name,
        selected_hyperparameter=best_alpha,
        weights=weights,
        raw_coefficients=raw,
        clipped_features=clipped,
        cv_scores=cv_scores,
        cv_metric=CV_METRIC,
        train_size=len(X),
        positive_count=int((y == 1).sum()),
        negative_count=int((y == 0).sum()),
        skipped_bootstrap_samples=int(skipped),
        weight_ci=weight_ci,
        seed=seed,
        feature_columns=list(FEATURE_COLUMNS),
        created_at=_utc_now(),
        notes=(
            "L2 ridge regression on 0/1 target. Negative coefficients clipped "
            "to zero; R weight reflects label association, not operational cost."
        ),
    )


def save_calibration_result(result: CalibrationResult, path: str | Path) -> None:
    """Atomically write the calibration result as stable, sorted JSON."""
    atomic_write_json(path, result.model_dump(mode="json"))


def load_calibration_result(path: str | Path) -> CalibrationResult:
    payload: dict[str, Any] = read_json(path)
    return CalibrationResult(**payload)


def register_calibrated_weights(result: CalibrationResult, name: str) -> None:
    """Register the calibrated weight vector under `name` in the runtime registry."""
    _register_calibrated_weights(name, result.weights, overwrite=True)
