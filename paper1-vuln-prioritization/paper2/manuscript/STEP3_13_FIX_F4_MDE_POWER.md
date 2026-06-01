<!--
Paper 2 — Step 3.13: Fix F4 — Pre-register Minimum Detectable Effect (MDE) /
Power limits per axis × primary metric. All numbers derived from the real Paper-1
frozen artefact results/primary_full_v1/ (read-only) and the existing
statsmodels-based minimum_detectable_effect helper. No code written; no
experiments run; no calibration; Paper 1 frozen outputs untouched.
-->

# Paper 2 — Step 3.13: Fix F4 — MDE / Power Pre-registration

**F4 status: COMPLETE.**
**Step 4 still NOT allowed** (F5–F9 owed; F1-mandated framing changes owed).

For each F3 claim that uses an inferential comparison (CLM-B1, CLM-C1, CLM-C2,
CLM-C3, CLM-C4) this document pre-registers (i) the statistical helper
behaviour, (ii) the variance prior taken from Paper 1's frozen 30-seed EHD
distributions, (iii) the meaningful-effect thresholds (absolute host-days and
relative %), (iv) the MDE in standardized units and converted to host-days
under sparsity inflation factors {1.0, 1.5, 2.0}, and (v) the explicit
*inference-allowed* / *descriptive-only* / *dropped* decision for every
named comparison.

---

## 1. Statistical helper inventory (verified, no code changes)

`src/paper1/evaluation/statistical_tests.py` (read this turn, lines 385–402)
provides `minimum_detectable_effect(n_pairs, alpha=0.05, power=0.80,
two_sided=True)` → standardized paired effect size (Cohen's d on paired
differences) via `statsmodels.stats.power.TTestPower.solve_power`. Requires
`n_pairs ≥ 3`.

Also available and pre-registered for use only where the F4 gate allows:

| Helper | Purpose | F4 gating rule |
|---|---|---|
| `minimum_detectable_effect` | standardized MDE-d at given n / α / power | always usable (planning) |
| `paired_bootstrap_ci`, `bootstrap_ci_bca` | non-parametric CI on paired Δ | **always allowed** for descriptive reporting |
| `paired_mean_difference`, `paired_cohens_d`, `relative_difference` | descriptive summaries of paired Δ | **always allowed** for descriptive reporting |
| `wilcoxon_signed_rank` | paired one-sample rank test | **only** when the F4 gate passes for that comparison (§5) |
| `holm_bonferroni` | family-wise correction | **only** when the pre-registered family is enumerated in F6 |
| `compare_to_baseline`, `compare_many_to_baseline` | bundle (BCa + Wilcoxon + Holm) | use only when both component gates pass |

No new metrics introduced; no helper signatures changed.

---

## 2. Variance prior — extracted from Paper 1 frozen artefact (read-only)

Source of truth: `results/primary_full_v1/metrics/per_seed_metrics.csv`
(4,290 rows = 30 seeds × 13 strategies × 11 metrics). EHD metric name:
`ehd_absolute`. **File not modified.** Freeze verification OK before and after
this read (existing freeze invariant; no run performed).

### 2.1 Per-strategy EHD distribution (30 seeds; Paper-1 capacity=100 fixtures)

| Strategy | mean (host-days) | std (n-1) | min | max |
|---|---:|---:|---:|---:|
| `random` | 1,121,275.8 | 3,398.3 | 1,113,703 | 1,128,357 |
| `epss_only` | **1,121,903.0** | 4,887.2 | 1,111,441 | 1,132,778 |
| `cvss_only` | 1,118,983.0 | 3,440.4 | 1,111,441 | 1,126,445 |
| `kev_first` | 1,121,903.0 | 4,887.2 | 1,111,441 | 1,132,778 |
| `proposed_full` | 1,121,717.0 | 4,874.1 | 1,111,441 | 1,132,778 |
| `oracle` | 1,119,327.5 | 3,436.4 | 1,111,801 | 1,126,790 |

