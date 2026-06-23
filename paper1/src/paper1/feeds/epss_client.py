"""FIRST EPSS historical client.

Two formats are supported:

1. The FIRST EPSS API at ``https://api.first.org/data/v1/epss`` with the
   ``date`` parameter for point-in-time queries.
2. The daily CSV.gz snapshots mirrored at
   ``https://epss.empiricalsecurity.com/epss_scores-YYYY-MM-DD.csv.gz``.

Historical EPSS data begins **2021-04-14**. Earlier dates are refused
with a clear error. The model version active on a given date is
captured as ``epss_version``; ``infer_epss_model_version`` provides a
best-effort mapping where known boundaries are recorded.
"""

from __future__ import annotations

import csv
import gzip
import re
from datetime import date, datetime
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd

from paper1.feeds.base import BaseFeedClient
from paper1.feeds.provenance import attach_provenance
from paper1.utils.time import ensure_utc, utc_now

__all__ = [
    "EPSS_CSV_URL_TEMPLATE",
    "EPSS_HISTORY_BEGIN",
    "EPSSClient",
    "epss_snapshot_url",
    "fetch_epss_csv",
    "infer_epss_model_version",
    "normalize_epss_csv",
]


EPSS_HISTORY_BEGIN = date(2021, 4, 14)
EPSS_CSV_URL_TEMPLATE = (
    "https://epss.empiricalsecurity.com/epss_scores-{date}.csv.gz"
)
SOURCE_NAME = "epss"

# Boundaries are documented best-effort. Treat as [VERIFY] for camera-ready;
# refine with FIRST's published release notes when available.
_EPSS_MODEL_BOUNDARIES = (
    # (effective_date, version_label)
    (date(2021, 4, 14), "v1"),
    (date(2022, 2, 4), "v2"),
    (date(2023, 3, 7), "v3"),
    (date(2025, 3, 17), "v4"),
)


def epss_snapshot_url(d: date) -> str:
    """URL of the daily EPSS CSV.gz snapshot for date `d`."""
    if d < EPSS_HISTORY_BEGIN:
        raise ValueError(
            f"EPSS historical data begins {EPSS_HISTORY_BEGIN.isoformat()}; "
            f"requested {d.isoformat()}"
        )
    return EPSS_CSV_URL_TEMPLATE.format(date=d.isoformat())


def infer_epss_model_version(d: date) -> str:
    """Best-effort label for the EPSS model active on date `d`.

    The boundaries are based on public FIRST release notes and may need
    revision at camera-ready time; mark as [VERIFY] in the paper.
    """
    if d < EPSS_HISTORY_BEGIN:
        raise ValueError(
            f"EPSS historical data begins {EPSS_HISTORY_BEGIN.isoformat()}"
        )
    version = "v1"
    for boundary, label in _EPSS_MODEL_BOUNDARIES:
        if d >= boundary:
            version = label
    return version


_HEADER_KV_RE = re.compile(r"#?\s*([a-zA-Z_]+)\s*:\s*([^,]+)")


def _parse_csv_header_line(line: str) -> dict[str, str]:
    """Parse the optional `#key:value,key:value` header line in EPSS CSV."""
    out: dict[str, str] = {}
    for match in _HEADER_KV_RE.finditer(line):
        out[match.group(1).strip()] = match.group(2).strip()
    return out


