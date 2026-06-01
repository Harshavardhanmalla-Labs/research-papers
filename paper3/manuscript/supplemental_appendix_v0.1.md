# HygieneBench — Supplemental Appendix

**Draft v0.1 — 2026-05-28**

Companion to: "HygieneBench: A Reproducible Synthetic Benchmark for Cyber-Hygiene Anomaly Detection Across Identity, Endpoint, and Patch Telemetry"

---

## A. Method Hyperparameter Grids

All hyperparameters below are fixed (not tuned on validation split). Grid values were pre-registered in `paper3/design/EXPERIMENTAL_DESIGN_v0_1.md` before any results were examined.

**M1 — Rule Baseline**

Task-specific weighted threshold rules. No trainable parameters. Feature thresholds specified per task in `paper3/design/TASK_SPECS.md`. Score = weighted sum of threshold indicator functions.

**M2 — Hybrid Risk Scorer**

Fixed weights: identity score (30%), endpoint score (30%), vulnerability score (30%), freshness penalty (10%). No trainable parameters.

**M3 — Isolation Forest**

| Parameter | Value | Rationale |
|---|---|---|
| n_estimators | 200 | Sufficient for stable ensemble on n≤1000 |
| contamination | 0.02 | Prior on anomaly rate (≈2% in medium dataset) |
| max_features | 1.0 | All features |
| random_state | seed (per run) | Deterministic |
| Preprocessing | MinMaxScaler | Required for feature scale invariance |

**M4 — Local Outlier Factor**

| Parameter | Value | Rationale |
|---|---|---|
| n_neighbors | min(20, n_train−1) | Standard LOF; clipped to avoid errors on small splits |
| novelty | True | Required for test-time scoring |
| metric | euclidean | Default |
| Preprocessing | MinMaxScaler | Required |

**M5 — One-Class SVM**

| Parameter | Value | Rationale |
|---|---|---|
| nu | 0.05 | Upper bound on anomaly fraction; conservative |
| kernel | rbf | Default for tabular data |
| gamma | scale | Auto-scaled to feature variance |
| Preprocessing | MinMaxScaler | Required for RBF kernel |

**M6 — Linear Autoencoder (PCA-based)**

| Parameter | Value | Rationale |
|---|---|---|
| latent_dim | 8 | Consistent with neural AE design in EXPERIMENTAL_DESIGN_v0_1.md |
| Reconstruction error | Euclidean distance in feature space | Anomaly score |
| Preprocessing | MinMaxScaler | Required |
| Note | Implemented as PCA; equivalent to linear AE with MSE loss | PyTorch not available |

**M7 — Temporal Z-score**

Task-specific temporal features (see Table A.1). Anomaly score = max absolute z-score over task features. Population statistics computed on training split.

**Table A.1: M7 temporal features by task**

| Task | Features used for z-score |
|---|---|
| T1 | days_since_last_logon, privileged_group_count |
| T2 | group_change_count_30d, priv_group_change_count_30d |
| T3 | days_since_agent_heartbeat, patch_compliance_score |
| T4 | days_since_agent_heartbeat, inventory_mismatch_flag |
| T5 | patch_compliance_score, critical_missing, max_kev_days_open |
| T6 | dormant_days_at_react, off_hours_rate |
| T7 | priv_adds, priv_add_rate |

**M8 — Graph-augmented Isolation Forest**

| Parameter | Value | Rationale |
|---|---|---|
| Graph | Bipartite user–group graph (networkx) | AD group membership edges |
| Node features | degree, privileged_degree, clustering_coefficient | Standard graph anomaly features |
| Isolation Forest | Same as M3 (n_estimators=200, contamination=0.02) | Consistent with M3 |
| Feature set | Concatenation of graph features + task tabular features | |
| Excluded tasks | T4, T5 | No meaningful graph signal; N/A per design |

---

## B. Full Per-Condition Results Tables

All values are mean across 3 seeds (42, 137, 2024). AP = Average Precision (interpolated). P@k = Precision@k at task-specific k. FPB = False Positive Burden = 1−P@k. ⚑ = failure-flagged (negative result).

All values are mean AP across 3 seeds (42, 137, 2024) for the given condition.
† M8 excluded from T4, T5 by design (N/A).

### B.1 Condition: C-BASE

