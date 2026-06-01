"""Vulnerability-host pair construction tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

from paper1.audit.schema import (
    Host,
    InstalledSoftware,
    PatchState,
    Vulnerability,
    VulnerabilityHostPair,
)
from paper1.model.pairs import (
    build_pairs,
    build_pairs_frame,
    is_patch_already_installed,
    match_vulnerability_to_host,
    product_keys_from_host,
    product_keys_from_vulnerability,
)


def _utc() -> datetime:
    return datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC)


def _host(
    *,
    host_id: str = "H-1",
    software: list[InstalledSoftware] | None = None,
    remediated: list[str] | None = None,
) -> Host:
    return Host(
        host_id=host_id,
        os_family="linux",
        os_version="Ubuntu 24.04 LTS",
        role="member_server",
        network_zone="internal",
        identity_tier="tier_1",
        installed_software=software
        or [
            InstalledSoftware(
                cpe="cpe:2.3:a:openssl:openssl:3.0.13:*:*:*:*:*:*:*",
                product="openssl",
                vendor="openssl",
                version="3.0.13",
            )
        ],
        patch_state=PatchState(
            kbs_installed=[],
            last_scan=_utc(),
            scan_source="t",
            remediated_cves=remediated or [],
        ),
        last_seen_per_source={"inventory": _utc()},
        group_id="G-1",
    )


def _vuln(
    *,
    cve_id: str = "CVE-2024-0001",
    cpe: str = "cpe:2.3:a:openssl:openssl:3.0.13:*:*:*:*:*:*:*",
    disclosure: date = date(2025, 1, 1),
) -> Vulnerability:
    return Vulnerability(
        cve_id=cve_id,
        cpe_matches=[cpe],
        cvss_v4_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
        cvss_v4_base=9.3,
        cvss_version_used="v4",
        disclosure_date=disclosure,
        feed_fetch_timestamp=_utc(),
    )


# -----------------------------------------------------------------------
# product key extraction
# -----------------------------------------------------------------------


def test_product_keys_from_host():
    keys = product_keys_from_host(_host())
    assert ("openssl", "openssl") in keys


def test_product_keys_from_vulnerability_concrete():
    keys = product_keys_from_vulnerability(_vuln())
    assert keys[("openssl", "openssl")] is True


def test_product_keys_from_vulnerability_wildcard():
    v = _vuln(cpe="cpe:2.3:a:sqlite:sqlite:*:*:*:*:*:*:*:*")
    keys = product_keys_from_vulnerability(v)
    assert keys[("sqlite", "sqlite")] is False


# -----------------------------------------------------------------------
# matching
# -----------------------------------------------------------------------


def test_exact_cpe_match():
    m = match_vulnerability_to_host(_vuln(), _host())
    assert m is not None
    assert m["match_method"] == "cpe_exact"
    assert m["match_confidence"] == 1.0


def test_wildcard_version_is_fuzzy():
    sw = [
        InstalledSoftware(
            cpe="cpe:2.3:a:sqlite:sqlite:3.45.0:*:*:*:*:*:*:*",
            product="sqlite",
            vendor="sqlite",
            version="3.45.0",
        )
    ]
    v = _vuln(cve_id="CVE-2024-0002", cpe="cpe:2.3:a:sqlite:sqlite:*:*:*:*:*:*:*:*")
    m = match_vulnerability_to_host(v, _host(software=sw))
    assert m is not None
    assert m["match_method"] == "cpe_fuzzy"
    assert m["match_confidence"] == 0.7


def test_no_match_returns_none():
    v = _vuln(cpe="cpe:2.3:a:other:product:1.0:*:*:*:*:*:*:*")
    assert match_vulnerability_to_host(v, _host()) is None


def test_manual_override_match():
    m = match_vulnerability_to_host(
        _vuln(cpe="cpe:2.3:a:zzz:zzz:1.0:*:*:*:*:*:*:*"),
        _host(),
        product_key_override=("openssl", "openssl"),
    )
    assert m is not None
    assert m["match_method"] == "manual"
    assert m["match_confidence"] == 0.6


def test_manual_override_no_match_returns_none():
    m = match_vulnerability_to_host(
        _vuln(), _host(), product_key_override=("absent", "absent")
    )
    assert m is None


# -----------------------------------------------------------------------
# patch state
# -----------------------------------------------------------------------


def test_remediated_cve_detected():
    v = _vuln(cve_id="CVE-2024-0009")
    host = _host(remediated=["CVE-2024-0009"])
    assert is_patch_already_installed(v, host)


def test_non_remediated_cve_not_flagged():
    assert not is_patch_already_installed(_vuln(), _host())


# -----------------------------------------------------------------------
# build_pairs
# -----------------------------------------------------------------------


def test_build_pairs_exact_match_creates_pair():
    pairs = build_pairs([_vuln()], [_host()], date(2025, 6, 1))
    assert len(pairs) == 1
    assert isinstance(pairs[0], VulnerabilityHostPair)
    assert pairs[0].pair_id == "H-1:CVE-2024-0001"
    assert pairs[0].pair_status == "open"
    assert pairs[0].first_observed == datetime(2025, 6, 1, 0, 0, 0, tzinfo=UTC)


def test_build_pairs_excludes_future_disclosure():
    v = _vuln(cve_id="CVE-2027-0001", disclosure=date(2027, 1, 1))
    pairs = build_pairs([v], [_host()], date(2025, 6, 1))
    assert pairs == []


def test_build_pairs_excludes_remediated():
    v = _vuln(cve_id="CVE-2024-0009")
    host = _host(remediated=["CVE-2024-0009"])
    pairs = build_pairs([v], [host], date(2025, 6, 1))
    assert pairs == []


def test_build_pairs_min_confidence_excludes_fuzzy():
    sw = [
        InstalledSoftware(
            cpe="cpe:2.3:a:sqlite:sqlite:3.45.0:*:*:*:*:*:*:*",
            product="sqlite",
            vendor="sqlite",
            version="3.45.0",
        )
    ]
    v = _vuln(cve_id="CVE-2024-0002", cpe="cpe:2.3:a:sqlite:sqlite:*:*:*:*:*:*:*:*")
    pairs = build_pairs([v], [_host(software=sw)], date(2025, 6, 1), min_confidence=0.8)
    assert pairs == []
    # With a permissive threshold the fuzzy pair survives.
    pairs2 = build_pairs([v], [_host(software=sw)], date(2025, 6, 1), min_confidence=0.5)
    assert len(pairs2) == 1


def test_build_pairs_deterministic_and_sorted():
    hosts = [_host(host_id=f"H-{i}") for i in range(5)]
    a = build_pairs([_vuln()], hosts, date(2025, 6, 1))
    b = build_pairs([_vuln()], hosts, date(2025, 6, 1))
    assert [p.pair_id for p in a] == [p.pair_id for p in b]
    assert [p.pair_id for p in a] == sorted(p.pair_id for p in a)


def test_build_pairs_scope_filter():
    hosts = [_host(host_id="H-keep"), _host(host_id="H-drop")]
    pairs = build_pairs(
        [_vuln()],
        hosts,
        date(2025, 6, 1),
        scope_filter=lambda h: h.host_id == "H-keep",
    )
    assert len(pairs) == 1
    assert pairs[0].host_id == "H-keep"


def test_build_pairs_frame_columns():
    frame = build_pairs_frame([_vuln()], [_host()], date(2025, 6, 1))
    assert list(frame.columns) == [
        "pair_id",
        "cve_id",
        "host_id",
        "match_method",
        "match_confidence",
        "pair_status",
        "first_observed",
        "pair_origin_feeds",
    ]
    assert len(frame) == 1