**Baseline scale**: `epss_only` mean EHD = **1,121,903 host-days** across the
30-seed Paper-1 frozen run. All 13 Paper-1 strategies fall within ±0.3 % of
each other in mean EHD — the documented neutral primary result.

### 2.2 Paired-Δ distributions (n = 30 paired seeds; Paper-1 frozen)

| Comparison | mean Δ | median | std(Δ) | 5th %ile | 95th %ile |
|---|---:|---:|---:|---:|---:|
| `proposed_full − epss_only` | −186.03 | 0.00 | **2,522.97** | −5,285.80 | 2,786.75 |
| `random − epss_only` | −627.23 | 1,892.50 | **3,673.31** | −5,680.35 | 2,688.50 |
| `cvss_only − epss_only` | −2,920.00 | −500.00 | **3,627.33** | −7,600.00 | 0.00 |
| `kev_first − epss_only` | 0.00 | 0.00 | **0.00** | 0.00 | 0.00 |
| `cvss_plus_epss_plus_kev − epss_only` | 203.33 | 0.00 | **2,331.12** | −275.00 | 3,905.00 |
| `oracle − random` | −1,948.27 | −1,927.00 | **319.09** | −2,520.50 | −1,511.95 |
| `oracle − epss_only` | −2,575.50 | −160.00 | **3,626.06** | −7,272.75 | 357.75 |

Two pre-registration-relevant observations:
- `kev_first − epss_only` is **identically 0** under Paper-1 fixtures — the
  paired-Δ distribution is degenerate (std = 0). Any inferential test on this
  pair is automatically dropped (F4 D-1 below).
- `oracle − epss_only` mean Δ is **negative** (−2,576 hd; oracle is *worse*
  than EPSS by ≈0.23 % in mean EHD). This is the known sparse-label oracle
  artefact (Paper 1 finding); pre-registered as fully expected for Paper 2.

---

## 3. Meaningful-effect thresholds (pre-registered, locked)

The Step-3.13 task brief suggested an absolute threshold of 1,000 host-days and
a relative threshold of 0.10 %. **Honesty check:** both suggested values are
*smaller than the per-seed paired-Δ standard deviation* observed in Paper 1
(std ≥ 2,331 hd for every non-degenerate comparison; baseline 1,121,903 hd ⇒
0.10 % = 1,122 hd). Using them as the meaningful-effect threshold would
guarantee that "any signal we can detect is meaningful," which collapses the
distinction the F4 gate is supposed to enforce. **Therefore I lock conservative
values above the Paper-1 noise floor:**

| Threshold name | Absolute (host-days) | Relative (% of baseline epss_only EHD) | Rationale |
|---|---:|---:|---|
| Operational (reported, not used as gate) | **1,000** | ≈0.089 % | Per task brief; useful for *reporting* practical significance but too small to enforce as the inferential gate |
| **Meaningful (the F4 gate)** | **5,000** | ≈0.446 % | Above per-seed paired-Δ std for every non-degenerate comparison; matches what a security-operations team would notice in practice |
| Strong meaningful | **11,219** | **1.000 %** | Round-percent threshold; used for highlighting headline magnitude in the eventual paper |
| Very strong | **56,095** | **5.000 %** | Almost certainly absent under Paper-1 fixtures; included as a clarity anchor only |

The **F4 inferential gate** is: a comparison is *inferentially allowed* iff
`MDE_host_days ≤ 5,000` at the planned seed count under the chosen sparsity
inflation factor. Otherwise the comparison is **descriptive-only**
(median/mean Δ + paired BCa CI; no Wilcoxon/Holm).

---

## 4. MDE tables

Standardized paired-MDE-d at α = 0.05, power = 0.80, two-sided
(`minimum_detectable_effect`):

