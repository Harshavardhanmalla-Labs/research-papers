"""
SyntheticHygieneGenerator — core synthetic telemetry generator for HygieneBench v0.1.

Generates all entity and event tables per SCHEMA_v0_1.md.
Anomaly injection is handled by injector.py.
All generation is deterministic given config.seed.
"""

from __future__ import annotations
import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from hygienebench.config import GeneratorConfig, ConditionConfig
from hygienebench.schema import (
    FreshnessFlag, AssetCriticality, OsType, NetworkSegment,
    GroupType, LogonType, AccountAction, RemediationAction,
    cvss_to_severity, CRITICALITY_ORDINAL
)


# ---------------------------------------------------------------------------
# Reference dates (fixed; all synthetic data relative to these)
# ---------------------------------------------------------------------------
REF_DATE = datetime(2024, 1, 1)  # T=0, start of observation window


@dataclass
class SyntheticHygieneDataset:
    """Container for all generated tables. All DataFrames match SCHEMA_v0_1.md."""
    users: pd.DataFrame
    groups: pd.DataFrame
    computers: pd.DataFrame
    assets: pd.DataFrame
    login_events: pd.DataFrame
    group_membership_events: pd.DataFrame
    endpoint_patch_state: pd.DataFrame
    vulnerability_records: pd.DataFrame
    remediation_events: pd.DataFrame
    account_lifecycle_events: pd.DataFrame
    telemetry_freshness_log: pd.DataFrame
    anomaly_labels: pd.DataFrame  # populated by injector.py; empty until injection
    config: GeneratorConfig
    dataset_id: str = ""

    def save(self, output_dir: str) -> None:
        """Save all tables as CSV files."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        for name in [
            "users", "groups", "computers", "assets",
            "login_events", "group_membership_events",
            "endpoint_patch_state", "vulnerability_records",
            "remediation_events", "account_lifecycle_events",
            "telemetry_freshness_log", "anomaly_labels",
        ]:
            df: pd.DataFrame = getattr(self, name)
            df.to_csv(os.path.join(output_dir, f"{name}.csv"), index=False)

    def summary(self) -> Dict:
        """Return a brief summary dict for dataset card generation."""
        return {
            "n_users": len(self.users),
            "n_groups": len(self.groups),
            "n_computers": len(self.computers),
            "n_assets": len(self.assets),
            "n_login_events": len(self.login_events),
            "n_group_membership_events": len(self.group_membership_events),
            "n_endpoint_patch_records": len(self.endpoint_patch_state),
            "n_vulnerability_records": len(self.vulnerability_records),
            "n_remediation_events": len(self.remediation_events),
            "n_account_lifecycle_events": len(self.account_lifecycle_events),
            "n_telemetry_freshness_records": len(self.telemetry_freshness_log),
            "n_anomaly_labels": len(self.anomaly_labels),
            "anomaly_class_counts": (
                self.anomaly_labels.groupby("anomaly_class")
                .size().to_dict() if len(self.anomaly_labels) > 0 else {}
            ),
        }


# ---------------------------------------------------------------------------
# Helper: deterministic UUID from seed + namespace + index
# ---------------------------------------------------------------------------
def _make_id(seed_tag: str, idx: int) -> str:
    raw = f"{seed_tag}:{idx}".encode()
    h = hashlib.md5(raw, usedforsecurity=False).hexdigest()
    return str(uuid.UUID(h))


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
class SyntheticHygieneGenerator:
    """
    Generates a fully synthetic HygieneBench dataset.

    Usage:
        config = GeneratorConfig.medium(seed=42, condition=ConditionConfig.c_base())
        gen    = SyntheticHygieneGenerator(config)
        ds     = gen.generate()
    """

    def __init__(self, config: GeneratorConfig):
        self.cfg = config
        self.rng = np.random.default_rng(config.seed)
        self._seed_tag = str(config.seed)
        self.obs_start = REF_DATE
        self.obs_end = REF_DATE + timedelta(days=config.obs_window_days)
        self.hist_start = REF_DATE - timedelta(days=config.history_days)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self) -> SyntheticHygieneDataset:
        groups = self._gen_groups()
        users = self._gen_users(groups)
        computers = self._gen_computers(users)
        assets = self._gen_assets(computers)
        base_memberships = self._gen_base_memberships(users, groups)

        login_events = self._gen_login_events(users, computers)
        group_events = self._gen_group_membership_events(users, groups, base_memberships)
        lifecycle_events = self._gen_account_lifecycle_events(users)
        patch_state = self._gen_endpoint_patch_state(computers)
        vuln_records = self._gen_vulnerability_records(computers)
        remediation_events = self._gen_remediation_events(vuln_records)
        freshness_log = self._gen_telemetry_freshness(users, computers, assets)

        # Apply condition (freshness/missingness regime)
        users, computers, assets, patch_state, vuln_records, freshness_log = \
            self._apply_condition(users, computers, assets, patch_state, vuln_records, freshness_log)

        dataset_id = (f"hygienebench_{self.cfg.generator_version}_"
                      f"{self.cfg.condition.condition_id}_"
                      f"seed{self.cfg.seed}_"
                      f"n{self.cfg.population.n_users}")

        return SyntheticHygieneDataset(
            users=users,
            groups=groups,
            computers=computers,
            assets=assets,
            login_events=login_events,
            group_membership_events=group_events,
            endpoint_patch_state=patch_state,
            vulnerability_records=vuln_records,
            remediation_events=remediation_events,
            account_lifecycle_events=lifecycle_events,
            telemetry_freshness_log=freshness_log,
            anomaly_labels=pd.DataFrame(),  # filled by AnomalyInjector
            config=self.cfg,
            dataset_id=dataset_id,
        )

    # ------------------------------------------------------------------
    # Groups (E2)
    # ------------------------------------------------------------------
    def _gen_groups(self) -> pd.DataFrame:
        pc = self.cfg.population
        rows = []

        dept_names = ["Finance", "Engineering", "IT", "HR", "Legal", "Operations", "Security", "Executive"]
        dept_names = dept_names[:pc.n_departments]

        # Privileged groups
        priv_names = ["Domain Admins", "Enterprise Admins", "Schema Admins",
                      "Account Operators", "Backup Operators", "Server Operators",
                      "Print Operators", "DNS Admins"]
        for i in range(pc.n_privileged_groups):
            gid = _make_id(f"{self._seed_tag}:group:priv", i)
            rows.append({
                "group_id": gid,
                "group_name": priv_names[i % len(priv_names)],
                "group_type": GroupType.SECURITY.value,
                "is_privileged": True,
                "member_count": 0,  # filled after user assignment
                "ou_path": f"OU=PrivilegedGroups,DC=corp,DC=local",
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": self.obs_start.isoformat(),
            })

        # Business security groups
        for i in range(pc.n_business_groups):
            dept = dept_names[i % len(dept_names)]
            gid = _make_id(f"{self._seed_tag}:group:biz", i)
            rows.append({
                "group_id": gid,
                "group_name": f"{dept}_Staff_{i:03d}",
                "group_type": GroupType.SECURITY.value,
                "is_privileged": False,
                "member_count": 0,
                "ou_path": f"OU={dept},DC=corp,DC=local",
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": self.obs_start.isoformat(),
            })

        # Distribution groups
        for i in range(pc.n_distribution_groups):
            dept = dept_names[i % len(dept_names)]
            gid = _make_id(f"{self._seed_tag}:group:dist", i)
            rows.append({
                "group_id": gid,
                "group_name": f"{dept}_DL_{i:03d}",
                "group_type": GroupType.DISTRIBUTION.value,
                "is_privileged": False,
                "member_count": 0,
                "ou_path": f"OU={dept},DC=corp,DC=local",
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": self.obs_start.isoformat(),
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Users (E1)
    # ------------------------------------------------------------------
    def _gen_users(self, groups: pd.DataFrame) -> pd.DataFrame:
        pc = self.cfg.population
        n = pc.n_users
        rng = self.rng

        dept_names = ["Finance", "Engineering", "IT", "HR", "Legal", "Operations", "Security", "Executive"]
        dept_names = dept_names[:pc.n_departments]

        n_privileged = max(1, int(n * pc.privileged_user_rate))
        n_service = max(1, int(n * pc.service_account_rate))
        n_regular = n - n_privileged - n_service

        user_types = (
            ["privileged"] * n_privileged
            + ["service"] * n_service
            + ["regular"] * n_regular
        )
        rng.shuffle(user_types)

        priv_groups = groups[groups["is_privileged"]]["group_id"].tolist()

        rows = []
        for i in range(n):
            uid = _make_id(f"{self._seed_tag}:user", i)
            dept = dept_names[rng.integers(0, len(dept_names))]
            utype = user_types[i]

            is_privileged = utype == "privileged"
            is_service = utype == "service"

            # Account creation: 1-4 years before obs window
            created_days_ago = int(rng.integers(365, 4 * 365))
            created_at = self.obs_start - timedelta(days=created_days_ago)

            # Last logon: service accounts log in frequently; regular users less so
            if is_service:
                last_logon_days = float(rng.exponential(0.5))  # very recent
            elif is_privileged:
                last_logon_days = float(rng.lognormal(1.5, 0.7))  # ~4-5 days typical
            else:
                last_logon_days = float(rng.lognormal(1.8, 0.8))  # ~6 days typical

            last_logon_days = max(0.1, last_logon_days)
            last_logon = self.obs_start - timedelta(days=last_logon_days)

            # Password last set
            pwd_days_ago = int(rng.integers(1, 180))

            # MFA: 75% enabled for privileged, 55% for regular
            mfa = bool(rng.random() < (0.75 if is_privileged else 0.55))

            # Privileged group assignment
            priv_group_count = 0
            if is_privileged and len(priv_groups) > 0:
                priv_group_count = int(rng.integers(1, min(3, len(priv_groups)) + 1))

            # Account enabled: 97% for regular/priv, 100% for service
            enabled = bool(rng.random() < (1.0 if is_service else 0.97))

            rows.append({
                "user_id": uid,
                "username": f"user_{i:05d}" if not is_service else f"svc_{i:05d}",
                "display_name": f"Synthetic User {i:05d}",
                "department": dept,
                "ou_path": f"OU={dept},DC=corp,DC=local",
                "account_enabled": enabled,
                "account_created_at": created_at.isoformat(),
                "account_last_logon": last_logon.isoformat(),
                "days_since_last_logon": round(last_logon_days, 1),
                "is_privileged": is_privileged,
                "privileged_group_count": priv_group_count,
                "is_service_account": is_service,
                "password_last_set": (self.obs_start - timedelta(days=pwd_days_ago)).isoformat(),
                "days_since_password_change": pwd_days_ago,
                "mfa_enabled": mfa,
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": self.obs_start.isoformat(),
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Computers (E3)
    # ------------------------------------------------------------------
    def _gen_computers(self, users: pd.DataFrame) -> pd.DataFrame:
        pc = self.cfg.population
        rng = self.rng
        regular_users = users[~users["is_service_account"]]["user_id"].tolist()

        n_workstations = int(len(regular_users) * pc.computers_per_user_ratio)
        n_servers = pc.n_extra_servers
        n_total = n_workstations + n_servers

        rows = []
        # Workstations
        for i in range(n_workstations):
            cid = _make_id(f"{self._seed_tag}:computer", i)
            primary_user = regular_users[i] if i < len(regular_users) else None
            criticality_roll = rng.random()
            if criticality_roll < 0.07:
                crit = AssetCriticality.CRITICAL
            elif criticality_roll < 0.25:
                crit = AssetCriticality.HIGH
            elif criticality_roll < 0.70:
                crit = AssetCriticality.MEDIUM
            else:
                crit = AssetCriticality.LOW

            heartbeat_days = float(rng.exponential(2.0))  # ~2-day mean heartbeat lag
            heartbeat_days = max(0.1, heartbeat_days)

            rows.append({
                "computer_id": cid,
                "hostname": f"ws-{i:05d}",
                "os_type": OsType.WINDOWS_WORKSTATION.value,
                "os_version": "Windows 11 22H2",
                "network_segment": NetworkSegment.WORKSTATION.value,
                "primary_user_id": primary_user,
                "asset_criticality": crit.value,
                "endpoint_agent_installed": True,
                "endpoint_agent_last_heartbeat": (
                    self.obs_start - timedelta(days=heartbeat_days)).isoformat(),
                "days_since_agent_heartbeat": round(heartbeat_days, 1),
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": self.obs_start.isoformat(),
            })

        # Servers
        for i in range(n_servers):
            cid = _make_id(f"{self._seed_tag}:computer:srv", i)
            criticality_roll = rng.random()
            if criticality_roll < 0.25:
                crit = AssetCriticality.CRITICAL
            elif criticality_roll < 0.60:
                crit = AssetCriticality.HIGH
            else:
                crit = AssetCriticality.MEDIUM

            seg = NetworkSegment.SERVER if rng.random() < 0.7 else NetworkSegment.DMZ
            heartbeat_days = float(rng.exponential(1.5))
            heartbeat_days = max(0.1, heartbeat_days)

            os_choice = OsType.WINDOWS_SERVER if rng.random() < 0.6 else OsType.LINUX_SERVER

            rows.append({
                "computer_id": cid,
                "hostname": f"srv-{i:05d}",
                "os_type": os_choice.value,
                "os_version": "Windows Server 2022" if os_choice == OsType.WINDOWS_SERVER else "RHEL 9",
                "network_segment": seg.value,
                "primary_user_id": None,
                "asset_criticality": crit.value,
                "endpoint_agent_installed": bool(rng.random() < 0.95),
                "endpoint_agent_last_heartbeat": (
                    self.obs_start - timedelta(days=heartbeat_days)).isoformat(),
                "days_since_agent_heartbeat": round(heartbeat_days, 1),
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": self.obs_start.isoformat(),
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Assets (E4) — mirrors computers with some extras
    # ------------------------------------------------------------------
    def _gen_assets(self, computers: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, c in computers.iterrows():
            rows.append({
                "asset_id": c["computer_id"],
                "asset_type": "endpoint" if c["os_type"] == OsType.WINDOWS_WORKSTATION.value else "server",
                "asset_criticality": c["asset_criticality"],
                "owner_ou": "OU=Workstations,DC=corp,DC=local",
                "in_inventory": True,
                "in_endpoint_mgmt": bool(c["endpoint_agent_installed"]),
                "inventory_mismatch_flag": False,
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": c["last_updated_at"],
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Base group memberships (internal state, not an event table)
    # ------------------------------------------------------------------
    def _gen_base_memberships(self, users: pd.DataFrame, groups: pd.DataFrame) -> pd.DataFrame:
        """Returns a mapping of user_id -> list[group_id] at T=0."""
        rng = self.rng
        priv_groups = groups[groups["is_privileged"]]["group_id"].tolist()
        biz_groups = groups[~groups["is_privileged"] & (groups["group_type"] == GroupType.SECURITY.value)]["group_id"].tolist()

        records = []
        for _, u in users.iterrows():
            uid = u["user_id"]
            dept = u["department"]

            # Each user gets 1-3 business security groups matching their dept
            dept_biz = [g for g in biz_groups if dept in groups.loc[groups["group_id"] == g, "group_name"].values[0]] if biz_groups else biz_groups
            if not dept_biz:
                dept_biz = biz_groups
            n_biz = int(rng.integers(1, min(4, len(dept_biz) + 1)))
            chosen_biz = rng.choice(dept_biz, size=min(n_biz, len(dept_biz)), replace=False).tolist()
            for gid in chosen_biz:
                records.append({"user_id": uid, "group_id": gid})

            # Privileged users also get privileged group membership
            if u["is_privileged"] and u["privileged_group_count"] > 0 and priv_groups:
                n_priv = min(u["privileged_group_count"], len(priv_groups))
                chosen_priv = rng.choice(priv_groups, size=n_priv, replace=False).tolist()
                for gid in chosen_priv:
                    records.append({"user_id": uid, "group_id": gid})

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Login events (R1)
    # ------------------------------------------------------------------
    def _gen_login_events(self, users: pd.DataFrame, computers: pd.DataFrame) -> pd.DataFrame:
        rng = self.rng
        computer_ids = computers["computer_id"].tolist()
        user_computer = dict(zip(
            computers["primary_user_id"].dropna(),
            computers["computer_id"]
        ))
        computer_seg = dict(zip(computers["computer_id"], computers["network_segment"]))

        obs_days = self.cfg.obs_window_days
        rows = []

        for _, u in users.iterrows():
            uid = u["user_id"]
            is_svc = u["is_service_account"]
            is_priv = u["is_privileged"]
            enabled = u["account_enabled"]

            if not enabled:
                continue

            # Daily login rate
            if is_svc:
                daily_rate = rng.uniform(2.0, 8.0)
            elif is_priv:
                daily_rate = rng.uniform(4.0, 10.0)
            else:
                daily_rate = rng.uniform(1.5, 6.0)

            n_logins = int(rng.poisson(daily_rate * obs_days * 5 / 7))
            if n_logins == 0:
                continue

            # Assign timestamps within obs window
            timestamps = []
            for _ in range(n_logins):
                day_offset = rng.integers(0, obs_days)
                dt = self.obs_start + timedelta(days=int(day_offset))
                is_biz_day = dt.weekday() < 5
                is_off_hours = not (is_biz_day and (8 <= rng.integers(0, 24) < 18))
                hour = int(rng.integers(8, 18)) if not is_off_hours and is_biz_day else int(rng.integers(0, 24))
                minute = int(rng.integers(0, 60))
                ts = dt.replace(hour=hour, minute=minute)
                timestamps.append(ts)

            primary_computer = user_computer.get(uid)
            primary_seg = computer_seg.get(primary_computer, NetworkSegment.WORKSTATION.value) if primary_computer else NetworkSegment.WORKSTATION.value

            for ts in timestamps:
                # 90% on primary computer, 10% on other
                if primary_computer and rng.random() < 0.90:
                    cid = primary_computer
                    cross_seg = False
                else:
                    cid = computer_ids[int(rng.integers(0, len(computer_ids)))]
                    cross_seg = (computer_seg.get(cid, "") != primary_seg)

                is_off_h = ts.hour < 8 or ts.hour >= 18 or ts.weekday() >= 5
                success = bool(rng.random() < 0.97)
                logon_type = LogonType.SERVICE.value if is_svc else (
                    LogonType.REMOTE_INTERACTIVE.value if rng.random() < 0.1 else LogonType.INTERACTIVE.value
                )

                eid = _make_id(f"{self._seed_tag}:login:{uid}", len(rows))
                rows.append({
                    "event_id": eid,
                    "user_id": uid,
                    "computer_id": cid,
                    "event_timestamp": ts.isoformat(),
                    "logon_type": logon_type,
                    "success": success,
                    "is_off_hours": is_off_h,
                    "is_cross_segment": cross_seg,
                    "is_anomalous": False,
                    "anomaly_class": None,
                })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Group membership events (R2)
    # ------------------------------------------------------------------
    def _gen_group_membership_events(
        self, users: pd.DataFrame, groups: pd.DataFrame, base_memberships: pd.DataFrame
    ) -> pd.DataFrame:
        rng = self.rng
        priv_users = users[users["is_privileged"]]["user_id"].tolist()
        all_users = users["user_id"].tolist()
        all_groups = groups["group_id"].tolist()
        obs_days = self.cfg.obs_window_days

        rows = []
        # Normal background group changes: ~0.3% of users per week get a change
        n_changes = max(1, int(len(all_users) * 0.003 * (obs_days / 7)))
        actors = rng.choice(priv_users, size=min(n_changes, len(priv_users)), replace=True).tolist() if priv_users else all_users

        for i in range(n_changes):
            target_user = all_users[int(rng.integers(0, len(all_users)))]
            group = all_groups[int(rng.integers(0, len(all_groups)))]
            actor = actors[i % len(actors)]
            day_offset = int(rng.integers(0, obs_days))
            ts = self.obs_start + timedelta(days=day_offset, hours=int(rng.integers(9, 17)))
            eid = _make_id(f"{self._seed_tag}:gmem", i)
            rows.append({
                "event_id": eid,
                "user_id": target_user,
                "group_id": group,
                "action": "add",
                "event_timestamp": ts.isoformat(),
                "actor_user_id": actor,
                "is_privileged_group": bool(groups.loc[groups["group_id"] == group, "is_privileged"].values[0]) if group in groups["group_id"].values else False,
                "is_anomalous": False,
                "anomaly_class": None,
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Account lifecycle events (R6)
    # ------------------------------------------------------------------
    def _gen_account_lifecycle_events(self, users: pd.DataFrame) -> pd.DataFrame:
        rng = self.rng
        priv_users = users[users["is_privileged"]]["user_id"].tolist()
        all_users = users["user_id"].tolist()
        obs_days = self.cfg.obs_window_days
        rows = []

        # Background: ~0.2% of accounts created/disabled per month
        n_events = max(2, int(len(all_users) * 0.002 * (obs_days / 30)))
        actor = priv_users[0] if priv_users else all_users[0]

        for i in range(n_events):
            uid = all_users[int(rng.integers(0, len(all_users)))]
            action_roll = rng.random()
            if action_roll < 0.5:
                action = AccountAction.CREATED.value
            elif action_roll < 0.7:
                action = AccountAction.DISABLED.value
            elif action_roll < 0.85:
                action = AccountAction.PASSWORD_RESET.value
            else:
                action = AccountAction.ENABLED.value

            day_offset = int(rng.integers(0, obs_days))
            ts = self.obs_start + timedelta(days=day_offset, hours=int(rng.integers(9, 17)))
            eid = _make_id(f"{self._seed_tag}:lifecycle", i)
            rows.append({
                "event_id": eid,
                "user_id": uid,
                "action": action,
                "event_timestamp": ts.isoformat(),
                "actor_user_id": actor,
                "days_since_last_logon_at_action": None,  # filled for reactivation anomalies
                "is_anomalous": False,
                "anomaly_class": None,
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Endpoint patch state (R3)
    # ------------------------------------------------------------------
    def _gen_endpoint_patch_state(self, computers: pd.DataFrame) -> pd.DataFrame:
        pc_cfg = self.cfg.patch
        rng = self.rng
        rows = []

        for _, c in computers.iterrows():
            cid = c["computer_id"]
            # Compliance drawn from beta distribution (concentrated near baseline)
            compliance = float(rng.beta(
                pc_cfg.baseline_compliance_rate * 10,
                (1 - pc_cfg.baseline_compliance_rate) * 10
            ))
            compliance = float(np.clip(compliance, 0.0, 1.0))

            missing_critical = max(0, int(rng.poisson((1 - compliance) * 3)))
            open_kev = 1 if (rng.random() < pc_cfg.kev_rate and missing_critical > 0) else 0

            # Patch lag (from DBIR 2026 priors)
            lag = float(rng.lognormal(
                np.log(pc_cfg.critical_patch_lag_mean_days),
                pc_cfg.critical_patch_lag_std_days / pc_cfg.critical_patch_lag_mean_days
            ))
            lag = float(np.clip(lag, 0.0, 180.0))

            rid = _make_id(f"{self._seed_tag}:patch", len(rows))
            rows.append({
                "record_id": rid,
                "computer_id": cid,
                "snapshot_timestamp": self.obs_start.isoformat(),
                "missing_patch_count": missing_critical + int(rng.poisson(2.0)),
                "critical_missing_patch_count": missing_critical,
                "patch_compliance_score": round(compliance, 3),
                "days_since_last_patch_applied": round(lag, 1),
                "open_kev_count": open_kev,
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": self.obs_start.isoformat(),
                "is_anomalous": False,
                "anomaly_class": None,
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Vulnerability records (R4)
    # ------------------------------------------------------------------
    def _gen_vulnerability_records(self, computers: pd.DataFrame) -> pd.DataFrame:
        pc_cfg = self.cfg.patch
        rng = self.rng
        rows = []

        for _, c in computers.iterrows():
            cid = c["computer_id"]
            n_cves = max(0, int(rng.poisson(pc_cfg.mean_open_cves_per_host)))
            n_cves = min(n_cves, pc_cfg.max_open_cves_per_host)

            for j in range(n_cves):
                # CVSS score from truncated normal shaped to NVD distribution
                score = float(rng.normal(pc_cfg.cvss_score_mean, pc_cfg.cvss_score_std))
                score = float(np.clip(score, 1.0, 10.0))
                severity = cvss_to_severity(score)
                is_kev = bool(rng.random() < pc_cfg.kev_rate)

                # Days open: higher CVSS tends toward shorter open duration (patched faster)
                base_lag = pc_cfg.critical_patch_lag_mean_days if score >= 9.0 else (
                    pc_cfg.high_patch_lag_mean_days if score >= 7.0 else pc_cfg.medium_patch_lag_mean_days
                )
                days_open = float(rng.lognormal(np.log(max(1, base_lag)), 0.7))
                days_open = float(np.clip(days_open, 0.0, 365.0))

                cve_pub_days_ago = int(rng.integers(int(days_open), int(days_open) + 180))
                first_observed = self.obs_start - timedelta(days=days_open)

                rem_status = "open"
                if rng.random() < 0.15:
                    rem_status = rng.choice(["patched", "deferred", "false_positive"],
                                             p=[0.7, 0.2, 0.1])

                exposed_priv = 0
                if c["primary_user_id"] is not None:
                    exposed_priv = 1  # simplified: 1 if host has a primary user

                rid = _make_id(f"{self._seed_tag}:vuln:{cid}", j)
                rows.append({
                    "record_id": rid,
                    "computer_id": cid,
                    "cve_id": f"CVE-SYNTH-2024-{abs(hash(rid)) % 90000:05d}",
                    "cvss_score": round(score, 1),
                    "cvss_severity": severity,
                    "is_kev_flagged": is_kev,
                    "cve_published_days_ago": cve_pub_days_ago,
                    "first_observed_at": first_observed.isoformat(),
                    "days_open": round(days_open, 1),
                    "remediation_status": rem_status,
                    "asset_criticality": c["asset_criticality"],
                    "exposed_privileged_user_count": exposed_priv,
                    "source_freshness_flag": FreshnessFlag.FRESH.value,
                    "last_updated_at": self.obs_start.isoformat(),
                    "is_anomalous": False,
                    "anomaly_class": None,
                })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Remediation events (R5)
    # ------------------------------------------------------------------
    def _gen_remediation_events(self, vuln_records: pd.DataFrame) -> pd.DataFrame:
        rng = self.rng
        rows = []
        patched = vuln_records[vuln_records["remediation_status"] == "patched"]

        for idx, v in patched.iterrows():
            days_open = float(v["days_open"])
            rem_day = max(0, self.obs_start.timestamp() - days_open * 86400)
            ts = datetime.fromtimestamp(rem_day)
            if ts < self.hist_start:
                ts = self.hist_start

            eid = _make_id(f"{self._seed_tag}:rem", len(rows))
            rows.append({
                "event_id": eid,
                "computer_id": v["computer_id"],
                "cve_id": v["cve_id"],
                "action_type": RemediationAction.PATCH_APPLIED.value,
                "action_timestamp": ts.isoformat(),
                "actor_type": "automated" if rng.random() < 0.6 else "manual",
                "remediation_latency_days": round(days_open, 1),
                "is_anomalous": False,
                "anomaly_class": None,
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Telemetry freshness log (R7)
    # ------------------------------------------------------------------
    def _gen_telemetry_freshness(
        self,
        users: pd.DataFrame,
        computers: pd.DataFrame,
        assets: pd.DataFrame,
    ) -> pd.DataFrame:
        rng = self.rng
        rows = []
        sources = {
            "ad_events": 1,      # expected refresh every 1 day
            "edr_agent": 7,      # expected every 7 days (BOD 23-01 anchor)
            "patch_mgmt": 7,
            "vuln_scanner": 14,  # expected every 14 days
            "asset_inventory": 14,
        }

        def _add_freshness(eid, etype, source, expected_days):
            actual_gap = float(rng.exponential(expected_days * 0.8))
            actual_gap = max(0.1, actual_gap)
            if actual_gap <= expected_days:
                flag = FreshnessFlag.FRESH.value
            elif actual_gap <= expected_days * 2:
                flag = FreshnessFlag.STALE_MILD.value
            else:
                flag = FreshnessFlag.STALE_HEAVY.value
            lid = _make_id(f"{self._seed_tag}:fresh:{eid}:{source}", len(rows))
            rows.append({
                "log_id": lid,
                "entity_type": etype,
                "entity_id": eid,
                "source_system": source,
                "expected_refresh_interval_days": expected_days,
                "actual_gap_days": round(actual_gap, 1),
                "freshness_flag": flag,
                "observation_timestamp": self.obs_start.isoformat(),
                "is_anomalous": False,
                "anomaly_class": None,
            })

        for _, u in users.iterrows():
            _add_freshness(u["user_id"], "user", "ad_events", sources["ad_events"])

        for _, c in computers.iterrows():
            for src, days in [("edr_agent", 7), ("patch_mgmt", 7), ("vuln_scanner", 14)]:
                _add_freshness(c["computer_id"], "computer", src, days)

        for _, a in assets.iterrows():
            _add_freshness(a["asset_id"], "asset", "asset_inventory", sources["asset_inventory"])

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Apply condition (freshness/missingness regime)
    # ------------------------------------------------------------------
    def _apply_condition(
        self,
        users: pd.DataFrame,
        computers: pd.DataFrame,
        assets: pd.DataFrame,
        patch_state: pd.DataFrame,
        vuln_records: pd.DataFrame,
        freshness_log: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        cond = self.cfg.condition
        rng = self.rng

        if cond.condition_id == "c_base":
            return users, computers, assets, patch_state, vuln_records, freshness_log

        n_users = len(users)
        n_computers = len(computers)

        # Apply staleness to a fraction of entities
        if cond.stale_rate > 0.0 and cond.stale_severity != "fresh":
            stale_user_mask = rng.random(n_users) < cond.stale_rate
            stale_comp_mask = rng.random(n_computers) < cond.stale_rate

            users = users.copy()
            computers = computers.copy()

            users.loc[stale_user_mask, "source_freshness_flag"] = cond.stale_severity
            computers.loc[stale_comp_mask, "source_freshness_flag"] = cond.stale_severity

            # For C-STALE: add noise to days_since_last_logon for stale users
            if cond.stale_severity == "stale_heavy":
                stale_idx = users.index[stale_user_mask]
                extra_days = rng.uniform(14, 60, size=len(stale_idx))
                users.loc[stale_idx, "days_since_last_logon"] = (
                    users.loc[stale_idx, "days_since_last_logon"] + extra_days
                ).clip(lower=0)

            # Update freshness log for affected entities
            freshness_log = freshness_log.copy()
            stale_user_ids = set(users[stale_user_mask]["user_id"].tolist())
            stale_comp_ids = set(computers[stale_comp_mask]["computer_id"].tolist())
            freshness_log.loc[
                freshness_log["entity_id"].isin(stale_user_ids | stale_comp_ids),
                "freshness_flag"
            ] = cond.stale_severity

        # Apply source missingness
        if cond.missing_sources and cond.missing_source_rate > 0.0:
            freshness_log = freshness_log.copy()
            patch_state = patch_state.copy()
            for src in cond.missing_sources:
                mask = (
                    (freshness_log["source_system"] == src)
                    & (rng.random(len(freshness_log)) < cond.missing_source_rate)
                )
                freshness_log.loc[mask, "freshness_flag"] = FreshnessFlag.MISSING.value
                freshness_log.loc[mask, "actual_gap_days"] = 9999.0

                # Also mark patch_state as missing for affected computers if patch_mgmt missing
                if src == "patch_mgmt":
                    missing_comp_ids = set(
                        freshness_log.loc[mask & (freshness_log["entity_type"] == "computer"), "entity_id"]
                    )
                    patch_state.loc[
                        patch_state["computer_id"].isin(missing_comp_ids),
                        "source_freshness_flag"
                    ] = FreshnessFlag.MISSING.value

        # OU-level gap (C-MISS): one OU loses all telemetry
        if cond.ou_level_gap:
            depts = users["department"].unique()
            gap_dept = depts[int(rng.integers(0, len(depts)))]
            gap_user_ids = set(users[users["department"] == gap_dept]["user_id"].tolist())
            freshness_log = freshness_log.copy()
            freshness_log.loc[
                freshness_log["entity_id"].isin(gap_user_ids),
                "freshness_flag"
            ] = FreshnessFlag.MISSING.value
            freshness_log.loc[
                freshness_log["entity_id"].isin(gap_user_ids),
                "anomaly_class"
            ] = "telemetry_missingness_cluster"

        return users, computers, assets, patch_state, vuln_records, freshness_log
