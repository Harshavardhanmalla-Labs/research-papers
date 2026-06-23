"""Per-pair remediation complexity score.

    R = 0.25·reboot + 0.15·user_disruption + 0.20·service_dep
        + 0.25·regression + 0.10·(1 - channel) + 0.05·(1 - bundle)
        + host_modifier

then clamped to [0, 1].
"""

from __future__ import annotations

from typing import Any

import numpy as np

from paper1.audit.schema import (
    Host,
    RemediationComplexityProfile,
    Vulnerability,
)

__all__ = [
    "HOST_MODIFIERS",
    "WEIGHTS",
    "bundle_factor",
    "compute_complexity",
    "deployment_channel_factor",
    "host_modifier",
    "reboot_factor",
    "regression_factor",
    "service_dependency_factor",
    "user_disruption_factor",
]


WEIGHTS: dict[str, float] = {
    "reboot": 0.25,
    "user_disruption": 0.15,
    "service_dep": 0.20,
    "regression": 0.25,
    "channel": 0.10,
    "bundle": 0.05,
}

HOST_MODIFIERS: dict[str, float] = {
    "kiosk": 0.15,
    "domain_controller": 0.20,
    "public_facing_server": 0.10,
    "mobile_device": -0.10,
}


def reboot_factor(product_meta: dict[str, Any] | None, rng: np.random.Generator) -> float:
    if product_meta is None:
        return 0.5
    p = float(product_meta.get("reboot_required_prior", 0.1))
    return 1.0 if rng.random() < p else 0.0


def user_disruption_factor(host: Host, product_meta: dict[str, Any] | None) -> float:
    if host.role in ("standard_workstation", "privileged_workstation", "kiosk", "mobile_device"):
        return 1.0 if (product_meta is None or product_meta.get("category") != "endpoint_agent") else 0.3
    return 0.3


def service_dependency_factor(product_meta: dict[str, Any] | None) -> float:
    if product_meta is None:
        return 0.5
    category = product_meta.get("category")
    if category in ("os_component", "database", "web_server"):
        return 1.0
    if category in ("runtime_library", "endpoint_agent"):
        return 0.7
    return 0.3


def regression_factor(product_meta: dict[str, Any] | None, rng: np.random.Generator) -> float:
    """Sample from a Beta around a per-category prior regression rate."""
    if product_meta is None:
        return 0.5
    category = product_meta.get("category")
    mean = {
        "browser": 0.05,
        "productivity": 0.10,
        "endpoint_agent": 0.10,
        "remote_access": 0.10,
        "runtime_library": 0.15,
        "web_server": 0.20,
        "database": 0.25,
        "os_component": 0.20,
        "mobile_os_component": 0.05,
    }.get(category, 0.10)
    a = max(0.5, mean * 10)
    b = max(0.5, (1.0 - mean) * 10)
    return float(rng.beta(a, b))


def deployment_channel_factor(product_meta: dict[str, Any] | None) -> float:
    if product_meta is None:
        return 1.0
    return float(product_meta.get("deployment_channel_available", 1.0))


def bundle_factor(product_meta: dict[str, Any] | None) -> float:
    if product_meta is None:
        return 0.0
    return 1.0 if product_meta.get("bundle_group") else 0.0


def host_modifier(host_role: str) -> float:
    return float(HOST_MODIFIERS.get(host_role, 0.0))


def compute_complexity(
    vulnerability: Vulnerability,
    host: Host,
    product_meta: dict[str, Any] | None,
    rng: np.random.Generator,
) -> RemediationComplexityProfile:
    f_reboot = reboot_factor(product_meta, rng)
    f_user = user_disruption_factor(host, product_meta)
    f_srvdep = service_dependency_factor(product_meta)
    f_regr = regression_factor(product_meta, rng)
    f_chan = deployment_channel_factor(product_meta)
    f_bund = bundle_factor(product_meta)
    h_mod = host_modifier(host.role)

    base = (
        WEIGHTS["reboot"] * f_reboot
        + WEIGHTS["user_disruption"] * f_user
        + WEIGHTS["service_dep"] * f_srvdep
        + WEIGHTS["regression"] * f_regr
        + WEIGHTS["channel"] * (1.0 - f_chan)
        + WEIGHTS["bundle"] * (1.0 - f_bund)
    )
    score = float(max(0.0, min(1.0, base + h_mod)))

    pair_id = f"{host.host_id}:{vulnerability.cve_id}"
    return RemediationComplexityProfile(
        pair_id=pair_id,
        complexity_score=score,
        factor_reboot=float(f_reboot),
        factor_user_disruption=float(f_user),
        factor_service_dep=float(f_srvdep),
        factor_regression=float(f_regr),
        factor_channel=float(f_chan),
        factor_bundle=float(f_bund),
        host_modifier=float(h_mod),
    )
