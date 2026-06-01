<!--
Paper 2 — Step 3.14: Fix F5 — Encode Kill Criteria as Runtime STOP Rules.
Merges Step-3.9 K1–K6, F3 S-A..S-G1, F4 SM-1..SM-6 into a single canonical
stop-rule registry. Every rule has a computable trigger, a locked threshold,
and an explicit action. No new metrics; no F3/F4 binding changes; no code; no
experiments. Paper 1 frozen outputs untouched.
-->

# Paper 2 — Step 3.14: Fix F5 — Canonical Stop-Rule Registry

**F5 status: COMPLETE.**
**Step 4 still NOT allowed** (F6–F9 owed; Step-3.10 framing changes still owed).

This document encodes the Step-3.14 kill criteria K1–K6 (from the task brief) as
runtime STOP rules with computable triggers and locked thresholds, preserves the
intent of the original Step-3.9 K1–K6 by promoting the missing items to
additional rules **K7–K8** (catalog-stability and seed-noise dominance), and
merges everything with the F3 claim-level stops (S-A..S-G1) and F4 statistical
stops (SM-1..SM-6) into a single canonical registry. Step-4 implementation will
read this registry verbatim; no rule may be added, removed, or re-thresholded
without a written supplement and a new decision-log row.

---

## 1. Provenance of every rule (no rule is invented in F5)

| Source doc | Rules contributed |
|---|---|
| `STEP3_9_PIVOT_RESEARCH_VALIDATION.md` §11 | original Step-3.9 K1–K6 (preserved in intent; canonical IDs assigned below) |
| `STEP3_12_FIX_F3_METRIC_CLAIM_BINDING.md` §7 | S-A, S-B1, S-B3, S-C1..C4, S-D1, S-E1, S-E2, S-F1, S-F2, S-G1 |
| `STEP3_13_FIX_F4_MDE_POWER.md` §7 | SM-1, SM-2, SM-3, SM-4, SM-5, SM-6 |
| Step-3.14 task brief | canonical kill IDs K1–K6 (verbatim thresholds where given) |
| Step-3.8 measured artefact `paper2/feasibility/probe_v2_multit0/` | numeric trigger inputs for K1 / K3 |

**Mapping of original Step-3.9 K1–K6 → canonical Step-3.14 IDs:**

| Step-3.9 ID | Original intent | Canonical Step-3.14 ID | Notes |
|---|---|---|---|
| Step-3.9 K1 | sweeps show no measurable variation | **K2** | F5 task brief restated with computable threshold (median ΔEHD < 1,000 hd AND BCa CI ⊂ ±5,000 hd) |
| Step-3.9 K2 | per-cell variance dominated by seed noise | **K8** (promoted) | CV_within / CV_across comparison |
| Step-3.9 K3 | CPE→catalog mapping unstable | **K7** (promoted) | catalog-perturbation drift > 30 % |
| Step-3.9 K4 | "all strategies equivalent" + venue insufficiency | covered by K2 + deferred to **F9** for the venue-fit part (not a runtime kill) |
| Step-3.9 K5 | leakage warning fires at scale | **K5.a** sub-trigger (merged into K5 audit/freeze category) |
| Step-3.9 K6 | Paper-1 freeze fails | **K6** (verbatim) |

---

## 2. Canonical Step-3.14 kill criteria K1–K6 (verbatim from task brief; thresholds locked)

Each rule has the F5 required fields. Numeric inputs come from artefacts that
already exist (Step-3.8 probe outputs, Step-4 will produce the rest).

### K1 — Calibration infeasibility
| Field | Value |
|---|---|
| `rule_id` | K1 |
| `severity` | **fatal** (pivot-locked) |
| `stage` | pre-registration (re-checked at every Step-4 startup) |
| `metric` | unique positive distinct CVEs |
| `artifact` | `paper2/feasibility/probe_v2_multit0/aggregate_counts.csv` (column `value` where `metric == "unique_positive_cves"`) + `decision_gate.json` field `decision` |
| `trigger` | `unique_positive_cves < 20` **OR** `decision != "GO"` |
| `locked_threshold` | 20 unique positive distinct CVEs |
| `action_on_trigger` | calibration paper remains killed/pivoted; **calibration experiments prohibited**; **all learned-weight claims forbidden** (no `register_calibrated_weights` calls in any Paper-2 run) |
| `audit_record` | append `{"event":"K1.calibration_pivot_locked","measured":7,"threshold":20,"decision":"PIVOT"}` to `paper2/audit/stop_rules.log` at Step-4 startup |
| `status_now` | **ALREADY TRIGGERED** — Step 3.8 measured 7 unique positives; decision = `PIVOT_away_from_calibration` |

