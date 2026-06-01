<!--
Paper 2 — Step 3.9: Research Validation Report for Pivot Option A.
Robustness/sensitivity-only Paper 2 using real public-feed features (NVD/EPSS/KEV) and
FIXED weights, on a real-feed extension of Paper 1's frozen synthetic-fleet benchmark.
Grounded in real Step 3.8 measurements; no new experiments; no fabricated citations
([VERIFY] flags retained); skeptical assessment.
-->

# Paper 2 — Step 3.9: Pivot Decision and Research Validation Report

## 1. Final pivot decision
- **The calibration paper is infeasible under the current public-feed + 31-product
  catalog setup.** Empirical evidence: full keyed multi-t0 run (Step 3.8) over the
  EPSS v3 era produced **7 unique positive distinct Label-A CVEs** out of 2,688
  catalog-matched CVEs across 18 monthly windows. 7 < 20 fires the literal PIVOT
  rule and the "Label A too sparse" rule simultaneously. Calibration was correctly
  not attempted.
- **Recommended pivot: Option A — robustness/sensitivity-only Paper 2** using real
  public-feed features and **fixed weights** (no calibration claim, no superiority
  claim) on a real-feed extension of Paper 1's frozen synthetic-fleet benchmark.
- **Catalog expansion is deferred, not pursued now.** Per the user's standing
  instruction; also consistent with "do not ask the gate question twice" hygiene.
  Expansion is recorded as a *future-work option*, not a Step-3.9 action.

## 2. Refined research question
> **"How stable are context-aware vulnerability-prioritization outcomes when
> public exploit labels are sparse and operational constraints vary?"**

Reframed sub-questions (all answerable with **fixed** weights and the measured
public-feed labels):
- Q1 (label-sparsity sensitivity): How much do ranking/scheduler outcomes change
  between Label-A-only and label-augmented variants when positives are sparse?
- Q2 (operational-constraint sensitivity): How do capacity, blackout, and
  approver-policy variations move EHD / capacity-efficiency / scheduler-feasibility
  for the *same* fixed-weight strategy?
- Q3 (feature-ablation sensitivity): Which feature contributes most to ranking
  stability under fixed weights when only 7 KEV-positive CVEs exist?
- Q4 (baseline gap): Does any fixed-weight context-aware strategy show a
  *consistent* (not necessarily statistically significant) EHD gap vs.
  EPSS-only / CVSS-only / random across the sensitivity axes?

None of these require calibration; all are statable as **sensitivity / robustness**
claims rather than superiority claims.

## 3. Why this is publishable despite failed calibration
1. **The negative feasibility result is itself informative.** Publishing the measured
   sparsity (7 / 2,688 / 18 monthly windows; KEV addition rate ≈ 0.014 % per
   (CVE, window) pair) gives the community a concrete data point on when
   per-feature calibration of vulnerability-prioritization weights is *not*
   statistically defensible on public feeds alone.
2. **Public-feed label sparsity is an operational reality.** Most defender teams do
   not have private exploit telemetry. A study that characterises behaviour under
   the labels they *do* have is directly relevant.
3. **Robustness under sparse labels is undertheorised.** Most prioritization papers
   either assume large labelled corpora or fold sparsity into a single robustness
   figure. A dedicated multi-axis sensitivity sweep with explicit MDE/power
   accounting is a small but real methodological contribution. (Prior-art
   verification against the same area still needed: `[VERIFY]` against the
   "robustness of vulnerability prioritization" and "EPSS sensitivity" literatures
   before Step 4.)
4. **Avoids p-hacking.** By committing in advance to fixed weights and to
   sensitivity-only claims, the paper sidesteps the standard failure mode of
   calibration on too few positives (overfit weights presented as a result).
5. **Reusable artefact.** The hardened public-feed acquisition pipeline + multi-t0
   probe + decision-gate machinery (Step-3.6 / 3.7 / 3.8) is a standalone
   reproducibility contribution independent of the headline result.

