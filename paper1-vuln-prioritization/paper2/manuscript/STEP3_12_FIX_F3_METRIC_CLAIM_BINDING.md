<!--
Paper 2 — Step 3.12: Fix F3 — Pre-register Metric → Claim Binding.
Locks the metric used to support every Paper-2 claim class, marks sparse-positive
metrics as diagnostic-only, and lists forbidden claims. No new metrics introduced;
no code written; no experiments run; Paper 1 frozen outputs untouched.
-->

# Paper 2 — Step 3.12: Fix F3 — Metric → Claim Binding (Pre-registered)

**F3 status: COMPLETE.**
**Step 4 still NOT allowed** (F4–F9 owed; F1-mandated framing changes still owed).

Every Paper-2 claim that may appear in the eventual manuscript must be bound here
to a single primary metric (or marked diagnostic-only) before any Paper-2
measurement is observed. Any claim not appearing in this table is not allowed.
No metric may serve two contradictory claims. The calibration-feasibility claim
remains on **unique positive distinct CVEs** (NOT pair count). No new metrics
are introduced (only the metrics inventoried in §1).

---

## 1. Metric inventory (verified, no new metrics)

### 1.1 Implemented in `src/paper1/evaluation/` (read this turn; not modified)
| Metric | Source | Notes |
|---|---|---|
| `compute_ehd` / `compute_pair_ehd` | `eehda.py:58` / `:29` | Exposure-Host-Day harm; **the primary operational metric for Paper 2** |
| `eehda_absolute(strategy_ehd)` | `eehda.py:85` | EEHDA point estimate |
| `eehda_relative(strategy_ehd, baseline_ehd)` | `eehda.py:89` | EHD ratio vs a baseline (we use `epss_only` per Step 3.9 §7) |
| `fraction_of_oracle(strategy_ehd, random_ehd, oracle_ehd)` | `eehda.py:95` | Position between random (0) and oracle (1) |
| `eehda_report(...)` | `eehda.py:102` | Bundled report |
| `precision_at_k`, `recall_at_k`, `ndcg_at_k`, `ranking_curve_at_ks` | `ranking_metrics.py` | **Diagnostic-only** under Step 3.8 sparsity |
| `rank_churn(prev, curr)` | `ranking_metrics.py:100` | Kendall-/spearman-style rank stability — primary for robustness deltas |
| `kev_deadline_breach_rate` | `compliance_metrics.py:33` | **Diagnostic-only** under Step 3.8 sparsity |
| `kev_remediation_latency` | `compliance_metrics.py:60` | Diagnostic-only (sparse) |
| `capacity_efficiency` | `compliance_metrics.py:108` | Secondary for operational-feasibility claim |
| `scheduler_feasibility_rate` | `scheduler_metrics.py:73` | Primary for operational-feasibility claim |
| `risk_acceptance_rate` | `scheduler_metrics.py:86` | Diagnostic-only (operational, not label-driven) |
| `scheduled_count` / `deferred_count` / `escalation_count` | `scheduler_metrics.py:35-43` | Sanity / diagnostic |
| `poam_review_trigger_compliance` | `scheduler_metrics.py:100` | Diagnostic; not used as a primary claim metric |
| `hash_chain_validity(audit_log_path)` | `audit_metrics.py:79` | Primary for audit/reproducibility |
| `audit_record_count_by_type` | `audit_metrics.py:85` | Sanity / sentinel for reproducibility |
| `audit_explanation_completeness` | `audit_metrics.py:43` | Sanity |
| `imputation_rate_per_feature` | `audit_metrics.py:62` | **Diagnostic-only** (operational sentinel) |
| `wilcoxon_signed_rank`, `holm_bonferroni`, `bootstrap_ci`, `bootstrap_ci_bca`, `paired_bootstrap_ci`, `paired_cohens_d`, `compare_to_baseline`, `compare_many_to_baseline`, `minimum_detectable_effect` | `statistical_tests.py` | Statistical infrastructure (F4 will pre-register usage); not metrics themselves |
| `aggregate_metrics`, `validate_metric_frame`, `validate_per_seed_metric_frame` | `metrics.py`, `statistical_tests.py:408` | Validation infrastructure |

