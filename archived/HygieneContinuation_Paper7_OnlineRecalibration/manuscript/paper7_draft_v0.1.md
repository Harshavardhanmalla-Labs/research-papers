# Rolling-History Online Calibration for Hygiene-Augmented Vulnerability Prioritization

**Authors:** Harshavardhan Malla, Independent Researcher
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date:** June 2026
**Status:** Draft v0.1

---

## Abstract

Paper 5's H3 ablation showed that grid-searching scorer weights on five calibration seeds at the same window being scored, then applying those weights to 25 evaluation seeds at that window, adds up to +21.3 percentage points of Precision@50 over the fixed Paper 4 weights at the canonical (K = 50, λ = 3) cell. The peek procedure is not deployable: it requires future-window data at scoring time. This paper evaluates a deployable alternative: **rolling-history online calibration**, in which weights at window w are fit on calibration-seed data at window w−1 only. We pre-registered three hypotheses and ran a 1,350-row evaluation (K ∈ {50, 100, 200}, λ = 3, six windows, 25 evaluation seeds, three calibration strategies).

**All three pre-registered hypotheses are rejected**, and the rejection pattern is the central scientific contribution.

**First (H1)** — online recalibration does not uniformly match or beat fixed weights: at K = 200 it loses −5.9 pp at W2 and −7.8 pp at W3 relative to the fixed Paper 4 weights. The fleet state changes faster than one-window-lag calibration can track.

**Second (H2)** — online sometimes *exceeds* the offline-peek ceiling: at K = 50, w = 5 online (0.580) beats offline-peek (0.550). The five-seed offline grid search overfits; the one-window lag acts as an implicit regulariser.

**Third (H3)** — online does not rescue HygienePrio at the high-capacity collapse cells documented in Paper 6: at K = 200 the cell-mean recovery ratio across windows w ≥ 2 is **−0.66** (negative).

The operational implication is sharp: rolling-history online recalibration is a beneficial procedure at moderate capacity (K = 50: recovery ratio 1.04, K = 100: 0.99) but is a *net hazard* at high capacity (K = 200: −0.66). Deploy rolling-history online recalibration only when the per-window fleet-state shift is small relative to the lag the recalibration window imposes; at high capacity, keep fixed Paper 4 weights.

All results are bounded to the synthetic EEHDA evaluation context.

**Keywords:** vulnerability prioritization; online calibration; rolling-history learning; EPSS; hygiene risk score; pre-registration; reproducibility.

---

The full submission manuscript is at `submission/ieee/main.tex` (compiles to 7 pages via tectonic).
The pre-registration protocol is at `design/PAPER7_PROTOCOL.md`.
Frozen results: `results/primary_v1/online_calib_results.csv` (1,350 rows).
Supplementary experiments (not for primary submission) under `experiments/0[3-6]_*/` with `experiments/SUPPLEMENTARY.md`.
