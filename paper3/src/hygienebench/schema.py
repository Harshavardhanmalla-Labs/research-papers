"""
Schema enumerations matching SCHEMA_v0_1.md.

All field names, enum values, and table structures here are authoritative for v0.1.
"""

from enum import Enum


class FreshnessFlag(str, Enum):
    FRESH = "fresh"
    STALE_MILD = "stale_mild"
    STALE_HEAVY = "stale_heavy"
    MISSING = "missing"


class AssetCriticality(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


CRITICALITY_ORDINAL = {
    AssetCriticality.LOW: 1,
    AssetCriticality.MEDIUM: 2,
    AssetCriticality.HIGH: 3,
    AssetCriticality.CRITICAL: 4,
}


class OsType(str, Enum):
    WINDOWS_WORKSTATION = "windows_workstation"
    WINDOWS_SERVER = "windows_server"
    LINUX_SERVER = "linux_server"


class NetworkSegment(str, Enum):
    WORKSTATION = "workstation"
    SERVER = "server"
    DMZ = "dmz"
    PRIVILEGED = "privileged"


class GroupType(str, Enum):
    SECURITY = "security"
    DISTRIBUTION = "distribution"


class RemediationAction(str, Enum):
    PATCH_APPLIED = "patch_applied"
    DEFERRED = "deferred"
    FALSE_CLOSED = "false_closed"
    EXCEPTION_GRANTED = "exception_granted"


class AccountAction(str, Enum):
    CREATED = "created"
    ENABLED = "enabled"
    DISABLED = "disabled"
    REACTIVATED = "reactivated"
    PASSWORD_RESET = "password_reset"
    DELETED = "deleted"


class LogonType(str, Enum):
    INTERACTIVE = "interactive"
    NETWORK = "network"
    REMOTE_INTERACTIVE = "remote_interactive"
    SERVICE = "service"


class AnomalyClass(str, Enum):
    STALE_PRIVILEGED_ACCOUNT = "stale_privileged_account"            # AH-01
    PRIVILEGE_ESCALATION_DRIFT = "privilege_escalation_drift"        # AH-02
    GROUP_MEMBERSHIP_DRIFT = "group_membership_drift"                # AH-03
    DORMANT_ACCOUNT_REACTIVATION = "dormant_account_reactivation"    # AH-04
    IMPOSSIBLE_OR_UNUSUAL_LOGIN = "impossible_or_unusual_login"      # AH-05
    ENDPOINT_IDENTITY_RISK_CORRELATION = "endpoint_identity_risk_correlation"  # AH-06
    PATCH_NONCOMPLIANCE_CLUSTER = "patch_noncompliance_cluster"      # AH-07
    KEV_EXPOSURE_AGING = "kev_exposure_aging"                        # AH-08
    ASSET_INVENTORY_MISMATCH = "asset_inventory_mismatch"            # AH-09
    MISSING_ENDPOINT_AGENT = "missing_endpoint_agent"                # AH-10
    TELEMETRY_MISSINGNESS_CLUSTER = "telemetry_missingness_cluster"  # AH-11
    ABNORMAL_REMEDIATION_DELAY = "abnormal_remediation_delay"        # AH-12


# Tasks to anomaly class mapping (from TASK_SPECS.md)
TASK_ANOMALY_CLASSES = {
    "T1": [AnomalyClass.STALE_PRIVILEGED_ACCOUNT, AnomalyClass.IMPOSSIBLE_OR_UNUSUAL_LOGIN],
    "T2": [AnomalyClass.GROUP_MEMBERSHIP_DRIFT, AnomalyClass.PRIVILEGE_ESCALATION_DRIFT],
    "T3": [AnomalyClass.ENDPOINT_IDENTITY_RISK_CORRELATION, AnomalyClass.KEV_EXPOSURE_AGING,
           AnomalyClass.MISSING_ENDPOINT_AGENT],
    "T4": [AnomalyClass.ASSET_INVENTORY_MISMATCH, AnomalyClass.MISSING_ENDPOINT_AGENT,
           AnomalyClass.TELEMETRY_MISSINGNESS_CLUSTER],
    "T5": [AnomalyClass.PATCH_NONCOMPLIANCE_CLUSTER, AnomalyClass.KEV_EXPOSURE_AGING,
           AnomalyClass.ABNORMAL_REMEDIATION_DELAY],
    "T6": [AnomalyClass.DORMANT_ACCOUNT_REACTIVATION, AnomalyClass.IMPOSSIBLE_OR_UNUSUAL_LOGIN],
    "T7": [AnomalyClass.PRIVILEGE_ESCALATION_DRIFT],
}

# CVSS severity bands
CVSS_CRITICAL_MIN = 9.0
CVSS_HIGH_MIN = 7.0
CVSS_MEDIUM_MIN = 4.0


def cvss_to_severity(score: float) -> str:
    if score >= CVSS_CRITICAL_MIN:
        return "critical"
    if score >= CVSS_HIGH_MIN:
        return "high"
    if score >= CVSS_MEDIUM_MIN:
        return "medium"
    return "low"