### 1.2 Calibration-feasibility metrics (probe artefacts, NOT evaluation module)
Source of truth: `paper2/feasibility/probe_v2_multit0/` (Step 3.8 outputs;
content-addressed). These metrics are *measured by the probe*, not by
`paper1.evaluation`:
| Metric | Source artefact | Step-3.8 measured value |
|---|---|---|
| **unique positive distinct CVEs** (the gate) | `aggregate_counts.csv` / `decision_gate.json` | **7** |
| event-window positives across t0s | `aggregate_counts.csv` | 7 |
| catalog-matched CVEs | `aggregate_counts.csv` | 2,688 |
| union distinct CVEs in pairs | `aggregate_counts.csv` | 2,688 |
| EPSS coverage per t0 | `epss_coverage.csv` | 17/18 ≥99.3%; 1 missing graceful |
| KEV-as-of-t0 count | `per_t0_counts.csv` | 987 → 1,253 |
| non-degenerate calibration status | `calibration_status.json` | not attempted (7 < 50) |
| train/test class presence | `calibration_status.json` | n/a (not attempted) |
| **leakage warning count** | probe summary / run log | **0** |
| NVD acquisition status | `nvd_acquisition_status.json` | complete, 11/11 chunks |

### 1.3 Freeze / reproducibility sentinel
- `make verify-primary-freeze PYTHON=.venv/bin/python` → content-addressed verification of Paper 1's `results/primary_full_v1/` (binary OK/FAIL).

**No new metrics are introduced in F3.** The bindings below use only the
metrics enumerated in §1.1 and §1.2.

---

## 2. Allowed claim classes (verbatim from the task brief; locked here)

| Class | Question |
|---|---|
| **A** Calibration feasibility | Is public-feed calibration statistically justified under the measured label density? |
| **B** Operational prioritization | Do fixed-prior strategies change downstream exposure host-days compared with EPSS/random/oracle baselines? |
| **C** Robustness / sensitivity | Are conclusions stable across weight priors, capacity ratios, blackout policies, and feature ablations? |
| **D** Ranking quality (**diagnostic-only**) | Do rankings concentrate sparse future positives near the top? |
| **E** Operational feasibility | Does the scheduler produce feasible schedules under each scenario? |
| **F** Audit / reproducibility | Are outputs reproducible and audit-verifiable? |
| **G** KEV deadline (**diagnostic-only**) | Does the strategy reduce KEV deadline breach risk? |

---

## 3. Metric → Claim binding table (pre-registered, immutable until a written fix supersedes)

Each claim has a unique ID `CLM-<class><n>`, a status, the *exactly-one* primary
metric (or *diagnostic-only* flag), allowed secondary metrics (if any), the
required axis, allowed and forbidden interpretations, the minimum data
condition that must hold before the claim is even evaluable, and the stop rule.

### Class A — Calibration feasibility (PRIMARY contribution per Step 3.10)

#### CLM-A1 — Headline calibration-infeasibility claim
| Field | Value |
|---|---|
| Claim text | *"Per-feature context-aware weight calibration on public-feed labels is not statistically justified under the measured label density (Step 3.8: 7 unique positive distinct CVEs across 18 monthly t0 windows on a 31-product catalog over the EPSS v3 era; <20 PIVOT threshold)."* |
| Status | **primary** |
| Primary metric | **unique positive distinct CVEs** (`aggregate_counts.csv`) |
| Secondary metrics | event-window positives; EPSS coverage; **leakage warning count** (must be 0); train/test class presence (n/a if not attempted); non-degenerate calibration status (must be `not attempted` or `degenerate`) |
| Required axis | n/a — this is a *measurement*, not a sweep |
| Allowed interpretation | "Calibration was not attempted because the pre-registered gate (unique positives ≥ 50, non-degenerate weights) was not met." |
| Forbidden interpretation | Any claim that pair count, positive-pair count, or `event_positive_cves_across_windows` constitutes the calibration sample size; any claim that 7 positives is *almost enough*; any claim that calibration *could* succeed at this label density |
| Minimum data condition | Step-3.8 full keyed multi-t0 probe completed (11/11 NVD chunks; 18 t0 windows; leakage warnings == 0) — **already satisfied** |
| Stop rule | If unique positives < 20, the calibration paper remains pivoted; **no calibration experiments are launched in Step 4.** |

