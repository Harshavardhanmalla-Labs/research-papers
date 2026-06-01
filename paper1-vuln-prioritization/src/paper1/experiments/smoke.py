"""End-to-end smoke experiment runner (Phase 11).

Wires the full pipeline on bundled toy fixtures, deterministically and
without any live feed:

    synthetic fleet -> toy vulnerabilities -> pair construction ->
    Label A/B -> temporal-split assignment -> seven-feature frame ->
    ranking strategies -> capacity-constrained scheduler -> evaluation
    metrics -> per-seed metric frame -> statistical-frame validation.

This is a *pipeline verification*, not a research result. It uses only
the toy fixtures in ``data/fixtures/`` and the deterministic synthetic
generator; nothing here fetches real external data or fabricates results.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from paper1 import __framework_version__
from paper1.audit.hash_chain import AuditLogger
from paper1.audit.schema import ExploitSignal, Vulnerability
from paper1.evaluation.audit_metrics import (
    audit_record_count_by_type,
    hash_chain_validity,
)
from paper1.evaluation.compliance_metrics import (
    capacity_efficiency,
    kev_deadline_breach_rate,
)
from paper1.evaluation.eehda import compute_ehd, eehda_report
from paper1.evaluation.metrics import aggregate_metrics
from paper1.evaluation.ranking_metrics import ndcg_at_k, precision_at_k, recall_at_k
from paper1.evaluation.scheduler_metrics import (
    risk_acceptance_rate,
    scheduler_feasibility_rate,
)
from paper1.evaluation.statistical_tests import validate_per_seed_metric_frame
from paper1.experiments.common import (
    ExperimentManifest,
    collect_artifact_versions,
    dataframe_to_parquet_or_csv,
    ensure_result_dirs,
    stable_config_sha,
    validate_audit_logs,
    validate_strategy_outputs,
    write_manifest,
)
from paper1.feeds.cve_client import parse_cpe23
from paper1.feeds.kev_client import normalize_kev_catalog
from paper1.feeds.poc_client import normalize_exploitdb_csv
from paper1.model.features import build_feature_frame
from paper1.model.frames import attach_labels, attach_split, pairs_to_frame
from paper1.model.labels import (
    label_a,
    label_b,
    label_dates_a,
    label_dates_b,
)
from paper1.model.pairs import build_pairs
from paper1.model.splits import assign_split, make_temporal_split
from paper1.model.strategies import rank_pairs
from paper1.scheduler.approver import ApproverPolicyA
from paper1.scheduler.blackout import load_blackout_config
from paper1.scheduler.scheduler import schedule_window
from paper1.synthetic.catalogs import (
    load_host_type_defaults,
    load_product_catalog,
    load_service_catalog,
)
from paper1.synthetic.criticality import compute_criticality
from paper1.synthetic.exposure import compute_exposure
from paper1.synthetic.fleet_generator import FleetGenerator
from paper1.synthetic.remediation_complexity import compute_complexity
from paper1.utils.config import load_yaml
from paper1.utils.seeds import derive_subseed, make_rng
from paper1.utils.time import ensure_utc, parse_date, utc_now

__all__ = ["run_smoke_experiment", "run_smoke_seed"]

_FIXTURES = Path(__file__).resolve().parents[3] / "data" / "fixtures"
_DEFAULT_CONFIG = (
    Path(__file__).resolve().parents[3] / "configs" / "experiment_smoke.yaml"
)

_REQUIRED_CONFIG_KEYS = {
    "config_name",
    "seed_master",
    "seeds",
    "fleet_size",
    "t0",
    "H_days",
    "data_window_start",
    "data_window_end",
    "capacity",
    "label",
    "strategies",
    "approver_policy",
    "blackout_config",
    "identity_config",
    "output_dir",
}

# The metric names emitted per (seed, strategy). Documented np.nan cases are
# noted in the README: kev_breach_rate / capacity_efficiency are NaN when no
# eligible pairs exist; ranking metrics are NaN when all top-k are censored.
_METRIC_NAMES = [
    "precision_at_k",
    "recall_at_k",
    "ndcg_at_k",
    "ehd_absolute",
    "kev_breach_rate",
    "capacity_efficiency",
    "scheduler_feasibility",
    "risk_acceptance_rate",
    "audit_hash_chain_valid",
    "audit_record_count",
    "scheduled_count",
]


def _is_na(value: Any) -> bool:
    if value is None or value is pd.NA:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _coerce_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return parse_date(str(value)[:10])


def _load_smoke_config(config_path: str | Path) -> dict[str, Any]:
    cfg = load_yaml(config_path)
    if not isinstance(cfg, dict):
        raise ValueError("experiment config must be a top-level mapping")
    missing = _REQUIRED_CONFIG_KEYS - set(cfg)
    if missing:
        raise ValueError(f"experiment config missing keys: {sorted(missing)}")
    return cfg


def _load_vulns() -> list[Vulnerability]:
    raw = json.loads((_FIXTURES / "vulnerabilities_toy.json").read_text(encoding="utf-8"))
    out: list[Vulnerability] = []
    for d in raw:
        kwargs = {k: v for k, v in d.items() if not k.startswith("_")}
        kwargs["disclosure_date"] = parse_date(kwargs["disclosure_date"])
        kwargs["feed_fetch_timestamp"] = datetime.fromisoformat(
            kwargs["feed_fetch_timestamp"].replace("Z", "+00:00")
        )
        out.append(Vulnerability(**kwargs))
    return out


def _t0_datetime(t0: date) -> datetime:
    return datetime(t0.year, t0.month, t0.day, tzinfo=UTC)


def run_smoke_seed(
    seed: int,
    config: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    """Run the full pipeline for one seed; write per-seed artifacts.

    Returns a per-seed summary including the per-(strategy, metric) rows.
    Fails loudly (raises) on any pipeline or validation error.
    """
    output_dir = Path(output_dir)
    t0 = parse_date(config["t0"])
    H = int(config["H_days"])
    window_start = parse_date(config["data_window_start"])
    window_end = parse_date(config["data_window_end"])
    eval_end = t0 + timedelta(days=int(config.get("evaluation_end_days", 90)))
    now = datetime.fromisoformat(
        str(config.get("schedule_now", "2025-06-03T20:00:00Z")).replace("Z", "+00:00")
    )
    ensure_utc(now)
    identity_config = config["identity_config"]
    capacity = int(config["capacity"])
    label_kind = str(config["label"])
    strategies = list(config["strategies"])
    seed_master = int(config["seed_master"])
    seed_root = derive_subseed(seed_master, f"seed|{seed}")
    t0_dt = _t0_datetime(t0)
    horizon_end = t0 + timedelta(days=H)

    # ---- A. synthetic fleet ------------------------------------------------
    hosts = FleetGenerator(
        fleet_size=int(config["fleet_size"]),
        seed=seed_root,
        identity_config=identity_config,
        t0=t0,
    ).generate()

    # ---- B. toy vulnerabilities -------------------------------------------
    vulns = _load_vulns()
    vuln_by_cve = {v.cve_id: v for v in vulns}

    # ---- C. vulnerability-host pairs --------------------------------------
    pairs = build_pairs(vulns, hosts, t0)
    if not pairs:
        raise ValueError("smoke pipeline produced no pairs")
    pair_frame = pairs_to_frame(pairs)
    # Guard: no pair may reference a future-disclosure vulnerability.
    for p in pairs:
        if vuln_by_cve[p.cve_id].disclosure_date > t0:
            raise ValueError(
                f"future-disclosure pair leaked: {p.pair_id} "
                f"({vuln_by_cve[p.cve_id].disclosure_date} > t0 {t0})"
            )

    # ---- D. Label A / B histories -----------------------------------------
    kev_raw = json.loads((_FIXTURES / "kev_toy.json").read_text(encoding="utf-8"))
    poc_text = (_FIXTURES / "poc_toy.csv").read_text(encoding="utf-8")
    kev_norm = normalize_kev_catalog(kev_raw, as_of_date=window_end)
    poc_norm = normalize_exploitdb_csv(poc_text, as_of_date=window_end)

    if label_kind == "A":
        labels = label_a(pairs, kev_norm, poc_norm, t0, H, window_end)
        label_dates = label_dates_a(pairs, kev_norm, poc_norm, t0, H, window_end)
    elif label_kind == "B":
        labels = label_b(pairs, poc_norm, t0, H, window_end)
        label_dates = label_dates_b(pairs, poc_norm, t0, H, window_end)
    else:
        raise ValueError(f"unsupported label {label_kind!r} (expected 'A' or 'B')")

    # Guard: every realized label event must fall in (t0, t0+H].
    for d in list(label_dates):
        if _is_na(d):
            continue
        dd = _coerce_date(d)
        if not (t0 < dd <= horizon_end):
            raise ValueError(f"label event {dd} outside (t0, t0+H]")

    labels_df = pd.DataFrame(
        {
            "pair_id": pair_frame["pair_id"].to_numpy(),
            "label": labels.to_numpy(),
            "label_date": label_dates.to_numpy(),
        }
    )
    labeled_frame = attach_labels(pair_frame, labels, label_dates, label_name=label_kind)

    # ---- E. temporal-split assignment (validation-only) -------------------
    split_cfg = make_temporal_split(
        None,
        window_start,
        window_end,
        H,
        train_months=int(config.get("train_split_months", 4)),
    )
    split_name = assign_split(t0, split_cfg)
    split_frame = attach_split(labeled_frame, [split_name] * len(labeled_frame))

    # ---- F. exploit signals (deterministic; as-of t0, no leakage) ---------
    kev_asof_t0 = normalize_kev_catalog(kev_raw, as_of_date=t0)
    kev_added_at_t0: dict[str, date] = {}
    if not kev_asof_t0.empty:
        for _, r in kev_asof_t0.iterrows():
            kev_added_at_t0[str(r["cve_id"])] = _coerce_date(r["kev_date_added"])

    paired_cves = sorted({p.cve_id for p in pairs})
    signals: list[ExploitSignal] = []
    for cve in paired_cves:
        is_kev = cve in kev_added_at_t0
        epss = float(make_rng(derive_subseed(seed_root, f"epss|{cve}")).random())
        signals.append(
            ExploitSignal(
                cve_id=cve,
                epss_score=epss,
                epss_percentile=0.5,
                epss_fetch_timestamp=t0_dt,
                epss_version="v4-toy",
                kev_status=is_kev,
                kev_date_added=kev_added_at_t0.get(cve),  # <= t0 by construction
                poc_observed=False,
                signal_staleness_days=0,
            )
        )

    # ---- G/H. exposure + remediation complexity ---------------------------
    host_by_id = {h.host_id: h for h in hosts}
    defaults = load_host_type_defaults()
    services = load_service_catalog()
    product_by_key = {
        (p["vendor"].lower(), p["product"].lower()): p
        for p in load_product_catalog()["products"]
    }
    crit = [
        compute_criticality(
            host=host_by_id[hid],
            host_defaults=defaults,
            identity_config=identity_config,
            cmdb_staleness_rate=0.0,
            rng=make_rng(derive_subseed(seed_root, f"crit|{hid}")),
            computed_at=t0_dt,
        )
        for hid in sorted({p.host_id for p in pairs})
    ]
    exposures = []
    complexities = []
    for p in pairs:
        vuln = vuln_by_cve[p.cve_id]
        parsed = parse_cpe23(vuln.cpe_matches[0])
        pk = (parsed.vendor.lower(), parsed.product.lower())
        meta = product_by_key.get(pk)
        exposures.append(
            compute_exposure(
                vulnerability=vuln,
                host=host_by_id[p.host_id],
                product_meta=meta,
                product_key=pk,
                service_catalog=services,
                rng=make_rng(derive_subseed(seed_root, f"expo|{p.pair_id}")),
            )
        )
        complexities.append(
            compute_complexity(
                vuln,
                host_by_id[p.host_id],
                meta,
                make_rng(derive_subseed(seed_root, f"cmplx|{p.pair_id}")),
            )
        )

    # ---- I. seven-feature frame -------------------------------------------
    feature_frame = build_feature_frame(
        pair_frame, vulns, signals, crit, exposures, complexities, t0
    )

    complexity_by_pair = {c.pair_id: float(c.complexity_score) for c in complexities}
    role_by_host = {h.host_id: h.role for h in hosts}
    group_by_host = {h.host_id: h.group_id for h in hosts}

    # Post-hoc KEV pairs for the (evaluation-time) compliance metric. This
    # uses the catalog as realized by data_window_end -- it is an evaluation
    # measurement, not a decision-time feature, so it does not leak into
    # scheduling (the scheduler queue's kev_due_date stays empty at t0).
    kev_due_by_cve: dict[str, Any] = {}
    if not kev_norm.empty:
        for _, r in kev_norm.iterrows():
            if not _is_na(r.get("kev_due_date")):
                kev_due_by_cve[str(r["cve_id"])] = r["kev_due_date"]
    kev_pairs_df = pd.DataFrame(
        [
            {"pair_id": p.pair_id, "kev_due_date": kev_due_by_cve[p.cve_id]}
            for p in pairs
            if p.cve_id in kev_due_by_cve
        ],
        columns=["pair_id", "kev_due_date"],
    )

    # ---- per-seed shared artifacts ----------------------------------------
    seed_dir = output_dir / f"seed_{seed:03d}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    dataframe_to_parquet_or_csv(split_frame, seed_dir / "pairs.csv")
    dataframe_to_parquet_or_csv(feature_frame, seed_dir / "features.csv")
    dataframe_to_parquet_or_csv(labels_df, seed_dir / "labels.csv")

    # ---- J/K/L. rank, schedule, metrics per strategy ----------------------
    blackout = load_blackout_config(config["blackout_config"])
    k = min(10, len(pairs))
    rankings_by_strategy: dict[str, pd.DataFrame] = {}
    ehd_by_strategy: dict[str, float] = {}
    audit_paths: dict[str, str] = {}
    metric_rows: list[dict[str, Any]] = []

    for strat in strategies:
        rank_kwargs: dict[str, Any] = {"seed": seed_root}
        if strat == "oracle":
            rank_kwargs["label_series"] = labels
        ranking = rank_pairs(strat, pair_frame, feature_frame, **rank_kwargs)
        rankings_by_strategy[strat] = ranking

        queue = ranking.copy()
        queue["host_role"] = queue["host_id"].map(role_by_host)
        queue["group_id"] = queue["host_id"].map(group_by_host)
        queue["kev_due_date"] = None  # decision-time: KEV due dates not known
        queue["complexity_score"] = queue["pair_id"].map(complexity_by_pair)
        queue["bundle_group"] = None
        queue["dependency_group"] = None

        strat_dir = seed_dir / f"strategy_{strat}"
        strat_dir.mkdir(parents=True, exist_ok=True)
        audit_path = strat_dir / "audit_log.jsonl"
        logger = AuditLogger(audit_path)
        result = schedule_window(
            queue,
            capacity=capacity,
            now=now,
            blackout_config=blackout,
            approver_policy=ApproverPolicyA(seed=seed_root),
            audit_logger=logger,
            seed=seed_root,
        )
        if len(result.scheduled) > capacity:
            raise ValueError(
                f"strategy {strat!r} scheduled {len(result.scheduled)} > capacity {capacity}"
            )
        audit_paths[strat] = str(audit_path)

        sched_hist = pd.DataFrame(
            [
                {
                    "pair_id": s.pair_id,
                    "strategy_name": strat,
                    "scheduled_at": s.scheduled_at,
                    "effective_remediation_time": s.effective_remediation_time,
                    "remediated_at": s.effective_remediation_time,
                    "status": "scheduled",
                }
                for s in result.scheduled
            ],
            columns=[
                "pair_id",
                "strategy_name",
                "scheduled_at",
                "effective_remediation_time",
                "remediated_at",
                "status",
            ],
        )

        ehd = compute_ehd(sched_hist, labels_df, eval_end, remediated_col="remediated_at")
        ehd_by_strategy[strat] = ehd
        scheduled_pairs_df = (
            sched_hist[["pair_id"]]
            if not sched_hist.empty
            else pd.DataFrame(columns=["pair_id"])
        )
        kev_breach = (
            kev_deadline_breach_rate(sched_hist, kev_pairs_df)
            if not kev_pairs_df.empty
            else float("nan")
        )
        cap_eff = (
            capacity_efficiency(scheduled_pairs_df, labels_df)
            if not scheduled_pairs_df.empty
            else float("nan")
        )

        metrics = {
            "precision_at_k": precision_at_k(ranking, labels_df, k),
            "recall_at_k": recall_at_k(ranking, labels_df, k),
            "ndcg_at_k": ndcg_at_k(ranking, labels_df, k),
            "ehd_absolute": ehd,
            "kev_breach_rate": kev_breach,
            "capacity_efficiency": cap_eff,
            "scheduler_feasibility": scheduler_feasibility_rate([result]),
            "risk_acceptance_rate": risk_acceptance_rate([result]),
            "audit_hash_chain_valid": 1.0 if hash_chain_validity(audit_path) else 0.0,
            "audit_record_count": float(sum(audit_record_count_by_type(audit_path).values())),
            "scheduled_count": float(len(result.scheduled)),
        }

        dataframe_to_parquet_or_csv(ranking, strat_dir / "ranking.csv")
        dataframe_to_parquet_or_csv(sched_hist, strat_dir / "schedule_history.csv")
        strat_metrics_df = pd.DataFrame(
            [{"strategy": strat, "metric": m, "value": v} for m, v in metrics.items()]
        )
        dataframe_to_parquet_or_csv(strat_metrics_df, strat_dir / "metrics.csv")

        for m_name in _METRIC_NAMES:
            v = metrics[m_name]
            metric_rows.append(
                {
                    "seed": int(seed),
                    "strategy": strat,
                    "metric": m_name,
                    "value": float(v) if v is not None else float("nan"),
                }
            )

    # ---- validation (fail loudly) -----------------------------------------
    validate_strategy_outputs(rankings_by_strategy, len(pairs))
    validate_audit_logs(audit_paths)

    return {
        "seed": int(seed),
        "pair_count": len(pairs),
        "strategy_count": len(strategies),
        "split": split_name,
        "metric_rows": metric_rows,
        "ehd_by_strategy": ehd_by_strategy,
        "audit_paths": audit_paths,
        "seed_dir": str(seed_dir),
    }


def _write_summary_md(
    path: Path,
    config: dict[str, Any],
    per_seed: pd.DataFrame,
    pair_counts: list[int],
    eehda: pd.DataFrame,
) -> None:
    lines: list[str] = []
    lines.append(f"# Smoke experiment summary: {config['config_name']}")
    lines.append("")
    lines.append(
        "**Pipeline verification only — NOT a paper result.** Uses bundled "
        "toy fixtures and the deterministic synthetic generator; no live feeds."
    )
    lines.append("")
    lines.append(f"- seeds: {config['seeds']}")
    lines.append(f"- strategies: {config['strategies']}")
    lines.append(f"- fleet_size: {config['fleet_size']}, capacity: {config['capacity']}")
    lines.append(f"- t0: {config['t0']}, H_days: {config['H_days']}, label: {config['label']}")
    lines.append(f"- pairs per seed: min={min(pair_counts)} max={max(pair_counts)}")
    lines.append("")
    lines.append("## Mean EHD (simulated exploited-host-days) by strategy")
    lines.append("")
    ehd = (
        per_seed[per_seed["metric"] == "ehd_absolute"]
        .groupby("strategy")["value"]
        .mean()
        .sort_values()
    )
    lines.append("| strategy | mean EHD |")
    lines.append("| --- | --- |")
    for strat, val in ehd.items():
        lines.append(f"| {strat} | {val:.2f} |")
    lines.append("")
    lines.append("## EEHDA report")
    lines.append("")
    lines.append(
        "| strategy | absolute | rel_to_random | rel_to_epss | fraction_of_oracle |"
    )
    lines.append("| --- | --- | --- | --- | --- |")
    for _, r in eehda.iterrows():
        lines.append(
            f"| {r['strategy']} | {r['absolute']:.2f} | {r['relative_to_random']} | "
            f"{r['relative_to_epss']} | {r['fraction_of_oracle']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_smoke_experiment(
    config_path: str | Path = _DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Run the end-to-end smoke experiment across all configured seeds.

    Writes a manifest, per-seed artifacts, aggregated metrics, an EEHDA
    report, and a markdown summary under the config's ``output_dir``.
    Returns a compact summary dict. Fails loudly on any validation error.
    """
    config = _load_smoke_config(config_path)
    output_dir = ensure_result_dirs(config["output_dir"])

    manifest = ExperimentManifest(
        config_name=str(config["config_name"]),
        config_sha=stable_config_sha(config_path),
        code_version=__framework_version__,
        created_at=utc_now(),
        seeds=[int(s) for s in config["seeds"]],
        strategies=list(config["strategies"]),
        output_dir=str(output_dir),
        artifact_versions=collect_artifact_versions(),
        notes=(
            "Phase 11 end-to-end smoke verification on toy fixtures; "
            "NOT a paper result."
        ),
    )
    write_manifest(output_dir / "manifest.json", manifest)

    all_rows: list[dict[str, Any]] = []
    pair_counts: list[int] = []
    seed_summaries: list[dict[str, Any]] = []
    for s in config["seeds"]:
        res = run_smoke_seed(int(s), config, output_dir)
        all_rows.extend(res["metric_rows"])
        pair_counts.append(res["pair_count"])
        seed_summaries.append(res)

    per_seed = pd.DataFrame(all_rows, columns=["seed", "strategy", "metric", "value"])
    validate_per_seed_metric_frame(per_seed)
    aggregated = aggregate_metrics(per_seed)

    ehd_mean = (
        per_seed[per_seed["metric"] == "ehd_absolute"]
        .groupby("strategy")["value"]
        .mean()
        .to_dict()
    )
    eehda = eehda_report(ehd_mean)

    metrics_dir = output_dir / "metrics"
    dataframe_to_parquet_or_csv(per_seed, metrics_dir / "per_seed_metrics.csv")
    dataframe_to_parquet_or_csv(aggregated, metrics_dir / "aggregated_metrics.csv")
    dataframe_to_parquet_or_csv(eehda, metrics_dir / "eehda_report.csv")
    _write_summary_md(output_dir / "summary.md", config, per_seed, pair_counts, eehda)

    # Re-verify every seed's audit logs at the experiment level.
    audit_all: dict[str, str] = {}
    for res in seed_summaries:
        for strat, p in res["audit_paths"].items():
            audit_all[f"seed{res['seed']:03d}:{strat}"] = p
    audit_logs_valid = validate_audit_logs(audit_all)

    return {
        "output_dir": str(output_dir),
        "seeds": [int(s) for s in config["seeds"]],
        "seed_count": len(config["seeds"]),
        "strategy_count": len(config["strategies"]),
        "strategies": list(config["strategies"]),
        "pair_count_min": int(min(pair_counts)),
        "pair_count_max": int(max(pair_counts)),
        "metric_rows": len(per_seed),
        "audit_logs_valid": bool(audit_logs_valid),
    }
