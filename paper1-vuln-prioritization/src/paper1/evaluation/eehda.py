"""Expected exploited-host-days (EHD) and EEHDA reporting.

EHD is a *simulated* operational metric: for a positive vulnerability-host
pair, it is the number of days the pair remained open on the host after
its label fired (KEV addition or PoC observation), bounded by the
evaluation end. Non-positive and censored pairs contribute zero.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

from paper1.evaluation.metrics import is_positive, to_day_number

__all__ = [
    "compute_ehd",
    "compute_pair_ehd",
    "eehda_absolute",
    "eehda_relative",
    "eehda_report",
    "fraction_of_oracle",
]


def compute_pair_ehd(
    pair_id: str,
    remediated_at: date | datetime | str | None,
    label_date: date | datetime | str,
    evaluation_end: date | datetime | str,
) -> float:
    """Exploited-host-days for one positive pair, in (fractional) days."""
    end_day = to_day_number(evaluation_end)
    label_day = to_day_number(label_date)
    rem_day = end_day if remediated_at is None else to_day_number(remediated_at)
    return max(0.0, min(rem_day, end_day) - label_day)


def _remediated_map(schedule_history: pd.DataFrame, remediated_col: str) -> dict[str, Any]:
    if schedule_history is None or schedule_history.empty:
        return {}
    col = remediated_col
    if col not in schedule_history.columns:
        if "effective_remediation_time" in schedule_history.columns:
            col = "effective_remediation_time"
        elif "remediated_at" in schedule_history.columns:
            col = "remediated_at"
        else:
            raise ValueError(
                f"schedule_history missing remediation column {remediated_col!r}"
            )
    return {str(r["pair_id"]): r[col] for _, r in schedule_history.iterrows()}


def compute_ehd(
    schedule_history: pd.DataFrame,
    labels: pd.DataFrame,
    evaluation_end: date | datetime | str,
    remediated_col: str = "remediated_at",
) -> float:
    """Total simulated EHD for a single strategy's schedule history.

    Positive labeled pairs not present in ``schedule_history`` are treated
    as never remediated (remediated_at = evaluation_end).
    """
    for c in ("pair_id", "label", "label_date"):
        if c not in labels.columns:
            raise ValueError(f"labels missing required column {c!r}")
    rem_by_pair = _remediated_map(schedule_history, remediated_col)
    total = 0.0
    for _, row in labels.iterrows():
        if not is_positive(row["label"]):
            continue
        label_date = row["label_date"]
        if label_date is None or (isinstance(label_date, float) and pd.isna(label_date)):
            continue
        pid = str(row["pair_id"])
        total += compute_pair_ehd(pid, rem_by_pair.get(pid), label_date, evaluation_end)
    return float(total)


def eehda_absolute(strategy_ehd: float) -> float:
    return float(strategy_ehd)


def eehda_relative(strategy_ehd: float, baseline_ehd: float) -> float:
    if baseline_ehd == 0:
        return np.nan
    return (baseline_ehd - strategy_ehd) / baseline_ehd


def fraction_of_oracle(strategy_ehd: float, random_ehd: float, oracle_ehd: float) -> float:
    denom = random_ehd - oracle_ehd
    if denom == 0:
        return np.nan
    return (random_ehd - strategy_ehd) / denom


def eehda_report(
    ehd_by_strategy: dict[str, float],
    baseline_random: str = "random",
    baseline_epss: str = "epss_only",
    oracle: str = "oracle",
) -> pd.DataFrame:
    """Per-strategy EEHDA table with the four reporting forms."""
    random_ehd = ehd_by_strategy.get(baseline_random)
    epss_ehd = ehd_by_strategy.get(baseline_epss)
    oracle_ehd = ehd_by_strategy.get(oracle)
    rows = []
    for strategy in sorted(ehd_by_strategy):
        ehd = ehd_by_strategy[strategy]
        rel_random = eehda_relative(ehd, random_ehd) if random_ehd is not None else np.nan
        rel_epss = eehda_relative(ehd, epss_ehd) if epss_ehd is not None else np.nan
        frac = (
            fraction_of_oracle(ehd, random_ehd, oracle_ehd)
            if (random_ehd is not None and oracle_ehd is not None)
            else np.nan
        )
        rows.append(
            {
                "strategy": strategy,
                "absolute": eehda_absolute(ehd),
                "relative_to_random": rel_random,
                "relative_to_epss": rel_epss,
                "fraction_of_oracle": frac,
            }
        )
    return pd.DataFrame(
        rows,
        columns=["strategy", "absolute", "relative_to_random", "relative_to_epss", "fraction_of_oracle"],
    )
