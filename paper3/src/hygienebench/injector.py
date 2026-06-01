"""
AnomalyInjector — injects labelled anomalies into a SyntheticHygieneDataset.

Each inject_* method targets one or more anomaly classes from SCHEMA_v0_1.md.
Returns the mutated dataset and a rows-list of anomaly_labels records.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from hygienebench.generator import SyntheticHygieneDataset, REF_DATE, _make_id
from hygienebench.schema import (
    AnomalyClass, FreshnessFlag, AssetCriticality,
    RemediationAction, AccountAction, LogonType
)


class AnomalyInjector:
    """
    Injects anomalies into an existing SyntheticHygieneDataset.

    Usage:
        injector = AnomalyInjector(seed=42)
        ds, labels_df = injector.inject(ds, tasks=["T1","T2","T3","T4","T5","T6","T7"])
    """

    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed + 999)  # offset so injector RNG differs from generator
        self._seed_tag = f"inj:{seed}"
        self._label_counter = 0

    def inject(
        self,
        ds: SyntheticHygieneDataset,
        tasks: List[str],
    ) -> SyntheticHygieneDataset:
        labels: List[Dict[str, Any]] = []

        task_methods = {
            "T1": self._inject_t1_stale_privileged,
            "T2": self._inject_t2_group_drift,
            "T3": self._inject_t3_endpoint_identity,
            "T4": self._inject_t4_telemetry_missingness,
            "T5": self._inject_t5_patch_vuln_hygiene,
            "T6": self._inject_t6_dormant_reactivation,
            "T7": self._inject_t7_escalation_drift,
        }

        for task in tasks:
            if task not in task_methods:
                continue
            ds, task_labels = task_methods[task](ds)
            labels.extend(task_labels)

        ds.anomaly_labels = pd.DataFrame(labels) if labels else pd.DataFrame(columns=[
            "label_id", "entity_type", "entity_id", "anomaly_class", "anomaly_severity",
            "injected_at", "observable_from", "source_record_ids",
            "benchmark_task_id", "split",
        ])
        return ds

    # ------------------------------------------------------------------
    # T1 — Stale Privileged Account Risk (AH-01)
    # ------------------------------------------------------------------
    def _inject_t1_stale_privileged(
        self, ds: SyntheticHygieneDataset
    ) -> tuple[SyntheticHygieneDataset, List[Dict]]:
        cfg = ds.config.anomaly
        n = cfg.t1_stale_priv_n
        rng = self.rng
        labels = []

        priv_users = ds.users[ds.users["is_privileged"]].copy()
        if len(priv_users) == 0 or n == 0:
            return ds, labels

        n = min(n, len(priv_users))
        targets = priv_users.sample(n=n, random_state=int(rng.integers(0, 2**31))).index

        users = ds.users.copy()
        for idx in targets:
            uid = users.at[idx, "user_id"]
            stale_days = float(rng.uniform(91, 365))
            last_logon = REF_DATE - timedelta(days=stale_days)
            users.at[idx, "days_since_last_logon"] = round(stale_days, 1)
            users.at[idx, "account_last_logon"] = last_logon.isoformat()

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "user",
                "entity_id": uid,
                "anomaly_class": AnomalyClass.STALE_PRIVILEGED_ACCOUNT.value,
                "anomaly_severity": "high",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": REF_DATE.isoformat(),
                "source_record_ids": uid,
                "benchmark_task_id": "T1",
                "split": "unassigned",
            })

        ds = SyntheticHygieneDataset(**{**ds.__dict__, "users": users})
        return ds, labels

    # ------------------------------------------------------------------
    # T2 — Group Membership Drift (AH-02, AH-03)
    # ------------------------------------------------------------------
    def _inject_t2_group_drift(
        self, ds: SyntheticHygieneDataset
    ) -> tuple[SyntheticHygieneDataset, List[Dict]]:
        cfg = ds.config.anomaly
        rng = self.rng
        labels = []

        priv_groups = ds.groups[ds.groups["is_privileged"]]["group_id"].tolist()
        biz_groups = ds.groups[~ds.groups["is_privileged"] & (ds.groups["group_type"] == "security")]["group_id"].tolist()
        all_users = ds.users["user_id"].tolist()
        priv_users = ds.users[ds.users["is_privileged"]]["user_id"].tolist()
        actor = priv_users[0] if priv_users else all_users[0]

        new_events = []

        # Type A: cross-OU drift
        for i in range(cfg.t2_drift_n):
            if not biz_groups:
                break
            uid = all_users[int(rng.integers(0, len(all_users)))]
            gid = biz_groups[int(rng.integers(0, len(biz_groups)))]
            day_off = int(rng.integers(0, ds.config.obs_window_days))
            ts = REF_DATE + timedelta(days=day_off, hours=int(rng.integers(0, 24)))
            eid = _make_id(f"{self._seed_tag}:t2:drift", i)
            new_events.append({
                "event_id": eid,
                "user_id": uid,
                "group_id": gid,
                "action": "add",
                "event_timestamp": ts.isoformat(),
                "actor_user_id": actor,
                "is_privileged_group": False,
                "is_anomalous": True,
                "anomaly_class": AnomalyClass.GROUP_MEMBERSHIP_DRIFT.value,
            })
            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "event",
                "entity_id": eid,
                "anomaly_class": AnomalyClass.GROUP_MEMBERSHIP_DRIFT.value,
                "anomaly_severity": "medium",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": ts,
                "source_record_ids": eid,
                "benchmark_task_id": "T2",
                "split": "unassigned",
            })

        # Type B: privilege escalation
        for i in range(cfg.t2_escalation_n):
            if not priv_groups:
                break
            # Pick a non-privileged user
            non_priv = ds.users[~ds.users["is_privileged"]]["user_id"].tolist()
            if not non_priv:
                break
            uid = non_priv[int(rng.integers(0, len(non_priv)))]
            gid = priv_groups[int(rng.integers(0, len(priv_groups)))]
            day_off = int(rng.integers(0, ds.config.obs_window_days))
            ts = REF_DATE + timedelta(days=day_off, hours=int(rng.integers(2, 6)))  # unusual time
            eid = _make_id(f"{self._seed_tag}:t2:esc", i)
            new_events.append({
                "event_id": eid,
                "user_id": uid,
                "group_id": gid,
                "action": "add",
                "event_timestamp": ts.isoformat(),
                "actor_user_id": actor,
                "is_privileged_group": True,
                "is_anomalous": True,
                "anomaly_class": AnomalyClass.PRIVILEGE_ESCALATION_DRIFT.value,
            })
            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "event",
                "entity_id": eid,
                "anomaly_class": AnomalyClass.PRIVILEGE_ESCALATION_DRIFT.value,
                "anomaly_severity": "critical",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": ts,
                "source_record_ids": eid,
                "benchmark_task_id": "T2",
                "split": "unassigned",
            })

        if new_events:
            gme = pd.concat([ds.group_membership_events, pd.DataFrame(new_events)], ignore_index=True)
            ds = SyntheticHygieneDataset(**{**ds.__dict__, "group_membership_events": gme})

        return ds, labels

    # ------------------------------------------------------------------
    # T3 — Endpoint–Identity Risk Correlation (AH-06)
    # ------------------------------------------------------------------
    def _inject_t3_endpoint_identity(
        self, ds: SyntheticHygieneDataset
    ) -> tuple[SyntheticHygieneDataset, List[Dict]]:
        cfg = ds.config.anomaly
        rng = self.rng
        labels = []

        priv_users = ds.users[ds.users["is_privileged"]].copy()
        if len(priv_users) == 0:
            return ds, labels

        computers = ds.computers.copy()
        patch_state = ds.endpoint_patch_state.copy()
        vuln_records = ds.vulnerability_records.copy()

        # Find computers assigned to privileged users
        priv_comps = computers[computers["primary_user_id"].isin(priv_users["user_id"])]
        if len(priv_comps) == 0:
            return ds, labels

        n = min(cfg.t3_risk_pair_n, len(priv_comps))
        target_comps = priv_comps.sample(n=n, random_state=int(rng.integers(0, 2**31))).index

        for cidx in target_comps:
            cid = computers.at[cidx, "computer_id"]
            uid = computers.at[cidx, "primary_user_id"]

            # Mark computer: high-criticality, stale agent
            computers.at[cidx, "asset_criticality"] = AssetCriticality.CRITICAL.value
            computers.at[cidx, "days_since_agent_heartbeat"] = float(rng.uniform(15, 45))
            computers.at[cidx, "endpoint_agent_last_heartbeat"] = (
                REF_DATE - timedelta(days=computers.at[cidx, "days_since_agent_heartbeat"])).isoformat()

            # Mark patch_state: non-compliant
            pmask = patch_state["computer_id"] == cid
            if pmask.any():
                patch_state.loc[pmask, "patch_compliance_score"] = round(float(rng.uniform(0.2, 0.45)), 3)
                patch_state.loc[pmask, "critical_missing_patch_count"] = int(rng.integers(2, 6))
                patch_state.loc[pmask, "open_kev_count"] = 1

            # Inject a KEV CVE record aged >= 30 days
            kev_rid = _make_id(f"{self._seed_tag}:t3:kev:{cid}", 0)
            kev_row = {
                "record_id": kev_rid,
                "computer_id": cid,
                "cve_id": f"CVE-SYNTH-KEV-{abs(hash(kev_rid)) % 9000:04d}",
                "cvss_score": round(float(rng.uniform(9.0, 10.0)), 1),
                "cvss_severity": "critical",
                "is_kev_flagged": True,
                "cve_published_days_ago": int(rng.integers(60, 180)),
                "first_observed_at": (REF_DATE - timedelta(days=float(rng.uniform(31, 90)))).isoformat(),
                "days_open": round(float(rng.uniform(31, 90)), 1),
                "remediation_status": "open",
                "asset_criticality": AssetCriticality.CRITICAL.value,
                "exposed_privileged_user_count": 1,
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": REF_DATE.isoformat(),
                "is_anomalous": True,
                "anomaly_class": AnomalyClass.ENDPOINT_IDENTITY_RISK_CORRELATION.value,
            }
            vuln_records = pd.concat([vuln_records, pd.DataFrame([kev_row])], ignore_index=True)

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "computer",
                "entity_id": cid,
                "anomaly_class": AnomalyClass.ENDPOINT_IDENTITY_RISK_CORRELATION.value,
                "anomaly_severity": "critical",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": REF_DATE.isoformat(),
                "source_record_ids": f"{cid},{uid}",
                "benchmark_task_id": "T3",
                "split": "unassigned",
            })

        ds = SyntheticHygieneDataset(**{
            **ds.__dict__,
            "computers": computers,
            "endpoint_patch_state": patch_state,
            "vulnerability_records": vuln_records,
        })
        return ds, labels

    # ------------------------------------------------------------------
    # T4 — Telemetry Missingness (AH-09, AH-10, AH-11)
    # ------------------------------------------------------------------
    def _inject_t4_telemetry_missingness(
        self, ds: SyntheticHygieneDataset
    ) -> tuple[SyntheticHygieneDataset, List[Dict]]:
        cfg = ds.config.anomaly
        rng = self.rng
        labels = []

        computers = ds.computers.copy()
        assets = ds.assets.copy()
        freshness = ds.telemetry_freshness_log.copy()

        # Type A: missing endpoint agent
        n_missing = max(1, int(len(computers) * cfg.t4_missing_agent_rate))
        miss_idx = rng.choice(len(computers), size=n_missing, replace=False)
        for i in miss_idx:
            cid = computers.iloc[i]["computer_id"]
            computers.at[computers.index[i], "endpoint_agent_installed"] = False
            computers.at[computers.index[i], "days_since_agent_heartbeat"] = 999.0

            fmask = (freshness["entity_id"] == cid) & (freshness["source_system"] == "edr_agent")
            freshness.loc[fmask, "freshness_flag"] = FreshnessFlag.MISSING.value
            freshness.loc[fmask, "actual_gap_days"] = 999.0
            freshness.loc[fmask, "is_anomalous"] = True
            freshness.loc[fmask, "anomaly_class"] = AnomalyClass.MISSING_ENDPOINT_AGENT.value

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "computer",
                "entity_id": cid,
                "anomaly_class": AnomalyClass.MISSING_ENDPOINT_AGENT.value,
                "anomaly_severity": "high",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": REF_DATE.isoformat(),
                "source_record_ids": cid,
                "benchmark_task_id": "T4",
                "split": "unassigned",
            })

        # Type C: inventory mismatch
        n_mismatch = max(1, int(len(assets) * cfg.t4_inventory_mismatch_rate))
        mism_idx = rng.choice(len(assets), size=n_mismatch, replace=False)
        for i in mism_idx:
            aid = assets.iloc[i]["asset_id"]
            assets.at[assets.index[i], "inventory_mismatch_flag"] = True
            assets.at[assets.index[i], "in_inventory"] = False

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "asset",
                "entity_id": aid,
                "anomaly_class": AnomalyClass.ASSET_INVENTORY_MISMATCH.value,
                "anomaly_severity": "medium",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": REF_DATE.isoformat(),
                "source_record_ids": aid,
                "benchmark_task_id": "T4",
                "split": "unassigned",
            })

        ds = SyntheticHygieneDataset(**{
            **ds.__dict__,
            "computers": computers,
            "assets": assets,
            "telemetry_freshness_log": freshness,
        })
        return ds, labels

    # ------------------------------------------------------------------
    # T5 — Patch / Vulnerability Hygiene (AH-07, AH-08, AH-12)
    # ------------------------------------------------------------------
    def _inject_t5_patch_vuln_hygiene(
        self, ds: SyntheticHygieneDataset
    ) -> tuple[SyntheticHygieneDataset, List[Dict]]:
        cfg = ds.config.anomaly
        rng = self.rng
        labels = []

        computers = ds.computers.copy()
        patch_state = ds.endpoint_patch_state.copy()
        vuln_records = ds.vulnerability_records.copy()
        remediation_events = ds.remediation_events.copy()

        # Type A: patch-noncompliance cluster (one OU block)
        cluster_size = min(cfg.t5_noncompliant_cluster_size, len(computers))
        start_idx = int(rng.integers(0, max(1, len(computers) - cluster_size)))
        cluster_comps = computers.iloc[start_idx:start_idx + cluster_size]

        for _, c in cluster_comps.iterrows():
            cid = c["computer_id"]
            pmask = patch_state["computer_id"] == cid
            if pmask.any():
                patch_state.loc[pmask, "patch_compliance_score"] = round(float(rng.uniform(0.1, 0.45)), 3)
                patch_state.loc[pmask, "critical_missing_patch_count"] = int(rng.integers(3, 8))
                patch_state.loc[pmask, "missing_patch_count"] = int(rng.integers(5, 15))
                patch_state.loc[pmask, "is_anomalous"] = True
                patch_state.loc[pmask, "anomaly_class"] = AnomalyClass.PATCH_NONCOMPLIANCE_CLUSTER.value

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "computer",
                "entity_id": cid,
                "anomaly_class": AnomalyClass.PATCH_NONCOMPLIANCE_CLUSTER.value,
                "anomaly_severity": "high",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": REF_DATE.isoformat(),
                "source_record_ids": cid,
                "benchmark_task_id": "T5",
                "split": "unassigned",
            })

        # Type B: KEV aging >= 30 days on critical assets
        crit_comps = computers[computers["asset_criticality"].isin(
            [AssetCriticality.CRITICAL.value, AssetCriticality.HIGH.value]
        )]["computer_id"].tolist()
        n_kev = min(cfg.t5_kev_n, len(crit_comps))
        kev_targets = rng.choice(crit_comps, size=n_kev, replace=False).tolist() if crit_comps else []

        for i, cid in enumerate(kev_targets):
            kev_rid = _make_id(f"{self._seed_tag}:t5:kev:{cid}", i)
            days_open = float(rng.uniform(31, 120))
            kev_row = {
                "record_id": kev_rid,
                "computer_id": cid,
                "cve_id": f"CVE-SYNTH-KEV-T5-{abs(hash(kev_rid)) % 9000:04d}",
                "cvss_score": round(float(rng.uniform(9.0, 10.0)), 1),
                "cvss_severity": "critical",
                "is_kev_flagged": True,
                "cve_published_days_ago": int(rng.integers(60, 180)),
                "first_observed_at": (REF_DATE - timedelta(days=days_open)).isoformat(),
                "days_open": round(days_open, 1),
                "remediation_status": "open",
                "asset_criticality": AssetCriticality.CRITICAL.value,
                "exposed_privileged_user_count": 0,
                "source_freshness_flag": FreshnessFlag.FRESH.value,
                "last_updated_at": REF_DATE.isoformat(),
                "is_anomalous": True,
                "anomaly_class": AnomalyClass.KEV_EXPOSURE_AGING.value,
            }
            vuln_records = pd.concat([vuln_records, pd.DataFrame([kev_row])], ignore_index=True)

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "computer",
                "entity_id": cid,
                "anomaly_class": AnomalyClass.KEV_EXPOSURE_AGING.value,
                "anomaly_severity": "critical",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": REF_DATE.isoformat(),
                "source_record_ids": kev_rid,
                "benchmark_task_id": "T5",
                "split": "unassigned",
            })

        # Type C: abnormal remediation delay
        all_comp_ids = computers["computer_id"].tolist()
        n_delay = min(cfg.t5_delay_n, len(all_comp_ids))
        delay_targets = rng.choice(all_comp_ids, size=n_delay, replace=False).tolist()
        for i, cid in enumerate(delay_targets):
            eid = _make_id(f"{self._seed_tag}:t5:delay:{cid}", i)
            delay_days = float(rng.uniform(91, 300))
            ts = REF_DATE - timedelta(days=delay_days)
            delay_row = {
                "event_id": eid,
                "computer_id": cid,
                "cve_id": f"CVE-SYNTH-DELAY-{abs(hash(eid)) % 9000:04d}",
                "action_type": RemediationAction.DEFERRED.value,
                "action_timestamp": ts.isoformat(),
                "actor_type": "manual",
                "remediation_latency_days": round(delay_days, 1),
                "is_anomalous": True,
                "anomaly_class": AnomalyClass.ABNORMAL_REMEDIATION_DELAY.value,
            }
            remediation_events = pd.concat(
                [remediation_events, pd.DataFrame([delay_row])], ignore_index=True
            )

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "computer",
                "entity_id": cid,
                "anomaly_class": AnomalyClass.ABNORMAL_REMEDIATION_DELAY.value,
                "anomaly_severity": "high",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": REF_DATE.isoformat(),
                "source_record_ids": eid,
                "benchmark_task_id": "T5",
                "split": "unassigned",
            })

        ds = SyntheticHygieneDataset(**{
            **ds.__dict__,
            "endpoint_patch_state": patch_state,
            "vulnerability_records": vuln_records,
            "remediation_events": remediation_events,
        })
        return ds, labels

    # ------------------------------------------------------------------
    # T6 — Dormant Account Reactivation (AH-04, AH-05)
    # ------------------------------------------------------------------
    def _inject_t6_dormant_reactivation(
        self, ds: SyntheticHygieneDataset
    ) -> tuple[SyntheticHygieneDataset, List[Dict]]:
        cfg = ds.config.anomaly
        rng = self.rng
        labels = []

        disabled_users = ds.users[~ds.users["account_enabled"]].copy()
        all_users = ds.users["user_id"].tolist()
        computers = ds.computers.copy()
        login_events = ds.login_events.copy()
        lifecycle_events = ds.account_lifecycle_events.copy()

        # If not enough disabled users, pick from enabled users who are long-dormant
        dormant_enabled = ds.users[
            ds.users["account_enabled"] & (ds.users["days_since_last_logon"] > 180)
        ]
        candidates = pd.concat([disabled_users, dormant_enabled]).drop_duplicates("user_id")
        if len(candidates) == 0:
            candidates = ds.users.sample(n=min(cfg.t6_dormant_n, len(ds.users)),
                                          random_state=int(rng.integers(0, 2**31)))

        n = min(cfg.t6_dormant_n, len(candidates))
        targets = candidates.sample(n=n, random_state=int(rng.integers(0, 2**31)))

        users = ds.users.copy()
        priv_actors = ds.users[ds.users["is_privileged"]]["user_id"].tolist()
        actor = priv_actors[0] if priv_actors else all_users[0]

        new_lifecycle = []
        new_logins = []

        for _, u in targets.iterrows():
            uid = u["user_id"]
            dormant_days = max(180, float(u["days_since_last_logon"]))

            # Reactivation event
            reactivation_day = int(rng.integers(5, ds.config.obs_window_days - 5))
            ts_react = REF_DATE + timedelta(days=reactivation_day, hours=int(rng.integers(2, 6)))

            eid_lifecycle = _make_id(f"{self._seed_tag}:t6:lifecycle:{uid}", 0)
            new_lifecycle.append({
                "event_id": eid_lifecycle,
                "user_id": uid,
                "action": AccountAction.REACTIVATED.value,
                "event_timestamp": ts_react.isoformat(),
                "actor_user_id": actor,
                "days_since_last_logon_at_action": round(dormant_days, 1),
                "is_anomalous": True,
                "anomaly_class": AnomalyClass.DORMANT_ACCOUNT_REACTIVATION.value,
            })

            # Enable the user
            uidx = users.index[users["user_id"] == uid]
            if len(uidx) > 0:
                users.at[uidx[0], "account_enabled"] = True

            # Post-reactivation: off-hours, cross-segment logins
            n_post_logins = int(rng.integers(3, 8))
            for k in range(n_post_logins):
                login_day = reactivation_day + int(rng.integers(0, 3))
                login_hour = int(rng.choice([0, 1, 2, 22, 23]))  # off-hours
                ts_login = REF_DATE + timedelta(days=login_day, hours=login_hour,
                                                 minutes=int(rng.integers(0, 60)))
                cid = computers["computer_id"].iloc[int(rng.integers(0, len(computers)))]
                eid_login = _make_id(f"{self._seed_tag}:t6:login:{uid}", k)
                new_logins.append({
                    "event_id": eid_login,
                    "user_id": uid,
                    "computer_id": cid,
                    "event_timestamp": ts_login.isoformat(),
                    "logon_type": LogonType.NETWORK.value,
                    "success": True,
                    "is_off_hours": True,
                    "is_cross_segment": bool(rng.random() < 0.6),
                    "is_anomalous": True,
                    "anomaly_class": AnomalyClass.IMPOSSIBLE_OR_UNUSUAL_LOGIN.value,
                })

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "user",
                "entity_id": uid,
                "anomaly_class": AnomalyClass.DORMANT_ACCOUNT_REACTIVATION.value,
                "anomaly_severity": "high",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": ts_react.isoformat(),
                "source_record_ids": f"{eid_lifecycle}",
                "benchmark_task_id": "T6",
                "split": "unassigned",
            })

        if new_lifecycle:
            lifecycle_events = pd.concat(
                [lifecycle_events, pd.DataFrame(new_lifecycle)], ignore_index=True
            )
        if new_logins:
            login_events = pd.concat(
                [login_events, pd.DataFrame(new_logins)], ignore_index=True
            )

        ds = SyntheticHygieneDataset(**{
            **ds.__dict__,
            "users": users,
            "login_events": login_events,
            "account_lifecycle_events": lifecycle_events,
        })
        return ds, labels

    # ------------------------------------------------------------------
    # T7 — Multi-Step Privilege Escalation Drift (AH-02)
    # ------------------------------------------------------------------
    def _inject_t7_escalation_drift(
        self, ds: SyntheticHygieneDataset
    ) -> tuple[SyntheticHygieneDataset, List[Dict]]:
        cfg = ds.config.anomaly
        rng = self.rng
        labels = []

        non_priv = ds.users[~ds.users["is_privileged"]]["user_id"].tolist()
        priv_groups = ds.groups[ds.groups["is_privileged"]]["group_id"].tolist()
        priv_actors = ds.users[ds.users["is_privileged"]]["user_id"].tolist()
        if not non_priv or not priv_groups or not priv_actors:
            return ds, labels

        n = min(cfg.t7_escalation_n, len(non_priv))
        targets = rng.choice(non_priv, size=n, replace=False).tolist()
        actor = priv_actors[0]

        new_events = []
        for j, uid in enumerate(targets):
            # 3-5 group additions over 30 days, spread >= 5 days apart
            n_additions = int(rng.integers(3, 6))
            start_day = int(rng.integers(0, ds.config.obs_window_days - 35))
            days_list = sorted(rng.choice(
                range(start_day, start_day + 30), size=n_additions, replace=False
            ).tolist())

            for k, day in enumerate(days_list):
                gid = priv_groups[int(rng.integers(0, len(priv_groups)))]
                ts = REF_DATE + timedelta(days=day, hours=int(rng.integers(9, 17)))
                eid = _make_id(f"{self._seed_tag}:t7:esc:{uid}", k)
                new_events.append({
                    "event_id": eid,
                    "user_id": uid,
                    "group_id": gid,
                    "action": "add",
                    "event_timestamp": ts.isoformat(),
                    "actor_user_id": actor,
                    "is_privileged_group": True,
                    "is_anomalous": True,
                    "anomaly_class": AnomalyClass.PRIVILEGE_ESCALATION_DRIFT.value,
                })

            lid = self._new_label_id()
            labels.append({
                "label_id": lid,
                "entity_type": "user",
                "entity_id": uid,
                "anomaly_class": AnomalyClass.PRIVILEGE_ESCALATION_DRIFT.value,
                "anomaly_severity": "critical",
                "injected_at": REF_DATE.isoformat(),
                "observable_from": (REF_DATE + timedelta(days=days_list[-1])).isoformat(),
                "source_record_ids": uid,
                "benchmark_task_id": "T7",
                "split": "unassigned",
            })

        if new_events:
            gme = pd.concat(
                [ds.group_membership_events, pd.DataFrame(new_events)], ignore_index=True
            )
            ds = SyntheticHygieneDataset(**{**ds.__dict__, "group_membership_events": gme})

        return ds, labels

    # ------------------------------------------------------------------
    def _new_label_id(self) -> str:
        lid = _make_id(f"{self._seed_tag}:label", self._label_counter)
        self._label_counter += 1
        return lid