def normalize_epss_csv(
    csv_bytes_or_text: bytes | str,
    as_of_date: date,
    *,
    cve_ids: set[str] | None = None,
    fetched_at: datetime | None = None,
) -> pd.DataFrame:
    """Parse EPSS CSV content into the canonical DataFrame.

    The EPSS daily CSV begins with an optional `#model_version:...,score_date:...`
    header line, followed by a `cve,epss,percentile` header row.
    """
    if isinstance(csv_bytes_or_text, bytes):
        text = csv_bytes_or_text.decode("utf-8")
    else:
        text = csv_bytes_or_text
    # Strip BOM if present.
    if text.startswith("﻿"):
        text = text.lstrip("﻿")

    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty EPSS CSV")

    header_kv: dict[str, str] = {}
    if lines[0].startswith("#"):
        header_kv = _parse_csv_header_line(lines[0])
        lines = lines[1:]

    if not lines:
        raise ValueError("EPSS CSV contains header but no rows")

    reader = csv.DictReader(lines)
    if reader.fieldnames is None:
        raise ValueError("EPSS CSV missing column headers")
    expected_cols = {"cve", "epss", "percentile"}
    if not expected_cols.issubset(set(reader.fieldnames)):
        raise ValueError(
            f"EPSS CSV column headers {reader.fieldnames!r} missing one of {expected_cols}"
        )

    model_version = header_kv.get("model_version") or infer_epss_model_version(as_of_date)
    fetched_at = fetched_at or utc_now()
    ensure_utc(fetched_at)

    rows: list[dict[str, Any]] = []
    for row in reader:
        cve = (row.get("cve") or "").strip()
        if not cve:
            continue
        if cve_ids is not None and cve not in cve_ids:
            continue
        try:
            score = float(row["epss"])
            pct = float(row["percentile"])
        except (TypeError, ValueError):
            continue
        if not (0.0 <= score <= 1.0):
            raise ValueError(f"{cve}: epss score {score} outside [0, 1]")
        if not (0.0 <= pct <= 1.0):
            raise ValueError(f"{cve}: percentile {pct} outside [0, 1]")
        record = {
            "cve_id": cve,
            "epss_score": score,
            "epss_percentile": pct,
            "as_of_date": as_of_date,
            "epss_version": model_version,
        }
        rows.append(
            attach_provenance(
                record,
                source_name=SOURCE_NAME,
                fetched_at=fetched_at,
                source_url=epss_snapshot_url(as_of_date),
                source_version=model_version,
            )
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "cve_id",
                "epss_score",
                "epss_percentile",
                "as_of_date",
                "epss_version",
                "source_name",
                "fetched_at",
                "source_url",
                "source_version",
            ]
        )
    return pd.DataFrame.from_records(rows)


def fetch_epss_csv(
    as_of_date: date,
    *,
    user_agent: str = "paper1/0.1 (research)",
    timeout_seconds: int = 60,
) -> bytes:
    """Download the EPSS CSV.gz for `as_of_date` and return the decompressed bytes.

    Not called during unit tests. Network behavior is exercised only by
    `scripts/fetch_epss.py`.
    """
    url = epss_snapshot_url(as_of_date)
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=timeout_seconds) as resp:
        compressed = resp.read()
    return gzip.decompress(compressed)


class EPSSClient(BaseFeedClient):
    """FIRST EPSS historical client."""

    source_name = SOURCE_NAME

    def fetch(self, as_of_date: date) -> bytes:
        """Live-fetch the EPSS CSV. Not invoked in unit tests."""
        return fetch_epss_csv(as_of_date)

    def normalize(self, raw: Any, as_of_date: date) -> pd.DataFrame:
        if isinstance(raw, (bytes, str)):
            df = normalize_epss_csv(raw, as_of_date)
        elif isinstance(raw, pd.DataFrame):
            df = raw
        else:
            raise TypeError(f"Unsupported raw EPSS payload type: {type(raw).__name__}")
        if not df.empty:
            self.verify_no_future(df, as_of_date, "as_of_date")
        return df

    def get_asof(self, as_of_date: date, cve_ids: list[str] | None = None) -> pd.DataFrame:
        """Load the EPSS snapshot for `as_of_date`, optionally filtered to `cve_ids`."""
        if as_of_date < EPSS_HISTORY_BEGIN:
            raise ValueError(
                f"EPSS historical data begins {EPSS_HISTORY_BEGIN.isoformat()}"
            )
        df = super().get_asof(as_of_date)
        if cve_ids is not None and not df.empty:
            allowed = set(cve_ids)
            df = df[df["cve_id"].isin(allowed)].reset_index(drop=True)
        if not df.empty:
            self.verify_no_future(df, as_of_date, "as_of_date")
        # Hard guarantee: as_of_date column must equal the requested date.
        # After JSON snapshot roundtrip values may arrive as ISO strings.
        if not df.empty:
            from paper1.utils.time import parse_date

            def _coerce(v: Any) -> date:
                if isinstance(v, datetime):
                    return v.date()
                if isinstance(v, date):
                    return v
                return parse_date(v)

            mismatched = df.loc[df["as_of_date"].apply(_coerce) != as_of_date]
            if not mismatched.empty:
                raise ValueError(
                    f"EPSS snapshot contains {len(mismatched)} rows whose "
                    f"as_of_date != {as_of_date}"
                )
        return df

    def load_epss_snapshot(self, as_of_date: date) -> pd.DataFrame:
        """Direct snapshot loader (no cve_ids filter)."""
        df, _meta = self.load_snapshot(as_of_date)
        return df
