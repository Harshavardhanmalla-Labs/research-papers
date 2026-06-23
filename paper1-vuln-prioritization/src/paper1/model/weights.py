"""Weight-vector registry for the linear prioritization model.

All weights are non-negative magnitudes. The remediation-complexity
weight ``R`` is stored positive but is *subtracted* during scoring
(see ``paper1.model.scoring``). ``get_weights`` always returns a
normalized copy whose seven weights sum to 1, so the registry contents
are never mutated by callers.
"""

from __future__ import annotations

import copy

__all__ = [
    "FEATURE_COLUMNS",
    "ablate_weight",
    "get_weights",
    "list_weights",
    "normalize_weights",
    "register_calibrated_weights",
    "register_weights",
    "validate_weights",
]

FEATURE_COLUMNS = ["E", "K", "S", "C", "X", "U", "R"]


# Built-in weight vectors. w_logit_placeholder / w_lin_placeholder are
# explicit placeholders that mirror w_hand until Phase 6 calibration
# replaces them with regression-fit values.
_BUILTIN: dict[str, dict[str, float]] = {
    "w_uniform": dict.fromkeys(FEATURE_COLUMNS, 1.0),
    "w_hand": {
        "E": 0.20,
        "K": 0.20,
        "S": 0.10,
        "C": 0.20,
        "X": 0.15,
        "U": 0.10,
        "R": 0.05,
    },
    "w_logit_placeholder": {
        "E": 0.20,
        "K": 0.20,
        "S": 0.10,
        "C": 0.20,
        "X": 0.15,
        "U": 0.10,
        "R": 0.05,
    },
    "w_lin_placeholder": {
        "E": 0.20,
        "K": 0.20,
        "S": 0.10,
        "C": 0.20,
        "X": 0.15,
        "U": 0.10,
        "R": 0.05,
    },
}

# User-registered vectors live here; built-ins are never mutated.
_registry: dict[str, dict[str, float]] = {}


def validate_weights(weights: dict[str, float]) -> None:
    """Raise if any feature is missing, extra, negative, or sum is non-positive."""
    keys = set(weights.keys())
    expected = set(FEATURE_COLUMNS)
    if keys != expected:
        missing = expected - keys
        extra = keys - expected
        raise ValueError(
            f"weights must have exactly {FEATURE_COLUMNS}; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    for k, v in weights.items():
        if not isinstance(v, (int, float)):
            raise ValueError(f"weight {k!r} must be numeric; got {type(v).__name__}")
        if v < 0:
            raise ValueError(f"weight {k!r} must be non-negative; got {v}")
    if sum(weights.values()) <= 0:
        raise ValueError("weights must sum to a positive value")


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Validate and return a copy whose weights sum to 1."""
    validate_weights(weights)
    total = float(sum(weights.values()))
    return {k: float(weights[k]) / total for k in FEATURE_COLUMNS}


def get_weights(name: str) -> dict[str, float]:
    """Return a normalized copy of a registered or built-in weight vector."""
    if name in _registry:
        raw = _registry[name]
    elif name in _BUILTIN:
        raw = _BUILTIN[name]
    else:
        raise ValueError(
            f"unknown weights {name!r}; available: {sorted(list_weights())}"
        )
    return normalize_weights(copy.deepcopy(raw))


def register_weights(
    name: str, weights: dict[str, float], overwrite: bool = False
) -> None:
    """Register a user weight vector (validated, stored un-normalized copy)."""
    if name in _BUILTIN:
        raise ValueError(f"cannot register over built-in weight name {name!r}")
    if name in _registry and not overwrite:
        raise ValueError(f"weights {name!r} already registered; pass overwrite=True")
    validate_weights(weights)
    _registry[name] = copy.deepcopy(weights)


def register_calibrated_weights(
    name: str, weights: dict[str, float], overwrite: bool = False
) -> None:
    """Register calibrated weights (thin wrapper over register_weights).

    Provided as a distinct, intention-revealing entry point for the
    calibration phase. Built-in placeholder names cannot be overwritten.
    """
    register_weights(name, weights, overwrite=overwrite)


def list_weights() -> list[str]:
    return sorted(set(_BUILTIN) | set(_registry))


def ablate_weight(weights: dict[str, float], feature_name: str) -> dict[str, float]:
    """Return a normalized copy with `feature_name` zeroed.

    The remaining six weights (including R) are renormalized to sum to 1.
    """
    if feature_name not in FEATURE_COLUMNS:
        raise ValueError(f"unknown feature {feature_name!r}")
    validate_weights(weights)
    out = copy.deepcopy(weights)
    out[feature_name] = 0.0
    total = float(sum(out.values()))
    if total <= 0:
        raise ValueError("cannot ablate the only non-zero weight")
    return {k: float(out[k]) / total for k in FEATURE_COLUMNS}
