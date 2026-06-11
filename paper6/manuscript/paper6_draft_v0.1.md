# Capacity-Indexed Decay of Exploit-Likelihood Vulnerability Prioritization

**Authors:** Harshavardhan Malla, Independent Researcher
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date:** June 2026
**Status:** Draft v0.1

---

## Abstract

Paper 5 reported that EPSS-only vulnerability prioritization decays from mean Precision@50 of 0.331 at maintenance Window 1 to 0.034 at Window 6 on the synthetic EEHDA fleet at a single capacity-arrival operating point (K = 50 pairs/window, λ = 3 new CVEs/window). This paper sweeps the two-dimensional grid K ∈ {10, 25, 50, 100, 200} and λ ∈ {1, 3, 6, 12} over six bi-weekly windows on the 25 evaluation seeds inherited from Paper 5, producing 15,000 pre-registered result rows.

Three pre-registered findings are reported honestly. **First**, EPSS-only exhibits a strictly negative decay slope in all 20 cells (mean slope range −0.025 to −0.052 P@50/window); no (K, λ) combination produces a steady-state EPSS regime. **Second**, the predicted monotone scaling of decay with K at fixed λ (H1) and with λ at fixed K (H2) is rejected: Spearman correlations fall below the pre-registered |ρ| ≥ 0.8 threshold across most slices, indicating non-monotone compositional dynamics. **Third, and most importantly, the pre-registered claim that HygienePrio-full retains W6 P@50 ≥ 0.40 across all cells (H4) is rejected.** At K ∈ {100, 200} HygienePrio-full collapses alongside EPSS-only, falling to 0.062 at the most aggressive cell (K = 200, λ = 1). The mechanism is symmetric to EPSS decay: high-throughput remediation exhausts the high-HRS tail of the fleet, after which HygienePrio's host-level signal becomes near-uninformative.

The robustness claim that survives is per-pair: HygienePrio-full outperforms EPSS-only at P@50 in **96.0% of all (cell, seed, window) triples** (2,881/3,000), with per-cell dominance never below 76.7%. In contrast to Paper 5's single-cell conclusion, the operational implication is that hygiene-augmented scoring is a strict improvement over EPSS-only across all capacity regimes studied, but the absolute P@50 floor it provides degrades at high capacity in the same way exploit-likelihood scoring does.

**An external-validity extension (§12) replaces synthetic EPSS/KEV attributes with samples from a frozen real public-data snapshot** (FIRST.org EPSS + CISA KEV, 2026-06-05). The HP > EPSS per-pair persistence drops from 96.0% (synthetic) to 10.0% (real distribution); the structural capacity-collapse finding survives both regimes.

All claims are bounded to the synthetic EEHDA evaluation context; external validation on real fleet telemetry with longitudinal exploitation outcome data is required before any deployment recommendation.

**Keywords:** vulnerability prioritization; EPSS; remediation capacity; CVE arrival rate; multi-window scheduling; sensitivity sweep; reproducibility.

---

The full submission manuscript is at `submission/ieee/main.tex` (compiles to 10 pages via tectonic).
The pre-registration protocol is at `design/PAPER6_PROTOCOL.md`.
Frozen results: `results/primary_sweep_v1/sweep_results.csv` (15,000 rows).
External validity extension data: `real_data/results/real_dist_capacity_sweep.csv` (6,750 rows).
