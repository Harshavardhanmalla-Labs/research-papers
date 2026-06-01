"""NVD JSON 2.0 client.

Live fetching is implemented via stdlib ``urllib.request`` against the
official NVD CVE 2.0 API; tests must not invoke ``fetch``. Normalization
produces a pandas DataFrame whose rows are compatible with the
``Vulnerability`` schema (Phase 1) modulo provenance fields.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from paper1.feeds.base import BaseFeedClient
from paper1.feeds.cve_client import CPEParseError, extract_affected_ranges, parse_cpe23
from paper1.feeds.provenance import attach_provenance
from paper1.utils.logging import get_logger
from paper1.utils.time import ensure_utc, utc_now

__all__ = [
    "NVD_API_URL",
    "NVDClient",
    "extract_cpe_matches",
    "extract_cvss",
    "normalize_nvd_record",
]


NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
SOURCE_NAME = "nvd"

_log = get_logger("paper1.feeds.nvd")


_CWE_RE = re.compile(r"^CWE-\d+$")


def extract_cvss(record: dict[str, Any]) -> dict[str, Any]:
    """Extract CVSS v4 and v3.1 vectors/base scores from an NVD CVE record.

    Prefers v4 when present; falls back to v3.1. Returns a dict with the
    five fields used by the ``Vulnerability`` schema.
    """
    metrics = (record.get("metrics") or {})
    v4 = (metrics.get("cvssMetricV40") or [])
    v31 = (metrics.get("cvssMetricV31") or [])

    cvss_v4_vector = None
    cvss_v4_base = None
    if v4:
        data = (v4[0] or {}).get("cvssData") or {}
        cvss_v4_vector = data.get("vectorString")
        base = data.get("baseScore")
        cvss_v4_base = float(base) if base is not None else None

    cvss_v31_vector = None
    cvss_v31_base = None
    if v31:
        data = (v31[0] or {}).get("cvssData") or {}
        cvss_v31_vector = data.get("vectorString")
        base = data.get("baseScore")
        cvss_v31_base = float(base) if base is not None else None

    if cvss_v4_vector is not None and cvss_v4_base is not None:
        cvss_version_used = "v4"
    elif cvss_v31_vector is not None and cvss_v31_base is not None:
        cvss_version_used = "v31"
    else:
        cvss_version_used = None

    return {
        "cvss_v4_vector": cvss_v4_vector,
        "cvss_v4_base": cvss_v4_base,
        "cvss_v31_vector": cvss_v31_vector,
        "cvss_v31_base": cvss_v31_base,
        "cvss_version_used": cvss_version_used,
    }


def extract_cpe_matches(record: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (cpe_matches, warnings).

    ``cpe_matches`` is the deduplicated canonical CPE list from every
    ``cpeMatch`` node under ``configurations``. ``warnings`` lists any
    unparseable CPE strings encountered.
    """
    matches: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for config in record.get("configurations", []) or []:
        for node in config.get("nodes", []) or []:
            for vr in extract_affected_ranges(node):
                cpe = vr.cpe
                if not cpe:
                    continue
                try:
                    parsed = parse_cpe23(cpe)
                except CPEParseError as exc:
                    warnings.append(f"{cpe}: {exc}")
                    continue
                canon = parsed.as_canonical()
                if canon not in seen:
                    seen.add(canon)
                    matches.append(canon)
    return matches, warnings


