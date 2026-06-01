# Paper 4 — HygienePrio: Design Decision Log

**Date created:** 2026-05-31  
**Version:** 1.0  
**Status:** Active (update as decisions are made)

This log documents the key design decisions made during the development of HygienePrio. Decisions are recorded with rationale, alternatives considered, and the decision outcome. The log exists to support reproducibility, peer review, and EB-1A portfolio documentation.

---

## Decision Index

| ID | Topic | Decision | Date |
|---|---|---|---|
| D01 | Positive result framing | Synthetic-only, hedged language | 2026-05-31 |
| D02 | Ground truth definition | HRS threshold-based, pre-registered | 2026-05-31 |
| D03 | Primary metric | Precision@K (not EHD from Paper 1) | 2026-05-31 |
| D04 | Interaction term inclusion | Include EPSS × HRS term | 2026-05-31 |
| D05 | Calibration/evaluation split | 5 calibration / 25 evaluation seeds | 2026-05-31 |
| D06 | HRS dimension weights | Fixed at pre-registration (not grid-searched) | 2026-05-31 |
| D07 | KEV recency model | Exponential decay, not binary KEV flag | 2026-05-31 |
| D08 | Statistical reporting | BCa CIs, no NHST p-values | 2026-05-31 |
| D09 | Ground truth circularity disclosure | Explicitly acknowledged in §9 | 2026-05-31 |
| D10 | Submission target | IEEE TNSM / ACM DTRAP | 2026-05-31 |
| D11 | Result number hedge | "Illustrative values" note in Table 1 | 2026-05-31 |
| D12 | Paper 1 null result framing | Cited as foundation, not as failure | 2026-05-31 |

---

## Decision Details

### D01 — Positive Result Framing: Synthetic-Only, Hedged Language

**Decision:** All numerical results are qualified as "(synthetic evaluation)". Abstract uses "suggests approximately X% improvement" not "achieves" or "proves". §9 explicitly bounds all claims to the synthetic evaluation context. No generalization to real enterprise fleets is claimed.

**Rationale:** The EEHDA fleet is synthetic. Making unqualified performance claims from synthetic data would be methodologically dishonest and potentially misleading to practitioners. The hedged framing is consistent with Paper 1 and Paper 3's approaches and is standard for synthetic-data security research.

**Alternatives considered:**
- *Strong positive framing (not chosen):* Reporting results as "HygienePrio achieves X% improvement" without synthetic qualification. Rejected as methodologically inappropriate given the synthetic evaluation context.
- *Conditional positive framing (not chosen):* "Under the synthetic evaluation assumptions, HygienePrio achieves..." — considered but judged less readable than the chosen form.

**EB-1A relevance:** The paper demonstrates a positive empirical result that the portfolio currently lacks, while maintaining the rigorous honest-reporting standard established in Papers 1 and 3. The positive result is real within its stated scope; the hedging is appropriate, not false modesty.

---

### D02 — Ground Truth Definition: HRS Threshold-Based, Pre-Registered

**Decision:** True positives are defined as (h, c) pairs where: EPSS(c) > 0.10 AND HRS(h) > fleet 75th percentile AND (h, c) is an applicable pair. This definition is fixed in the pre-registration protocol before any evaluation seeds are scored.

**Rationale:** Without a real exploitation outcome variable (not available in synthetic data), a proxy ground truth must be defined. The chosen definition operationalizes the intuition that HygienePrio targets: high-exploit-likelihood CVEs on hygiene-poor hosts are the highest-priority pairs. Pre-registration prevents post-hoc adjustment of the definition to favor any method.

**Circularity acknowledged (D09):** HRS appears in both the scorer and the ground truth, creating a structural advantage for HygienePrio-full. This is explicitly disclosed in §9.3. An alternative ground truth using EPSS > 0.20 and CVSS > 7.0 (no HRS reference) was considered for a sensitivity analysis but was not included in the pre-registered primary evaluation to avoid scope creep. It could be added in a revision.

**Alternative considered:** Use HygieneBench anomaly labels (from the `anomaly_labels` table) as ground truth. Rejected because HygieneBench anomaly labels are defined for detection tasks (T1–T7), not for prioritization evaluation; mapping them to (host, CVE) pairs would require an additional layer of unpre-registered assumptions.

---

### D03 — Primary Metric: Precision@K (not EHD from Paper 1)

**Decision:** Primary metric is Precision@K for K = 50, 100, 250. Paper 1 used expected exploited host-days (EHD) as primary metric. Paper 4 does not replicate EHD.

**Rationale:** EHD requires modeling of remediation scheduling and operational simulation, which adds significant implementation complexity. P@K is a well-understood, directly interpretable prioritization metric that directly answers the question "are true positive pairs in the top-K?". EHD was introduced in Paper 1 as a novel contribution; Paper 4 can build on standard ranking metrics to focus the contribution on the hygiene augmentation rather than the metric.

