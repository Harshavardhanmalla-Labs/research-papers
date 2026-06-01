"""BaseFeedClient — common interface for NVD / EPSS / KEV / PoC clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from paper1.feeds.provenance import update_manifest_entry
from paper1.feeds.snapshots import load_snapshot, snapshot_path, write_snapshot
from paper1.utils.time import ensure_utc, parse_date

__all__ = ["BaseFeedClient", "FutureDataError"]


class FutureDataError(ValueError):
    """Raised when a record's published/added date exceeds the as-of cutoff."""


class BaseFeedClient(ABC):
    """Common surface area for all feed clients.

    Subclasses must set ``source_name`` and implement ``fetch`` and
    ``normalize``. The base class provides snapshot path resolution,
    snapshot write/load helpers, manifest registration, and
    no-future-leakage verification.
    """

    source_name: str = ""

    def __init__(
        self,
        cache_root: str | Path,
        manifest_path: str | Path | None = None,
        license_note: str = "",
    ) -> None:
        if not self.source_name:
            raise ValueError(
                f"{type(self).__name__} must set class attribute 'source_name'"
            )
        self.cache_root = Path(cache_root)
        # Default manifest sits at the cache root.
        self.manifest_path = (
            Path(manifest_path)
            if manifest_path is not None
            else self.cache_root / "MANIFEST.json"
        )
        self.license_note = license_note

    # ----- abstract methods -----------------------------------------------

    @abstractmethod
    def fetch(self, as_of_date: date) -> Any:
        """Fetch raw upstream data for the as-of date.

        Implementations may return any source-specific intermediate
        representation. Tests should never invoke this on live network.
        """

    @abstractmethod
    def normalize(self, raw: Any, as_of_date: date) -> pd.DataFrame:
        """Convert raw upstream data into the canonical per-feed DataFrame."""

    # ----- snapshot helpers -----------------------------------------------

    def snapshot_path(self, as_of_date: date) -> Path:
        return snapshot_path(self.cache_root, self.source_name, as_of_date)

    def load_snapshot(self, as_of_date: date) -> tuple[pd.DataFrame, dict[str, Any]]:
        return load_snapshot(self.snapshot_path(as_of_date))

    def write_snapshot(
        self,
        as_of_date: date,
        df: pd.DataFrame,
        *,
        fetched_at: datetime,
        source_version: str | None = None,
        extra: dict[str, Any] | None = None,
        register: bool = True,
    ) -> Path:
        ensure_utc(fetched_at)
        path = write_snapshot(
            self.cache_root,
            self.source_name,
            as_of_date,
            df,
            fetched_at=fetched_at,
            source_version=source_version,
            extra=extra,
        )
        if register:
            update_manifest_entry(
                self.manifest_path,
                source_name=self.source_name,
                snapshot_date=as_of_date,
                snapshot_file=path,
                record_count=len(df),
                license_note=self.license_note,
            )
        return path

    # ----- as-of access ---------------------------------------------------

    def get_asof(self, as_of_date: date) -> pd.DataFrame:
        """Default: load the snapshot for `as_of_date`.

        Subclasses may override to combine multiple snapshots (e.g., KEV
        reconstruction from a current catalog) but the contract stands:
        no record may have a date field strictly after ``as_of_date``.
        """
        if not isinstance(as_of_date, date) or isinstance(as_of_date, datetime):
            raise TypeError("as_of_date must be a date (not datetime)")
        df, meta = self.load_snapshot(as_of_date)
        meta_date = parse_date(meta["as_of_date"])
        if meta_date != as_of_date:
            raise ValueError(
                f"Snapshot as_of_date {meta_date} != requested {as_of_date}"
            )
        return df

    # ----- no-future-leakage verification ---------------------------------

    @staticmethod
    def verify_no_future(
        df: pd.DataFrame,
        as_of_date: date,
        date_column: str,
    ) -> None:
        """Raise FutureDataError if any row's `date_column` exceeds `as_of_date`."""
        if not isinstance(as_of_date, date) or isinstance(as_of_date, datetime):
            raise TypeError("as_of_date must be a date (not datetime)")
        if df.empty or date_column not in df.columns:
            return
        col = df[date_column]
        # Normalize the column to dates for comparison.
        parsed = []
        for v in col:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                parsed.append(None)
                continue
            if isinstance(v, datetime):
                parsed.append(v.date())
            elif isinstance(v, date):
                parsed.append(v)
            else:
                try:
                    parsed.append(parse_date(v))
                except Exception:
                    # Treat unparseable values conservatively: a malformed
                    # date is itself a provenance failure.
                    raise FutureDataError(
                        f"Unparseable {date_column!r} value {v!r}; cannot verify cutoff"
                    ) from None
        offenders = [
            (idx, d) for idx, d in zip(df.index, parsed, strict=True)
            if d is not None and d > as_of_date
        ]
        if offenders:
            sample = offenders[:5]
            raise FutureDataError(
                f"{len(offenders)} record(s) in {date_column!r} exceed as_of_date "
                f"{as_of_date}; sample: {sample}"
            )
