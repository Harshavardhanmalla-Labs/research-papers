"""Audit-evidence schemas, append-only logging, and hash-chain integrity."""

from paper1.audit.hash_chain import (
    AuditLogger,
    compute_record_hash,
    verify_chain,
)
from paper1.audit.schema import (
    AssetCriticalityProfile,
    AuditDecisionRecord,
    ExperimentConfig,
    ExploitSignal,
    Host,
    InstalledSoftware,
    LocalExposureProfile,
    MetricResult,
    OutcomeRecord,
    PatchState,
    RemediationAction,
    RemediationComplexityProfile,
    StrategyResult,
    Vulnerability,
    VulnerabilityHostPair,
)

__all__ = [
    "AssetCriticalityProfile",
    "AuditDecisionRecord",
    "AuditLogger",
    "ExperimentConfig",
    "ExploitSignal",
    "Host",
    "InstalledSoftware",
    "LocalExposureProfile",
    "MetricResult",
    "OutcomeRecord",
    "PatchState",
    "RemediationAction",
    "RemediationComplexityProfile",
    "StrategyResult",
    "Vulnerability",
    "VulnerabilityHostPair",
    "compute_record_hash",
    "verify_chain",
]
