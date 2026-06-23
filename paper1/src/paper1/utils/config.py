"""YAML config loading and shape validation.

Configs are the contract between paper text and code. Loading verifies
that the file exists and contains the required top-level keys for its
declared type; deeper schema validation is delegated to downstream code
in later phases.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from paper1.utils.io import compute_file_sha256

__all__ = [
    "REQUIRED_KEYS",
    "config_sha256",
    "load_config",
    "load_yaml",
    "validate_config_file",
]


# Required top-level keys per config file name. Files not listed here
# are loaded but not shape-validated.
REQUIRED_KEYS: dict[str, set[str]] = {
    "primary.yaml": {
        "config_name",
        "seed_master",
        "fleet_size",
        "capacity_ratio",
        "label",
        "approver_policy",
        "identity_config",
        "blackout_config",
        "epss_version_handling",
        "data_window_start",
        "data_window_end",
        "H_days",
        "train_split_months",
        "strategies",
        "seed_count",
        "maintenance_cadence_days",
        "remediation_failure_rate",
        "rollback_probability_given_failure",
        "output_dir",
    },
    "smoke.yaml": {
        "config_name",
        "seed_master",
        "fleet_size",
        "capacity_ratio",
        "label",
        "approver_policy",
        "identity_config",
        "blackout_config",
        "data_window_start",
        "data_window_end",
        "H_days",
        "strategies",
        "seed_count",
        "output_dir",
    },
    "gbt.yaml": {
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
        "random_state_from_master",
    },
    "labels.yaml": {"labels"},
    "strategies.yaml": {"strategies"},
    "sensitivity.yaml": {"dimensions", "seeds_per_condition"},
    "approver_policy_a.yaml": {"policy_name", "rho_senior"},
    "approver_policy_b.yaml": {
        "policy_name",
        "rho_senior",
        "low_complexity_delay_business_days",
        "high_complexity_cab_cadence_business_days",
    },
    "identity_ad_entra.yaml": {"identity_mapping_config", "tiers"},
    "identity_federated.yaml": {"identity_mapping_config"},
    "blackout_primary.yaml": {"config_name", "blackouts"},
    "blackout_none.yaml": {"config_name", "blackouts"},
    "blackout_light.yaml": {"config_name", "blackouts"},
    "blackout_strict_monthly.yaml": {"config_name", "blackouts"},
}


def load_yaml(path: str | Path) -> Any:
    """Load a YAML file with safe_load."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_config_file(path: str | Path) -> dict[str, Any]:
    """Load and shape-validate a config file by its filename.

    Returns the loaded mapping on success. Raises ValueError if required
    top-level keys are missing.
    """
    p = Path(path)
    payload = load_yaml(p)
    if not isinstance(payload, dict):
        raise ValueError(f"Config {p.name} must be a mapping at top level")
    required = REQUIRED_KEYS.get(p.name)
    if required is None:
        return payload
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(
            f"Config {p.name} is missing required keys: {sorted(missing)}"
        )
    return payload


def load_config(path: str | Path, model_type: type | None = None) -> Any:
    """Load and validate; optionally instantiate a Pydantic model."""
    payload = validate_config_file(path)
    if model_type is None:
        return payload
    return model_type(**payload)


def config_sha256(path: str | Path) -> str:
    """SHA-256 of the on-disk config bytes (canonical hashing target)."""
    return compute_file_sha256(path)


def _normalized_config_sha256(payload: Any) -> str:
    """SHA-256 of a canonicalized JSON serialization (file-independent)."""
    import json

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
