"""
Dataset validation — checks schema compliance, referential integrity,
and anomaly label coverage for a generated HygieneBench dataset directory.
"""

from __future__ import annotations
import json
import os
from typing import Dict, List, Tuple
import pandas as pd


# Required tables and their required columns
REQUIRED_TABLES: Dict[str, List[str]] = {
    "users": [
        "user_id", "username", "department", "ou_path", "account_enabled",
        "account_last_logon", "days_since_last_logon", "is_privileged",
        "privileged_group_count", "is_service_account", "source_freshness_flag",
    ],
    "groups": [
        "group_id", "group_name", "group_type", "is_privileged", "member_count",
        "source_freshness_flag",
    ],
    "computers": [
        "computer_id", "hostname", "os_type", "network_segment", "asset_criticality",
        "endpoint_agent_installed", "days_since_agent_heartbeat", "source_freshness_flag",
    ],
    "assets": [
        "asset_id", "asset_type", "asset_criticality", "in_inventory",
        "in_endpoint_mgmt", "inventory_mismatch_flag", "source_freshness_flag",
    ],
    "login_events": [
        "event_id", "user_id", "computer_id", "event_timestamp",
        "logon_type", "success", "is_off_hours", "is_cross_segment",
        "is_anomalous", "anomaly_class",
    ],
    "group_membership_events": [
        "event_id", "user_id", "group_id", "action", "event_timestamp",
        "actor_user_id", "is_privileged_group", "is_anomalous", "anomaly_class",
    ],
    "endpoint_patch_state": [
        "record_id", "computer_id", "patch_compliance_score",
        "critical_missing_patch_count", "open_kev_count",
        "source_freshness_flag", "is_anomalous",
    ],
    "vulnerability_records": [
        "record_id", "computer_id", "cve_id", "cvss_score", "cvss_severity",
        "is_kev_flagged", "days_open", "remediation_status",
        "source_freshness_flag", "is_anomalous",
    ],
    "remediation_events": [
        "event_id", "computer_id", "cve_id", "action_type",
        "action_timestamp", "remediation_latency_days", "is_anomalous",
    ],
    "account_lifecycle_events": [
        "event_id", "user_id", "action", "event_timestamp",
        "actor_user_id", "is_anomalous",
    ],
    "telemetry_freshness_log": [
        "log_id", "entity_type", "entity_id", "source_system",
        "expected_refresh_interval_days", "actual_gap_days",
        "freshness_flag", "is_anomalous",
    ],
    "anomaly_labels": [
        "label_id", "entity_type", "entity_id", "anomaly_class",
        "anomaly_severity", "injected_at", "benchmark_task_id", "split",
    ],
}

VALID_FRESHNESS_FLAGS = {"fresh", "stale_mild", "stale_heavy", "missing"}
VALID_ANOMALY_CLASSES = {
    "stale_privileged_account", "privilege_escalation_drift", "group_membership_drift",
    "dormant_account_reactivation", "impossible_or_unusual_login",
    "endpoint_identity_risk_correlation", "patch_noncompliance_cluster",
    "kev_exposure_aging", "asset_inventory_mismatch", "missing_endpoint_agent",
    "telemetry_missingness_cluster", "abnormal_remediation_delay",
}


