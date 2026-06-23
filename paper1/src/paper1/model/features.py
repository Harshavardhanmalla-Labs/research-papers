"""Seven-feature vector assembly (E, K, S, C, X, U, R).

Features are observation-only at ``t0``: KEV status reflects KEV
membership as of t0, EPSS is the t0 score, and CVSS comes from the
disclosed record. The label functions (Phase 4) are the only place that
looks past t0. Missing continuous features are imputed (median / mean /
zero); a missing KEV status defaults to 0 with a recorded warning.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

from paper1.audit.schema import (
    AssetCriticalityProfile,
    ExploitSignal,
    LocalExposureProfile,
    RemediationComplexityProfile,
    Vulnerability,
)

__all__ = ["FEATURE_COLUMNS", "build_feature_frame"]

FEATURE_COLUMNS = ["E", "K", "S", "C", "X", "U", "R"]
_CONTINUOUS_IMPUTABLE = ["E", "S", "C", "X", "R"]
_SUPPORTED_IMPUTATION = {"median", "mean", "zero"}
_UNSUPPORTED_IMPUTATION = {"last_known", "missingness_as_feature"}


def _to_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Expected date|datetime|str; got {type(value).__name__}")


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


# ---------------------------------------------------------------------------
# Lookup builders (accept list[pydantic] or DataFrame)
# ---------------------------------------------------------------------------


def _vuln_lookups(
    vulns: list[Vulnerability] | pd.DataFrame,
) -> tuple[dict[str, float], dict[str, date]]:
    s_by_cve: dict[str, float] = {}
    disclosure_by_cve: dict[str, date] = {}
    if isinstance(vulns, pd.DataFrame):
        for _, r in vulns.iterrows():
            ver = r.get("cvss_version_used")
            base = r.get("cvss_v4_base") if ver == "v4" else r.get("cvss_v31_base")
            s_by_cve[r["cve_id"]] = (float(base) / 10.0) if base is not None and not pd.isna(base) else np.nan
            if "disclosure_date" in r and r["disclosure_date"] is not None:
                disclosure_by_cve[r["cve_id"]] = _to_date(r["disclosure_date"])
    else:
        for v in vulns:
            base = v.cvss_v4_base if v.cvss_version_used == "v4" else v.cvss_v31_base
            s_by_cve[v.cve_id] = (float(base) / 10.0) if base is not None else np.nan
            disclosure_by_cve[v.cve_id] = v.disclosure_date
    return s_by_cve, disclosure_by_cve


def _signal_lookups(
    signals: list[ExploitSignal] | pd.DataFrame,
    t0_date: date,
) -> tuple[dict[str, float], dict[str, float], dict[str, date | None]]:
    e_by_cve: dict[str, float] = {}
    k_by_cve: dict[str, float] = {}
    due_by_cve: dict[str, date | None] = {}
    if isinstance(signals, pd.DataFrame):
        rows = (r for _, r in signals.iterrows())
        for r in rows:
            cve = r["cve_id"]
            e_by_cve[cve] = float(r["epss_score"]) if r.get("epss_score") is not None else np.nan
            kev = bool(r.get("kev_status", False))
            k_by_cve[cve] = 1.0 if kev else 0.0
            added = r.get("kev_date_added")
            if kev and added is not None and not (isinstance(added, float) and pd.isna(added)):
                if _to_date(added) > t0_date:
                    raise ValueError(
                        f"KEV leakage: {cve} kev_date_added {added} > t0 {t0_date}"
                    )
            due = r.get("kev_due_date")
            due_by_cve[cve] = _to_date(due) if due is not None and not (isinstance(due, float) and pd.isna(due)) else None
    else:
        for s in signals:
            e_by_cve[s.cve_id] = float(s.epss_score)
            k_by_cve[s.cve_id] = 1.0 if s.kev_status else 0.0
            if s.kev_status and s.kev_date_added is not None and s.kev_date_added > t0_date:
                raise ValueError(
                    f"KEV leakage: {s.cve_id} kev_date_added {s.kev_date_added} > t0 {t0_date}"
                )
            due_by_cve[s.cve_id] = s.kev_due_date
    return e_by_cve, k_by_cve, due_by_cve


def _criticality_lookup(
    profiles: list[AssetCriticalityProfile] | pd.DataFrame,
) -> dict[str, float]:
    out: dict[str, float] = {}
    if isinstance(profiles, pd.DataFrame):
        for _, r in profiles.iterrows():
            out[r["host_id"]] = float(r["criticality_score"])
    else:
        for p in profiles:
            out[p.host_id] = float(p.criticality_score)
    return out


def _by_pair(
    profiles: list[Any] | pd.DataFrame, value_attr: str
) -> dict[str, float]:
    out: dict[str, float] = {}
    if isinstance(profiles, pd.DataFrame):
        for _, r in profiles.iterrows():
            out[r["pair_id"]] = float(r[value_attr])
    else:
        for p in profiles:
            out[p.pair_id] = float(getattr(p, value_attr))
    return out


# ---------------------------------------------------------------------------
# Imputation
# ---------------------------------------------------------------------------


def _impute_fill(values: list[float], strategy: str) -> float:
    if strategy == "zero":
        return 0.0
    present = np.array([v for v in values if v is not None and not np.isnan(v)], dtype=float)
    if present.size == 0:
        return 0.0
    if strategy == "median":
        return float(np.median(present))
    if strategy == "mean":
        return float(np.mean(present))
    raise ValueError(f"unsupported imputation strategy {strategy!r}")


def _compute_u(due: date | None, k: float, e: float, t0_date: date) -> float:
    if due is not None:
        days = (due - t0_date).days
        if days <= 0:
            return 1.0
        return _clip01(1.0 - days / 30.0)
    return _clip01(0.25 * k + 0.75 * e)


def build_feature_frame(
    pair_frame: pd.DataFrame,
    vulnerabilities: list[Vulnerability] | pd.DataFrame,
    exploit_signals: list[ExploitSignal] | pd.DataFrame,
    criticality_profiles: list[AssetCriticalityProfile] | pd.DataFrame,
    exposure_profiles: list[LocalExposureProfile] | pd.DataFrame,
    complexity_profiles: list[RemediationComplexityProfile] | pd.DataFrame,
    t0: date | datetime | str,
    imputation_strategy: str = "median",
) -> pd.DataFrame:
    """Assemble the per-pair seven-feature frame with audit fields."""
    if imputation_strategy in _UNSUPPORTED_IMPUTATION:
        raise NotImplementedError(
            f"imputation strategy {imputation_strategy!r} is not implemented in Phase 5"
        )
    if imputation_strategy not in _SUPPORTED_IMPUTATION:
        raise ValueError(
            f"unknown imputation strategy {imputation_strategy!r}; "
            f"supported: {sorted(_SUPPORTED_IMPUTATION)}"
        )
    if "pair_id" not in pair_frame.columns:
        raise ValueError("pair_frame missing 'pair_id' column")
    if pair_frame["pair_id"].duplicated().any():
        raise ValueError("pair_frame contains duplicate pair_id values")
    for col in ("cve_id", "host_id"):
        if col not in pair_frame.columns:
            raise ValueError(f"pair_frame missing {col!r} column")

    t0_date = _to_date(t0)
    s_by_cve, disclosure_by_cve = _vuln_lookups(vulnerabilities)
    e_by_cve, k_by_cve, due_by_cve = _signal_lookups(exploit_signals, t0_date)
    c_by_host = _criticality_lookup(criticality_profiles)
    x_by_pair = _by_pair(exposure_profiles, "exposure_score")
    r_by_pair = _by_pair(complexity_profiles, "complexity_score")

    pairs = pair_frame[["pair_id", "cve_id", "host_id"]].reset_index(drop=True)

    # First pass: collect raw (possibly-NaN) values, enforce no-future guard.
    raw: dict[str, list[Any]] = {c: [] for c in ["E", "K", "S", "C", "X", "R"]}
    dues: list[date | None] = []
    k_missing: list[bool] = []
    for _, row in pairs.iterrows():
        cve = row["cve_id"]
        host = row["host_id"]
        pid = row["pair_id"]
        if cve in disclosure_by_cve and disclosure_by_cve[cve] > t0_date:
            raise ValueError(
                f"feature leakage: {cve} disclosure_date "
                f"{disclosure_by_cve[cve]} > t0 {t0_date}"
            )
        raw["E"].append(e_by_cve.get(cve, np.nan))
        if cve in k_by_cve:
            raw["K"].append(k_by_cve[cve])
            k_missing.append(False)
        else:
            raw["K"].append(np.nan)
            k_missing.append(True)
        raw["S"].append(s_by_cve.get(cve, np.nan))
        raw["C"].append(c_by_host.get(host, np.nan))
        raw["X"].append(x_by_pair.get(pid, np.nan))
        raw["R"].append(r_by_pair.get(pid, np.nan))
        dues.append(due_by_cve.get(cve))

    n = len(pairs)
    imputed_features: list[list[str]] = [[] for _ in range(n)]
    warnings: list[list[str]] = [[] for _ in range(n)]

    # K: default missing to 0 with a recorded warning.
    k_vals = [0.0 if (v is None or np.isnan(v)) else float(v) for v in raw["K"]]
    for i, missing in enumerate(k_missing):
        if missing:
            warnings[i].append("K_missing_defaulted_to_0")

    # Continuous imputation.
    imputed_cols: dict[str, list[float]] = {}
    for col in _CONTINUOUS_IMPUTABLE:
        fill = _impute_fill(raw[col], imputation_strategy)
        out_col: list[float] = []
        for i, v in enumerate(raw[col]):
            if v is None or (isinstance(v, float) and np.isnan(v)):
                out_col.append(fill)
                imputed_features[i].append(col)
            else:
                out_col.append(float(v))
        imputed_cols[col] = out_col

    e_vals = [_clip01(v) for v in imputed_cols["E"]]
    s_vals = [_clip01(v) for v in imputed_cols["S"]]
    c_vals = [_clip01(v) for v in imputed_cols["C"]]
    x_vals = [_clip01(v) for v in imputed_cols["X"]]
    r_vals = [_clip01(v) for v in imputed_cols["R"]]
    k_vals = [_clip01(v) for v in k_vals]
    u_vals = [
        _compute_u(dues[i], k_vals[i], e_vals[i], t0_date) for i in range(n)
    ]

    feature_imputed = [
        bool(imputed_features[i]) or k_missing[i] for i in range(n)
    ]

    out = pd.DataFrame(
        {
            "pair_id": pairs["pair_id"],
            "cve_id": pairs["cve_id"],
            "host_id": pairs["host_id"],
            "E": e_vals,
            "K": k_vals,
            "S": s_vals,
            "C": c_vals,
            "X": x_vals,
            "U": u_vals,
            "R": r_vals,
            "feature_imputed": feature_imputed,
            "imputed_features": imputed_features,
            "feature_warnings": warnings,
        }
    )
    return out
