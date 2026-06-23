"""PoC / ExploitDB client tests — fixture-based, license gate enforced."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from paper1.feeds.poc_client import (
    POC_ENV_FLAG,
    POCClient,
    PoCLicenseGateError,
    extract_cves_from_exploitdb_row,
    fetch_poc_index,
    normalize_exploitdb_csv,
)

_SAMPLE_CSV = (
    "id,file,description,date_published,author,type,platform,port,codes\n"
    "100,exploits/x.py,Sample 1,2024-06-15,author,remote,linux,,CVE-2024-0001\n"
    "101,exploits/y.py,Sample 2,2025-05-20,author,local,windows,,CVE-2025-0001;CVE-2025-0002\n"
    "102,exploits/z.py,Sample 3,2026-08-01,author,webapps,multiple,,CVE-2026-0001\n"
    "103,exploits/q.py,No CVE,2025-01-01,author,remote,linux,,OSVDB-1234\n"
)


# -----------------------------------------------------------------------
# License gate
# -----------------------------------------------------------------------


def test_fetch_refused_without_env_flag(monkeypatch):
    monkeypatch.delenv(POC_ENV_FLAG, raising=False)
    with pytest.raises(PoCLicenseGateError):
        fetch_poc_index()


def test_fetch_refused_when_env_flag_is_false(monkeypatch):
    monkeypatch.setenv(POC_ENV_FLAG, "false")
    with pytest.raises(PoCLicenseGateError):
        fetch_poc_index()


def test_client_fetch_refused_without_env_flag(monkeypatch, tmp_path: Path):
    monkeypatch.delenv(POC_ENV_FLAG, raising=False)
    client = POCClient(cache_root=tmp_path)
    with pytest.raises(PoCLicenseGateError):
        client.fetch(date(2026, 5, 31))


# -----------------------------------------------------------------------
# Row-level CVE extraction
# -----------------------------------------------------------------------


def test_extract_cves_multiple_in_codes_field():
    row = {"codes": "CVE-2025-0001;CVE-2025-0002;OSVDB-9"}
    cves = extract_cves_from_exploitdb_row(row)
    assert cves == ["CVE-2025-0001", "CVE-2025-0002"]


def test_extract_cves_handles_no_cves():
    row = {"codes": "OSVDB-1234"}
    assert extract_cves_from_exploitdb_row(row) == []


def test_extract_cves_dedup():
    row = {
        "codes": "CVE-2025-0001;CVE-2025-0001",
        "description": "References CVE-2025-0001 again",
    }
    cves = extract_cves_from_exploitdb_row(row)
    assert cves == ["CVE-2025-0001"]


def test_extract_cves_uppercases():
    row = {"codes": "cve-2025-0001"}
    assert extract_cves_from_exploitdb_row(row) == ["CVE-2025-0001"]


# -----------------------------------------------------------------------
# CSV normalization
# -----------------------------------------------------------------------


def test_normalize_emits_row_per_cve():
    df = normalize_exploitdb_csv(_SAMPLE_CSV, as_of_date=date(2026, 5, 31))
    # CVE-2026-0001 excluded as future; CVE-2025-0001/-0002 from one EDB id.
    assert set(df["cve_id"]) == {"CVE-2024-0001", "CVE-2025-0001", "CVE-2025-0002"}
    # The row with multiple CVEs produces multiple rows.
    edb_101_rows = df[df["source_identifier"] == "EDB-101"]
    assert len(edb_101_rows) == 2


def test_normalize_excludes_future_first_seen():
    df = normalize_exploitdb_csv(_SAMPLE_CSV, as_of_date=date(2026, 5, 31))
    assert "CVE-2026-0001" not in set(df["cve_id"])


def test_normalize_cve_filter():
    df = normalize_exploitdb_csv(
        _SAMPLE_CSV,
        as_of_date=date(2026, 5, 31),
        cve_ids={"CVE-2025-0001"},
    )
    assert len(df) == 1
    assert df["cve_id"].iloc[0] == "CVE-2025-0001"


def test_normalize_provenance_attached():
    df = normalize_exploitdb_csv(_SAMPLE_CSV, as_of_date=date(2026, 5, 31))
    assert (df["source_name"] == "poc").all()
    assert df["poc_observed"].all()


def test_normalize_no_matching_rows_returns_empty_frame():
    df = normalize_exploitdb_csv(_SAMPLE_CSV, as_of_date=date(2020, 1, 1))
    assert df.empty
    assert "cve_id" in df.columns


def test_normalize_missing_headers_raises():
    with pytest.raises(ValueError):
        normalize_exploitdb_csv("", as_of_date=date(2026, 5, 31))


# -----------------------------------------------------------------------
# Client get_poc_first_seen
# -----------------------------------------------------------------------


def test_client_get_poc_first_seen_aggregates_to_earliest(tmp_path: Path):
    extra_csv = _SAMPLE_CSV + (
        "104,exploits/a.py,Older CVE-2025-0001,2025-03-01,author,remote,linux,,CVE-2025-0001\n"
    )
    client = POCClient(cache_root=tmp_path)
    df = normalize_exploitdb_csv(extra_csv, as_of_date=date(2026, 5, 31))
    client.write_snapshot(
        date(2026, 5, 31), df,
        fetched_at=datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC),
    )
    out = client.get_poc_first_seen(["CVE-2025-0001"], date(2026, 5, 31))
    assert len(out) == 1
    earliest = out["poc_first_seen"].iloc[0]
    # After JSON snapshot roundtrip the value may arrive as ISO string,
    # datetime, or date. Normalize before comparing.
    if isinstance(earliest, str):
        earliest = date.fromisoformat(earliest)
    elif isinstance(earliest, datetime):
        earliest = earliest.date()
    assert earliest == date(2025, 3, 1)


def test_client_get_poc_first_seen_no_filter_returns_all(tmp_path: Path):
    client = POCClient(cache_root=tmp_path)
    df = normalize_exploitdb_csv(_SAMPLE_CSV, as_of_date=date(2026, 5, 31))
    client.write_snapshot(
        date(2026, 5, 31), df,
        fetched_at=datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC),
    )
    out = client.get_poc_first_seen(None, date(2026, 5, 31))
    assert set(out["cve_id"]) == {"CVE-2024-0001", "CVE-2025-0001", "CVE-2025-0002"}
