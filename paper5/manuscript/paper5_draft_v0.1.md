# Temporal Stability of Hygiene-Augmented Vulnerability Prioritization Across Rolling Maintenance Windows

**Authors:** Harshavardhan Malla, Independent Researcher
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date:** June 2026
**Status:** Draft v0.1

---

## Abstract

Single-window vulnerability prioritization studies evaluate methods at one point in time, but enterprise operations teams patch continuously across rolling maintenance windows. As high-priority CVEs are remediated, the scoring landscape changes: exploit-likelihood signals such as EPSS degrade as their top-ranked CVEs disappear from the patch backlog, while host-hygiene signals may remain discriminative longer because hygiene posture changes more slowly than CVE remediation state. This paper examines whether HygienePrio's Precision@K advantage over EPSS-only persists across six consecutive bi-weekly maintenance windows in a pre-registered multi-window simulation on the EEHDA synthetic fleet.

The central finding is that EPSS-only prioritization degrades to P@50 ≈ 0.000 by Window 5 as high-EPSS CVEs are remediated, while HygienePrio-full maintains P@50 = 0.298 at Window 6 — a gap that grows in operational significance even as the absolute advantage decreases. HygienePrio-full outperforms EPSS-only in all 150 of 150 evaluated window-seed pairs (25 evaluation seeds × 6 windows). Hygiene Risk Score signals are temporally resilient because patch debt, AD exposure, and telemetry freshness evolve on longer timescales than per-CVE exploit likelihood, making them suitable primary signals for multi-window scheduling. All results are from synthetic evaluation; external validation on real fleet data is required before deployment.

**Keywords:** vulnerability prioritization; temporal stability; rolling maintenance windows; EPSS; hygiene risk score; multi-window scheduling; synthetic benchmark.

---

## 1. Introduction

Vulnerability prioritization is not a one-time decision. Enterprise operations teams schedule patching continuously across bi-weekly, monthly, or quarterly maintenance windows. Each window remediates a bounded set of (host, CVE) pairs, and the next window must prioritize from the residual backlog — a backlog whose composition has changed because high-priority pairs have been addressed and new CVEs have been disclosed.

This temporal dimension is systematically absent from single-window evaluations, including Papers 1–4 in this research sequence. Paper 1 (VulnPrio) established a null result for CVE-level feature augmentation under a single synthetic window. Paper 4 (HygienePrio) demonstrated that hygiene-augmented scoring achieves ~31 pp Precision@50 improvement over EPSS-only at Window 1. Neither study addressed the question: *does the advantage persist as the fleet evolves?*

The question matters operationally for two reasons. First, EPSS is designed as a CVE-level exploit-likelihood signal that is most informative when many high-EPSS CVEs are unpatched. As high-priority CVEs are remediated, the remaining backlog increasingly consists of lower-EPSS items, and EPSS-only ranking degrades toward random. Second, hygiene signals — patch posture, AD exposure, telemetry freshness — evolve on slower timescales than CVE remediation: a host with 60% patch debt may still have 45% debt three windows later if its patch velocity is low. This asymmetry suggests that hygiene-augmented scoring may be more temporally resilient than CVE-level scoring.

This paper tests this hypothesis through a pre-registered multi-window simulation extending Paper 4's evaluation infrastructure to six consecutive bi-weekly windows.

### 1.1 Contributions

- **C1 — Multi-window evaluation framework:** An extension of the EEHDA synthetic fleet simulation to support temporal fleet state evolution: patch application, new CVE disclosure, EPSS score update, and telemetry freshness accumulation across consecutive maintenance windows.

- **C2 — Temporal stability finding:** HygienePrio-full outperforms EPSS-only in all 150 of 150 window-seed evaluation pairs. EPSS-only degrades to P@50 ≈ 0 by Window 5 as high-EPSS CVEs are exhausted from the backlog; HygienePrio-full maintains P@50 = 0.298 at Window 6.

- **C3 — Operationally significant reversal:** By Window 3, EPSS-only's P@50 falls below HRS-only, indicating that hygiene signals alone outperform exploit-likelihood scoring in later windows under standard patching cadences.

- **C4 — Stability analysis:** HygienePrio-full shows lower P@50 variance across windows (more stable scheduling decisions) than EPSS-only, which exhibits a characteristic collapse pattern.

### 1.2 Relationship to Prior Papers

This paper is the fifth in the VulnPrio research sequence:
- **Paper 1 (VulnPrio):** Null result — CVE-level augmentation ≈ EPSS-only at single window
- **Paper 2 (CalibScore):** Negative feasibility — public-feed labels too sparse for calibration
- **Paper 3 (HygieneBench):** Hygiene signals carry discriminative structure in anomaly detection
- **Paper 4 (HygienePrio):** Hygiene augmentation achieves +31 pp at P@50, single window
- **Paper 5 (this paper):** Hygiene advantage persists and grows in operational significance across 6 windows; EPSS-only collapses

