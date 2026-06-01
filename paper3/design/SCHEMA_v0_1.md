# Paper 3 — Synthetic Telemetry Schema v0.1

**Date:** 2026-05-28
**Status:** Locked for Step 2. No implementation yet. This is a specification document only.
**Companion:** `STEP2_DATASET_FEASIBILITY.md`

---

## Overview

This schema defines the structure of the synthetic cyber-hygiene telemetry dataset generated for Paper 3. All data is synthetic and seeded. No real user, device, or organizational data is used. The schema covers six entity classes and seven event/state record types.

Version 0.1 is a design spec. Implementation begins at Step 3 (not yet authorized).

---

## Design Principles

1. **Seeded determinism.** Every generation run with the same seed produces byte-identical output.
2. **Entity-state model.** The primary unit of analysis is the *entity at a point in time*, not a flow or packet. An entity can be a user, group, computer, or asset.
3. **Multi-domain coverage.** The schema deliberately spans four domains: identity (AD), endpoint (EDR/patch), vulnerability, and telemetry meta. Cross-domain correlation is a first-class design requirement.
4. **Telemetry freshness as a first-class field.** Every record carries a `last_updated_at` and a `source_freshness_flag`. Staleness and missingness are injected systematically.
5. **Anomaly labels are ground-truth.** Injected anomalies carry explicit labels, severity, class, and timestamps. Labels are stored separately from the observation table to prevent label-leakage in feature engineering.
6. **No PII.** All entity identifiers are synthetic UUIDs plus human-readable aliases generated from publicly available wordlists (not real names).

---

## Entity Tables

### E1 — `users`

| Field | Type | Description |
|---|---|---|
| `user_id` | UUID | Synthetic primary key |
| `username` | str | Synthetic alias (e.g., `user_a0042`) |
| `display_name` | str | Synthetic display name |
| `department` | str | Synthetic org unit name |
| `ou_path` | str | Synthetic OU hierarchy (e.g., `OU=Finance,DC=corp,DC=local`) |
| `account_enabled` | bool | Active / disabled status |
| `account_created_at` | datetime | Synthetic creation timestamp |
| `account_last_logon` | datetime | Most recent logon event timestamp |
| `days_since_last_logon` | int | Derived; key hygiene signal |
| `is_privileged` | bool | Member of at least one privileged group |
| `privileged_group_count` | int | Count of privileged group memberships |
| `is_service_account` | bool | Service account flag |
| `password_last_set` | datetime | Synthetic password change timestamp |
| `days_since_password_change` | int | Derived |
| `mfa_enabled` | bool | Synthetic MFA status |
| `source_freshness_flag` | enum | `fresh` / `stale_mild` / `stale_heavy` / `missing` |
| `last_updated_at` | datetime | Timestamp of last telemetry record for this user |

---

### E2 — `groups`

| Field | Type | Description |
|---|---|---|
| `group_id` | UUID | Synthetic primary key |
| `group_name` | str | Synthetic alias |
| `group_type` | enum | `security` / `distribution` |
| `is_privileged` | bool | Domain Admins, Enterprise Admins, or equivalent |
| `member_count` | int | Current synthetic member count |
| `ou_path` | str | Synthetic OU path |
| `baseline_member_ids` | list[UUID] | Snapshot at T=0; used for drift detection |
| `source_freshness_flag` | enum | `fresh` / `stale_mild` / `stale_heavy` / `missing` |
| `last_updated_at` | datetime | Timestamp of last telemetry for this group |

---

### E3 — `computers`

| Field | Type | Description |
|---|---|---|
| `computer_id` | UUID | Synthetic primary key |
| `hostname` | str | Synthetic alias (e.g., `ws-0042`) |
| `os_type` | enum | `windows_workstation` / `windows_server` / `linux_server` |
| `os_version` | str | Synthetic version string |
| `network_segment` | enum | `workstation` / `server` / `dmz` / `privileged` |
| `primary_user_id` | UUID | FK → `users` (nullable for shared/service hosts) |
| `asset_criticality` | enum | `critical` / `high` / `medium` / `low` |
| `endpoint_agent_installed` | bool | EDR/management agent present |
| `endpoint_agent_last_heartbeat` | datetime | Last agent check-in |
| `days_since_agent_heartbeat` | int | Derived; key hygiene signal |
| `source_freshness_flag` | enum | `fresh` / `stale_mild` / `stale_heavy` / `missing` |
| `last_updated_at` | datetime | Timestamp of last telemetry for this computer |

---

### E4 — `assets`