| Method | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|
| M1 Rule | 1.000 | 0.766 | 1.000 | 0.998 | 0.458 | 1.000 | 1.000 |
| M2 Hybrid | 1.000 | 0.661 | 0.852 | 0.779 | 0.452 | 0.587 | 0.336 |
| M3 IForest | 0.886 | 0.644 | 1.000 | 0.782 | 0.644 | 0.368 | 0.694 |
| M4 LOF | 0.665 | 0.890 | 0.301 | 1.000 | 0.584 | 1.000 | 0.750 |
| M5 OCSVM | 1.000 | 0.913 | 1.000 | 1.000 | 0.668 | 1.000 | 0.622 |
| M6 Linear-AE | 0.740 | 0.755 | 1.000 | 1.000 | 0.274 | 1.000 | 0.944 |
| M7 Z-score | 1.000 | 0.951 | 0.100 | 0.807 | 0.243 | 1.000 | 1.000 |
| M8 Graph-IF† | 0.886 | 0.644 | 1.000 | N/A | N/A | 0.368 | 0.694 |

### B.2 Condition: C-STALE

| Method | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|
| M1 Rule | 1.000 | 0.766 | 1.000 | 0.998 | 0.458 | 1.000 | 1.000 |
| M2 Hybrid | 1.000 | 0.661 | 0.614 | 0.779 | 0.452 | 0.554 | 0.336 |
| M3 IForest | 0.760 | 0.644 | 1.000 | 0.780 | 0.644 | 0.258 | 0.778 |
| M4 LOF | 0.686 | 0.890 | 0.144 | 1.000 | 0.584 | 1.000 | 0.400 |
| M5 OCSVM | 1.000 | 0.913 | 1.000 | 1.000 | 0.668 | 1.000 | 1.000 |
| M6 Linear-AE | 0.647 | 0.755 | 0.050 | 1.000 | 0.274 | 1.000 | 1.000 |
| M7 Z-score | 1.000 | 0.951 | 0.100 | 0.807 | 0.243 | 1.000 | 1.000 |
| M8 Graph-IF† | 0.760 | 0.644 | 1.000 | N/A | N/A | 0.258 | 0.778 |

*T3 AP degrades sharply under staleness for M4 (0.144), M6 (0.050), M7 (0.100). M1 Rule and M5 are most staleness-robust on T3.*

### B.3 Condition: C-FRESH

| Method | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|
| M1 Rule | 1.000 | 0.855 | 1.000 | 0.948 | 0.726 | 1.000 | 1.000 |
| M2 Hybrid | 1.000 | 0.735 | 1.000 | 0.759 | 0.651 | 0.799 | 0.308 |
| M3 IForest | 1.000 | 0.796 | 1.000 | 0.725 | 0.773 | 0.595 | 0.917 |
| M4 LOF | 1.000 | 0.975 | 0.240 | 0.983 | 0.828 | 1.000 | 1.000 |
| M5 OCSVM | 1.000 | 0.967 | 0.880 | 1.000 | 0.837 | 0.869 | 0.778 |
| M6 Linear-AE | 0.983 | 0.886 | 1.000 | 0.967 | 0.671 | 1.000 | 0.844 |
| M7 Z-score | 1.000 | 0.966 | 0.370 | 0.797 | 0.500 | 1.000 | 1.000 |
| M8 Graph-IF† | 1.000 | 0.796 | 1.000 | N/A | N/A | 0.595 | 0.917 |

### B.4 Condition: C-MISS

| Method | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|
| M1 Rule | 1.000 | 0.855 | 1.000 | 0.955 | 0.726 | 1.000 | 1.000 |
| M2 Hybrid | 1.000 | 0.735 | 1.000 | 0.758 | 0.651 | 0.812 | 0.308 |
| M3 IForest | 0.967 | 0.796 | 1.000 | 0.701 | 0.773 | 0.568 | 1.000 |
| M4 LOF | 1.000 | 0.975 | 0.290 | 0.985 | 0.828 | 1.000 | 1.000 |
| M5 OCSVM | 1.000 | 0.967 | 0.880 | 0.992 | 0.837 | 1.000 | 0.750 |
| M6 Linear-AE | 0.754 | 0.886 | 0.395 | 0.928 | 0.671 | 1.000 | 0.944 |
| M7 Z-score | 1.000 | 0.966 | 0.370 | 0.784 | 0.500 | 1.000 | 1.000 |
| M8 Graph-IF† | 0.967 | 0.796 | 1.000 | N/A | N/A | 0.568 | 1.000 |

### B.5 Condition: C-UNSUP