**Honest caveat.** "Negative-result publishable" is a real category but a *narrower*
audience than a positive-finding paper. Top-tier security venues `[VERIFY]`
historically reject pure-sensitivity papers without a methodological hook; the hook
here must be *"failure-aware calibration gate + sparsity-honest sensitivity"*, not
*"better prioritization."*

## 4. How this differs from Paper 1
| Dimension | Paper 1 (frozen) | Paper 2 pivot |
|---|---|---|
| Inputs | Toy synthetic fixtures | **Real NVD / EPSS / KEV public feeds** + same synthetic fleet generator |
| Weights | Placeholder | **Fixed** (placeholder from Paper 1 *or* literature-prior; published-weight source must be `[VERIFY]`-checked before locking) |
| Primary claim | Benchmark/framework reproducibility; neutral primary result | **Sensitivity / robustness** of fixed-weight prioritization under sparse real labels |
| Runs | One primary frozen run (30 seeds × 13 strategies × 11 metrics) | **Sensitivity sweeps** across capacity / blackout / approver / feature-ablation / label-source axes, on a **read-only extension** of Paper 1's frozen benchmark |
| Calibration | None claimed (placeholder weights documented) | **Explicitly not attempted**; documented infeasibility (Step 3.8) is part of the contribution |
| Frozen outputs touched | All produced by Paper 1 | **None** — Paper 1's `results/primary_full_v1/` stays content-addressed-frozen |

The Paper 1 ↔ Paper 2 boundary is therefore: same code skeleton + same fleet
generator + new public-feed feature attach + new sensitivity sweeps, with Paper 1's
frozen primary result untouched and referenced as the synthetic-only control.

## 5. Proposed contribution list (5 items; tightly bounded; no superiority claim)
- **C1. Empirical characterisation of public-feed label sparsity** for a 31-product
  public-sector-typical catalog: 2,688 catalog-matched CVEs, 7 unique Label-A
  positives across 18 monthly t0 windows in the EPSS v3 era (real, leakage-safe,
  Step-3.8 measured).
- **C2. Real-feed extension of Paper 1's frozen benchmark** — same scheduler /
  metric stack, real EPSS-as-of-t0 / KEV-as-of-t0 features, synthetic fleet retained
  for external-validity transparency.
- **C3. Multi-axis sensitivity sweep** of fixed-weight context-aware scoring under
  capacity, blackout, approver, feature-ablation, label-source, and catalog-match
  strictness variations — reported as deltas with bootstrap CIs.
- **C4. Failure-aware calibration-gate methodology**: the multi-t0 probe + decision
  rubric + Step-3.7/3.8/3.9 audit trail as a reusable pattern for deciding when *not*
  to calibrate on public feeds.
- **C5. Reproducible public-feed acquisition + freeze pipeline**: chunked / resumable
  / paced NVD client with per-chunk cache, multi-t0 aggregation with CVE-level
  dedup, content-addressed freeze (inherited from Paper 1).

No "proposed_full beats EPSS" claim; no calibration claim; no production-validation
claim; no real-employer-data claim.

## 6. Candidate experiment axes
All axes are evaluable with **fixed weights** and the existing Step-3.8 measured
public-feed inputs. No new full experiments are run at this step; this is the
*design space* for Step 4 pre-registration.

| Axis | Levels |
|---|---|
| Capacity ratio (per-week %) | 0.005, 0.01, 0.02, 0.05 |
| Strategy | random, cvss_only, epss_only, kev_first, cvss_x_epss, cvss_plus_epss_plus_kev, cve_max, cve_mean, cve_sum, proposed_full *(fixed weights)*, proposed_no_criticality, proposed_no_exposure, oracle (13 — same as Paper 1) |
| Label source | **Label A KEV-only (primary)**; optionally Label B local-PoC *(only if license-gated env is set; never redistribute)* |
| Feature ablation | drop C, drop X, drop R, drop K, drop E (each evaluated separately against full) |
| Blackout policy | none, light, primary, strict |
| Approver policy | A, B |
| EPSS era | v3 only (2023-03-07..2025-03-16); v4 explicitly out of scope (model-version change) |
| Catalog-match strictness | `cpe_exact` only; `cpe_fuzzy` or `manual` flagged as future work, not run here |