| Field | Type | Description |
|---|---|---|
| `asset_id` | UUID | Synthetic primary key; may overlap with `computer_id` for managed endpoints |
| `asset_type` | enum | `endpoint` / `server` / `network_device` / `cloud_resource` |
| `asset_criticality` | enum | `critical` / `high` / `medium` / `low` |
| `owner_ou` | str | Owning organizational unit |
| `in_inventory` | bool | Appears in asset inventory |
| `in_endpoint_mgmt` | bool | Appears in endpoint management system |
| `inventory_mismatch_flag` | bool | Asset in one system but not the other (hygiene anomaly class) |
| `source_freshness_flag` | enum | `fresh` / `stale_mild` / `stale_heavy` / `missing` |
| `last_updated_at` | datetime | Timestamp of last inventory record |

---

## Event/State Record Tables

### R1 — `login_events`

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | Synthetic event key |
| `user_id` | UUID | FK → `users` |
| `computer_id` | UUID | FK → `computers` |
| `event_timestamp` | datetime | Synthetic timestamp |
| `logon_type` | enum | `interactive` / `network` / `remote_interactive` / `service` |
| `success` | bool | Success / failure |
| `is_off_hours` | bool | Derived from business-hours model |
| `is_cross_segment` | bool | Login from non-primary segment |
| `is_anomalous` | bool | Anomaly injection flag (ground truth) |
| `anomaly_class` | str | Null unless injected; e.g., `impossible_location`, `dormant_reactivation` |

---

### R2 — `group_membership_events`

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | Synthetic event key |
| `user_id` | UUID | FK → `users` |
| `group_id` | UUID | FK → `groups` |
| `action` | enum | `add` / `remove` |
| `event_timestamp` | datetime | Synthetic timestamp |
| `actor_user_id` | UUID | Who made the change (FK → `users`) |
| `is_privileged_group` | bool | Target group is privileged |
| `is_anomalous` | bool | Anomaly injection flag |
| `anomaly_class` | str | Null unless injected; e.g., `privilege_escalation_drift`, `group_membership_drift` |

---

### R3 — `endpoint_patch_state`

| Field | Type | Description |
|---|---|---|
| `record_id` | UUID | Synthetic record key |
| `computer_id` | UUID | FK → `computers` |
| `snapshot_timestamp` | datetime | When this patch state was observed |
| `missing_patch_count` | int | Count of missing patches |
| `critical_missing_patch_count` | int | Count of missing critical/KEV patches |
| `patch_compliance_score` | float | 0.0–1.0 |
| `days_since_last_patch_applied` | int | Patch lag signal |
| `open_kev_count` | int | Count of open KEV-flagged CVEs |
| `source_freshness_flag` | enum | `fresh` / `stale_mild` / `stale_heavy` / `missing` |
| `last_updated_at` | datetime | Timestamp of this record |
| `is_anomalous` | bool | Anomaly injection flag |
| `anomaly_class` | str | Null unless injected; e.g., `patch_noncompliance_cluster`, `kev_exposure_aging` |

---

### R4 — `vulnerability_records`

| Field | Type | Description |
|---|---|---|
| `record_id` | UUID | Synthetic record key |
| `computer_id` | UUID | FK → `computers` |
| `cve_id` | str | Synthetic CVE-analog (e.g., `CVE-SYNTH-2024-00042`) |
| `cvss_score` | float | Synthetic CVSS v3 base score |
| `cvss_severity` | enum | `critical` / `high` / `medium` / `low` |
| `is_kev_flagged` | bool | Synthetic KEV flag |
| `cve_published_days_ago` | int | Age of the CVE |
| `first_observed_at` | datetime | When vulnerability first appeared in scanner output |
| `days_open` | int | Duration unpatched |
| `remediation_status` | enum | `open` / `patched` / `deferred` / `false_positive` |
| `asset_criticality` | enum | FK-derived from `computers.asset_criticality` |
| `exposed_privileged_user_count` | int | Count of privileged users whose primary asset has this CVE open |
| `source_freshness_flag` | enum | `fresh` / `stale_mild` / `stale_heavy` / `missing` |
| `last_updated_at` | datetime | Timestamp of this record |
| `is_anomalous` | bool | Anomaly injection flag |
| `anomaly_class` | str | Null unless injected |

---

### R5 — `remediation_events`

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | Synthetic event key |
| `computer_id` | UUID | FK → `computers` |
| `cve_id` | str | Synthetic CVE-analog |
| `action_type` | enum | `patch_applied` / `deferred` / `false_closed` / `exception_granted` |
| `action_timestamp` | datetime | Synthetic timestamp |
| `actor_type` | enum | `automated` / `manual` |
| `remediation_latency_days` | int | Days from first observation to remediation |
| `is_anomalous` | bool | Anomaly injection flag |
| `anomaly_class` | str | Null unless injected; e.g., `abnormal_remediation_delay` |

---

