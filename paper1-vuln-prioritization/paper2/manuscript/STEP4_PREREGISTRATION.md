<!--
Paper 2 — Step 4: Pre-Registration Document.
Locks the study before any implementation or experiment execution.
References F2–F9 (does NOT duplicate them). No experiments, no code, no
Paper 1 modification. Step 5 (runner implementation) not started.
-->

# Paper 2 — Step 4: Pre-Registration

## 1. Document status

| Attribute | Value |
|---|---|
| Document type | **Pre-registration** |
| Experiments run in this step | **None** |
| Code written in this step | **None** |
| Paper 1 frozen outputs modified | **None** (read-only verifications only) |
| Step 5 (runner implementation) | **Not started** |
| Step 6 (pilot launch) | **Not started** |
| Date locked | 2026-05-28 |
| Sole new artefact produced | this file |
| Decision-log row | `PAPER2_DECISION_LOG.md` Step 4 row (also added this turn) |

This document is the **immutable design contract** for the rest of Paper 2.
Any deviation requires a written `STEP4.x_SUPPLEMENT_<short_name>.md`
companion + a new row in `PAPER2_DECISION_LOG.md`. No deviation may be
applied silently.

---

## 2. Title

**Pre-registered title (Title #1, recommended by F9):**

> **"When Calibration Fails: A Failure-Aware Public-Feed Gate for Vulnerability Prioritization Under Sparse Exploit Labels"**

**Held alternates** (selectable at venue submission without a new fix; any
substantive subtitle change requires a Step-4.x supplement):

- #2 — "Sparse Exploit Labels and the Limits of Calibrated Vulnerability Prioritization"
- #3 — "A Failure-Aware Methodology for Vulnerability Prioritization Under Public-Feed Label Sparsity"

Authors / affiliations / contact are deferred to manuscript stage.

---

## 3. Abstract (pre-registration summary)

This pre-registration commits Paper 2 to study **when** per-feature
context-aware weight calibration on public-feed vulnerability-prioritization
labels is *not* statistically justified, and to characterise the behaviour of
**fixed-prior** strategies under public-feed label sparsity. We have already
empirically established (Step 3.8, with `NVD_API_KEY`) that on a public-sector-
typical 31-product catalog, the EPSS v3 era (2023-03-07 .. 2025-03-16) over
18 monthly t0 windows yields:

- 110,224 real NVD records,
- **2,688 catalog-matched CVEs**,
- and **only 7 unique Label-A positive CVEs** (KEV addition in `(t0, t0+30]`).

Calibration of per-feature weights was **not attempted** (pre-registered
gate: ≥ 50 unique positive distinct CVEs + non-degenerate weights;
7 < 20 fires PIVOT). Paper 2 therefore makes **no learned-calibration
claim and no superiority claim**. The primary contribution is a
**failure-aware multi-t0 calibration gate methodology** — a chunked /
resumable / paced public-feed acquisition pipeline + a multi-t0
distinct-positive-CVE gate + a stop-rule registry — packaged as a
reproducible artefact. The secondary, **confirmatory** contribution is a
sensitivity sweep on a real-feed extension of Paper 1's frozen
synthetic-fleet benchmark across (i) six fixed design-prior weight vectors,
(ii) four capacity ratios, (iii) blackout policies, and (iv) feature
ablations. Conclusions are stated as descriptive deltas with paired-seed
bootstrap CIs and explicit MDE / power accounting; ranking-quality and
KEV-deadline metrics are reported as **diagnostic-only** under the measured
sparsity. **No reweighting after results, no post-hoc metric selection, no
calibration improvement claim, no production-readiness claim, no synthetic-
fleet-equals-real-host claim.** Paper 1's frozen primary artefact remains
content-addressed-frozen and untouched.

---

## 4. Research question

**Q (primary):** *When public-feed exploit labels are too sparse for
statistically defensible calibration, can a failure-aware gate and a
pre-registered sensitivity design produce an honest, reproducible methodology
for studying fixed-prior vulnerability prioritization?*

Sub-questions (each mapped to a pre-registered claim class in F3):

- **Q1 (calibration feasibility, CLM-A1 / A2):** Is per-feature weight
  calibration on KEV-only labels intersected with a catalog-restricted
  public-feed slice statistically justified at the measured label density?
- **Q2 (operational outcome, CLM-B1 / B2 / B3):** What is the descriptive
  paired ΔEHD of fixed-prior strategies vs. `epss_only` at the central
  cell, with bootstrap CIs and no superiority interpretation?
- **Q3 (robustness / sensitivity, CLM-C1..C4):** Are the operational
  conclusions stable across the F2 weight-vector family (A3), capacity
  ratios (A1), blackout policies (A6), and feature ablations (A5)?
- **Q4 (operational feasibility, CLM-E1 / E2):** Does the pre-registered
  scheduler produce feasible schedules and stay within capacity in every
  pre-registered cell?
- **Q5 (audit / reproducibility, CLM-F1 / F2):** Are outputs content-
  addressed and audit-verifiable, and is Paper 1's freeze invariant
  preserved before and after every Paper-2 run?

Diagnostic-only questions (CLM-D1, CLM-G1) are not granted research-question
status.

---

## 5. Prior-art position (summarises F1 only; no new claims)

Step-3.10 catalogued **15 verified academic / standard sources (P1–P15)**.
The literature *owns*:

- **Capacity-constrained vulnerability remediation** — VULCON (Farris et al.,
  ACM TOPS 21(4), 2018 `[VERIFY-DOI 10.1145/3196884]`), Deep VULMAN (Hore et
  al., ESwA 2023; arXiv 2208.02369), Roytman *"Capacity is King"*.
- **EPSS temporal stability** — Ravalico et al. (SSRN 5147459, 2025).
- **Context-feature ablations against EPSS** — Sherif et al. (arXiv
  2603.12450, 2026) on 280,694 CVEs.
- **Cross-system empirical comparison** — Koscinski et al. (arXiv
  2508.13644, 2025) on CVSS / SSVC / EPSS / Exploitability-Index.
- **Foundational EPSS / case-control** — Jacobs et al. 2021 DTRAP doi
  10.1145/3436242, Jacobs et al. 2023 arXiv 2302.14172, Allodi & Massacci
  2014 TISSEC doi 10.1145/2630069.
- **Standards** — CISA SSVC v2.0; NIST CSWP 41 LEV `[VERIFY]`.
- **Field taxonomy** — Jiang et al. 2025 survey (arXiv 2502.11070, 82 studies).

**Surviving novelty (verbatim from Step 3.10):**

> "A failure-aware calibration-gate methodology — the multi-t0
> distinct-positive-CVE gate with chunked / resumable / paced public-feed
> acquisition — applied to a public-sector-typical 31-product catalog over
> the EPSS v3 era, producing a documented negative result (7 unique
> positive Label-A CVEs over 18 monthly t0 windows) that establishes when
> per-feature context-aware weight calibration on public-feed labels is
> not statistically justified. Confirmatory secondary sensitivity sweeps
> (capacity, blackout, feature-ablation, label-source) on a real-feed
> extension of a frozen synthetic-fleet benchmark situate the finding
> within the established sensitivity literature."

No upgrade of this scope is permitted in Step 5+ without a new F1 supplement.

---

## 6. Framing changes from F1 — committed (one line each on how Paper 2 honors them)

| # | Step-3.10 §9 requirement | How Paper 2 honors it |
|---|---|---|
| 1 | Drop "Robustness of Context-Aware Vulnerability Prioritization …" headline | Title #1 leads with "When Calibration Fails …"; abstract leads with the 7-positives finding; §1 of the eventual paper will not use the word "Robustness" in the title or heading. |
| 2 | Elevate negative result + multi-t0 gate to primary contribution | §3 abstract; §4 research question Q1 / Q5; F5 K1 + K3 already-triggered status surfaced explicitly. |
| 3 | Demote sensitivity sweeps to confirmatory / secondary | §4 Q2..Q4 are stated as descriptive deltas; F3 binding keeps CLM-B1/C* as primary metric *bindings* but with descriptive interpretation; SM-4 forbids "significant" language for small effects even when Holm passes. |
| 4 | Acknowledge synthetic fleet as a Limitation, not novelty | Eventual paper's Limitations section must contain: *"the synthetic fleet limits external validity; real-host generalisation is not claimed."* This sentence is required, not optional. |
| 5 | Cite P1–P15 with **visible** differentiation in Related Work | Each P1–P15 citation must be followed by exactly one sentence stating what Paper 2 does differently (not just additionally). This is a Step-7 manuscript-CI check. |
| 6 | Drop "fixed / published weights" wording | Correct phrase: **"pre-registered design priors over fixed weight vectors"** (F2). Any occurrence of "fixed/published weights" is a CI failure. |
| 7 | No `[CITATION]` placeholders in the final manuscript | Every reference in the eventual paper is either fully verified or replaced with the next-best verified source. Submission-time gate. |

---

## 7. Fixed weights (references F2; does not duplicate)

**Source of truth:** `STEP3_11_FIX_F2_WEIGHTS.md` (Step 3.11).

The six **pre-registered design-prior** weight vectors are:

- `w_uniform`,
- `w_paper1_placeholder` (= Paper 1's existing `w_hand`),
- `w_epss_dominant`,
- `w_cvss_dominant`,
- `w_kev_dominant`,
- `w_context_dominant`.

Every vector carries `weight_family="fixed_prior_v1"` and
`weight_source="design_prior"`. **The vectors are design priors, not
literature numeric estimates, and not learned / calibrated / optimised /
validated.** No vector may be reweighted after results are observed
(F2 W4); no learned weights may be introduced in Paper 2 (F2 W5 + F5 K1
forbid `register_calibrated_weights` calls).

`w_paper1_placeholder` must always be labelled **"Paper 1 placeholder
weights"** in result tables — never "optimised", "calibrated", "learned",
"validated", or "literature-derived" (F2 W7).

---

## 8. Claim → metric binding (references F3; does not duplicate)

**Source of truth:** `STEP3_12_FIX_F3_METRIC_CLAIM_BINDING.md` (Step 3.12).

| Class | Primary metric (locked) |
|---|---|
| **A** Calibration feasibility | **unique positive distinct CVEs** (Step-3.8 measured = 7; never pair count, never event sum) |
| **B** Operational prioritization | **EHD** — paired ΔEHD vs `epss_only` at the cell with BCa CI (descriptive Δ + CI, never superiority) |
| **C** Robustness / sensitivity | **sensitivity ΔEHD** across the bound axis (A3 weight family / A1 capacity / A6 blackout / A5 feature ablation) |
| **D** Ranking quality | **diagnostic-only** (precision@k / recall@k / nDCG@k under Step-3.8 sparsity) |
| **E** Operational feasibility | **scheduler_feasibility_rate** (sentinel) |
| **F** Audit / reproducibility | **hash_chain_validity == True** + Paper-1 freeze status |
| **G** KEV deadline | **diagnostic-only** (`kev_deadline_breach_rate` under sparsity) |

Claim cards CLM-A1, CLM-A2, CLM-B1..3, CLM-C1..4, CLM-D1, CLM-E1..2,
CLM-F1..2, CLM-G1 are pre-registered with stop rules S-A..S-G1. Diagnostic-
only metrics may appear in appendix tables but **never** in abstract,
contributions list, main-text headline claims, or discussion.

---

## 9. MDE / inference policy (references F4; does not duplicate)

**Source of truth:** `STEP3_13_FIX_F4_MDE_POWER.md` (Step 3.13).

- **Baseline EHD scale**: `epss_only` mean EHD = **1,121,903 host-days**
  (Paper-1 frozen, 30 seeds, capacity = 100).
- **Meaningful threshold** (the F4 inferential gate): **5,000 host-days**
  (≈ 0.45 % of baseline) — chosen above the per-seed paired-Δ noise floor.
  Operational threshold (1,000 hd / 0.10 %) is reported but not used as the
  gate.
- **MDE-d at n = 30, α = 0.05, power = 0.80, two-sided**: 0.5292;
  MDE-hd ranges 1,234–2,916 hd at ×1.0–×1.5 sparsity inflation across the
  CLM-B1 / CLM-C* comparisons — **below 5,000 hd at every inflation
  factor for every non-degenerate comparison**.
- **Inferential tests** (Wilcoxon + Holm) allowed only when **all six** of
  the F4 policy conditions hold (n ≥ 30; std(Δ) > 0; MDE-hd ≤ 5,000 at
  chosen inflation; pair in pre-registered Holm family; no leakage warning;
  audit chain OK). Otherwise descriptive-only: paired mean + median + BCa
  CI; no Wilcoxon p, no Holm-corrected p, no significance language anywhere.
- **`kev_first − epss_only`** is **auto-dropped** for inference (SM-1) if
  paired-Δ std = 0 (it was 0 under Paper-1 fixtures; Paper-2 may or may not
  reproduce).
- **`fraction_of_oracle`** (CLM-B3) is **descriptive-only** (SM-3
  `oracle_inference: disabled`). Paper-1 mean `oracle − epss_only` Δ was
  −2,576 hd, below the meaningful threshold; oracle is sparse-label-weak.
- **SM-4** (effect-size honesty): even if Holm passes, if BCa CI overlaps 0
  or ⊂ [−5,000, +5,000] hd, the manuscript must use descriptive language
  ("small ΔEHD with CI [L, U]"), not "significant difference".
- **SM-5**: diagnostic-only metrics (CLM-D1, CLM-G1) never get significance
  language. CI rejects markdown that pairs `precision_at_k` /
  `recall_at_k` / `ndcg_at_k` / `kev_deadline_breach_rate` with `p =`,
  `p<`, "significant", or "significance".

---

## 10. Stop rules (references F5; does not duplicate)

**Source of truth:** `STEP3_14_FIX_F5_KILL_CRITERIA.md` (Step 3.14) +
machine-readable YAML to be materialised at Step-5 startup.

**Currently TRIGGERED** (permanent until a new pre-registration step
re-measures):

- **K1 — Calibration infeasibility.** `unique_positive_distinct_cves = 7 < 20`
  ⇒ calibration paper killed; learned-weight claims forbidden;
  `register_calibrated_weights` may not be called from Paper-2 code.
- **K3 — Public-feed label sparsity.** `unique_positive_cves < 20` OR
  per-window positives < 3 in > 75 % of windows ⇒ ranking + KEV-breach
  metrics diagnostic-only.
- **S-A** mirrors K1 (forbid learned-weight claims).

**Runtime stop rules** (evaluated at Step 5+ implementation):

- **K2** (post-run): all primary axes show |median ΔEHD| < 1,000 hd AND
  BCa CI ⊂ ±5,000 hd ⇒ paper reframed as failure-aware methodology only;
  no positive robustness-effect claim.
- **K4** (per-cell): `scheduler_feasibility_rate < 0.95` ⇒ exclude the cell
  from primary operational claims with a written footnote.
- **K5** (per-run): `hash_chain_validity == False` OR freeze verification
  fails OR leakage warning fires ⇒ **HARD HALT** the affected run.
- **K6** (every run): `make verify-primary-freeze` exits non-zero ⇒ **HARD
  HALT the entire step**.
- **K7** (pre-run perturbation check): catalog drift > 30 % under single-
  product perturbation ⇒ mapping-stability footnote (or pivot if multiple
  drift > 30 %).
- **K8** (post-axis): `CV_within > CV_across` ⇒ sensitivity for that axis
  is descriptive-only.

F3 S-A..S-G1 and F4 SM-1..SM-6 also apply per the F5 merged registry. No
runtime can bypass a triggered rule.

---

## 11. Factorial design (references F6; does not duplicate)

**Source of truth:** `STEP3_15_FIX_F6_MINIMAL_FACTORIAL.md` and the
companion `paper2/design/STEP3_15_MINIMAL_FACTORIAL_CELLS.csv` /
`STEP3_15_MINIMAL_FACTORIAL_CELLS.yaml` (Step 3.15).

| Group | New runnable cells | Reused (refs to primary) |
|---|---:|---:|
| Primary | **12** | — |
| Capacity sensitivity | 15 | 5 |
| Blackout sensitivity | 9 | 3 |
| Feature ablation | 12 | 2 |
| **Total planned runnable cells** | **48** | **10** |
| Deferred (not counted) | (8) | — |

**Central / default settings:** `n_seeds = 30`,
`label_source = label_a_kev_only`, `epss_era = v3`,
`catalog_strictness = cpe_exact_existing31`, `blackout_policy = primary`,
`approver_policy = A`, `capacity_ratio = 0.01`,
`t0_window_set = monthly_18_2023_09_to_2025_02`, PoC off.

**Total planned seed-runs at n = 30: 1,440 (primary)**;
**288 (pilot at n = 6).**

**Deferred** (explicitly NOT counted in run total): approver-B sweep, EPSS
v4 era, catalog expansion, PoC Label B, fuzzy CPE matching, n=50/100 seeds,
all-15-pairwise weight comparisons (already supported by primary at no
extra compute), GBT / learned comparator (**FORBIDDEN by K1**).

No cell may be added, dropped, or re-parameterised at Step 5 / Step 6
without a written `STEP4.x_*.md` supplement and a new decision-log row.

---

## 12. Freeze invariant (references F7; does not duplicate)

**Source of truth:** `STEP3_16_FIX_F7_FREEZE_INVARIANT.md` (Step 3.16).

- **Reference manifest:** `results/primary_full_v1/FREEZE_MANIFEST.json`,
  201,491 B, **SHA-256 `750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833`**;
  `make verify-primary-freeze` returns OK (390 audit logs valid).
- **Wrap (every Paper-2 batch):** pre-flight → run → post-run, with
  `make verify-primary-freeze PYTHON=.venv/bin/python`, manifest SHA, and
  `git status --porcelain` captured at both gates.
- **Five hard assertions** on post-run: `before_status == OK`,
  `after_status == OK`, `manifest_sha_before == manifest_sha_after`, no
  Paper-1 path in `git status --porcelain`, `freeze_primary_invocation_count == 0`.
- **Four witness files per batch** (`freeze_witness_before.json`,
  `freeze_witness_after.json`, `freeze_invariant_result.json`,
  `freeze_invariant_result.md`) + append-only batches index. Every Paper-2
  metric row carries the batch's `freeze_witness_id`.
- **Forbidden writes:** `results/primary_full_v1/`, `paper/tables/`,
  `paper/figures/`, `paper/manuscript/`, `paper/acm/`, `paper/eb1a/`,
  `FREEZE_MANIFEST.json`.
- **Forbidden ops:** `make freeze-primary`, `make inspect-primary --freeze`,
  `paper1.experiments.inspect.freeze(...)`, `register_calibrated_weights(...)`.
- **Paper-1 weight-registry lock test** must land at
  `tests/test_paper1_weights_locked.py` during Step 5 implementation and
  pass on every push touching `src/`, `paper2/`, or `tests/` (specification
  in F7 §8).

---

## 13. Compute plan (references F8; does not duplicate)

**Source of truth:** `STEP3_17_FIX_F8_COMPUTE_BUDGET.md` and the companion
`paper2/design/STEP3_17_PLANNED_BATCHES.yaml` (Step 3.17).

- **Chosen plan: F8-f pilot-then-primary.**
- **Envelope:** target ≤ 12 h wall-clock; **hard maximum 18 h**; per-batch
  abort at × 1.5 × estimate; ≤ 16 GB RAM; ≤ 25 GB incremental disk;
  parallelism = **seed-level, `max_workers = 4`** (2 if mem < 16 GB);
  acceptable overnight runs ≤ 2.
- **Pilot:** 4 batches × 48 cells × **6 seeds = 288 seed-runs**, est. 2–4 h.
- **Pilot gate:** computes `measured_per_seed_run_seconds` →
  `projected_primary_runtime_hours`; decision is
  `PROCEED_TO_PRIMARY_NO_FALLBACK` (≤ 18 h) or
  `APPLY_FALLBACK_ORDER_AND_REPLAN` (> 18 h).
- **Primary** (only if gate passes): 4 batches × 48 cells × **30 seeds =
  1,440 seed-runs**, est. 9.8–19.5 h serial / 3–6 h with 4 workers.
- **Fallback escalation order** (deterministic; only if pilot projects
  > 18 h): F8-e → F8-d → F8-c → F8-b → F8-a (last resort). Stop at the
  first option that brings the projection within budget.
  `pilot_only_fallback.enabled = false` (closed by default).
- **Shared computation (binding):** NVD universe ONCE per run; EPSS / KEV
  as-of maps ONCE per t0; fleet ONCE per seed; pair frames ONCE per
  (seed, t0); feature frames ONCE per (seed, t0); reuse across all
  strategies / weight vectors / capacities / blackouts / approvers /
  ablations within the same (seed, t0).
- **Abort / resume:** ×1.5 runtime overrun → pause + manual approval;
  K6 / K5 → hard halt; K2 all-axis → reframe-as-negative; K4 → exclude
  cell; resume skips completed seed / cell checkpoints unless `--force`
  + new decision-log row.

---

## 14. Venue strategy (references F9; does not duplicate)

**Source of truth:** `STEP3_18_FIX_F9_VENUE_PLAN.md` (Step 3.18).

- **Primary:** **USENIX CSET** (Workshop on Cyber Security Experimentation
  and Test) — strong fit; reproducibility / methodology charter; 2026
  cycle CFP URL `[VERIFY at submission time]`.
- **Backup 1:** **LASER** (Learning from Authoritative Security Experiment
  Results) — explicit null-results friendly; NDSS / ACSAC colocation
  pattern; 2026 colocation `[VERIFY]`.
- **Backup 2:** **ACM DTRAP** (Digital Threats: Research and Practice) —
  journal; methodology / measurement; the foundational EPSS paper landed
  here.
- **Top-tier venues (USENIX Security / IEEE S&P / ACM CCS / NDSS) honestly
  rejected** as poor fit per Step-3.10 — listed for transparency, not
  pursued.
- **Change-our-minds clause** (carried verbatim from F9):
  - **KILL (any one → abandon Paper 2):** K9-KILL-A.1 no venue home after
    3 attempts; A.2 pilot projection > 18 h even after full F8-a fallback;
    A.3 K2 every axis + reviewer rejects gate as trivial; A.4 everything
    degenerate; A.5 no insight beyond sparsity number; A.6 later-discovered
    prior art duplicates gate.
  - **PIVOT (any one → reshape):** K9-PIVOT-B.1 all Δs zero → pure
    methodology + sparsity paper; B.2 catalog expansion needed but
    deferred → spin off Paper-2.5 / 3; B.3 `epss_only` dominates → "EPSS
    hard to beat at this sparsity" headline; B.4 only acquisition + gate
    publishable → artefact paper (DTRAP).
  - **KEEP (all must hold):** K9-KEEP-C.1 gate stays novel; C.2 pilot
    confirms runtime feasible; C.3 ≥ 1 sensitivity axis interpretable or
    usefully-negative; C.4 stop-rule framework produces reproducible
    artefact; C.5 venue fit remains plausible.

---

## 15. Planned outputs (Step 5 + Step 6 deliverables; described, not produced here)

The following artefacts will be produced by **Step 5 implementation** and
**Step 6 pilot launch** (not in Step 4):

| Stage | Artefact | Notes |
|---|---|---|
| Step 5 | `paper2_runtime/` package | Runner + stop-rule loader + freeze-wrap context manager + per-cell metric writer. **Not** under `src/paper1/`. |
| Step 5 | `tests/test_paper1_weights_locked.py` | Per F7 §8. |
| Step 5 | `tests/test_paper2_runtime_*.py` | Stop-rule wiring; freeze-wrap; cell loader; reuse semantics. |
| Step 5 | `paper2/audit/stop_rules.log` | Append-only, hash-chained. |
| Step 6 | Pilot run configs (one per pilot batch) | Loaded from F6 + F8 YAMLs verbatim. |
| Step 6 | `paper2/audit/batches/<batch_id>/freeze_witness_*.json` + `freeze_invariant_result.{json,md}` | Per F7 §6. |
| Step 6 | `paper2/audit/batches/index.json` | Append-only batches index. |
| Step 6 | `paper2/audit/pilot_gate_decision.json` | `PROCEED_TO_PRIMARY_NO_FALLBACK` or `APPLY_FALLBACK_ORDER_AND_REPLAN`. |
| Step 6 | Per-cell `per_seed_metrics.csv` + `_meta.json` | Each row carries `freeze_witness_id`. |
| Step 7 (only if pilot passes) | Primary run artefacts, mirroring Step 6 schema | — |
| Step 8 (only if primary passes Step-7 stop-rule gates) | Aggregate tables + figures | Generated by a reporting step that reads Paper-2 outputs read-only. |
| Step 9 (only if Step 8 passes the change-our-minds clause) | Manuscript draft | Title #1 from §2; framing per §6; references per §5 with visible differentiation. |

No paper draft is produced before Step 8 (which itself depends on a passing
primary). No paper draft is produced from a run whose freeze witness is
missing or whose `freeze_witness_id` is not `OK` in the batches index.

---

## 16. Forbidden claims (eventual paper will not contain any of these)

Carried verbatim from F3 §6, F4 SM-policy, F5 K1, F9:

- No "fixed weights outperform EPSS in general" claim.
- No "context-aware prioritization is superior" claim.
- No "calibration improves results" claim (calibration was not attempted).
- No "the model is validated" claim.
- No "production readiness" claim.
- No "government deployment" or "compliance achievement" claim.
- No learned-model / GBT / DRL comparator anywhere in Paper 2 (K1).
- No claim using pair count or `event_positive_cves_across_windows` as the
  calibration sample size.
- No claim selected after seeing which metric "looks best" (post-hoc metric
  selection).
- No claim ranking weight vectors by quality (vectors are design priors,
  not quality-ordered).
- No claim that the synthetic-fleet extension matches real-host risk.
- No claim based on EPSS v4 (A8 held fixed at v3).
- No claim using PoC labels without the explicit license gate set.
- No superiority interpretation of CLM-B1 / B2 / B3 (descriptive Δ + CI
  only).
- No significance language anywhere near diagnostic-only metrics (CLM-D1,
  CLM-G1).

Manuscript-CI enforces these via the F3-forbidden-phrase guard + the
SM-5 diagnostic-only guard + the F9 framing-change checks.

---

## 17. Carried `[VERIFY]` blockers (no fabrication; re-verify at submission)

| Item | Status | Re-verification trigger |
|---|---|---|
| **VULCON** DOI 10.1145/3196884 (Farris et al., ACM TOPS 21(4), 2018) | `[VERIFY-DOI]` — ACM DL returned 403 in two attempts | re-verify at manuscript stage via institutional access |
| **NIST CSWP 41 — LEV** (May 2025) | `[VERIFY]` — URL real (981 KB PDF); WebFetch text extraction unparseable | human re-read of the PDF before any direct quote |
| **VulnScore** (Springer IJIS 2025, doi 10.1007/s10207-025-01164-3) | `[VERIFY]` — retained as soft context only | re-verify only if cited substantively |
| **CSET 2026 / LASER 2026 CFP URLs** | `[VERIFY at submission time]` — venue series real; year-specific URLs not yet published | re-check at submission window |

No `[CITATION]` placeholders are introduced. Items above are tracked so the
manuscript step does not slip them in unverified.

---

## 18. Step 5 handoff

**Step 5 may begin.** Constraints:

1. **Step 5 implements the runner** under a **new** `paper2_runtime/`
   package and Step-5-side `scripts/paper2_*`; it **may not** modify
   `src/paper1/` except for **register-only additions** of the four new F2
   weight vectors via `register_weights` (not `register_calibrated_weights`).
2. **Step 5 may not change the pre-registered design.** Any change to F2 /
   F3 / F4 / F5 / F6 / F7 / F8 / F9 requires a written
   `STEP4.x_*.md` supplement + a new decision-log row **before** the change
   takes effect.
3. **Step 5 must start with `make verify-primary-freeze`**; tests must lock
   the Paper-1 weight-registry values per F7 §8.
4. **Step 5 may not launch the primary** before the pilot finishes and the
   pilot-gate decision is `PROCEED_TO_PRIMARY_NO_FALLBACK`. Even within
   Step 5, the pilot and the primary are separate steps (Step 6, Step 7).
5. **Step 5 produces no calibrated / learned cells.** K1 + S-A forbid.
6. **Step 5 produces no manuscript text.** The manuscript stage is Step 9
   and gated by Steps 7 + 8.
7. **Step 5 produces no [CITATION] placeholders.** Manuscript stage is
   gated by the §17 re-verification triggers.
8. **Step 5 must wrap every test invocation that touches the freeze with
   the F7 pre-flight / post-run contract**, even for unit tests.

If at any point during Step 5+ a triggered rule (K1..K8 / S-A..S-G1 /
SM-1..SM-6) is bypassed, **K5 / K6 fires**, the run is invalid, and a new
decision-log row records the violation.

---

## 19. Sources of truth (read at Step 5 startup; immutable from here)

| Source doc | Purpose |
|---|---|
| `STEP3_10_PRIOR_ART_F1.md` | F1 verified prior-art table P1–P15 + falsification answers |
| `STEP3_11_FIX_F2_WEIGHTS.md` | F2 locked weight vectors + W1–W7 stop rules |
| `STEP3_12_FIX_F3_METRIC_CLAIM_BINDING.md` | F3 claim cards CLM-A1..G1 + 13 forbidden claims + S-A..S-G1 |
| `STEP3_13_FIX_F4_MDE_POWER.md` | F4 MDE table + meaningful threshold + per-claim inference status + SM-1..SM-6 |
| `STEP3_14_FIX_F5_KILL_CRITERIA.md` | F5 canonical stop-rule registry K1–K8 |
| `STEP3_15_FIX_F6_MINIMAL_FACTORIAL.md` | F6 minimal factorial + fallback options F8-a..F8-f |
| `paper2/design/STEP3_15_MINIMAL_FACTORIAL_CELLS.{csv,yaml}` | F6 cell enumeration (machine-loadable) |
| `STEP3_16_FIX_F7_FREEZE_INVARIANT.md` | F7 freeze contract + weight-registry lock test |
| `STEP3_17_FIX_F8_COMPUTE_BUDGET.md` | F8 envelope + pilot-then-primary plan + fallback order |
| `paper2/design/STEP3_17_PLANNED_BATCHES.yaml` | F8 planned-batches (machine-loadable) |
| `STEP3_18_FIX_F9_VENUE_PLAN.md` | F9 venue strategy + change-our-minds + Step-4 entry criteria |
| `PAPER2_DECISION_LOG.md` | Decision-log chain (Steps 1 .. 4) |
| `paper2/feasibility/probe_v2_multit0/` | Step-3.8 measured artefacts (7 unique positives, 2,688 catalog CVEs, 18 windows) |
| `results/primary_full_v1/` | Paper-1 frozen artefact (read-only forever; K6 territory) |

Step 5 + later may **read** any of the above. Step 5 + later may **not
modify** any of the above without a written supplement + a new decision-log
row.

---

## 20. Invariants honored in this Step 4

- Paper 1 frozen outputs **untouched**.
- No experiments run.
- No code written.
- No new metrics, axes, weights, cells, stop rules, MDE thresholds, freeze
  rules, compute parameters, venue choices, or change-our-minds conditions
  introduced beyond what F2–F9 already locked.
- No calibration claim. No superiority claim. No production-validation
  claim. No real-host generalisation claim. No `[CITATION]` placeholder.
- PoC license-gated and off.
- The calibration-feasibility claim remains anchored to unique positive
  distinct CVEs (7 < 20); pair count and event sum are forbidden as
  calibration sample-size proxies.

**This pre-registration is the immutable contract for Steps 5–9. The only
permitted way to change it is a written `STEP4.x_*.md` supplement
accompanied by a new row in `PAPER2_DECISION_LOG.md`. Step 5
implementation may now begin.**
