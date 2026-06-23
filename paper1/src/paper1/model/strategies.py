"""Prioritization strategies.

Every strategy ranks the full set of pairs exactly once, deterministically,
breaking ties by ``pair_id`` ascending. The ``oracle`` strategy is
evaluation-only (it reads the future label) and is NOT deployable. The
``gbt_comparator`` requires a pre-fitted LightGBM model (passed via
``gbt_model``); it is a reference comparator, not the deployed model.
"""

from __future__ import annotations

import warnings as _warnings
from typing import Any

import pandas as pd

from paper1.model.features import FEATURE_COLUMNS
from paper1.model.scoring import score_pairs_linear
from paper1.model.weights import ablate_weight, get_weights
from paper1.utils.seeds import make_rng

__all__ = [
    "FEATURE_STRATEGIES",
    "STRATEGY_NAMES",
    "rank_pairs",
]

OUTPUT_COLUMNS = ["pair_id", "cve_id", "host_id", "priority_score", "rank", "strategy_name"]

STRATEGY_NAMES = [
    "random",
    "cvss_only",
    "epss_only",
    "kev_first",
    "cvss_x_epss",
    "cvss_plus_epss_plus_kev",
    "cve_max",
    "cve_mean",
    "cve_sum",
    "proposed_full",
    "proposed_no_criticality",
    "proposed_no_exposure",
    "oracle",
    "gbt_comparator",
]

# Strategies that require the feature frame.
FEATURE_STRATEGIES = {
    "cvss_only",
    "epss_only",
    "kev_first",
    "cvss_x_epss",
    "cvss_plus_epss_plus_kev",
    "cve_max",
    "cve_mean",
    "cve_sum",
    "proposed_full",
    "proposed_no_criticality",
    "proposed_no_exposure",
}


def _assemble(pair_frame: pd.DataFrame, feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Pair identity columns joined with the seven features, in pair order."""
    work = pair_frame[["pair_id", "cve_id", "host_id"]].reset_index(drop=True).copy()
    feat = feature_frame.set_index("pair_id")
    for col in FEATURE_COLUMNS:
        if col not in feat.columns:
            raise ValueError(f"feature_frame missing feature column {col!r}")
        work[col] = work["pair_id"].map(feat[col])
    if work[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("some pairs have no matching feature row")
    return work


def _finalize(work: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
    out = work.sort_values(
        ["priority_score", "pair_id"], ascending=[False, True]
    ).reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    out["strategy_name"] = strategy_name
    return out[OUTPUT_COLUMNS]


def _proposed_scores(
    pair_frame: pd.DataFrame, feature_frame: pd.DataFrame, weights: dict[str, float]
) -> pd.Series:
    scored = score_pairs_linear(feature_frame, weights)
    score_by_pair = scored.set_index("pair_id")["priority_score"]
    return pair_frame["pair_id"].map(score_by_pair)


def rank_pairs(
    strategy_name: str,
    pair_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
    label_series: pd.Series | None = None,
    seed: int | None = None,
    weights_name: str = "w_logit_placeholder",
    gbt_model: Any | None = None,
) -> pd.DataFrame:
    """Rank all pairs under the named strategy. Returns OUTPUT_COLUMNS frame."""
    if strategy_name not in STRATEGY_NAMES:
        raise ValueError(
            f"unknown strategy {strategy_name!r}; known: {STRATEGY_NAMES}"
        )

    if strategy_name == "gbt_comparator":
        if gbt_model is None:
            raise ValueError("gbt_comparator requires a fitted gbt_model")
        # Lazy import to keep the strategies module import lightweight.
        from paper1.model.gbt_comparator import predict_gbt

        preds = predict_gbt(gbt_model, feature_frame)
        score_by_pair = dict(zip(feature_frame["pair_id"], preds, strict=True))
        work = pair_frame[["pair_id", "cve_id", "host_id"]].reset_index(drop=True).copy()
        work["priority_score"] = work["pair_id"].map(score_by_pair)
        if work["priority_score"].isna().any():
            raise ValueError("some pairs have no GBT prediction (missing feature row)")
        return _finalize(work, strategy_name)

    base = pair_frame[["pair_id", "cve_id", "host_id"]].reset_index(drop=True).copy()

    if strategy_name == "random":
        ordered = base.sort_values("pair_id").reset_index(drop=True)
        rng = make_rng(seed if seed is not None else 0)
        ordered["priority_score"] = rng.random(len(ordered))
        work = base.merge(ordered[["pair_id", "priority_score"]], on="pair_id", how="left")
        return _finalize(work, strategy_name)

    if strategy_name == "oracle":
        if label_series is None:
            raise ValueError("oracle strategy requires label_series")
        if len(label_series) != len(base):
            raise ValueError("label_series length must match pair_frame length")
        vals = []
        n_na = 0
        for v in list(label_series):
            if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
                vals.append(0.0)
                n_na += 1
            else:
                vals.append(1.0 if bool(v) else 0.0)
        if n_na:
            _warnings.warn(
                f"oracle: {n_na} censored/NA labels treated as 0 (non-positive)",
                stacklevel=2,
            )
        work = base.copy()
        work["priority_score"] = vals
        return _finalize(work, strategy_name)

    # Feature-based strategies.
    work = _assemble(pair_frame, feature_frame)

    if strategy_name == "cvss_only":
        work["priority_score"] = work["S"]
    elif strategy_name == "epss_only":
        work["priority_score"] = work["E"]
    elif strategy_name == "kev_first":
        work["priority_score"] = work["K"] * 2.0 + work["E"]
    elif strategy_name == "cvss_x_epss":
        work["priority_score"] = work["S"] * work["E"]
    elif strategy_name == "cvss_plus_epss_plus_kev":
        work["priority_score"] = work["S"] + work["E"] + 0.5 * work["K"]
    elif strategy_name == "proposed_full":
        work["priority_score"] = _proposed_scores(
            work, feature_frame, get_weights(weights_name)
        )
    elif strategy_name == "proposed_no_criticality":
        w = ablate_weight(get_weights(weights_name), "C")
        work["priority_score"] = _proposed_scores(work, feature_frame, w)
    elif strategy_name == "proposed_no_exposure":
        w = ablate_weight(get_weights(weights_name), "X")
        work["priority_score"] = _proposed_scores(work, feature_frame, w)
    elif strategy_name in ("cve_max", "cve_mean", "cve_sum"):
        pair_scores = _proposed_scores(work, feature_frame, get_weights(weights_name))
        tmp = work[["pair_id", "cve_id"]].copy()
        tmp["pair_score"] = pair_scores.to_numpy()
        agg = {"cve_max": "max", "cve_mean": "mean", "cve_sum": "sum"}[strategy_name]
        cve_score = tmp.groupby("cve_id")["pair_score"].transform(agg)
        work["priority_score"] = cve_score.to_numpy()
    else:  # pragma: no cover - guarded above
        raise ValueError(f"unhandled strategy {strategy_name!r}")

    return _finalize(work, strategy_name)
