"""Snapshot file IO and manifest tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from paper1.feeds.provenance import (
    load_manifest,
    snapshot_id,
    update_manifest_entry,
    verify_manifest,
    verify_snapshot_file,
)
from paper1.feeds.snapshots import (
    SNAPSHOT_SCHEMA_VERSION,
    load_snapshot,
    snapshot_path,
    write_snapshot,
)


def test_snapshot_path_format(tmp_path: Path):
    p = snapshot_path(tmp_path, "epss", date(2026, 5, 26))
    assert p.name == "epss_20260526.json"
    assert p.parent.name == "epss"


def test_snapshot_path_rejects_datetime(tmp_path: Path):
    with pytest.raises(TypeError):
        snapshot_path(tmp_path, "epss", datetime(2026, 5, 26, tzinfo=UTC))  # type: ignore[arg-type]


def test_snapshot_path_rejects_bad_source(tmp_path: Path):
    with pytest.raises(ValueError):
        snapshot_path(tmp_path, "bad/source", date(2026, 5, 26))


def test_write_and_load_snapshot_roundtrip(tmp_path: Path):
    df = pd.DataFrame(
        [
            {"cve_id": "CVE-2025-2", "x": 2.0},
            {"cve_id": "CVE-2025-1", "x": 1.0},
        ]
    )
    path = write_snapshot(
        tmp_path,
        "test",
        date(2026, 5, 26),
        df,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
        source_version="v1",
        extra={"note": "hello"},
    )
    assert path.exists()
    out, meta = load_snapshot(path)
    # Records were sorted by cve_id for hash stability.
    assert out["cve_id"].tolist() == ["CVE-2025-1", "CVE-2025-2"]
    assert meta["source_name"] == "test"
    assert meta["source_version"] == "v1"
    assert meta["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert meta["extra"] == {"note": "hello"}


def test_load_snapshot_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "nope.json")


def test_load_snapshot_record_count_mismatch_raises(tmp_path: Path):
    # Hand-build an inconsistent snapshot.
    from paper1.utils.io import atomic_write_json

    bad = {
        "source_name": "x",
        "as_of_date": "2026-05-26",
        "fetched_at": "2026-05-26T12:00:00Z",
        "source_version": None,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "record_count": 99,
        "extra": {},
        "records": [{"cve_id": "CVE-2025-1"}],
    }
    p = tmp_path / "x_20260526.json"
    atomic_write_json(p, bad)
    with pytest.raises(ValueError):
        load_snapshot(p)


def test_load_snapshot_wrong_schema_version_raises(tmp_path: Path):
    from paper1.utils.io import atomic_write_json

    bad = {
        "source_name": "x",
        "as_of_date": "2026-05-26",
        "fetched_at": "2026-05-26T12:00:00Z",
        "source_version": None,
        "schema_version": "999",
        "record_count": 0,
        "extra": {},
        "records": [],
    }
    p = tmp_path / "x_20260526.json"
    atomic_write_json(p, bad)
    with pytest.raises(ValueError):
        load_snapshot(p)


# -----------------------------------------------------------------------
# Manifest tests
# -----------------------------------------------------------------------


def test_snapshot_id_format():
    sid = snapshot_id("epss", date(2026, 5, 26))
    assert sid == "epss|2026-05-26"


def test_manifest_roundtrip(tmp_path: Path):
    mp = tmp_path / "MANIFEST.json"
    # Write a snapshot first so update_manifest_entry can hash a real file.
    df = pd.DataFrame([{"cve_id": "CVE-2025-1", "x": 1.0}])
    sp = write_snapshot(
        tmp_path,
        "epss",
        date(2026, 5, 26),
        df,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    update_manifest_entry(
        mp,
        source_name="epss",
        snapshot_date=date(2026, 5, 26),
        snapshot_file=sp,
        record_count=1,
        license_note="CC-BY (verify)",
    )
    m = load_manifest(mp)
    assert len(m["snapshots"]) == 1
    entry = m["snapshots"][0]
    assert entry["source_name"] == "epss"
    assert entry["snapshot_date"] == "2026-05-26"
    assert entry["record_count"] == 1
    assert len(entry["sha256"]) == 64


def test_manifest_dedup_on_update(tmp_path: Path):
    mp = tmp_path / "MANIFEST.json"
    df1 = pd.DataFrame([{"cve_id": "CVE-2025-1"}])
    sp = write_snapshot(
        tmp_path, "epss", date(2026, 5, 26), df1,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    update_manifest_entry(
        mp, source_name="epss", snapshot_date=date(2026, 5, 26),
        snapshot_file=sp, record_count=1,
    )
    # Overwrite with a different snapshot.
    df2 = pd.DataFrame([{"cve_id": "CVE-2025-1"}, {"cve_id": "CVE-2025-2"}])
    sp = write_snapshot(
        tmp_path, "epss", date(2026, 5, 26), df2,
        fetched_at=datetime(2026, 5, 26, 13, 0, 0, tzinfo=UTC),
    )
    update_manifest_entry(
        mp, source_name="epss", snapshot_date=date(2026, 5, 26),
        snapshot_file=sp, record_count=2,
    )
    m = load_manifest(mp)
    epss_entries = [e for e in m["snapshots"] if e["source_name"] == "epss"]
    assert len(epss_entries) == 1
    assert epss_entries[0]["record_count"] == 2


def test_verify_snapshot_file_detects_mutation(tmp_path: Path):
    df = pd.DataFrame([{"cve_id": "CVE-2025-1"}])
    sp = write_snapshot(
        tmp_path, "test", date(2026, 5, 26), df,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    from paper1.utils.io import compute_file_sha256

    original = compute_file_sha256(sp)
    assert verify_snapshot_file(sp, original)
    # Mutate file
    sp.write_text(sp.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not verify_snapshot_file(sp, original)


def test_verify_manifest_ok(tmp_path: Path):
    mp = tmp_path / "MANIFEST.json"
    df = pd.DataFrame([{"cve_id": "CVE-2025-1"}])
    sp = write_snapshot(
        tmp_path, "test", date(2026, 5, 26), df,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    update_manifest_entry(
        mp, source_name="test", snapshot_date=date(2026, 5, 26),
        snapshot_file=sp, record_count=1,
    )
    ok, issues = verify_manifest(mp)
    assert ok, issues


def test_verify_manifest_detects_mutation(tmp_path: Path):
    mp = tmp_path / "MANIFEST.json"
    df = pd.DataFrame([{"cve_id": "CVE-2025-1"}])
    sp = write_snapshot(
        tmp_path, "test", date(2026, 5, 26), df,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    update_manifest_entry(
        mp, source_name="test", snapshot_date=date(2026, 5, 26),
        snapshot_file=sp, record_count=1,
    )
    sp.write_text(sp.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    ok, issues = verify_manifest(mp)
    assert not ok
    assert any("SHA-256 mismatch" in i for i in issues)


def test_verify_manifest_missing_file(tmp_path: Path):
    mp = tmp_path / "MANIFEST.json"
    df = pd.DataFrame([{"cve_id": "CVE-2025-1"}])
    sp = write_snapshot(
        tmp_path, "test", date(2026, 5, 26), df,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    update_manifest_entry(
        mp, source_name="test", snapshot_date=date(2026, 5, 26),
        snapshot_file=sp, record_count=1,
    )
    sp.unlink()
    ok, issues = verify_manifest(mp)
    assert not ok
    assert any("file missing" in i for i in issues)


def test_verify_manifest_no_file(tmp_path: Path):
    ok, _ = verify_manifest(tmp_path / "missing.json")
    assert not ok