| Method | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|
| M1 Rule | 1.000 | 0.855 | 1.000 | 0.958 | 0.726 | 1.000 | 1.000 |
| M2 Hybrid | 1.000 | 0.735 | 1.000 | 0.758 | 0.651 | 0.799 | 0.308 |
| M3 IForest | 0.983 | 0.796 | 1.000 | 0.703 | 0.773 | 0.661 | 0.917 |
| M4 LOF | 1.000 | 0.975 | 0.219 | 0.987 | 0.828 | 1.000 | 1.000 |
| M5 OCSVM | 1.000 | 0.967 | 0.880 | 0.992 | 0.837 | 0.963 | 0.778 |
| M6 Linear-AE | 0.811 | 0.886 | 0.394 | 0.942 | 0.671 | 1.000 | 0.844 |
| M7 Z-score | 1.000 | 0.966 | 0.370 | 0.803 | 0.500 | 1.000 | 1.000 |
| M8 Graph-IF† | 0.983 | 0.796 | 1.000 | N/A | N/A | 0.661 | 0.917 |

*C-UNSUP uses C-FRESH datasets with labels withheld from training. Results closely track C-FRESH because the methods are fully unsupervised (no labels used during fitting).*

---

## C. Failure-Flag Detail by Method × Task × Condition

Failure flag = True if AP(method)−AP(rule) < 0.05 AND P@k(method)−P@k(rule) < 0.05 in ≥2/3 seeds (2 of 3 seeds).

| Method | T1 | T2 | T3 | T4 | T5 | T6 | T7 | Total flagged |
|---|---|---|---|---|---|---|---|---|
| M2 Hybrid (5 cond) | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 35/35 |
| M3 IForest (5 cond) | 5/5 | 5/5 | 5/5 | 5/5 | 3/5 | 5/5 | 5/5 | 33/35 |
| M4 LOF (5 cond) | 5/5 | 0/5 | 5/5 | 5/5 | 3/5 | 5/5 | 5/5 | 28/35 |
| M5 OCSVM (5 cond) | 5/5 | 0/5 | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 | 25/35 |
| M6 Linear-AE (5 cond) | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 35/35 |
| M7 Z-score (5 cond) | 5/5 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 30/35 |
| M8 Graph-IF (5 cond, 5 tasks) | 5/5 | 5/5 | 5/5 | N/A | N/A | 5/5 | 5/5 | 25/25 |

*Each "condition" entry represents one (method, task, condition_id) triple, reported as flagged/total_conditions.*

Key patterns:
- T2 consistently NOT flagged for M4, M5, M7 (these methods genuinely beat the rule on group-membership drift)
- T5 NOT flagged for M5 and partially M3, M4 (patch/vulnerability hygiene benefits from ML)
- M6 and M2 are flagged on all tasks under all conditions — their fixed-parameter designs do not adapt to task heterogeneity

---

## D. Dataset Schema Reference

### D.1 Table Descriptions

**`users`** — One row per AD user account.
Key columns: `user_id`, `username`, `department`, `ou_path`, `account_enabled`, `account_last_logon`, `days_since_last_logon`, `is_privileged`, `privileged_group_count`, `is_service_account`, `source_freshness_flag`.

**`groups`** — One row per AD group.
Key columns: `group_id`, `group_name`, `group_type`, `is_privileged`, `member_count`.

**`computers`** — One row per managed endpoint.
Key columns: `computer_id`, `hostname`, `os_type`, `network_segment`, `asset_criticality`, `endpoint_agent_installed`, `days_since_agent_heartbeat`.

**`assets`** — One row per asset inventory entry (correlated with computers).
Key columns: `asset_id`, `asset_type`, `asset_criticality`, `in_inventory`, `in_endpoint_mgmt`, `inventory_mismatch_flag`.

**`login_events`** — One row per authentication event (30-day window).
Key columns: `event_id`, `user_id`, `computer_id`, `event_timestamp`, `logon_type`, `success`, `is_off_hours`, `is_cross_segment`, `is_anomalous`, `anomaly_class`.

**`group_membership_events`** — One row per group add/remove event.
Key columns: `event_id`, `user_id`, `group_id`, `action`, `event_timestamp`, `actor_user_id`, `is_privileged_group`, `is_anomalous`, `anomaly_class`.

**`endpoint_patch_state`** — One row per endpoint, snapshot of patch posture.
Key columns: `record_id`, `computer_id`, `patch_compliance_score`, `critical_missing_patch_count`, `open_kev_count`.

**`vulnerability_records`** — One row per (endpoint, CVE) exposure record.
Key columns: `record_id`, `computer_id`, `cve_id`, `cvss_score`, `cvss_severity`, `is_kev_flagged`, `days_open`, `remediation_status`.

**`remediation_events`** — One row per remediation action.
Key columns: `event_id`, `computer_id`, `cve_id`, `action_type`, `action_timestamp`, `remediation_latency_days`.

