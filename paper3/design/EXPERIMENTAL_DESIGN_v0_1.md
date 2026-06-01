# Paper 3 — Experimental Design v0.1

**Date:** 2026-05-28
**Status:** Locked for Step 3. No implementation yet. Specification document only.
**Companion:** `TASK_SPECS.md`, `SCHEMA_v0_1.md`, `STEP2_DATASET_FEASIBILITY.md`

---

## Purpose

Lock the experimental design before any implementation begins (Step 4). Defines: benchmark tasks, condition matrix, method suite with feature sets, metric suite, negative-result protocol, and reproducibility requirements. Nothing in this document is implemented; all choices are design decisions to be executed in Step 4.

---

## 1. Benchmark Overview

The benchmark evaluates **7 anomaly-detection tasks (T1–T7)** across **5 experimental conditions** that independently vary telemetry quality and dataset characteristics. For each task × condition cell, **8 methods** are evaluated. The evaluation produces per-task, per-condition metric tables with explicit failure-aware reporting.

```
Tasks T1–T7  ×  Conditions C-A through C-E  ×  8 Methods
= 7 × 5 × 8 = 280 primary evaluation runs
+ 3 seed replications per run = 840 total primary runs
```

Supplemental sweeps (appendix) vary population scale, full imbalance range, and full missingness range.

---

## 2. Condition Matrix

### 2.1 Primary Conditions (Paper Body)

Five primary conditions, crossing freshness and missingness regimes, at a fixed medium population scale and fixed-baseline class imbalance.

| Condition ID | Label | Population | Freshness Regime | Missingness Regime | Class Imbalance | Label Sparsity |
|---|---|---|---|---|---|---|
| **C-BASE** | Clean baseline | Medium (1,000 users) | None (all fresh) | None | Medium (1:50) | Fully labeled |
| **C-FRESH** | Fresh + one-source gap | Medium | None (all fresh) | One source missing | Medium (1:50) | Fully labeled |
| **C-STALE** | Heavy staleness, no missingness | Medium | Heavy (3–10× interval) | None | Medium (1:50) | Fully labeled |
| **C-MISS** | Heavy staleness + two-source gap | Medium | Heavy (3–10× interval) | Two sources missing | Medium (1:50) | Fully labeled |
| **C-UNSUP** | Unsupervised (no labels at train) | Medium | Mild (1–2× interval) | One source missing | Medium (1:50) | Unlabeled |

**Rationale for condition selection:**
- C-BASE establishes a clean-telemetry floor; all methods should perform best here.
- C-FRESH isolates the effect of a single source gap without staleness.
- C-STALE isolates the effect of heavy staleness without gaps.
- C-MISS represents the hardest realistic condition (stale + multi-source gap); expected to reveal the largest method separations.
- C-UNSUP tests purely unsupervised detectors without any label access; critical for realistic public-sector deployment.

### 2.2 Supplemental Conditions (Appendix)

Vary one axis at a time from C-BASE:

| Supplement | Axis Varied | Values |
|---|---|---|
| S-SCALE | Population scale | Small (200 users), Medium (1,000), Large (5,000) |
| S-IMBAL | Class imbalance | Low (1:10), Medium (1:50), High (1:200) |
| S-MISS-FULL | Missingness regime | None, one-source, two-source, systematic-OU |
| S-SPARSE | Label sparsity | Fully labeled, 50% labeled, unlabeled |

Supplemental results are reported in full in the appendix; the paper body summarizes only noteworthy patterns (e.g., where method rank order reverses across scale or imbalance).

---

## 3. Method Suite

Eight methods evaluated across all tasks and conditions. Methods are grouped into three tiers.

### Tier 1 — Rule Baselines (no training)

**M1 — Rule Baseline (task-specific thresholds)**
- Description: Threshold-based scoring function with hand-coded thresholds on the most salient hygiene signals for each task (see `TASK_SPECS.md` §3). Deterministic; no hyperparameters.
- Feature set: Task-specific core signals (e.g., T1: `days_since_last_logon`, `is_privileged`, `privileged_group_count`).
- Score: Weighted sum of threshold-exceeding indicators; ranked descending.
- Purpose: Establishes the non-ML floor. All ML methods must beat this to claim value.

