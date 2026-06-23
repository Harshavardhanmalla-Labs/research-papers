"""Temporal split tests."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from paper1.model.splits import (
    assign_split,
    filter_pairs_by_split,
    make_temporal_split,
    validate_split_gap,
)

START = date(2024, 6, 1)
END = date(2026, 5, 31)
H = 30


def test_split_windows_for_24_month_period():
    cfg = make_temporal_split(None, START, END, H, train_months=18)
    # 18 months after 2024-06-01 is 2025-12-01.
    assert cfg["train_end"] == date(2025, 12, 1)
    assert cfg["gap_end"] == date(2025, 12, 31)
    assert cfg["test_end"] == date(2026, 5, 1)
    assert cfg["data_window_end"] == END


def test_train_t0_assigned_train():
    cfg = make_temporal_split(None, START, END, H)
    assert assign_split(date(2024, 9, 1), cfg) == "train"
    assert assign_split(date(2025, 12, 1), cfg) == "train"  # boundary inclusive


def test_gap_t0_assigned_gap():
    cfg = make_temporal_split(None, START, END, H)
    assert assign_split(date(2025, 12, 15), cfg) == "gap"
    assert assign_split(date(2025, 12, 31), cfg) == "gap"  # boundary inclusive


def test_test_t0_assigned_test():
    cfg = make_temporal_split(None, START, END, H)
    assert assign_split(date(2026, 1, 1), cfg) == "test"
    assert assign_split(date(2026, 5, 1), cfg) == "test"  # boundary inclusive


def test_censored_near_window_end():
    cfg = make_temporal_split(None, START, END, H)
    assert assign_split(date(2026, 5, 20), cfg) == "censored"
    assert assign_split(date(2026, 5, 31), cfg) == "censored"


def test_gap_is_at_least_h_days():
    cfg = make_temporal_split(None, START, END, H)
    validate_split_gap(cfg, H)  # must not raise
    assert (cfg["gap_end"] - cfg["train_end"]).days == H


def test_invalid_data_window_raises():
    with pytest.raises(ValueError):
        make_temporal_split(None, END, START, H)  # end before start


def test_window_too_short_for_train_plus_gap_raises():
    # 18-month train + 30-day gap cannot fit into a 6-month window.
    with pytest.raises(ValueError):
        make_temporal_split(None, date(2025, 1, 1), date(2025, 7, 1), H, train_months=18)


def test_assign_split_before_start_raises():
    cfg = make_temporal_split(None, START, END, H)
    with pytest.raises(ValueError):
        assign_split(date(2024, 1, 1), cfg)


def test_counts_included_when_decision_times_supplied():
    times = [
        date(2024, 9, 1),   # train
        date(2025, 12, 15), # gap
        date(2026, 1, 1),   # test
        date(2026, 5, 25),  # censored
    ]
    cfg = make_temporal_split(times, START, END, H)
    assert cfg["counts"] == {"train": 1, "gap": 1, "test": 1, "censored": 1}


def test_no_train_test_overlap():
    cfg = make_temporal_split(None, START, END, H)
    # The last train day and the first test day are separated by >= H days.
    assert (cfg["test_start"] - cfg["train_end"]).days >= H


def test_filter_pairs_by_split():
    frame = pd.DataFrame(
        {
            "pair_id": ["a", "b", "c"],
            "split": ["train", "test", "train"],
        }
    )
    train = filter_pairs_by_split(frame, "train")
    assert set(train["pair_id"]) == {"a", "c"}


def test_filter_pairs_by_split_missing_column_raises():
    frame = pd.DataFrame({"pair_id": ["a"]})
    with pytest.raises(ValueError):
        filter_pairs_by_split(frame, "train")
