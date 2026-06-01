# Exhibit Description

> Draft exhibit description for evidentiary use. Factual only; subject to attorney
> review. Asserts no publication, peer review, citation, deployment, compliance, or
> model superiority.

**Exhibit title:** Research Manuscript and Reproducible Artifact: *Context-Aware
Vulnerability Prioritization for Government Endpoint Fleets*.

## What the exhibit contains

- A complete research **manuscript** (Abstract + 17 sections) in submission-style
  Markdown and as an ACM `acmart` LaTeX scaffold (not yet submitted or published).
- A **reference software implementation** (Python package `paper1`) with an
  automated test suite (currently 743 passing tests), configuration files, and
  Make targets.
- A **frozen result artifact** (`results/primary_full_v1/`): 30 seeds, 13
  prioritization strategies, 4,290 per-seed metric rows, 390 hash-chain-valid audit
  logs, sealed with a content-addressed freeze manifest (per-file SHA-256) that
  verifies.
- **Generated tables (7) and figures (5)** produced solely from the frozen
  artifact, with an index and a reproducibility appendix.
- Supporting **audits**: claim-safety audit, citation audit, references worklist,
  and a submission checklist.

## Why it supports original contribution

The exhibit demonstrates the independent design and construction of a reproducible,
audit-evidence-producing benchmark for vulnerability-host pair prioritization under
operational capacity constraints — an original methodological framework (pair-level
decision unit, tamper-evident decision records, capacity-constrained scheduling
simulation, and a freeze/verify integrity pipeline). The artifact is internally
verifiable: numbers trace to a frozen, integrity-checked result, and the pipeline
is deterministic and tested.

## How it relates to the beneficiary's expertise

It evidences hands-on expertise across cybersecurity, vulnerability management,
security-operations modeling, and reproducible research engineering, including the
ability to specify, build, test, and document a large multi-component research
system and to report results with scientific integrity.

## Limitations (stated for accuracy)

Evaluation is on a synthetic, public-sector-shaped fleet with bundled toy fixtures
and uncalibrated (placeholder) weights; the empirical result is **neutral** (the
proposed model did not outperform the EPSS baseline or a random ordering); there is
no real-world or government deployment; no compliance is established; and the
manuscript is not submitted, peer-reviewed, accepted, or published.

## Supporting files

`paper/manuscript/`, `paper/acm/`, `paper/tables/`, `paper/figures/`,
`paper/closeout/`, `results/primary_full_v1/` (with `FREEZE_MANIFEST.json` and
`report/report_manifest.json`), and the `paper1` source repository with its tests.
