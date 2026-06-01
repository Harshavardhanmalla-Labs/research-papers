# Paper 2 — Original Contribution Statement

This file states what is original in Paper 2 *as a methodology artefact*,
relative to publicly available prior work. It does not claim peer-review
status, citation count, take-up, or external use.

## What is original

1. **A failure-aware multi-t0 calibration gate that refuses to fit when
   public-feed positive labels are too sparse.** The gate is operationalized
   as a stop rule (`K1`) driven by a measurable quantity (unique distinct
   positive CVEs across `t0` windows under a leakage-safe label) with a
   pre-registered minimum. The gate is part of the methodology, not a
   post-hoc rationalization: it was committed to in the pre-registration
   before any data was collected.

2. **A reproducible sparse-label experimental design.** Nine fix documents
   (F1–F9) lock the weight vectors, metric bindings, inference policy, cell
   enumeration, freeze invariant, and compute budget before any seed-run is
   executed. The design is machine-readable; every downstream module reads
   the pre-registration rather than carrying its own copy of the numbers.

3. **An end-to-end audited artefact chain.** Pre-registration → runtime
   package → pilot gate → primary run → aggregation → inference → post-run
   stop rules → figures → submission scaffold, with a single freeze-witness
   identifier carried on every metric row and verified before and after
   every batch.

4. **An honest negative result on public-feed sparse-label feasibility.**
   The author reports that only 7 unique positive CVEs were observed across
   18 monthly t0 windows and 2,688 catalog-matched CVEs, that calibration
   was therefore not attempted, and that across-cell deltas in the
   confirmatory sensitivity sweep are descriptive only because the K8 stop
   rule fires on every measured axis.

5. **A claim-audit harness for negative-result methodology papers.** The
   harness scans the manuscript for an enumerated list of overclaim
   phrases, with proximity rules (e.g., "significant" near a diagnostic-only
   metric is flagged) and a negation window (e.g., a phrase preceded by
   "not" within ~6 words is allowed). The harness reports zero violations
   on the current draft.

## What this builds on (and does not duplicate)

Paper 2 explicitly positions itself against the public prior-work entries
identified during pre-registration (P1–P15 in `STEP4_PREREGISTRATION.md`),
each referenced in the manuscript's Related Work section with a one-sentence
differentiation. Examples of prior work and how Paper 2 differs:

- Prior work that fits per-feature weights on a single time origin and a
  partial vulnerability label: Paper 2 evaluates the *feasibility* of that
  fitting under a multi-`t0`, leakage-safe label, and reports that the
  label density on public feeds is too low for defensible fitting on this
  dataset.
- Prior work that proposes new ranking signals: Paper 2 takes the existing
  signals (CVSS / EPSS / KEV / fixed-prior weight families) and asks under
  what label-density regime they can be combined by fitting; the answer on
  public feeds is: not on this dataset.
- Prior work that reports positive prioritization results: Paper 2 reports a
  negative result and provides the methodology that surfaced it.

## What is not claimed as original

- The use of NVD, EPSS, and KEV as public exploit-signal feeds.
- The CVSS base scoring rubric, the EPSS scoring system, the CISA KEV
  catalog format, or the SSVC decision rubric.
- The Paper 1 frozen comparator scoring formula (it is reused, not
  re-derived, and the Paper 1 frozen outputs were not modified).
- The general idea of multi-time-origin evaluation in cybersecurity
  research (this exists in prior work; what is original here is the
  *failure-aware gate* on top of it).

## What the originality argument rests on

Paper 2's originality argument does not rest on a comparator-beating
performance number. It rests on three artefacts:

1. The pre-registered failure-aware gate (machine-readable, executable,
   reproducible).
2. The audited end-to-end run that triggered the gate honestly.
3. The negative-result discipline (claim-audit, citation-audit, freeze
   invariant) that ensures the report cannot drift into overclaim.

All three are present in the repository and can be re-verified by anyone
re-running the pre-registered pipeline.
