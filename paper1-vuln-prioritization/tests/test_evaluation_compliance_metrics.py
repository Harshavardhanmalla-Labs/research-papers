"""Compliance metric tests."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from paper1.evaluation.compliance_metrics import (
    capacity_efficiency,
    kev_deadline_breach_rate,
    kev_remediation_latency,
)

# -----------------------------------------------------------------------
# KEV deadline breach
# -----------------------------------------------------------------------


def test_kev_breach_all_on_time_zero():
    kev = pd.DataFrame({"pair_id": ["p1", "p2"], "kev_due_date": [date(2025, 6, 10), date(2025, 6, 12)]})
    sched = pd.DataFrame({"pair_id": ["p1", "p2"], "remediated_at": [date(2025, 6, 9), date(2025, 6, 11)]})
    assert kev_deadline_breach_rate(sched, kev) == 0.0


def test_kev_breach_one_late_one_on_time():
    kev = pd.DataFrame({"pair_id": ["p1", "p2"], "kev_due_date": [date(2025, 6, 10), date(2025, 6, 12)]})
    sched = pd.DataFrame({"pair_id": ["p1", "p2"], "remediated_at": [date(2025, 6, 9), date(2025, 6, 20)]})
    assert kev_deadline_breach_rate(sched, kev) == pytest.approx(0.5)


def test_kev_breach_missing_remediation_is_breach():
    kev = pd.DataFrame({"pair_id": ["p1", "p2"], "kev_due_date": [date(2025, 6, 10), date(2025, 6, 12)]})
    sched = pd.DataFrame({"pair_id": ["p1"], "remediated_at": [date(2025, 6, 9)]})  # p2 missing
    assert kev_deadline_breach_rate(sched, kev) == pytest.approx(0.5)


def test_kev_breach_no_kev_pairs_nan():
    kev = pd.DataFrame({"pair_id": [], "kev_due_date": []})
    sched = pd.DataFrame({"pair_id": [], "remediated_at": []})
    assert np.isnan(kev_deadline_breach_rate(sched, kev))


def test_kev_breach_excludes_missing_due_date():
    kev = pd.DataFrame({"pair_id": ["p1", "p2"], "kev_due_date": [date(2025, 6, 10), pd.NA]})
    sched = pd.DataFrame({"pair_id": ["p1"], "remediated_at": [date(2025, 6, 9)]})
    # only p1 counts; on time -> 0
    assert kev_deadline_breach_rate(sched, kev) == 0.0


# -----------------------------------------------------------------------
# KEV remediation latency
# -----------------------------------------------------------------------


def test_kev_latency_median_p95():
    kev = pd.DataFrame({
        "pair_id": ["p1", "p2", "p3"],
        "kev_date_added": [date(2025, 6, 1), date(2025, 6, 1), date(2025, 6, 1)],
    })
    sched = pd.DataFrame({
        "pair_id": ["p1", "p2", "p3"],
        "remediated_at": [date(2025, 6, 3), date(2025, 6, 6), date(2025, 6, 11)],
    })
    out = kev_remediation_latency(sched, kev)
    # latencies: 2, 5, 10
    assert out["count"] == 3
    assert out["median_days"] == pytest.approx(5.0)
    assert out["p95_days"] == pytest.approx(np.percentile([2, 5, 10], 95))


def test_kev_latency_criticality_filter():
    kev = pd.DataFrame({
        "pair_id": ["p1", "p2"],
        "kev_date_added": [date(2025, 6, 1), date(2025, 6, 1)],
    })
    sched = pd.DataFrame({
        "pair_id": ["p1", "p2"],
        "remediated_at": [date(2025, 6, 3), date(2025, 6, 20)],
    })
    crit = pd.DataFrame({"pair_id": ["p1", "p2"], "criticality_score": [0.9, 0.2]})
    out = kev_remediation_latency(sched, kev, criticality_frame=crit, criticality_threshold=0.7)
    # only p1 (crit 0.9) counts -> latency 2
    assert out["count"] == 1
    assert out["median_days"] == pytest.approx(2.0)


def test_kev_latency_empty_nan():
    kev = pd.DataFrame({"pair_id": ["p1"], "kev_date_added": [date(2025, 6, 1)]})
    sched = pd.DataFrame(columns=["pair_id", "remediated_at"])
    out = kev_remediation_latency(sched, kev)
    assert out["count"] == 0
    assert np.isnan(out["median_days"])


# -----------------------------------------------------------------------
# capacity efficiency
# -----------------------------------------------------------------------


def test_capacity_efficiency_toy():
    scheduled = pd.DataFrame({"pair_id": ["p1", "p2", "p3", "p4"]})
    labels = pd.DataFrame({
        "pair_id": ["p1", "p2", "p3", "p4"],
        "label": [True, False, True, pd.NA],
    })
    # non-censored scheduled: p1,p2,p3 -> 2 positives / 3 = 0.667
    assert capacity_efficiency(scheduled, labels) == pytest.approx(2 / 3)


def test_capacity_efficiency_no_labeled_nan():
    scheduled = pd.DataFrame({"pair_id": ["p1"]})
    labels = pd.DataFrame({"pair_id": ["p1"], "label": [pd.NA]})
    assert np.isnan(capacity_efficiency(scheduled, labels))
