"""Frame assembly tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import pytest

from paper1.audit.schema import (
    Host,
    InstalledSoftware,
    PatchState,
    Vulnerability,
    VulnerabilityHostPair,
)
from paper1.model.frames import (
    PAIR_FRAME_COLUMNS,
    attach_labels,
    attach_split,
    hosts_to_frame,
    pairs_to_frame,
    validate_pair_frame,
    vulnerabilities_to_frame,
)


def _utc() -> datetime:
    return datetime(2026, 5, 31, 12, 0, 0, tzinfo=UTC)


def _pairs(n: int = 3) -> list[VulnerabilityHostPair]:
    return [
        VulnerabilityHostPair(
            pair_id=f"H-{i}:CVE-2024-000{i}",
            cve_id=f"CVE-2024-000{i}",
            host_id=f"H-{i}",
            match_method="cpe_exact",
            match_confidence=1.0,
            pair_status="open",
            first_observed=datetime(2025, 6, 1, tzinfo=UTC),
        )
        for i in range(n)
    ]


def test_pairs_to_frame_column_order():
    frame = pairs_to_frame(_pairs())
    assert list(frame.columns) == PAIR_FRAME_COLUMNS
    assert len(frame) == 3


def test_pairs_to_frame_preserves_order():
    pairs = _pairs()
    frame = pairs_to_frame(pairs)
    assert frame["pair_id"].tolist() == [p.pair_id for p in pairs]


def test_pairs_to_frame_empty():
    frame = pairs_to_frame([])
    assert list(frame.columns) == PAIR_FRAME_COLUMNS
    assert frame.empty


def test_vulnerabilities_to_frame():
    v = Vulnerability(
        cve_id="CVE-2024-0001",
        cpe_matches=["cpe:2.3:a:v:p:1.0:*:*:*:*:*:*:*"],
        cvss_v4_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
        cvss_v4_base=9.3,
        cvss_version_used="v4",
        disclosure_date=date(2025, 1, 1),
        feed_fetch_timestamp=_utc(),
    )
    frame = vulnerabilities_to_frame([v])
    assert frame["cve_id"].iloc[0] == "CVE-2024-0001"
    assert frame["cvss_v4_base"].iloc[0] == 9.3


def test_hosts_to_frame():
    h = Host(
        host_id="H-1",
        os_family="linux",
        os_version="Ubuntu 24.04 LTS",
        role="member_server",
        network_zone="internal",
        identity_tier="tier_1",
        installed_software=[
            InstalledSoftware(
                cpe="cpe:2.3:a:openssl:openssl:3.0.13:*:*:*:*:*:*:*",
                product="openssl",
                vendor="openssl",
                version="3.0.13",
            )
        ],
        patch_state=PatchState(kbs_installed=[], last_scan=_utc(), scan_source="t"),
        last_seen_per_source={"inventory": _utc()},
        group_id="G-1",
    )
    frame = hosts_to_frame([h])
    assert frame["host_id"].iloc[0] == "H-1"
    assert frame["n_installed_software"].iloc[0] == 1


def test_attach_labels_adds_columns():
    frame = pairs_to_frame(_pairs())
    labels = pd.Series([True, False, True], dtype="boolean")
    dates = pd.Series([date(2025, 6, 5), pd.NA, date(2025, 6, 7)], dtype="object")
    out = attach_labels(frame, labels, dates, label_name="A")
    assert "label_A" in out.columns
    assert "label_A_date" in out.columns
    assert out["label_A"].tolist() == [True, False, True]


def test_attach_labels_length_mismatch_raises():
    frame = pairs_to_frame(_pairs())
    with pytest.raises(ValueError):
        attach_labels(frame, pd.Series([True], dtype="boolean"))


def test_attach_split_adds_column():
    frame = pairs_to_frame(_pairs())
    out = attach_split(frame, ["train", "test", "train"])
    assert out["split"].tolist() == ["train", "test", "train"]


def test_attach_split_length_mismatch_raises():
    frame = pairs_to_frame(_pairs())
    with pytest.raises(ValueError):
        attach_split(frame, ["train"])


def test_validate_pair_frame_ok():
    frame = pairs_to_frame(_pairs())
    validate_pair_frame(frame)


def test_validate_pair_frame_missing_column_raises():
    frame = pairs_to_frame(_pairs()).drop(columns=["cve_id"])
    with pytest.raises(ValueError):
        validate_pair_frame(frame)


def test_validate_pair_frame_duplicate_pair_id_raises():
    pairs = _pairs(2)
    frame = pairs_to_frame(pairs)
    dup = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        validate_pair_frame(dup)


def test_validate_pair_frame_allows_duplicates_when_flagged():
    pairs = _pairs(2)
    frame = pairs_to_frame(pairs)
    dup = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    validate_pair_frame(dup, allow_duplicates=True)
