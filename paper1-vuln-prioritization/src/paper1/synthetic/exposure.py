"""Per-pair local exposure score.

Exposure is computed as:

    X(v, h) = installed * service_running * network_reachable
              * (1 - mitigation_present) * auth_precondition

Each factor is in [0, 1]. Unobservable preconditions default to 0.5 and
are recorded in ``preconditions_unknown`` so the auditor can see why
the score lies where it does.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from paper1.audit.schema import (
    Host,
    LocalExposureProfile,
    Vulnerability,
)
from paper1.feeds.cve_client import CPEParseError, parse_cpe23

__all__ = [
    "EVALUATOR_VERSION",
    "auth_precondition_factor",
    "compute_exposure",
    "installed_vuln_factor",
    "mitigation_present_factor",
    "network_reachable_factor",
    "service_running_factor",
]


EVALUATOR_VERSION = "lee_v0.2"
_UNKNOWN_DEFAULT = 0.5


def _product_keys_from_cpes(cpes: list[str]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for c in cpes:
        try:
            p = parse_cpe23(c)
        except CPEParseError:
            continue
        keys.add((p.vendor.lower(), p.product.lower()))
    return keys


def installed_vuln_factor(
    vulnerability: Vulnerability,
    host: Host,
    *,
    product_key: tuple[str, str] | None = None,
) -> float:
    """1.0 if the vulnerable product/version is installed; 0.0 otherwise.

    Matching uses (vendor, product) keys from CPEs on both sides. The
    caller may pass an explicit ``product_key`` to override.
    """
    if product_key is not None:
        target_keys: set[tuple[str, str]] = {product_key}
    else:
        target_keys = _product_keys_from_cpes(vulnerability.cpe_matches)
    if not target_keys:
        return 0.0
    host_keys = _product_keys_from_cpes([s.cpe for s in host.installed_software])
    return 1.0 if (target_keys & host_keys) else 0.0


def service_running_factor(
    product_key: tuple[str, str] | None,
    host: Host,
    service_catalog: dict[str, Any],
    rng: np.random.Generator,
    *,
    precondition_completeness: float = 1.0,
) -> tuple[float, str | None]:
    """Return (factor, unknown_reason). ``factor`` is in [0, 1]."""
    if rng.random() > precondition_completeness:
        return _UNKNOWN_DEFAULT, "service_running"
    if product_key is None:
        return _UNKNOWN_DEFAULT, "service_running"
    services = service_catalog.get("services") or {}
    entry = services.get(product_key[1])
    if entry is None:
        return _UNKNOWN_DEFAULT, "service_running"
    enabled = bool((entry.get("default_enabled_by_role") or {}).get(host.role, False))
    return (1.0 if enabled else 0.0), None


def network_reachable_factor(
    vulnerability: Vulnerability,
    host: Host,
    *,
    precondition_completeness: float = 1.0,
    rng: np.random.Generator | None = None,
) -> tuple[float, str | None]:
    """Reachability heuristic from host zone and CVE attack vector.

    For Phase 3 we look at the CVSS v4 / v3.1 vector strings if present
    and map AV:N, AV:A, AV:L, AV:P to zone-dependent factors.
    """
    if rng is not None and rng.random() > precondition_completeness:
        return _UNKNOWN_DEFAULT, "network_reachable"
    vec = vulnerability.cvss_v4_vector or vulnerability.cvss_v31_vector or ""
    av = _extract_av(vec)
    zone = host.network_zone
    if av == "N":  # network
        if zone in ("public", "dmz"):
            return 1.0, None
        return 0.3, None
    if av == "A":  # adjacent network
        if zone in ("internal", "dmz"):
            return 0.7, None
        return 0.1, None
    if av == "L":  # local
        return 1.0, None
    if av == "P":  # physical
        return 0.1, None
    # Unknown attack vector — treat as unknown.
    return _UNKNOWN_DEFAULT, "network_reachable"


def _extract_av(vector: str) -> str | None:
    for part in vector.split("/"):
        if part.startswith("AV:"):
            return part.split(":", 1)[1][:1].upper()
    return None


def mitigation_present_factor(
    product_key: tuple[str, str] | None,
    product_meta: dict[str, Any] | None,
    rng: np.random.Generator,
    *,
    precondition_completeness: float = 1.0,
) -> tuple[float, str | None, list[str]]:
    """Sample mitigation presence; return (factor, unknown_reason, observed)."""
    if rng.random() > precondition_completeness:
        return _UNKNOWN_DEFAULT, "mitigation_present", []
    if product_meta is None:
        return 0.0, None, []
    prior = float(product_meta.get("mitigation_prior", 0.0))
    if prior <= 0.0:
        return 0.0, None, []
    if rng.random() < prior:
        return 1.0, None, ["mitigation_observed"]
    return 0.0, None, []


def auth_precondition_factor(
    vulnerability: Vulnerability,
    host: Host,
    rng: np.random.Generator,
    *,
    precondition_completeness: float = 1.0,
) -> tuple[float, str | None]:
    """Probability that the CVE's authentication precondition is met."""
    if rng.random() > precondition_completeness:
        return _UNKNOWN_DEFAULT, "auth_precondition_met"
    vec = vulnerability.cvss_v4_vector or vulnerability.cvss_v31_vector or ""
    pr = _extract_pr(vec)
    if pr is None:
        return _UNKNOWN_DEFAULT, "auth_precondition_met"
    if pr == "N":
        return 1.0, None
    # Authentication required: internal hosts have ambient auth surface;
    # restricted hosts less so.
    if host.network_zone in ("internal",):
        return 0.6, None
    if host.network_zone in ("restricted", "air_gapped"):
        return 0.3, None
    return 0.5, None


