"""ExploitDB / public-PoC client with license gate.

ExploitDB's redistribution terms are unresolved as of this writing. To
avoid accidental redistribution, **live fetching is disabled unless**
the environment variable ``PAPER1_ENABLE_POC_FETCH=true`` is set.

Library-side normalization works on any locally provided ExploitDB CSV
content (e.g., a downloaded ``files_exploits.csv``) so unit tests can
exercise the parser via fixtures without invoking the network.
"""

from __future__ import annotations

import csv
import io
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd

from paper1.feeds.base import BaseFeedClient
from paper1.feeds.provenance import attach_provenance
from paper1.utils.time import ensure_utc, parse_date, utc_now

__all__ = [
    "POC_ENV_FLAG",
    "POCClient",
    "PoCLicenseGateError",
    "extract_cves_from_exploitdb_row",
    "fetch_poc_index",
    "normalize_exploitdb_csv",
]


POC_ENV_FLAG = "PAPER1_ENABLE_POC_FETCH"
SOURCE_NAME = "poc"

EXPLOITDB_DEFAULT_URL = (
    "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv"
)


class PoCLicenseGateError(RuntimeError):
    """Raised when a live PoC fetch is attempted without the license gate set."""


_CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def extract_cves_from_exploitdb_row(row: dict[str, Any]) -> list[str]:
    """Extract every CVE-NNNN-NNNN[+] identifier referenced in a row.

    ExploitDB rows commonly carry a ``codes`` column with multiple
    semicolon-separated identifiers (CVE, OSVDB, etc.). This function
    scans every value in the row for matching CVE identifiers and
    returns the deduplicated upper-cased list.
    """
    seen: list[str] = []
    seen_set: set[str] = set()
    for value in row.values():
        if value is None:
            continue
        if not isinstance(value, str):
            value = str(value)
        for match in _CVE_PATTERN.finditer(value):
            cve = match.group(0).upper()
            if cve not in seen_set:
                seen_set.add(cve)
                seen.append(cve)
    return seen


def _row_first_seen_date(row: dict[str, Any]) -> date | None:
    """Pick the best first-seen date from an ExploitDB row.

    ExploitDB rows typically include a ``date_published`` column. Fall
    back to ``date`` or ``date_added`` if present.
    """
    for key in ("date_published", "date", "date_added"):
        v = row.get(key)
        if not v:
            continue
        try:
            return parse_date(v)
        except Exception:
            continue
    return None


def normalize_exploitdb_csv(
    text_or_path: str | bytes | Path,
    as_of_date: date,
    *,
    cve_ids: set[str] | None = None,
    fetched_at: datetime | None = None,
    source_url: str | None = None,
) -> pd.DataFrame:
    """Parse an ExploitDB ``files_exploits.csv`` file into the canonical frame.

    Output columns: ``cve_id, poc_observed, poc_first_seen, source_name,
    source_identifier, as_of_date, fetched_at, source_url``.

    The function emits **one row per (CVE, ExploitDB-id)** pair.
    Aggregation across multiple PoCs per CVE (e.g., earliest
    ``poc_first_seen``) is the caller's responsibility — kept separate so
    diagnostics remain visible.

    Rows with ``poc_first_seen > as_of_date`` are dropped.
    """
    if isinstance(text_or_path, Path):
        text = text_or_path.read_text(encoding="utf-8")
    elif isinstance(text_or_path, bytes):
        text = text_or_path.decode("utf-8")
    else:
        text = text_or_path

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("ExploitDB CSV missing column headers")

    fetched_at = fetched_at or utc_now()
    ensure_utc(fetched_at)

    rows: list[dict[str, Any]] = []
    for row in reader:
        cves = extract_cves_from_exploitdb_row(row)
        if not cves:
            continue
        first_seen = _row_first_seen_date(row)
        if first_seen is None:
            continue
        if first_seen > as_of_date:
            continue
        edb_id = row.get("id") or row.get("EDB-ID") or ""
        for cve in cves:
            if cve_ids is not None and cve not in cve_ids:
                continue
            rec = {
                "cve_id": cve,
                "poc_observed": True,
                "poc_first_seen": first_seen,
                "as_of_date": as_of_date,
            }
            rows.append(
                attach_provenance(
                    rec,
                    source_name=SOURCE_NAME,
                    fetched_at=fetched_at,
                    source_url=source_url or EXPLOITDB_DEFAULT_URL,
                    source_identifier=f"EDB-{edb_id}" if edb_id else None,
                )
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "cve_id",
                "poc_observed",
                "poc_first_seen",
                "as_of_date",
                "source_name",
                "fetched_at",
                "source_url",
                "source_identifier",
            ]
        )
    return pd.DataFrame.from_records(rows)


def fetch_poc_index(
    *,
    user_agent: str = "paper1/0.1 (research)",
    timeout_seconds: int = 60,
    url: str = EXPLOITDB_DEFAULT_URL,
) -> bytes:
    """Live-fetch the ExploitDB index CSV. Gated by env var; not used in tests."""
    if os.environ.get(POC_ENV_FLAG, "").lower() != "true":
        raise PoCLicenseGateError(
            f"Live PoC fetch is disabled. Set {POC_ENV_FLAG}=true to enable, "
            "after confirming ExploitDB license terms for your use case."
        )
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=timeout_seconds) as resp:
        return resp.read()


class POCClient(BaseFeedClient):
    """ExploitDB / public-PoC client."""

    source_name = SOURCE_NAME

    def fetch(self, as_of_date: date) -> bytes:
        return fetch_poc_index()

    def normalize(self, raw: Any, as_of_date: date) -> pd.DataFrame:
        if isinstance(raw, (bytes, str, Path)):
            df = normalize_exploitdb_csv(raw, as_of_date)
        elif isinstance(raw, pd.DataFrame):
            df = raw
        else:
            raise TypeError(f"Unsupported raw PoC payload: {type(raw).__name__}")
        if not df.empty:
            self.verify_no_future(df, as_of_date, "poc_first_seen")
        return df

    def get_poc_first_seen(
        self,
        cve_ids: list[str] | None,
        as_of_date: date,
    ) -> pd.DataFrame:
        """Return rows whose `poc_first_seen <= as_of_date`, optionally filtered.

        Reduces multiple PoCs per CVE to the earliest ``poc_first_seen``.
        """
        df = self.get_asof(as_of_date)
        if df.empty:
            return df
        if cve_ids is not None:
            allowed = set(cve_ids)
            df = df[df["cve_id"].isin(allowed)]
        if df.empty:
            return df
        # Aggregate to one row per cve_id, earliest poc_first_seen.
        df = df.sort_values(["cve_id", "poc_first_seen"], kind="mergesort")
        df = df.drop_duplicates(subset=["cve_id"], keep="first").reset_index(drop=True)
        self.verify_no_future(df, as_of_date, "poc_first_seen")
        return df
