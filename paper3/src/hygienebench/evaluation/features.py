"""
Feature extraction per benchmark task for HygieneBench v0.1.

Each extract_* method returns:
  entities_df  — one row per scoreable entity (entity_id as index)
  labels_s     — binary Series (1=anomalous, 0=normal), aligned to entities_df
  feature_cols — list of column names to use as ML features
  split_s      — 'train'/'val'/'test' Series, aligned to entities_df

Feature engineering is intentionally conservative (no leakage from labels).
All normalisation is deferred to methods.py (fit on train, apply to test).
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

FRESHNESS_ORD = {"fresh": 1.0, "stale_mild": 0.5, "stale_heavy": 0.2, "missing": 0.0}


def _freshness_score(s: pd.Series) -> pd.Series:
    return s.map(FRESHNESS_ORD).fillna(0.5)


def _crit_ord(s: pd.Series) -> pd.Series:
    m = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return s.map(m).fillna(2).astype(float)


def _comp_split(computer_ids: pd.Series, seed: int) -> pd.Series:
    """Deterministic 60/20/20 split for computers (no split column in computers table)."""
    rng = np.random.default_rng(seed + 1234)
    ids = computer_ids.values.tolist()
    shuffled = ids.copy()
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * 0.60)
    n_val = int(n * 0.20)
    split_map = {}
    for i, cid in enumerate(shuffled):
        if i < n_train:
            split_map[cid] = "train"
        elif i < n_train + n_val:
            split_map[cid] = "val"
        else:
            split_map[cid] = "test"
    return computer_ids.map(split_map)


class TaskFeatureExtractor:
    """Extracts per-task features and labels from a loaded dataset directory."""

    def __init__(self, dataset_dir: str):
        self.dir = dataset_dir
        self._cache: Dict[str, pd.DataFrame] = {}

    def _load(self, name: str) -> pd.DataFrame:
        if name not in self._cache:
            self._cache[name] = pd.read_csv(
                f"{self.dir}/{name}.csv", low_memory=False
            )
        return self._cache[name]

    def extract(
        self, task_id: str, seed: int = 42
    ) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        methods = {
            "T1": self._t1,
            "T2": self._t2,
            "T3": self._t3,
            "T4": self._t4,
            "T5": self._t5,
            "T6": self._t6,
            "T7": self._t7,
        }
        return methods[task_id](seed)

    # ------------------------------------------------------------------ T1
    def _t1(self, seed: int) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        users = self._load("users")
        labels = self._load("anomaly_labels")
        login = self._load("login_events")

        # Scope: all users (privileged and normal) — detect stale privileged accounts
        # Include non-privileged so detectors learn what "normal" inactivity looks like
        df = users.copy()

        # Login aggregates (30-day window proxy: last obs_window count / 3)
        login_agg = (
            login.groupby("user_id")
            .agg(
                login_count=("event_id", "count"),
                off_hours_sum=("is_off_hours", "sum"),
            )
            .reset_index()
        )
        df = df.merge(login_agg, on="user_id", how="left")
        df["login_count"] = df["login_count"].fillna(0.0)
        df["off_hours_sum"] = df["off_hours_sum"].fillna(0.0)
        df["off_hours_rate"] = np.where(
            df["login_count"] > 0, df["off_hours_sum"] / df["login_count"], 0.0
        )

        # Features
        df["freshness_score"] = _freshness_score(df["source_freshness_flag"])
        df["is_privileged_int"] = df["is_privileged"].astype(int)
        df["mfa_enabled_int"] = df["mfa_enabled"].astype(int)
        df["is_service_int"] = df["is_service_account"].astype(int)

        feat_cols = [
            "days_since_last_logon",
            "days_since_password_change",
            "privileged_group_count",
            "is_privileged_int",
            "is_service_int",
            "mfa_enabled_int",
            "login_count",
            "off_hours_rate",
            "freshness_score",
        ]
        df = df.fillna(0)

        t1_anom = labels[labels["benchmark_task_id"] == "T1"]["entity_id"].tolist()
        label_s = df["user_id"].isin(t1_anom).astype(int)
        label_s.index = df.index

        # Move anomalous users to test split
        split_s = df["split"].copy() if "split" in df.columns else pd.Series("train", index=df.index)
        split_s[df["user_id"].isin(t1_anom)] = "test"

        df = df.set_index("user_id")
        return df, label_s, feat_cols, split_s

    # ------------------------------------------------------------------ T2
    def _t2(self, seed: int) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        gme = self._load("group_membership_events")
        users = self._load("users")
        labels = self._load("anomaly_labels")

        df = gme[gme["action"] == "add"].copy()
        if len(df) == 0:
            return pd.DataFrame(), pd.Series(dtype=int), [], pd.Series(dtype=str)

        # Join user privilege info
        user_priv = users.set_index("user_id")["is_privileged"].astype(int)
        df["target_is_privileged"] = df["user_id"].map(user_priv).fillna(0)
        df["actor_is_privileged"] = df["actor_user_id"].map(user_priv).fillna(0)
        df["is_privileged_group_int"] = df["is_privileged_group"].astype(int)

        # Temporal features
        df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
        df["hour_of_day"] = df["event_timestamp"].dt.hour
        df["is_off_hours"] = ((df["hour_of_day"] < 8) | (df["hour_of_day"] >= 18)).astype(int)
        df["is_weekend"] = (df["event_timestamp"].dt.weekday >= 5).astype(int)

        feat_cols = [
            "is_privileged_group_int",
            "target_is_privileged",
            "actor_is_privileged",
            "hour_of_day",
            "is_off_hours",
            "is_weekend",
        ]

        t2_anom = labels[labels["benchmark_task_id"] == "T2"]["entity_id"].tolist()
        label_s = df["event_id"].isin(t2_anom).astype(int)
        label_s.index = df.index

        # Time-based split: first 60% = train, next 20% = val, last 20% = test
        df_sorted = df.sort_values("event_timestamp")
        n = len(df_sorted)
        splits = ["train"] * int(n * 0.6) + ["val"] * int(n * 0.2) + ["test"] * (n - int(n * 0.6) - int(n * 0.2))
        split_map = dict(zip(df_sorted.index, splits))
        split_s = df.index.map(split_map)
        split_s = pd.Series(split_s, index=df.index)
        split_s[df["event_id"].isin(t2_anom)] = "test"

        df = df.set_index("event_id")
        return df, label_s, feat_cols, split_s

    # ------------------------------------------------------------------ T3
    def _t3(self, seed: int) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        computers = self._load("computers")
        users = self._load("users")
        patch = self._load("endpoint_patch_state")
        vuln = self._load("vulnerability_records")
        labels = self._load("anomaly_labels")

        # Scope: all computers that have a primary user
        df = computers[computers["primary_user_id"].notna()].copy()
        priv_map = users.set_index("user_id")["is_privileged"]
        df["primary_user_is_privileged"] = df["primary_user_id"].map(priv_map).fillna(False).astype(int)

        # Join patch state
        patch_agg = patch.groupby("computer_id").agg(
            patch_compliance_score=("patch_compliance_score", "min"),
            critical_missing=("critical_missing_patch_count", "max"),
            open_kev=("open_kev_count", "max"),
        ).reset_index()
        df = df.merge(patch_agg, on="computer_id", how="left")

        # Join vuln: max days_open for critical/KEV CVEs
        kev_vuln = vuln[vuln["is_kev_flagged"] == True].groupby("computer_id").agg(
            max_kev_days_open=("days_open", "max"),
            kev_count=("record_id", "count"),
        ).reset_index()
        df = df.merge(kev_vuln, on="computer_id", how="left")

        df["asset_crit_ord"] = _crit_ord(df["asset_criticality"])
        df["freshness_score"] = _freshness_score(df["source_freshness_flag"])
        df = df.fillna(0)

        feat_cols = [
            "days_since_agent_heartbeat",
            "asset_crit_ord",
            "primary_user_is_privileged",
            "patch_compliance_score",
            "critical_missing",
            "open_kev",
            "max_kev_days_open",
            "kev_count",
            "freshness_score",
        ]

        t3_anom = labels[labels["benchmark_task_id"] == "T3"]["entity_id"].tolist()
        label_s = df["computer_id"].isin(t3_anom).astype(int)
        label_s.index = df.index

        split_s = _comp_split(df["computer_id"], seed)
        split_s.index = df.index
        split_s[df["computer_id"].isin(t3_anom)] = "test"

        df = df.set_index("computer_id")
        return df, label_s, feat_cols, split_s

    # ------------------------------------------------------------------ T4
    def _t4(self, seed: int) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        computers = self._load("computers")
        assets = self._load("assets")
        freshness = self._load("telemetry_freshness_log")
        labels = self._load("anomaly_labels")

        df = computers.copy()
        # Asset info
        asset_info = assets.set_index("asset_id")
        df["inventory_mismatch"] = df["computer_id"].map(
            asset_info["inventory_mismatch_flag"]
        ).fillna(False).astype(int)
        df["in_inventory"] = df["computer_id"].map(
            asset_info["in_inventory"]
        ).fillna(True).astype(int)

        # Freshness aggregates per computer
        fresh_agg = freshness.groupby("entity_id").agg(
            missing_source_count=("freshness_flag", lambda x: (x == "missing").sum()),
            max_gap_days=("actual_gap_days", "max"),
            min_freshness=("freshness_flag", lambda x: min(
                FRESHNESS_ORD.get(v, 0.5) for v in x
            )),
        ).reset_index().rename(columns={"entity_id": "computer_id"})
        df = df.merge(fresh_agg, on="computer_id", how="left")

        df["agent_installed_int"] = df["endpoint_agent_installed"].astype(int)
        df["asset_crit_ord"] = _crit_ord(df["asset_criticality"])
        df["freshness_score"] = _freshness_score(df["source_freshness_flag"])
        df = df.fillna({"missing_source_count": 0, "max_gap_days": 0, "min_freshness": 1.0})
        df = df.fillna(0)

        feat_cols = [
            "agent_installed_int",
            "days_since_agent_heartbeat",
            "inventory_mismatch",
            "in_inventory",
            "missing_source_count",
            "max_gap_days",
            "min_freshness",
            "asset_crit_ord",
            "freshness_score",
        ]

        t4_anom = labels[labels["benchmark_task_id"] == "T4"]["entity_id"].tolist()
        label_s = df["computer_id"].isin(t4_anom).astype(int)
        label_s.index = df.index

        split_s = _comp_split(df["computer_id"], seed)
        split_s.index = df.index
        split_s[df["computer_id"].isin(t4_anom)] = "test"

        df = df.set_index("computer_id")
        return df, label_s, feat_cols, split_s

    # ------------------------------------------------------------------ T5
    def _t5(self, seed: int) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        computers = self._load("computers")
        patch = self._load("endpoint_patch_state")
        vuln = self._load("vulnerability_records")
        remed = self._load("remediation_events")
        labels = self._load("anomaly_labels")

        df = computers.copy()

        # Patch state
        patch_agg = patch.groupby("computer_id").agg(
            compliance=("patch_compliance_score", "min"),
            crit_missing=("critical_missing_patch_count", "max"),
            total_missing=("missing_patch_count", "max"),
            open_kev=("open_kev_count", "max"),
            patch_lag=("days_since_last_patch_applied", "max"),
        ).reset_index()
        df = df.merge(patch_agg, on="computer_id", how="left")

        # Vulnerability: max days open for critical CVEs
        crit_vuln = vuln[vuln["cvss_severity"].isin(["critical", "high"])].groupby("computer_id").agg(
            max_crit_days_open=("days_open", "max"),
            crit_cve_count=("record_id", "count"),
            kev_count=("is_kev_flagged", "sum"),
        ).reset_index()
        df = df.merge(crit_vuln, on="computer_id", how="left")

        # Remediation: max latency for deferred/open items
        remed_agg = remed.groupby("computer_id").agg(
            max_rem_latency=("remediation_latency_days", "max"),
        ).reset_index()
        df = df.merge(remed_agg, on="computer_id", how="left")

        df["asset_crit_ord"] = _crit_ord(df["asset_criticality"])
        df = df.fillna(0)

        feat_cols = [
            "compliance",
            "crit_missing",
            "total_missing",
            "open_kev",
            "patch_lag",
            "max_crit_days_open",
            "crit_cve_count",
            "kev_count",
            "max_rem_latency",
            "asset_crit_ord",
        ]

        t5_anom = labels[labels["benchmark_task_id"] == "T5"]["entity_id"].tolist()
        label_s = df["computer_id"].isin(t5_anom).astype(int)
        label_s.index = df.index

        split_s = _comp_split(df["computer_id"], seed)
        split_s.index = df.index
        split_s[df["computer_id"].isin(t5_anom)] = "test"

        df = df.set_index("computer_id")
        return df, label_s, feat_cols, split_s

    # ------------------------------------------------------------------ T6
    def _t6(self, seed: int) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        users = self._load("users")
        lifecycle = self._load("account_lifecycle_events")
        login = self._load("login_events")
        labels = self._load("anomaly_labels")

        df = users.copy()

        # Reactivation events per user
        react = lifecycle[lifecycle["action"] == "reactivated"].copy()
        react["dormant_days"] = pd.to_numeric(
            react["days_since_last_logon_at_action"], errors="coerce"
        ).fillna(0)
        react_agg = react.groupby("user_id").agg(
            was_reactivated=("event_id", "count"),
            dormant_days_at_react=("dormant_days", "max"),
        ).reset_index()
        df = df.merge(react_agg, on="user_id", how="left")
        df["was_reactivated"] = df["was_reactivated"].fillna(0).astype(int)
        df["dormant_days_at_react"] = df["dormant_days_at_react"].fillna(0)

        # Post-reactivation login patterns (off-hours, cross-segment)
        login_agg = login.groupby("user_id").agg(
            total_logins=("event_id", "count"),
            off_hours_logins=("is_off_hours", "sum"),
            cross_seg_logins=("is_cross_segment", "sum"),
            anomalous_logins=("is_anomalous", "sum"),
        ).reset_index()
        df = df.merge(login_agg, on="user_id", how="left")
        df["total_logins"] = df["total_logins"].fillna(0)
        df["off_hours_logins"] = df["off_hours_logins"].fillna(0)
        df["cross_seg_logins"] = df["cross_seg_logins"].fillna(0)
        df["anomalous_logins"] = df["anomalous_logins"].fillna(0)
        df["off_hours_rate"] = np.where(
            df["total_logins"] > 0, df["off_hours_logins"] / df["total_logins"], 0
        )
        df["cross_seg_rate"] = np.where(
            df["total_logins"] > 0, df["cross_seg_logins"] / df["total_logins"], 0
        )

        df["is_privileged_int"] = df["is_privileged"].astype(int)
        df["freshness_score"] = _freshness_score(df["source_freshness_flag"])
        df = df.fillna(0)

        feat_cols = [
            "days_since_last_logon",
            "was_reactivated",
            "dormant_days_at_react",
            "off_hours_rate",
            "cross_seg_rate",
            "total_logins",
            "is_privileged_int",
            "freshness_score",
        ]

        t6_anom = labels[labels["benchmark_task_id"] == "T6"]["entity_id"].tolist()
        label_s = df["user_id"].isin(t6_anom).astype(int)
        label_s.index = df.index

        split_s = df["split"].copy() if "split" in df.columns else pd.Series("train", index=df.index)
        split_s[df["user_id"].isin(t6_anom)] = "test"

        df = df.set_index("user_id")
        return df, label_s, feat_cols, split_s

    # ------------------------------------------------------------------ T7
    def _t7(self, seed: int) -> Tuple[pd.DataFrame, pd.Series, List[str], pd.Series]:
        users = self._load("users")
        gme = self._load("group_membership_events")
        groups = self._load("groups")
        lifecycle = self._load("account_lifecycle_events")
        labels = self._load("anomaly_labels")

        df = users.copy()
        priv_groups = set(groups[groups["is_privileged"]]["group_id"].tolist())

        adds = gme[gme["action"] == "add"].copy()
        adds["event_timestamp"] = pd.to_datetime(adds["event_timestamp"])
        adds["is_priv_add"] = adds["group_id"].isin(priv_groups).astype(int)

        # Aggregate per user over observation window (all adds)
        agg = adds.groupby("user_id").agg(
            total_adds=("event_id", "count"),
            priv_adds=("is_priv_add", "sum"),
            unique_days=("event_timestamp", lambda x: x.dt.date.nunique()),
        ).reset_index()
        df = df.merge(agg, on="user_id", how="left")
        df["total_adds"] = df["total_adds"].fillna(0)
        df["priv_adds"] = df["priv_adds"].fillna(0)
        df["unique_days"] = df["unique_days"].fillna(0)

        # Has any role-change lifecycle event?
        role_events = lifecycle[lifecycle["action"].isin(["enabled", "created"])]["user_id"].unique()
        df["has_role_event"] = df["user_id"].isin(role_events).astype(int)

        # Rate of priv adds (per week proxy)
        df["priv_add_rate"] = df["priv_adds"] / 13.0  # 90 days / 7

        df["is_privileged_int"] = df["is_privileged"].astype(int)
        df["current_priv_group_count"] = df["privileged_group_count"]
        df = df.fillna(0)

        feat_cols = [
            "total_adds",
            "priv_adds",
            "priv_add_rate",
            "unique_days",
            "has_role_event",
            "is_privileged_int",
            "current_priv_group_count",
            "days_since_last_logon",
        ]

        t7_anom = labels[labels["benchmark_task_id"] == "T7"]["entity_id"].tolist()
        label_s = df["user_id"].isin(t7_anom).astype(int)
        label_s.index = df.index

        split_s = df["split"].copy() if "split" in df.columns else pd.Series("train", index=df.index)
        split_s[df["user_id"].isin(t7_anom)] = "test"

        df = df.set_index("user_id")
        return df, label_s, feat_cols, split_s