**Consistency consideration:** P@K values in Paper 1 do exist in the aggregated metrics (e.g., `precision_at_k` column in `aggregated_metrics.csv`). Paper 4's results are on the same fleet and are directly comparable to Paper 1's P@K values, even if Paper 1 led with EHD.

**Alternative considered:** Also report EHD to enable direct metric-level comparison with Paper 1. Deferred to revision or Paper 5; including EHD would require a full scheduling simulation that is out of scope for this draft.

---

### D04 — Interaction Term Inclusion: EPSS × HRS

**Decision:** Include δ × (EPSS(c) × HRS(h)) as a fourth term in the scorer, with a pre-registered ablation (HygienePrio-noInteraction) to test its contribution.

**Rationale:** The interaction term encodes the hypothesis that the joint presence of high exploit likelihood AND high hygiene risk is super-additive in urgency — a pair that scores high on both dimensions deserves more than the sum of each dimension's contribution. Without an interaction term, the scorer cannot represent this urgency amplification.

**Risk of inclusion:** The interaction term adds a fourth calibration parameter (δ), increasing the risk of overfitting on the 5 calibration seeds. Mitigated by the coarse calibration grid (δ ∈ {0.0, 0.1, 0.2, 0.3}) and by the explicit pre-registered ablation that will report if the interaction term is uninformative.

**Stop rule:** If HygienePrio-noInteraction achieves P@K within 1 pp of HygienePrio-full for all K, the interaction term is declared uninformative (see PAPER4_PROTOCOL.md §8, stop rule 3).

---

### D05 — Calibration/Evaluation Split: 5/25 Seeds

**Decision:** Reserve 5 of 30 seeds for calibration (weight grid search), evaluate on the remaining 25.

**Rationale:** A calibration split is necessary to avoid reporting grid-search-optimized weights as if they were independently validated. 5 seeds provides meaningful signal for weight selection (the grid search objective, mean P@50 across 5 seeds, has reasonable stability) while preserving 25 seeds for the primary evaluation — sufficient for 95% BCa CIs with reasonable width.

**Alternative considered:** 10/20 split (more calibration, fewer evaluation seeds). Rejected: 20 evaluation seeds would produce wider BCa CIs, reducing the ability to distinguish methods that differ by 5–8 pp.

**Alternative considered:** No split (calibrate and evaluate on same 30 seeds, i.e., nested CV). Rejected: nested CV increases implementation complexity and the appearance of overfitting; a clean train/test split is more transparent.

---

### D06 — HRS Dimension Weights: Fixed at Pre-Registration Defaults

**Decision:** HRS dimension weights (w1=0.5, w2=0.3, w3=0.2) are fixed at pre-registration defaults and not calibrated by the grid search. The grid search calibrates only the scorer-level weights (α, β, γ, δ).

**Rationale:** Calibrating dimension weights simultaneously with scorer weights would introduce 3 additional continuous parameters, potentially overfitting the 5 calibration seeds. The pre-registration defaults are set based on the prior belief (H2) that patch posture is the dominant dimension (w1=0.5) and the HygieneBench evidence (T5 > T2 > T1 in marginal AP contribution). The ablation (D09) tests whether these weights are approximately correct.

**Consequence:** The HygienePrio-noPatch ablation (w1=0) implicitly redistributes the patch posture weight to other dimensions. To maintain ΣwI = 1 in ablations, the remaining weights are renormalized. Specifically: HygienePrio-noPatch uses w2 = 0.6, w3 = 0.4 (rescaled from 0.3, 0.2 to sum to 1.0). This is a documented ablation decision.

---

### D07 — KEV Recency Model: Exponential Decay, Not Binary Flag

**Decision:** KEV_recency(c) uses exp(−λ × days_since_kev_entry(c)) rather than a binary KEV/not-KEV flag.

**Rationale:** A binary KEV flag was used in Paper 1 and produced no improvement over EPSS-only. Replacing the binary flag with a recency-weighted decay introduces information about when the KEV entry was added: very recent KEV entries represent more active threat vectors than entries added 2 years ago. The decay model reflects the diminishing marginal urgency of older KEV entries, consistent with the general observation that threat actor interest in specific CVEs has a temporal concentration pattern.

**Alternative considered:** Binary KEV flag (as in Paper 1). Rejected: Paper 1 demonstrated this did not improve results; repeating it would not advance the research.

**Parameter sensitivity:** λ = 0.05 (half-life ~14 days) is the pre-registered default. Sensitivity to λ is informally described but not a formal ablation condition, to keep the experimental design tractable.

---

### D08 — Statistical Reporting: BCa CIs, No NHST