**M2 — Hybrid Risk Scorer**
- Description: Deterministic weighted combination of three sub-scores: identity hygiene score + endpoint patch score + vulnerability exposure score, with a telemetry-freshness penalty multiplier.
- Feature set: Cross-domain features from `users`, `computers`, `endpoint_patch_state`, `vulnerability_records`, `telemetry_freshness_log`.
- Score: `risk_score = w_id * identity_score + w_ep * endpoint_score + w_vx * vuln_score * freshness_penalty`.
- Weights: fixed at 1/3 each for v0.1; sensitivity swept in supplemental.
- Purpose: A stronger, more principled rule baseline. No training.

### Tier 2 — Classical Unsupervised Anomaly Detectors

All Tier 2 methods use the same **tabular feature set** unless noted, normalized per-feature to [0, 1] using train-split statistics.

**Tabular feature set (shared):**

| Feature | Source table | Notes |
|---|---|---|
| `days_since_last_logon` | users | Key identity hygiene signal |
| `days_since_password_change` | users | |
| `privileged_group_count` | users | |
| `is_privileged` | users | Binary |
| `days_since_agent_heartbeat` | computers | Key endpoint signal |
| `endpoint_agent_installed` | computers | Binary |
| `patch_compliance_score` | endpoint_patch_state | |
| `critical_missing_patch_count` | endpoint_patch_state | |
| `open_kev_count` | vulnerability_records | Aggregated per computer |
| `days_open_max_critical` | vulnerability_records | Max days open for critical CVE |
| `asset_criticality_ordinal` | computers | Ordinal encoding |
| `inventory_mismatch_flag` | assets | Binary |
| `source_freshness_score` | telemetry_freshness_log | Composite across sources; 0=missing, 1=fresh |
| `login_frequency_7d` | login_events | Trailing 7-day count |
| `off_hours_login_rate` | login_events | Fraction of logins outside business hours |
| `cross_segment_login_rate` | login_events | Fraction of logins from non-primary segment |
| `group_change_rate_30d` | group_membership_events | Group change events per 30 days for user |
| `remediation_delay_days_max` | remediation_events | Max delay for open critical remediations |

**M3 — Isolation Forest**
- Library: scikit-learn `IsolationForest`.
- Hyperparameter grid (swept in val split): `n_estimators` ∈ {100, 200}, `contamination` ∈ {0.01, 0.02, 0.05}; `max_features` = 1.0.
- Feature set: full tabular set above.
- Score: negative anomaly score from `decision_function`; higher = more anomalous.

**M4 — Local Outlier Factor (LOF)**
- Library: scikit-learn `LocalOutlierFactor` (novelty=True for test-time scoring).
- Hyperparameter grid: `n_neighbors` ∈ {10, 20, 30}; `metric` = euclidean.
- Feature set: full tabular set (LOF sensitive to dimensionality; apply PCA to 10 components if feature count > 15 in a given task).
- Score: negative LOF score; higher = more anomalous.

**M5 — One-Class SVM (OCSVM)**
- Library: scikit-learn `OneClassSVM`.
- Hyperparameter grid: `kernel` = rbf; `nu` ∈ {0.01, 0.05, 0.10}; `gamma` ∈ {scale, auto}.
- Feature set: full tabular set.
- Score: decision function; higher = more anomalous.

### Tier 3 — Deep / Structural Methods

**M6 — Autoencoder**
- Architecture: Fully connected; input → 64 → 32 → 16 → 32 → 64 → output (reconstruction). Depth and width fixed for v0.1; swept in supplemental.
- Loss: Mean squared reconstruction error (MSE).
- Training: Train on normal (non-anomaly) entities only in train split (since C-BASE and C-STALE have known labels; for C-UNSUP, train on full train split without label access).
- Score: Per-entity reconstruction error on held-out test split; higher = more anomalous.
- Library: PyTorch (version locked in reproducibility manifest).
- Feature set: full tabular set.

**M7 — Temporal Z-Score / Rolling Baseline**
- Description: For each entity and each time-series feature, compute a rolling mean and standard deviation over a 30-day lookback window. Score each observation by its z-score; aggregate across features per entity.
- Applicable tasks: T1 (account inactivity trend), T6 (reactivation spike), T7 (escalation rate drift). For purely cross-sectional tasks (T4, T5), M7 falls back to a single-observation z-score against population distribution.
- Score: max z-score across features per entity; higher = more anomalous.
- Feature set: temporal features only (`days_since_last_logon`, `login_frequency_7d`, `group_change_rate_30d`, `remediation_delay_days_max`).

