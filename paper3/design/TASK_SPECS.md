# Paper 3 — Benchmark Task Specifications

**Date:** 2026-05-28
**Status:** Locked for Step 3. No implementation yet. Specification document only.
**Companion:** `EXPERIMENTAL_DESIGN_v0_1.md`, `SCHEMA_v0_1.md`

---

## Overview

Seven benchmark tasks (T1–T7) covering the 12 anomaly classes defined in `SCHEMA_v0_1.md`. Each task specifies:
- Formal definition
- Entity scope and ground-truth unit
- Anomaly classes involved
- Injection protocol (high-level; implementation in Step 4)
- Expected class imbalance ratio at medium population
- Evaluation budget (k for P@k)
- Feature set for rule baseline
- Method applicability flags
- ATT&CK enabling-condition note

---

## T1 — Stale Privileged Account Risk

### Formal definition
Detect user accounts that are members of privileged groups (e.g., Domain Admins, Enterprise Admins, or equivalent) but have not authenticated in ≥ N days, where N is a threshold reflecting organizational inactivity policy.

### Entity scope and ground-truth unit
- **Entity type:** User.
- **Ground-truth unit:** One binary label per user (anomalous / normal) per evaluation snapshot.
- **Scope filter:** All users with `is_privileged = True`.

### Anomaly classes
- **AH-01** (`stale_privileged_account`) — primary.
- **AH-05** (`impossible_or_unusual_login`) — secondary; may co-occur with stale-account anomalies.

### Injection protocol (design-level)
1. Baseline: generate a population of privileged users with normally-distributed `days_since_last_logon` (mean = 5 days, SD = 10 days, right tail clipped at 30 days).
2. Inject anomalies: set `days_since_last_logon` > threshold (90 days) for a random subset of privileged accounts (prevalence = 2%; adjustable for imbalance sweep).
3. Also remove recent `login_events` for these users (their login history shows silence ≥ N days).
4. Freshness regime: for C-STALE and C-MISS conditions, additionally inject `source_freshness_flag = stale_heavy` on a fraction of non-anomalous accounts (creates ambiguity: is the account stale or just telemetry stale?).

### Class imbalance (medium population, 1:50 default)
- Total privileged users: ~50 (5% of 1,000-user population = 50 privileged users at default privileged rate).
- Anomalies injected: 1–2 users (≈2% of privileged pool = ~1 per seed; adjusted upward for testability to 3–5 per run).
- **Imbalance ratio: approximately 1:10 to 1:15** within the privileged-user scope (narrower than the global 1:50 because the denominator is filtered to privileged users only).

### Evaluation budget
- **k = 10** (daily SOC review of top-10 flagged privileged accounts).

### Rule baseline features (M1)
| Feature | Threshold | Score contribution |
|---|---|---|
| `days_since_last_logon` | > 90 days | +3 |
| `days_since_last_logon` | > 30 days | +1 |
| `privileged_group_count` | > 2 | +1 |
| `days_since_password_change` | > 180 days | +1 |
| `source_freshness_flag` | `fresh` | 0 (no penalty) |
| `source_freshness_flag` | `stale_heavy` | -1 (uncertainty discount) |
| `mfa_enabled` | False | +1 |

Final M1 score = weighted sum; rank descending.

### Method applicability
- M1 (Rule): ✓
- M2 (Hybrid scorer): ✓
- M3 (Isolation Forest): ✓
- M4 (LOF): ✓
- M5 (OCSVM): ✓
- M6 (Autoencoder): ✓
- M7 (Temporal z-score): ✓ (primary method: `days_since_last_logon` trend)
- M8 (Graph): ✓ (user nodes + group membership edges)

### ATT&CK enabling-condition note
Stale privileged accounts provide a persistent, low-noise credential pool for T1078.002 (Valid Accounts — Domain Accounts). Paper 3 does not claim to detect T1078.002; it detects the enabling hygiene condition.

---

## T2 — Group Membership Drift

### Formal definition
Detect anomalous additions or removals of users from security groups that deviate from the established baseline membership distribution, including cases where privilege escalation (addition to privileged groups) is the anomaly.

### Entity scope and ground-truth unit
- **Entity type:** Group membership event.
- **Ground-truth unit:** One binary label per `group_membership_events` record (anomalous / normal).
- **Scope filter:** All `group_membership_events` with `action = add` within the observation window.

### Anomaly classes
- **AH-03** (`group_membership_drift`) — primary (anomalous add to non-privileged group outside normal pattern).
- **AH-02** (`privilege_escalation_drift`) — secondary (anomalous add to privileged group).