**`account_lifecycle_events`** — One row per account create/enable/disable event.
Key columns: `event_id`, `user_id`, `action`, `event_timestamp`, `actor_user_id`.

**`telemetry_freshness_log`** — One row per (entity, data source) freshness record.
Key columns: `log_id`, `entity_type`, `entity_id`, `source_system`, `expected_refresh_interval_days`, `actual_gap_days`, `freshness_flag`.

**`anomaly_labels`** — Ground-truth annotations. One row per injected anomaly.
Key columns: `label_id`, `entity_type`, `entity_id`, `anomaly_class`, `anomaly_severity`, `injected_at`, `benchmark_task_id`, `split`.

### D.2 Structural Priors

| Domain | Prior | Source | Status |
|---|---|---|---|
| Patch lag (critical) | 43-day mean | Verizon DBIR 2026 | [CONFIRMED] |
| CVE severity distribution | NVD base score bins | NIST NVD | [CONFIRMED] |
| KEV proportion | ~5% of NVD CVEs | CISA KEV catalog | [CONFIRMED] |
| Telemetry cadence | 14-day asset, 72-hour patch | CISA BOD 23-01 | [CONFIRMED-DOC] |
| AD group size distribution | Power-law approximation | [PRIOR-UNAVAILABLE] | Disclosed assumption |
| EDR agent missingness rate | 10-15% assumption | [PRIOR-UNAVAILABLE] | Disclosed assumption |

---

## E. Reproducibility Checklist

| Item | Status |
|---|---|
| Generator seeded with `numpy.random.default_rng(seed)` | ✓ |
| Injector uses `seed + 999` offset | ✓ |
| Dataset cards generated with generation timestamp | ✓ |
| Split assignments in `anomaly_labels.split` column | ✓ |
| All results indexed by (condition_id, task_id, method_id, seed) | ✓ |
| Run manifest in `results/primary_full_v1/run_manifest.json` | ✓ |
| Hyperparameters fixed pre-hoc (not tuned on val) | ✓ |
| k values fixed pre-hoc per TASK_SPECS.md | ✓ |
| Failure protocol pre-registered in PAPER3_DECISION_LOG.md | ✓ |
| No employer or production data at any stage | ✓ |
| All figures reproducible from `primary_results.csv` | ✓ |

---

## F. Citation Verification Status

All citations verified as of 2026-05-28. References renumbered: [11] Noonan et al. removed; old [12] Sculley et al. is now [11].

| Ref | Description | Status |
|---|---|---|
| [1] CISA BOD 23-01 | October 2022 directive | [CONFIRMED] — cisa.gov |
| [2] NIST SP 800-40 Rev. 4 | April 2022 | [CONFIRMED] — csrc.nist.gov |
| [3] Kent 2015 LANL | Los Alamos dataset | [CONFIRMED] — doi.org/10.2172/1259877 |
| [4] Glasser & Lindauer 2013 | CERT insider threat | [CONFIRMED] — IEEE SPW 2013 |
| [5] Sharafaldin et al. 2018 | CICIDS2017 | [CONFIRMED] — ICISSP 2018 |
| [6] Rodriguez 2019 Mordor | GitHub: OTRF/Security-Datasets | [CONFIRMED] — active repo |
| [7] DARPA I2O 2018 | TC-E3 data release | [CONFIRMED] — github.com/darpa-i2o/Transparent-Computing; updated from placeholder "DARPA GARD Program" to confirmed GitHub URL |
| [8] Ding et al. 2019 SDM | DOMINANT: deep graph anomaly detection | [CONFIRMED] — SIAM SDM 2019; replaced unverified Ma et al. VLDB 2021 (no such paper found) |
| [9] Liu et al. 2024 JMLR | PyGOD JMLR 25(141) | [CONFIRMED] — jmlr.org/papers/v25/23-0963.html; author list corrected to Kay Liu, Yingtong Dou, Xueying Ding, Xiyang Hu, et al. |
| [10] Creech & Hu 2013 | KDD replacement dataset | [CONFIRMED] — IEEE WCNC 2013 |
| [11] Sculley et al. 2018 | Winner's curse / empirical rigor | [CONFIRMED] — ICLR Workshop on Reproducibility in ML 2018; renumbered from [12] |
| ~~[11] Noonan et al. 2020~~ | ~~Synthetic insider threat datasets~~ | [REMOVED] — not found in AISec 2020 proceedings (11 papers, none by Noonan); in-text citation removed from §2 |

No outstanding verification items. All references are confirmed or removed.