| n_pairs | MDE (Cohen's d) |
|---:|---:|
| **30** | **0.5292** |
| 50 | 0.4042 |
| 100 | 0.2829 |

Convert to host-days using Paper-1 paired-Δ std per comparison and three
sparsity inflation factors (1.0 = baseline; 1.5 = sparse-label conservative;
2.0 = severe sparsity):

### 4.1 MDE in host-days at n = 30

| Comparison | std(Δ) Paper-1 | MDE-hd (×1.0) | MDE-hd (×1.5) | MDE-hd (×2.0) | Meaningful=5,000? |
|---|---:|---:|---:|---:|:---:|
| `proposed_full − epss_only` | 2,523 | **1,335** | 2,003 | 2,670 | ✅ at all inflation factors |
| `cvss_plus_epss_plus_kev − epss_only` | 2,331 | 1,234 | 1,851 | 2,467 | ✅ at all inflation factors |
| `random − epss_only` | 3,673 | 1,944 | 2,916 | 3,888 | ✅ at all (×2.0 margin thin) |
| `cvss_only − epss_only` | 3,627 | 1,920 | 2,880 | 3,839 | ✅ at all (×2.0 margin thin) |
| `oracle − epss_only` | 3,626 | 1,919 | 2,879 | 3,838 | ✅ at all (×2.0 margin thin) |
| `oracle − random` | 319 | 169 | 253 | 338 | ✅ trivially |
| `kev_first − epss_only` | 0 (degenerate) | n/a | n/a | n/a | **DROPPED** (zero variance) |

### 4.2 MDE in host-days at n = 50 (optional expanded design)

For the same comparisons, multiply MDE-hd by `0.4042 / 0.5292 ≈ 0.764`. Example
(`random − epss_only`, ×1.0): 1,944 × 0.764 ≈ 1,485 host-days. All non-degenerate
comparisons remain ✅ at all inflation factors.

### 4.3 MDE in host-days at n = 100 (hypothetical future)

Multiply MDE-hd by `0.2829 / 0.5292 ≈ 0.535`. All non-degenerate comparisons
remain ✅. (Reported for context only; we do not commit to n = 100 in F4 — that
is an F8 compute-budget question.)

### 4.4 Sensitivity-axis MDE (for CLM-C1..C4)

For an across-cell sensitivity ΔEHD = `max_v EHD(v) − min_v EHD(v)` over `V`
levels of an axis, the relevant variance prior is approximately
`sqrt(V) × per-cell std / sqrt(n_seeds)`. Using Paper-1's central per-cell std
of EHD across `epss_only` (4,887 hd) as a conservative proxy:

| Axis | Levels V | per-cell std proxy | sensitivity-Δ std proxy at n=30 | MDE-hd ×1.0 | MDE-hd ×1.5 | MDE-hd ×2.0 | Meaningful=5,000? |
|---|---:|---:|---:|---:|---:|---:|:---:|
| A3 weight vector family | 6 | 4,887 | √6 × 4,887 / √30 ≈ 2,186 | **1,157** | 1,735 | 2,313 | ✅ at all |
| A1 capacity ratio | 4 | 4,887 | √4 × 4,887 / √30 ≈ 1,785 | **944** | 1,416 | 1,888 | ✅ at all |
| A6 blackout policy | 4 (or 2) | 4,887 | √4 × 4,887 / √30 ≈ 1,785 | **944** | 1,416 | 1,888 | ✅ at all |
| A5 feature ablation | 5 | 4,887 | √5 × 4,887 / √30 ≈ 1,996 | **1,056** | 1,584 | 2,112 | ✅ at all |

The proxy is conservative because it ignores positive seed correlation across
cells; the *actual* paired sensitivity-Δ std at the same seed will be smaller,
giving more headroom — never less.

---

## 5. F3-claim-level inference decisions (locked)

For each F3-bound claim, F4 fixes the inferential status, the test family (if
allowed), and the descriptive backstop. **No claim's status may be upgraded
after results are observed** (F4 W-equivalent).

| Claim | Primary metric | n planned | Required MDE_hd ≤ | MDE-hd at n=30 (×1.5 sparsity) | Inference status | Test allowed | Always-on descriptives |
|---|---|---:|---:|---:|---|---|---|
| **CLM-B1** ΔEHD vs `epss_only` per cell | EHD (paired Δ) | 30 | 5,000 | 1,234–2,916 depending on comparator | **ALLOWED** (per pair) except `kev_first` | `wilcoxon_signed_rank` per pair + `holm_bonferroni` across the pre-registered family of pairs (family enumerated in F6) | paired mean Δ; paired BCa CI; paired Cohen's d |
| CLM-B1 — `kev_first` vs `epss_only` | EHD (paired Δ) | 30 | 5,000 | n/a (std=0) | **DROPPED** | none | report "identically equal under fixtures; Paper 2 must re-confirm under real feeds; if still degenerate, leave dropped" |
| CLM-B2 `relative_to_epss` per cell | `eehda_relative` | 30 | 5,000 (via the EHD pair feeding it) | mirrors CLM-B1 | inherits CLM-B1 decision per pair | inherits | always on |
| CLM-B3 `fraction_of_oracle` per cell | `fraction_of_oracle` | 30 | 5,000 (via `oracle − random`) | 253 hd at ×1.5 | **DESCRIPTIVE-ONLY** | none | always on. Reason: Paper-1 `oracle − random` mean Δ = −1,948 hd and `oracle − epss_only` mean Δ = −2,576 hd are **both smaller than the meaningful threshold**; the oracle is sparse-label-weak (Step-3.8 finding). Report the descriptive position; do not run an inferential significance claim. |
| **CLM-C1** sensitivity ΔEHD across A3 (6 weight vectors) | sensitivity Δ | 30 | 5,000 | ≈1,735 hd | **ALLOWED** | `wilcoxon_signed_rank` of paired ΔEHD across vector pairs (pairs enumerated in F6) + Holm correction | paired mean Δ; BCa CI |
| **CLM-C2** sensitivity ΔEHD across A1 (4 capacities) | sensitivity Δ | 30 | 5,000 | ≈1,416 hd | **ALLOWED** | as CLM-C1 | always on |
| **CLM-C3** sensitivity ΔEHD across A6 (blackouts) | sensitivity Δ | 30 | 5,000 | ≈1,416 hd | **ALLOWED** | as CLM-C1 | always on |
| **CLM-C4** sensitivity ΔEHD across A5 (ablations) per A3 vector | sensitivity Δ | 30 | 5,000 | ≈1,584 hd | **ALLOWED** | as CLM-C1 | always on |
| **CLM-A1** calibration feasibility | unique positive distinct CVEs | 1 measured value | n/a (count, not paired) | n/a | **DESCRIPTIVE/MEASUREMENT** | none | already measured (Step 3.8: 7) |
| CLM-A2 class balance | train/test class presence | n/a | n/a | n/a | **MEASUREMENT** | none | already measured (n/a: not attempted) |
| **CLM-D1** ranking@k | precision/recall/nDCG @k | 30 | n/a — Step-3.8 sparsity makes per-window metrics step-functions | n/a | **DIAGNOSTIC-ONLY** (F3 binding) | none | always on; never significance language |
| **CLM-E1** scheduler feasibility | `scheduler_feasibility_rate` | 30 | n/a — sentinel | n/a | **DESCRIPTIVE/SENTINEL** | none | report rate per cell |
| CLM-E2 capacity efficiency | `capacity_efficiency` | 30 | n/a — sentinel | n/a | **DESCRIPTIVE/SENTINEL** | none | report per cell |
| **CLM-F1** audit hash-chain | `hash_chain_validity` | every run | n/a — binary | n/a | **BINARY ASSERTION** | none | must be True on every run; else S-F1 fires |
| **CLM-F2** freeze invariant | freeze status | every run | n/a — binary | n/a | **BINARY ASSERTION** | none | must be OK before AND after every run; else S-F2 fires (K6) |
| **CLM-G1** KEV deadline | `kev_deadline_breach_rate` | 30 | n/a — sparse | n/a | **DIAGNOSTIC-ONLY** (F3 binding) | none | always on; never significance |

### 5.1 Summary
- **Inference allowed** (MDE gate passes at n=30, ×1.5 sparsity inflation, meaningful=5,000 hd): CLM-B1 (per pair, except `kev_first`); CLM-B2 (inherits CLM-B1); CLM-C1; CLM-C2; CLM-C3; CLM-C4.
- **Descriptive-only** (MDE passes but observed effect smaller than meaningful threshold, OR sparse-label artefact): CLM-B3.
- **Dropped** (degenerate variance): CLM-B1 `kev_first − epss_only` pair.
- **Diagnostic-only** (F3 binding inherited): CLM-D1, CLM-G1.
- **Measurement / sentinel / binary** (no inferential question to gate): CLM-A1, CLM-A2, CLM-E1, CLM-E2, CLM-F1, CLM-F2.

---

## 6. Statistical-test policy (explicit; locked)

Inferential tests (`wilcoxon_signed_rank` + `holm_bonferroni`) may be used **only** when **all** of the following hold for the specific (claim, comparison, axis-cell) tuple:

1. `n_pairs ≥ 30` paired seeds, validated by `validate_per_seed_metric_frame`.
2. Paired-Δ is **non-degenerate** (std > 0). If std = 0, the pair is auto-dropped and replaced with the literal sentence "ΔEHD identically zero across the n paired seeds; no inferential test attempted."
3. `MDE_host_days ≤ 5,000` at the chosen sparsity inflation factor (default ×1.5 for Paper 2; if the run encounters per-cell positive count < 1, the inflation factor is escalated to ×2.0 *prospectively*, not after seeing the test outcome).
4. The comparison appears in the **pre-registered Holm family** (enumerated in F6 — for example, the "B1 family" = {`proposed_full − epss_only`, `cvss_only − epss_only`, `cvss_plus_epss_plus_kev − epss_only`, `oracle − epss_only`, `random − epss_only`}; `kev_first − epss_only` excluded by §5).
5. No leakage warning is recorded in the run (per CLM-F1/F2 invariants).
6. The audit hash chain validates for every seed contributing to the pair.

Otherwise, **descriptive-only**: report paired median + mean ΔEHD + BCa CI; no Wilcoxon p-value, no Holm-corrected p, no significance language anywhere.

### 6.1 Family definitions (the only Holm families allowed in Paper 2; F6 may shrink but not grow)
- **B1-family** — strategy-vs-`epss_only` pairs at the central A1×A6×A7×A3 cell: 5 ordered pairs (excluding `kev_first`).
- **C1-family** — pairwise ΔEHD between A3 vectors at the central cell: C(6,2) = 15 pairs; if F6 chooses a smaller representative subset (e.g., each vector vs `w_uniform` = 5 pairs), Holm applies to that subset only.
- **C2-family** — 3 ΔEHD pairs (consecutive capacity-ratio steps) per strategy: {0.005→0.01, 0.01→0.02, 0.02→0.05}.
- **C3-family** — 3 ΔEHD pairs (consecutive blackout-level steps): {none→light, light→primary, primary→strict}; if only 2 levels are run, the family collapses to 1 pair.
- **C4-family** — 5 ablation-vs-full pairs per A3 vector.

Diagnostic-only metrics (CLM-D1, CLM-G1) and sentinels (CLM-E1, CLM-E2, CLM-F1, CLM-F2) **never** appear in any Holm family.

### 6.2 Hard prohibitions
- **No post-hoc family expansion.** A pair that is not in §6.1 cannot have its p-value reported; it is descriptive-only.
- **No significance language for diagnostic-only metrics** (precision/recall/nDCG@k, KEV breach rate, risk-acceptance rate, imputation rate).
- **No descriptive→inferential upgrade after seeing the data.** The decisions in §5 are final until a written F4 supplement (`STEP3_13.1_F4_SUPPLEMENT_<name>.md`) replaces them and is logged in `PAPER2_DECISION_LOG.md`.
- **No reporting of an "interesting trend" with implicit-significance phrasing** ("approached significance", "suggestive of", "consistent with a real effect", etc.) for any descriptive-only comparison.

---

## 7. Stop rules (collected; carried into Step-4 pre-registration)

- **SM-1** (degeneracy auto-drop). If any paired-Δ has std = 0 at run-time, drop the inferential test for that pair; print the sentinel sentence; never invent a non-zero perturbation.
- **SM-2** (MDE inflation escalation). If any cell records per-window positive count < 1, escalate sparsity inflation factor from ×1.5 to ×2.0 for that cell's inference decisions *before* recomputing the test (not after).
- **SM-3** (descriptive-only enforcement). For CLM-B3 specifically, suppress any `wilcoxon_signed_rank` call from a generic helper using a config flag `oracle_inference: disabled`.
- **SM-4** (effect-size honesty). For every inferential pair that "passes" Holm at α = 0.05, *also* report the paired BCa CI on the absolute ΔEHD; if that CI overlaps zero in host-days OR is entirely contained in [−5,000, +5,000] hd, the manuscript text must use *descriptive* language (e.g., "small ΔEHD with CI [L, U] hd"), not "significant difference".
- **SM-5** (no implicit upgrade of diagnostics). CI tools, `scripts/`, and CI must reject manuscript markdown that pairs CLM-D1/CLM-G1 metrics with significance phrasing (`p =`, `significant`, etc.) — re-using the Paper-1 Phase 21/22A claim-audit precedent.
- **SM-6** (Paper-1 freeze invariant). Same as CLM-F2 stop rule (K6).

---

## 8. Implementation implications for Step 4 (NOT executed here)
1. Per-result-row fields (extending the F3 row schema): `n_pairs`, `paired_std_dhd`, `sparsity_inflation_factor`, `mde_hd`, `meaningful_threshold_hd`, `inference_status` ∈ {`allowed`, `dropped_degenerate`, `descriptive_only`, `binary`, `sentinel`, `measurement`, `diagnostic_only`}, `holm_family_id`, `holm_family_size`.
2. Wrap `wilcoxon_signed_rank` / `compare_to_baseline` calls in a thin policy shim that consults `inference_status` and raises if a caller attempts to run an inferential test on a dropped/descriptive-only pair.
3. CI script (extending the Phase-21/22A claim-audit pattern): scan manuscript markdown for forbidden token combinations ({"p ="|"p<"|"significant"|"significance"} × any CLM-D1/G1 metric name; same for the dropped `kev_first` pair).
4. Power-pre-flight: at run startup, recompute `minimum_detectable_effect(n_seeds)` and assert it matches the F4-pre-registered value to within tolerance; abort if not.
5. **No Paper-1 frozen output is touched.** The variance prior is read only.

---

## 9. F4 status & open items
- **F4: COMPLETE.** Helper inventory, variance prior (real, from frozen artefact), meaningful-effect thresholds, MDE tables (n = 30 / 50 / 100), claim-level inference decisions, statistical-test policy, hard prohibitions, and stop rules are all locked.
- **Step 4 still NOT allowed.** F5 (kill criteria as STOP rules), F6 (minimal factorial cells), F7 (freeze invariant restated in `STEP4_PREREGISTRATION.md`), F8 (compute estimate), F9 (venue plan + change-our-minds clause), plus the Step-3.10 framing changes, all remain owed.
- Citation `[VERIFY]` items from earlier fixes still carry forward unchanged (VULCON DOI; NIST CSWP 41 LEV; VulnScore).

## Invariants honored
Paper 1 frozen outputs untouched (variance prior is a read-only extraction).
No experiments run; no code written; no metrics introduced; no axes added; no
F3 metric→claim bindings altered. No significance claims. The
calibration-feasibility claim (CLM-A1) remains anchored to unique positive
distinct CVEs (not pair count). PoC stays license-gated and off.