**M8 — Graph Anomaly Detector (DOMINANT-style)**
- Graph construction:
  - Nodes: users, computers, groups (multi-type).
  - Edges: user → group (membership), user → computer (primary assignment), computer → vulnerability (open CVE).
  - Node features: task-specific subset of tabular feature set.
- Architecture: GCN-based dual autoencoder (structure + attribute reconstruction); following Ding et al. SDM 2019.
- Score: Combined structure-reconstruction + attribute-reconstruction error per node; higher = more anomalous.
- Library: PyTorch Geometric (version locked in reproducibility manifest). Optional: PyGOD if publication is confirmed.
- Applicable tasks: T2 (group drift), T3 (endpoint–identity correlation), T7 (escalation drift). For tasks with no meaningful graph signal (T4, T5), M8 is reported as N/A and excluded from that task's result table.

---

## 4. Metric Suite

### 4.1 Primary Metrics

For every task × condition × method combination:

| Metric | Symbol | Definition | Notes |
|---|---|---|---|
| Precision at k | P@k | True positives in top-k ranked entities / k | k is task-specific; see §4.3 |
| Recall at k | R@k | True positives in top-k ranked entities / total anomalies | Paired with P@k |
| Average Precision | AP | Area under P-R curve (across all thresholds) | Primary summary metric; preferred over AUC under imbalance |
| False-Positive Burden | FPB | (k − true positives in top-k) / k | Analyst-review waste rate; directly interpretable for SOC context |

### 4.2 Conditional Metrics

| Metric | Symbol | When reported | Rationale |
|---|---|---|---|
| ROC-AUC | AUC | Only when imbalance ratio ≤ 1:20 | AUC is misleading under heavy imbalance (Davis & Goadrich, ICML 2006) |
| Rank Stability | τ | Supplemental, across 3 seeds | Kendall's τ between rank orders across seed replications |
| Time-to-Detection | TTD | Tasks T1, T4, T6, T7 | Rank position of the first injected anomaly at each time step; lower rank = better |
| Calibration | CAL | Not reported in v0.1 | Calibration is Paper 2's primary contribution; excluded from Paper 3 to maintain distinctness |

### 4.3 Task-Specific k Values

| Task | k | Rationale |
|---|---|---|
| T1 (stale privileged account) | 10 | Daily SOC review budget for privileged-account hygiene |
| T2 (group membership drift) | 20 | Weekly review of group-change events |
| T3 (endpoint–identity correlation) | 15 | Weekly review of high-risk asset–identity pairs |
| T4 (telemetry missingness) | 20 | Weekly review of coverage gaps |
| T5 (patch/vuln hygiene) | 25 | Weekly review of patch-risk assets |
| T6 (dormant reactivation) | 10 | Daily review of reactivation events |
| T7 (escalation drift) | 10 | Weekly review of multi-step escalation patterns |

k values are fixed and documented; they are *not* tuned to maximize any method's performance.

### 4.4 Metric Reporting Format

Each task × condition × method cell in the results table reports: `AP ± σ (3 seeds) | P@k | R@k | FPB`. AUC added where applicable. Failure flag (⚑) appended if the negative-result protocol declares the method does not outperform the rule baseline.

---

## 5. Negative-Result Protocol

### 5.1 Declaration Criteria

For a given task × condition pair, a method M is declared **"does not outperform rule baseline"** if **both** of the following hold:

1. **AP criterion:** `AP(M) − AP(M1) < δ_AP` where `δ_AP = 0.05` across all three seed replications.
2. **P@k criterion:** `P@k(M) − P@k(M1) < δ_pk` where `δ_pk = 0.05` in at least two of three seed replications.

Note: thresholds δ_AP = 0.05 and δ_pk = 0.05 represent a *minimum meaningful improvement* for SOC operational decision-making, not a statistical significance test. Reporting against fixed thresholds is more interpretable than p-values in a single-lab benchmark setting with small seed counts.

### 5.2 Reporting Rules

- Results that fail both criteria are reported with a failure flag (⚑) in the results table.
- They are **not omitted** from the paper.
- The discussion section explicitly addresses *which tasks and conditions* show ML adding value vs. not.
- Where the rule baseline (M1) already achieves P@k ≥ 0.90 on a task, that task is marked "rules sufficient" and ML failure flags are contextualized accordingly.