### K2 — Robustness sweeps show no measurable variation
| Field | Value |
|---|---|
| `rule_id` | K2 |
| `severity` | hard-pivot (paper re-framed) |
| `stage` | post-run, after every primary robustness-axis sweep completes |
| `metric` | paired ΔEHD across each primary robustness axis (A1 capacity, A3 weight family, A5 ablation, A6 blackout) |
| `artifact` | Step-4 per-seed metric frame (column `ehd_absolute`) + paired-Δ derived table |
| `trigger` | for **every** primary robustness axis (A1, A3, A5, A6), at every cell in the minimal factorial: `\|median(paired ΔEHD)\| < 1,000 host-days` **AND** BCa-95 % CI ⊂ `[-5,000, +5,000]` host-days |
| `locked_threshold` | 1,000 host-days median + ±5,000 host-days CI envelope (F4 operational + F4 meaningful) |
| `action_on_trigger` | paper is re-framed as **negative / failure-aware methodology result**; CLM-C1..C4 are demoted to descriptive-only with explicit "no measurable variation across the swept axis" sentence; no positive robustness-effect claim allowed |
| `audit_record` | append `{"event":"K2.robustness_null","axes_triggered":[...],"per_axis_median_dehd":{...},"per_axis_ci":{...}}` |
| `branching` | if K2 fires on **some but not all** primary axes → paper keeps its scope with explicit per-axis stop-rule report; only when K2 fires on **all** primary axes does the full reframing trigger |
| `status_now` | not measurable until Step 4 |

### K3 — Public-feed label sparsity invalidates ranking claims
| Field | Value |
|---|---|
| `rule_id` | K3 |
| `severity` | downgrade-claim (ranking diagnostic-only) |
| `stage` | pre-registration (already measured) + per-cell at run time |
| `metric` | per-window future positives count; total unique positive distinct CVEs |
| `artifact` | `paper2/feasibility/probe_v2_multit0/per_t0_counts.csv` (column `positive_cves_this_window`) + `aggregate_counts.csv` (column `value` at `metric == "unique_positive_cves"`) |
| `trigger` | `(positive_cves_this_window < 3) for more than 75 % of t0 windows` **OR** `unique_positive_cves < 20` |
| `locked_threshold` | 3 per-window positives; 75 % of windows; 20 unique positives |
| `action_on_trigger` | ranking metrics (`precision_at_k`, `recall_at_k`, `ndcg_at_k`) stay **diagnostic-only** (CLM-D1 binding from F3); no headline ranking claim; KEV breach rate (CLM-G1) also stays diagnostic |
| `audit_record` | `{"event":"K3.label_sparsity","windows_with_lt3_positives":18,"total_windows":18,"unique_positive_cves":7,"threshold_windows_pct":75,"threshold_unique":20}` |
| `status_now` | **ALREADY TRIGGERED** — Step 3.8: every one of the 18 windows had positives ≤ 2 (max = 2, in 5 windows; 0 in 13 windows = 72.2 % literal), AND `unique_positive_cves = 7 < 20`. Even though the "< 3 in 75 % of windows" clause alone is 72.2 % (just below 75 %), the OR with `unique < 20` fires K3 unconditionally |

### K4 — Scheduler infeasibility
| Field | Value |
|---|---|
| `rule_id` | K4 |
| `severity` | exclude-cell |
| `stage` | per-cell, post-run |
| `metric` | `scheduler_feasibility_rate` |
| `artifact` | Step-4 per-seed metric frame (column `metric == "scheduler_feasibility"`) aggregated per cell |
| `trigger` | for any primary factorial cell: `scheduler_feasibility_rate < 0.95` |
| `locked_threshold` | 0.95 |
| `action_on_trigger` | **exclude the affected cell** from primary operational claims (CLM-E1, CLM-B1 at that cell); write a footnote table row recording cell id, observed rate, and the reason; **do not silently drop** |
| `audit_record` | `{"event":"K4.scheduler_infeasible","cell_id":"...","rate":<f>,"threshold":0.95}` |
| `status_now` | not measurable until Step 4. Paper-1 frozen artefact had `scheduler_feasibility = 1.0` across all 30 seeds × 13 strategies (read-only confirmation), so the Paper-2 baseline expectation is rate ≈ 1.0. |