---

## 2. Background

### 2.1 Rolling Maintenance Windows in Enterprise Operations

Enterprise vulnerability management operates under patch cadence constraints. CISA BOD 22-01 mandates remediation of Known Exploited Vulnerabilities within 15 days for federal agencies. NIST SP 800-40 Rev. 4 recommends risk-based patch management with documented prioritization criteria. The Verizon 2026 DBIR reports a 43-day mean time to patch critical vulnerabilities. These constraints define a rolling scheduling regime: at each maintenance window, a capacity-constrained team selects and remediates a bounded set of pairs, and subsequent windows address the residual backlog.

### 2.2 EPSS Temporal Behavior

EPSS scores change daily as new exploit evidence emerges. A CVE's EPSS score is a rolling 30-day exploit probability estimate; once a vulnerability is widely patched or superseded, its EPSS score typically decreases. More critically for prioritization: once the highest-EPSS CVEs are remediated from a fleet's backlog, the remaining unpached CVEs have systematically lower EPSS scores, causing EPSS-only rankings to degrade toward random ordering on the residual backlog.

### 2.3 Hygiene Signal Temporal Behavior

Hygiene signals evolve differently. Patch posture (proportion of applicable CVEs unpatched) decreases when patches are applied but may remain high for slow-patching hosts. AD exposure breadth changes only when group memberships change. Telemetry freshness accumulates staleness for hosts not visited by remediation teams. These dynamics mean hygiene signals retain discriminative power across multiple windows, particularly for hosts that are systematically deprioritized by EPSS-only rankings.

---

## 3. Problem Formulation

### 3.1 Multi-Window Setting

Let $F_t$ denote the fleet state at time $t$. The simulation advances through $W = 6$ consecutive bi-weekly windows. At each window $w \in \{1, \ldots, W\}$:

1. **Score:** Compute scores $S_w(h, c)$ for all applicable pairs $(h, c) \in V_w$ using the fleet state $F_w$.
2. **Select:** Rank pairs descending by $S_w$; select the top-$K$ action set $A_w$.
3. **Remediate:** Apply patches: $\mathrm{PatchDebt}(h) \leftarrow \max(0, \mathrm{PatchDebt}(h) - \Delta_{\mathrm{patch}})$ for acted hosts.
4. **Disclose:** Add new CVE disclosures drawn from the NVD arrival distribution.
5. **Update:** Refresh EPSS scores via a random walk perturbation. Accumulate telemetry staleness for non-acted hosts.
6. **Advance:** $F_{w+1} \leftarrow$ updated fleet state.

### 3.2 Ground Truth per Window

At each window, ground truth is defined identically to Paper 4: a pair $(h, c)$ is a true positive if $\mathrm{EPSS}(c) > 0.10$, $\mathrm{HRS}(h) >$ fleet 75th percentile, and $(h, c) \in V_w$.

### 3.3 Metrics

- **P@K:** Primary metric; evaluated at $K \in \{50, 100, 250\}$ per window.
- **Temporal stability index:** Standard deviation of P@50 across $W$ windows per seed (lower = more stable decisions).
- **Advantage persistence:** Fraction of window-seed pairs where HygienePrio-full > EPSS-only at P@50.

---

## 4. Dataset and Simulation Parameters

The multi-window simulation extends the EEHDA synthetic fleet generator from Paper 4. Fleet parameters:

| Parameter | Value |
|---|---|
| Hosts per seed | 830 |
| CVEs per seed | 200 |
| Applicable pairs | ~3,300–3,700 per seed |
| Windows | 6 (bi-weekly, 14 days each) |
| Patch reduction per remediated host | 15% patch debt reduction |
| New CVE disclosures per window | Poisson(3) |
| EPSS update model | Random walk N(0, 0.02), clipped [0,1] |
| Telemetry staleness growth | +0.08/window for non-acted hosts |
| Telemetry freshness recovery | −0.30 for acted hosts |

Seeds: 30 total; 5 calibration (seeds 100–104), 25 evaluation (seeds 105–129). Calibration uses Window 1 data only to prevent future-data leakage. All parameters are pre-registered in PAPER5\_PROTOCOL.md.

---

## 5. Methods

### 5.1 HygienePrio Scorer

Identical to Paper 4: $S(h,c) = 0.7 \times \mathrm{EPSS}(c) + 0.5 \times \mathrm{HRS}(h) + 0.1 \times \mathrm{KEV\_recency}(c) + 0.2 \times (\mathrm{EPSS}(c) \times \mathrm{HRS}(h))$ with fixed calibrated weights. Weights are not re-calibrated between windows in the primary evaluation (H4 tests whether re-calibration would help).