#### CLM-A2 — Class-balance degeneracy sub-claim
| Field | Value |
|---|---|
| Claim text | *"At the measured positive count (7) and 2,681 negatives, train/test grouped splits cannot supply both classes per fold for any reasonable scheme; class imbalance ≈ 1:380."* |
| Status | secondary (supports CLM-A1) |
| Primary metric | train/test class presence (from `calibration_status.json`) |
| Secondary metrics | unique positive distinct CVEs; CVE-level dedup row count |
| Required axis | n/a |
| Allowed interpretation | "Class imbalance makes per-feature weight learning structurally unstable." |
| Forbidden interpretation | Any attempt to fix imbalance with class-weighting / SMOTE / threshold tuning and report "calibration now works." |
| Minimum data condition | calibration_status.json present (already so) |
| Stop rule | Same as CLM-A1 |

### Class B — Operational prioritization (CONFIRMATORY per Step 3.10)

#### CLM-B1 — Δ-EHD vs EPSS-only baseline, per axis cell
| Field | Value |
|---|---|
| Claim text | *"Fixed-prior strategy S at cell (capacity, blackout, approver, EPSS era, catalog strictness) C produces ΔEHD = EHD(S, C) − EHD(epss_only, C) with paired-seed BCa CI [L, U]."* |
| Status | primary (descriptive, not superiority) |
| Primary metric | **EHD** (`compute_ehd`) — point estimate per (S, C, seed); paired-seed delta vs `epss_only` |
| Secondary metrics | `eehda_relative(strategy_ehd, epss_ehd)`; `fraction_of_oracle(strategy, random, oracle)` |
| Required axis | A2 strategy × A3 weight-vector-family × A1 capacity (cell); other axes held at central level |
| Allowed interpretation | "ΔEHD is/is not distinguishable from 0 within paired-seed BCa CI" — descriptive |
| Forbidden interpretation | "Strategy S beats EPSS" / "is superior" / "outperforms" (CLM-B1 is descriptive Δ + CI, not superiority — see §6) |
| Minimum data condition | All cells have ≥ minimum-seeds count (set in F4); per-seed metric frame validates (`validate_per_seed_metric_frame`); freeze before and after each run is OK |
| Stop rule | If 95 % BCa CI for ΔEHD overlaps 0 in every cell, **report that as the finding** (kill rule W1 from F2 mirrors this). No re-tuning. |

#### CLM-B2 — Relative-to-EPSS magnitude
| Field | Value |
|---|---|
| Claim text | *"Strategy S at cell C produces `relative_to_epss = EHD(S)/EHD(epss_only) = r` with bootstrap CI [L,U]."* |
| Status | secondary (supports CLM-B1) |
| Primary metric | `eehda_relative` |
| Secondary metrics | `fraction_of_oracle` |
| Required axis | same as CLM-B1 |
| Allowed interpretation | Reporting r and CI, descriptive |
| Forbidden interpretation | Same as CLM-B1 (no superiority language) |
| Minimum data condition | same as CLM-B1 |
| Stop rule | same as CLM-B1 |

#### CLM-B3 — Position between random and oracle
| Field | Value |
|---|---|
| Claim text | *"Strategy S sits at `fraction_of_oracle = f` between random (0) and oracle (1), with CI."* |
| Status | secondary |
| Primary metric | `fraction_of_oracle` |
| Secondary metrics | EHD itself |
| Required axis | same as CLM-B1 |
| Allowed interpretation | Descriptive position |
| Forbidden interpretation | Any claim that oracle is "achievable" (oracle is a label-built upper bound with only 7 positives — diagnostic upper bound, not target) |
| Minimum data condition | random and oracle cells run in same seed sweep |
| Stop rule | If oracle ≈ random within CI (because positives are too sparse to separate them), explicitly report "oracle ill-defined under measured sparsity" and do NOT use CLM-B3 as a headline. |

### Class C — Robustness / sensitivity (CONFIRMATORY per Step 3.10)