### K5 — Audit / freeze failure
| Field | Value |
|---|---|
| `rule_id` | K5 |
| `severity` | **hard halt** of the affected run |
| `stage` | per-run (pre-flight, post-run); per-seed (post-seed) |
| `metric` | `hash_chain_validity(audit_log_path)` (binary) + freeze verification status |
| `artifact` | per-run audit log file + `results/primary_full_v1/FREEZE_MANIFEST.json` |
| `trigger` | `hash_chain_validity == False` **OR** `make verify-primary-freeze` exits non-zero **OR** a Step-3.9-K5-style real-feed leakage warning is recorded by `label_a` (sub-trigger **K5.a**) |
| `locked_threshold` | binary (any failure = trigger) |
| `action_on_trigger` | **halt the affected run**; do not generate any paper table from its output; surface the failing artefact path in the abort message; require a written incident note in the decision log before any re-run |
| `audit_record` | `{"event":"K5.audit_or_freeze_failure","hash_chain_valid":<b>,"freeze_ok":<b>,"leakage_warning":<b>,"artifact":<path>}` |
| `status_now` | not triggered; Paper 1 freeze verified OK before and after every Paper-2 step so far (Steps 3.5–3.13). |

### K6 — Paper 1 frozen artifact modified
| Field | Value |
|---|---|
| `rule_id` | K6 |
| `severity` | **hard halt** of the entire Paper-2 step |
| `stage` | every run (pre-flight AND post-run wrap); every long step (3.5+) |
| `metric` | freeze verification status (binary) |
| `artifact` | `results/primary_full_v1/FREEZE_MANIFEST.json` via `scripts/inspect_primary_results.py --verify-freeze` |
| `trigger` | `make verify-primary-freeze PYTHON=.venv/bin/python` exits non-zero either immediately before or immediately after any Paper-2 run |
| `locked_threshold` | binary |
| `action_on_trigger` | **halt immediately**; Paper-2 result invalid until freeze is restored from a verified copy or new provenance is documented; CI must refuse to publish tables/figures derived from a run that did not record both `freeze_status_before == OK` and `freeze_status_after == OK` |
| `audit_record` | `{"event":"K6.paper1_freeze_failed","when":"pre_run\|post_run","artifact":"results/primary_full_v1/FREEZE_MANIFEST.json"}` |
| `status_now` | not triggered; verified OK at every step boundary so far. |

---

## 3. Preserved Step-3.9 rules promoted to canonical IDs

### K7 — Catalog → CVE mapping unstable (Step-3.9 K3)
| Field | Value |
|---|---|
| `rule_id` | K7 |
| `severity` | downgrade-claim (pair-stability footnote) or pivot if extreme |
| `stage` | pre-run perturbation check, executed once during Step-4 setup |
| `metric` | catalog-perturbation drift = (|symmetric difference of catalog-matched-CVE-set under perturbed vs. unperturbed catalog| / |union|) |
| `artifact` | new pre-run check writing to `paper2/feasibility/catalog_drift_check.json`; perturbation method: drop / swap one product at a time from the 31-product catalog, recompute catalog-matched CVE set against the cached NVD universe, record drift |
| `trigger` | drift > 30 % across any single one-product perturbation |
| `locked_threshold` | 30 % |
| `action_on_trigger` | (a) record catalog-stability as an explicit limitation in every Paper-2 table footer; (b) if drift > 30 % under **multiple** perturbations, **pivot K7** to "catalog-mapping unstable; Paper 2 results cannot bind to a specific catalog choice" and reduce CLM-B1/CLM-C1..C4 scope accordingly |
| `audit_record` | `{"event":"K7.catalog_drift","max_drift":<f>,"perturbations":[...]}` |
| `status_now` | not measured yet (pre-run check; deferred to Step 4 setup). Per Step-3.9 §11 K3 wording, this is the canonical encoding. |

