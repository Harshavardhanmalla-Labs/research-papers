"""Temporal train / gap / test split with an H-day leakage gap.

Windows (all bounds are dates):

    train     : [data_window_start, train_end]
    gap       : (train_end, train_end + H_days]
    test      : (train_end + H_days, data_window_end - H_days]
    censored  : t0 such that t0 + H_days > data_window_end

The gap guarantees that no test-window decision time can be within
``H_days`` of any training-window label horizon, preventing label
leakage across the boundary.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Literal

import pandas as pd

__all__ = [
    "assign_split",
    "filter_pairs_by_split",
    "make_temporal_split",
    "validate_split_gap",
]

SplitName = Literal["train", "gap", "test", "censored"]


def _to_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Expected date|datetime|str; got {type(value).__name__}")


def make_temporal_split(
    decision_times: list[date] | pd.Series | None,
    data_window_start: date | datetime | str,
    data_window_end: date | datetime | str,
    H_days: int,
    train_months: int = 18,
) -> dict[str, Any]:
    """Compute split window boundaries; optionally tally decision_times.

    Uses ``pandas.DateOffset(months=train_months)`` so the train window
    respects calendar month lengths (no 30-day approximation).
    """
    if H_days <= 0:
        raise ValueError("H_days must be positive")
    if train_months <= 0:
        raise ValueError("train_months must be positive")
    start = _to_date(data_window_start)
    end = _to_date(data_window_end)
    if end <= start:
        raise ValueError("data_window_end must be after data_window_start")

    train_end = (pd.Timestamp(start) + pd.DateOffset(months=train_months)).date()
    gap_end = train_end + timedelta(days=H_days)
    test_end = end - timedelta(days=H_days)

    if not (start < train_end < gap_end <= test_end <= end):
        raise ValueError(
            "invalid data window: require "
            f"start({start}) < train_end({train_end}) < gap_end({gap_end}) "
            f"<= test_end({test_end}) <= end({end}); adjust train_months/H_days"
        )

    config: dict[str, Any] = {
        "data_window_start": start,
        "train_end": train_end,
        "gap_end": gap_end,
        "test_start": gap_end,  # test is the half-open interval (gap_end, test_end]
        "test_end": test_end,
        "data_window_end": end,
        "H_days": H_days,
        "train_months": train_months,
    }

    if decision_times is not None:
        times = list(decision_times)
        counts = {"train": 0, "gap": 0, "test": 0, "censored": 0}
        for t in times:
            counts[assign_split(t, config)] += 1
        config["counts"] = counts

    return config


def assign_split(t0: date | datetime | str, split_config: dict[str, Any]) -> SplitName:
    """Assign a decision time to one of train / gap / test / censored."""
    t = _to_date(t0)
    start = split_config["data_window_start"]
    if t < start:
        raise ValueError(f"t0 {t} precedes data_window_start {start}")
    # Censored region sits at the tail: t0 + H > data_window_end.
    if t > split_config["test_end"]:
        return "censored"
    if t <= split_config["train_end"]:
        return "train"
    if t <= split_config["gap_end"]:
        return "gap"
    return "test"


def validate_split_gap(split_config: dict[str, Any], H_days: int) -> None:
    """Raise if the gap is shorter than H_days."""
    gap = (split_config["gap_end"] - split_config["train_end"]).days
    if gap < H_days:
        raise ValueError(f"split gap {gap}d is shorter than H_days {H_days}")


def filter_pairs_by_split(pair_frame: pd.DataFrame, split_name: str) -> pd.DataFrame:
    """Return rows of `pair_frame` whose 'split' column equals split_name."""
    if "split" not in pair_frame.columns:
        raise ValueError("pair_frame has no 'split' column; call attach_split first")
    return pair_frame[pair_frame["split"] == split_name].reset_index(drop=True)
