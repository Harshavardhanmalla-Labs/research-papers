"""Label A / Label B construction with strict temporal cutoffs.

A pair is positive under a label if a qualifying event occurs in the
half-open window ``(t0, t0 + H_days]``. Events on exactly ``t0`` do NOT
count; events on exactly ``t0 + H_days`` DO count. When ``t0 + H_days``
exceeds ``data_window_end`` the labels are censored (pd.NA).

Label A:  positive if CVE enters KEV OR a public PoC is first observed
          within the window.
Label B:  positive only if a public PoC is first observed within the
          window (independent of KEV — bounds EPSS-KEV entanglement).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from paper1.audit.schema import VulnerabilityHostPair

__all__ = [
    "censor_mask",
    "ensure_no_label_future_leakage",
    "label_a",
    "label_b",
    "label_dates_a",
    "label_dates_b",
    "validate_event_dates",
]


def _coerce_date(value: Any) -> date:
    """Coerce a value to a date; raise ValueError on malformed input."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError as exc:
            raise ValueError(f"Malformed date string: {value!r}") from exc
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Missing date value where a date was required")
    raise ValueError(f"Unsupported date value: {value!r} ({type(value).__name__})")


def _to_date(value: date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError(f"Expected date|datetime; got {type(value).__name__}")


def _pair_index_and_cves(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
) -> tuple[pd.Index, list[str]]:
    if isinstance(pairs, pd.DataFrame):
        if "cve_id" not in pairs.columns:
            raise ValueError("pairs DataFrame missing 'cve_id' column")
        return pairs.index, pairs["cve_id"].tolist()
    return pd.RangeIndex(len(pairs)), [p.cve_id for p in pairs]


def validate_event_dates(history_df: pd.DataFrame, date_col: str) -> None:
    """Raise ValueError if any value in `date_col` is malformed."""
    if history_df is None or history_df.empty:
        return
    if date_col not in history_df.columns:
        raise ValueError(f"history missing date column {date_col!r}")
    for v in history_df[date_col]:
        _coerce_date(v)


def ensure_no_label_future_leakage(
    feature_history: pd.DataFrame,
    date_col: str,
    t0: date | datetime,
) -> None:
    """Guard: raise if any feature-history row postdates t0.

    Use this on data that is supposed to be observation-only at t0 (the
    feature side). Labels intentionally look into the future; features
    must not. A test fixture that injects ``published_at > t0`` must
    trip this guard.
    """
    if feature_history is None or feature_history.empty:
        return
    if date_col not in feature_history.columns:
        raise ValueError(f"feature history missing date column {date_col!r}")
    cutoff = _to_date(t0)
    offenders = []
    for v in feature_history[date_col]:
        d = _coerce_date(v)
        if d > cutoff:
            offenders.append(d)
    if offenders:
        raise ValueError(
            f"{len(offenders)} feature rows postdate t0={cutoff} "
            f"(sample: {sorted(offenders)[:5]})"
        )


def _earliest_events_in_window(
    history_df: pd.DataFrame | None,
    cve_col: str,
    date_col: str,
    t0: date,
    t0_plus_h: date,
) -> dict[str, date]:
    """Map cve_id -> earliest event date within (t0, t0 + H]."""
    out: dict[str, date] = {}
    if history_df is None or history_df.empty:
        return out
    if cve_col not in history_df.columns or date_col not in history_df.columns:
        raise ValueError(
            f"history missing required columns {cve_col!r}/{date_col!r}"
        )
    for cve, raw in zip(history_df[cve_col], history_df[date_col], strict=True):
        if cve is None:
            continue
        d = _coerce_date(raw)
        if t0 < d <= t0_plus_h:
            if cve not in out or d < out[cve]:
                out[cve] = d
    return out


def censor_mask(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
    t0: date | datetime,
    H_days: int,
    data_window_end: date | datetime,
) -> pd.Series:
    """Boolean Series (index-aligned) True where the pair is censored."""
    index, _ = _pair_index_and_cves(pairs)
    t0_plus_h = _to_date(t0) + timedelta(days=H_days)
    censored = t0_plus_h > _to_date(data_window_end)
    return pd.Series([censored] * len(index), index=index, dtype="boolean")


def _label_from_positive_set(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
    positive: set[str],
    censored: bool,
) -> pd.Series:
    index, cves = _pair_index_and_cves(pairs)
    if censored:
        return pd.Series([pd.NA] * len(index), index=index, dtype="boolean")
    return pd.Series([c in positive for c in cves], index=index, dtype="boolean")


def label_a(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
    kev_history: pd.DataFrame | None,
    poc_history: pd.DataFrame | None,
    t0: date | datetime,
    H_days: int,
    data_window_end: date | datetime,
) -> pd.Series:
    """Label A: KEV addition OR PoC observation within (t0, t0+H]."""
    t0_date = _to_date(t0)
    t0_plus_h = t0_date + timedelta(days=H_days)
    if t0_plus_h > _to_date(data_window_end):
        return _label_from_positive_set(pairs, set(), censored=True)
    kev = _earliest_events_in_window(kev_history, "cve_id", "kev_date_added", t0_date, t0_plus_h)
    poc = _earliest_events_in_window(poc_history, "cve_id", "poc_first_seen", t0_date, t0_plus_h)
    positive = set(kev) | set(poc)
    return _label_from_positive_set(pairs, positive, censored=False)


def label_b(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
    poc_history: pd.DataFrame | None,
    t0: date | datetime,
    H_days: int,
    data_window_end: date | datetime,
) -> pd.Series:
    """Label B: PoC observation within (t0, t0+H] only."""
    t0_date = _to_date(t0)
    t0_plus_h = t0_date + timedelta(days=H_days)
    if t0_plus_h > _to_date(data_window_end):
        return _label_from_positive_set(pairs, set(), censored=True)
    poc = _earliest_events_in_window(poc_history, "cve_id", "poc_first_seen", t0_date, t0_plus_h)
    return _label_from_positive_set(pairs, set(poc), censored=False)


def _label_dates(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
    event_maps: list[dict[str, date]],
    censored: bool,
) -> pd.Series:
    index, cves = _pair_index_and_cves(pairs)
    if censored:
        return pd.Series([pd.NA] * len(index), index=index, dtype="object")
    values: list[Any] = []
    for c in cves:
        candidates = [m[c] for m in event_maps if c in m]
        values.append(min(candidates) if candidates else pd.NA)
    return pd.Series(values, index=index, dtype="object")


def label_dates_a(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
    kev_history: pd.DataFrame | None,
    poc_history: pd.DataFrame | None,
    t0: date | datetime,
    H_days: int,
    data_window_end: date | datetime,
) -> pd.Series:
    """Earliest qualifying event date per pair for Label A; NA otherwise."""
    t0_date = _to_date(t0)
    t0_plus_h = t0_date + timedelta(days=H_days)
    if t0_plus_h > _to_date(data_window_end):
        return _label_dates(pairs, [], censored=True)
    kev = _earliest_events_in_window(kev_history, "cve_id", "kev_date_added", t0_date, t0_plus_h)
    poc = _earliest_events_in_window(poc_history, "cve_id", "poc_first_seen", t0_date, t0_plus_h)
    return _label_dates(pairs, [kev, poc], censored=False)


def label_dates_b(
    pairs: list[VulnerabilityHostPair] | pd.DataFrame,
    poc_history: pd.DataFrame | None,
    t0: date | datetime,
    H_days: int,
    data_window_end: date | datetime,
) -> pd.Series:
    """Earliest qualifying PoC date per pair for Label B; NA otherwise."""
    t0_date = _to_date(t0)
    t0_plus_h = t0_date + timedelta(days=H_days)
    if t0_plus_h > _to_date(data_window_end):
        return _label_dates(pairs, [], censored=True)
    poc = _earliest_events_in_window(poc_history, "cve_id", "poc_first_seen", t0_date, t0_plus_h)
    return _label_dates(pairs, [poc], censored=False)