### K8 — Per-cell variance dominated by seed noise (Step-3.9 K2)
| Field | Value |
|---|---|
| `rule_id` | K8 |
| `severity` | downgrade-claim (sensitivity-axis reporting becomes descriptive-only) |
| `stage` | post-run, per axis |
| `metric` | CV_within (per cell std / mean of EHD across seeds) vs CV_across (axis-level max-min ΔEHD / mean EHD) |
| `artifact` | Step-4 per-seed metric frame |
| `trigger` | for any primary robustness axis: `CV_within > CV_across` |
| `locked_threshold` | strict inequality |
| `action_on_trigger` | for that axis, CLM-C* is reported **descriptively only** with the explicit sentence "axis-level variation is below within-cell seed-noise scale; no informative sensitivity claim"; sentivity-Δ inferential test for that axis is *dropped* (SM-2-style auto-drop) |
| `audit_record` | `{"event":"K8.seed_noise_dominant","axis":<id>,"cv_within":<f>,"cv_across":<f>}` |
| `status_now` | not measurable until Step 4. |

**Note on Step-3.9 K4 (venue insufficiency).** Step-3.9 K4 — "results collapse + sparsity figure alone insufficient for the venue" — is partly covered by K2 (no measurable variation) at run time and partly by **F9** (venue plan + change-our-minds clause) at manuscript time. It is **not** encoded as a runtime STOP rule because "sufficient for the chosen venue" requires the venue itself, which F9 will pick. F5 explicitly does not invent a runtime threshold for venue fit.

---

## 4. Canonical merged registry (by category × stage × enforcement)

All rules carry: `rule_id`, `severity`, `stage`, `metric`, `artifact`, `trigger`, `locked_threshold`, `action_on_trigger`, `audit_record`.

### 4.1 Acquisition / data rules

| ID | Severity | Stage | Trigger | Action | Source |
|---|---|---|---|---|---|
| K1 | fatal (pivot-locked) | pre-registration | `unique_positive_cves < 20` OR `decision != GO` | calibration forbidden; learned-weight claims forbidden | Step-3.14 K1 |
| K3 | downgrade-claim | pre-reg + per-cell | per-window positives < 3 in > 75 % of windows OR unique positives < 20 | ranking + KEV-breach diagnostic-only | Step-3.14 K3 |
| K7 | downgrade or pivot | pre-run setup | catalog-perturbation drift > 30 % | mapping-stability footnote or pivot | Step-3.9 K3 (promoted) |
| S-A | downgrade-claim | pre-reg | mirrors K1 | same as K1 | F3 |

### 4.2 Calibration-feasibility rules

| ID | Severity | Stage | Trigger | Action | Source |
|---|---|---|---|---|---|
| K1 | fatal | pre-reg | (see §4.1) | pivot to robustness-only | Step-3.14 K1 |
| S-A | downgrade-claim | pre-reg | unique positives < 20 → no calibration experiments | mirror | F3 |

### 4.3 Metric-validity rules

| ID | Severity | Stage | Trigger | Action | Source |
|---|---|---|---|---|---|
| S-D1 | diagnostic-only | per-cell | per-window positives = 0 | metric = `NaN` not 0; no promotion | F3 |
| S-G1 | diagnostic-only | per-cell | KEV events / cell < 20 at central capacity | KEV breach diagnostic-only; no headline | F3 |
| K3 | downgrade-claim | per-cell | (see §4.1) | ranking diagnostic-only | Step-3.14 K3 |

### 4.4 Statistical-inference rules