### Injection protocol (design-level)
1. Baseline: generate normal group-membership events at a low background rate (expected rate: 0.5% of users experience a group change per week).
2. Inject two types of anomalies:
   - **Type A (drift):** Add 1–3 users to non-privileged groups outside their normal OU affiliation (cross-OU membership).
   - **Type B (escalation):** Add 1–2 users to privileged groups without a correlated role-change event (i.e., no manager-approval lifecycle event).
3. Anomaly prevalence: ~1% of all group-add events per observation window.
4. Freshness regime: in C-STALE, delay the delivery of group-change events by the staleness factor (events still occur but arrive late — tests whether detectors can handle temporally shifted signals).

### Class imbalance (medium population)
- Total group-add events per observation window: ~200–500 (varies with population and window length).
- Anomalies: ~2–5 per window.
- **Imbalance ratio: approximately 1:100.**

### Evaluation budget
- **k = 20** (weekly review of top-20 flagged group-change events).

### Rule baseline features (M1)
| Feature | Threshold | Score contribution |
|---|---|---|
| `is_privileged_group` | True | +4 |
| actor OU ≠ target OU | Cross-OU | +2 |
| `action` = add AND user has no recent role-change event | | +2 |
| `event_timestamp` = off-hours | | +1 |
| `actor_user_id` has no prior group-management history | | +1 |

### Method applicability
- M1–M6: ✓
- M7 (Temporal z-score): ✓ (track `group_change_rate_30d` per user)
- M8 (Graph): ✓ (primary method — group membership changes are graph edge additions; DOMINANT reconstructs expected structure)

---

## T3 — Endpoint–Identity Risk Correlation

### Formal definition
Detect cases where a privileged user's primary endpoint hosts one or more critical or KEV-flagged vulnerabilities that remain unpatched, combined with indicators of reduced endpoint visibility (stale agent or missing patch records). The anomaly is the *co-occurrence* of identity privilege and endpoint exposure risk.

### Entity scope and ground-truth unit
- **Entity type:** (User, Computer) pair where `users.is_privileged = True` and the computer is the user's `primary_user_id` assignment.
- **Ground-truth unit:** One binary label per (user, computer) pair.

### Anomaly classes
- **AH-06** (`endpoint_identity_risk_correlation`) — primary.
- **AH-08** (`kev_exposure_aging`) — contributing factor (open KEV ≥ 30 days).
- **AH-10** (`missing_endpoint_agent`) — contributing factor.

### Injection protocol (design-level)
1. Baseline: privileged users are assigned primary computers with normal patch compliance (~85%) and no KEV exposures.
2. Inject anomalies:
   - Assign N privileged users to computers with: `open_kev_count ≥ 1`, `patch_compliance_score < 0.5`, `days_since_agent_heartbeat > 14`.
   - N = 3–5% of privileged user count.
3. Also inject some non-privileged high-criticality asset exposure (as confounders — tests whether methods correctly prioritize privilege + exposure co-occurrence over exposure alone).
4. For C-UNSUP: agent heartbeat data is partially missing, making the correlation harder to confirm.

### Class imbalance
- Total privileged user–computer pairs: ~50.
- Anomalous pairs: ~2–3.
- **Imbalance ratio: approximately 1:20 within privileged scope.**

### Evaluation budget
- **k = 15** (weekly review of top-15 at-risk identity–endpoint pairs).

### Rule baseline features (M1)
| Feature | Threshold | Score contribution |
|---|---|---|
| `is_privileged` | True | +2 |
| `open_kev_count` | ≥ 1 | +4 |
| `patch_compliance_score` | < 0.5 | +2 |
| `days_since_agent_heartbeat` | > 14 | +2 |
| `asset_criticality` | critical | +2 |
| `days_open_max_critical` | > 30 | +1 |

### Method applicability
- M1–M6: ✓
- M7 (Temporal): ✓ (track `open_kev_count` and `days_since_agent_heartbeat` over time)
- M8 (Graph): ✓ (user → computer edge; node features include privilege + patch state)

---

## T4 — Telemetry Missingness Clusters

### Formal definition
Detect cases where one or more telemetry sources (EDR agent, patch management, vulnerability scanner, asset inventory) have stopped reporting for a computer or a group of computers (e.g., an entire OU), indicating loss of visibility rather than normal data latency.

