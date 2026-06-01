<!--
Paper 2 — Step 3.11: Fix F2 — Lock the Fixed-Weight Source.
Documents the locked, pre-registration-equivalent fixed-weight set for Paper 2's
sensitivity sweeps. No code changes in this step (per "do not build" rule);
implementation will happen inside Step 4. No paper drafting; no experiments;
no calibration; Paper 1 frozen outputs untouched.
-->

# Paper 2 — Step 3.11: Fix F2 — Locked Fixed-Weight Source

**F2 status: COMPLETE.**
**Chosen strategy: Option C — weight choice is itself a sensitivity axis.**
**Step 4 still NOT allowed** (F3–F9 owed).

The decision: Paper 2 will treat the prioritization weight vector as a
**pre-registered sensitivity axis** over six fixed vectors. The vectors are
locked in this document and cannot be re-tuned after results are observed. No
learned / calibrated weights are introduced — calibration remains infeasible per
Step 3.8 (7 unique positive Label-A CVEs over 18 monthly t0 windows).

---

## 1. Inspected: existing Paper 1 weight registry

Source of truth: `src/paper1/model/weights.py` (read this turn; not modified).

### 1.1 Feature columns (exact)
```
FEATURE_COLUMNS = ["E", "K", "S", "C", "X", "U", "R"]
```
- `E` — EPSS exploit-likelihood (real-feed in Paper 2).
- `K` — KEV-listing status as of t0 (real-feed in Paper 2).
- `S` — CVSS severity (real-feed in Paper 2; v3.1 / v4 per NVD).
- `C` — synthetic asset criticality (Paper-1 synthetic fleet).
- `X` — synthetic local exposure.
- `U` — synthetic remediation urgency.
- `R` — remediation complexity, **subtracted as a cost** in scoring.

### 1.2 Scoring formula (confirmed in `src/paper1/model/scoring.py:3`)
```
score = w_E*E + w_K*K + w_S*S + w_C*C + w_X*X + w_U*U − w_R*R
```
`R` is stored as a non-negative magnitude in the registry and the sign-flip
happens inside scoring (line 42: `(-w * v) if f == "R" else (w * v)`). This is
consistent with the F2 brief.

### 1.3 Existing weight vectors in the registry (verbatim)
```
w_uniform              = {E:1, K:1, S:1, C:1, X:1, U:1, R:1}        # normalizes to 1/7 each
w_hand                 = {E:0.20, K:0.20, S:0.10, C:0.20, X:0.15, U:0.10, R:0.05}   # sum=1.00
w_logit_placeholder    = {E:0.20, K:0.20, S:0.10, C:0.20, X:0.15, U:0.10, R:0.05}   # placeholder; mirrors w_hand
w_lin_placeholder      = {E:0.20, K:0.20, S:0.10, C:0.20, X:0.15, U:0.10, R:0.05}   # placeholder; mirrors w_hand
```
Module docstring explicitly states *"`w_logit_placeholder` / `w_lin_placeholder`
are explicit placeholders that mirror `w_hand` until Phase 6 calibration replaces
them with regression-fit values."* Paper 1's `proposed_full` strategy uses
`weights_name="w_logit_placeholder"` (`src/paper1/model/strategies.py:99`).

### 1.4 Are placeholders named as placeholders? **Yes.**
Both module docstring and variable names ("placeholder") are explicit. Paper 1's
manuscript also tags `proposed_full` results as "placeholder-weight" outcomes
(Paper 1 closeout package). No silent re-labelling has occurred.

### 1.5 Do any calibrated weights exist but were not used? **No.**
The registry contains only `w_uniform` + `w_hand` + the two placeholders (which
mirror `w_hand`). No calibrated vector was ever registered via
`register_calibrated_weights` — Paper 1 documented this gap; Paper 2 Steps 3.6–3.8
empirically established that public-feed calibration is infeasible. The
`register_calibrated_weights` entry point exists but has not been called.

### 1.6 Registry safety
- `validate_weights` rejects missing / extra / negative / zero-sum weights.
- `normalize_weights` always returns a sum-to-1 copy (callers never mutate the
  registry).