| ID | Severity | Stage | Trigger | Action | Source |
|---|---|---|---|---|---|
| SM-1 | auto-drop | per-comparison | paired-Δ std = 0 | drop inferential test; print sentinel sentence | F4 |
| SM-2 | escalate | per-cell | per-window positives < 1 | escalate sparsity inflation ×1.5 → ×2.0 **before** recomputing | F4 |
| SM-3 | disable | per-comparison | comparator = oracle (sparse-label-weak) | `oracle_inference: disabled` config flag for CLM-B3 | F4 |
| SM-4 | descriptive-language | post-test | Holm passes at α = 0.05 BUT BCa CI overlaps 0 OR ⊂ [-5,000, +5,000] hd | manuscript uses descriptive language only, not "significant" | F4 |
| SM-5 | CI guard | manuscript | diagnostic-only metric paired with significance phrasing in markdown | CI reject merge | F4 |
| SM-6 | hard halt | per-run | freeze verification fails | K6 alias | F4 |
| S-B1 | descriptive | post-cell | ΔEHD CI overlaps 0 in every cell | report it; no re-tuning | F3 |
| S-B3 | descriptive | post-cell | oracle ≈ random within CI | "oracle ill-defined" report; not headline | F3 |
| S-C1 | descriptive | post-axis | vectors indistinguishable | report it; no re-tuning | F3 |
| S-C2 | reframe | post-axis | monotonic strong moderation by capacity | reframe finding; do not cherry-pick | F3 |
| S-C3 | exclude-cell | per-cell | scheduler_feasibility_rate == 0 | exclude with written note | F3 |
| S-C4 | report-honest | post-axis | ablation sign-flip between vectors | report; do not pick convenient vector | F3 |
| K2 | hard-pivot | post-run | (see §2 K2) | reframe paper as negative-result | Step-3.14 K2 |
| K8 | downgrade-claim | post-axis | CV_within > CV_across | descriptive-only for that axis | Step-3.9 K2 (promoted) |

### 4.5 Scheduler-feasibility rules

| ID | Severity | Stage | Trigger | Action | Source |
|---|---|---|---|---|---|
| K4 | exclude-cell | per-cell | scheduler_feasibility_rate < 0.95 | exclude affected cell from primary claims | Step-3.14 K4 |
| S-C3 | exclude-cell | per-cell | scheduler_feasibility_rate == 0 | exclude with written note | F3 |
| S-E1 | code-defect | per-cell | scheduler_feasibility_rate < 1 because scheduled_count > capacity | treat as code defect; fix; re-run; do not paper-over | F3 |
| S-E2 | code-defect | per-cell | capacity_efficiency invariant violated (scheduled_count > capacity) | same as S-E1 | F3 |

### 4.6 Audit / freeze rules

| ID | Severity | Stage | Trigger | Action | Source |
|---|---|---|---|---|---|
| K5 | hard halt | per-run | hash_chain_validity False OR freeze fails OR leakage warning fires | halt; no tables from affected output | Step-3.14 K5 (+ Step-3.9 K5 leakage as sub-trigger K5.a) |
| K6 | hard halt | every step | `make verify-primary-freeze` non-zero pre or post | halt entire step; freeze invariant first | Step-3.14 K6 |
| S-F1 | hard halt | post-run | hash_chain_validity == False | stop, investigate, exclude the run | F3 |
| S-F2 | hard halt | every step | freeze fail | K6 alias | F3 |
| SM-6 | hard halt | every step | K6 alias | K6 alias | F4 |

### 4.7 Manuscript-claim rules

| ID | Severity | Stage | Trigger | Action | Source |
|---|---|---|---|---|---|
| SM-4 | descriptive-language | manuscript | (see §4.4) | descriptive language only | F4 |
| SM-5 | CI guard | manuscript | (see §4.4) | CI reject merge | F4 |
| `F3-forbidden-phrase guard` | CI reject | manuscript | any of the 13 forbidden-claim phrases from F3 §6 appears in markdown | CI reject; require written exception | F3 §6 |

---

## 5. Machine-readable registry sketch (YAML; Step-4 implementation contract)