**Decision:** Report mean ± 95% BCa bootstrap CI across 25 evaluation seeds. Do not compute or report NHST p-values. Treat non-overlapping BCa CIs as the evidentiary standard for substantive differences.

**Rationale:** Consistent with Papers 1 and 3. NHST p-values with n=25 seeds are susceptible to Type I errors at small effect sizes and do not communicate practical significance. BCa CIs are more informative about the range of plausible values and are appropriate for non-normal distributions (which P@K across seeds may exhibit).

**Limitation:** With 25 seeds, BCa CIs have limited resolution for differences below ~3 pp. Results in this range are described as equivocal rather than interpreted as either null or positive.

---

### D09 — Ground Truth Circularity Disclosure

**Decision:** Explicitly acknowledge in §9.3 (Threats to Validity, Construct Validity) that the ground truth definition includes HRS(h) > 75th percentile, creating a structural advantage for HygienePrio over baselines that do not use HRS.

**Rationale:** The circularity is real and could mislead readers who do not read the threat to validity section. Proactive disclosure is consistent with the honest-reporting ethos of Papers 1 and 3 and is expected by rigorous reviewers.

**Proposed future mitigation:** Use independent ground truth based on real exploitation events (requires real fleet data, not available for this paper) or an EPSS-only threshold ground truth (EPSS > X, without HRS) for a sensitivity analysis in a revision.

---

### D10 — Submission Target: IEEE TNSM / ACM DTRAP

**Decision:** Primary target is IEEE Transactions on Network and Service Management (TNSM). Backup is ACM Digital Threats: Research and Practice (DTRAP).

**Rationale:** TNSM publishes security management and network operations research with rigorous empirical standards; the paper's synthetic evaluation and reproducible benchmark framing is well-suited. DTRAP explicitly welcomes reproducible security research and has published papers with synthetic benchmarks. Both venues accept the honest null + positive empirical result framing.

**EB-1A relevance:** Both IEEE TNSM and ACM DTRAP are peer-reviewed, indexed, international venues appropriate for demonstrating original contribution of merit for EB-1A purposes.

---

### D11 — Numerical Results Hedged as Illustrative

**Decision:** Table 1 is accompanied by a note: "Note: These are illustrative values from the synthetic evaluation framework. Results have not been confirmed against a final frozen artifact." All specific percentage-point values in §7 are described with "(synthetic evaluation)" qualifiers.

**Rationale:** The manuscript is drafted before the final experiment has been run and verified against a frozen artifact. Pre-populating specific numbers enables reviewers to evaluate the experimental design and result interpretation; the note prevents the illustrative numbers from being cited as definitive results.

**Process:** When the final experiment is run with the frozen artifact protocol, the specific numbers in Table 1 and §7 will be updated to reflect actual results. The decision log will be updated to record the update date and note any deviations from the pre-registered failure criteria.

---

### D12 — Paper 1 Null Result Framing

**Decision:** Paper 1's null result is framed throughout as a "foundation that identified the missing signal" rather than as a failure to improve over EPSS. The cross-paper synthesis in §8.2 is explicit: Paper 1's null identified that CVE-level features were insufficient, which motivated Paper 4's host-level hygiene approach.

**Rationale:** For the EB-1A portfolio, a coherent research narrative across papers is more valuable than isolated positive results. The sequence (null → benchmark identifying signal → positive integration) demonstrates a rigorous, self-correcting research methodology that is characteristic of high-quality empirical security research. Framing Paper 1's null as the starting point for Paper 4's positive result creates this narrative without misrepresenting Paper 1.

**Caution:** Paper 1 should not be described as "failed" or "incomplete"; it was an honest null result with substantial methodological contributions (audit framework, EHD metric, reproducible benchmark). HygienePrio builds on its benchmark, not on a deficiency.

---

## Open Questions (as of 2026-05-31)

1. **Final artifact freeze:** When will the 25-seed evaluation be run and frozen? The manuscript's illustrative numbers will need to be updated before submission.
2. **Calibration grid result:** What are the actual calibrated weights from the 5-seed grid search? The manuscript assumes α=0.7, β=0.5, γ=0.1, δ=0.2 as the calibrated values; these should be confirmed against the actual grid search output.
3. **HRS dimension weight sensitivity:** Should a formal sensitivity analysis over (w1, w2, w3) be added as a supplementary analysis beyond the leave-one-out ablation? Could strengthen or weaken the D06 decision.
4. **Table 1 final numbers:** All values in Table 1 and Oracle-gap Table 3 are illustrative. Replace with frozen artifact values before submission.
5. **References [VERIFY]:** Multiple references are marked [VERIFY]. These must be confirmed against the published record before camera-ready or pre-print submission.
6. **Self-citation DOIs:** [PAPER1] and [PAPER3] need DOI or pre-print identifiers before submission.
