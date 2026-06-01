"""UTC time helpers and simulation clock.

All datetimes in `paper1` are UTC and timezone-aware. Naive datetimes are
rejected at schema-load time and at simulation entry points.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

__all__ = ["SimulationClock", "ensure_utc", "parse_date", "utc_now"]


def utc_now() -> datetime:
    """Current UTC datetime, timezone-aware."""
    return datetime.now(tz=UTC)


def ensure_utc(dt: datetime) -> datetime:
    """Return `dt` if it is timezone-aware and UTC; raise otherwise."""
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime; got {type(dt).__name__}")
    if dt.tzinfo is None:
        raise ValueError("Naive datetime not permitted; require timezone-aware UTC")
    offset = dt.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError(f"Datetime must be UTC; got offset {offset}")
    return dt


def parse_date(value: str | date) -> date:
    """Parse an ISO-8601 date or pass through a date instance.

    Accepts only the form YYYY-MM-DD when given a string; rejects datetime
    strings to keep date and datetime spaces strictly separated.
    """
    if isinstance(value, datetime):
        # A datetime is not a date for our purposes; force the caller to be
        # explicit (date(dt.year, dt.month, dt.day)).
        raise TypeError("Pass a date, not a datetime")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise TypeError(f"Cannot parse date from {type(value).__name__}")
    return date.fromisoformat(value)


class SimulationClock:
    """Monotonic clock for simulations.

    Advances by a fixed step in days. Refuses to step past `end_date`.
    Refuses to rewind. Used by the simulation loop so no code reads
    `datetime.now()` while a simulation is running.
    """

    def __init__(self, start_date: date, end_date: date, step_days: int):
        if not isinstance(start_date, date) or isinstance(start_date, datetime):
            raise TypeError("start_date must be a date (not datetime)")
        if not isinstance(end_date, date) or isinstance(end_date, datetime):
            raise TypeError("end_date must be a date (not datetime)")
        if end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        if step_days <= 0:
            raise ValueError("step_days must be positive")
        self._start = start_date
        self._end = end_date
        self._step = step_days
        self._current = start_date

    @property
    def current(self) -> date:
        return self._current

    @property
    def start(self) -> date:
        return self._start

    @property
    def end(self) -> date:
        return self._end

    @property
    def step_days(self) -> int:
        return self._step

    def advance(self) -> date:
        next_date = self._current + timedelta(days=self._step)
        if next_date > self._end:
            raise StopIteration(
                f"SimulationClock exhausted at {self._current.isoformat()}; "
                f"next step {next_date.isoformat()} > end {self._end.isoformat()}"
            )
        self._current = next_date
        return self._current

    def __iter__(self) -> Iterator[date]:
        yield self._current
        while True:
            try:
                yield self.advance()
            except StopIteration:
                return