### Entity scope and ground-truth unit
- **Entity type:** Computer (for per-asset missingness) and OU / organizational unit (for cluster missingness).
- **Ground-truth unit:** One binary label per computer.
- Cluster anomalies are flagged at the OU level; per-computer labels are derived from OU membership.

### Anomaly classes
- **AH-09** (`asset_inventory_mismatch`) — asset in one system but not another.
- **AH-10** (`missing_endpoint_agent`) — agent not installed or no heartbeat.
- **AH-11** (`telemetry_missingness_cluster`) — systematic loss across an OU.

### Injection protocol (design-level)
1. Baseline: all computers have active agents with heartbeat freshness within normal intervals (1–7 days per source).
2. Inject anomalies:
   - **Type A (single-asset):** Set `endpoint_agent_installed = False` or `days_since_agent_heartbeat > 30` for a random 5% of computers.
   - **Type B (cluster):** Select one OU (10–30 computers); set all patch-management and agent records for that OU to `source_freshness_flag = missing`.
   - **Type C (inventory mismatch):** Set `inventory_mismatch_flag = True` for 3–5% of assets (asset appears in vuln scanner but not in asset inventory).
3. For C-MISS (two sources missing): inject both agent gap and inventory gap simultaneously, creating compounding ambiguity.

### Class imbalance
- Anomalous computers: 5–10% of total (at default injection rate).
- **Imbalance ratio: approximately 1:15** (less extreme than identity tasks because missingness is more common).

### Evaluation budget
- **k = 20** (weekly review of top-20 coverage-gap assets).

### Rule baseline features (M1)
| Feature | Threshold | Score contribution |
|---|---|---|
| `endpoint_agent_installed` | False | +4 |
| `days_since_agent_heartbeat` | > 14 | +3 |
| `days_since_agent_heartbeat` | > 30 | +2 (additional) |
| `inventory_mismatch_flag` | True | +3 |
| `source_freshness_flag` (per source) | `missing` | +2 per source |
| `asset_criticality` | critical | +1 (prioritize critical gaps) |

### Method applicability
- M1–M5: ✓
- M6 (Autoencoder): ✓ (missingness pattern as a reconstruction-error signal)
- M7 (Temporal z-score): ✓ (track `actual_gap_days` from `telemetry_freshness_log`)
- M8 (Graph): ✗ (graph structure is not informative for missingness detection; excluded from T4 results)

---

## T5 — Patch and Vulnerability Hygiene Anomalies

### Formal definition
Detect computers with anomalous patch posture: patch-noncompliance clusters (unusually high missing critical patches), KEV-flagged vulnerabilities aging past a policy threshold (30 days per CISA BOD 22-01 guidance), or abnormally delayed remediation relative to peer assets.

### Entity scope and ground-truth unit
- **Entity type:** Computer.
- **Ground-truth unit:** One binary label per computer per snapshot.

### Anomaly classes
- **AH-07** (`patch_noncompliance_cluster`) — primary.
- **AH-08** (`kev_exposure_aging`) — primary.
- **AH-12** (`abnormal_remediation_delay`) — secondary.

### Injection protocol (design-level)
1. Baseline: computers have patch compliance score distributed normally (mean = 0.85, SD = 0.10). KEV-flagged CVEs are absent or promptly patched.
2. Inject anomalies:
   - **Type A (noncompliance cluster):** Select a cluster of 5–10 computers in the same OU; set `patch_compliance_score < 0.50` and `critical_missing_patch_count ≥ 3` for all.
   - **Type B (KEV aging):** Set `is_kev_flagged = True` and `days_open ≥ 30` for 2–3 CVEs on high-criticality assets.
   - **Type C (remediation delay):** Inject `remediation_events` with `remediation_latency_days > 90` for critical CVEs (expected: ≤ 30 days per policy).
3. Cluster injection: anomalies in Type A co-occur at the OU level (spatial correlation). Tests whether detectors identify cluster patterns vs. isolated outliers.

### Class imbalance
- Anomalous computers: ~8–12% of total.
- **Imbalance ratio: approximately 1:10 to 1:12** (less extreme; patch anomalies are more common operationally).

### Evaluation budget
- **k = 25** (weekly review of top-25 patch-risk assets).

### Rule baseline features (M1)
| Feature | Threshold | Score contribution |
|---|---|---|
| `open_kev_count` | ≥ 1 | +4 |
| `days_open_max_critical` | > 30 | +3 |
| `patch_compliance_score` | < 0.50 | +3 |
| `critical_missing_patch_count` | ≥ 3 | +2 |
| `remediation_delay_days_max` | > 90 | +2 |
| `asset_criticality` | critical | +1 |
| `source_freshness_flag` | `stale_heavy` | -1 (uncertainty discount) |

