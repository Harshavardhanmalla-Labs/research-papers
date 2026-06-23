"""Vulnerability-host pair construction."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, time
from typing import Any

import pandas as pd

from paper1.audit.schema import Host, Vulnerability, VulnerabilityHostPair
from paper1.feeds.cve_client import CPEParseError, parse_cpe23

__all__ = [
    "build_pairs",
    "build_pairs_frame",
    "is_patch_already_installed",
    "match_vulnerability_to_host",
    "product_keys_from_host",
    "product_keys_from_vulnerability",
]

_WILDCARD_VERSIONS = {"*", "-", ""}


def _to_date(value: date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError(f"Expected date|datetime; got {type(value).__name__}")


def _to_utc_midnight(value: date | datetime) -> datetime:
    d = _to_date(value)
    return datetime.combine(d, time(hour=0), tzinfo=UTC)


def product_keys_from_host(host: Host) -> set[tuple[str, str]]:
    """Return the set of (vendor, product) keys for the host's software."""
    keys: set[tuple[str, str]] = set()
    for sw in host.installed_software:
        try:
            p = parse_cpe23(sw.cpe)
        except CPEParseError:
            continue
        keys.add((p.vendor.lower(), p.product.lower()))
    return keys


def product_keys_from_vulnerability(
    vuln: Vulnerability,
) -> dict[tuple[str, str], bool]:
    """Return {(vendor, product): has_concrete_version} from the vuln CPEs.

    ``has_concrete_version`` is True if at least one CPE for that key
    names a non-wildcard version.
    """
    out: dict[tuple[str, str], bool] = {}
    for cpe in vuln.cpe_matches:
        try:
            p = parse_cpe23(cpe)
        except CPEParseError:
            continue
        key = (p.vendor.lower(), p.product.lower())
        concrete = p.version not in _WILDCARD_VERSIONS
        out[key] = out.get(key, False) or concrete
    return out


def match_vulnerability_to_host(
    vuln: Vulnerability,
    host: Host,
    *,
    product_key_override: tuple[str, str] | None = None,
) -> dict[str, Any] | None:
    """Return match metadata for (vuln, host) or None if no product match.

    - Concrete-version CPE match  -> cpe_exact, confidence 1.0
    - Wildcard-version CPE match  -> cpe_fuzzy, confidence 0.7
    - product_key override match  -> manual,    confidence 0.6
    """
    host_keys = product_keys_from_host(host)

    if product_key_override is not None:
        key = (product_key_override[0].lower(), product_key_override[1].lower())
        if key in host_keys:
            return {
                "match_method": "manual",
                "match_confidence": 0.6,
                "matched_product_key": key,
            }
        return None

    vuln_keys = product_keys_from_vulnerability(vuln)
    matched = set(vuln_keys) & host_keys
    if not matched:
        return None
    any_concrete = any(vuln_keys[k] for k in matched)
    # Deterministic representative key for provenance.
    representative = sorted(matched)[0]
    if any_concrete:
        return {
            "match_method": "cpe_exact",
            "match_confidence": 1.0,
            "matched_product_key": representative,
        }
    return {
        "match_method": "cpe_fuzzy",
        "match_confidence": 0.7,
        "matched_product_key": representative,
    }


def is_patch_already_installed(vuln: Vulnerability, host: Host) -> bool:
    """Conservative remediation check.

    Excludes the pair only when the host's patch_state explicitly lists
    the CVE in ``remediated_cves``. No implicit supersession inference.
    """
    remediated = getattr(host.patch_state, "remediated_cves", None) or []
    return vuln.cve_id in set(remediated)


def _origin_feeds(vuln: Vulnerability) -> list[str]:
    feeds = ["nvd"]
    if vuln.vendor_advisory_refs:
        feeds.append("vendor_advisory")
    return feeds


def build_pairs(
    vulnerabilities: list[Vulnerability],
    hosts: list[Host],
    t0: date | datetime,
    scope_filter: Callable[[Host], bool] | None = None,
    min_confidence: float = 0.5,
) -> list[VulnerabilityHostPair]:
    """Build the set of open vulnerability-host pairs at time t0.

    Pairs are returned sorted by pair_id for deterministic output.
    """
    t0_date = _to_date(t0)
    first_observed = _to_utc_midnight(t0)
    pairs: list[VulnerabilityHostPair] = []

    for vuln in vulnerabilities:
        if vuln.disclosure_date > t0_date:
            continue
        for host in hosts:
            if scope_filter is not None and not scope_filter(host):
                continue
            match = match_vulnerability_to_host(vuln, host)
            if match is None:
                continue
            if match["match_confidence"] < min_confidence:
                continue
            if is_patch_already_installed(vuln, host):
                continue
            pairs.append(
                VulnerabilityHostPair(
                    pair_id=f"{host.host_id}:{vuln.cve_id}",
                    cve_id=vuln.cve_id,
                    host_id=host.host_id,
                    match_method=match["match_method"],
                    match_confidence=float(match["match_confidence"]),
                    pair_status="open",
                    first_observed=first_observed,
                    pair_origin_feeds=_origin_feeds(vuln),
                )
            )

    pairs.sort(key=lambda p: p.pair_id)
    return pairs


def build_pairs_frame(
    vulnerabilities: list[Vulnerability],
    hosts: list[Host],
    t0: date | datetime,
    scope_filter: Callable[[Host], bool] | None = None,
    min_confidence: float = 0.5,
) -> pd.DataFrame:
    """Build pairs and return them as a DataFrame (delegates to frames)."""
    from paper1.model.frames import pairs_to_frame

    pairs = build_pairs(
        vulnerabilities, hosts, t0, scope_filter=scope_filter, min_confidence=min_confidence
    )
    return pairs_to_frame(pairs)