```yaml
# paper2/manuscript/STEP3_14_STOP_RULES_REGISTRY.yaml — to be machine-loaded by Step-4
schema_version: 1
source_provenance:
  step_3_8: paper2/feasibility/probe_v2_multit0/
  step_3_9: paper2/manuscript/STEP3_9_PIVOT_RESEARCH_VALIDATION.md
  step_3_12: paper2/manuscript/STEP3_12_FIX_F3_METRIC_CLAIM_BINDING.md
  step_3_13: paper2/manuscript/STEP3_13_FIX_F4_MDE_POWER.md
  step_3_14: this file

# Numeric threshold constants (locked here; F4 contributes meaningful/operational).
constants:
  unique_positive_threshold: 20
  per_window_positive_floor: 3
  per_window_floor_share: 0.75
  meaningful_threshold_hd: 5000
  operational_threshold_hd: 1000
  scheduler_feasibility_floor: 0.95
  catalog_drift_threshold: 0.30

rules:
  # ---- Acquisition / data ----
  - rule_id: K1
    severity: fatal
    stage: pre_registration
    category: acquisition
    metric: unique_positive_distinct_cves
    artifact: paper2/feasibility/probe_v2_multit0/aggregate_counts.csv
    artifact_field: 'value where metric == unique_positive_cves'
    trigger: value < ${constants.unique_positive_threshold}
    action: pivot_calibration_to_sensitivity
    forbid:
      - learned_weight_claims
      - calibration_experiments
      - register_calibrated_weights_calls
    audit_record_template: {event: K1.calibration_pivot_locked, measured: <int>, threshold: 20, decision: <str>}
    status_now: TRIGGERED
    measured_value: 7

  - rule_id: K3
    severity: downgrade_claim
    stage: [pre_registration, per_cell]
    category: metric_validity
    metric: [positive_cves_this_window, unique_positive_distinct_cves]
    artifact: paper2/feasibility/probe_v2_multit0/per_t0_counts.csv
    trigger:
      any_of:
        - share_of_windows(positive_cves_this_window < ${constants.per_window_positive_floor}) > ${constants.per_window_floor_share}
        - unique_positive_distinct_cves < ${constants.unique_positive_threshold}
    action: ranking_metrics_diagnostic_only
    affects: [CLM-D1, CLM-G1]
    status_now: TRIGGERED  # 7 < 20

  - rule_id: K7
    severity: downgrade_or_pivot
    stage: pre_run_setup
    category: acquisition
    metric: catalog_perturbation_drift
    artifact: paper2/feasibility/catalog_drift_check.json   # produced by Step-4 pre-run check
    trigger: max(drift) > ${constants.catalog_drift_threshold}
    action: catalog_stability_footnote_or_pivot
    status_now: NOT_MEASURED

  # ---- Statistical inference ----
  - rule_id: K2
    severity: hard_pivot
    stage: post_run
    category: statistical_inference
    metric: median_paired_delta_ehd
    trigger:
      all_of_axes: [A1, A3, A5, A6]
      condition: 'abs(median_paired_delta_ehd) < ${constants.operational_threshold_hd} AND bca95_ci subset_of [-${constants.meaningful_threshold_hd}, +${constants.meaningful_threshold_hd}]'
    action: reframe_as_negative_result
    affects: [CLM-C1, CLM-C2, CLM-C3, CLM-C4]

  - rule_id: K8
    severity: downgrade_claim
    stage: post_axis
    category: statistical_inference
    metric: [cv_within, cv_across]
    trigger: cv_within > cv_across
    action: descriptive_only_for_axis
    affects: per_axis_CLM-C*

  - rule_id: SM-1
    severity: auto_drop
    stage: per_comparison
    category: statistical_inference
    metric: paired_delta_std
    trigger: paired_delta_std == 0
    action: drop_inferential_test_and_print_sentinel

  - rule_id: SM-2
    severity: escalate_prospective
    stage: per_cell
    category: statistical_inference
    metric: per_window_positive_count
    trigger: per_window_positive_count < 1
    action: escalate_sparsity_inflation_1.5x_to_2.0x_before_recompute

  - rule_id: SM-3
    severity: disable
    stage: per_comparison
    category: statistical_inference
    metric: comparator
    trigger: comparator == oracle
    action: oracle_inference_disabled_flag
    affects: [CLM-B3]

  - rule_id: SM-4
    severity: descriptive_language
    stage: post_test
    category: manuscript_claim
    metric: [holm_p, paired_bca_ci]
    trigger: holm_p < 0.05 AND (ci_overlaps_zero OR ci_subset_of([-${constants.meaningful_threshold_hd}, +${constants.meaningful_threshold_hd}]))
    action: use_descriptive_language_not_significant

  - rule_id: SM-5
    severity: ci_reject
    stage: manuscript_generation
    category: manuscript_claim
    metric: markdown_text
    trigger: diagnostic_only_metric_name near significance_phrase(p =, p<, significant, significance)
    action: ci_reject_merge

  - rule_id: S-B1
    severity: descriptive
    stage: post_cell
    category: statistical_inference
    metric: bca95_ci_paired_delta_ehd
    trigger: ci_overlaps_zero_in_every_cell
    action: report_no_re_tuning

  - rule_id: S-B3
    severity: descriptive
    stage: post_cell
    category: statistical_inference
    metric: paired_delta_ehd(oracle, random)
    trigger: 'abs(delta) < ${constants.meaningful_threshold_hd} AND ci_overlaps_zero'
    action: report_oracle_ill_defined

  - rule_id: S-C1
    severity: descriptive
    stage: post_axis
    category: statistical_inference
    metric: paired_delta_ehd_across_A3
    trigger: ci_overlaps_zero_for_every_vector_pair
    action: report_no_re_tuning

  - rule_id: S-C2
    severity: reframe
    stage: post_axis
    category: statistical_inference
    metric: paired_delta_ehd_across_A1
    trigger: monotonic_change_same_sign_every_strategy
    action: reframe_as_strong_moderation

  - rule_id: S-C3
    severity: exclude_cell
    stage: per_cell
    category: scheduler_feasibility
    metric: scheduler_feasibility_rate
    trigger: scheduler_feasibility_rate == 0
    action: exclude_cell_with_written_note

  - rule_id: S-C4
    severity: report_honest
    stage: post_axis
    category: statistical_inference
    metric: ablation_effect_sign
    trigger: sign_flips_between_vectors
    action: report_do_not_pick_convenient

  - rule_id: S-D1
    severity: diagnostic_only
    stage: per_cell
    category: metric_validity
    metric: [precision_at_k, recall_at_k, ndcg_at_k]
    trigger: per_window_positive_count == 0
    action: report_NaN_not_0; no_promotion_to_primary

  - rule_id: S-G1
    severity: diagnostic_only
    stage: per_cell
    category: metric_validity
    metric: kev_deadline_breach_rate
    trigger: kev_events_per_cell < 20
    action: kev_breach_diagnostic_only

  # ---- Scheduler feasibility ----
  - rule_id: K4
    severity: exclude_cell
    stage: per_cell
    category: scheduler_feasibility
    metric: scheduler_feasibility_rate
    artifact: per_seed_metric_frame
    trigger: scheduler_feasibility_rate < ${constants.scheduler_feasibility_floor}
    action: exclude_cell_from_primary_operational_claims_with_footnote
    affects: [CLM-E1, CLM-B1@cell]

  - rule_id: S-E1
    severity: code_defect
    stage: per_cell
    category: scheduler_feasibility
    metric: scheduled_count
    trigger: scheduled_count > capacity
    action: fix_and_rerun; never_paper_over

  - rule_id: S-E2
    severity: code_defect
    stage: per_cell
    category: scheduler_feasibility
    metric: capacity_efficiency
    trigger: scheduled_count > capacity
    action: fix_and_rerun; never_paper_over

  # ---- Audit / freeze ----
  - rule_id: K5
    severity: hard_halt
    stage: per_run
    category: audit_freeze
    metric: [hash_chain_validity, freeze_status, leakage_warning_count]
    artifact: audit_log_path
    trigger:
      any_of:
        - hash_chain_validity == false
        - freeze_status != OK
        - leakage_warning_count > 0     # K5.a sub-trigger
    action: halt_affected_run; no_tables_from_output

  - rule_id: K6
    severity: hard_halt
    stage: [pre_run, post_run, every_step]
    category: audit_freeze
    metric: verify_primary_freeze_exit
    artifact: results/primary_full_v1/FREEZE_MANIFEST.json
    trigger: verify_primary_freeze_exit != 0
    action: halt_entire_step

  - rule_id: SM-6
    alias_of: K6

  - rule_id: S-F1
    alias_of: K5
    note: hash-chain sub-condition

  - rule_id: S-F2
    alias_of: K6

  # ---- Manuscript claim ----
  - rule_id: F3-forbidden-phrase-guard
    severity: ci_reject
    stage: manuscript_generation
    category: manuscript_claim
    trigger: any_forbidden_phrase_present_in_markdown
    action: ci_reject_merge
    forbidden_phrases_source: STEP3_12_FIX_F3_METRIC_CLAIM_BINDING.md §6
```

