# Paper 7 — Pre-Registration Protocol (Consolidated)

**Working title:** Online Recalibration for Hygiene-Augmented Vulnerability
Prioritization: A Pre-Registered Comparison of Six Procedures

**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**First-experiment lock date:** 2026-06-04 (E1 lag-1 protocol)
**Last-experiment lock date:** 2026-06-05 (E6 CUSUM protocol)
**Builds on:** Paper 4 (HygienePrio scorer), Paper 5 (multi-window simulator),
Paper 6 ((K, λ) sweep showing K=200 absolute collapse).

---

## 1. Motivation

Paper 5's H3 ablation showed that grid-searching scorer weights on the
calibration seeds at the same window being scored (an offline-peek
procedure) lifts Precision@50 by up to +21.3 pp at W2 over the fixed
Paper 4 weights at the canonical (K=50, λ=3) operating point.
Paper 5 noted the procedure is not deployable: real operations
teams cannot peek into the current window when scoring it.

Paper 6 showed that at high capacity (K ∈ {100, 200}) HygienePrio's
absolute floor collapses regardless of scoring weights. The question
this paper asks is whether any deployable recalibration procedure can
(a) approach Paper 5's offline ceiling at moderate capacity and
(b) avoid the K=200 absolute collapse at high capacity.

We evaluate six procedures in a pre-registered sequence, each one
designed to address the failure mode identified by the previous one:

**E1 — Lag-1 online (Paper 7 original protocol).** Refit on
calibration seeds at window w−1; apply at window w. Deployable.

**E2 — Multi-window smoothing.** EWMA-3 and trailing-mean-3 over
the calibration-seed history. Addresses E1 K=200 hazard?

**E3 — Single-τ adaptive change-point.** Magnitude detector on the
calibration-target shift |Δ_w|; revert to fixed weights when fired.

**E4 — τ sensitivity sweep.** Sweeps τ over {0.02, 0.03, 0.05, 0.075,
0.10} to characterise the H1/H2 Pareto frontier of E3.

**E5 — Capacity-aware τ vector.** Pre-registered τ_K = {50: 0.20,
100: 0.05, 200: 0.02}. Addresses E4 negative feasibility result.

**E6 — One-sided CUSUM.** Accumulator detector with pre-registered
(k=0.04, h=0.10). Addresses E5 static-gate collapse at K=200.

## 2. Pre-registered hypotheses (per experiment)

The full hypothesis ledger is below; each was locked before the
corresponding experiment's evaluation seeds were inspected. Hypotheses
H1.x belong to experiment x, etc.

**E1 (lag-1) — locked 2026-06-04:**
- H1.E1: Online ≥ fixed at every (cell, window) within 1 pp.
- H2.E1: Online ≤ offline (Paper 5 H3 ceiling) at every (cell, window).
- H3.E1: Online recovers ≥50% of offline gap at K∈{100,200}, w∈{4,5,6}.

**E2 (smoothing) — locked 2026-06-04:**
- H1.E2: EWMA-3 ≥ fixed at K=200 every w (no hazard).
- H2.E2: |EWMA-3 − lag-1| ≤ 2 pp at K∈{50,100}.
- H3.E2: |EWMA-3 − trail3| ≤ 2 pp everywhere.
- H4.E2: EWMA-3 K=200 recovery ratio ≥ 0.5.

**E3 (single-τ adaptive) — locked 2026-06-04:**
- H1.E3: Adaptive ≥ fixed at K=200 every w.
- H2.E3: |Adaptive − lag-1| ≤ 2 pp at K∈{50,100}.
- H3.E3: Adaptive rescues high-K cells.
- H4.E3: Adaptive K=200 cell mean ≥ gated cell mean.

**E4 (τ sweep) — locked 2026-06-04:**
- H1.E4: Worst K=200 hazard monotone non-decreasing in τ.
- H2.E4: K=50 cost monotone non-increasing in τ.
- H3.E4: ∃τ satisfying both Paper-5/E3 tolerances.
- H4.E4: Fire fraction monotone non-decreasing in τ.

**E5 (capacity-aware) — locked 2026-06-04:**
- H1.E5: Capacity-aware reaches joint feasibility region.
- H2.E5: Capacity-aware ≥ adaptive05 within 1 pp.
- H3.E5: Fire fraction monotone in K (Spearman ≥ 0.8).
- H4.E5: Capacity-aware ≥ gated K=200 by +0.01.

**E6 (CUSUM) — locked 2026-06-05:**
- H1.E6: CUSUM reaches joint feasibility region.
- H2.E6: CUSUM K=200 ≥ gated K=200 by +0.01.
- H3.E6: CUSUM K=200 fires < cap_aware K=200.
- H4.E6: CUSUM K=200 ≥ cap_aware K=200 − 0.01.

## 3. Shared experimental setup

- EEHDA synthetic fleet (Paper 4)
- Paper 5 multi-window simulator, 6 windows
- Capacity K ∈ {50, 100, 200}; arrival rate λ = 3 (E1, E3–E6); E2 holds same
- Calibration seeds 100–104 (5 seeds); evaluation seeds 105–129 (25 seeds)
- Selection policy: HygienePrio-full under fixed weights drives the
  fleet trajectory for ALL strategies; isolates the recalibration
  decision from the selection decision
- Grid for weight search: 108-point (α, β, γ, δ) lattice from Paper 5
- Reporting: 95% percentile bootstrap CIs (10,000 resamples)

## 4. Frozen artifacts

Per-experiment frozen CSVs in `paper7/experiments/0X_*/results/` are
the canonical evidence for every numerical claim in the manuscript.

## 5. Stop rules

For each experiment: if Hk.Ex is rejected, the corresponding
subsection in §7 is rewritten honestly to qualify the claim before
the discussion is drafted, and the next experiment's protocol is
locked accordingly.

## 6. Reproducibility

Each experiment ships with its own `src/` and CLI runner:
```
PYTHONPATH=experiments/01_lag1_src python3 experiments/01_lag1_src/run_temporal.py
PYTHONPATH=experiments/02_smoothing/src python3 experiments/02_smoothing/src/run_multi_history.py
... (one per experiment)
```

## 7. Certification

Each per-experiment protocol was locked before that experiment's
evaluation-seed P@50 was inspected. Any deviation is reported in
the corresponding subsection of §7.

Signed: Harshavardhan Malla, 2026-06-04 / 2026-06-05.
