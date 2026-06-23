"""Tests for paper2_runtime.run_planner — F6 + F8 read-only summariser."""

from __future__ import annotations

import pytest

from paper2_runtime.run_planner import (
    FALLBACK_DECISION,
    PROCEED_DECISION,
    assert_primary_blocked_until_pilot_passes,
    build_pilot_plan,
    build_primary_plan,
    estimate_seed_runs,
    summarize_plan,
)


def test_pilot_plan_has_four_batches():
    assert len(build_pilot_plan()) == 4


def test_primary_plan_has_four_batches():
    assert len(build_primary_plan()) == 4


def test_primary_blocked_without_pilot_pass():
    with pytest.raises(RuntimeError):
        assert_primary_blocked_until_pilot_passes(None)
    with pytest.raises(RuntimeError):
        assert_primary_blocked_until_pilot_passes(FALLBACK_DECISION)


def test_primary_allowed_only_on_proceed_decision():
    # No exception is the success path.
    assert_primary_blocked_until_pilot_passes(PROCEED_DECISION)


def test_seed_run_totals_match_F8():
    sr = estimate_seed_runs()
    assert sr["pilot_seed_runs"] == 288
    assert sr["primary_seed_runs"] == 1440
    assert sr["combined_seed_runs"] == 1728


def test_summary_has_required_keys():
    summary = summarize_plan()
    for k in (
        "chosen_plan", "compute_envelope", "f6_planned_runnable_cells",
        "pilot_batches", "primary_batches", "pilot_seed_runs",
        "primary_seed_runs", "combined_seed_runs", "fallback_order",
    ):
        assert k in summary, k
    assert summary["f6_planned_runnable_cells"] == 48
    # Fallback order ids loaded.
    assert summary["fallback_order"][0] == "F8-e"
    assert summary["fallback_order"][-1] == "F8-a"
