"""Local exposure tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

from paper1.audit.schema import (
    Host,
    InstalledSoftware,
    LocalExposureProfile,
    PatchState,
    Vulnerability,
)
from paper1.synthetic.catalogs import load_service_catalog
from paper1.synthetic.exposure import compute_exposure
from paper1.utils.seeds import make_rng


def _utc_dt() -> datetime:
    return datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC)


def _make_vuln(
    *,
    cve_id: str = "CVE-2025-0001",
    cvss_vector: str = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
    cpe: str = "cpe:2.3:a:nginx:nginx:1.24.0:*:*:*:*:*:*:*",
) -> Vulnerability:
    return Vulnerability(
        cve_id=cve_id,
        cpe_matches=[cpe],
        cvss_v4_vector=cvss_vector,
        cvss_v4_base=9.3,
        cvss_version_used="v4",
        disclosure_date=date(2025, 4, 1),
        feed_fetch_timestamp=_utc_dt(),
    )


def _make_host(
    *,
    role: str = "public_facing_server",
    zone: str = "dmz",
    os_family: str = "linux",
    installed: list[InstalledSoftware] | None = None,
) -> Host:
    return Host(
        host_id="H-test-001",
        os_family=os_family,
        os_version="Ubuntu 24.04 LTS",
        role=role,
        network_zone=zone,
        identity_tier="tier_1",
        installed_software=installed or [],
        patch_state=PatchState(kbs_installed=[], last_scan=_utc_dt(), scan_source="t"),
        last_seen_per_source={"inventory": _utc_dt()},
        group_id="G-1",
    )


def _nginx_software(version: str = "1.24.0") -> InstalledSoftware:
    return InstalledSoftware(
        cpe=f"cpe:2.3:a:nginx:nginx:{version}:*:*:*:*:*:*:*",
        product="nginx",
        vendor="nginx",
        version=version,
    )


def test_exposure_zero_when_product_not_installed():
    services = load_service_catalog()
    vuln = _make_vuln()
    host = _make_host(installed=[])
    profile = compute_exposure(
        vulnerability=vuln,
        host=host,
        service_catalog=services,
        rng=make_rng(1),
    )
    assert isinstance(profile, LocalExposureProfile)
    assert profile.factor_installed_vuln == 0.0
    assert profile.exposure_score == 0.0


def test_exposure_high_when_all_factors_favor():
    services = load_service_catalog()
    vuln = _make_vuln(
        cvss_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
    )
    host = _make_host(
        role="public_facing_server",
        zone="public",
        installed=[_nginx_software()],
    )
    profile = compute_exposure(
        vulnerability=vuln,
        host=host,
        product_meta={"category": "web_server", "mitigation_prior": 0.0},
        product_key=("nginx", "nginx"),
        service_catalog=services,
        rng=make_rng(1),
        precondition_completeness=1.0,
    )
    assert profile.factor_installed_vuln == 1.0
    assert profile.factor_service_running == 1.0
    assert profile.factor_network_reachable == 1.0
    assert profile.factor_mitigation_present == 0.0
    assert profile.exposure_score > 0.5


def test_exposure_dmz_vs_internal_reachability_for_network_vector():
    services = load_service_catalog()
    vuln = _make_vuln(
        cvss_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
    )
    dmz_host = _make_host(role="public_facing_server", zone="dmz", installed=[_nginx_software()])
    internal_host = _make_host(role="member_server", zone="internal", installed=[_nginx_software()])
    dmz_profile = compute_exposure(
        vulnerability=vuln,
        host=dmz_host,
        product_meta={"category": "web_server", "mitigation_prior": 0.0},
        product_key=("nginx", "nginx"),
        service_catalog=services,
        rng=make_rng(1),
    )
    internal_profile = compute_exposure(
        vulnerability=vuln,
        host=internal_host,
        product_meta={"category": "web_server", "mitigation_prior": 0.0},
        product_key=("nginx", "nginx"),
        service_catalog=services,
        rng=make_rng(1),
    )
    assert dmz_profile.factor_network_reachable >= internal_profile.factor_network_reachable


def test_exposure_unknown_precondition_defaults_recorded():
    services = load_service_catalog()
    vuln = _make_vuln()
    host = _make_host(role="public_facing_server", zone="dmz", installed=[_nginx_software()])
    profile = compute_exposure(
        vulnerability=vuln,
        host=host,
        product_meta={"category": "web_server", "mitigation_prior": 0.0},
        product_key=("nginx", "nginx"),
        service_catalog=services,
        rng=make_rng(1),
        precondition_completeness=0.0,  # every factor becomes "unknown"
    )
    # All four soft factors should have defaulted to 0.5 and been recorded.
    assert set(profile.preconditions_unknown) >= {
        "service_running",
        "network_reachable",
        "mitigation_present",
        "auth_precondition_met",
    }


def test_exposure_schema_validates():
    services = load_service_catalog()
    vuln = _make_vuln()
    host = _make_host(installed=[_nginx_software()])
    profile = compute_exposure(
        vulnerability=vuln,
        host=host,
        product_key=("nginx", "nginx"),
        service_catalog=services,
        rng=make_rng(1),
    )
    assert isinstance(profile, LocalExposureProfile)
    assert 0.0 <= profile.exposure_score <= 1.0
    assert profile.pair_id == f"{host.host_id}:{vuln.cve_id}"


def test_exposure_no_cpe_match_yields_zero():
    services = load_service_catalog()
    vuln = _make_vuln(cpe="cpe:2.3:a:other:product:1.0:*:*:*:*:*:*:*")
    host = _make_host(installed=[_nginx_software()])
    profile = compute_exposure(
        vulnerability=vuln,
        host=host,
        service_catalog=services,
        rng=make_rng(1),
    )
    assert profile.factor_installed_vuln == 0.0
    assert profile.exposure_score == 0.0
