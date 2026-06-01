<!--
Paper 2 — Step 3.15: Fix F6 — Enumerate the Minimal Factorial Cells.
Locks the primary + sensitivity + ablation cell set, plus a fallback table and
the explicit list of deferred cells. Source-of-truth files live alongside this
report:
  paper2/design/STEP3_15_MINIMAL_FACTORIAL_CELLS.csv
  paper2/design/STEP3_15_MINIMAL_FACTORIAL_CELLS.yaml
No new metrics, no new axes, no F2/F3/F4/F5 changes; no experiments run; Paper 1
frozen outputs untouched.
-->

# Paper 2 — Step 3.15: Fix F6 — Minimal Factorial Cell Enumeration

**F6 status: COMPLETE.**
**Step 4 still NOT allowed** (F7, F8, F9 owed; F1-mandated framing changes owed).

This document fixes the **exact** set of runnable cells for Paper 2. The cell
enumeration is materialized as a CSV and a YAML companion so Step-4 can load it
verbatim. No cell may be added, dropped, or re-parameterized post-hoc; any
change requires a written `STEP3_15.x_*.md` supplement and a new decision-log
row.

---

## 1. Central / default design (locked)

| Setting | Value | Rationale |
|---|---|---|
| `n_seeds` | **30** | Same as Paper 1; F4 MDE table confirms this seed count clears the meaningful threshold (5,000 hd) for every non-degenerate CLM-B1 / CLM-C* comparison at ×1.0–×2.0 sparsity inflation |
| `label_source` | `label_a_kev_only` | F3 CLM-A1 / CLM-B1 binding; PoC labels remain license-gated and OFF |
| `epss_era` | `v3` (2023-03-07 .. 2025-03-16) | A8 held fixed per Step 3.9; v4 deferred (model-version boundary) |
| `catalog_strictness` | `cpe_exact_existing31` | A9 held fixed per Step 3.9; fuzzy/manual matching deferred |
| `blackout_policy` | `primary` (central) | Step-3.15 task brief; central for CLM-B1/B2/B3 cells |
| `approver_policy` | `A` (central) | Step-3.15 task brief; approver-B sweep deferred |
| `capacity_ratio` | `0.01` (central) | Step-3.15 task brief; full capacity sweep done as secondary table |
| `t0_window_set` | `monthly_18_2023_09_to_2025_02` | Same 18 monthly windows already used in Step 3.8 (data already cached) |
| `paper1_freeze_invariant` | must hold before AND after every run | K6 (F5) |

---

## 2. Strategies in scope (locked)

