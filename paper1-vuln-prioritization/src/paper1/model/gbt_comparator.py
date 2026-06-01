"""LightGBM reference comparator.

This is a *reference* comparator used to quantify the cost of the
auditable linear scoring model. It is **not** the deployed
recommendation: a gradient-boosted-tree model does not produce the
decomposable per-feature contributions that the linear model emits for
NIST 800-53 AU-3 / CJIS audit records. SHAP-based explanation is
explicitly out of scope for this phase.

Training obeys the same discipline as the linear calibrator: only the
``train`` split, only non-censored labels, and a temporal (no-shuffle)
validation split for early stopping. The seven features E, K, S, C, X,
U, R are used as-is; no engineered features are added.
"""

from __future__ import annotations

import warnings as _warnings
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

import lightgbm as lgb
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, field_validator

from paper1.model.calibration import prepare_training_frame, selection_mask
from paper1.model.weights import FEATURE_COLUMNS
from paper1.utils.io import atomic_write_json, read_json
from paper1.utils.logging import get_logger

__all__ = [
    "VALIDATION_FRACTION",
    "GBTResult",
    "fit_gbt",
    "load_gbt_config",
    "load_gbt_result",
    "predict_gbt",
    "rank_pairs_gbt",
    "save_gbt_result",
]

_log = get_logger("paper1.model.gbt")

VALIDATION_FRACTION = 0.2

_REQUIRED_CONFIG_KEYS = {
    "implementation",
    "objective",
    "num_boost_round",
    "early_stopping_rounds",
    "max_depth",
    "num_leaves",
    "learning_rate",
    "reg_lambda",
    "min_data_in_leaf",
    "is_unbalance",
    "deterministic",
    "feature_set",
}

_GBT_OUTPUT_COLUMNS = [
    "pair_id",
    "cve_id",
    "host_id",
    "priority_score",
    "rank",
    "strategy_name",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _to_ordinal(value: Any) -> int:
    if isinstance(value, datetime):
        return value.toordinal()
    if isinstance(value, date):
        return value.toordinal()
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, str):
        return date.fromisoformat(value[:10]).toordinal()
    raise TypeError(f"cannot order decision time {value!r}")


class GBTResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    model_type: Literal["lightgbm"]
    label_name: str
    config: dict[str, Any]
    selected_iteration: int
    train_size: int
    positive_count: int
    negative_count: int
    feature_columns: list[str]
    validation_scores: dict[str, float]
    seed: int
    created_at: datetime
    notes: str = ""

    @field_validator("created_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None or v.utcoffset().total_seconds() != 0:
            raise ValueError("created_at must be timezone-aware UTC")
        return v


def load_gbt_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate the GBT config (defaults to configs/gbt.yaml)."""
    import yaml

    p = Path(path) if path is not None else _repo_root() / "configs" / "gbt.yaml"
    if not p.exists():
        raise FileNotFoundError(f"GBT config not found: {p}")
    with open(p, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict):
        raise ValueError("GBT config must be a mapping")
    missing = _REQUIRED_CONFIG_KEYS - set(config.keys())
    if missing:
        raise ValueError(f"GBT config missing keys: {sorted(missing)}")
    if config["implementation"] != "lightgbm":
        raise ValueError(
            f"GBT implementation must be 'lightgbm'; got {config['implementation']!r}"
        )
    if list(config["feature_set"]) != list(FEATURE_COLUMNS):
        raise ValueError(
            f"GBT feature_set {config['feature_set']} must equal FEATURE_COLUMNS "
            f"{FEATURE_COLUMNS}"
        )
    return config


def _filtered_times(
    feature_frame: pd.DataFrame,
    label_series: pd.Series | list,
    decision_times: list | pd.Series | None,
    split_series: pd.Series | list | None,
) -> list:
    mask = selection_mask(feature_frame, label_series, split_series, ("train",))
    n = len(feature_frame)
    if decision_times is None:
        times = list(range(n))
    else:
        times = list(decision_times)
        if len(times) != n:
            raise ValueError("decision_times length must match feature_frame")
    return [times[i] for i in range(n) if mask[i]]


def _model_params(config: dict[str, Any], seed: int) -> dict[str, Any]:
    return {
        "objective": config["objective"],
        "n_estimators": int(config["num_boost_round"]),
        "max_depth": int(config["max_depth"]),
        "num_leaves": int(config["num_leaves"]),
        "learning_rate": float(config["learning_rate"]),
        "reg_lambda": float(config["reg_lambda"]),
        "min_child_samples": int(config["min_data_in_leaf"]),
        "is_unbalance": bool(config["is_unbalance"]),
        "deterministic": bool(config["deterministic"]),
        "force_row_wise": True,
        "n_jobs": 1,
        "random_state": int(seed),
        "verbose": -1,
    }


def fit_gbt(
    feature_frame: pd.DataFrame,
    label_series: pd.Series | list,
    decision_times: list | pd.Series | None = None,
    split_series: pd.Series | list | None = None,
    config: dict[str, Any] | None = None,
    seed: int = 0,
    label_name: str = "A",
) -> tuple[lgb.LGBMClassifier, GBTResult]:
    """Fit the LightGBM comparator on the train split with temporal early stopping."""
    cfg = config if config is not None else load_gbt_config()
    X, y = prepare_training_frame(feature_frame, label_series, split_series, ("train",))
    times = _filtered_times(feature_frame, label_series, decision_times, split_series)

    n = len(X)
    ordinals = np.array([_to_ordinal(t) for t in times])
    order = np.argsort(ordinals, kind="stable")
    n_val = max(1, round(VALIDATION_FRACTION * n))
    val_pos = order[-n_val:]
    tr_pos = order[:-n_val]

    model = lgb.LGBMClassifier(**_model_params(cfg, seed))
    notes = (
        "LightGBM reference comparator (NOT the deployed model). "
        "Same seven features and temporal no-leakage discipline as the linear model."
    )
    validation_scores: dict[str, float] = {}

    use_early = (
        len(tr_pos) > 0
        and len(np.unique(y.iloc[tr_pos].to_numpy())) >= 2
        and len(np.unique(y.iloc[val_pos].to_numpy())) >= 2
    )

    if use_early:
        model.fit(
            X.iloc[tr_pos][FEATURE_COLUMNS],
            y.iloc[tr_pos],
            eval_set=[(X.iloc[val_pos][FEATURE_COLUMNS], y.iloc[val_pos])],
            eval_metric="auc",
            callbacks=[
                lgb.early_stopping(int(cfg["early_stopping_rounds"]), verbose=False),
                lgb.log_evaluation(0),
            ],
        )
        best_iter = model.best_iteration_
        selected_iteration = int(best_iter if best_iter and best_iter > 0 else model.n_estimators_)
        try:
            valid_scores = model.best_score_.get("valid_0", {})
            if "auc" in valid_scores:
                validation_scores = {"auc_best": float(valid_scores["auc"])}
        except (AttributeError, KeyError, TypeError):
            validation_scores = {}
    else:
        _warnings.warn(
            "GBT validation fold is single-class; fitting without early stopping",
            stacklevel=2,
        )
        notes += " Validation fold single-class; fit without early stopping."
        model.fit(X[FEATURE_COLUMNS], y)
        selected_iteration = int(getattr(model, "n_estimators_", int(cfg["num_boost_round"])))

    result = GBTResult(
        model_type="lightgbm",
        label_name=label_name,
        config=dict(cfg),
        selected_iteration=selected_iteration,
        train_size=n,
        positive_count=int((y == 1).sum()),
        negative_count=int((y == 0).sum()),
        feature_columns=list(FEATURE_COLUMNS),
        validation_scores=validation_scores,
        seed=int(seed),
        created_at=datetime.now(tz=UTC),
        notes=notes,
    )
    return model, result


def predict_gbt(model: lgb.LGBMClassifier, feature_frame: pd.DataFrame) -> pd.Series:
    """Probability of the positive class per row; index-aligned, in [0, 1]."""
    missing = set(FEATURE_COLUMNS) - set(feature_frame.columns)
    if missing:
        raise ValueError(f"feature_frame missing feature columns: {sorted(missing)}")
    proba = model.predict_proba(feature_frame[FEATURE_COLUMNS])[:, 1]
    series = pd.Series(proba, index=feature_frame.index, dtype=float).clip(0.0, 1.0)
    if series.isna().any():
        raise ValueError("GBT predictions contain NaN")
    return series


def rank_pairs_gbt(
    pair_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
    model: lgb.LGBMClassifier,
) -> pd.DataFrame:
    """Rank pairs by GBT positive-class probability (deterministic tie-break)."""
    preds = predict_gbt(model, feature_frame)
    score_by_pair = dict(zip(feature_frame["pair_id"], preds, strict=True))
    work = pair_frame[["pair_id", "cve_id", "host_id"]].reset_index(drop=True).copy()
    work["priority_score"] = work["pair_id"].map(score_by_pair)
    if work["priority_score"].isna().any():
        raise ValueError("some pairs have no GBT prediction (missing feature row)")
    out = work.sort_values(
        ["priority_score", "pair_id"], ascending=[False, True]
    ).reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    out["strategy_name"] = "gbt_comparator"
    return out[_GBT_OUTPUT_COLUMNS]


def save_gbt_result(result: GBTResult, path: str | Path) -> None:
    atomic_write_json(path, result.model_dump(mode="json"))


def load_gbt_result(path: str | Path) -> GBTResult:
    payload: dict[str, Any] = read_json(path)
    return GBTResult(**payload)