Total cells (full crossing) is large; Step 4 must downsize to a **pre-registered
factorial subset** (e.g., capacity × strategy × {one blackout level} × {one
approver}, with feature-ablation sweeps held at the central capacity/blackout/approver).
The Step-1 instruction to *not* run full Paper 2 experiments is honored here.

## 7. Metrics (kept honest about what each can and cannot say with 7 positives)
| Metric (from Paper 1's 11) | Use under sparse labels | Caveat |
|---|---|---|
| EHD / EEHDA (host-day harm) | **Primary** — depends on per-host criticality + KEV-as-of-t0 features, not only Label-A positives | Still meaningful with 7 positives |
| capacity_efficiency | **Primary** — depends on remediated set vs. capacity, not on positives | OK |
| scheduler_feasibility | **Primary** — operational constraint satisfaction | OK |
| `relative_to_epss` (proposed Paper-2 quantity) | **Secondary** — EHD-ratio of strategy to EPSS-only | OK; new derived metric, define formally |
| `fraction_of_oracle` (proposed) | **Secondary** — distance to upper bound | Oracle is weak with sparse positives — flag |
| precision_at_k, recall_at_k, ndcg_at_k | **Diagnostic only** | With 7 positives, per-window precision@k is a 0/1/2-step function; do not over-interpret |
| kev_breach_rate | **Diagnostic only** | Same sparsity problem |
| risk_acceptance_rate | OK | Operational rather than label-driven |
| rank_churn (proposed; cross-axis Kendall-τ of per-CVE ranks) | **Primary** — sensitivity itself | Independent of positives |
| audit_hash_chain_valid, audit_record_count, scheduled_count | Sanity / infra | Must be 100 % / non-zero |
| Sensitivity deltas (Δ EHD, Δ rank-churn) across axes | **Primary** — these *are* the paper | OK |

**Rule of the paper**: every primary claim must be a *delta* (sensitivity across an
axis) or an *operational* outcome (EHD, capacity, feasibility), never a per-window
label-positive recall.

## 8. Statistical design (sparsity-honest)
- **Paired seed comparisons** within each axis cell (same seed across strategies),
  reusing Paper 1's seed scheme for compatibility.
- **Bootstrap CIs (BCa)** on per-metric deltas; report CI width prominently, not
  just point estimates.
- **Wilcoxon signed-rank + Holm-Bonferroni** *only* on axes where pre-registered MDE
  power analysis shows the test can detect a meaningful effect; otherwise report
  descriptively.
- **MDE / power analysis pre-registered**: for each axis × metric, compute the
  minimum detectable effect at our seed count (≤30 per cell, matching Paper 1) and
  state it in the pre-registration. Where MDE > the effect we would consider
  meaningful, **drop the inferential test and report descriptives only**.
- **Do not over-interpret p-values.** Explicit clause: with the Step-3.8 positive
  count (7), any per-positive-recall test is severely under-powered; we do not
  draw inferential conclusions from such tests.
- **Multiple-comparison budget pre-declared.** All families enumerated in advance
  in the Step-4 pre-registration; corrections applied within family.

## 9. Feasibility assessment (uses Step-3.8 measured facts only)
| Item | Status |
|---|---|
| Public feeds acquirable end-to-end | **yes** — Step 3.8: 110,224 NVD records (11/11 chunks), 18/18 EPSS snapshots (17 ≥99.3% coverage, 1 graceful miss), KEV cumulative |
| Leakage-safe labels constructible | **yes** — Step 3.8: 0 leakage warnings; `(t0, t0+H]` enforced; KEV-as-of-t0 used only as feature K |
| Calibration of per-feature weights | **no** — 7 unique positives < 50 (well below) |
| Fixed-weight sensitivity sweeps | **yes** — all sweep axes are weight-independent or use already-defined fixed weights |
| Operational metrics (EHD, capacity, feasibility) | **yes** — independent of label positivity |
| Paper 1 frozen artefact reusable as control | **yes** — content-addressed freeze verified before/after every run |
| Rank-churn / cross-axis stability | **yes** — definable on the 2,688 catalog-matched CVEs, no positives needed |
| PoC/ExploitDB inclusion | **conditional** — only if `PAPER1_ENABLE_POC_FETCH=true`; never redistribute |
| Catalog expansion (deferred) | future work; not pursued in Paper 2 per Step 3.9 |

## 10. Risks (skeptical)
1. **Too few positive labels for any strong ranking claim.** 7 unique positives
   limits precision/recall/nDCG to anecdote-level; the paper must explicitly *not*
   rely on these.
2. **Oracle weakened by sparse positives.** "Fraction of oracle" loses meaning when
   the oracle itself is built from 7 events; report as diagnostic, not result.
3. **EPSS may dominate every operational metric.** If EHD / capacity_efficiency
   under fixed weights tracks EPSS within bootstrap noise, the paper's headline
   becomes *"EPSS-only is hard to beat with fixed context-aware weights at this
   sparsity"* — an honest but smaller-impact finding.
4. **Fixed weights may produce a null sensitivity result** (all strategies look
   indistinguishable). Acceptable as a sensitivity-paper finding only if the
   *sweep itself* shows interesting axis-dependent variation (capacity, blackout).
5. **Mostly-methodological result.** The contribution may end up as
   "we measured sparsity + designed a failure-aware gate" rather than a substantive
   security finding. Plan venue accordingly (workshop / methodology track).
6. **Synthetic fleet still limits external validity.** No real-host claim is
   possible; restate this as an explicit limitation, not a fixable flaw.
7. **Catalog-match quality.** A 2.8 % CPE→catalog match rate is real but
   non-trivially driven by the 31-product list; bias analysis required.
8. **No PoC / ExploitDB** by default → Label B unavailable in this sandbox.
   Document as bounded-scope, not as missing data.
9. **Frozen-weights provenance.** If we use Paper 1's *placeholder* weights, the
   paper must label them as placeholders, not "published weights." If we use a
   genuine literature weight set, citation needs `[VERIFY]` before Step 4 — there
   is no widely-accepted published prior for this exact 7-feature scheme, so the
   honest choice is **placeholder-as-fixed**, transparently documented.
10. **Reviewer pushback on "negative result"**: top-tier venues `[VERIFY]` often
    reject; aim for workshop / methodology track or a venue that explicitly accepts
    null-result / reproducibility submissions.

## 11. Kill criteria (pre-registered; trigger PIVOT-2 or Paper-3 alternative)
Pivot away from this Option-A paper (and consider Paper 3) if **any** of the
following is observed in pilot sensitivity sweeps *before* Step-4 full pre-registration:
- **K1.** Sensitivity sweeps produce **no measurable variation** (median ΔEHD < 5 %
  of EPSS-only EHD across **every** axis, with 95 % BCa CI overlapping 0).
- **K2.** Even sensitivity reporting is uninformative because the relevant per-cell
  variance is dominated by seed noise (CV_within > CV_across for every axis).
- **K3.** Public-feed CPE→catalog mapping is too noisy to define stable per-CVE
  pairs (e.g., > 30 % of catalog-matched CVEs change under minor catalog edits).
- **K4.** Results collapse into **"all strategies equivalent"** with no
  axis-dependent variation, no methodological insight beyond the sparsity figure
  itself, and the sparsity figure alone is insufficient for the chosen venue.
- **K5.** Any leakage warning fires in real-feed Label A construction at scale.
- **K6.** Paper 1's freeze verification fails at any point in Paper 2 work.

## 12. Go / no-go score (skeptical; explicit reasoning)
| Score | Value /10 | Reasoning |
|---|---:|---|
| Publishability | **5** | Negative-result + sensitivity is a real but narrow category. Workshop / methodology track realistic; top-tier venue `[VERIFY]` unlikely. Hook ("failure-aware calibration gate") is the leverage. |
| Novelty | **4** | Sensitivity-of-vuln-prioritization studies exist `[VERIFY]`. The failure-aware-gate angle + the public-feed sparsity measurement + the multi-t0 probe artefact are moderately fresh in combination. |
| EB1A value | **4** | Negative + methodological is harder to spin than a positive finding. Real value comes from (a) public-feed acquisition pipeline (b) decision-gate framework (c) reproducibility — none of which are dramatic claims. |
| Overall | — | **CONDITIONAL GO** to Step 4 with fixes (next subsection). Not GO (publishability is bounded). Not NO-GO (the artefact + sparsity finding are publishable and the Paper-1→Paper-2 path stays coherent). |

**Recommended decision: CONDITIONAL GO** to a pre-registered robustness/sensitivity-only
Step 4 with the fixes below. (A confident GO would require independent prior-art
verification — `[VERIFY]` for the sensitivity / EPSS-stability literature — before
locking the contribution claim.)

## 13. Recommended Step 4 (CONDITIONAL GO — fixes required before pre-registration)
The Step-4 pre-registration document must include:

**F1. Prior-art verification (blocking).** Execute a targeted web/library search for
prior public-feed vulnerability-prioritization sensitivity studies (Jacobs et al.
EPSS family `[VERIFY]`; Allodi/Massacci exploitation-prediction line `[VERIFY]`;
robustness-of-ranking literature in security `[VERIFY]`). Output: a kill-or-keep
note. If a paper already publishes the same sensitivity finding, PIVOT-2.

**F2. Lock fixed-weight source (blocking).** Either (i) reuse Paper 1's documented
placeholder weights *and label them placeholders in every table*, or (ii) adopt a
clearly-cited literature weight prior `[VERIFY]`. Do not paper-over the choice.

**F3. Pre-register the metric→claim mapping.** Each claim in the paper must cite
exactly one *primary* metric from §7 and bind to one *axis* from §6. No post-hoc
metric selection.

**F4. Pre-register MDE / power per axis** (§8). Drop inferential tests where MDE >
the meaningful-effect threshold; report descriptives only.

**F5. Pre-register kill criteria (§11) as STOP rules** during the pilot sweep, with
written acceptance/rejection thresholds for each Kn.

**F6. Define the *minimal* factorial.** Full crossing of §6 is too large; the
pre-registration must enumerate the specific cells to run (e.g., 13 strategies × 4
capacities × 1 blackout × 1 approver = 52 cells × 30 seeds = 1,560 runs as the
*primary* table; feature-ablation and blackout/approver sweeps held as secondary
tables at the central cell).

**F7. Paper 1 freeze invariant** must be re-asserted in the pre-registration: every
Paper-2 run begins and ends with `make verify-primary-freeze`; the audit trail must
include the freeze hash before and after.

**F8. Compute / wallclock estimate.** The Step-3.8 run took ~14 min for one
(fleet, seed, sweep-cell-equivalent) configuration; a 1,560-run primary table is
~5–10 days of compute on the current laptop. Either accept this, parallelise, or
shrink the factorial. Decide *in* pre-registration, not after.

**F9. Venue plan and "what would change our minds" clause.** Pre-register the
target venue tier (workshop/methodology) and the result patterns that would
invalidate publication intent.

**Once F1–F9 land in `paper2/manuscript/STEP4_PREREGISTRATION.md`, Step 4 is
*then* permitted to start. Until then, Step 4 remains NOT allowed.**

## Invariants honored (re-asserted)
- Paper 1 frozen outputs untouched (`results/primary_full_v1/`); `verify-primary-freeze`
  remains the gate on every Paper-2 run.
- No paper drafting in this step. No new full experiments. No calibration claim. No
  superiority claim. No catalog expansion. No PoC/ExploitDB use without the license
  gate. No fabricated citations (`[VERIFY]` retained on every literature claim).
- All numeric facts in this report come from Step-3.8 measured artefacts under
  `paper2/feasibility/probe_v2_multit0/`; nothing fabricated.
