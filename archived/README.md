# Archived Papers

All directories here are complete papers (protocol, code, frozen CSVs,
LaTeX + compiled PDF) but are **not part of the current submission program**.
Kept for reproducibility — can be revived as standalone submissions later.

---

## HygienePrio Continuation Papers (archived 2026-06-18)

Papers 5–9 built incrementally on Paper 4 (HygienePrio) and were archived
so the active list shows only one hygiene paper. Each can be submitted
independently in the future as its own contribution.

| Directory | Research question | Pages |
|---|---|---|
| `HygieneContinuation_Paper5_TemporalStability/` | Does HygienePrio's advantage persist across rolling windows? | 8pp |
| `HygieneContinuation_Paper6_CapacityDecay/` | How does the prioritization landscape depend on capacity K and decay λ? | 10pp |
| `HygieneContinuation_Paper7_OnlineRecalibration/` | Can lag-1 online recalibration recover the offline-peek ceiling? | 8pp |
| `HygieneContinuation_Paper8_Smoothing/` | Can EWMA/trailing-mean smoothing fix the K=200 hazard? (falsified) | 7pp |
| `HygieneContinuation_Paper9_SelfTrajectory/` | Is the K=200 collapse intrinsic or a selection-coupling artefact? | 10pp |

---

## Exploratory Experiments (archived 2026-06-11)

Four experiments that were generated during exploratory loop runs and were
never part of the planned research program.

| Directory | What it explored |
|---|---|
| `Exp_AdaptiveSingleTau/` | Single-threshold magnitude detector (τ=0.05) |
| `Exp_TauSweep/` | Sweep over τ∈{0.02…0.10} across feasibility region |
| `Exp_CapacityAware/` | Per-K threshold vector τ_K |
| `Exp_CUSUM/` | One-sided CUSUM — first to beat static gate at K=200 |

---

## Active papers (not here)

The 5 unique submission-ready papers live at the repo root:

```
paper1-vuln-prioritization/   Paper 1 — VulnPrio       (IEEE)     unique topic
paper1-vuln-prioritization/   Paper 2 — CalibScore      (CSET)     unique topic
paper3/                        Paper 3 — HygieneBench   (ACM AISec) unique topic
paper4/                        Paper 4 — HygienePrio    (IEEE TNSM) unique topic
paper10/                       Paper 10 — AutoHeal      (IEEE TNSM) unique topic
```
