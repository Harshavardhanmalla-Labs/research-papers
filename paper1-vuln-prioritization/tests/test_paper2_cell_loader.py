"""Tests for paper2_runtime.cell_loader — F6 cell enumeration."""

from __future__ import annotations

from paper2_runtime.cell_loader import (
    assert_no_duplicate_runnable_cells,
    deferred_cells,
    group_cells_by_table_group,
    load_cells,
    planned_cells,
    reused_cells,
    validate_cells,
)


def test_loads_and_validates_cells():
    cells = load_cells()
    validate_cells(cells)
    assert len(cells) == 66, "primary 12 + capacity 20 + blackout 12 + ablation 14 + deferred 8 = 66"


def test_cell_counts_match_F6_locks():
    cells = load_cells()
    assert len(planned_cells(cells)) == 48
    assert len(reused_cells(cells)) == 10
    assert len(deferred_cells(cells)) == 8


def test_no_duplicate_runnable_cells():
    cells = load_cells()
    assert_no_duplicate_runnable_cells(cells)


def test_deferred_cells_excluded_from_planned():
    cells = load_cells()
    p = planned_cells(cells)
    d = deferred_cells(cells)
    p_ids = {c.cell_id for c in p}
    d_ids = {c.cell_id for c in d}
    assert p_ids.isdisjoint(d_ids)


def test_group_by_table_group_matches_F6_summary():
    cells = load_cells()
    groups = group_cells_by_table_group(cells)
    # Planned counts per group must match F6 §9.
    planned_by_group = {g: [c for c in cs if c.run_status == "planned"]
                        for g, cs in groups.items()}
    assert len(planned_by_group["primary"]) == 12
    assert len(planned_by_group["capacity_sensitivity"]) == 15
    assert len(planned_by_group["blackout_sensitivity"]) == 9
    assert len(planned_by_group["feature_ablation"]) == 12