### Method applicability
- M1–M6: ✓
- M7 (Temporal z-score): ✓ (track `patch_compliance_score` and `open_kev_count` over time per computer)
- M8 (Graph): ✗ (patch posture is primarily a node attribute, not a structural/relational anomaly; graph structure adds limited signal; excluded from T5)

---

## T6 — Dormant Account Reactivation

### Formal definition
Detect user accounts reactivated (re-enabled) after an extended period of inactivity (≥ 180 days since last logon), followed by login events with anomalous patterns (off-hours, cross-segment, or high-velocity) in the post-reactivation window.

### Entity scope and ground-truth unit
- **Entity type:** User.
- **Ground-truth unit:** One binary label per user per reactivation event (a user may have at most one reactivation event per observation window).

### Anomaly classes
- **AH-04** (`dormant_account_reactivation`) — primary.
- **AH-05** (`impossible_or_unusual_login`) — secondary (post-reactivation abnormal login pattern).

### Injection protocol (design-level)
1. Baseline: generate a pool of disabled/dormant accounts (5–10% of user population); reactivation events occur at background rate (~0.1% per week) with normal post-reactivation login patterns.
2. Inject anomalies:
   - Set `days_since_last_logon_at_action > 180` at time of reactivation event.
   - Inject post-reactivation `login_events` with: `is_off_hours = True` AND (`is_cross_segment = True` OR `login_frequency_7d > 3× baseline`).
   - Anomaly count: 3–5 per observation window.
3. Also inject some non-anomalous reactivations (accounts dormant < 90 days, normal post-reactivation pattern) as hard negatives.

### Class imbalance
- Reactivation events per window: 10–20 (background rate + anomalies).
- Anomalous reactivations: 3–5.
- **Imbalance ratio: approximately 1:4 to 1:6 within reactivation scope** (most reactivations are potentially suspicious; rule baseline has to distinguish by post-reactivation pattern).

Note: the lower imbalance ratio on this task justifies reporting ROC-AUC in addition to AP.

### Evaluation budget
- **k = 10** (daily review of top-10 reactivation events).

### Rule baseline features (M1)
| Feature | Threshold | Score contribution |
|---|---|---|
| `days_since_last_logon_at_action` | > 180 days | +4 |
| `days_since_last_logon_at_action` | > 90 days | +2 |
| Post-reactivation `is_off_hours` | True | +2 |
| Post-reactivation `is_cross_segment` | True | +2 |
| Post-reactivation `login_frequency_7d` | > 3× baseline | +2 |
| `is_privileged` (reactivated user) | True | +2 |

### Method applicability
- M1–M6: ✓
- M7 (Temporal z-score): ✓ (primary method — post-reactivation login spike against rolling baseline)
- M8 (Graph): Partial ✓ (reactivated user reappears as a node; sudden edge creation to computers)

---

## T7 — Multi-Step Privilege Escalation Drift

### Formal definition
Detect users who have undergone a gradual, multi-step increase in privilege group membership over a 30-day observation window, where no single addition event is individually anomalous but the cumulative pattern is.

### Entity scope and ground-truth unit
- **Entity type:** User.
- **Ground-truth unit:** One binary label per user per 30-day observation window (end-of-window classification).

### Anomaly classes
- **AH-02** (`privilege_escalation_drift`) — primary.

### Injection protocol (design-level)
1. Baseline: users' `privileged_group_count` is stable within ±1 over 30 days (normal role adjustments).
2. Inject anomalies:
   - For 1–2 users per seed: inject a sequence of 3–5 group additions over 30 days, each spaced ≥ 5 days apart, each individually within the normal single-event range.
   - Cumulative delta in `privileged_group_count`: +3 to +5 over 30 days.
   - No correlated role-change event (no manager approval, no HR lifecycle event).
3. Hard negatives: inject users with 2–3 group additions that *do* have correlated role-change events (authorized escalation).
4. This is the hardest task: the anomaly is temporal and cumulative, not detectable from a single snapshot.

### Class imbalance
- Anomalous users: 1–2 per observation window (out of 1,000).
- **Imbalance ratio: approximately 1:500 to 1:1000.** Extremely severe.
- Note: This imbalance makes T7 the most challenging task. It is expected that many methods (including some ML methods) will fail to outperform the rule baseline under such extreme imbalance. This is anticipated and reported as a finding.