### R6 — `account_lifecycle_events`

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | Synthetic event key |
| `user_id` | UUID | FK → `users` |
| `action` | enum | `created` / `enabled` / `disabled` / `reactivated` / `password_reset` / `deleted` |
| `event_timestamp` | datetime | Synthetic timestamp |
| `actor_user_id` | UUID | Who performed the action |
| `days_since_last_logon_at_action` | int | User inactivity at time of reactivation (if applicable) |
| `is_anomalous` | bool | Anomaly injection flag |
| `anomaly_class` | str | Null unless injected; e.g., `dormant_account_reactivation`, `stale_privileged_account` |

---

### R7 — `telemetry_freshness_log`

| Field | Type | Description |
|---|---|---|
| `log_id` | UUID | Log record key |
| `entity_type` | enum | `user` / `group` / `computer` / `asset` |
| `entity_id` | UUID | FK to the relevant entity table |
| `source_system` | enum | `ad_events` / `edr_agent` / `patch_mgmt` / `vuln_scanner` / `asset_inventory` |
| `expected_refresh_interval_days` | int | Normal cadence for this source |
| `actual_gap_days` | int | Observed gap since last update |
| `freshness_flag` | enum | `fresh` / `stale_mild` / `stale_heavy` / `missing` |
| `observation_timestamp` | datetime | When this freshness record was generated |
| `is_anomalous` | bool | Anomaly injection flag |
| `anomaly_class` | str | Null unless injected; e.g., `telemetry_missingness_cluster`, `missing_endpoint_agent` |

---

## Anomaly Label Table

### L1 — `anomaly_labels`

Stored separately from observation tables to enforce strict train/test discipline.

| Field | Type | Description |
|---|---|---|
| `label_id` | UUID | Label record key |
| `entity_type` | enum | Primary entity type for this anomaly |
| `entity_id` | UUID | Primary entity key |
| `anomaly_class` | enum | See taxonomy below |
| `anomaly_severity` | enum | `critical` / `high` / `medium` / `low` |
| `injected_at` | datetime | When this anomaly was injected in synthetic time |
| `observable_from` | datetime | Earliest timestamp at which the anomaly is detectable |
| `source_record_ids` | list[UUID] | FKs to the source records that constitute this anomaly |
| `benchmark_task_id` | str | Which benchmark task (T1–T7) this anomaly belongs to |
| `split` | enum | `train` / `val` / `test` |

---

## Anomaly Taxonomy v0.1

| Class ID | Class Name | Primary Entity | Source Tables | Benchmark Task | ATT&CK Enabling Condition |
|---|---|---|---|---|---|
| AH-01 | `stale_privileged_account` | User | users, account_lifecycle_events | T1 | Enables T1078.002 (Domain Accounts) |
| AH-02 | `privilege_escalation_drift` | User, Group | group_membership_events | T2, T7 | Enables T1098 (Account Manipulation) |
| AH-03 | `group_membership_drift` | Group | groups, group_membership_events | T2 | Enables T1484 (Domain Policy Modification) |
| AH-04 | `dormant_account_reactivation` | User | users, account_lifecycle_events, login_events | T6 | Enables T1078 (Valid Accounts) |
| AH-05 | `impossible_or_unusual_login` | User, Computer | login_events | T1, T6 | Enables T1078 (Valid Accounts) |
| AH-06 | `endpoint_identity_risk_correlation` | Computer, User | computers, vulnerability_records, users | T3 | Enables T1078 (access via unpatched host) |
| AH-07 | `patch_noncompliance_cluster` | Computer | endpoint_patch_state | T5 | Enables exploitation via unpatched CVE |
| AH-08 | `kev_exposure_aging` | Computer | vulnerability_records, endpoint_patch_state | T5 | CISA KEV mandate violation |
| AH-09 | `asset_inventory_mismatch` | Asset | assets | T4 | Unmanaged asset — unknown exposure surface |
| AH-10 | `missing_endpoint_agent` | Computer | computers, telemetry_freshness_log | T4 | Loss of EDR visibility |
| AH-11 | `telemetry_missingness_cluster` | Computer/OU | telemetry_freshness_log | T4 | Systematic loss of detection coverage |
| AH-12 | `abnormal_remediation_delay` | Computer | remediation_events, vulnerability_records | T5 | Prolonged exposure of open critical CVE |

**ATT&CK mapping caveat (mandatory in paper):** These mappings describe *enabling conditions*, not detection claims. Paper 3 does not claim to detect the listed ATT&CK techniques; it detects hygiene-state anomalies that *could enable* those techniques if exploited.

---

## Schema Versioning

| Version | Date | Notes |
|---|---|---|
| v0.1 | 2026-05-28 | Initial spec; Step 2 output; no implementation |
| v0.2 | TBD | Step 3 refinements after implementation begins |

---

## Schema Changelog Discipline

- Breaking changes (field renamed, type changed, table removed) require a new minor version number.
- All data generated under v0.1 must be re-generated if the schema breaks.
- Additive changes (new optional field) may be noted as a patch (v0.1.1).

---

*End of SCHEMA_v0_1.md*