The Step-4 implementation **must** load this YAML (or a sidecar generated from it),
attach a `rule_id` to every audit-log event, and refuse any code path that bypasses
a triggered rule.

---

## 6. Step-4 implementation contract (binding; no code now)

When Step 4 starts (only after F6–F9 land):

1. **Materialize the registry.** Generate `paper2/manuscript/STEP3_14_STOP_RULES_REGISTRY.yaml` from §5 verbatim (no edits). The Python loader lives under a new module `paper2_runtime.stop_rules` to be created in Step 4; it does *not* live under `src/paper1/` to keep Paper 1 untouched.
2. **Pre-flight gate.** At every Paper-2 run startup: assert K1 status (read Step-3.8 artefacts), assert K6 status (`make verify-primary-freeze`), assert K3 status (per-window positives + unique-positives load), refuse to proceed unless all pre-registration STOP rules' actions are honored in the run configuration (e.g., refuse to start if the config includes a `calibration` step while K1 is triggered).
3. **Per-cell gate.** Per cell: evaluate K3 per-cell sub-condition, K4 scheduler feasibility, S-C3/S-E1/S-E2 invariants.
4. **Per-comparison gate.** Wrap `wilcoxon_signed_rank` / `compare_to_baseline` calls in a policy shim that consults SM-1, SM-2, SM-3 and the F4 inference-status flag; raise on bypass attempts.
5. **Post-run gate.** Evaluate K2, K5, K7, K8, S-B1, S-B3, S-C1, S-C2, S-C4 against the produced metric frame; write `paper2/audit/stop_rules.log` (append-only, hash-chained, same pattern as Paper-1 audit logs).
6. **Manuscript-CI gate.** Re-use the Paper-1 Phase-21/22A claim-audit pattern: scan markdown for F3 §6 forbidden phrases (F3-forbidden-phrase-guard), SM-4 / SM-5 misuse, and any `p =` / `significant` near CLM-D1/G1 metric names. Block merges that violate.
7. **Audit completeness.** Every triggered rule must produce an `audit_record` per §2 / §3 / §5; missing audit records are themselves a CI failure (rule self-policing).
8. **No rule edits at runtime.** Edits to the registry require a written supplement (`STEP3_14.x_*.md`) and a decision-log row before they take effect.

