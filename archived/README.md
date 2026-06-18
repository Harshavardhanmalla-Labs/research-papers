# Archived / Parked Experiments

These four directories were written as standalone papers during exploratory
loop runs (2026-06-04 / 06-05) and later **parked** when the research plan
was consolidated back to the 9 distinct topics.

Each directory is a complete standalone paper (protocol, code, frozen CSVs,
LaTeX + compiled PDF) but is **not part of the primary submission program**.
They are kept here for reproducibility and in case any direction is
resurrected as a follow-up.

## What's here

| Directory | What it explored | Old paper # |
|---|---|---|
| `Exp_AdaptiveSingleTau/` | Single-threshold magnitude detector (τ=0.05) — does it avoid the K=200 hazard? | Paper 10 (old) |
| `Exp_TauSweep/` | Sweep over τ∈{0.02…0.10} — does any τ reach the H1/H2 feasibility region? | Paper 11 (old) |
| `Exp_CapacityAware/` | Per-K threshold vector τ_K — does it reach feasibility? | Paper 12 (old) |
| `Exp_CUSUM/` | One-sided CUSUM (k=0.04, h=0.10) — first method to beat static gate at K=200 (+0.9 pp) | Paper 13 (old) |

## Active papers (not here)

The current submission-ready papers live at the repo root:

```
paper1-vuln-prioritization/   Paper 1 — VulnPrio  (isolated)
paper1-vuln-prioritization/   Paper 2 — CalibScore (isolated)
paper3/                        Paper 3 — HygieneBench    (ACM AISec)
paper4/                        Paper 4 — HygienePrio     (IEEE TNSM)
paper5/                        Paper 5 — Temporal Stability (IEEE TNSM)
paper6/                        Paper 6 — Capacity-Indexed Decay (IEEE TNSM)
paper7/                        Paper 7 — Online Recalibration lag-1 (IEEE TNSM)
paper8/                        Paper 8 — Multi-History Smoothing (IEEE TNSM)
paper9/                        Paper 9 — Self-Trajectory Evaluation (IEEE TNSM)
paper10/                       Paper 10 — AutoHeal (IEEE TNSM)
```