#### CLM-C1 — Stability across weight-vector family (F2 axis A3)
| Field | Value |
|---|---|
| Claim text | *"Across the six pre-registered weight vectors {`w_uniform`, `w_paper1_placeholder`, `w_epss_dominant`, `w_cvss_dominant`, `w_kev_dominant`, `w_context_dominant`}, the headline EHD pattern is/is not stable (max-min ΔEHD across vectors with paired-seed BCa CI)."* |
| Status | primary for class C |
| Primary metric | **sensitivity delta in EHD across A3** = `max_v EHD(v) − min_v EHD(v)` per (capacity, blackout, approver) cell |
| Secondary metrics | `rank_churn` between pairs of vectors at the same cell; `capacity_efficiency`; `scheduler_feasibility_rate` |
| Required axis | A3 weight-vector family, held at central A1/A6/A7 |
| Allowed interpretation | "Conclusions are/are not stable across plausible fixed weight priors" |
| Forbidden interpretation | Any claim that one vector is the "right" choice; W4 (no re-weighting after results); W6 (no literature-numeric masquerading) |
| Minimum data condition | All six vectors run at central cell with ≥ seed-count (F4) |
| Stop rule | F2 W1: if all vectors are statistically indistinguishable on EHD across every cell, report that. No re-tuning. |

#### CLM-C2 — Stability across capacity ratios (A1)
| Field | Value |
|---|---|
| Claim text | *"Across capacity ratios {0.005, 0.01, 0.02, 0.05}, the EHD delta vs EPSS-only is/is not stable for each strategy."* |
| Status | primary for class C |
| Primary metric | sensitivity delta in EHD across A1 |
| Secondary metrics | `capacity_efficiency`; `scheduler_feasibility_rate`; rank_churn across capacities |
| Required axis | A1 capacity, A2 strategy, A3 weight vector held at central |
| Allowed interpretation | Descriptive stability/instability across capacity |
| Forbidden interpretation | Claiming any specific capacity is "optimal" (the choice is exogenous to the paper); claiming "strategy dominates capacity" without citing Roytman *Capacity is King* (P3 in Step 3.10) |
| Minimum data condition | All four capacities run for ≥ central strategies × ≥ seed-count |
| Stop rule | If every strategy's ΔEHD changes monotonically with capacity in the same direction (no sensitivity), report capacity as a *strong moderator* and re-frame the finding accordingly. |

#### CLM-C3 — Stability across blackout policies (A6)
| Field | Value |
|---|---|
| Claim text | *"Across blackout policies {none, light, primary, strict}, the EHD delta vs EPSS-only is/is not stable per strategy at the central cell."* |
| Status | primary for class C |
| Primary metric | sensitivity delta in EHD across A6 |
| Secondary metrics | scheduler_feasibility_rate (must stay defined under strict blackout); rank_churn |
| Required axis | A6 blackout, others central |
| Allowed interpretation | Descriptive stability/instability |
| Forbidden interpretation | Recommending a specific blackout policy (out of scope) |
| Minimum data condition | All four policies run; scheduler_feasibility_rate > 0 in every cell |
| Stop rule | If `scheduler_feasibility_rate == 0` in any cell, that cell is excluded with a written note (do not silently drop). |

#### CLM-C4 — Stability across feature ablations (A5)
| Field | Value |
|---|---|
| Claim text | *"Removing feature f ∈ {C, X, R, K, E} from each fixed-prior vector changes EHD by Δf with CI; the headline EHD pattern is/is not preserved."* |
| Status | primary for class C |
| Primary metric | sensitivity delta in EHD across A5, applied to each A3 vector |
| Secondary metrics | rank_churn between ablated and full at the central cell |
| Required axis | A5 feature ablation × A3 weight-vector family; A1/A6/A7 central |
| Allowed interpretation | "Feature f contributes/does not contribute meaningfully across the vector family" |
| Forbidden interpretation | Any claim of "the most important feature" without showing it across the full vector family; any superiority interpretation (sensitivity, not contribution attribution) |
| Minimum data condition | Ablations run at central A1/A6/A7 for each of the six A3 vectors |
| Stop rule | If ablation effect sign flips between vectors, report explicitly — do not pick the convenient vector. |

### Class D — Ranking quality (DIAGNOSTIC-ONLY)

