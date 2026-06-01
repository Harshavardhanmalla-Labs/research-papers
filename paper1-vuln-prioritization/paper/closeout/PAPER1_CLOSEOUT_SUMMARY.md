# Paper 1 — Closeout Summary

**Title:** Context-Aware Vulnerability Prioritization for Government Endpoint
Fleets: Integrating Exploit Intelligence, Asset Criticality, and Endpoint
Telemetry.
**Author:** Harshavardhan Malla, Independent Researcher.
**Type:** reproducible benchmark / framework paper with a **neutral** empirical
result.

## Contribution summary

A reproducible, audit-evidence-producing benchmark for context-aware
vulnerability-**host pair** prioritization under capacity constraints. It
integrates exploit intelligence (EPSS, KEV, public PoC signals), telemetry-derived
asset criticality, and per-pair local exposure; ranks pairs; schedules under a
fixed per-window capacity with blackout windows, an approval policy, and documented
risk acceptance (a *capacity-constrained scheduling simulation*, not autonomous
remediation); and records every decision in an append-only, hash-chained audit log.
The contribution is the evaluation **infrastructure** (pairs as a traceable decision
unit, audit-evidence records, freeze/verify integrity protocol), not a superior
model.

## Artifact summary

- Reference implementation: Python package `paper1` (Phases 1-14) with tests,
  configs, and Make targets.
- Frozen primary artifact: `results/primary_full_v1/` (freeze verified;
  `FREEZE_MANIFEST.json` + `report/report_manifest.json`).
- Generated, frozen-only tables (7) and figures (5): `paper/tables/`,
  `paper/figures/`; index in `paper/manuscript/table_figure_index.md`.
- Manuscript: `paper/manuscript/paper_submission_draft.md` (clean) and
  `paper_full_draft.md` (annotated); ACM scaffold in `paper/acm/`.

## Empirical result summary

30 seeds x 13 strategies x 11 metrics = 4,290 metric rows; 390 audit logs, all
hash-chain valid; 0 NaN; 0 infinite; capacity 100 with max scheduled 100; strict
inspection passed with zero issues; freeze verified. **Under toy fixtures and
uncalibrated (placeholder) weights, the strategies are statistically
indistinguishable on EHD**: `proposed_full` neither beats the `epss_only` baseline
nor a random ordering (it is nominally worse than random on EHD, capacity
efficiency, and top-10 precision). Total inter-strategy EHD spread is < 0.5% of the
mean, within per-seed standard deviation. KEV-deadline breach is dominated by the
capacity constraint, not the policy. These are reported plainly as a neutral
benchmark result.

## Limitations summary

Synthetic/toy-fixture evaluation; placeholder (uncalibrated) weights;
within-noise differences; no live/production data; no commercial RBVM baseline; no
robustness/sensitivity sweeps yet; feed/label proxy caveats; telemetry
observability assumptions; synthetic-fleet generalization; audit evidence is not
compliance; scheduler models timing not patch success; the oracle is not a strict
EHD lower bound; GBT comparator excluded.

## Target venue

Recommended primary: **ACM Digital Threats: Research and Practice (DTRAP)**;
fallbacks: IEEE Access, then Computers & Security. See
`paper/manuscript/venue_formatting_plan.md`.

## Current readiness

Structurally complete; numbers re-verified against the frozen artifact;
claim-safety clean; ACM scaffold built (not compiled here — no TeX toolchain).
**Ready for venue formatting; not yet ready for submission** (citation
verification, template application, and the calibrated-weights decision remain).
See `PAPER1_READY_STATE.md`, `PAPER1_BLOCKERS.md`, `PAPER1_NEXT_ACTIONS.md`.