---

## 7. Triggered-now summary
- **K1: TRIGGERED** (7 < 20) — calibration paper permanently pivoted; learned-weight claims forbidden.
- **K3: TRIGGERED** (7 < 20 satisfies the OR-branch; per-window count branch 72.2 %, marginal). Ranking + KEV-breach metrics locked diagnostic-only.
- **S-A: TRIGGERED** (mirrors K1).
- All other rules are **NOT_MEASURED** until Step 4 actually runs and produces a per-seed metric frame.

K1's triggered status is **permanent** unless a new Step-3.x pre-registration measures `unique_positive_cves ≥ 20` from a *re-run* full-window multi-t0 probe (e.g., after catalog expansion, which Step-3.9 deferred). K3's triggered status is similarly permanent on the current public-feed + 31-product slice.

---

## 8. F5 status
- **F5: COMPLETE.** Canonical Step-3.14 K1–K6 encoded with computable triggers, locked thresholds, and explicit actions. Step-3.9 K1–K6 intent preserved (K1↔K2; K2↔K8; K3↔K7; K4↔covered by K2 + deferred to F9; K5↔K5.a sub-trigger; K6↔K6). F3 S-* and F4 SM-* merged into the categorized registry. Step-4 implementation contract written. Machine-readable YAML sketch ready for Step-4 materialization. No new metrics introduced; no F3/F4 binding changes; no code; no experiments.
- **Step 4 still NOT allowed.** F6 (minimal factorial cells), F7 (re-assert freeze invariant in `STEP4_PREREGISTRATION.md`), F8 (compute estimate), F9 (venue plan + change-our-minds clause), plus Step-3.10 framing changes, all remain owed.

## Invariants honored
Paper 1 frozen outputs untouched (no read of `results/primary_full_v1/` in this step beyond what Step-3.13 already documented). No experiments; no code; no metric introduction; no F3/F4 binding changes. No calibration claim; no superiority claim. PoC license-gated and off. `[VERIFY]` items from F1/F2 still pending pre-manuscript.