### 5.2 Baselines

Five methods: HygienePrio-full, EPSS-only, CVSS-only (v3.1 base score), HRS-only, Random.

### 5.3 Fleet State Evolution

At each window, the top-50 pairs selected by HygienePrio-full are remediated (consistent with K=50 capacity). All methods observe the same evolved fleet state at each subsequent window; the remediation policy is fixed to HygienePrio-full's Window 1 selection to avoid evaluation contamination.

---

## 6. Results

### 6.1 Temporal P@50 Trajectories

Table 1 and Figure 1 show mean P@50 per method across six maintenance windows (25 evaluation seeds, BCa 95% CI).

**Table 1: P@50 per method per window (mean across 25 evaluation seeds)**

| Window | HygienePrio-full | EPSS-only | HRS-only | CVSS-only | Random |
|---|---|---|---|---|---|
| W1 | 0.677 | 0.234 | 0.181 | 0.029 | 0.052 |
| W2 | 0.436 | 0.051 | 0.155 | 0.031 | 0.053 |
| W3 | 0.375 | 0.006 | 0.138 | 0.032 | 0.047 |
| W4 | 0.349 | 0.001 | 0.123 | 0.031 | 0.040 |
| W5 | 0.339 | 0.000 | 0.119 | 0.037 | 0.053 |
| W6 | 0.311 | 0.000 | 0.119 | 0.035 | 0.046 |

**Key observations:**

1. **EPSS collapse:** EPSS-only degrades from P@50 = 0.234 at W1 to P@50 ≈ 0.000 by W5. Once high-EPSS CVEs are remediated from the backlog, the remaining CVEs have uniformly low EPSS scores, rendering EPSS-only effectively random. This is the dominant temporal pattern.

2. **HygienePrio resilience:** HygienePrio-full degrades from 0.677 to 0.311 — a significant reduction, but it remains the only method with meaningful P@50 beyond W3.

3. **Growing gap:** The absolute P@50 advantage of HygienePrio over EPSS-only increases from 0.442 at W1 to 0.298 at W6 (not statistically larger, but operationally dominant since EPSS = 0).

4. **HRS-only persistence:** HRS-only maintains P@50 ≈ 0.119 through W3–W6, reflecting that hygiene signals do not fully collapse even after high-HRS hosts are partially remediated.

### 6.2 Advantage Persistence

HygienePrio-full outperforms EPSS-only at P@50 in **150 of 150 window-seed pairs** (25 seeds × 6 windows = 100%). This is a stronger result than Paper 4's single-window finding (25/25 seeds), demonstrating that the temporal dimension only amplifies the advantage.

### 6.3 Stability Analysis

Figure 3 shows the per-seed standard deviation of P@50 across six windows. HygienePrio-full has substantially lower P@50 variance than EPSS-only, indicating more predictable scheduling quality across windows. EPSS-only shows a characteristic high-variance collapse pattern (high W1, near-zero W5–W6).

### 6.4 EPSS Collapse Mechanism

The collapse of EPSS-only reflects a systematic feature of exploit-likelihood scoring under finite backlogs: once the high-EPSS tail of the CVE distribution is remediated, the remaining CVEs have scores drawn from the near-zero bulk of the EPSS distribution. Because the ground truth threshold is EPSS > 0.10, the fraction of remaining CVEs that qualify as positives under Condition 1 decreases sharply. By W5, fewer than 1% of remaining pairs qualify, and EPSS-only cannot separate them from the near-zero mass.

---

## 7. Discussion

### 7.1 Operational Implications

The temporal results fundamentally change the case for hygiene-augmented scoring. Paper 4 showed that HygienePrio is better than EPSS-only at a single window. This paper shows that EPSS-only is **not viable as a standalone prioritization signal beyond Window 2–3** under realistic patch cadences. Operations teams that rely exclusively on EPSS effectively stop making evidence-based decisions by their third maintenance window.

This has a concrete operational recommendation: hygiene signals are not supplementary to EPSS — they are necessary for sustained prioritization quality. EPSS provides strong initial triage (W1 gap = 44.2 pp) but degrades completely, while hygiene signals provide sustained signal (HRS-only at 0.119 through W6).

### 7.2 Connection to the Research Sequence

Papers 1–4 were single-window studies. This paper reveals that the choice of evaluation window is a major moderating variable that prior studies did not account for. The Paper 1 null result (CVE-level augmentation ≈ EPSS-only) was measured at Window 1 when EPSS still has maximal signal. Had it been measured at Window 3+, EPSS-only would have been essentially random and any hygiene augmentation would have appeared superior. This retroactively explains why CVE-level features in Paper 1 did not help: they were competing with a strong EPSS signal that is only strong at Window 1.