#### CLM-D1 — Per-window precision/recall/nDCG@k (diagnostic)
| Field | Value |
|---|---|
| Claim text | *"At per-t0 horizons with positive counts ∈ {0,1,2}, precision@k / recall@k / nDCG@k take 0/(0|1/k|2/k|1) step-function values; rank-quality claims are NOT supportable as headline."* |
| Status | **diagnostic-only** (Step 3.8 sparsity) |
| Primary metric | n/a — not bound to any primary claim |
| Allowed (diagnostic) metrics | `precision_at_k`, `recall_at_k`, `ndcg_at_k`, `ranking_curve_at_ks` |
| Required axis | reported per-t0 as descriptive appendix only |
| Allowed interpretation | "Per-window ranking metrics are reported as diagnostics; under the measured 7-positive sparsity they cannot bear a headline claim." |
| Forbidden interpretation | Any per-window ranking comparison used as a primary or secondary support for CLM-B1/C1; any per-cell precision@k aggregation that pretends to inferential weight |
| Minimum data condition | per-window positive count must be reported alongside the metric value; if positive count == 0, the metric is undefined and is reported as `NaN`, not 0 |
| Stop rule | If a reviewer pushes to elevate D1 to primary, this binding is the written refusal: gate is Step-3.8 measured sparsity. |

### Class E — Operational feasibility

#### CLM-E1 — Scheduler feasibility under each scenario
| Field | Value |
|---|---|
| Claim text | *"Across all pre-registered cells, the scheduler produces feasible schedules at rate `scheduler_feasibility_rate` ∈ [0, 1]."* |
| Status | primary for class E |
| Primary metric | `scheduler_feasibility_rate` |
| Secondary metrics | `capacity_efficiency`; `scheduled_count` ≤ capacity (sentinel); `risk_acceptance_rate` (diagnostic) |
| Required axis | every cell in the pre-registered factorial |
| Allowed interpretation | "Pipeline operates within capacity in X% of cells" |
| Forbidden interpretation | Any claim that scheduler feasibility implies prioritization quality (it does not) |
| Minimum data condition | every cell completes; audit logs valid (CLM-F1) |
| Stop rule | If any cell has `scheduler_feasibility_rate < 1.0` because `scheduled_count > capacity`, treat as a code defect, fix and re-run; do not paper over. |

#### CLM-E2 — Capacity utilisation stays within bound
| Field | Value |
|---|---|
| Claim text | *"For every cell, `capacity_efficiency` ∈ [0, 1]; scheduled count ≤ capacity."* |
| Status | secondary (sentinel) |
| Primary metric | `capacity_efficiency` |
| Secondary metrics | `scheduled_count`, `deferred_count`, `escalation_count` |
| Required axis | every cell |
| Allowed interpretation | Sentinel only |
| Forbidden interpretation | Any "efficient prioritization" headline using capacity_efficiency without binding to EHD |
| Minimum data condition | Same as CLM-E1 |
| Stop rule | Violation → code defect → fix → re-run |

### Class F — Audit / reproducibility

#### CLM-F1 — Audit hash-chain validity end-to-end
| Field | Value |
|---|---|
| Claim text | *"Every Paper-2 run yields a complete append-only audit log whose SHA-256 hash chain validates."* |
| Status | primary for class F |
| Primary metric | `hash_chain_validity(audit_log_path)` == True |
| Secondary metrics | `audit_record_count_by_type` (non-zero for each expected type); `audit_explanation_completeness` (sentinel) |
| Required axis | every Paper-2 run (no axis sweep needed) |
| Allowed interpretation | "Paper-2 outputs are content-addressed-auditable" |
| Forbidden interpretation | Any claim that auditability implies correctness of substantive results |
| Minimum data condition | audit logs written on every run |
| Stop rule | Any chain validity False → stop, investigate, do not include the run |

#### CLM-F2 — Paper-1 freeze invariant preserved
| Field | Value |
|---|---|
| Claim text | *"`make verify-primary-freeze` passes immediately before and immediately after every Paper-2 run."* |
| Status | primary (invariant) |
| Primary metric | freeze verification status (binary) |
| Secondary metrics | n/a |
| Required axis | every Paper-2 run |
| Allowed interpretation | "Paper 1's frozen artefact was not perturbed by Paper 2 work" |
| Forbidden interpretation | n/a |
| Minimum data condition | freeze status recorded in each run's audit |
| Stop rule | Any freeze failure → stop the whole step, investigate, do not include any subsequent run; this is kill criterion K6 from Step 3.9 |

