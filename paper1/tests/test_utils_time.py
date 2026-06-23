"""UTC time and SimulationClock tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from paper1.utils.time import SimulationClock, ensure_utc, parse_date, utc_now


def test_utc_now_is_timezone_aware():
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_ensure_utc_rejects_naive_datetime():
    with pytest.raises(ValueError):
        ensure_utc(datetime(2026, 5, 26, 12, 0, 0))


def test_ensure_utc_accepts_utc_datetime():
    dt = datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)
    assert ensure_utc(dt) == dt


def test_ensure_utc_rejects_non_utc_offset():
    dt = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    with pytest.raises(ValueError):
        ensure_utc(dt)


def test_ensure_utc_rejects_non_datetime():
    with pytest.raises(TypeError):
        ensure_utc("2026-05-26T12:00:00Z")  # type: ignore[arg-type]


def test_parse_date_from_string():
    assert parse_date("2026-05-26") == date(2026, 5, 26)


def test_parse_date_passthrough():
    d = date(2026, 5, 26)
    assert parse_date(d) is d


def test_parse_date_rejects_datetime():
    with pytest.raises(TypeError):
        parse_date(datetime(2026, 5, 26))


def test_simulation_clock_advances_by_step():
    clock = SimulationClock(date(2026, 1, 1), date(2026, 6, 1), step_days=14)
    assert clock.current == date(2026, 1, 1)
    next_date = clock.advance()
    assert next_date == date(2026, 1, 15)
    assert clock.current == date(2026, 1, 15)


def test_simulation_clock_iteration_yields_all_dates():
    clock = SimulationClock(date(2026, 1, 1), date(2026, 1, 30), step_days=7)
    dates = list(clock)
    assert dates[0] == date(2026, 1, 1)
    assert dates[-1] == date(2026, 1, 29)
    # 7-day step: 1, 8, 15, 22, 29
    assert dates == [
        date(2026, 1, 1),
        date(2026, 1, 8),
        date(2026, 1, 15),
        date(2026, 1, 22),
        date(2026, 1, 29),
    ]


def test_simulation_clock_raises_after_end_date():
    clock = SimulationClock(date(2026, 1, 1), date(2026, 1, 10), step_days=7)
    clock.advance()  # 2026-01-08, valid
    with pytest.raises(StopIteration):
        clock.advance()  # next is 2026-01-15 which > end_date


def test_simulation_clock_rejects_end_before_start():
    with pytest.raises(ValueError):
        SimulationClock(date(2026, 6, 1), date(2026, 1, 1), step_days=7)


def test_simulation_clock_rejects_non_positive_step():
    with pytest.raises(ValueError):
        SimulationClock(date(2026, 1, 1), date(2026, 6, 1), step_days=0)
    with pytest.raises(ValueError):
        SimulationClock(date(2026, 1, 1), date(2026, 6, 1), step_days=-1)


def test_simulation_clock_rejects_datetime_for_dates():
    with pytest.raises(TypeError):
        SimulationClock(datetime(2026, 1, 1), date(2026, 6, 1), step_days=7)  # type: ignore[arg-type]