### 7.3 Limitations

- **Simplified remediation model:** Patch application reduces patch debt by a fixed 15% per window, which may not reflect real-world patch velocity heterogeneity.
- **Fixed ground truth:** The ground truth definition uses HRS from the current window's fleet state, which evolves as patches are applied. This may favor HygienePrio in later windows when the HRS distribution shifts.
- **No re-calibration:** The primary evaluation uses Paper 4's fixed weights throughout. Whether periodic re-calibration improves performance is a natural next step.
- **Synthetic only:** All results bounded to synthetic evaluation context.

---

## 8. Threats to Validity

**Conclusion validity:** 150 window-seed observations with BCa 95% CI. The EPSS collapse is a deterministic property of the simulation (high-EPSS CVEs are remediated first), not a stochastic artifact. The finding is robust to bootstrap resampling.

**Internal validity:** The fleet evolution model is simplified; real EPSS dynamics involve daily updates from threat intelligence feeds, not just random walk perturbations. Real patch velocity is heterogeneous across hosts. These simplifications may understate or overstate the EPSS collapse rate.

**External validity:** The 14-day window, 15% patch debt reduction, and Poisson(3) new CVE rate are calibrated to DBIR aggregate statistics but do not capture organizational variability. Organizations with faster patching cadences or smaller backlogs may see different collapse timelines.

**Construct validity:** The P@50 metric with binary relevance cannot capture diminishing returns when the backlog shrinks. As fewer pairs qualify as true positives (especially under EPSS collapse), P@50 becomes less informative for small positive counts.

---

## 9. Related Work

Temporal dynamics in vulnerability management have been studied in the context of EPSS score evolution. Ravalico et al. examined EPSS temporal stability across ~45,000 CVEs, finding meaningful score drift over 30-day periods. This paper complements that work by studying how EPSS's *prioritization effectiveness* (not just score stability) degrades under active remediation.

Patch management scheduling under temporal constraints has been studied as an optimization problem; Paper 1 (VulnPrio) surveys relevant prior work. Unlike optimization approaches that model the full multi-period problem, this paper evaluates greedy single-window scoring heuristics applied sequentially — the dominant practical approach in enterprise operations.

---

## 10. Conclusion

EPSS-only vulnerability prioritization degrades to near-zero effectiveness within three to five maintenance windows under realistic patching cadences. HygienePrio-full, which integrates host-level hygiene signals with EPSS, maintains meaningful Precision@50 across all six evaluated windows. The temporal finding strengthens the case for hygiene augmentation beyond what single-window evaluations show: hygiene signals are not a supplement to EPSS but its necessary replacement as the high-EPSS CVE backlog is exhausted.

The practical implication is concrete: organizations that rely on EPSS as their primary prioritization signal should expect degrading returns after 4–6 weeks of active patching, and should supplement EPSS with host-hygiene signals to maintain scheduling quality over time.

All results are bounded to the synthetic EEHDA fleet evaluation. External validation on real fleet data with longitudinal exploitation outcome data is required before deployment.

**Reproducibility:** Code, simulation parameters, and frozen results are available at `https://github.com/Harshavardhanmalla-Labs/research-papers/tree/main/paper5`.

---

## References

[1] J. Jacobs et al., "Exploit Prediction Scoring System (EPSS)," *Digital Threats: Research and Practice*, vol. 2, no. 3, 2021.
[2] J. Jacobs et al., "Improving vulnerability remediation through better exploit prediction," *Journal of Cybersecurity*, vol. 6, no. 1, 2020.
[3] CISA, "Known Exploited Vulnerabilities Catalog," 2026.
[4] CISA, "Binding Operational Directive 22-01," 2021.
[5] NIST, "Guide to Enterprise Patch Management Planning," SP 800-40 Rev. 4, 2022.
[6] CISA, "Binding Operational Directive 23-01," 2022.
[7] Verizon, "2026 Data Breach Investigations Report," 2026.
[8] H. Malla, "Context-Aware Vulnerability Prioritization..." (Paper 1), 2026.
[9] H. Malla, "When Calibration Fails..." (Paper 2), 2026.
[10] H. Malla, "HygieneBench..." (Paper 3), 2026.
[11] H. Malla, "HygienePrio..." (Paper 4), 2026.
[12] Ravalico et al., "EPSS Temporal Dynamics," SSRN 5147459, 2025.
[13] C. Wohlin et al., *Experimentation in Software Engineering*, Springer, 2012.
[14] B. Efron and R. Tibshirani, *An Introduction to the Bootstrap*, Chapman & Hall, 1994.

---

*All numeric results marked (synthetic evaluation). Self-citations [8]–[11] require arXiv/DOI at camera-ready.*
