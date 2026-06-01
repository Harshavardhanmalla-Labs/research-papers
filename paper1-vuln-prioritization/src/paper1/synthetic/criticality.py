"""Asset criticality with the Identity Privilege Exposure Score (IPES).

Aggregate formula (when all five sub-scores are present):

    C = 0.30·role + 0.25·identity + 0.20·network + 0.20·data + 0.05·cmdb

When CMDB is missing, the cmdb term is dropped and the remaining
weights are renormalized so they sum to 1. `subscore_cmdb` is then
left as None and 'cmdb' is added to ``inputs_missing``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np

from paper1.audit.schema import AssetCriticalityProfile, Host

__all__ = [
    "BASE_WEIGHTS",
    "DERIVATION_METHOD",
    "compute_criticality",
    "renormalize_weights",
    "sample_cmdb_subscore",
    "sample_data_subscore",
    "sample_identity_privilege_exposure",
    "sample_network_subscore",
    "sample_role_subscore",
]


DERIVATION_METHOD = "acr_v0.3"

# Base aggregation weights. Order matters only for the renormalization
# helper that drops cmdb when missing.
BASE_WEIGHTS: dict[str, float] = {
    "role": 0.30,
    "identity": 0.25,
    "network": 0.20,
    "data": 0.20,
    "cmdb": 0.05,
}


def _uniform_in_range(rng: np.random.Generator, lo: float, hi: float) -> float:
    if lo > hi:
        raise ValueError(f"range lo > hi: {lo} > {hi}")
    return float(rng.uniform(lo, hi))


def sample_role_subscore(
    host_role: str,
    defaults: dict[str, Any],
    rng: np.random.Generator,
) -> float:
    lo, hi = defaults["host_types"][host_role]["role_subscore_range"]
    return _uniform_in_range(rng, float(lo), float(hi))


def sample_identity_privilege_exposure(
    host_role: str,
    identity_config: str,
    defaults: dict[str, Any],
    rng: np.random.Generator,
) -> float:
    role_cfg = defaults["host_types"][host_role]
    if identity_config in ("ad_entra_default", "ad_entra", "ad"):
        key = "ipes_ad_entra"
    elif identity_config in ("federated", "federated_default"):
        key = "ipes_federated"
    else:
        raise ValueError(f"Unknown identity_config: {identity_config!r}")
    lo, hi = role_cfg[key]
    return _uniform_in_range(rng, float(lo), float(hi))


def sample_network_subscore(
    zone: str,
    host_role: str,
    defaults: dict[str, Any],
    rng: np.random.Generator,
) -> float:
    role_cfg = defaults["host_types"][host_role]
    lo, hi = role_cfg["network_subscore_range"]
    base = _uniform_in_range(rng, float(lo), float(hi))
    # Zone bias: public > dmz > internal > restricted > air_gapped.
    zone_bias = {
        "public": 0.10,
        "dmz": 0.05,
        "internal": 0.0,
        "restricted": -0.05,
        "air_gapped": -0.10,
    }.get(zone, 0.0)
    return float(max(0.0, min(1.0, base + zone_bias)))


def sample_data_subscore(
    data_sensitivity: str | None,
    host_role: str,
    defaults: dict[str, Any],
    rng: np.random.Generator,
) -> float:
    role_cfg = defaults["host_types"][host_role]
    lo, hi = role_cfg["data_subscore_range"]
    base = _uniform_in_range(rng, float(lo), float(hi))
    bonus = {
        "cji": 0.15,
        "phi": 0.10,
        "cui": 0.10,
        "pii": 0.05,
        "general": 0.0,
        "non_sensitive": -0.05,
    }.get(data_sensitivity or "general", 0.0)
    return float(max(0.0, min(1.0, base + bonus)))


def sample_cmdb_subscore(
    true_criticality: float,
    cmdb_present: bool,
    staleness_rate: float,
    rng: np.random.Generator,
) -> float | None:
    """Optionally perturb the true criticality to model CMDB-tag drift."""
    if not cmdb_present:
        return None
    if not (0.0 <= staleness_rate <= 1.0):
        raise ValueError(f"staleness_rate {staleness_rate} outside [0, 1]")
    if rng.random() < staleness_rate:
        # Stale: random value uncorrelated with true_criticality.
        return float(rng.uniform(0.0, 1.0))
    # Fresh: small Gaussian jitter around true_criticality.
    jitter = float(rng.normal(0.0, 0.05))
    return float(max(0.0, min(1.0, true_criticality + jitter)))


def renormalize_weights(
    present: list[str],
    base_weights: dict[str, float] = BASE_WEIGHTS,
) -> dict[str, float]:
    """Return weights for the present sub-scores, rescaled to sum to 1."""
    subset = {k: base_weights[k] for k in present if k in base_weights}
    total = sum(subset.values())
    if total <= 0.0:
        raise ValueError("No sub-scores present to weight")
    return {k: v / total for k, v in subset.items()}


def compute_criticality(
    host: Host,
    host_defaults: dict[str, Any],
    identity_config: str,
    cmdb_staleness_rate: float,
    rng: np.random.Generator,
    *,
    inputs_missing: list[str] | None = None,
    computed_at: datetime | None = None,
) -> AssetCriticalityProfile:
    """Compute the criticality profile for a host.

    `inputs_missing` may pre-declare other missing inputs (telemetry).
    If 'cmdb' is in inputs_missing, the CMDB sub-score is None.
    """
    missing = list(inputs_missing or [])
    role_score = sample_role_subscore(host.role, host_defaults, rng)
    identity_score = sample_identity_privilege_exposure(
        host.role, identity_config, host_defaults, rng
    )
    network_score = sample_network_subscore(host.network_zone, host.role, host_defaults, rng)
    data_score = sample_data_subscore(host.data_sensitivity_proxy, host.role, host_defaults, rng)

    # True criticality used to seed the CMDB sub-score drift.
    true_criticality = (
        BASE_WEIGHTS["role"] * role_score
        + BASE_WEIGHTS["identity"] * identity_score
        + BASE_WEIGHTS["network"] * network_score
        + BASE_WEIGHTS["data"] * data_score
    ) / (1.0 - BASE_WEIGHTS["cmdb"])
    true_criticality = max(0.0, min(1.0, true_criticality))

    cmdb_present = "cmdb" not in missing and host.cmdb_tags is not None
    cmdb_score = sample_cmdb_subscore(true_criticality, cmdb_present, cmdb_staleness_rate, rng)

    present = ["role", "identity", "network", "data"]
    if cmdb_score is not None:
        present.append("cmdb")
    elif "cmdb" not in missing:
        missing.append("cmdb")

    weights = renormalize_weights(present)
    score = (
        weights["role"] * role_score
        + weights["identity"] * identity_score
        + weights["network"] * network_score
        + weights["data"] * data_score
        + (weights["cmdb"] * cmdb_score if cmdb_score is not None else 0.0)
    )
    score = max(0.0, min(1.0, float(score)))

    if computed_at is None:
        # All datetimes in this layer come from a deterministic base
        # derived from t0; we don't use utc_now here because it is the
        # caller's responsibility to bind compute time to t0.
        raise ValueError("computed_at is required (must be derived from t0)")

    return AssetCriticalityProfile(
        host_id=host.host_id,
        criticality_score=score,
        subscore_role=float(role_score),
        subscore_identity=float(identity_score),
        subscore_network=float(network_score),
        subscore_data=float(data_score),
        subscore_cmdb=(float(cmdb_score) if cmdb_score is not None else None),
        derivation_method=DERIVATION_METHOD,
        identity_mapping_config=identity_config,
        inputs_missing=sorted(set(missing)),
        computed_at=computed_at,
    )
