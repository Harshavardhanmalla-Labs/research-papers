"""Pydantic v2 schemas for every entity referenced in the methodology.

All models are frozen and forbid extra fields. Datetime fields are UTC.
Hash fields are validated as 64-char lowercase hex SHA-256.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

# ---------------------------------------------------------------------------
# Reusable validators
# ---------------------------------------------------------------------------

_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_CWE_RE = re.compile(r"^CWE-\d+$")


def _validate_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware (UTC required)")
    if dt.tzinfo.utcoffset(dt) != UTC.utcoffset(dt):
        # Accept any tzinfo whose UTC offset is zero; reject otherwise.
        offset = dt.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise ValueError("Datetime must be UTC (zero UTC offset)")
    return dt


# ---------------------------------------------------------------------------
# Literal type aliases
# ---------------------------------------------------------------------------

OSFamily = Literal[
    "windows_workstation",
    "windows_server",
    "linux",
    "macos",
    "ios",
    "android",
    "other",
]
Role = Literal[
    "standard_workstation",
    "privileged_workstation",
    "member_server",
    "domain_controller",
    "kiosk",
    "mobile_device",
    "public_facing_server",
    "restricted_zone_system",
    "buffer",
]
Zone = Literal["public", "dmz", "internal", "restricted", "air_gapped"]
IdentityTier = Literal["tier_0", "tier_1", "tier_2", "non_ad"]
DataSensitivity = Literal["cji", "pii", "phi", "cui", "general", "non_sensitive"]
PairStatus = Literal[
    "open", "scheduled", "remediated", "deferred", "accepted_risk", "excluded"
]
DecisionType = Literal[
    "score", "schedule", "approve", "accept_risk", "defer", "outcome"
]
MatchMethod = Literal["cpe_exact", "cpe_fuzzy", "manual"]
ActionType = Literal["patch_apply", "mitigation_apply", "accept_risk", "defer"]
ApprovalStatus = Literal["pending", "approved", "rejected", "modified"]
DeploymentStatus = Literal["success", "failed", "rolled_back", "not_attempted"]
AttributionConfidence = Literal["high", "medium", "low"]


# ---------------------------------------------------------------------------
# Frozen-model base
# ---------------------------------------------------------------------------


class _FrozenBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=False)


# ---------------------------------------------------------------------------
# Component models
# ---------------------------------------------------------------------------


class InstalledSoftware(_FrozenBase):
    cpe: str
    product: str
    vendor: str
    version: str
    install_date: date | None = None


class PatchState(_FrozenBase):
    kbs_installed: list[str] = Field(default_factory=list)
    last_scan: datetime
    scan_source: str
    # CVEs explicitly recorded as remediated on this host. Used by the
    # pair builder to exclude already-closed vulnerability-host pairs.
    remediated_cves: list[str] = Field(default_factory=list)

    @field_validator("last_scan")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return _validate_utc(v)

    @field_validator("remediated_cves")
    @classmethod
    def _cve_ids(cls, v: list[str]) -> list[str]:
        for c in v:
            if not _CVE_RE.match(c):
                raise ValueError(f"Invalid CVE id in remediated_cves: {c!r}")
        return v


# ---------------------------------------------------------------------------
# Vulnerability
# ---------------------------------------------------------------------------


class Vulnerability(_FrozenBase):
    cve_id: str
    cwe_ids: list[str] = Field(default_factory=list)
    cpe_matches: list[str] = Field(min_length=1)
    cvss_v4_vector: str | None = None
    cvss_v4_base: float | None = None
    cvss_v31_vector: str | None = None
    cvss_v31_base: float | None = None
    cvss_version_used: Literal["v4", "v31"]
    disclosure_date: date
    vendor_advisory_refs: list[str] = Field(default_factory=list)
    mitigations_listed: list[dict[str, Any]] = Field(default_factory=list)
    preconditions: dict[str, Any] = Field(default_factory=dict)
    feed_fetch_timestamp: datetime

    @field_validator("cve_id")
    @classmethod
    def _cve_id(cls, v: str) -> str:
        if not _CVE_RE.match(v):
            raise ValueError(f"Invalid CVE id: {v!r}")
        return v

    @field_validator("cwe_ids")
    @classmethod
    def _cwe_ids(cls, v: list[str]) -> list[str]:
        for c in v:
            if not _CWE_RE.match(c):
                raise ValueError(f"Invalid CWE id: {c!r}")
        return v

    @field_validator("cvss_v4_base", "cvss_v31_base")
    @classmethod
    def _cvss_range(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 10.0):
            raise ValueError(f"CVSS base must be in [0, 10]; got {v}")
        return v

    @field_validator("feed_fetch_timestamp")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return _validate_utc(v)

    @model_validator(mode="after")
    def _check_cvss_consistency(self) -> Vulnerability:
        if self.cvss_version_used == "v4" and (
            self.cvss_v4_vector is None or self.cvss_v4_base is None
        ):
            raise ValueError("cvss_version_used=v4 requires v4 vector and base")
        if self.cvss_version_used == "v31" and (
            self.cvss_v31_vector is None or self.cvss_v31_base is None
        ):
            raise ValueError("cvss_version_used=v31 requires v3.1 vector and base")
        return self


# ---------------------------------------------------------------------------
# Host
# ---------------------------------------------------------------------------


class Host(_FrozenBase):
    host_id: str
    os_family: OSFamily
    os_version: str
    role: Role
    network_zone: Zone
    identity_tier: IdentityTier
    data_sensitivity_proxy: DataSensitivity | None = None
    installed_software: list[InstalledSoftware] = Field(default_factory=list)
    patch_state: PatchState
    last_seen_per_source: dict[str, datetime]
    staleness_flags: list[str] = Field(default_factory=list)
    cmdb_tags: dict[str, str] | None = None
    group_id: str

    @field_validator("last_seen_per_source")
    @classmethod
    def _utc_dict(cls, v: dict[str, datetime]) -> dict[str, datetime]:
        for _source, dt in v.items():
            _validate_utc(dt)
        return v


# ---------------------------------------------------------------------------
# Vulnerability-host pair
# ---------------------------------------------------------------------------


class VulnerabilityHostPair(_FrozenBase):
    pair_id: str
    cve_id: str
    host_id: str
    match_method: MatchMethod
    match_confidence: float = Field(ge=0.0, le=1.0)
    pair_status: PairStatus
    first_observed: datetime
    pair_origin_feeds: list[str] = Field(default_factory=list)

    @field_validator("cve_id")
    @classmethod
    def _cve_id(cls, v: str) -> str:
        if not _CVE_RE.match(v):
            raise ValueError(f"Invalid CVE id: {v!r}")
        return v

    @field_validator("first_observed")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return _validate_utc(v)


# ---------------------------------------------------------------------------
# Exploit signal
# ---------------------------------------------------------------------------


class ExploitSignal(_FrozenBase):
    cve_id: str
    epss_score: float = Field(ge=0.0, le=1.0)
    epss_percentile: float = Field(ge=0.0, le=1.0)
    epss_fetch_timestamp: datetime
    epss_version: str
    kev_status: bool
    kev_date_added: date | None = None
    kev_due_date: date | None = None
    kev_required_action: str | None = None
    poc_observed: bool
    poc_first_seen: datetime | None = None
    signal_staleness_days: int = Field(ge=0)

    @field_validator("cve_id")
    @classmethod
    def _cve_id(cls, v: str) -> str:
        if not _CVE_RE.match(v):
            raise ValueError(f"Invalid CVE id: {v!r}")
        return v

    @field_validator("epss_fetch_timestamp")
    @classmethod
    def _utc_fetch(cls, v: datetime) -> datetime:
        return _validate_utc(v)

    @field_validator("poc_first_seen")
    @classmethod
    def _utc_poc(cls, v: datetime | None) -> datetime | None:
        return _validate_utc(v) if v is not None else None


# ---------------------------------------------------------------------------
# Asset criticality
# ---------------------------------------------------------------------------


def _zero_one(v: float) -> float:
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"Value must be in [0, 1]; got {v}")
    return v


class AssetCriticalityProfile(_FrozenBase):
    host_id: str
    criticality_score: float = Field(ge=0.0, le=1.0)
    subscore_role: float = Field(ge=0.0, le=1.0)
    subscore_identity: float = Field(ge=0.0, le=1.0)
    subscore_network: float = Field(ge=0.0, le=1.0)
    subscore_data: float = Field(ge=0.0, le=1.0)
    subscore_cmdb: float | None = None
    derivation_method: str
    identity_mapping_config: str
    inputs_missing: list[str] = Field(default_factory=list)
    computed_at: datetime

    @field_validator("subscore_cmdb")
    @classmethod
    def _cmdb_range(cls, v: float | None) -> float | None:
        return _zero_one(v) if v is not None else None

    @field_validator("computed_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return _validate_utc(v)


# ---------------------------------------------------------------------------
# Local exposure
# ---------------------------------------------------------------------------


class LocalExposureProfile(_FrozenBase):
    pair_id: str
    exposure_score: float = Field(ge=0.0, le=1.0)
    factor_installed_vuln: float = Field(ge=0.0, le=1.0)
    factor_service_running: float = Field(ge=0.0, le=1.0)
    factor_network_reachable: float = Field(ge=0.0, le=1.0)
    factor_mitigation_present: float = Field(ge=0.0, le=1.0)
    factor_auth_precondition_met: float = Field(ge=0.0, le=1.0)
    preconditions_unknown: list[str] = Field(default_factory=list)
    mitigations_observed: list[str] = Field(default_factory=list)
    reachability_assumption: str
    evaluator_version: str


# ---------------------------------------------------------------------------
# Remediation complexity
# ---------------------------------------------------------------------------


class RemediationComplexityProfile(_FrozenBase):
    pair_id: str
    complexity_score: float = Field(ge=0.0, le=1.0)
    factor_reboot: float = Field(ge=0.0, le=1.0)
    factor_user_disruption: float = Field(ge=0.0, le=1.0)
    factor_service_dep: float = Field(ge=0.0, le=1.0)
    factor_regression: float = Field(ge=0.0, le=1.0)
    factor_channel: float = Field(ge=0.0, le=1.0)
    factor_bundle: float = Field(ge=0.0, le=1.0)
    host_modifier: float


# ---------------------------------------------------------------------------
# Remediation action
# ---------------------------------------------------------------------------


class RemediationAction(_FrozenBase):
    action_id: str
    pair_id: str
    window_id: str
    action_type: ActionType
    proposed_by: str
    approval_status: ApprovalStatus


# ---------------------------------------------------------------------------
# Audit decision record
# ---------------------------------------------------------------------------


class AuditDecisionRecord(_FrozenBase):
    record_id: str
    pair_id: str
    window_id: str
    decision_type: DecisionType
    priority_score: float | None = None
    feature_values: dict[str, float] | None = None
    feature_contributions: dict[str, float] | None = None
    weights_version: str
    data_feed_versions: dict[str, str]
    imputations_applied: list[dict[str, Any]] | None = None
    approver_id: str | None = None
    approver_decision: str | None = None
    approver_comments: str | None = None
    risk_acceptance_reason: str | None = None
    risk_acceptance_compensating_controls: list[str] | None = None
    risk_acceptance_expiration_date: date | None = None
    risk_acceptance_review_trigger: str | None = None
    risk_acceptance_approver_id: str | None = None
    framework_version: str
    record_hash: str
    prior_record_hash: str
    created_at: datetime

    @field_validator("record_hash", "prior_record_hash")
    @classmethod
    def _hex(cls, v: str) -> str:
        if not _SHA256_HEX_RE.match(v):
            raise ValueError("Hash must be 64-character lowercase hexadecimal SHA-256")
        return v

    @field_validator("created_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return _validate_utc(v)

    @model_validator(mode="after")
    def _check_required_by_decision_type(self) -> AuditDecisionRecord:
        if self.decision_type == "score":
            if self.feature_values is None:
                raise ValueError("decision_type=score requires feature_values")
            if self.feature_contributions is None:
                raise ValueError("decision_type=score requires feature_contributions")
        if self.decision_type == "accept_risk":
            missing = []
            if self.risk_acceptance_reason is None:
                missing.append("risk_acceptance_reason")
            if self.risk_acceptance_approver_id is None:
                missing.append("risk_acceptance_approver_id")
            if self.risk_acceptance_expiration_date is None:
                missing.append("risk_acceptance_expiration_date")
            if missing:
                raise ValueError(
                    "decision_type=accept_risk requires: " + ", ".join(missing)
                )
        return self


# ---------------------------------------------------------------------------
# Outcome record
# ---------------------------------------------------------------------------


class OutcomeRecord(_FrozenBase):
    outcome_id: str
    pair_id: str
    window_id: str
    deployment_status: DeploymentStatus | None = None
    deployment_timestamp: datetime | None = None
    time_to_remediate_days: float | None = None
    regression_detected: bool | None = None
    regression_description: str | None = None
    subsequent_kev_addition: bool | None = None
    subsequent_exploit_observed: bool | None = None
    attribution_confidence: AttributionConfidence | None = None

    @field_validator("deployment_timestamp")
    @classmethod
    def _utc(cls, v: datetime | None) -> datetime | None:
        return _validate_utc(v) if v is not None else None


# ---------------------------------------------------------------------------
# Experiment / strategy / metric
# ---------------------------------------------------------------------------


class ExperimentConfig(_FrozenBase):
    config_name: str
    seed_master: int
    fleet_size: int = Field(gt=0)
    capacity_ratio: float = Field(gt=0.0, le=1.0)
    label: Literal["A", "B"]
    approver_policy: Literal["A", "B"]
    identity_config: str
    blackout_config: str
    epss_version_handling: str
    data_window_start: date
    data_window_end: date
    H_days: int = Field(gt=0)
    train_split_months: int = Field(gt=0)
    strategies: list[str] = Field(min_length=1)
    seed_count: int = Field(gt=0)
    maintenance_cadence_days: int = Field(gt=0)
    remediation_failure_rate: float = Field(ge=0.0, le=1.0)
    rollback_probability_given_failure: float = Field(ge=0.0, le=1.0)
    output_dir: str
    code_commit_sha: str | None = None
    feed_snapshot_manifest_sha: str | None = None

    @model_validator(mode="after")
    def _window_order(self) -> ExperimentConfig:
        if self.data_window_end <= self.data_window_start:
            raise ValueError("data_window_end must be after data_window_start")
        return self


class StrategyResult(_FrozenBase):
    experiment_config_sha: str
    strategy_name: str
    seed: int
    per_window_results_path: str
    audit_log_path: str

    @field_validator("experiment_config_sha")
    @classmethod
    def _sha(cls, v: str) -> str:
        if not _SHA256_HEX_RE.match(v):
            raise ValueError("experiment_config_sha must be 64-char lowercase hex")
        return v


class MetricResult(_FrozenBase):
    experiment_config_sha: str
    cell_id: str
    strategy: str
    metric: str
    point: float
    ci_low: float | None = None
    ci_high: float | None = None
    seed_count: int = Field(gt=0)
    method: str
    family_alpha: float | None = None
    p_value_vs_baseline: float | None = None
    p_value_holm_adjusted: float | None = None
    notes: str = ""

    @field_validator("experiment_config_sha")
    @classmethod
    def _sha(cls, v: str) -> str:
        if not _SHA256_HEX_RE.match(v):
            raise ValueError("experiment_config_sha must be 64-char lowercase hex")
        return v
