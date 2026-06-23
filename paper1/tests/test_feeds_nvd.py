"""NVD client tests — fixture-based, no network."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from paper1.audit.schema import Vulnerability
from paper1.feeds.nvd_client import (
    NVDClient,
    extract_cpe_matches,
    extract_cvss,
    normalize_nvd_record,
)


def _make_nvd_record(
    *,
    cve_id: str = "CVE-2025-00012345",
    published: str = "2025-04-08T12:00:00.000",
    with_v4: bool = True,
    with_v31: bool = True,
    with_cpe: bool = True,
    cwe: str | None = "CWE-79",
) -> dict:
    metrics: dict = {}
    if with_v4:
        metrics["cvssMetricV40"] = [
            {
                "source": "test",
                "type": "Primary",
                "cvssData": {
                    "version": "4.0",
                    "vectorString": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
                    "baseScore": 9.3,
                },
            }
        ]
    if with_v31:
        metrics["cvssMetricV31"] = [
            {
                "cvssData": {
                    "version": "3.1",
                    "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    "baseScore": 9.8,
                }
            }
        ]
    cve = {
        "id": cve_id,
        "published": published,
        "metrics": metrics,
        "references": [{"url": "https://vendor.example/advisory"}],
    }
    if cwe:
        cve["weaknesses"] = [
            {"description": [{"lang": "en", "value": cwe}]}
        ]
    if with_cpe:
        cve["configurations"] = [
            {
                "nodes": [
                    {
                        "cpeMatch": [
                            {
                                "vulnerable": True,
                                "criteria": "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*",
                                "versionStartIncluding": "1.0",
                                "versionEndExcluding": "2.0",
                            }
                        ]
                    }
                ]
            }
        ]
    return {"cve": cve}


# -----------------------------------------------------------------------
# extract_cvss
# -----------------------------------------------------------------------


def test_extract_cvss_prefers_v4():
    rec = _make_nvd_record(with_v4=True, with_v31=True)["cve"]
    cvss = extract_cvss(rec)
    assert cvss["cvss_version_used"] == "v4"
    assert cvss["cvss_v4_base"] == 9.3
    assert cvss["cvss_v31_base"] == 9.8


def test_extract_cvss_falls_back_to_v31():
    rec = _make_nvd_record(with_v4=False, with_v31=True)["cve"]
    cvss = extract_cvss(rec)
    assert cvss["cvss_version_used"] == "v31"
    assert cvss["cvss_v4_base"] is None
    assert cvss["cvss_v31_base"] == 9.8


def test_extract_cvss_no_metrics_returns_none():
    rec = _make_nvd_record(with_v4=False, with_v31=False)["cve"]
    cvss = extract_cvss(rec)
    assert cvss["cvss_version_used"] is None


# -----------------------------------------------------------------------
# extract_cpe_matches
# -----------------------------------------------------------------------


def test_extract_cpe_matches_returns_canonical():
    rec = _make_nvd_record(with_cpe=True)["cve"]
    cpes, warnings = extract_cpe_matches(rec)
    assert len(cpes) == 1
    assert cpes[0].startswith("cpe:2.3:a:vendor:product")
    assert warnings == []


def test_extract_cpe_matches_warns_on_malformed():
    rec = {
        "configurations": [
            {
                "nodes": [
                    {
                        "cpeMatch": [
                            {"vulnerable": True, "criteria": "not-a-cpe"},
                            {"vulnerable": True, "criteria": "cpe:2.3:a:v:p:1:*:*:*:*:*:*:*"},
                        ]
                    }
                ]
            }
        ]
    }
    cpes, warnings = extract_cpe_matches(rec)
    assert len(cpes) == 1
    assert len(warnings) == 1


def test_extract_cpe_matches_empty_config():
    rec = {"configurations": []}
    cpes, warnings = extract_cpe_matches(rec)
    assert cpes == []
    assert warnings == []


# -----------------------------------------------------------------------
# normalize_nvd_record
# -----------------------------------------------------------------------


def test_normalize_valid_record():
    row, warnings = normalize_nvd_record(_make_nvd_record())
    assert row is not None
    assert row["cve_id"] == "CVE-2025-00012345"
    assert row["cwe_ids"] == ["CWE-79"]
    assert row["cvss_version_used"] == "v4"
    assert row["disclosure_date"] == date(2025, 4, 8)


def test_normalize_invalid_cve_id():
    row, warnings = normalize_nvd_record({"cve": {"id": "BAD-0001-1"}})
    assert row is None
    assert any("missing or invalid cve id" in w for w in warnings)


def test_normalize_missing_cvss_skipped():
    row, warnings = normalize_nvd_record(
        _make_nvd_record(with_v4=False, with_v31=False)
    )
    assert row is None
    assert any("no CVSS" in w for w in warnings)


def test_normalize_no_cpe_emits_warning_but_row_returned():
    row, warnings = normalize_nvd_record(_make_nvd_record(with_cpe=False))
    assert row is not None
    assert row["cpe_matches"] == []
    assert any("no CPE matches" in w for w in warnings)


def test_normalized_dict_instantiates_vulnerability_schema():
    row, _ = normalize_nvd_record(_make_nvd_record())
    assert row is not None
    # Build kwargs in the shape Vulnerability expects.
    kwargs = {
        "cve_id": row["cve_id"],
        "cwe_ids": row["cwe_ids"],
        "cpe_matches": row["cpe_matches"],
        "cvss_v4_vector": row["cvss_v4_vector"],
        "cvss_v4_base": row["cvss_v4_base"],
        "cvss_v31_vector": row["cvss_v31_vector"],
        "cvss_v31_base": row["cvss_v31_base"],
        "cvss_version_used": row["cvss_version_used"],
        "disclosure_date": row["disclosure_date"],
        "vendor_advisory_refs": row["vendor_advisory_refs"],
        "mitigations_listed": row["mitigations_listed"],
        "preconditions": row["preconditions"],
        "feed_fetch_timestamp": datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    }
    v = Vulnerability(**kwargs)
    assert v.cve_id == "CVE-2025-00012345"


# -----------------------------------------------------------------------
# NVDClient.normalize and as-of behavior
# -----------------------------------------------------------------------


def test_client_normalize_filters_future_disclosures(tmp_path: Path):
    client = NVDClient(cache_root=tmp_path)
    raw = {
        "vulnerabilities": [
            _make_nvd_record(cve_id="CVE-2025-0001", published="2025-01-01T00:00:00.000"),
            _make_nvd_record(cve_id="CVE-2026-9999", published="2026-06-01T00:00:00.000"),
        ]
    }
    df = client.normalize(raw, date(2026, 5, 31))
    assert len(df) == 1
    assert df["cve_id"].iloc[0] == "CVE-2025-0001"


def test_client_normalize_collects_warnings(tmp_path: Path):
    client = NVDClient(cache_root=tmp_path)
    raw = {
        "vulnerabilities": [
            _make_nvd_record(cve_id="CVE-2025-0001"),
            {"cve": {"id": "BAD-2025-1"}},
        ]
    }
    df = client.normalize(raw, date(2026, 5, 31))
    assert len(df) == 1
    assert df.attrs["normalization_warnings"]


def test_client_normalize_raises_on_unsupported_type(tmp_path: Path):
    client = NVDClient(cache_root=tmp_path)
    with pytest.raises(TypeError):
        client.normalize(123, date(2026, 5, 31))


def test_client_fetch_raises_in_library_path(tmp_path: Path):
    client = NVDClient(cache_root=tmp_path)
    with pytest.raises(NotImplementedError):
        client.fetch(date(2026, 5, 31))


def test_get_cves_disclosed_asof_excludes_future(tmp_path: Path):
    client = NVDClient(cache_root=tmp_path)
    raw = {
        "vulnerabilities": [
            _make_nvd_record(cve_id="CVE-2025-0001", published="2025-01-01T00:00:00.000"),
            _make_nvd_record(cve_id="CVE-2025-0002", published="2025-05-15T00:00:00.000"),
        ]
    }
    df = client.normalize(raw, date(2025, 5, 31))
    client.write_snapshot(date(2025, 5, 31), df, fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC))
    out = client.get_cves_disclosed_asof(date(2025, 5, 31))
    assert set(out["cve_id"]) == {"CVE-2025-0001", "CVE-2025-0002"}
