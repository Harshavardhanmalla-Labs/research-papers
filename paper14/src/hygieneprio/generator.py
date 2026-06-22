"""
Synthetic EEHDA fleet generator for Paper 4.

Extends the HygieneBench (Paper 3) fleet schema to produce the vulnerability-host
pair tables required by HygienePrio, with EPSS scores, KEV membership, and CVSS
base scores aligned to the structural priors used in Paper 1.

Structural priors (all public):
  - Verizon DBIR 2026: 43-day median critical patch lag
  - NIST NVD: CVE severity distributions (CVSS base score mix)
  - CISA BOD 23-01: 72-hour patch data freshness, 14-day asset discovery
  - FIRST EPSS v3: heavy-right-tail exploit probability distribution (~12% > 0.10)
  - CISA KEV: ~8% of CVEs in high-EPSS fixtures have confirmed exploitation entry
"""

from __future__ import annotations

import hashlib
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# EPSS fixture — approximates heavy-right-tail real EPSS distribution
# ---------------------------------------------------------------------------
# ~88% of CVEs have EPSS in [0, 0.10]; ~12% in (0.10, 1.0].
# Modelled as mixture: 88% Beta(0.5, 8) (mass near 0), 12% Beta(2, 4) (heavier tail).

def _sample_epss(n: int, rng: np.random.Generator) -> np.ndarray:
    low_mask = rng.random(n) < 0.88
    scores = np.where(
        low_mask,
        rng.beta(0.5, 8.0, n),
        rng.beta(2.0, 4.0, n),
    )
    return np.clip(scores, 1e-4, 1.0)


def _sample_cvss(n: int, rng: np.random.Generator) -> np.ndarray:
    """NVD CVSS distribution: modal ~7.5, mix of medium/high/critical."""
    # Approximate: 20% Low (2–4), 35% Medium (4–7), 35% High (7–9), 10% Critical (9–10)
    categories = rng.choice([0, 1, 2, 3], size=n, p=[0.20, 0.35, 0.35, 0.10])
    scores = np.where(categories == 0, rng.uniform(2.0, 4.0, n),
             np.where(categories == 1, rng.uniform(4.0, 7.0, n),
             np.where(categories == 2, rng.uniform(7.0, 9.0, n),
                                        rng.uniform(9.0, 10.0, n))))
    return np.round(scores, 1)


