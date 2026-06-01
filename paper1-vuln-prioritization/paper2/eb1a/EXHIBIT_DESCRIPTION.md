# Paper 2 — Exhibit Description

This file describes each technical artefact that Paper 2 produces, in the
order an attorney would likely list them as exhibits. Each entry records:
what the artefact is, where it lives in the repository, what it shows, and
what *cannot* be inferred from it.

Nothing in this file asserts publication, acceptance, peer review,
citation, take-up, or external use. Each exhibit is a *technical artefact*
the author built and audited inside this repository.

---

## Exhibit P2-1 — Pre-registration (F1–F9)

**Location.** `paper2/manuscript/STEP4_PREREGISTRATION.md` and the nine
fix documents under `paper2/manuscript/STEP3_*FIX_*.md`.

**What it shows.** The author committed in writing — before any data was
collected — to a specific design: six weight vectors, 28 stop rules, a
fixed inference policy (5,000 host-day effect threshold; MDE-d ≈ 0.5292 at
n = 30), a fixed cell enumeration (48 cells), a freeze invariant tied to a
SHA-256 manifest, and a compute envelope.

**What cannot be inferred.** That the pre-registration was reviewed by a
third party. It was authored by the author and is enforced by the
author's own code.

---

## Exhibit P2-2 — Runtime package

**Location.** `paper2_runtime/` (13 Python modules) and `tests/test_paper2_*.py`
(154 tests, all passing).

**What it shows.** The pre-registered design is operationalized as
machine-readable code. The runtime refuses operations the pre-registration
forbids (e.g., a calibration cell, a primary batch from outside the
allowed list, a missing freeze witness) and emits stop-rule events when
pre-registered conditions are met.

**What cannot be inferred.** That the package has been installed, used, or
audited outside this repository.

---

## Exhibit P2-3 — Public-feed feasibility probe

**Location.** `paper2/feasibility/probe_v2_multit0/summary.json` and
companion calibration / acquisition status files.

**What it shows.** Aggregate quantities measured on real public feeds
(NVD, EPSS, KEV) over a 41-month universe window and 18 monthly time-origin
windows: 110,224 total NVD records, 104,495 normalized CVEs, 95,006 CVEs
with CPE, 2,688 catalog-matched CVEs, **7 unique positive CVEs**, and
`calibration.attempted = false` with reason "unique positive distinct CVEs
7 < min 50".

**What cannot be inferred.** That 7 is the truth about the entire field;
it is the count *on this catalog, this universe window, this label
definition*. The author makes no claim that a different catalog would
produce the same count.

---

## Exhibit P2-4 — Pilot run + pilot gate decision

**Location.** `paper2/audit/pilot_gate_decision.json` and per-batch
artefacts under `paper2/results/B-pilot-*/`.

**What it shows.** Four pilot batches (288 seed-runs total) executed in
459.5 wall-clock seconds with a measured per-seed-run cost of 1.596 s,
projecting a primary runtime of 0.83 h under a 1.3× safety factor — well
under the pre-registered 18-h compute ceiling. Pilot gate decision:
`PROCEED_TO_PRIMARY_NO_FALLBACK`. All four pilot batches verified
freeze-OK; K1, K3, S-A triggered on every batch.

**What cannot be inferred.** That the pilot certified any model. The pilot
is a runtime-projection and stop-rule-rehearsal step; it does not fit
weights.

---

## Exhibit P2-5 — Primary run

**Location.** `paper2/audit/primary_complete.json` and per-cell metric
CSVs under `paper2/results/B-primary-*/`.

**What it shows.** Four primary batches: 48 cells, 1,440 seed-runs, 8,640
metric rows in 2,143.21 wall-clock seconds. All four batches freeze-OK; all
8,640 rows carry the freeze-witness identifier
`750e144b…b022833`; no calibration cells; no forbidden operations.
Completion status: `PRIMARY_COMPLETE_VALID`.

**What cannot be inferred.** That any cell produced a better outcome than
any other. K8 fires on every measured axis; the runs are honest
measurements, not a ranking of strategies.

