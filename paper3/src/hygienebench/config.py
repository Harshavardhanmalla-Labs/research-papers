"""
Configuration dataclasses for the HygieneBench synthetic generator.

All parameters have research-grounded defaults documented in STEP2_DATASET_FEASIBILITY.md.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PopulationConfig:
    """Controls synthetic population size and structural parameters."""
    n_users: int = 1000
    n_business_groups: int = 40            # Non-privileged security groups
    n_privileged_groups: int = 5           # Domain Admins equivalents
    n_distribution_groups: int = 20        # Distribution groups (mail, comms)
    computers_per_user_ratio: float = 0.9  # Most users have a primary computer
    n_extra_servers: int = 20              # Server-only machines
    privileged_user_rate: float = 0.05    # 5% of users in >= 1 privileged group
    service_account_rate: float = 0.10    # 10% of accounts are service accounts
    n_ou_depth: int = 3                    # OU hierarchy depth
    n_departments: int = 8                 # Business departments

    def __post_init__(self):
        assert 0 < self.privileged_user_rate < 0.20, "Privileged rate should be 1-20%"
        assert 0 < self.service_account_rate < 0.30, "Service account rate should be 1-30%"


@dataclass
class PatchConfig:
    """Patch lag and compliance parameters. Priors: DBIR 2026, NIST SP 800-40 Rev.4."""
    baseline_compliance_rate: float = 0.85       # Fraction of patches applied on schedule
    critical_patch_lag_mean_days: float = 15.0   # Mean lag for critical patches (DBIR: 43d avg across all orgs)
    critical_patch_lag_std_days: float = 12.0
    high_patch_lag_mean_days: float = 30.0
    medium_patch_lag_mean_days: float = 60.0
    kev_rate: float = 0.05                        # ~5% of CVEs flagged as KEV
    cvss_score_mean: float = 6.5                  # NVD empirical mean ~6-7
    cvss_score_std: float = 1.8
    max_open_cves_per_host: int = 20              # Cap for synthetic generation
    mean_open_cves_per_host: float = 4.0          # Mean open CVEs per non-compliant host


@dataclass
class ConditionConfig:
    """
    Telemetry freshness and missingness regime.
    Maps to C-BASE, C-FRESH, C-STALE, C-MISS, C-UNSUP from EXPERIMENTAL_DESIGN_v0_1.md.
    """
    condition_id: str = "c_base"

    # Staleness: fraction of entities that receive a staleness flag
    stale_rate: float = 0.0               # fraction of entities with stale telemetry
    stale_severity: str = "fresh"         # 'fresh', 'stale_mild', 'stale_heavy'

    # Missingness: which source(s) are missing for affected entities
    missing_sources: List[str] = field(default_factory=list)  # e.g. ['edr_agent']
    missing_source_rate: float = 0.0      # fraction of entities missing each source
    ou_level_gap: bool = False            # True: one entire OU loses all telemetry

    # Label visibility (for C-UNSUP)
    labels_visible_at_train: bool = True  # False = purely unsupervised condition

    @classmethod
    def c_base(cls) -> "ConditionConfig":
        return cls(condition_id="c_base")

    @classmethod
    def c_fresh(cls) -> "ConditionConfig":
        return cls(
            condition_id="c_fresh",
            stale_rate=0.0,
            stale_severity="fresh",
            missing_sources=["patch_mgmt"],
            missing_source_rate=0.10,
        )

    @classmethod
    def c_stale(cls) -> "ConditionConfig":
        return cls(
            condition_id="c_stale",
            stale_rate=0.20,
            stale_severity="stale_heavy",
            missing_sources=[],
            missing_source_rate=0.0,
        )

    @classmethod
    def c_miss(cls) -> "ConditionConfig":
        return cls(
            condition_id="c_miss",
            stale_rate=0.20,
            stale_severity="stale_heavy",
            missing_sources=["patch_mgmt", "vuln_scanner"],
            missing_source_rate=0.15,
            ou_level_gap=True,
        )

    @classmethod
    def c_unsup(cls) -> "ConditionConfig":
        return cls(
            condition_id="c_unsup",
            stale_rate=0.15,
            stale_severity="stale_mild",
            missing_sources=["edr_agent"],
            missing_source_rate=0.10,
            labels_visible_at_train=False,
        )


@dataclass
class AnomalyConfig:
    """
    Anomaly injection rates per anomaly class.
    Default rates produce the class imbalance ratios documented in TASK_SPECS.md.
    """
    # T1: stale privileged account (injected among privileged users only)
    t1_stale_priv_n: int = 4              # absolute count of anomalies (not rate; small pool)

    # T2: group membership drift
    t2_drift_n: int = 4                   # cross-OU membership adds
    t2_escalation_n: int = 2             # privileged group adds without role-change

    # T3: endpoint-identity risk correlation
    t3_risk_pair_n: int = 3              # high-risk (user, computer) pairs

    # T4: telemetry missingness
    t4_missing_agent_rate: float = 0.05  # fraction of computers missing agent
    t4_inventory_mismatch_rate: float = 0.04
    t4_cluster_ou: Optional[str] = None  # if None, pick a random OU at inject time

    # T5: patch/vuln hygiene
    t5_noncompliant_cluster_size: int = 8  # OU cluster size with low compliance
    t5_kev_n: int = 5                       # KEV CVEs aged >= 30 days
    t5_delay_n: int = 4                     # remediations with abnormal delay (>90d)

    # T6: dormant reactivation
    t6_dormant_n: int = 4                  # anomalous reactivations (>180d dormant + odd login)

    # T7: multi-step escalation drift
    t7_escalation_n: int = 2              # users with 3-5 group additions over 30d


@dataclass
class GeneratorConfig:
    """Top-level configuration for a single benchmark dataset generation run."""
    seed: int = 42
    population: PopulationConfig = field(default_factory=PopulationConfig)
    patch: PatchConfig = field(default_factory=PatchConfig)
    condition: ConditionConfig = field(default_factory=ConditionConfig.c_base)
    anomaly: AnomalyConfig = field(default_factory=AnomalyConfig)
    tasks: List[str] = field(default_factory=lambda: ["T1", "T2", "T3", "T4", "T5", "T6", "T7"])

    # Temporal window
    obs_window_days: int = 90            # Observation window length
    history_days: int = 365             # Historical data before obs window

    # Schema version (must match SCHEMA_v0_1.md)
    schema_version: str = "v0.1"
    generator_version: str = "v0.1"

    @classmethod
    def small(cls, seed: int = 42, condition: Optional[ConditionConfig] = None) -> "GeneratorConfig":
        pop = PopulationConfig(n_users=200, n_business_groups=15, n_privileged_groups=3,
                                n_extra_servers=5)
        return cls(seed=seed, population=pop,
                   condition=condition or ConditionConfig.c_base())

    @classmethod
    def medium(cls, seed: int = 42, condition: Optional[ConditionConfig] = None) -> "GeneratorConfig":
        return cls(seed=seed, condition=condition or ConditionConfig.c_base())

    @classmethod
    def large(cls, seed: int = 42, condition: Optional[ConditionConfig] = None) -> "GeneratorConfig":
        pop = PopulationConfig(n_users=5000, n_business_groups=120, n_privileged_groups=8,
                                n_extra_servers=80)
        return cls(seed=seed, population=pop,
                   condition=condition or ConditionConfig.c_base())