**Baselines** (use Paper 1's existing strategy implementations as-is):
`random`, `cvss_only`, `epss_only`, `kev_first`, `cvss_x_epss`,
`cvss_plus_epss_plus_kev`.

**Fixed-prior family** `proposed_fixed_prior`, parameterised by the F2 weight
vectors (Step 3.11):
`w_uniform`, `w_paper1_placeholder`, `w_epss_dominant`, `w_cvss_dominant`,
`w_kev_dominant`, `w_context_dominant`.

**Forbidden**: any calibrated / learned / GBT / LightGBM / DRL comparator. K1
(F5) is already triggered (Step 3.8 measured 7 unique positive CVEs < 20);
introducing a learned comparator in Paper 2 would directly violate K1's
forbid-list (`learned_weight_claims`, `calibration_experiments`,
`register_calibrated_weights_calls`).

---

## 3. Primary cell set (12 cells; 30 seeds each)

Purpose: quantify ΔEHD vs `epss_only` across baseline strategies and the six
fixed-prior vectors at the central capacity / blackout / approver. The 12-cell
primary set **alone** also supports CLM-C1 (sensitivity ΔEHD across A3 weight
family) by paired analysis of the 6 `proposed_fixed_prior` cells — no extra
runs are required for CLM-C1.

| cell_id | strategy | weight_vector | claim_id | inference_family_id |
|---|---|---|---|---|
| `P-random-na` | `random` | n/a | CLM-B1 | B1 |
| `P-cvss_only-na` | `cvss_only` | n/a | CLM-B1 | B1 |
| `P-epss_only-na` | `epss_only` (**central baseline**) | n/a | CLM-B1 | B1 |
| `P-kev_first-na` | `kev_first` (SM-1 risk: Paper-1 paired-Δ = 0) | n/a | CLM-B1 | B1 |
| `P-cvss_x_epss-na` | `cvss_x_epss` | n/a | CLM-B1 | B1 |
| `P-cvss_plus_epss_plus_kev-na` | `cvss_plus_epss_plus_kev` | n/a | CLM-B1 | B1 |
| `P-proposed-w_uniform` | `proposed_fixed_prior` | `w_uniform` | CLM-B1 + CLM-C1 | B1 + C1 |
| `P-proposed-w_paper1_placeholder` | `proposed_fixed_prior` | `w_paper1_placeholder` | CLM-B1 + CLM-C1 | B1 + C1 |
| `P-proposed-w_epss_dominant` | `proposed_fixed_prior` | `w_epss_dominant` | CLM-B1 + CLM-C1 | B1 + C1 |
| `P-proposed-w_cvss_dominant` | `proposed_fixed_prior` | `w_cvss_dominant` | CLM-B1 + CLM-C1 | B1 + C1 |
| `P-proposed-w_kev_dominant` | `proposed_fixed_prior` | `w_kev_dominant` | CLM-B1 + CLM-C1 | B1 + C1 |
| `P-proposed-w_context_dominant` | `proposed_fixed_prior` | `w_context_dominant` | CLM-B1 + CLM-C1 | B1 + C1 |

**Primary cell count: 12; primary seed-runs at n = 30: 360.**

---

## 4. Capacity sensitivity (15 new runnable + 5 reused; 450 new seed-runs)

Purpose: CLM-C2 ΔEHD sensitivity across capacity ratios. Strategies (5,
reduced): `epss_only`, `cvss_plus_epss_plus_kev`,
`proposed_fixed_prior::w_paper1_placeholder`,
`proposed_fixed_prior::w_epss_dominant`,
`proposed_fixed_prior::w_context_dominant`. Capacities: **0.005, 0.01, 0.02, 0.05**.
The central `0.01` cells are **reused** from the primary table (5 reused
references in the CSV).

| cell_id pattern | new cells |
|---|---:|
| `CAP-<strategy>-cap0005` | 5 |
| `CAP-<strategy>-cap0020` | 5 |
| `CAP-<strategy>-cap0050` | 5 |
| `CAP-<strategy>-cap0010` | 0 new (5 reused from primary) |

**Capacity new runnable: 15; capacity reused: 5; new seed-runs at n=30: 450.**

---

## 5. Blackout sensitivity (9 new runnable + 3 reused; 270 new seed-runs)

Purpose: CLM-C3 ΔEHD sensitivity across blackout policies. Strategies (3,
reduced): `epss_only`, `proposed_fixed_prior::w_paper1_placeholder`,
`proposed_fixed_prior::w_context_dominant`. Levels: **none, light, primary,
strict**. Central `primary` cells reused from the primary table.

| cell_id pattern | new cells |
|---|---:|
| `BLK-<strategy>-none` | 3 |
| `BLK-<strategy>-light` | 3 |
| `BLK-<strategy>-strict` | 3 |
| `BLK-<strategy>-primary` | 0 new (3 reused from primary) |

**Blackout new runnable: 9; blackout reused: 3; new seed-runs at n=30: 270.**

---

## 6. Feature-ablation (12 new runnable + 2 reused; 360 new seed-runs)

Purpose: CLM-C4 ΔEHD sensitivity across feature ablations *per A3 vector*.
Weight vectors (2, reduced): `w_paper1_placeholder`, `w_context_dominant`.
Ablations: **`full`, `remove_E`, `remove_K`, `remove_S`, `remove_C`, `remove_X`,
`remove_R`** (using `ablate_weight` from `src/paper1/model/weights.py`).
`full` cells reused from primary.

| cell_id pattern | new cells |
|---|---:|
| `ABL-<vector>-remove_E` | 2 |
| `ABL-<vector>-remove_K` | 2 |
| `ABL-<vector>-remove_S` | 2 |
| `ABL-<vector>-remove_C` | 2 |
| `ABL-<vector>-remove_X` | 2 |
| `ABL-<vector>-remove_R` | 2 |
| `ABL-<vector>-full` | 0 new (2 reused from primary) |

**Ablation new runnable: 12; ablation reused: 2; new seed-runs at n=30: 360.**

---

## 7. Deferred cells (8 entries; **NOT** counted in planned run total)

Carried in the CSV / YAML with status `deferred` and a written rationale:

| cell_id | Deferred reason |
|---|---|
| `DEF-approver_B_sweep` | secondary approver-policy sweep; outside primary budget |
| `DEF-epss_v4_era` | A8 held fixed at v3; v4 = model-version boundary |
| `DEF-catalog_expansion` | deferred per Step 3.9 and Step 3.10; requires F1.x supplement and a new Step-3.8 probe |
| `DEF-poc_label_b` | license-gated; never redistributed; `PAPER1_ENABLE_POC_FETCH` must remain unset by default |
| `DEF-fuzzy_cpe_matching` | A9 held fixed at `cpe_exact`; fuzzy/manual matching deferred |
| `DEF-seeds_50_or_100` | F4 MDE table already gives n=50/100 numbers; runs deferred unless F8 budget grows |
| `DEF-all_pairwise_weight_comparisons` | **No extra runs needed**: the C(6,2)=15 pairwise CLM-C1 Holm family is supported by paired analysis of the 6 primary `proposed_fixed_prior` cells at no extra compute; the entry is kept explicit to record that fact |
| `DEF-gbt_or_learned_comparator` | **FORBIDDEN by K1**; cannot be re-enabled in Paper 2 without overriding K1 — would require a new pre-registration step |

Deferred cells are explicitly excluded from total planned run / seed counts.

---

## 8. Fallback table (used only if F8 proves the primary too expensive)

If F8 compute-budget analysis cannot afford the full 48 runnable cells × 30
seeds = 1,440 seed-runs, Paper 2 falls back to **one** of these reductions
(decided in F8, not here; F6 only locks the option set):

| Fallback option | Description | New runnable cells | New seed-runs at n=30 | Cost reduction |
|---|---|---:|---:|---|
| **F8-a** seed reduction | Same 48 cells, n=10 (or smallest n where F4 MDE-hd stays ≤ 5,000 with × 1.5 inflation) | 48 | 480 (or smaller) | linear |
| **F8-b** capacity-collapse | Drop capacity sweep to 2 levels {0.01, 0.05}: 5 × 1 = 5 new cells (10 reused) | 38 | 1,140 | −10 cells |
| **F8-c** blackout-collapse | Drop blackout sweep to 2 levels {primary, strict}: 3 × 1 = 3 new cells (6 reused) | 42 | 1,260 | −6 cells |
| **F8-d** ablation-collapse | Drop ablation set to `w_paper1_placeholder` only × 6 removes = 6 new cells (1 reused) | 42 | 1,260 | −6 cells |
| **F8-e** combined collapse | F8-b + F8-c + F8-d together | 26 | 780 | −22 cells |
| **F8-f** pilot+primary | Run primary (12) at n=30; defer all sensitivity tables to a follow-up | 12 | 360 | −36 cells |

F4 SM-2 stop rule still applies under any fallback: if per-window positives < 1
the sparsity-inflation factor escalates ×1.5 → ×2.0 *before* the test runs;
fallbacks must still clear MDE-hd ≤ 5,000 at the escalated factor or the
inferential test for that pair is dropped.

---

## 9. Planned cell-count summary

| Group | New runnable | Reused (refs to primary) |
|---|---:|---:|
| Primary | **12** | — |
| Capacity sensitivity | 15 | 5 |
| Blackout sensitivity | 9 | 3 |
| Feature ablation | 12 | 2 |
| **Total planned runnable cells** | **48** | **10** |
| Deferred | (8, not counted) | — |

**Total planned seed-runs at n = 30: 48 × 30 = 1,440.**

These counts are machine-checkable against the CSV: every row with
`run_status == planned` is a runnable seed-run × 30; every row with
`run_status == reused` references a primary cell via `reuse_of_cell_id`;
deferred rows carry `run_status == deferred`.

---

## 10. Runtime estimate (planning only; locked numbers come in F8)

Step 3.8 measured: full keyed multi-t0 probe took ≈14 min wall-clock for
acquisition (12/14 min once the API key was present) + the 18-window per-t0
pass over 110,224 NVD records × 500 hosts × 2,688 catalog-matched CVEs in a
single configuration. Paper 1's full 30-seed primary run took ≈18 min for 30
seeds × 13 strategies × 11 metrics (frozen artefact).

These are not directly comparable to a Paper-2 cell — Paper-2 cells run real
public-feed inputs (heavier per t0) but share the NVD universe / EPSS / KEV
data across cells and seeds. A defensible planning range, with substantial
shared computation:

| Implementation profile | Estimated wall-clock for 48 cells × 30 seeds |
|---|---|
| **Optimistic** (shared per-t0 pair-build & feature attach across cells; per-cell marginal cost is scoring + scheduling + EHD only; ~0.3 s per (cell, t0, seed)) | **≈8–12 hours** on a laptop |
| **Mid** (per-(seed, t0) re-builds; per-cell scoring/scheduler ~1 s × 18 t0 × 30 seeds × 48 cells) | **≈12–24 hours** |
| **Pessimistic** (no shared computation; per-cell × per-seed roughly mirrors Step-3.8 per-config cost) | **multi-day** |

**Compute-risk warning for F8:** without explicit shared-computation
engineering (NVD universe and per-t0 pair frames built ONCE per seed, then
re-used across all 48 cells), Paper 2 will not fit a single laptop day. F8 must
either (i) require shared-computation architecture in the Step-4 runner, or
(ii) choose one of the F6 §8 fallback options (most likely F8-a seed
reduction or F8-f pilot-then-primary). F6 itself does **not** decide the
runtime; it only enumerates the cells.

---

## 11. How F6 respects F2 / F3 / F4 / F5

- **F2 (weights, Step 3.11):** every `proposed_fixed_prior` cell uses one of the
  six locked vectors only; tags must carry `weight_family="fixed_prior_v1"`,
  `weight_source="design_prior"`, `weight_vector_name=<name>`, and the
  citation chain (W6). No vector is "tuned" or chosen post-hoc.
- **F3 (metric→claim binding, Step 3.12):** every cell carries `claim_id`
  and `inference_family_id`. CLM-D1 and CLM-G1 metrics
  (precision/recall/nDCG@k, KEV breach rate) are reported as `diagnostic_metrics`
  in every row but **never** as a primary metric; CI must scan markdown for
  significance phrasing near these metric names (F5 SM-5).
- **F4 (MDE / power, Step 3.13):** n=30 is honored. CLM-B3 fraction-of-oracle
  cells reuse the same row as their EHD parent cell; `SM-3 oracle_inference:
  disabled` is the runtime flag. CLM-B1 `kev_first` pair is **dropped** for
  inference (SM-1) unless Paper-2 reproduces a non-degenerate paired-Δ.
- **F5 (stop rules, Step 3.14):** the YAML companion lists the pre-flight,
  per-cell, per-comparison, post-run, and manuscript gates verbatim. **K1 and
  K3 are already TRIGGERED**: no calibration cells, no learned cells, and no
  headline ranking claim is supported by the enumeration above. K6 (Paper-1
  freeze) wraps every Paper-2 run regardless of which cell is being executed.

---

## 12. Implementation implications for Step 4 (NOT executed here)

1. **Load the YAML** verbatim at run start; refuse to launch any cell not
   present in `STEP3_15_MINIMAL_FACTORIAL_CELLS.yaml` (or its CSV companion).
2. **Per-row tagging** (extends the F3/F4/F5 row schema with):
   `cell_id`, `table_group`, `claim_id`, `inference_family_id`,
   `weight_vector`, `capacity_ratio`, `blackout_policy`, `approver_policy`,
   `label_source`, `epss_era`, `catalog_strictness`, `ablation`,
   `t0_window_set`, `reuse_of_cell_id`, `run_status`.
3. **Shared computation** across the 48 cells (per §10) is the recommended
   path; F8 will decide if it is required or if a fallback is taken.
4. **Reused cells** must not be re-executed: when the runner encounters
   `run_status == reused`, it must point downstream consumers to the primary
   cell's per-seed metric frame; tests must lock the per-seed values to the
   primary cell's hash so a future change to the primary cell flags the reuse
   chain as stale.
5. **Paper 1 freeze invariant** (K6 / S-F2) wraps every Paper-2 run, including
   reuse-only consumers. No exception.
6. **Manuscript CI** scans tables for cells outside the enumeration; any row
   whose `(strategy, weight_vector, capacity_ratio, blackout_policy,
   approver_policy, ablation, label_source, epss_era, catalog_strictness)`
   tuple is not in the YAML is a CI failure.

---

## 13. F6 status & open items
- **F6: COMPLETE.** Cell enumeration locked at:
  - `paper2/design/STEP3_15_MINIMAL_FACTORIAL_CELLS.csv`
  - `paper2/design/STEP3_15_MINIMAL_FACTORIAL_CELLS.yaml`
  Primary (12) + capacity (15) + blackout (9) + ablation (12) = **48 new
  runnable cells**; 10 reused-from-primary references; 8 explicitly deferred
  rows; **1,440 planned seed-runs at n = 30**. Runtime range
  ~8–24 h on a laptop assuming shared per-seed computation across cells;
  F8 will decide budget and (if necessary) which fallback option to take.
- **Step 4 still NOT allowed.** F7 (re-assert freeze invariant in
  `STEP4_PREREGISTRATION.md`), F8 (compute estimate + decision), F9 (venue
  plan + change-our-minds clause), and the Step-3.10 framing changes still
  owed.

## Invariants honored
Paper 1 frozen outputs untouched. No experiments run; no code written; no new
metrics or axes introduced; no F2/F3/F4/F5 changes. No calibration / no
superiority / no learned-comparator cells (K1). PoC license-gated and off
(K5.a applies). The CLM-A1 sample size remains `unique_positive_distinct_cves`
(not pair count, not event sum).