### Class G — KEV deadline (DIAGNOSTIC-ONLY)

#### CLM-G1 — KEV breach rate (diagnostic)
| Field | Value |
|---|---|
| Claim text | *"`kev_deadline_breach_rate` per cell is reported as a descriptive diagnostic. Under Step 3.8 sparsity (7 unique positives, ≤2 KEV events per t0 window in any positive window) it cannot bear a headline claim."* |
| Status | **diagnostic-only** |
| Primary metric | n/a |
| Allowed (diagnostic) metrics | `kev_deadline_breach_rate`, `kev_remediation_latency` |
| Required axis | reported per cell, with KEV event count alongside |
| Allowed interpretation | Descriptive only |
| Forbidden interpretation | Any headline KEV-deadline claim under measured sparsity |
| Minimum data condition | KEV event count reported alongside the rate; if count == 0, metric reported as `NaN` |
| Stop rule | If sufficient KEV events appear in a future run (≥ 20 events per cell at the central capacity), F3 may be reopened to promote G1 to primary — until then, diagnostic-only. |

---

## 4. Axis → Claim binding table (uses Step-3.9 §6 + Step-3.11 weight-vector axis)

| Axis ID | Axis | Levels | Claim it supports | Metric | Primary / Secondary / Diagnostic | Inclusion |
|---|---|---|---|---|---|---|
| A1 | capacity ratio | 0.005, 0.01, 0.02, 0.05 | **CLM-C2**, CLM-B1, CLM-E1, CLM-E2 | EHD; capacity_efficiency; scheduler_feasibility_rate | **primary** for CLM-C2; secondary for CLM-B1/E1/E2 | **minimal factorial — REQUIRED** |
| A2 | strategy | 13 strategies (Paper 1's full list) | CLM-B1, CLM-B2, CLM-B3 | EHD; eehda_relative; fraction_of_oracle | primary for CLM-B* | **minimal factorial — REQUIRED** |
| A3 | weight-vector family (Step 3.11) | `w_uniform`, `w_paper1_placeholder`, `w_epss_dominant`, `w_cvss_dominant`, `w_kev_dominant`, `w_context_dominant` | **CLM-C1**, applied to `proposed_full` template | sensitivity delta in EHD; rank_churn | **primary** for CLM-C1 | **minimal factorial — REQUIRED** |
| A4 | label source | Label A KEV-only **(primary)**; Label B local-PoC (only if license-gated) | CLM-A1 (sparsity by label source); CLM-B1 robustness re-run | unique positive CVEs (A); EHD (B) | primary for CLM-A1 secondary report; secondary for CLM-B1 robustness | **CONFIRMATORY — secondary table only** (PoC requires `PAPER1_ENABLE_POC_FETCH=true`; do not redistribute) |
| A5 | feature ablation | drop C, drop X, drop R, drop K, drop E | **CLM-C4**, evaluated per A3 vector | sensitivity delta in EHD; rank_churn | **primary** for CLM-C4 | **CONFIRMATORY — required at central A1/A6/A7** |
| A6 | blackout policy | none, light, primary, strict | **CLM-C3**, CLM-E1 | sensitivity delta in EHD; scheduler_feasibility_rate | **primary** for CLM-C3; secondary for CLM-E1 | **minimal factorial — at least 2 levels** |
| A7 | approver policy | A, B | CLM-C* (robustness extension), CLM-E1 | sensitivity delta in EHD; scheduler_feasibility_rate | secondary | **CONFIRMATORY — secondary table at central A1/A6** |
| A8 | EPSS era | v3 only (2023-03-07 .. 2025-03-16) | n/a (held fixed; not a sweep) | n/a | n/a (held fixed) | **HELD FIXED** — v4 explicitly out of scope per Step 3.9 |
| A9 | catalog strictness | `cpe_exact` only | n/a (held fixed; `cpe_fuzzy`/`manual` deferred) | n/a | n/a | **HELD FIXED** — deferred per Step 3.9 |

The minimal-factorial enumeration (which cells exactly) is **F6's job**, not F3.
F3 fixes which axes serve which claims and with which metric; F6 will pick the
specific cells subject to compute budget (F8).

---

## 5. Diagnostic-only metrics (explicit list and rationale)

| Metric | Why diagnostic-only |
|---|---|
| `precision_at_k`, `recall_at_k`, `ndcg_at_k`, `ranking_curve_at_ks` | Step-3.8 measured sparsity: at per-t0 positives ∈ {0,1,2}, these are 0 / step-function values; *insufficient event count* to bear a headline ranking-quality claim. |
| `kev_deadline_breach_rate`, `kev_remediation_latency` | Same root cause: per-window KEV events ≤ 2 in 5/18 windows, 0 in 13/18; **unstable denominator** under sparsity. |
| `risk_acceptance_rate` | Operational sentinel; not bound to any label outcome; useful for *interpretation*, not a headline claim. |
| `imputation_rate_per_feature` | Operational sentinel; informative but not a research claim. |
| `audit_explanation_completeness` | Sanity / sentinel. |
| `poam_review_trigger_compliance` | Compliance scaffolding from Paper 1; not used as Paper-2 primary or secondary. |

A diagnostic-only metric **may appear in appendix tables** but **may not** be
cited in the abstract, the contributions list, the main-text claims, or the
discussion as a basis for a substantive conclusion.

---

## 6. Forbidden claims (explicit; bound to W*-style stop rules)

The following claims are **forbidden** in Paper 2 regardless of measurement
outcome. They cannot be promoted to "supported" by any binding in §3.

| Forbidden claim | Why forbidden | Stop rule |
|---|---|---|
| *"Fixed weights outperform EPSS in general."* | Step 3.10 prior art (Sherif 2026, Roytman, Koscinski 2025) — superiority claim collides; also Step 3.11 W2 |
| *"Context-aware prioritization is superior."* | Step 3.10 prior art (Sherif 2026, VulRG, SSVC) + no calibration in this paper |
| *"Calibration improves results."* | Step 3.8 calibration not attempted (7 < 50 gate) |
| *"The model is validated."* | No external validation; only sensitivity sweeps on a frozen synthetic-fleet extension |
| *"Production readiness."* | Synthetic fleet (acknowledged limitation per Step 3.10 §9.5) |
| *"Compliance achievement."* | Out of scope (compliance was the killed Paper 2 topic in Step 2.5) |
| *Any claim using pair count as the calibration sample size.* | Step 3.8 + Step 3.11 W7; effective N is unique positive distinct CVEs |
| *Any claim using `event_positive_cves_across_windows` as the calibration sample size.* | Same root cause — duplicates per-window appearances of the same CVE |
| *Any claim selected after seeing which metric "looks best".* | Cherry-picking is what F3 exists to prevent |
| *Any claim that ranks weight vectors by quality.* | Step 3.11 W6 — vectors are design priors, not quality-ordered |
| *Any claim that the synthetic-fleet extension matches real-host risk.* | Step 3.10 §9.5 limitation |
| *Any claim based on EPSS v4 results.* | A8 held fixed at v3 (model-version boundary) |
| *Any claim based on PoC labels without the license gate set.* | Standing project rule (license-gated; never redistributed) |

---

## 7. Stop rules summary (collected from §3, §4, §6; carried into Step-4 pre-registration)

- **S-A** (CLM-A1): unique positives < 20 → calibration paper remains pivoted; no calibration experiments.
- **S-B1** (CLM-B1): if ΔEHD CI overlaps 0 in every cell, report that as the finding; no re-tuning. *(Mirrors F2 W1.)*
- **S-B3** (CLM-B3): if oracle ≈ random within CI, report "oracle ill-defined" and do not use B3 as headline.
- **S-C1** (CLM-C1): if vectors indistinguishable, report; no re-tuning. *(F2 W1.)*
- **S-C2** (CLM-C2): if monotonic strong moderation by capacity, re-frame, do not cherry-pick.
- **S-C3** (CLM-C3): cells with `scheduler_feasibility_rate == 0` excluded **with a written note**.
- **S-C4** (CLM-C4): ablation sign-flip between vectors → report; do not pick the convenient vector.
- **S-D1** (CLM-D1): metric undefined when per-window positives = 0 → `NaN`, not 0. No promotion to primary.
- **S-E1** (CLM-E1): scheduler infeasibility → code defect → fix → re-run; do not paper over.
- **S-E2** (CLM-E2): capacity overflow → same as S-E1.
- **S-F1** (CLM-F1): hash-chain invalid → stop, investigate, exclude the run.
- **S-F2** (CLM-F2): freeze verification fail → stop the step (kill criterion K6).
- **S-G1** (CLM-G1): elevation to primary requires ≥20 KEV events per cell at the central capacity in a future re-run; otherwise diagnostic-only.

---

## 8. Implementation implications for Step 4 (NOT executed here)

When Step 4 begins (only after F4–F9 land), the implementation must:

1. **Per-row tagging.** Every Paper-2 result row must carry: `claim_id` ∈
   {CLM-A1, …, CLM-G1, or `diagnostic`}, `primary_metric_name`,
   `secondary_metric_names`, `axis_cell_id` (the (A1, A2, A3, A5, A6, A7) tuple),
   `weight_family` / `weight_source` / `weight_vector_name` (from F2),
   `freeze_status_before`, `freeze_status_after`, `audit_hash_chain_valid`.
2. **Per-cell positive count.** Every D1/G1 row must carry the per-window
   positive count alongside the metric value; metrics undefined when count = 0
   are written as `NaN`.
3. **Forbidden-claim guard.** A pre-commit/test-time guard scans manuscript
   markdown for any of the §6 forbidden phrases and fails CI; the existing
   Paper-1 claim-audit script (`Phase 21 / 22A`) is the precedent.
4. **No new metrics may be added** without writing a new F3 supplement
   (`STEP3_12.1_F3_SUPPLEMENT_<short-name>.md`) and updating the decision log.
5. **Statistical infrastructure.** `wilcoxon_signed_rank` + `holm_bonferroni`
   may be used only on axes where F4 (next step) shows MDE ≤ meaningful-effect
   threshold; otherwise descriptives + BCa CI only. F3 does not pre-register
   the tests themselves — that is F4.
6. **Paper-1 freeze invariant.** Wrap every Paper-2 run with
   `make verify-primary-freeze` before and after; record both freeze hashes in
   the audit log (CLM-F2 is this).
7. **Per-axis stop-rule enforcement.** §7 stop rules are encoded as runtime
   checks; violations halt the run and emit a structured error, never silently
   alter results.

---

## 9. Unresolved issues
- F4 (MDE / power per axis) must be locked before any per-axis inferential test
  is allowed. F3 binds metrics to claims; F4 will bind statistical-test
  applicability to MDE thresholds.
- F6 (minimal factorial enumeration) must commit to specific cells; F3 only
  identifies *which axes are required* for each claim.
- F2 unresolved citation items carry forward: VULCON `[VERIFY-DOI]`, NIST
  CSWP 41 LEV `[VERIFY]`, VulnScore `[VERIFY]`.
- The F1-mandated framing changes (Step-3.10 §9 items 1–7) must land in
  `STEP4_PREREGISTRATION.md` before Step 4 starts.

---

## 10. F3 status and decision-flow summary
- **F3: COMPLETE.** Metric → claim binding table locked for classes A–G; 13
  claims pre-registered with explicit primary metric, secondary metrics,
  required axis, allowed/forbidden interpretations, minimum data condition,
  and stop rule. Axis → claim mapping locked. Diagnostic-only metrics
  enumerated with rationale. 13 forbidden claims enumerated with stop rules.
  No new metrics introduced; no new axes introduced; Paper 1 frozen outputs
  untouched.
- **Step 4 still NOT allowed.** F4–F9 owed; F1-mandated framing changes owed.

## Invariants honored
Paper 1 frozen outputs untouched. No code written; no experiments run; no paper
drafted. No new metrics or axes introduced. No calibration claim, no superiority
claim. The calibration-feasibility claim remains anchored to **unique positive
distinct CVEs** (not pair count, not event sum). PoC/ExploitDB license-gated
and off by default. No fabricated citations.
