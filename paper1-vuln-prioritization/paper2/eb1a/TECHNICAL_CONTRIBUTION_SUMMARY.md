# Paper 2 — Technical Contribution Summary

Audience: a technically literate reviewer (cybersecurity researcher,
applied-statistics reviewer, attorney's technical advisor). Scope: what the
artefact actually does, with concrete numbers.

## Setting

Vulnerability prioritization research routinely fits per-feature weights
that combine signals such as CVSS base, EPSS probability, KEV membership, and
asset-context indicators, and ranks per-CVE-per-host pairs by the resulting
score. Two questions sit underneath this practice:

1. Are public exploit-signal feeds dense enough — under a leakage-safe label
   — to support defensible fitting of per-feature weights?
2. If they are not, what should the methodology do instead?

Paper 2 addresses both.

## Contribution 1 — Failure-aware multi-t0 calibration gate

The gate operates over a set of monthly time origins (`t0`) inside a chosen
universe window. For each `t0` the design takes a leakage-safe label window
of horizon `h_days` *after* `t0`, counts unique distinct positive CVEs across
all `t0`, and decides whether the count meets a pre-registered minimum. If
not, the gate refuses to fit weights, records the count and reason, and
emits the trigger as a machine-readable stop-rule event (`K1`).

Concrete values on this dataset:

| Quantity | Value | Source field |
|---|---|---|
| Universe window | 2021-09-01 to 2025-02-01 | `feasibility/probe_v2_multit0/summary.json` `aggregate.universe_*` |
| Number of `t0` windows | 18 | `aggregate.n_windows` |
| `h_days` per `t0` | 30 | `aggregate.h_days` |
| Catalog-matched CVEs | 2,688 | `aggregate.catalog_matched_cves` |
| Unique positive distinct CVEs | 7 | `aggregate.unique_positive_cves` |
| Pre-registered minimum | 50 | `calibration.reason` |
| Decision | calibration not attempted | `calibration.attempted = false`; `decision = "PIVOT_away_from_calibration"` |

The gate is a methodology contribution: it tells the rest of the pipeline
that fitting is not defensible on this label density, and the pipeline obeys.
Per-feature weight fitting does not run. No fitted weights enter any
downstream comparison.

## Contribution 2 — Pre-registered sparse-label methodology

Nine fix documents (F1–F9, locked before any data was collected) commit the
study to a fixed set of design priors (six weight vectors:
`w_uniform`, `w_paper1_placeholder`, `w_epss_dominant`, `w_cvss_dominant`,
`w_kev_dominant`, `w_context_dominant`), a fixed set of stop rules (28 rules
across the K- / S- / SM- families), fixed claim bindings, a fixed inference
policy (effect-size threshold 5,000 host-days; MDE-d ≈ 0.5292 at n = 30 per
cell), a fixed cell enumeration (48 cells), and a fixed compute envelope.
The pre-registration is the source-of-truth; downstream code reads it.

The Paper 1 frozen artefact is enforced as an invariant: a SHA-256 manifest
witness (`750e144b…b022833`) is required to be byte-equal before and after
every Paper 2 batch, and the same identifier is attached to every metric
row written by the runner.

## Contribution 3 — Audited primary run

| Quantity | Value | Source field |
|---|---|---|
| Pilot batches | 4 | `audit/pilot_gate_decision.json` |
| Pilot seed-runs | 288 | same |
| Primary batches | 4 | `audit/primary_complete.json` |
| Primary cells | 48 | same |
| Primary seed-runs | 1,440 | same |
| Primary metric rows | 8,640 | sum of `per_batch[*].per_row_total` |
| Per-row freeze-witness coverage | 100% | `all_rows_have_freeze_witness_id = true` |
| Stop rules triggered during execution | K1, K3, S-A | `stop_rules_triggered` |
| Hard-halt rules triggered | none | `hard_halt_triggered` |
| Completion status | PRIMARY_COMPLETE_VALID | `status` |

## Contribution 4 — Confirmatory sensitivity framework with honest demotion

Because calibration was not attempted, the remaining study is a fixed-prior
sensitivity sweep across four axes: capacity (A1), weight family (A3),
feature ablation (A5), blackout (A6). The framework computes per-axis
within-cell coefficient of variation (CV_within) and across-cell CV
(CV_across) and demotes any axis where CV_within > CV_across (rule K8). On
this dataset K8 fires on **all four axes**, so all four are reported as
descriptive only. The framework records that demotion in
`audit/post_run_stop_rule_evaluation.json` and the manuscript reflects it.

The K2 rule (paired BCa CI around |median Δ EHD| crosses zero or stays
inside ± 5,000 host-days per axis) does **not** fire on any measured axis at
the cell-mean test, but every axis is descriptively demoted by K8 anyway.
The K7 rule (catalog stability under product perturbations) is **SKIPPED**
because no perturbation data was generated; the manuscript records that as a
limitation.

## Contribution 5 — Reproducible artefact chain

- `paper2_runtime/` Python package: 13 modules (stop rules, freeze
  invariant, cell loader, batch loader, weights, inference policy, run
  planner, batch runner, pilot gate, primary gate, aggregate, inference,
  figures, post-run stop rules, Step-9 audit).
- 154 paper2 tests under `tests/test_paper2_*.py`; all pass.
- Pre-registered batches `paper2/design/STEP3_17_PLANNED_BATCHES.yaml` and
  cell CSV.
- Step-9 outputs: 19 aggregation tables, 12 inference tables, 14 figures
  (7 PNG + 7 PDF), 3 post-run files, 2 audit files.
- Manuscript draft `paper2/manuscript/paper2_full_draft.md` and LaTeX
  scaffold `paper2/submission/cset/` (`main.tex` + 16 section files + 15
  verified BibTeX entries).
- Claim-audit script `scripts/paper2_claim_audit.py` (forbidden-phrase
  scanner with proximity rules).

## Reproducibility statement

Every numeric quantity in this file is traceable to a JSON field or CSV cell
in the repository, listed in `paper2/submission/REPRODUCIBILITY_APPENDIX.md`.
No quantity here was generated for this document; all were copied from
artefacts emitted by the pre-registered pipeline.
