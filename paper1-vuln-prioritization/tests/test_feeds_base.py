"""BaseFeedClient tests using a stub subclass (no network)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from paper1.feeds.base import BaseFeedClient, FutureDataError


class _StubClient(BaseFeedClient):
    source_name = "stub"

    def fetch(self, as_of_date: date) -> Any:
        return {"as_of": as_of_date.isoformat(), "records": []}

    def normalize(self, raw: Any, as_of_date: date) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"cve_id": "CVE-2025-1", "as_of_date": as_of_date, "value": 1.0},
                {"cve_id": "CVE-2025-2", "as_of_date": as_of_date, "value": 2.0},
            ]
        )


def test_class_must_set_source_name(tmp_path: Path):
    class _Missing(BaseFeedClient):
        def fetch(self, as_of_date):
            return None

        def normalize(self, raw, as_of_date):
            return pd.DataFrame()

    with pytest.raises(ValueError):
        _Missing(cache_root=tmp_path)


def test_snapshot_path_deterministic(tmp_path: Path):
    c = _StubClient(cache_root=tmp_path)
    p1 = c.snapshot_path(date(2026, 5, 26))
    p2 = c.snapshot_path(date(2026, 5, 26))
    assert p1 == p2
    assert p1.name == "stub_20260526.json"
    assert "stub" in str(p1)


def test_write_then_load_snapshot_roundtrip(tmp_path: Path):
    c = _StubClient(cache_root=tmp_path)
    df = c.normalize(None, date(2026, 5, 26))
    path = c.write_snapshot(
        date(2026, 5, 26),
        df,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
        source_version="stub-v1",
    )
    assert path.exists()
    loaded_df, meta = c.load_snapshot(date(2026, 5, 26))
    assert len(loaded_df) == 2
    assert meta["source_name"] == "stub"
    assert meta["source_version"] == "stub-v1"
    assert meta["as_of_date"] == date(2026, 5, 26)


def test_get_asof_returns_snapshot(tmp_path: Path):
    c = _StubClient(cache_root=tmp_path)
    df = c.normalize(None, date(2026, 5, 26))
    c.write_snapshot(date(2026, 5, 26), df, fetched_at=datetime.now(UTC))
    out = c.get_asof(date(2026, 5, 26))
    assert len(out) == 2


def test_get_asof_rejects_datetime(tmp_path: Path):
    c = _StubClient(cache_root=tmp_path)
    with pytest.raises(TypeError):
        c.get_asof(datetime(2026, 5, 26, 0, 0, 0, tzinfo=UTC))  # type: ignore[arg-type]


def test_verify_no_future_raises_on_future_date():
    df = pd.DataFrame(
        [
            {"id": 1, "d": date(2026, 5, 26)},
            {"id": 2, "d": date(2026, 6, 1)},
        ]
    )
    with pytest.raises(FutureDataError):
        BaseFeedClient.verify_no_future(df, date(2026, 5, 26), "d")


def test_verify_no_future_passes_when_no_future():
    df = pd.DataFrame(
        [
            {"id": 1, "d": date(2026, 5, 26)},
            {"id": 2, "d": date(2026, 5, 25)},
        ]
    )
    BaseFeedClient.verify_no_future(df, date(2026, 5, 26), "d")


def test_verify_no_future_handles_none_values():
    df = pd.DataFrame(
        [
            {"id": 1, "d": date(2026, 5, 26)},
            {"id": 2, "d": None},
        ]
    )
    BaseFeedClient.verify_no_future(df, date(2026, 5, 26), "d")


def test_verify_no_future_unparseable_raises():
    df = pd.DataFrame([{"id": 1, "d": "not-a-date"}])
    with pytest.raises(FutureDataError):
        BaseFeedClient.verify_no_future(df, date(2026, 5, 26), "d")


def test_write_snapshot_registers_manifest(tmp_path: Path):
    c = _StubClient(cache_root=tmp_path)
    df = c.normalize(None, date(2026, 5, 26))
    c.write_snapshot(date(2026, 5, 26), df, fetched_at=datetime.now(UTC))
    assert c.manifest_path.exists()
    from paper1.feeds.provenance import load_manifest

    manifest = load_manifest(c.manifest_path)
    assert any(
        e["source_name"] == "stub" and e["snapshot_date"] == "2026-05-26"
        for e in manifest["snapshots"]
    )
