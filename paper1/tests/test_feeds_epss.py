"""FIRST EPSS client tests — fixture-based, no network."""

from __future__ import annotations

import gzip
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from paper1.feeds.epss_client import (
    EPSSClient,
    epss_snapshot_url,
    infer_epss_model_version,
    normalize_epss_csv,
)

_SAMPLE_CSV = """#model_version:v2025.03.14,score_date:2026-05-26T00:00:00+0000
cve,epss,percentile
CVE-2025-0001,0.0046,0.10915
CVE-2025-0002,0.0237,0.49584
CVE-2025-0003,0.7300,0.99100
"""


def test_epss_snapshot_url_format():
    url = epss_snapshot_url(date(2026, 5, 26))
    assert url.endswith("epss_scores-2026-05-26.csv.gz")


def test_epss_snapshot_url_rejects_before_history_begin():
    with pytest.raises(ValueError):
        epss_snapshot_url(date(2020, 1, 1))


def test_infer_model_version_after_v4_boundary():
    v = infer_epss_model_version(date(2025, 3, 18))
    assert v == "v4"


def test_infer_model_version_before_v4_boundary():
    v = infer_epss_model_version(date(2024, 1, 1))
    assert v == "v3"


def test_infer_model_version_before_history_raises():
    with pytest.raises(ValueError):
        infer_epss_model_version(date(2020, 1, 1))


# -----------------------------------------------------------------------
# CSV parsing
# -----------------------------------------------------------------------


def test_normalize_csv_text():
    df = normalize_epss_csv(_SAMPLE_CSV, date(2026, 5, 26))
    assert len(df) == 3
    assert set(df["cve_id"]) == {"CVE-2025-0001", "CVE-2025-0002", "CVE-2025-0003"}
    assert (df["epss_score"] >= 0).all() and (df["epss_score"] <= 1).all()
    assert (df["epss_percentile"] >= 0).all() and (df["epss_percentile"] <= 1).all()
    # Provenance fields present.
    assert df["source_name"].iloc[0] == "epss"
    assert df["epss_version"].iloc[0] == "v2025.03.14"


def test_normalize_csv_gzipped_bytes():
    raw = gzip.compress(_SAMPLE_CSV.encode("utf-8"))
    decompressed = gzip.decompress(raw)
    df = normalize_epss_csv(decompressed, date(2026, 5, 26))
    assert len(df) == 3


def test_normalize_csv_cve_filter():
    df = normalize_epss_csv(
        _SAMPLE_CSV, date(2026, 5, 26), cve_ids={"CVE-2025-0002"}
    )
    assert len(df) == 1
    assert df["cve_id"].iloc[0] == "CVE-2025-0002"


def test_normalize_csv_rejects_out_of_range_score():
    bad = "cve,epss,percentile\nCVE-2025-1,1.5,0.5\n"
    with pytest.raises(ValueError):
        normalize_epss_csv(bad, date(2026, 5, 26))


def test_normalize_csv_rejects_out_of_range_percentile():
    bad = "cve,epss,percentile\nCVE-2025-1,0.5,2.0\n"
    with pytest.raises(ValueError):
        normalize_epss_csv(bad, date(2026, 5, 26))


def test_normalize_csv_missing_required_column():
    bad = "cve,epss\nCVE-2025-1,0.5\n"
    with pytest.raises(ValueError):
        normalize_epss_csv(bad, date(2026, 5, 26))


def test_normalize_csv_empty():
    with pytest.raises(ValueError):
        normalize_epss_csv("", date(2026, 5, 26))


def test_normalize_csv_header_only():
    with pytest.raises(ValueError):
        normalize_epss_csv(
            "#model_version:v2025.03.14,score_date:2026-05-26T00:00:00+0000\n",
            date(2026, 5, 26),
        )


def test_normalize_csv_no_header_kv_uses_inferred_version():
    text = "cve,epss,percentile\nCVE-2025-1,0.5,0.5\n"
    df = normalize_epss_csv(text, date(2026, 5, 26))
    # No #model_version header, fall back to inferred (>= 2025-03-17 → v4).
    assert df["epss_version"].iloc[0] == "v4"


# -----------------------------------------------------------------------
# EPSSClient
# -----------------------------------------------------------------------


def test_client_get_asof_round_trip(tmp_path: Path):
    client = EPSSClient(cache_root=tmp_path)
    as_of = date(2026, 5, 26)
    df = normalize_epss_csv(
        _SAMPLE_CSV,
        as_of,
        fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    client.write_snapshot(
        as_of, df, fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
        source_version="v2025.03.14",
    )
    out = client.get_asof(as_of)
    assert len(out) == 3


def test_client_get_asof_cve_filter(tmp_path: Path):
    client = EPSSClient(cache_root=tmp_path)
    as_of = date(2026, 5, 26)
    df = normalize_epss_csv(
        _SAMPLE_CSV, as_of, fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC),
    )
    client.write_snapshot(as_of, df, fetched_at=datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC))
    out = client.get_asof(as_of, cve_ids=["CVE-2025-0001"])
    assert len(out) == 1
    assert out["cve_id"].iloc[0] == "CVE-2025-0001"


def test_client_get_asof_before_history_raises(tmp_path: Path):
    client = EPSSClient(cache_root=tmp_path)
    with pytest.raises(ValueError):
        client.get_asof(date(2020, 1, 1))


def test_client_normalize_rejects_unsupported_type(tmp_path: Path):
    client = EPSSClient(cache_root=tmp_path)
    with pytest.raises(TypeError):
        client.normalize(123, date(2026, 5, 26))