- `ablate_weight` zeroes a feature and renormalises the remaining six (used by
  Paper 1's `proposed_no_criticality` and `proposed_no_exposure` strategies).
- All six F2 vectors below are guaranteed-valid under this validator.

---

## 2. Literature-source review (from F1 only)

For each candidate basis identified in Step 3.10, the table records whether the
source supplies *actual numeric weights*, only *feature-inclusion justification*,
or only a *priority ordering* — and therefore whether it can support a fixed
prior or only a sensitivity-axis label.

| Source | Numeric weights? | Feature-inclusion justification? | Priority ordering? | OK as sensitivity-axis label? | Citation status |
|---|---|---|---|---|---|
| EPSS — Jacobs et al. 2021 DTRAP; Jacobs et al. 2023 (arXiv 2302.14172); FIRST EPSS | **No** — EPSS publishes a *single* exploit-probability score per CVE; internal XGBoost weights over 1,164 features are *not* a 7-feature prior. | yes (for `E`) | yes (E should weigh heavily on exploit probability) | **yes** — supports "EPSS-dominant" axis label | verified |
| CVSS v3.1 / v4 — FIRST | **No** — CVSS publishes the severity formula's internal sub-scores (AV/AC/PR/UI/S/C/I/A); not a 7-feature priority. | yes (for `S`) | yes (S should weigh heavily on severity-led prior) | **yes** — supports "CVSS-dominant" axis label | verified |
| CISA KEV catalog | **No** — KEV is a binary status list. | yes (for `K`) | yes (KEV-listed should dominate) | **yes** — supports "KEV-dominant" axis label | verified |
| CISA / CMU-SEI SSVC v2.0 | **No** — SSVC is a *decision tree* over qualitative inputs, not a weighted sum. | partial (justifies `K`, `C`-like Mission Impact, `X`-like Exposure) | yes (Exploitation→Automatable→Mission/Well-being tree gives an ordering) | partial — supports "context-dominant" framing for `C`/`X` but not numeric | verified |
| NIST CSWP 41 LEV (May 2025) `[VERIFY]` | **No** — LEV proposes a *probability* metric complementary to EPSS, not 7-feature weights. | yes (for `E`-like) | yes (probability-led) | **yes** — supports EPSS-/probability-dominant labelling | `[VERIFY]` re-confirm before manuscript |
| Sherif et al. 2026 KRI (arXiv 2603.12450) | **No** — KRI is a *category* framework (threat + impact + exposure) with model-fit AUPRC numbers; their fits are *learned*, not a fixed weighted-sum prior. | yes (for `C`/`X` analogues) | yes (context features should matter) | **yes** — supports "context-dominant" axis label | verified (Step 3.10) |
| Ravalico et al. 2025 EPSS temporal dynamics (SSRN 5147459) | No (it studies EPSS stability) | n/a | n/a | n/a | verified |
| VULCON (Farris et al. 2018) `[VERIFY-DOI]` | **No** — uses CVSS as the per-vuln scalar inside an MIP; no 7-feature prior | partial (for `S`) | yes (CVSS-led baseline) | **yes** — supports "CVSS-dominant" axis label | `[VERIFY-DOI 10.1145/3196884]` |
| Deep VULMAN (Hore et al. 2023) | **No** — RL learns the policy; not a fixed prior | n/a | n/a | n/a | verified |
| Roytman "Capacity is King" | **No** — vendor research note, no numeric prior | n/a | yes (known-exploit-first beats CVSS) | **yes** — supports KEV-/exploit-dominant axis label | verified |
| Koscinski et al. 2025 (arXiv 2508.13644) | **No** — compares CVSS/SSVC/EPSS/Exploitability-Index but does not publish a weighted-sum prior | n/a | yes (systems disagree) | partial — supports the sensitivity framing itself | verified |
| VulRG (arXiv 2502.11143) | **No** — graph-based propagation; no 7-feature prior | n/a | n/a | n/a | verified |
| VulnScore (Springer IJIS 2025) `[VERIFY]` | **No** — composite of EPSS + CVSS + Vulners-AI + user criticality; deployed-system, weights tied to that pipeline | partial (for E, S, C) | yes (composite) | partial | `[VERIFY]` |
| Allodi & Massacci 2014 (TISSEC) | **No** — case-control; logistic coefficients are *learned*, not a fixed prior | yes (PoC/black-market presence stronger than CVSS) | yes (exploit-presence-led) | partial — supports KEV-/exploit-dominant axis label | verified |
| Jiang et al. 2025 survey (arXiv 2502.11070) | **No** — taxonomy paper | n/a | n/a | confirms that *categories* (severity / exploitability / context / predictive / aggregation) are recognised | verified |

**Direct conclusion.** *No source in the F1 set publishes numeric weights for a
seven-feature `(E, K, S, C, X, U, R)` prioritization scheme.* Sources justify
*feature inclusion* and *priority ordering*; they do not supply *numeric
weights*. Therefore Option B ("literature-grounded simple prior") cannot be
honestly executed at a single locked numeric value — any number we write would
be invented and falsely attributed.

---

## 3. F2 decision

### 3.1 Options considered
- **Option A — Paper 1 placeholder weights only.** Honest, reproducible, but
  delivers only one weight vector. Cannot demonstrate whether the paper's
  findings are robust to plausible alternative priors — and the F1 prior art
  (Sherif 2026 ablation, Koscinski 2025 system disagreement, Roytman strategy
  sweep) makes "single-vector sensitivity claim" indefensible.
- **Option B — Single literature-grounded fixed prior.** Rejected: §2 shows no
  source supplies numeric weights for our 7-feature scheme. Picking a single
  literature-flavoured vector would require inventing numbers and attributing
  them to the literature — that is **fabrication** and is ruled out by the F2
  hard rules.
- **Option C — Weight choice as a sensitivity axis (six vectors).** Each vector
  carries a *design-prior* rationale and an *axis-label* citation chain (§2);
  numbers are pre-registered before any Paper-2 measurements; the paper studies
  whether conclusions move under the family. Most honest and least p-hackable.

### 3.2 Choice
**Option C.** Aligns with the Step-3.10 narrowed framing: weight choice becomes
one of the *confirmatory* sensitivity axes (alongside capacity, blackout,
feature-ablation, label-source). The headline contribution remains the
failure-aware-gate methodology + the negative feasibility result; the
fixed-weight family is *supporting evidence* that the headline conclusions do
not depend on a single arbitrary weight vector.

---

## 4. Locked fixed-weight vectors (pre-registered)

All six vectors below are **locked**: their numeric values must not be changed
after any Paper-2 measurement is observed. They are *design priors*, not
literature-derived numeric estimates. Each carries a rationale and an
*axis-label* citation (the citation justifies the *direction* of the prior, not
the specific numbers).

All vectors satisfy:
- 7 keys exactly = `{E, K, S, C, X, U, R}`,
- every weight ≥ 0,
- positive weights pre-normalisation sum to 1.0,
- `R` is **stored positive** and **subtracted in scoring** (handled by
  `paper1.model.scoring`).

| Name | E | K | S | C | X | U | R | Σ | Rationale (design prior, NOT a literature numeric claim) | Axis-label citation chain |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| **`w_uniform`** *(already registered)* | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 1.00 | Null prior: no feature is privileged. Baseline against which all other priors are compared. | none required |
| **`w_paper1_placeholder`** *(already registered as `w_hand` / `w_logit_placeholder`)* | 0.20 | 0.20 | 0.10 | 0.20 | 0.15 | 0.10 | 0.05 | 1.00 | The *exact* pre-existing Paper 1 placeholder weights. Carried forward unchanged so Paper 2's `proposed_full` cell is comparable to Paper 1's frozen artefact. **Must always be labelled "Paper 1 placeholder weights"** — never "optimized" / "calibrated" / "learned" / "validated" / "literature-derived". | Paper 1 frozen artefact `results/primary_full_v1/` (self-reference, documented placeholder) |
| **`w_epss_dominant`** *(new — to be registered in Step 4)* | **0.50** | 0.15 | 0.10 | 0.10 | 0.05 | 0.05 | 0.05 | 1.00 | Reflects the "EPSS deserves the largest weight because it is a calibrated probability of exploitation" prior. The 0.50 is a *design choice*, not a number from the EPSS papers. | EPSS (Jacobs et al. 2021 DTRAP doi 10.1145/3436242; Jacobs et al. 2023 arXiv 2302.14172); NIST LEV CSWP 41 `[VERIFY]` |
| **`w_cvss_dominant`** *(new)* | 0.15 | 0.10 | **0.50** | 0.10 | 0.05 | 0.05 | 0.05 | 1.00 | Reflects the "severity-led" prior used by VULCON and many deployed scanners. The 0.50 is a design choice. | CVSS v3.1 / v4 (FIRST); VULCON (Farris et al. 2018) `[VERIFY-DOI 10.1145/3196884]` |
| **`w_kev_dominant`** *(new)* | 0.15 | **0.50** | 0.10 | 0.10 | 0.05 | 0.05 | 0.05 | 1.00 | Reflects the "known-exploited-first" prior consistent with Roytman's "strategy dominates capacity" finding and Allodi & Massacci's exploit-presence finding. The 0.50 is a design choice. | CISA KEV catalog; Roytman *Capacity is King*; Allodi & Massacci 2014 (TISSEC doi 10.1145/2630069) |
| **`w_context_dominant`** *(new)* | 0.15 | 0.10 | 0.10 | **0.30** | **0.25** | 0.05 | 0.05 | 1.00 | Reflects the "asset-context outweighs raw threat" prior found in SSVC's stakeholder-specific tree and Sherif et al.'s KRI (threat + impact + exposure). The 0.30/0.25 split is a design choice. | CISA SSVC v2.0 (CMU-SEI); Sherif et al. 2026 (arXiv 2603.12450) |

### 4.1 Pre-registered tags (must appear in every Step-4 result table)
- All six vectors are tagged **`weight_family = "fixed_prior_v1"`**.
- Each vector is tagged **`weight_source = "design_prior"`** (never `learned` /
  `calibrated` / `optimized`).
- Each vector is tagged **`registered_at = "Step 3.11 (pre-registration)"`**.
- Each vector is tagged with the citation chain above (verbatim).

### 4.2 Conflicts with the existing design
- **`w_uniform`** — the existing registry value is `dict.fromkeys(FEATURE_COLUMNS, 1.0)`,
  which the registry normalises to `1/7 ≈ 0.1429` per feature. The F2 task's
  suggested "uniform: all 1/7" is *the same vector after normalisation* — no
  conflict; reuse `w_uniform` as-is.
- **`w_paper1_placeholder`** — the F2 task suggests "use exact existing `w_hand`".
  The exact existing `w_hand` is `{E:0.20, K:0.20, S:0.10, C:0.20, X:0.15, U:0.10, R:0.05}`.
  The F2 task's *suggested* placeholder numbers were `{E:0.20, K:0.20, S:0.10, C:0.20, X:0.15, U:0.10, R:0.05}` —
  match. No conflict.
- The four new vectors (`w_epss_dominant`, `w_cvss_dominant`, `w_kev_dominant`,
  `w_context_dominant`) all sum to 1.00 and contain only non-negative weights;
  they pass `validate_weights` and `normalize_weights` unchanged.

### 4.3 What cannot be claimed about any vector
- Not "optimized", "calibrated", "learned", "validated", "literature-derived",
  "published", or "fit".
- No vector may be presented as *the* correct weighting — they are deliberately
  diverse design priors used to test whether conclusions are robust.
- No comparison across vectors may be framed as a superiority claim about
  *strategies*; comparisons are *sensitivity findings* about *how much
  conclusions move with the prior*.

---

## 5. Kill / stop rules for weights

Pre-registered (locked in this document, will be carried into
`STEP4_PREREGISTRATION.md`):

- **W1.** If the six fixed-weight vectors are statistically *indistinguishable*
  on every primary metric (paired-seed BCa CI for ΔEHD vs `w_uniform` overlaps 0
  for every named vector at every capacity cell), **report that as the finding**
  — do not re-tune any vector to manufacture a separation.
- **W2.** If `epss_only` (a strategy, not one of these vectors) dominates every
  fixed-weight vector on EHD across every capacity cell, **report that as the
  finding** — do not introduce a "better" weight vector to recover separation.
- **W3.** If `w_context_dominant` performs *worse* than `w_uniform` on EHD,
  **report that as the finding** — do not adjust C / X / U weights to recover
  a context advantage.
- **W4.** **No re-weighting after results.** The six vectors are immutable from
  this document forward. Any vector change requires a new fix (F2.1) with a
  written justification preceding the next experiment.
- **W5.** **No learned weights in Paper 2.** Per Step 3.8, calibration is
  infeasible on this label set. Introducing a learned vector would be a
  *separate future study* with its own feasibility gate, not a Paper-2 result.
- **W6.** **No literature-derived numeric vectors masquerading as fixed
  priors.** The four named-prior vectors are explicitly *design priors with
  citation chains for the direction*, never *numeric quotations from
  literature*. Any text that implies otherwise must be corrected before any
  Step-4 measurement is taken.
- **W7.** **The `proposed_full` strategy's labelling rule is unchanged from
  Paper 1**: it remains a *placeholder-weight* result. Paper 2 may run
  `proposed_full` under any of the six vectors; each cell must record the
  vector name in the result table.

---

## 6. Exact implementation implications (for Step 4, NOT executed here)

In **Step 4** (only), after F3–F9 are also locked:

1. Add the four new built-in entries to `src/paper1/model/weights.py:_BUILTIN`
   (or `paper2/`-side mirror) with the literal values in §4. Module docstring
   must be updated to state that the four `*_dominant` vectors are
   pre-registered design priors, not learned weights.
2. Extend `paper1.model.strategies.FEATURE_STRATEGIES` (or a Paper-2-side
   registry) so each of the six vectors can be selected as
   `weights_name=<vector>` for the `proposed_full` strategy template — yielding
   six `proposed_full__<vector>` cells per capacity / blackout cell.
3. Update `proposed_no_criticality` / `proposed_no_exposure` semantics:
   feature-ablation sweeps must run on the *family* of six vectors, not only
   on `w_logit_placeholder` — otherwise the ablation finding cannot be
   disentangled from the choice of vector.
4. Tests must assert: every Paper-2 result row carries `weight_family`,
   `weight_source`, `weight_vector_name`, and the citation-chain tag; the
   freeze check rejects any row missing them.
5. No changes to `register_calibrated_weights` (kept inert in Paper 2).
6. **Paper 1's frozen outputs and existing built-ins are never modified.**
   Adding new built-in entries does not alter the existing four (`w_uniform`,
   `w_hand`, `w_logit_placeholder`, `w_lin_placeholder`); a Paper-2 unit test
   must lock their numeric values to detect accidental drift.

No code in this step. The above is *what Step 4 will do*; the values to
implement are §4.

---

## 7. Unresolved citation items
- `[VERIFY-DOI 10.1145/3196884]` — VULCON (Farris et al. ACM TOPS 21(4), 2018):
  DOI confirmed via SERP; full ACM DL page returned HTTP 403 in Step 3.10.
  Re-verify when manuscript references are compiled.
- `[VERIFY]` — NIST CSWP 41 LEV (May 2025): consistent across multiple search
  results; full text not fetched this turn.
- `[VERIFY]` — VulnScore (Alqahtani & Almukaynizi, Springer IJIS 2025,
  10.1007/s10207-025-01164-3): listed in SERP, used only as soft-context for
  composite-scoring framing; not relied on for any numeric claim.
- All other §2 citations were fetched and verified during Step 3.10.

These are out-of-band notes; they do not block F2. F1's surviving-citation
chain stands.

---

## 8. F2 status and decision-flow summary
- **F2: COMPLETE.** Option C locked; six vectors specified; W1–W7 stop rules
  pre-registered; conflicts checked against the existing registry; no code
  written.
- **Step 4 still NOT allowed.** F3 (metric → claim binding), F4 (MDE / power
  pre-registration), F5 (kill criteria K1–K6 as STOP rules), F6 (minimal
  factorial), F7 (Paper-1 freeze invariant restated), F8 (compute estimate),
  F9 (venue plan + change-our-minds clause) remain owed. The Step-3.10
  framing changes (drop the "Robustness" headline, demote sensitivity sweeps
  to confirmatory, elevate the negative result and gate methodology to primary,
  acknowledge synthetic-fleet as a limitation, cite P1–P15 with visible
  differentiation, drop "fixed/published weights" wording) must also land in
  `STEP4_PREREGISTRATION.md`.

## Invariants honored (re-asserted)
Paper 1 frozen outputs untouched. No experiments run; no code written; no paper
drafted. No calibration claim; no superiority claim. The chosen vectors are
*design priors*, never "published" or "literature-derived" numeric estimates. No
fabricated citations. PoC/ExploitDB stays off. The sparse-label cause of the
calibration failure (Step 3.8) is reaffirmed, not hidden.
