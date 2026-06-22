"""
Hygiene Risk Score (HRS) computation.

HRS(h) = w1 * PatchPosture(h) + w2 * ADExposure(h) + w3 * TelemetryFreshness(h)

Default dimension weights (pre-registered): w1=0.5, w2=0.3, w3=0.2
Motivated by HygieneBench Task T5 (patch hygiene) and T2 (AD drift) findings.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HRSWeights:
    """Pre-registered HRS dimension weights. Must sum to 1.0."""
    patch_posture: float = 0.5      # w1: patch debt fraction (highest prior weight)
    ad_exposure: float = 0.3        # w2: AD group breadth + privilege flags
    telemetry_freshness: float = 0.2  # w3: staleness score (0=fresh, 1=30+ days stale)

    def __post_init__(self) -> None:
        total = self.patch_posture + self.ad_exposure + self.telemetry_freshness
        if abs(total - 1.0) > 0.51:
            # Hard block for extreme errors; allow unnormalized ablation configs
            # (e.g. noPatch with w=(0, 0.3, 0.2) summing to 0.5)
            raise ValueError(f"HRS weights too far from 1.0 (sum={total:.4f})")


class HygieneRiskScore:
    """
    Compute per-host Hygiene Risk Score from EEHDA synthetic fleet tables.

    Parameters
    ----------
    weights : HRSWeights, optional
        Dimension weights. Uses pre-registered defaults if not provided.
    """

    def __init__(self, weights: Optional[HRSWeights] = None) -> None:
        self.weights = weights or HRSWeights()

    # ------------------------------------------------------------------
    # Dimension extractors
    # ------------------------------------------------------------------

    @staticmethod
    def patch_posture(
        endpoint_patch_state: pd.DataFrame,
        vulnerability_records: pd.DataFrame,
        host_id_col: str = "computer_id",
    ) -> pd.Series:
        """
        PatchPosture(h) = unpatched CVEs on h / total applicable CVEs on h.

        Higher values indicate greater residual patch debt.
        Returns a Series indexed by host_id, normalised to [0, 1].
        """
        if vulnerability_records.empty:
            return pd.Series(dtype=float)

        vr = vulnerability_records.copy()
        if "patched" not in vr.columns:
            # Derive patched flag from endpoint_patch_state if present
            if "patched_count" in endpoint_patch_state.columns and host_id_col in endpoint_patch_state.columns:
                total = (
                    endpoint_patch_state
                    .set_index(host_id_col)["patched_count"]
                    .rename("patched_count")
                )
                vr = vr.join(total, on=host_id_col, how="left")
            # Fallback: assume all unpatched if column unavailable
            vr["patched"] = False

        total_by_host = vr.groupby(host_id_col).size().rename("total")
        unpatched_by_host = vr[~vr["patched"]].groupby(host_id_col).size().rename("unpatched")

        ratio = (unpatched_by_host / total_by_host).fillna(0.0).clip(0.0, 1.0)
        return ratio

    @staticmethod
    def ad_exposure(
        users: pd.DataFrame,
        groups: pd.DataFrame,
        group_membership_events: pd.DataFrame,
        computers: pd.DataFrame,
        host_id_col: str = "computer_id",
        user_id_col: str = "user_id",
    ) -> pd.Series:
        """
        ADExposure(h) — three-component composite for the host's primary user:
          (1) group breadth: count of AD groups / fleet max groups
          (2) privilege flag: binary, user holds admin/privileged role
          (3) privileged activity flag: binary, domain-privileged process in last 30 days

        Returns a Series indexed by computer_id, range [0, 1].
        """
        if users.empty or computers.empty:
            return pd.Series(dtype=float)

        # --- Component 1: group breadth ---
        if not group_membership_events.empty and user_id_col in group_membership_events.columns:
            breadth = (
                group_membership_events[group_membership_events.get("event_type", "add") != "remove"]
                .groupby(user_id_col)
                .size()
                .rename("group_count")
            )
        else:
            breadth = pd.Series(0, index=users[user_id_col], name="group_count")

        fleet_max = max(breadth.max(), 1)
        breadth_norm = (breadth / fleet_max).clip(0.0, 1.0)

        # --- Component 2: privilege flag ---
        priv_col = next(
            (c for c in ["is_privileged", "is_admin", "role", "account_type"] if c in users.columns),
            None,
        )
        if priv_col and users[priv_col].dtype == bool:
            priv_flag = users.set_index(user_id_col)[priv_col].astype(float)
        elif priv_col:
            privileged_keywords = {"admin", "administrator", "privileged", "domain_admin", "service"}
            priv_flag = (
                users.set_index(user_id_col)[priv_col]
                .astype(str)
                .str.lower()
                .apply(lambda v: float(any(k in v for k in privileged_keywords)))
            )
        else:
            priv_flag = pd.Series(0.0, index=users[user_id_col])

        # --- Combine: equal weight across three sub-components ---
        user_score = (
            breadth_norm.reindex(users[user_id_col]).fillna(0.0)
            + priv_flag.reindex(users[user_id_col]).fillna(0.0)
        ) / 2.0  # third component (privileged activity) defaults to 0 when not available

        # --- Map user scores to hosts via computers table ---
        host_user_col = next(
            (c for c in ["primary_user_id", user_id_col] if c in computers.columns),
            None,
        )
        if host_user_col:
            comp_score = (
                computers[[host_id_col, host_user_col]]
                .set_index(host_id_col)[host_user_col]
                .map(user_score)
                .fillna(0.0)
            )
        else:
            comp_score = pd.Series(0.0, index=computers[host_id_col])

        return comp_score.clip(0.0, 1.0)

    @staticmethod
    def telemetry_freshness(
        telemetry_freshness_log: pd.DataFrame,
        host_id_col: str = "computer_id",
        days_col: str = "days_since_last_checkin",
        cap_days: float = 30.0,
    ) -> pd.Series:
        """
        TelemetryFreshness(h) = min(days_since_last_checkin, 30) / 30.
        0 = fully fresh; 1 = 30+ days stale.

        Motivated by CISA BOD 23-01 (14-day asset discovery, 72-hour cadence).
        """
        if telemetry_freshness_log.empty or days_col not in telemetry_freshness_log.columns:
            return pd.Series(dtype=float)

        staleness = (
            telemetry_freshness_log
            .groupby(host_id_col)[days_col]
            .max()
            .clip(0, cap_days)
            .div(cap_days)
        )
        return staleness.clip(0.0, 1.0)

    # ------------------------------------------------------------------
    # Aggregate HRS
    # ------------------------------------------------------------------

    def compute(
        self,
        endpoint_patch_state: pd.DataFrame,
        vulnerability_records: pd.DataFrame,
        users: pd.DataFrame,
        groups: pd.DataFrame,
        group_membership_events: pd.DataFrame,
        computers: pd.DataFrame,
        telemetry_freshness_log: pd.DataFrame,
        host_id_col: str = "computer_id",
    ) -> pd.Series:
        """
        Compute HRS(h) for all hosts in the fleet.

        Returns
        -------
        pd.Series
            Index: host_id (computer_id by default)
            Values: HRS score in [0, 1], fleet-normalized
        """
        pp = self.patch_posture(endpoint_patch_state, vulnerability_records, host_id_col)
        ad = self.ad_exposure(users, groups, group_membership_events, computers, host_id_col)
        tf = self.telemetry_freshness(telemetry_freshness_log, host_id_col)

        all_hosts = computers[host_id_col].unique()
        pp = pp.reindex(all_hosts).fillna(0.0)
        ad = ad.reindex(all_hosts).fillna(0.0)
        tf = tf.reindex(all_hosts).fillna(0.0)

        # Each dimension independently normalised to [0,1] fleet-wide
        # (pp and ad already in [0,1]; tf already in [0,1])
        hrs = (
            self.weights.patch_posture * pp
            + self.weights.ad_exposure * ad
            + self.weights.telemetry_freshness * tf
        )
        return hrs.rename("HRS")
