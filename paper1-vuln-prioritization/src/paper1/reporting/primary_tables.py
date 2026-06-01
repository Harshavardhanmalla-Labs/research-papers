"""Paper-ready tables from frozen primary outputs (Phase 17).

Every table is built only from the frozen metric frames
(``per_seed_metrics.csv``, ``aggregated_metrics.csv``, ``eehda_report.csv``)
and written as CSV + Markdown + LaTeX. No numbers are hand-copied and no
interpretation is asserted here -- EHD is treated consistently as
*lower-is-better*; that is the only "direction" encoded.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

__all__ = [
    "build_acceptance_checks",
    "build_audit_metrics",
    "build_ehd_primary",
    "build_metric_summary",
    "build_operational_metrics",
    "build_ranking_metrics",
    "build_strategy_comparison_vs_epss",
    "generate_all_tables",
    "write_table",
]

_EPS = 1e-9
_RANKING_METRICS = ["precision_at_k", "recall_at_k", "ndcg_at_k"]
_OPERATIONAL_METRICS = [
    "kev_breach_rate",
    "capacity_efficiency",
    "scheduled_count",
    "scheduler_feasibility",
    "risk_acceptance_rate",
]
_AUDIT_METRICS = ["audit_hash_chain_valid", "audit_record_count"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _pivot(agg: pd.DataFrame, value_col: str) -> pd.DataFrame:
    return agg.pivot_table(index="strategy", columns="metric", values=value_col, aggfunc="first")


def _col(pivot: pd.DataFrame, metric: str) -> pd.Series:
    if metric in pivot.columns:
        return pivot[metric]
    return pd.Series(np.nan, index=pivot.index)


def _fmt(x: Any) -> str:
    if isinstance(x, (bool, np.bool_)):
        return str(bool(x))
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, (float, np.floating)):
        if pd.isna(x):
            return "NaN"
        return f"{float(x):.6g}"
    return str(x)


def _df_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(str(c) for c in cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_fmt(row[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _latex_escape(text: str) -> str:
    return "".join(_LATEX_ESCAPES.get(ch, ch) for ch in text)


def _df_to_latex(df: pd.DataFrame) -> str:
    """Plain-LaTeX tabular (no jinja2/Styler dependency); uses \\hline rules."""
    cols = list(df.columns)
    colspec = " ".join("l" for _ in cols)
    header = " & ".join(_latex_escape(str(c)) for c in cols) + r" \\"
    body = [
        " & ".join(_latex_escape(_fmt(row[c])) for c in cols) + r" \\"
        for _, row in df.iterrows()
    ]
    return (
        "\\begin{tabular}{" + colspec + "}\n"
        "\\hline\n"
        + header
        + "\n\\hline\n"
        + "\n".join(body)
        + "\n\\hline\n"
        "\\end{tabular}\n"
    )


def write_table(df: pd.DataFrame, directory: str | Path, name: str) -> dict[str, str]:
    """Write a DataFrame as CSV + Markdown + LaTeX; return the file paths."""
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    csv_path = d / f"{name}.csv"
    md_path = d / f"{name}.md"
    tex_path = d / f"{name}.tex"
    df.to_csv(csv_path, index=False)
    md_path.write_text(_df_to_markdown(df), encoding="utf-8")
    tex_path.write_text(_df_to_latex(df), encoding="utf-8")
    return {"csv": str(csv_path), "md": str(md_path), "tex": str(tex_path)}


# ---------------------------------------------------------------------------
# table builders
# ---------------------------------------------------------------------------


def build_metric_summary(aggregated: pd.DataFrame) -> pd.DataFrame:
    """Table 1: per (strategy, metric) mean / std / count."""
    cols = ["strategy", "metric", "mean", "std", "count"]
    out = aggregated[[c for c in cols if c in aggregated.columns]].copy()
    return out.sort_values(["strategy", "metric"]).reset_index(drop=True)


def build_ehd_primary(aggregated: pd.DataFrame, eehda: pd.DataFrame) -> pd.DataFrame:
    """Table 2: per-strategy EHD (absolute mean/std + EEHDA reporting forms)."""
    m = _pivot(aggregated, "mean")
    s = _pivot(aggregated, "std")
    out = pd.DataFrame(
        {
            "strategy": m.index,
            "absolute_EHD_mean": _col(m, "ehd_absolute").to_numpy(),
            "absolute_EHD_std": _col(s, "ehd_absolute").to_numpy(),
        }
    )
    eehda_cols = ["strategy", "relative_to_random", "relative_to_epss", "fraction_of_oracle"]
    e = eehda[[c for c in eehda_cols if c in eehda.columns]].copy()
    e = e.rename(
        columns={
            "relative_to_random": "relative_to_random_mean",
            "relative_to_epss": "relative_to_epss_mean",
            "fraction_of_oracle": "fraction_of_oracle_mean",
        }
    )
    out = out.merge(e, on="strategy", how="left")
    # Lower EHD is better -> present best (lowest mean EHD) first.
    return out.sort_values("absolute_EHD_mean").reset_index(drop=True)


def build_strategy_comparison_vs_epss(aggregated: pd.DataFrame) -> pd.DataFrame:
    """Table 3: each non-oracle strategy vs epss_only on mean EHD.

    EHD is lower-is-better: a negative ``delta_vs_epss`` means the strategy
    accrues FEWER simulated exploited-host-days than epss_only, i.e. better.
    """
    m = _pivot(aggregated, "mean")
    ehd = _col(m, "ehd_absolute")
    if "epss_only" not in ehd.index or pd.isna(ehd.get("epss_only")):
        raise ValueError("epss_only EHD missing; cannot build comparison-vs-epss table")
    epss_mean = float(ehd["epss_only"])
    rows: list[dict[str, Any]] = []
    for strat in sorted(ehd.index):
        if strat == "oracle":
            continue
        mean_ehd = float(ehd[strat])
        delta = mean_ehd - epss_mean
        rel = delta / epss_mean if epss_mean != 0 else np.nan
        if delta < -_EPS:
            direction = "better (lower EHD than epss_only)"
        elif delta > _EPS:
            direction = "worse (higher EHD than epss_only)"
        else:
            direction = "approximately equal to epss_only"
        rows.append(
            {
                "strategy": strat,
                "mean_EHD": mean_ehd,
                "delta_vs_epss": delta,
                "relative_delta_vs_epss": rel,
                "interpretation_direction": direction,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "strategy",
            "mean_EHD",
            "delta_vs_epss",
            "relative_delta_vs_epss",
            "interpretation_direction",
        ],
    ).sort_values("mean_EHD").reset_index(drop=True)


def build_ranking_metrics(aggregated: pd.DataFrame) -> pd.DataFrame:
    """Table 4: ranking-quality metrics (precision/recall/nDCG @ k) by strategy."""
    m = _pivot(aggregated, "mean")
    s = _pivot(aggregated, "std")
    out = pd.DataFrame({"strategy": m.index})
    for metric in _RANKING_METRICS:
        out[f"{metric}_mean"] = _col(m, metric).to_numpy()
        out[f"{metric}_std"] = _col(s, metric).to_numpy()
    return out.sort_values("strategy").reset_index(drop=True)


def build_operational_metrics(aggregated: pd.DataFrame) -> pd.DataFrame:
    """Table 5: operational metrics (KEV breach, capacity efficiency, ...)."""
    m = _pivot(aggregated, "mean")
    out = pd.DataFrame({"strategy": m.index})
    for metric in _OPERATIONAL_METRICS:
        out[f"{metric}_mean"] = _col(m, metric).to_numpy()
    return out.sort_values("strategy").reset_index(drop=True)


def build_audit_metrics(aggregated: pd.DataFrame) -> pd.DataFrame:
    """Table 6: audit-trail metrics present in the per-seed metric set.

    ``audit_explanation_completeness`` / per-feature imputation rate are
    computed by the evaluation layer but are not part of the per-seed metric
    set written by the runner, so they are not in this frozen artifact.
    """
    m = _pivot(aggregated, "mean")
    out = pd.DataFrame({"strategy": m.index})
    for metric in _AUDIT_METRICS:
        out[f"{metric}_mean"] = _col(m, metric).to_numpy()
    return out.sort_values("strategy").reset_index(drop=True)


def build_acceptance_checks(
    per_seed_metrics: pd.DataFrame,
    freeze_verified: bool,
    capacity: int | None = None,
) -> pd.DataFrame:
    """Table 7: acceptance / integrity checks as (check, value) rows."""
    df = per_seed_metrics.copy()
    values = pd.to_numeric(df["value"], errors="coerce")
    sched = values[df["metric"] == "scheduled_count"]
    audit = values[df["metric"] == "audit_hash_chain_valid"]
    nan_count = int(values.isna().sum())
    inf_count = int(np.isinf(values).sum())
    max_sched = float(sched.max()) if len(sched) else np.nan
    cap = capacity if capacity is not None else (float(sched.max()) if len(sched) else np.nan)
    checks = [
        ("seed_count", int(df["seed"].nunique())),
        ("strategy_count", int(df["strategy"].nunique())),
        ("metric_rows", len(df)),
        ("audit_logs_checked", len(audit)),
        ("audit_logs_valid", bool(len(audit) > 0 and (audit == 1.0).all())),
        ("nan_count", nan_count),
        ("infinite_metric_count", inf_count),
        ("max_scheduled_count", max_sched),
        ("capacity", cap),
        ("scheduled_within_capacity", bool(len(sched) == 0 or (sched <= cap).all())),
        ("freeze_verified", bool(freeze_verified)),
    ]
    return pd.DataFrame(checks, columns=["check", "value"])


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------


def generate_all_tables(
    frozen: dict[str, Any],
    tables_dir: str | Path,
    capacity: int | None = None,
) -> dict[str, dict[str, str]]:
    """Build and write all paper tables; return {table_name: {fmt: path}}."""
    agg = frozen["aggregated_metrics"]
    eehda = frozen["eehda_report"]
    per_seed = frozen["per_seed_metrics"]
    freeze_verified = bool(frozen.get("freeze_verified", False))

    tables = {
        "table_primary_metric_summary": build_metric_summary(agg),
        "table_ehd_primary": build_ehd_primary(agg, eehda),
        "table_strategy_comparison_vs_epss": build_strategy_comparison_vs_epss(agg),
        "table_ranking_metrics": build_ranking_metrics(agg),
        "table_operational_metrics": build_operational_metrics(agg),
        "table_audit_metrics": build_audit_metrics(agg),
        "table_acceptance_checks": build_acceptance_checks(
            per_seed, freeze_verified, capacity
        ),
    }
    written: dict[str, dict[str, str]] = {}
    for name, df in tables.items():
        written[name] = write_table(df, tables_dir, name)
    return written
