# Paper 5 — Pre-Registration Protocol

**Title:** Temporal Stability of Hygiene-Augmented Vulnerability Prioritization Across Rolling Maintenance Windows

**Date pre-registered:** 2026-06-04
**Author:** Harshavardhan Malla, Independent Researcher

---

## 1. Research Questions

**RQ1 (Temporal stability):** Does HygienePrio's Precision@K advantage over EPSS-only persist across multiple consecutive maintenance windows as the fleet state evolves (patches applied, new CVEs disclosed, telemetry refreshed)?

**RQ2 (Degradation rate):** At what rate does HygienePrio's advantage attenuate as high-HRS hosts receive remediation (reducing HRS variance)?

**RQ3 (Re-calibration frequency):** How often must the HygienePrio weights be re-calibrated to maintain performance comparable to the initial calibration?

**RQ4 (EHD consistency):** Are the P@K findings from Paper 4 consistent with the Expected Exploited Host-Days (EHD) metric from Paper 1 under multi-window evaluation?

---

## 2. Study Design

### 2.1 Multi-Window Simulation

Each seed generates a fleet at time T=0. The simulation runs W=6 consecutive bi-weekly maintenance windows. At each window:

1. Compute HRS(h) for all hosts from current fleet state
2. Score all pairs with HygienePrio and baselines
3. Select top-K pairs for remediation
4. Apply remediation: mark selected pairs as patched, update patch_state
5. Disclose new CVEs (drawn from NVD distribution, 14-day window)
6. Refresh EPSS scores (daily snapshot + random walk perturbation)
7. Update telemetry freshness (hosts not acted on accumulate staleness)
8. Advance time by 14 days

### 2.2 Evaluation Metrics

- **P@K** at K=50,100,250 per window (primary; consistent with Paper 4)
- **EHD** per window (primary Paper 1 metric; enables cross-paper comparison)
- **Stability index:** Mean absolute deviation of P@50 across W windows per seed
- **Advantage persistence:** Fraction of windows where HygienePrio-full > EPSS-only

### 2.3 Seeds

- 30 seeds total; 5 calibration, 25 evaluation (same split as Paper 4)
- Calibration uses only Window 1 data (to avoid future-data leakage)

### 2.4 Baselines

Same 9 methods as Paper 4. Additionally:
- **HygienePrio-recalibrated:** Re-calibrates weights at each window using the most recent 5 seeds' Window N data (tests whether recalibration helps)
- **EPSS-dynamic:** Uses the updated EPSS score at each window (not a single snapshot)

---

## 3. Primary Hypotheses

**H1:** HygienePrio-full maintains P@50 > EPSS-only (non-overlapping BCa CIs) for at least 4 of 6 windows.

**H2:** The advantage is largest at Window 1 (before high-HRS hosts are remediated) and attenuates monotonically.

**H3:** EHD findings are directionally consistent with P@K findings: HygienePrio-full produces lower EHD than EPSS-only in the majority of windows and seeds.

**H4:** Re-calibration at each window does not substantially outperform fixed-weight HygienePrio (< 5 pp improvement at P@50), suggesting the initial calibration is sufficiently stable.

---

## 4. Analysis Plan

- BCa bootstrap CIs (10,000 resamples) across 25 evaluation seeds per window
- Report P@K and EHD time-series plots (Window 1–6)
- Report stability index distribution across seeds
- All comparisons pre-registered; no post-hoc method additions

---

## 5. Scope Limitations

- Synthetic fleet only; no real deployment data
- CVE disclosure model is simplified (Poisson draws from NVD distribution)
- Attacker behavior is not modeled; KEV recency does not evolve dynamically
- Patch application is instantaneous in simulation; no latency model