### Evaluation budget
- **k = 10** (weekly review of top-10 escalation patterns).

### Rule baseline features (M1)
| Feature | Threshold | Score contribution |
|---|---|---|
| `privileged_group_count delta (30d)` | ≥ 3 | +5 |
| `privileged_group_count delta (30d)` | ≥ 2 | +2 |
| No correlated role-change event in window | | +3 |
| `group_change_rate_30d` | > 2× population mean | +2 |
| All group additions to *different* privileged groups | | +2 |

### Method applicability
- M1 (Rule): ✓ (requires 30-day temporal window aggregation)
- M2 (Hybrid scorer): ✓
- M3 (Isolation Forest): ✓ (feature: 30-day delta features computed as input)
- M4 (LOF): ✓
- M5 (OCSVM): ✓
- M6 (Autoencoder): ✓ (input: 30-day feature vector)
- M7 (Temporal z-score): ✓ (primary method — `privileged_group_count` time series)
- M8 (Graph): ✓ (primary method — cumulative edge additions to privileged group nodes)

### Special considerations
- Feature engineering for non-graph methods requires **temporal window aggregation** (30-day delta features), not single-snapshot features. This is the only task where feature computation requires temporal join across `group_membership_events`.
- For the graph method (M8): the graph is constructed at end-of-window using the full 30-day event stream; edge weights reflect event count within the window.

---

## Cross-Task Summary Table

| Task | Anomaly Classes | Entity | Ground-Truth Unit | k | Imbalance Ratio | AUC Reported? | M7 Applicable? | M8 Applicable? |
|---|---|---|---|---|---|---|---|---|
| T1 (Stale privileged) | AH-01, AH-05 | User | Per-user | 10 | ~1:10–1:15 | Marginal | ✓ | ✓ |
| T2 (Group drift) | AH-02, AH-03 | Event | Per-event | 20 | ~1:100 | No | ✓ | ✓ (primary) |
| T3 (Endpoint–identity) | AH-06, AH-08, AH-10 | (User, Computer) pair | Per-pair | 15 | ~1:20 | Yes | ✓ | ✓ |
| T4 (Telemetry missingness) | AH-09, AH-10, AH-11 | Computer | Per-computer | 20 | ~1:15 | Yes | ✓ | ✗ |
| T5 (Patch/vuln hygiene) | AH-07, AH-08, AH-12 | Computer | Per-computer | 25 | ~1:10–1:12 | Yes | ✓ | ✗ |
| T6 (Dormant reactivation) | AH-04, AH-05 | User | Per-reactivation event | 10 | ~1:4–1:6 | Yes | ✓ (primary) | Partial |
| T7 (Escalation drift) | AH-02 | User | Per-user (30d window) | 10 | ~1:500–1:1000 | No | ✓ (primary) | ✓ (primary) |

---

## Hyperparameter Grids (Locked)

These grids are fixed at design time and not changed after implementation begins. Validation-split selection only.

| Method | Hyperparameter | Grid |
|---|---|---|
| M3 (Isolation Forest) | n_estimators | {100, 200} |
| M3 | contamination | {0.01, 0.02, 0.05} |
| M4 (LOF) | n_neighbors | {10, 20, 30} |
| M4 | metric | euclidean |
| M5 (OCSVM) | kernel | rbf |
| M5 | nu | {0.01, 0.05, 0.10} |
| M5 | gamma | {scale, auto} |
| M6 (Autoencoder) | latent_dim | {8, 16} |
| M6 | learning_rate | {1e-3, 1e-4} |
| M6 | epochs | 100 (fixed; early stopping on val loss) |
| M8 (Graph) | alpha (structure vs. attribute weight) | {0.3, 0.5, 0.7} |
| M8 | learning_rate | {1e-3, 1e-4} |
| M8 | epochs | 100 (fixed; early stopping) |

All other hyperparameters are at library defaults for v0.1.

---

## Future Task Candidates (Not in v0.1)

These anomaly classes from the taxonomy are deferred to future work:

- **AH-09 (asset inventory mismatch) as a standalone task:** Currently bundled into T4. May warrant its own task in a v0.2 benchmark if the T4 cluster task dilutes the signal.
- **AH-12 (abnormal remediation delay) as a standalone task:** Currently part of T5. Remediation delay could be separated into a process-mining-style temporal task.
- **Cross-asset lateral movement correlation:** Not in v0.1 taxonomy; would require inter-asset login correlation beyond the current schema. Explicitly deferred to future work.

---

*End of TASK_SPECS.md*