def validate_dataset(dataset_dir: str) -> Tuple[bool, Dict]:
    report: Dict = {
        "dataset_dir": dataset_dir,
        "checks": {},
        "warnings": [],
        "errors": [],
        "passed": False,
    }

    if not os.path.isdir(dataset_dir):
        report["errors"].append(f"Directory not found: {dataset_dir}")
        return False, report

    tables: Dict[str, pd.DataFrame] = {}

    # 1. Table presence and column checks
    for table_name, req_cols in REQUIRED_TABLES.items():
        path = os.path.join(dataset_dir, f"{table_name}.csv")
        if not os.path.exists(path):
            report["errors"].append(f"Missing table: {table_name}.csv")
            report["checks"][table_name] = "MISSING"
            continue
        try:
            df = pd.read_csv(path)
        except Exception as e:
            report["errors"].append(f"Cannot read {table_name}.csv: {e}")
            report["checks"][table_name] = "READ_ERROR"
            continue

        missing_cols = [c for c in req_cols if c not in df.columns]
        if missing_cols:
            report["errors"].append(f"{table_name}: missing columns {missing_cols}")
            report["checks"][table_name] = f"MISSING_COLS:{missing_cols}"
        else:
            report["checks"][table_name] = f"OK (rows={len(df)})"
        tables[table_name] = df

    if report["errors"]:
        return False, report

    # 2. Row count sanity
    users = tables["users"]
    computers = tables["computers"]
    labels = tables["anomaly_labels"]

    n_users = len(users)
    n_comps = len(computers)

    if n_users < 10:
        report["errors"].append(f"Too few users: {n_users}")
    if n_comps < 5:
        report["errors"].append(f"Too few computers: {n_comps}")

    # 3. Referential integrity (spot checks)
    login_user_ids = set(tables["login_events"]["user_id"].dropna().unique())
    valid_user_ids = set(users["user_id"].unique())
    orphan_logins = login_user_ids - valid_user_ids
    if orphan_logins:
        report["warnings"].append(
            f"login_events has {len(orphan_logins)} user_ids not in users table"
        )

    comp_ids_in_patch = set(tables["endpoint_patch_state"]["computer_id"].unique())
    valid_comp_ids = set(computers["computer_id"].unique())
    orphan_patch = comp_ids_in_patch - valid_comp_ids
    if orphan_patch:
        report["warnings"].append(
            f"endpoint_patch_state has {len(orphan_patch)} computer_ids not in computers table"
        )

    # 4. Freshness flag validity
    for tname in ["users", "computers", "assets"]:
        if tname not in tables:
            continue
        df = tables[tname]
        if "source_freshness_flag" in df.columns:
            bad = set(df["source_freshness_flag"].dropna().unique()) - VALID_FRESHNESS_FLAGS
            if bad:
                report["errors"].append(f"{tname}: invalid freshness flags: {bad}")

    # 5. Anomaly class validity
    if len(labels) > 0 and "anomaly_class" in labels.columns:
        bad_cls = set(labels["anomaly_class"].dropna().unique()) - VALID_ANOMALY_CLASSES
        if bad_cls:
            report["errors"].append(f"anomaly_labels: unknown classes: {bad_cls}")

    # 6. Label coverage: every task should have at least 1 label
    if len(labels) > 0:
        per_task = labels.groupby("benchmark_task_id").size().to_dict()
        report["anomaly_counts_per_task"] = per_task
        for task in ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]:
            if task not in per_task or per_task[task] == 0:
                report["warnings"].append(f"Task {task} has 0 anomaly labels")
    else:
        report["warnings"].append("anomaly_labels table is empty")

    # 7. Split coverage
    if "split" in labels.columns and len(labels) > 0:
        split_dist = labels["split"].value_counts().to_dict()
        report["label_split_distribution"] = split_dist
        for s in ["train", "val", "test"]:
            if split_dist.get(s, 0) == 0:
                report["warnings"].append(f"Split '{s}' has 0 anomaly labels")

    # 8. Dataset card
    card_path = os.path.join(dataset_dir, "dataset_card.json")
    if os.path.exists(card_path):
        try:
            with open(card_path) as f:
                card = json.load(f)
            report["dataset_card"] = {
                "dataset_id": card.get("dataset_id"),
                "seed": card.get("seed"),
                "condition_id": card.get("condition_id"),
                "n_users": card.get("n_users"),
                "n_anomaly_labels": card.get("n_anomaly_labels"),
            }
        except Exception as e:
            report["warnings"].append(f"Cannot parse dataset_card.json: {e}")
    else:
        report["warnings"].append("dataset_card.json not found")

    # Final verdict
    passed = len(report["errors"]) == 0
    report["passed"] = passed
    return passed, report
