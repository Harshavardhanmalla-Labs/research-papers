"""EHD / EEHDA metric tests."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from paper1.evaluation.eehda import (
    compute_ehd,
    compute_pair_ehd,
    eehda_relative,
    eehda_report,
    fraction_of_oracle,
)

END = date(2025, 12, 31)


# -----------------------------------------------------------------------
# compute_pair_ehd
# -----------------------------------------------------------------------


def test_remediated_before_label_is_zero():
    ehd = compute_pair_ehd("p", date(2025, 6, 1), date(2025, 6, 10), END)
    assert ehd == 0.0


def test_remediated_same_day_as_label_is_zero():
    ehd = compute_pair_ehd("p", date(2025, 6, 10), date(2025, 6, 10), END)
    assert ehd == 0.0


def test_remediated_five_days_after_label():
    ehd = compute_pair_ehd("p", date(2025, 6, 15), date(2025, 6, 10), END)
    assert ehd == pytest.approx(5.0)


def test_never_remediated_uses_evaluation_end():
    ehd = compute_pair_ehd("p", None, date(2025, 12, 21), END)
    assert ehd == pytest.approx(10.0)  # Dec 21 -> Dec 31


# -----------------------------------------------------------------------
# compute_ehd over labels + schedule history
# -----------------------------------------------------------------------


def _labels(rows):
    return pd.DataFrame(rows, columns=["pair_id", "label", "label_date"])


def test_compute_ehd_positive_only():
    labels = _labels([
        ("p1", True, date(2025, 6, 10)),
        ("p2", False, date(2025, 6, 10)),   # non-positive contributes 0
        ("p3", pd.NA, date(2025, 6, 10)),   # censored excluded
    ])
    sched = pd.DataFrame({
        "pair_id": ["p1"],
        "strategy_name": ["s"],
        "effective_remediation_time": [date(2025, 6, 15)],
    })
    # p1 remediated 5 days late; p2/p3 contribute 0.
    assert compute_ehd(sched, labels, END) == pytest.approx(5.0)


def test_compute_ehd_unscheduled_positive_uses_end():
    labels = _labels([("p1", True, date(2025, 12, 21))])
    sched = pd.DataFrame(columns=["pair_id", "strategy_name", "effective_remediation_time"])
    # p1 never remediated -> Dec 21..Dec 31 = 10 days
    assert compute_ehd(sched, labels, END) == pytest.approx(10.0)


def test_compute_ehd_uses_remediated_at_column():
    labels = _labels([("p1", True, date(2025, 6, 10))])
    sched = pd.DataFrame({"pair_id": ["p1"], "remediated_at": [date(2025, 6, 13)]})
    assert compute_ehd(sched, labels, END, remediated_col="remediated_at") == pytest.approx(3.0)


# -----------------------------------------------------------------------
# relative / oracle
# -----------------------------------------------------------------------


def test_eehda_relative_hand_computed():
    # baseline (random) = 100, strategy = 40 -> (100-40)/100 = 0.6
    assert eehda_relative(40.0, 100.0) == pytest.approx(0.6)


def test_eehda_relative_zero_baseline_nan():
    assert np.isnan(eehda_relative(0.0, 0.0))


def test_fraction_of_oracle_hand_computed():
    # random=100, oracle=20, strategy=40 -> (100-40)/(100-20) = 60/80 = 0.75
    assert fraction_of_oracle(40.0, 100.0, 20.0) == pytest.approx(0.75)


def test_fraction_of_oracle_zero_denominator_nan():
    assert np.isnan(fraction_of_oracle(40.0, 50.0, 50.0))


def test_eehda_report_columns_and_values():
    ehd = {"random": 100.0, "epss_only": 60.0, "oracle": 20.0, "proposed_full": 40.0}
    report = eehda_report(ehd)
    assert list(report.columns) == [
        "strategy", "absolute", "relative_to_random", "relative_to_epss", "fraction_of_oracle"
    ]
    prop = report[report["strategy"] == "proposed_full"].iloc[0]
    assert prop["absolute"] == pytest.approx(40.0)
    assert prop["relative_to_random"] == pytest.approx(0.6)
    assert prop["relative_to_epss"] == pytest.approx((60 - 40) / 60)
    assert prop["fraction_of_oracle"] == pytest.approx(0.75)
