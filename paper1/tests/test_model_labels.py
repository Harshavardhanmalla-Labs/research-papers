"""Label A / Label B construction tests."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from paper1.model.labels import (
    censor_mask,
    ensure_no_label_future_leakage,
    label_a,
    label_b,
    label_dates_a,
    label_dates_b,
    validate_event_dates,
)

T0 = date(2025, 6, 1)
H = 30
WINDOW_END = date(2026, 5, 31)


def _pairs_frame(cves: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"cve_id": cves, "pair_id": [f"H:{c}" for c in cves]})


def _kev(cve: str, d: date) -> pd.DataFrame:
    return pd.DataFrame({"cve_id": [cve], "kev_date_added": [d]})


def _poc(cve: str, d: date) -> pd.DataFrame:
    return pd.DataFrame({"cve_id": [cve], "poc_first_seen": [d]})


def _empty_poc() -> pd.DataFrame:
    return pd.DataFrame({"cve_id": [], "poc_first_seen": []})


def _empty_kev() -> pd.DataFrame:
    return pd.DataFrame({"cve_id": [], "kev_date_added": []})


# -----------------------------------------------------------------------
# KEV vs PoC behavior
# -----------------------------------------------------------------------


def test_kev_only_positive_in_a_negative_in_b():
    pairs = _pairs_frame(["CVE-2024-0001"])
    kev = _kev("CVE-2024-0001", date(2025, 6, 15))
    a = label_a(pairs, kev, _empty_poc(), T0, H, WINDOW_END)
    b = label_b(pairs, _empty_poc(), T0, H, WINDOW_END)
    assert bool(a.iloc[0]) is True
    assert bool(b.iloc[0]) is False


def test_poc_only_positive_in_both():
    pairs = _pairs_frame(["CVE-2024-0002"])
    poc = _poc("CVE-2024-0002", date(2025, 6, 10))
    a = label_a(pairs, _empty_kev(), poc, T0, H, WINDOW_END)
    b = label_b(pairs, poc, T0, H, WINDOW_END)
    assert bool(a.iloc[0]) is True
    assert bool(b.iloc[0]) is True


def test_label_a_date_is_earliest_qualifying_event():
    pairs = _pairs_frame(["CVE-2024-0003"])
    kev = _kev("CVE-2024-0003", date(2025, 6, 20))
    poc = _poc("CVE-2024-0003", date(2025, 6, 5))
    dates = label_dates_a(pairs, kev, poc, T0, H, WINDOW_END)
    assert dates.iloc[0] == date(2025, 6, 5)  # PoC earlier than KEV


def test_label_b_date():
    pairs = _pairs_frame(["CVE-2024-0004"])
    poc = _poc("CVE-2024-0004", date(2025, 6, 7))
    dates = label_dates_b(pairs, poc, T0, H, WINDOW_END)
    assert dates.iloc[0] == date(2025, 6, 7)


# -----------------------------------------------------------------------
# boundary timing
# -----------------------------------------------------------------------


def test_event_exactly_t0_does_not_count():
    pairs = _pairs_frame(["CVE-2024-0005"])
    kev = _kev("CVE-2024-0005", T0)  # exactly t0
    a = label_a(pairs, kev, _empty_poc(), T0, H, WINDOW_END)
    assert bool(a.iloc[0]) is False


def test_event_exactly_t0_plus_h_counts():
    pairs = _pairs_frame(["CVE-2024-0006"])
    kev = _kev("CVE-2024-0006", date(2025, 7, 1))  # t0 + 30
    a = label_a(pairs, kev, _empty_poc(), T0, H, WINDOW_END)
    assert bool(a.iloc[0]) is True


def test_event_after_horizon_does_not_count():
    pairs = _pairs_frame(["CVE-2024-0007"])
    kev = _kev("CVE-2024-0007", date(2025, 7, 2))  # t0 + 31
    a = label_a(pairs, kev, _empty_poc(), T0, H, WINDOW_END)
    assert bool(a.iloc[0]) is False


# -----------------------------------------------------------------------
# censoring
# -----------------------------------------------------------------------


def test_censoring_returns_na_when_horizon_exceeds_window_end():
    pairs = _pairs_frame(["CVE-2024-0008"])
    kev = _kev("CVE-2024-0008", date(2026, 5, 20))
    # t0 near the end: t0 + H > window_end
    t0 = date(2026, 5, 20)
    a = label_a(pairs, kev, _empty_poc(), t0, H, WINDOW_END)
    assert a.isna().all()
    mask = censor_mask(pairs, t0, H, WINDOW_END)
    assert bool(mask.iloc[0]) is True


def test_label_dates_censored_na():
    pairs = _pairs_frame(["CVE-2024-0008"])
    poc = _poc("CVE-2024-0008", date(2026, 5, 25))
    dates = label_dates_a(pairs, _empty_kev(), poc, date(2026, 5, 20), H, WINDOW_END)
    assert dates.isna().all()


# -----------------------------------------------------------------------
# ordering / alignment
# -----------------------------------------------------------------------


def test_output_preserves_pair_order():
    pairs = _pairs_frame(["CVE-A-0001", "CVE-B-0002", "CVE-C-0003"])
    kev = _kev("CVE-B-0002", date(2025, 6, 10))
    a = label_a(pairs, kev, _empty_poc(), T0, H, WINDOW_END)
    assert list(a) == [False, True, False]


def test_label_accepts_list_of_pairs():
    from datetime import UTC, datetime

    from paper1.audit.schema import VulnerabilityHostPair

    pair = VulnerabilityHostPair(
        pair_id="H:CVE-2024-0010",
        cve_id="CVE-2024-0010",
        host_id="H",
        match_method="cpe_exact",
        match_confidence=1.0,
        pair_status="open",
        first_observed=datetime(2025, 6, 1, tzinfo=UTC),
    )
    kev = _kev("CVE-2024-0010", date(2025, 6, 15))
    a = label_a([pair], kev, _empty_poc(), T0, H, WINDOW_END)
    assert bool(a.iloc[0]) is True


# -----------------------------------------------------------------------
# malformed dates / leakage guard
# -----------------------------------------------------------------------


def test_malformed_event_date_raises():
    bad = pd.DataFrame({"cve_id": ["CVE-2024-0011"], "kev_date_added": ["not-a-date"]})
    with pytest.raises(ValueError):
        validate_event_dates(bad, "kev_date_added")


def test_label_a_malformed_date_raises():
    pairs = _pairs_frame(["CVE-2024-0011"])
    bad = pd.DataFrame({"cve_id": ["CVE-2024-0011"], "kev_date_added": ["bogus"]})
    with pytest.raises(ValueError):
        label_a(pairs, bad, _empty_poc(), T0, H, WINDOW_END)


def test_no_label_future_leakage_guard_catches_future_feature():
    feature_history = pd.DataFrame(
        {
            "cve_id": ["CVE-2024-0012", "CVE-2024-0013"],
            "published_at": [date(2025, 5, 1), date(2025, 7, 1)],  # second postdates t0
        }
    )
    with pytest.raises(ValueError):
        ensure_no_label_future_leakage(feature_history, "published_at", T0)


def test_no_label_future_leakage_passes_when_clean():
    feature_history = pd.DataFrame(
        {"cve_id": ["CVE-2024-0014"], "published_at": [date(2025, 5, 1)]}
    )
    ensure_no_label_future_leakage(feature_history, "published_at", T0)


def test_empty_poc_history_is_no_positives_not_failure():
    pairs = _pairs_frame(["CVE-2024-0015"])
    b = label_b(pairs, _empty_poc(), T0, H, WINDOW_END)
    assert bool(b.iloc[0]) is False