def _parse_published(value: str | None) -> date | None:
    if not value:
        return None
    # NVD publishes ISO-8601 timestamps with millisecond precision.
    try:
        # Trim to seconds for safety, allow timezone or naive.
        v = value.replace("Z", "+00:00") if value.endswith("Z") else value
        dt = datetime.fromisoformat(v)
        return dt.date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def normalize_nvd_record(record: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """Normalize a single CVE record to a dict + collected warnings.

    Returns ``(row, warnings)``. ``row`` is None when the record is
    unusable (missing CVE id, missing CVSS, etc.); warnings always
    collect descriptive notes.
    """
    cve = record.get("cve") if "cve" in record else record
    warnings: list[str] = []

    cve_id = (cve or {}).get("id")
    if not cve_id or not re.match(r"^CVE-\d{4}-\d{4,}$", cve_id):
        warnings.append(f"missing or invalid cve id: {cve_id!r}")
        return None, warnings

    cvss = extract_cvss(cve)
    if cvss["cvss_version_used"] is None:
        warnings.append(f"{cve_id}: no CVSS v4 or v3.1 metrics; record skipped")
        return None, warnings

    cpe_matches, cpe_warnings = extract_cpe_matches(cve)
    warnings.extend(f"{cve_id}: {w}" for w in cpe_warnings)
    if not cpe_matches:
        warnings.append(f"{cve_id}: no CPE matches; emitted with empty cpe list")

    cwe_ids: list[str] = []
    for weakness in cve.get("weaknesses", []) or []:
        for desc in weakness.get("description", []) or []:
            v = desc.get("value")
            if v and _CWE_RE.match(v):
                cwe_ids.append(v)
    cwe_ids = sorted(set(cwe_ids))

    disclosure_date = _parse_published(cve.get("published"))
    if disclosure_date is None:
        warnings.append(f"{cve_id}: unparseable published date {cve.get('published')!r}")
        return None, warnings

    refs = [
        r.get("url")
        for r in (cve.get("references") or [])
        if r.get("url")
    ]

    row = {
        "cve_id": cve_id,
        "cwe_ids": cwe_ids,
        "cpe_matches": cpe_matches,
        **cvss,
        "disclosure_date": disclosure_date,
        "vendor_advisory_refs": refs,
        "mitigations_listed": [],
        "preconditions": {},
        "normalization_warnings": [],
    }
    return row, warnings


class NVDClient(BaseFeedClient):
    """NVD CVE 2.0 client."""

    source_name = SOURCE_NAME

    def fetch(self, as_of_date: date) -> dict[str, Any]:
        """Fetch all CVEs published on or before `as_of_date` via the NVD API.

        Not called during unit tests. Implementations of bulk historical
        fetches typically paginate over `resultsPerPage` and `startIndex`;
        this method delegates pagination to the caller (script) so unit
        tests can stub out `fetch` without coupling to network behavior.
        Raises NotImplementedError to discourage accidental live use from
        within library code.
        """
        raise NotImplementedError(
            "NVDClient.fetch is intentionally not implemented in library code. "
            "Use scripts/fetch_nvd.py for live ingestion."
        )

    def normalize(self, raw: Any, as_of_date: date) -> pd.DataFrame:
        """Normalize an NVD JSON 2.0 response into a canonical DataFrame.

        Filters out CVEs whose `published` date is strictly after
        `as_of_date`; collects per-record warnings on the resulting frame
        in an `extra` attribute on the DataFrame.
        """
        if isinstance(raw, list):
            entries = raw
        elif isinstance(raw, dict):
            entries = raw.get("vulnerabilities") or raw.get("CVE_Items") or []
        else:
            raise TypeError(f"Unsupported raw NVD payload type: {type(raw).__name__}")

        rows: list[dict[str, Any]] = []
        all_warnings: list[str] = []
        for entry in entries:
            row, warnings = normalize_nvd_record(entry)
            all_warnings.extend(warnings)
            if row is None:
                continue
            if row["disclosure_date"] > as_of_date:
                continue
            rows.append(row)

        fetched_at = utc_now()
        for r in rows:
            r.update(
                attach_provenance(
                    {},
                    source_name=self.source_name,
                    fetched_at=fetched_at,
                    source_url=NVD_API_URL,
                )
            )

        df = pd.DataFrame.from_records(rows) if rows else pd.DataFrame()
        if not df.empty:
            self.verify_no_future(df, as_of_date, "disclosure_date")
        df.attrs["normalization_warnings"] = all_warnings
        return df

    def get_cves_disclosed_asof(self, as_of_date: date) -> pd.DataFrame:
        """Convenience wrapper around `get_asof` for NVD."""
        df = self.get_asof(as_of_date)
        if not df.empty:
            self.verify_no_future(df, as_of_date, "disclosure_date")
        return df


# ---------------------------------------------------------------------------
# Live-fetch helper used by scripts (kept out of library normalization path)
# ---------------------------------------------------------------------------


def fetch_nvd_window(
    start_date: date,
    end_date: date,
    api_key: str | None = None,
    *,
    results_per_page: int = 2000,
    user_agent: str = "paper1/0.1 (research)",
    timeout_seconds: int = 60,
) -> list[dict[str, Any]]:
    """Paginate the NVD CVE 2.0 API across a publication-date window.

    Used by `scripts/fetch_nvd.py`. Not invoked in unit tests.
    """
    if end_date < start_date:
        raise ValueError("end_date must be >= start_date")
    start_iso = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC).isoformat()
    end_iso = datetime.combine(end_date, datetime.max.time(), tzinfo=UTC).isoformat()
    out: list[dict[str, Any]] = []
    start_index = 0
    while True:
        params = {
            "pubStartDate": start_iso,
            "pubEndDate": end_iso,
            "resultsPerPage": str(results_per_page),
            "startIndex": str(start_index),
        }
        url = f"{NVD_API_URL}?{urlencode(params)}"
        headers = {"User-Agent": user_agent}
        if api_key:
            headers["apiKey"] = api_key
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout_seconds) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        vulns = payload.get("vulnerabilities", [])
        out.extend(vulns)
        total = payload.get("totalResults", len(vulns))
        start_index += len(vulns)
        _log.info(
            "nvd page fetched",
            extra={
                "start_index": start_index,
                "page_size": len(vulns),
                "total_results": total,
            },
        )
        if start_index >= total or not vulns:
            break
    return out


# Silence "fetched_at unused" import lints when only get_asof is used.
_ = ensure_utc
