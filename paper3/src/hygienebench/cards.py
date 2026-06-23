"""
DatasetCard and RunManifest generators for HygieneBench v0.1.

Matches the dataset card spec in SCHEMA_v0_1.md §Dataset Card Specification.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from hygienebench.generator import SyntheticHygieneDataset
from hygienebench.splitter import split_summary


def make_dataset_card(ds: SyntheticHygieneDataset) -> Dict[str, Any]:
    cfg = ds.config
    cond = cfg.condition
    summary = ds.summary()
    splits = split_summary(ds)

    imbalance = {}
    if summary["anomaly_class_counts"] and summary["n_users"] > 0:
        for cls, cnt in summary["anomaly_class_counts"].items():
            denom = summary["n_users"]
            imbalance[cls] = round(cnt / max(denom, 1), 4)

    return {
        "dataset_id": ds.dataset_id,
        "generator_version": cfg.generator_version,
        "schema_version": cfg.schema_version,
        "seed": cfg.seed,
        "condition_id": cond.condition_id,
        "population_scale": (
            "small" if cfg.population.n_users <= 300
            else "large" if cfg.population.n_users >= 3000
            else "medium"
        ),
        "n_users": summary["n_users"],
        "n_groups": summary["n_groups"],
        "n_computers": summary["n_computers"],
        "n_assets": summary["n_assets"],
        "n_login_events": summary["n_login_events"],
        "n_group_membership_events": summary["n_group_membership_events"],
        "n_vulnerability_records": summary["n_vulnerability_records"],
        "n_anomaly_labels": summary["n_anomaly_labels"],
        "anomaly_class_counts": summary["anomaly_class_counts"],
        "class_imbalance_ratios": imbalance,
        "split_counts": splits,
        "freshness_regime": {
            "stale_rate": cond.stale_rate,
            "stale_severity": cond.stale_severity,
            "missing_sources": cond.missing_sources,
            "missing_source_rate": cond.missing_source_rate,
            "ou_level_gap": cond.ou_level_gap,
        },
        "labels_visible_at_train": cond.labels_visible_at_train,
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "structural_prior_sources": {
            "patch_lag": "DBIR 2026 aggregate (43-day mean critical); lognormal model assumption",
            "cve_severity": "NVD empirical distribution (public); normal approximation",
            "ad_group_size": "Model assumption (no published distribution); sensitivity swept",
            "telemetry_cadence": "CISA BOD 23-01 (7/14-day mandate as normal baseline)",
            "privileged_rate": "Model assumption 5%; sensitivity swept",
        },
        "synthetic_data_disclaimer": (
            "All data is fully synthetic and seeded. No employer, government, or production "
            "data was used or referenced. Entity identifiers are random UUIDs derived from "
            "the seed. Performance claims are bounded to this synthetic evaluation environment."
        ),
    }


def save_dataset_card(ds: SyntheticHygieneDataset, output_dir: str) -> None:
    import os
    card = make_dataset_card(ds)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "dataset_card.json")
    with open(path, "w") as f:
        json.dump(card, f, indent=2, default=str)


def make_run_manifest(
    task_id: str,
    condition_id: str,
    method_id: str,
    seed: int,
    ds: SyntheticHygieneDataset,
    hyperparameters: Dict[str, Any],
    metrics: Dict[str, Any],
    library_versions: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    cfg = ds.config
    splits = split_summary(ds)
    return {
        "run_id": None,  # filled by evaluation runner
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "condition_id": condition_id,
        "method_id": method_id,
        "seed": seed,
        "generator_version": cfg.generator_version,
        "schema_version": cfg.schema_version,
        "dataset_id": ds.dataset_id,
        "hyperparameters": hyperparameters,
        "split_counts": splits,
        "metrics": metrics,
        "library_versions": library_versions or {},
    }
