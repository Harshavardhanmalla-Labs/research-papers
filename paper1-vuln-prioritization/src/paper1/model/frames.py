"""DataFrame assembly helpers for pairs, vulnerabilities, hosts, labels."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from paper1.audit.schema import Host, Vulnerability, VulnerabilityHostPair

__all__ = [
    "PAIR_FRAME_COLUMNS",
    "attach_labels",
    "attach_split",
    "hosts_to_frame",
    "pairs_to_frame",
    "validate_pair_frame",
    "vulnerabilities_to_frame",
]


PAIR_FRAME_COLUMNS = [
    "pair_id",
    "cve_id",
    "host_id",
    "match_method",
    "match_confidence",
    "pair_status",
    "first_observed",
    "pair_origin_feeds",
]

_REQUIRED_PAIR_COLUMNS = {
    "pair_id",
    "cve_id",
    "host_id",
    "match_method",
    "match_confidence",
    "pair_status",
    "first_observed",
}


def pairs_to_frame(pairs: list[VulnerabilityHostPair]) -> pd.DataFrame:
    """Convert pairs to a DataFrame with stable column order."""
    if not pairs:
        return pd.DataFrame(columns=PAIR_FRAME_COLUMNS)
    rows: list[dict[str, Any]] = []
    for p in pairs:
        rows.append(
            {
                "pair_id": p.pair_id,
                "cve_id": p.cve_id,
                "host_id": p.host_id,
                "match_method": p.match_method,
                "match_confidence": p.match_confidence,
                "pair_status": p.pair_status,
                "first_observed": p.first_observed,
                "pair_origin_feeds": list(p.pair_origin_feeds),
            }
        )
    return pd.DataFrame(rows, columns=PAIR_FRAME_COLUMNS)


def vulnerabilities_to_frame(vulns: list[Vulnerability]) -> pd.DataFrame:
    cols = [
        "cve_id",
        "cvss_version_used",
        "cvss_v4_base",
        "cvss_v31_base",
        "disclosure_date",
        "cpe_matches",
        "cwe_ids",
    ]
    if not vulns:
        return pd.DataFrame(columns=cols)
    rows = [
        {
            "cve_id": v.cve_id,
            "cvss_version_used": v.cvss_version_used,
            "cvss_v4_base": v.cvss_v4_base,
            "cvss_v31_base": v.cvss_v31_base,
            "disclosure_date": v.disclosure_date,
            "cpe_matches": list(v.cpe_matches),
            "cwe_ids": list(v.cwe_ids),
        }
        for v in vulns
    ]
    return pd.DataFrame(rows, columns=cols)


def hosts_to_frame(hosts: list[Host]) -> pd.DataFrame:
    cols = [
        "host_id",
        "os_family",
        "os_version",
        "role",
        "network_zone",
        "identity_tier",
        "data_sensitivity_proxy",
        "group_id",
        "n_installed_software",
    ]
    if not hosts:
        return pd.DataFrame(columns=cols)
    rows = [
        {
            "host_id": h.host_id,
            "os_family": h.os_family,
            "os_version": h.os_version,
            "role": h.role,
            "network_zone": h.network_zone,
            "identity_tier": h.identity_tier,
            "data_sensitivity_proxy": h.data_sensitivity_proxy,
            "group_id": h.group_id,
            "n_installed_software": len(h.installed_software),
        }
        for h in hosts
    ]
    return pd.DataFrame(rows, columns=cols)


def validate_pair_frame(pair_frame: pd.DataFrame, *, allow_duplicates: bool = False) -> None:
    """Validate required columns and pair_id uniqueness."""
    missing = _REQUIRED_PAIR_COLUMNS - set(pair_frame.columns)
    if missing:
        raise ValueError(f"pair_frame missing required columns: {sorted(missing)}")
    if not allow_duplicates:
        dupes = pair_frame["pair_id"][pair_frame["pair_id"].duplicated()]
        if len(dupes) > 0:
            raise ValueError(f"duplicate pair_id values: {sorted(set(dupes))[:5]}")


def attach_labels(
    pair_frame: pd.DataFrame,
    labels: pd.Series,
    label_dates: pd.Series | None = None,
    label_name: str = "A",
) -> pd.DataFrame:
    """Return a copy of pair_frame with label_{name} (+ optional date) columns."""
    if len(labels) != len(pair_frame):
        raise ValueError(
            f"labels length {len(labels)} != pair_frame length {len(pair_frame)}"
        )
    out = pair_frame.copy()
    label_col = f"label_{label_name}"
    out[label_col] = labels.to_numpy()
    if label_dates is not None:
        if len(label_dates) != len(pair_frame):
            raise ValueError("label_dates length mismatch")
        out[f"label_{label_name}_date"] = label_dates.to_numpy()
    return out


def attach_split(
    pair_frame: pd.DataFrame,
    split_assignments: Sequence[str] | pd.Series,
) -> pd.DataFrame:
    """Return a copy of pair_frame with a 'split' column."""
    if len(split_assignments) != len(pair_frame):
        raise ValueError("split_assignments length mismatch")
    out = pair_frame.copy()
    if isinstance(split_assignments, pd.Series):
        out["split"] = split_assignments.to_numpy()
    else:
        out["split"] = list(split_assignments)
    return out