### 5.3 Interpretation Framing (Mandatory in Paper)

The paper will include a dedicated subsection: "When ML Adds Value and When It Does Not." This subsection:
- Lists tasks/conditions where at least one ML method outperforms the rule baseline by ≥ δ.
- Lists tasks/conditions where no ML method does.
- Interprets the pattern in terms of signal richness, class imbalance, and telemetry quality.
- Explicitly avoids concluding "ML is better than rules in general" or "rules are sufficient in general."

---

## 6. Reproducibility Requirements

### 6.1 Seed Strategy

- Three fixed global seeds: **42, 137, 2024**.
- Each seed governs: (a) synthetic data generation, (b) train/val/test split, (c) ML model weight initialization.
- Generator seed and split seed are always identical to the global seed for a given run (no separate seeding).
- All results are reported as mean ± standard deviation across the three seeds.

### 6.2 Split Strategy

- **Train / Validation / Test split: 60% / 20% / 20%** by entity count, stratified by anomaly class.
- Stratification ensures all anomaly classes appear in all three splits at approximately the expected prevalence.
- No entity appears in more than one split.
- Split indices are stored in the run manifest.

### 6.3 Hyperparameter Selection

- All hyperparameters are selected on the **validation split** only.
- Final evaluation uses the **test split** only, with the best hyperparameters from validation.
- Hyperparameter grids are fixed in `TASK_SPECS.md` §4 and not changed post-hoc.

### 6.4 Run Manifest (per run)

Each run produces a JSON manifest file:

```json
{
  "run_id": "uuid",
  "timestamp": "ISO-8601",
  "task_id": "T1",
  "condition_id": "C-BASE",
  "method_id": "M3",
  "seed": 42,
  "generator_version": "v0.1",
  "schema_version": "v0.1",
  "dataset_id": "...",
  "hyperparameters": {"n_estimators": 200, "contamination": 0.02},
  "split": {"train": 600, "val": 200, "test": 200},
  "metrics": {
    "AP": 0.72,
    "AP_baseline": 0.65,
    "P_at_k": 0.60,
    "R_at_k": 0.30,
    "FPB": 0.40,
    "AUC": null,
    "failure_flag": false
  },
  "library_versions": {
    "scikit-learn": "1.x.x",
    "torch": "2.x.x",
    "torch-geometric": "2.x.x",
    "numpy": "1.x.x",
    "pandas": "2.x.x"
  }
}
```

### 6.5 Dataset Card

One dataset card per generated freeze (see `SCHEMA_v0_1.md` §Dataset Card Specification). Cards are generated automatically at freeze time and stored alongside the dataset.

### 6.6 Model Card (for trained methods M5, M6, M8)

One model card per (method, task, condition, seed) triple:
- Method name and version.
- Training duration (wall-clock seconds).
- Best hyperparameters from validation.
- Library versions.
- Anomaly score distribution statistics (mean, std, 95th percentile) on train split.

### 6.7 Release Artifacts (planned for Step 4/5)

| Artifact | Description |
|---|---|
| `hygienebench/` package | Synthetic generator + benchmark harness + evaluation runner |
| `datasets/` | Frozen dataset cards + split manifests (data generated on demand by seed) |
| `results/` | All 840 run manifests (primary) + supplemental |
| `model_cards/` | Model cards for trained methods |
| `figures/` | All paper figures, generated deterministically from run manifests |
| `paper/` | LaTeX source |
| `Makefile` | `make reproduce` reruns all experiments from scratch |

---

## 7. Scope Constraints (Non-Negotiable)

The following constraints carry forward from Step 1 and Step 2 and are re-confirmed here for the implementation step:

- **No code yet.** Step 3 is design-only.
- **No employer data.** All telemetry is synthetic.
- **No calibration as a primary result.** Calibration is Paper 2's contribution.
- **No attack-detection claims.** Paper 3 detects hygiene-state anomalies.
- **No product-comparison claims.** Paper 3 does not compete with Sentinel, Defender, or UBA products.
- **No ATT&CK technique detection claims.** Anomaly classes map to ATT&CK *enabling conditions* only.
- **No generalization claims beyond the synthetic evaluation.** Real-data validation is explicitly stated as future work.

---

*End of EXPERIMENTAL_DESIGN_v0_1.md*
