"""CISA KEV catalog client.

The KEV catalog is published as a single cumulative JSON document. The
client implements *reconstructed* historical as-of queries:

    Given the latest catalog at fetch time, ``get_kev_asof(d)`` returns
    every entry whose ``dateAdded <= d``.

The ``reconstructed_asof_from_current_catalog`` flag is set in the
returned DataFrame's ``attrs`` so callers know the data was not derived
from a point-in-time snapshot of the catalog itself. Where genuine
point-in-time KEV snapshots are bundled with the artifact, those take
precedence.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd

from paper1.feeds.base import BaseFeedClient
from paper1.feeds.provenance import attach_provenance
from paper1.utils.logging import get_logger
from paper1.utils.time import ensure_utc, parse_date, utc_now

__all__ = ["KEV_CATALOG_URL", "KEVClient", "fetch_kev_catalog", "normalize_kev_catalog"]


KEV_CATALOG_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
)
SOURCE_NAME = "kev"

_log = get_logger("paper1.feeds.kev")


def fetch_kev_catalog(
    *,
    user_agent: str = "paper1/0.1 (research)",
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Download the current KEV catalog. Not invoked in unit tests."""
    req = Request(KEV_CATALOG_URL, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=timeout_seconds) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _safe_parse_date(v: Any) -> date | None:
    if v in (None, "", "N/A"):
        return None
    try:
        return parse_date(v)
    except Exception:
        return None


def normalize_kev_catalog(
    raw: dict[str, Any] | list[dict[str, Any]],
    as_of_date: date,
    *,
    fetched_at: datetime | None = None,
) -> pd.DataFrame:
    """Normalize a KEV catalog payload to a canonical DataFrame.

    Excludes entries whose ``dateAdded`` is strictly after ``as_of_date``.
    Entries with malformed dateAdded raise a warning and are skipped.
    """
    if isinstance(raw, dict):
        entries = raw.get("vulnerabilities") or []
        catalog_version = raw.get("catalogVersion")
    elif isinstance(raw, list):
        entries = raw
        catalog_version = None
    else:
        raise TypeError(f"Unsupported KEV payload type: {type(raw).__name__}")

    fetched_at = fetched_at or utc_now()
    ensure_utc(fetched_at)

    rows: list[dict[str, Any]] = []
    skipped = 0
    for entry in entries:
        cve_id = entry.get("cveID") or entry.get("cve_id")
        if not cve_id:
            skipped += 1
            continue
        date_added = _safe_parse_date(entry.get("dateAdded") or entry.get("date_added"))
        if date_added is None:
            _log.warning("kev: malformed dateAdded", extra={"cve_id": cve_id})
            skipped += 1
            continue
        if date_added > as_of_date:
            continue
        due_date = _safe_parse_date(entry.get("dueDate") or entry.get("due_date"))
        rec = {
            "cve_id": cve_id,
            "kev_status": True,
            "kev_date_added": date_added,
            "kev_due_date": due_date,
            "kev_required_action": entry.get("requiredAction") or entry.get("required_action"),
            "as_of_date": as_of_date,
        }
        rows.append(
            attach_provenance(
                rec,
                source_name=SOURCE_NAME,
                fetched_at=fetched_at,
                source_url=KEV_CATALOG_URL,
                source_version=catalog_version,
            )
        )

    df = (
        pd.DataFrame.from_records(rows)
        if rows
        else pd.DataFrame(
            columns=[
                "cve_id",
                "kev_status",
                "kev_date_added",
                "kev_due_date",
                "kev_required_action",
                "as_of_date",
                "source_name",
                "fetched_at",
                "source_url",
                "source_version",
            ]
        )
    )
    df.attrs["reconstructed_asof_from_current_catalog"] = True
    df.attrs["skipped_count"] = skipped
    return df


class KEVClient(BaseFeedClient):
    """CISA KEV catalog client."""

    source_name = SOURCE_NAME

    def fetch(self, as_of_date: date) -> dict[str, Any]:
        return fetch_kev_catalog()

    def normalize(self, raw: Any, as_of_date: date) -> pd.DataFrame:
        df = normalize_kev_catalog(raw, as_of_date)
        if not df.empty:
            self.verify_no_future(df, as_of_date, "kev_date_added")
            # due_date may legitimately exceed as_of_date — do not check.
        return df

    def get_kev_asof(self, as_of_date: date) -> pd.DataFrame:
        """Load the KEV snapshot for `as_of_date` and reapply the no-future check."""
        df = self.get_asof(as_of_date)
        if not df.empty:
            self.verify_no_future(df, as_of_date, "kev_date_added")
        return df

    def kev_added_in_window(
        self,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Return KEV entries whose dateAdded falls in `[start_date, end_date]`.

        Uses the snapshot for `end_date` as the source (which contains
        every entry through that date).
        """
        if end_date < start_date:
            raise ValueError("end_date must be >= start_date")
        df = self.get_kev_asof(end_date)
        if df.empty:
            return df
        col = df["kev_date_added"].apply(
            lambda v: v.date() if isinstance(v, datetime) else (v if isinstance(v, date) else parse_date(v))
        )
        mask = (col >= start_date) & (col <= end_date)
        return df.loc[mask].reset_index(drop=True)
