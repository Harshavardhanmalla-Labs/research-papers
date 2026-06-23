"""KEV client tests — fixture-based, no network."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from paper1.feeds.kev_client import KEVClient, normalize_kev_catalog


def _fixture_catalog() -> dict:
    return {
        "title": "CISA Catalog of Known Exploited Vulnerabilities",
        "catalogVersion": "2026.05.26",
        "dateReleased": "2026-05-26T00:00:00.000Z",
        "count": 4,
        "vulnerabilities": [
            {
                "cveID": "CVE-2024-0001",
                "vendorProject": "Vendor",
                "product": "Product",
                "vulnerabilityName": "Test",
                "dateAdded": "2024-06-15",
                "shortDescription": "...",
                "requiredAction": "Apply updates",
                "dueDate": "2024-07-06",
            },
            {
                "cveID": "CVE-2025-0001",
                "vendorProject": "Vendor",
                "product": "Product",
                "vulnerabilityName": "Test2",
                "dateAdded": "2025-05-20",
                "shortDescription": "...",
                "requiredAction": "Apply updates",
                "dueDate": "2025-06-10",
            },
            {
                "cveID": "CVE-2026-0001",
                "vendorProject": "Vendor",
                "product": "Product",
                "vulnerabilityName": "Future",
                "dateAdded": "2026-08-01",  # future relative to typical as-of
                "shortDescription": "...",
                "requiredAction": "Apply updates",
                "dueDate": "2026-08-22",
            },
            {
                "cveID": "CVE-2025-9999",
                "vendorProject": "Vendor",
                "product": "Product",
                "vulnerabilityName": "Malformed",
                "dateAdded": "NOT-A-DATE",
                "requiredAction": "Apply updates",
                "dueDate": "2025-12-01",
            },
        ],
    }


def test_normalize_excludes_future_date_added():
    cat = _fixture_catalog()
    df = normalize_kev_catalog(cat, as_of_date=date(2026, 5, 31))
    assert "CVE-2026-0001" not in set(df["cve_id"])
    assert "CVE-2024-0001" in set(df["cve_id"])
    assert "CVE-2025-0001" in set(df["cve_id"])


def test_normalize_skips_malformed_dates():
    cat = _fixture_catalog()
    df = normalize_kev_catalog(cat, as_of_date=date(2026, 5, 31))
    assert "CVE-2025-9999" not in set(df["cve_id"])
    assert df.attrs["skipped_count"] >= 1


def test_normalize_due_date_after_as_of_retained():
    cat = {
        "vulnerabilities": [
            {
                "cveID": "CVE-2025-0010",
                "dateAdded": "2025-05-20",
                "dueDate": "2026-12-31",  # after as_of
                "requiredAction": "...",
            }
        ]
    }
    df = normalize_kev_catalog(cat, as_of_date=date(2025, 5, 31))
    assert len(df) == 1
    assert df["kev_due_date"].iloc[0] == date(2026, 12, 31)


def test_normalize_handles_list_payload():
    df = normalize_kev_catalog(
        [
            {
                "cveID": "CVE-2025-1",
                "dateAdded": "2025-01-01",
                "dueDate": "2025-02-01",
                "requiredAction": "...",
            }
        ],
        as_of_date=date(2025, 5, 1),
    )
    assert len(df) == 1


def test_normalize_rejects_unsupported_type():
    with pytest.raises(TypeError):
        normalize_kev_catalog("not a list or dict", as_of_date=date(2025, 5, 1))


def test_normalize_attrs_reconstruction_flag():
    df = normalize_kev_catalog(_fixture_catalog(), as_of_date=date(2026, 5, 31))
    assert df.attrs["reconstructed_asof_from_current_catalog"] is True


# -----------------------------------------------------------------------
# KEVClient with snapshot persistence
# -----------------------------------------------------------------------


def test_kev_client_get_asof(tmp_path: Path):
    client = KEVClient(cache_root=tmp_path)
    df = client.normalize(_fixture_catalog(), date(2026, 5, 31))
    client.write_snapshot(date(2026, 5, 31), df, fetched_at=datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC))
    out = client.get_kev_asof(date(2026, 5, 31))
    assert "CVE-2024-0001" in set(out["cve_id"])
    assert "CVE-2026-0001" not in set(out["cve_id"])


def test_kev_client_added_in_window(tmp_path: Path):
    client = KEVClient(cache_root=tmp_path)
    df = client.normalize(_fixture_catalog(), date(2026, 5, 31))
    client.write_snapshot(date(2026, 5, 31), df, fetched_at=datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC))
    # Window ends at a date for which we have written a snapshot.
    added = client.kev_added_in_window(date(2025, 1, 1), date(2026, 5, 31))
    assert "CVE-2025-0001" in set(added["cve_id"])
    assert "CVE-2024-0001" not in set(added["cve_id"])
    assert "CVE-2026-0001" not in set(added["cve_id"])  # future, excluded


def test_kev_window_rejects_inverted_dates(tmp_path: Path):
    client = KEVClient(cache_root=tmp_path)
    df = client.normalize(_fixture_catalog(), date(2026, 5, 31))
    client.write_snapshot(date(2026, 5, 31), df, fetched_at=datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC))
    with pytest.raises(ValueError):
        client.kev_added_in_window(date(2026, 1, 1), date(2025, 1, 1))


def test_kev_client_normalize_runs_no_future_check(tmp_path: Path):
    # Sanity: client.normalize should never produce a future date_added.
    client = KEVClient(cache_root=tmp_path)
    df = client.normalize(_fixture_catalog(), date(2026, 5, 31))
    # No rows should have kev_date_added > 2026-05-31.
    for d in df["kev_date_added"]:
        assert d <= date(2026, 5, 31)