def _sample_patch_lag_days(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Patch lag distribution based on DBIR 2026: 43-day median for critical patches.
    Modelled as log-normal with median=43, sigma≈1.0 (heavy right tail).
    """
    # log-normal: median = exp(mu) → mu = ln(43); sigma=1.0
    mu = np.log(43)
    return np.clip(rng.lognormal(mu, 1.0, n), 0, None)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

class EEHDAFleetGenerator:
    """
    Generate one synthetic EEHDA fleet instance for a given seed.

    Parameters
    ----------
    seed : int
        Deterministic seed. All outputs are fully reproducible from this seed.
    n_hosts : int
        Number of managed hosts (computers/assets). Default: 830.
    n_users : int
        Number of AD user accounts. Default: 1000.
    n_groups : int
        Number of AD groups. Default: 65.
    cves_per_host_mean : float
        Mean applicable CVEs per host. Default: ~4.2 (→ ~3500 total for 830 hosts).
    """

    def __init__(
        self,
        seed: int,
        n_hosts: int = 830,
        n_users: int = 1000,
        n_groups: int = 65,
        cves_per_host_mean: float = 4.2,
    ) -> None:
        self.seed = seed
        self.n_hosts = n_hosts
        self.n_users = n_users
        self.n_groups = n_groups
        self.cves_per_host_mean = cves_per_host_mean
        self._rng = np.random.default_rng(seed)

    def _host_id(self, i: int) -> str:
        h = hashlib.sha256(f"host:{self.seed}:{i}".encode()).hexdigest()[:8]
        return f"H-{h}"

    def _user_id(self, i: int) -> str:
        h = hashlib.sha256(f"user:{self.seed}:{i}".encode()).hexdigest()[:8]
        return f"U-{h}"

    def _cve_id(self, i: int) -> str:
        year = 2022 + (i % 3)
        num = 10000 + i
        return f"CVE-{year}-{num:05d}"

    def generate_computers(self) -> pd.DataFrame:
        host_ids = [self._host_id(i) for i in range(self.n_hosts)]
        user_ids = [self._user_id(i) for i in range(self.n_users)]
        return pd.DataFrame({
            "computer_id": host_ids,
            "primary_user_id": self._rng.choice(user_ids, size=self.n_hosts),
            "os_type": self._rng.choice(
                ["windows_server", "windows_workstation", "linux"],
                size=self.n_hosts,
                p=[0.20, 0.60, 0.20],
            ),
            "is_internet_facing": self._rng.random(self.n_hosts) < 0.15,
        })

    def generate_users(self) -> pd.DataFrame:
        user_ids = [self._user_id(i) for i in range(self.n_users)]
        role_probs = [0.80, 0.12, 0.05, 0.03]  # standard, local_admin, service, domain_admin
        return pd.DataFrame({
            "user_id": user_ids,
            "role": self._rng.choice(
                ["standard", "local_admin", "service_account", "domain_admin"],
                size=self.n_users,
                p=role_probs,
            ),
            "is_privileged": self._rng.random(self.n_users) < 0.20,
            "last_login_days_ago": self._rng.exponential(5, self.n_users).clip(0, 365).astype(int),
        })

    def generate_groups(self) -> pd.DataFrame:
        return pd.DataFrame({
            "group_id": [f"G-{self.seed}-{i:03d}" for i in range(self.n_groups)],
            "group_type": self._rng.choice(["security", "distribution"], size=self.n_groups, p=[0.7, 0.3]),
            "is_privileged": self._rng.random(self.n_groups) < 0.15,
        })

    def generate_group_membership_events(self, users: pd.DataFrame) -> pd.DataFrame:
        """~51 group membership events over 30-day window per seed."""
        n_events = max(1, int(self._rng.poisson(51)))
        user_ids = users["user_id"].values
        group_ids = [f"G-{self.seed}-{i:03d}" for i in range(self.n_groups)]
        return pd.DataFrame({
            "user_id": self._rng.choice(user_ids, size=n_events),
            "group_id": self._rng.choice(group_ids, size=n_events),
            "event_type": self._rng.choice(["add", "remove"], size=n_events, p=[0.75, 0.25]),
            "days_ago": self._rng.integers(0, 30, size=n_events),
        })

    def generate_vulnerability_records(self, computers: pd.DataFrame) -> pd.DataFrame:
        """
        Per-host CVE exposure records.

        Each host has a Poisson(cves_per_host_mean) number of applicable CVEs.
        EPSS drawn from synthetic fixture; CVSS from NVD distribution.
        KEV prevalence ~8%; patch lag from DBIR 2026 log-normal.
        """
        host_ids = computers["computer_id"].values
        rows = []
        cve_counter = 0

        for host_id in host_ids:
            n_cves = max(1, int(self._rng.poisson(self.cves_per_host_mean)))
            epss_scores = _sample_epss(n_cves, self._rng)
            cvss_scores = _sample_cvss(n_cves, self._rng)
            patch_lags = _sample_patch_lag_days(n_cves, self._rng)
            kev_flags = self._rng.random(n_cves) < 0.08
            kev_days = np.where(
                kev_flags,
                self._rng.integers(0, 365, size=n_cves),
                -1,
            ).astype(float)
            kev_days[~kev_flags] = np.nan

            for j in range(n_cves):
                patched = patch_lags[j] < 43  # median DBIR threshold
                rows.append({
                    "computer_id": host_id,
                    "cve_id": self._cve_id(cve_counter),
                    "epss_score": round(float(epss_scores[j]), 4),
                    "cvss_base_score": float(cvss_scores[j]),
                    "in_kev": bool(kev_flags[j]),
                    "days_since_kev_entry": float(kev_days[j]),
                    "patch_lag_days": round(float(patch_lags[j]), 1),
                    "patched": bool(patched),
                })
                cve_counter += 1

        return pd.DataFrame(rows)

    def generate_endpoint_patch_state(
        self, computers: pd.DataFrame, vulnerability_records: pd.DataFrame
    ) -> pd.DataFrame:
        """Summary patch state per host derived from vulnerability records."""
        summary = (
            vulnerability_records
            .groupby("computer_id")
            .agg(
                total_cves=("cve_id", "count"),
                patched_count=("patched", "sum"),
            )
            .reset_index()
        )
        summary["unpatched_count"] = summary["total_cves"] - summary["patched_count"]
        summary["patch_compliance_pct"] = (
            summary["patched_count"] / summary["total_cves"] * 100
        ).round(1)
        return summary

    def generate_telemetry_freshness_log(self, computers: pd.DataFrame) -> pd.DataFrame:
        """
        Per-host telemetry freshness log.

        CISA BOD 23-01: 72-hour patch data cadence (3-day ideal).
        Staleness distribution: mostly fresh, tail of 15-30+ day staleness.
        """
        host_ids = computers["computer_id"].values
        # Most hosts: 0-3 days stale; tail: exponential up to 30+ days
        stale_mask = self._rng.random(len(host_ids)) < 0.15  # 15% have notable staleness
        days = np.where(
            stale_mask,
            self._rng.exponential(10.0, len(host_ids)).clip(3, 60),
            self._rng.uniform(0.0, 3.0, len(host_ids)),
        )
        return pd.DataFrame({
            "computer_id": host_ids,
            "days_since_last_checkin": np.round(days, 1),
            "telemetry_source": self._rng.choice(
                ["endpoint_agent", "network_scan", "manual"],
                size=len(host_ids),
                p=[0.75, 0.20, 0.05],
            ),
        })

    def generate_all(self) -> dict[str, pd.DataFrame]:
        """Generate all tables for this fleet seed. Returns dict of DataFrames."""
        computers = self.generate_computers()
        users = self.generate_users()
        groups = self.generate_groups()
        gme = self.generate_group_membership_events(users)
        vuln_records = self.generate_vulnerability_records(computers)
        patch_state = self.generate_endpoint_patch_state(computers, vuln_records)
        telemetry = self.generate_telemetry_freshness_log(computers)

        return {
            "computers": computers,
            "users": users,
            "groups": groups,
            "group_membership_events": gme,
            "vulnerability_records": vuln_records,
            "endpoint_patch_state": patch_state,
            "telemetry_freshness_log": telemetry,
        }