def _extract_pr(vector: str) -> str | None:
    for part in vector.split("/"):
        if part.startswith("PR:"):
            return part.split(":", 1)[1][:1].upper()
    return None


def compute_exposure(
    vulnerability: Vulnerability,
    host: Host,
    *,
    product_meta: dict[str, Any] | None = None,
    product_key: tuple[str, str] | None = None,
    service_catalog: dict[str, Any],
    mitigation_catalog: dict[str, Any] | None = None,
    precondition_completeness: float = 1.0,
    rng: np.random.Generator,
) -> LocalExposureProfile:
    """Compute the LocalExposureProfile for a (vulnerability, host) pair."""
    unknown: list[str] = []
    mitigations_observed: list[str] = []

    f_install = installed_vuln_factor(vulnerability, host, product_key=product_key)
    f_service, u = service_running_factor(
        product_key,
        host,
        service_catalog,
        rng,
        precondition_completeness=precondition_completeness,
    )
    if u:
        unknown.append(u)
    f_net, u = network_reachable_factor(
        vulnerability,
        host,
        precondition_completeness=precondition_completeness,
        rng=rng,
    )
    if u:
        unknown.append(u)
    f_mit, u, observed = mitigation_present_factor(
        product_key,
        product_meta,
        rng,
        precondition_completeness=precondition_completeness,
    )
    if u:
        unknown.append(u)
    mitigations_observed.extend(observed)
    f_auth, u = auth_precondition_factor(
        vulnerability,
        host,
        rng,
        precondition_completeness=precondition_completeness,
    )
    if u:
        unknown.append(u)

    score = float(
        max(0.0, min(1.0, f_install * f_service * f_net * (1.0 - f_mit) * f_auth))
    )
    pair_id = f"{host.host_id}:{vulnerability.cve_id}"
    return LocalExposureProfile(
        pair_id=pair_id,
        exposure_score=score,
        factor_installed_vuln=float(f_install),
        factor_service_running=float(f_service),
        factor_network_reachable=float(f_net),
        factor_mitigation_present=float(f_mit),
        factor_auth_precondition_met=float(f_auth),
        preconditions_unknown=sorted(set(unknown)),
        mitigations_observed=sorted(set(mitigations_observed)),
        reachability_assumption=f"zone={host.network_zone}",
        evaluator_version=EVALUATOR_VERSION,
    )
