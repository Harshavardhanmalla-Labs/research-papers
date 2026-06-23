"""Cross-feed no-future-leakage tests.

Every feed client must refuse to surface records whose published or
added date is strictly after the requested as-of date. These tests use
local fixtures only.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from paper1.feeds.base import BaseFeedClient, FutureDataError
from paper1.feeds.epss_client import EPSSClient, normalize_epss_csv
from paper1.feeds.kev_client import KEVClient
from paper1.feeds.nvd_client import NVDClient
from paper1.feeds.poc_client import POCClient, normalize_exploitdb_csv

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------


def _epss_csv(score_date: date) -> str:
    iso = score_date.isoformat()
    return (
        f"#model_version:v4,score_date:{iso}T00:00:00+0000\n"
        "cve,epss,percentile\n"
        "CVE-2025-0001,0.10,0.50\n"
    )


def _kev_catalog(date_added_iso: str) -> dict:
    return {
        "vulnerabilities": [
            {
                "cveID": "CVE-2025-FUT",
                "dateAdded": date_added_iso,
                "dueDate": "9999-12-31",
                "requiredAction": "x",
            }
        ]
    }


def _nvd_record(cve_id: str, published_iso: str) -> dict:
    return {
        "cve": {
            "id": cve_id,
            "published": published_iso,
            "metrics": {
                "cvssMetricV31": [
                    {
                        "cvssData": {
                            "version": "3.1",
                            "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                            "baseScore": 9.8,
                        }
                    }
                ]
            },
            "configurations": [
                {
                    "nodes": [
                        {
                            "cpeMatch": [
                                {
                                    "vulnerable": True,
                                    "criteria": "cpe:2.3:a:v:p:1.0:*:*:*:*:*:*:*",
                                }
                            ]
                        }
                    ]
                }
            ],
        }
    }


def _poc_csv(date_iso: str) -> str:
    return (
        "id,file,description,date_published,author,type,platform,port,codes\n"
        f"200,exploits/x.py,Future,{date_iso},a,remote,linux,,CVE-2025-FUT\n"
    )


# -----------------------------------------------------------------------
# EPSS
# -----------------------------------------------------------------------


def test_epss_get_asof_rejects_mismatched_as_of(tmp_path: Path):
    """If a snapshot's as_of_date column has values other than the requested
    date, get_asof raises explicitly."""
    client = EPSSClient(cache_root=tmp_path)
    # Hand-craft a row whose as_of_date doesn't match the requested date.
    df = pd.DataFrame(
        [
            {
                "cve_id": "CVE-2025-0001",
                "epss_score": 0.5,
                "epss_percentile": 0.5,
                "as_of_date": date(2026, 6, 1),  # different from snapshot date
                "epss_version": "v4",
                "source_name": "epss",
                "fetched_at": datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC).isoformat().replace("+00:00", "Z"),
                "source_url": "x",
                "source_version": "v4",
            }
        ]
    )
    client.write_snapshot(date(2026, 5, 26), df, fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC))
    with pytest.raises((ValueError, FutureDataError)):
        client.get_asof(date(2026, 5, 26))


def test_epss_normalize_with_future_score_date_caught_by_verify(tmp_path: Path):
    # Build a normalized frame whose as_of_date is in the future relative
    # to the requested cutoff. verify_no_future should raise.
    df = normalize_epss_csv(_epss_csv(date(2026, 6, 1)), date(2026, 6, 1))
    with pytest.raises(FutureDataError):
        BaseFeedClient.verify_no_future(df, date(2026, 5, 26), "as_of_date")


# -----------------------------------------------------------------------
# NVD
# -----------------------------------------------------------------------


def test_nvd_normalize_excludes_future_published(tmp_path: Path):
    client = NVDClient(cache_root=tmp_path)
    raw = {
        "vulnerabilities": [
            _nvd_record("CVE-2025-0001", "2025-04-08T00:00:00.000"),
            _nvd_record("CVE-2025-9999", "2026-06-15T00:00:00.000"),
        ]
    }
    df = client.normalize(raw, date(2026, 5, 31))
    assert "CVE-2025-9999" not in set(df["cve_id"])


def test_nvd_verify_no_future_directly(tmp_path: Path):
    client = NVDClient(cache_root=tmp_path)
    raw = {"vulnerabilities": [_nvd_record("CVE-2025-0001", "2025-04-08T00:00:00.000")]}
    df = client.normalize(raw, date(2026, 5, 31))
    # Sanity: a separately constructed frame with a future date triggers.
    bad = df.copy()
    bad["disclosure_date"] = date(2027, 1, 1)
    with pytest.raises(FutureDataError):
        BaseFeedClient.verify_no_future(bad, date(2026, 5, 31), "disclosure_date")


# -----------------------------------------------------------------------
# KEV
# -----------------------------------------------------------------------


def test_kev_normalize_excludes_future_date_added(tmp_path: Path):
    client = KEVClient(cache_root=tmp_path)
    df = client.normalize(_kev_catalog("2026-08-01"), date(2026, 5, 31))
    assert df.empty or "CVE-2025-FUT" not in set(df["cve_id"])


def test_kev_get_asof_does_not_surface_future(tmp_path: Path):
    client = KEVClient(cache_root=tmp_path)
    # Mix a past and future entry; persist; verify get_kev_asof drops future.
    catalog = {
        "vulnerabilities": [
            {
                "cveID": "CVE-2025-0001",
                "dateAdded": "2025-05-01",
                "dueDate": "2025-06-01",
                "requiredAction": "x",
            },
            {
                "cveID": "CVE-2025-FUT",
                "dateAdded": "2026-08-01",
                "dueDate": "2026-09-01",
                "requiredAction": "x",
            },
        ]
    }
    df = client.normalize(catalog, date(2026, 5, 31))
    client.write_snapshot(date(2026, 5, 31), df, fetched_at=datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC))
    out = client.get_kev_asof(date(2026, 5, 31))
    assert "CVE-2025-0001" in set(out["cve_id"])
    assert "CVE-2025-FUT" not in set(out["cve_id"])


# -----------------------------------------------------------------------
# PoC
# -----------------------------------------------------------------------


def test_poc_get_first_seen_excludes_future(tmp_path: Path):
    client = POCClient(cache_root=tmp_path)
    df = normalize_exploitdb_csv(_poc_csv("2026-08-01"), as_of_date=date(2026, 5, 31))
    assert df.empty
    client.write_snapshot(
        date(2026, 5, 31), df,
        fetched_at=datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC),
    )
    out = client.get_poc_first_seen(None, date(2026, 5, 31))
    assert out.empty


# -----------------------------------------------------------------------
# BaseFeedClient.verify_no_future
# -----------------------------------------------------------------------


def test_base_verify_no_future_empty_frame():
    """Empty frame should not raise."""
    BaseFeedClient.verify_no_future(pd.DataFrame(), date(2026, 5, 31), "d")


def test_base_verify_no_future_missing_column():
    """Missing column is a no-op (verification is per-column when present)."""
    df = pd.DataFrame([{"id": 1, "other": date(2027, 1, 1)}])
    BaseFeedClient.verify_no_future(df, date(2026, 5, 31), "d")


def test_base_verify_no_future_string_dates_parsed():
    df = pd.DataFrame([{"id": 1, "d": "2026-05-26"}, {"id": 2, "d": "2026-06-15"}])
    with pytest.raises(FutureDataError):
        BaseFeedClient.verify_no_future(df, date(2026, 5, 31), "d")


def test_base_verify_no_future_datetime_dates():
    df = pd.DataFrame(
        [
            {"id": 1, "d": datetime(2026, 5, 26, tzinfo=UTC)},
            {"id": 2, "d": datetime(2026, 6, 15, tzinfo=UTC)},
        ]
    )
    with pytest.raises(FutureDataError):
        BaseFeedClient.verify_no_future(df, date(2026, 5, 31), "d")


def test_base_verify_no_future_rejects_datetime_cutoff():
    df = pd.DataFrame([{"d": date(2026, 5, 26)}])
    with pytest.raises(TypeError):
        BaseFeedClient.verify_no_future(df, datetime(2026, 5, 31, tzinfo=UTC), "d")  # type: ignore[arg-type]
