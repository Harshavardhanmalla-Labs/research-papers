"""Tests for paper2_runtime.batch_loader — F8 planned batches."""

from __future__ import annotations

from paper2_runtime.batch_loader import (
    assert_batch_cell_counts_match_f6,
    load_planned_batches,
    pilot_batches,
    primary_batches,
    validate_batches,
)
from paper2_runtime.cell_loader import load_cells


def test_loads_pilot_and_primary_batches():
    plan = load_planned_batches()
    assert len(plan.pilot) == 4
    assert len(plan.primary) == 4
    assert len(pilot_batches(plan)) == 4
    assert len(primary_batches(plan)) == 4


def test_validate_batches_passes_against_F6():
    plan = load_planned_batches()
    cells = load_cells()
    validate_batches(plan, cells)
    assert_batch_cell_counts_match_f6(plan, cells)


def test_planned_seed_run_totals_match_F8_locks():
    plan = load_planned_batches()
    pilot_total = sum(b.planned_seed_runs for b in plan.pilot)
    primary_total = sum(b.planned_seed_runs for b in plan.primary)
    assert pilot_total == 288
    assert primary_total == 1440


def test_freeze_wrap_required_on_every_batch():
    plan = load_planned_batches()
    for b in plan.pilot + plan.primary:
        assert b.freeze_wrap_required


def test_no_duplicate_batch_ids():
    plan = load_planned_batches()
    ids = [b.batch_id for b in plan.pilot + plan.primary]
    assert len(ids) == len(set(ids))


def test_fallback_order_present():
    plan = load_planned_batches()
    ids = [item.get("id") for item in plan.fallback_order]
    # Expect F8-e first, F8-a last.
    assert ids[0] == "F8-e"
    assert ids[-1] == "F8-a"