---

## Exhibit P2-6 — Aggregation + inference + post-run stop rules

**Location.** `paper2/tables/` (19 aggregation tables + 12 inference
tables), `paper2/figures/` (14 figures), `paper2/audit/step9_aggregation_complete.json`,
`paper2/audit/post_run_stop_rule_evaluation.json`.

**What it shows.** Aggregation of per-seed metrics into per-cell and
per-strategy summaries; paired Δ EHD vs. the central `epss_only` baseline
with BCa CI and Holm-corrected Wilcoxon under the pre-registered inference
policy; per-axis K2 (effect-size at cell-mean) and K8 (CV_within vs.
CV_across) evaluations. K7 (catalog stability) is recorded as SKIPPED with
rationale (no perturbation data was generated).

**What cannot be inferred.** That a statistically significant effect was
found. K8 fires on every measured axis, so the manuscript reports those
axes descriptively only.

---

## Exhibit P2-7 — Manuscript draft

**Location.** `paper2/manuscript/paper2_full_draft.md` (17 sections).

**What it shows.** The text of the methodology paper, including the
abstract, the failure-aware gate methodology, the study design, the
feasibility evidence, the sensitivity sweep, the inference policy, the
results, the discussion, the limitations, the future work, the conclusion,
the reproducibility section, and the references.

**What cannot be inferred.** That the manuscript has been peer-reviewed,
accepted, or sent to a venue.

---

## Exhibit P2-8 — Submission scaffold

**Location.** `paper2/submission/cset/` (LaTeX scaffold for USENIX CSET as
primary target; `main.tex` + 16 section files + 15 verified BibTeX
entries + 14 figures + 33 tables) and the four top-level submission
documents under `paper2/submission/` (`README.md`,
`REPRODUCIBILITY_APPENDIX.md`, `CLAIM_AUDIT_REPORT.md`,
`CITATION_AUDIT_REPORT.md`).

**What it shows.** The author has assembled the artefacts a venue
submission would need.

**What cannot be inferred.** That the author has submitted the package to
any venue. The package has not been sent; the LaTeX template has not been
swapped to a venue-specific class; the author block remains anonymized
placeholder.

---

## Exhibit P2-9 — Claim-audit script

**Location.** `scripts/paper2_claim_audit.py` and the
`paper2/submission/CLAIM_AUDIT_REPORT.md` it produced.

**What it shows.** A Python script that scans the manuscript for an
enumerated set of overclaim phrases, with proximity rules (e.g.,
"significant" within 100 chars of `precision_at_k`) and a negation window
(e.g., "validated" preceded by "not" within ~6 words is allowed). The
report on the current draft reads `PASS  (0 violations)`.

**What cannot be inferred.** That every possible overclaim has been
caught. The script catches what it is configured to catch.

---

## Exhibit P2-10 — Citation-audit report

**Location.** `paper2/submission/CITATION_AUDIT_REPORT.md` and
`paper2/submission/cset/references.bib`.

**What it shows.** 15 verified BibTeX entries; 0 unresolved `[VERIFY]`
markers; three previously-blocking citations (VULCON, NIST CSWP 41,
VulnScore) re-verified via Crossref / NIST PDF before final packaging;
four routine pre-submission human-review chores logged.

**What cannot be inferred.** That every cited author has reviewed how
their work is summarised in the manuscript.

---

## Exhibit P2-11 — Paper 1 freeze invariant evidence

**Location.** `paper/report/report_manifest.json` (Paper 1) and the
per-batch `freeze_invariant_result.json` files under
`paper2/results/B-primary-*/`.

**What it shows.** The Paper 1 freeze SHA-256 manifest
`750e144b…b022833` is byte-equal in both Paper 1's report manifest and as
the freeze-witness on every Paper 2 primary batch summary. Paper 1's
frozen outputs were not modified during Paper 2's execution.

**What cannot be inferred.** That Paper 1 has been peer-reviewed, accepted,
or cited. The invariant proves byte-equality, not external recognition.
