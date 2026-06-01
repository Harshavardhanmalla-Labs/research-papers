"""Modeling layer (Phase 4): pairs, labels, temporal splits, frames.

Phase 4 composes Phase 2 feed outputs and Phase 3 synthetic hosts into
vulnerability-host pairs, attaches leakage-controlled labels, and
defines the temporal train/gap/test split. No scoring, scheduling, or
metrics live here.
"""

from paper1.model.calibration import (
    bootstrap_weight_ci,
    class_weight_from_labels,
    coefficients_to_weights,
    make_time_block_folds,
    prepare_training_frame,
)
from paper1.model.features import build_feature_frame
from paper1.model.frames import (
    attach_labels,
    attach_split,
    hosts_to_frame,
    pairs_to_frame,
    validate_pair_frame,
    vulnerabilities_to_frame,
)
from paper1.model.gbt_comparator import (
    GBTResult,
    fit_gbt,
    load_gbt_config,
    load_gbt_result,
    predict_gbt,
    rank_pairs_gbt,
    save_gbt_result,
)
from paper1.model.labels import (
    censor_mask,
    ensure_no_label_future_leakage,
    label_a,
    label_b,
    label_dates_a,
    label_dates_b,
    validate_event_dates,
)
from paper1.model.linear_model import (
    CalibrationResult,
    fit_weights_linear,
    fit_weights_logit,
    load_calibration_result,
    register_calibrated_weights,
    save_calibration_result,
)
from paper1.model.pairs import (
    build_pairs,
    build_pairs_frame,
    is_patch_already_installed,
    match_vulnerability_to_host,
    product_keys_from_host,
    product_keys_from_vulnerability,
)
from paper1.model.scoring import (
    compute_feature_contributions,
    score_pairs_linear,
    sort_ranking,
    validate_feature_frame,
)
from paper1.model.splits import (
    assign_split,
    filter_pairs_by_split,
    make_temporal_split,
    validate_split_gap,
)
from paper1.model.strategies import STRATEGY_NAMES, rank_pairs
from paper1.model.weights import (
    FEATURE_COLUMNS,
    ablate_weight,
    get_weights,
    normalize_weights,
    register_weights,
    validate_weights,
)

__all__ = [
    "FEATURE_COLUMNS",
    "STRATEGY_NAMES",
    "CalibrationResult",
    "GBTResult",
    "ablate_weight",
    "assign_split",
    "attach_labels",
    "attach_split",
    "bootstrap_weight_ci",
    "build_feature_frame",
    "build_pairs",
    "build_pairs_frame",
    "censor_mask",
    "class_weight_from_labels",
    "coefficients_to_weights",
    "compute_feature_contributions",
    "ensure_no_label_future_leakage",
    "filter_pairs_by_split",
    "fit_gbt",
    "fit_weights_linear",
    "fit_weights_logit",
    "get_weights",
    "hosts_to_frame",
    "is_patch_already_installed",
    "label_a",
    "label_b",
    "label_dates_a",
    "label_dates_b",
    "load_calibration_result",
    "load_gbt_config",
    "load_gbt_result",
    "make_temporal_split",
    "make_time_block_folds",
    "match_vulnerability_to_host",
    "normalize_weights",
    "pairs_to_frame",
    "predict_gbt",
    "prepare_training_frame",
    "product_keys_from_host",
    "product_keys_from_vulnerability",
    "rank_pairs",
    "rank_pairs_gbt",
    "register_calibrated_weights",
    "register_weights",
    "save_calibration_result",
    "save_gbt_result",
    "score_pairs_linear",
    "sort_ranking",
    "validate_event_dates",
    "validate_feature_frame",
    "validate_pair_frame",
    "validate_split_gap",
    "validate_weights",
    "vulnerabilities_to_frame",
]
