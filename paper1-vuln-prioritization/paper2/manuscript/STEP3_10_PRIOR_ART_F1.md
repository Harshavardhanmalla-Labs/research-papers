<!--
Paper 2 — Step 3.10: Fix F1 — Prior-Art Verification (executed).
Targeted web/library prior-art search for the Step-3.9 pivot
("robustness/sensitivity-only Paper 2"). Verified sources only;
unverified claims carry [VERIFY]. No fabricated citations.
Paper 1 (results/primary_full_v1/) untouched; no experiments run.
-->

# Paper 2 — Step 3.10: Prior-Art Verification (Fix F1)

**Decision: CONDITIONAL KEEP** with a substantial framing pivot.
The original Step-3.9 pivot headline ("Robustness of Context-Aware Vulnerability
Prioritization") **is largely occupied by prior work**: capacity-constrained
prioritization (VULCON 2018, Deep VULMAN 2023, Roytman "Capacity is King"),
context/asset-aware ablation (Sherif et al. 2026 KRI), EPSS temporal stability
(Ravalico et al. 2025), CVSS/EPSS/SSVC empirical comparison (Koscinski et al.
2025), and the field has a recent survey (Jiang et al. 2025, arXiv 2502.11070).
The **genuinely novel piece that survives** is much narrower: the
**failure-aware multi-t0 calibration-gate methodology** + the **specific negative
feasibility finding** for KEV-only-labelled, catalog-restricted public-feed slices.
Step 4 is **NOT** yet allowed — F1 surfaces required framing changes that must be
incorporated before pre-registration.

## 1. Search methodology
- Targeted Web search across the 12 areas and 18 specific queries listed in the
  Step-3.10 task brief. Two waves (general + verification fetches).
- Followed verified-link policy: every paper cited in §3 was fetched (arXiv abs
  page, doi page, or institutional URL) and the title/authors/date confirmed
  from the source. Items that could not be fully verified carry `[VERIFY]`.
- One source (VULCON ACM DL) returned HTTP 403 on fetch; metadata is cross-checked
  from the SERP and a second-source listing; marked `[VERIFY-DOI]`.
- No employer/production data. No Paper 1 freeze touched. No experiments run.

## 2. Sources searched
Google Scholar (via web), arXiv, ACM DL, Springer, USENIX (via web), FIRST.org
(EPSS), CISA (KEV/SSVC), CMU SEI (SSVC), NIST (CSWP/LEV), SSRN (EPSS dynamics),
and select vendor/research blogs (Empirical Security, Orange Cyberdefense,
Splunk, Wiz, runZero) as non-academic context — not used to establish novelty
claims.

## 3. Verified sources table

Columns abbreviated: EPSS/CVSS/KEV/Ctx (context features); TR (temporal
robustness); Sens (sensitivity/ablation); Cap (capacity-constrained scheduling);
Sparse (sparse exploit labels); Synth (synthetic benchmark); Pub (public-feed
data); Threat (to pivot novelty); ND = Required differentiation.

| # | Source | Link | Type | What it studies | EPSS | CVSS | KEV | Ctx | TR | Sens | Cap | Sparse | Synth | Pub | Threat | ND |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Sherif, Yevseyeva, Basto-Fernandes, Cook — *Bridging the Gap Between Security Metrics and KRIs* (arXiv **2603.12450**, Mar 2026) | https://arxiv.org/abs/2603.12450 | academic | KRI framework (threat+impact+exposure) vs CVSS/EPSS; 280,694 CVEs; **ablation analysis** (EPSS AUPRC 0.365 vs full KRI 0.223; KRI captures 92.3 % impact-weighted value @ k=500) | y | y | y | y | n | **y** | n | n | n | y | **HIGH** | Our claim cannot be "ablation of CVSS/EPSS/context features"; must move to *failure-aware-gate* angle |
| P2 | Jiang, Oo, Meng, Lim, Sikdar — *A Survey on Vulnerability Prioritization* (arXiv **2502.11070**, Feb 2025) | https://arxiv.org/abs/2502.11070 | academic | Survey of 82 studies; 5-category taxonomy (severity / exploitability / contextual / predictive / aggregation) | y | y | y | y | partial | partial | partial | n | n | y | **HIGH** | Field is mature; must situate within survey's taxonomy and identify the surviving gap (failure-aware-gate is not a taxonomy category) |
| P3 | Roytman — *Capacity is King* (Empirical Security research note) | https://research.empiricalsecurity.com/research/capacity-is-king | vendor research | Sweeps **3 capacity tiers** (6.6 % / 15.2 / 27.1 % monthly closure) × strategies (CVSS / random / known-exploit) on observed enterprise data; headline "strategy dominates capacity"; "CVSS≈random" | y partial | y | y partial | n | n | **y** | **y** | n | n | y (real scan) | **HIGH** | Our sensitivity-across-capacity headline is essentially already published as a vendor finding |
| P4 | Farris, Shah, Cybenko, Ganesan, Sushil — *VULCON: A System for Vulnerability Prioritization, Mitigation, and Management* (ACM TOPS **21(4)**, 2018, doi 10.1145/3196884) `[VERIFY-DOI]` | https://dl.acm.org/doi/10.1145/3196884 | academic | Mixed-integer multi-objective optimization for capacity-constrained vulnerability remediation; real SOC scan data; 8.97 % vulnerability-exposure reduction | n (pre-EPSS-v3) | y | n | partial | n | y | **y** | n | n | y (real scan) | **HIGH** | Capacity-constrained scheduling is "owned" by VULCON; we must not claim novelty there |
| P5 | Hore, Sharma, Sahay — *Deep VULMAN: A Deep RL-Enabled Cyber Vulnerability Management Framework* (Expert Systems with Applications **221**, 2023, doi 10.1016/j.eswa.2023.119734; arXiv 2208.02369) | https://arxiv.org/abs/2208.02369 | academic | DRL + integer programming for vulnerability prioritization under fluctuating arrivals + resource constraints; anticipates future events | partial | y | y partial | y partial | y (dynamic) | y (vs deterministic baseline) | **y** | n | partial (simulated) | y | **HIGH** | Capacity + dynamic-prioritization framing also occupied; differentiate by methodology (gate-driven, not RL) |
| P6 | Ravalico, Farina, Trevisan, Bartoli — *Analysing the Temporal Dynamics of EPSS* (SSRN **5147459**, 2025) | https://dx.doi.org/10.2139/ssrn.5147459 | academic | EPSS temporal stability on **45,000+** vulnerabilities since v3 release | **y** | partial | partial | n | **y** | partial | n | n | n | y | **HIGH** | We cannot claim EPSS temporal-stability novelty; drop that axis as a contribution claim |
| P7 | Koscinski, Nelson, Okutan, Falso, Mirakhorli — *Conflicting Scores, Confusing Signals: An Empirical Study of Vulnerability Scoring Systems* (arXiv **2508.13644**, Aug 2025) | https://arxiv.org/abs/2508.13644 | academic | Cross-system empirical comparison of **CVSS / SSVC / EPSS / Exploitability-Index** on 600 Microsoft Patch-Tuesday CVEs over 4 months; reveals significant ranking disparities | y | y | n (uses Exploitability-Index instead) | n | n | partial | n | n | n | y | **MEDIUM-HIGH** | Cross-system disparity finding is published; we cannot lead with "scoring systems disagree" |
| P8 | Jacobs, Romanosky, Edwards, Adjerid, Roytman — *Exploit Prediction Scoring System (EPSS)* (ACM **DTRAP**, 2021, doi 10.1145/3436242) | https://dl.acm.org/doi/10.1145/3436242 | academic | Foundational EPSS paper | **y** | y | y | partial | partial | n | n | partial | n | y | MEDIUM (baseline) | Standard citation; not a novelty threat per se |
| P9 | Jacobs et al. — *Enhancing Vulnerability Prioritization: Data-Driven Exploit Predictions with Community-Driven Insights* (arXiv **2302.14172**, 2023) | https://arxiv.org/abs/2302.14172 | academic | EPSS v3 model paper (16→1,164 features; XGBoost) | **y** | y | y | partial | y | y (model-level) | n | y (one of the issues) | n | y | MEDIUM | Standard citation; not a head-on threat |
| P10 | Allodi & Massacci — *Comparing Vulnerability Severity and Exploits Using Case-Control Studies* (ACM **TISSEC** 17(1), 2014, doi 10.1145/2630069) | https://dl.acm.org/doi/10.1145/2630069 | academic | Case-control study: CVSS poor predictor; PoC + black-market presence much stronger; classifier stabilises ~85 % | n (pre-EPSS) | **y** | n | n | y | y | n | y (relative) | n | y | MEDIUM (foundational) | Foundational; cite, do not compete |
| P11 | CISA / CMU SEI — *SSVC v2.0* (2023) | https://www.cisa.gov/sites/default/files/publications/cisa-ssvc-guide%20508c.pdf | standard | Stakeholder-Specific Vulnerability Categorization (decision tree on exploitation/automation/exposure/safety/mission) | n | n | y partial | **y** | n | y (decision-tree variations) | n | n | n | y | MEDIUM | Established standard; cite, do not compete |
| P12 | NIST — *CSWP 41 "Likely Exploited Vulnerabilities (LEV)"* (May 2025) `[VERIFY]` | https://nvlpubs.nist.gov/nistpubs/cswp/nist.cswp.41.pdf | standard (gov) | Proposed metric for vulnerability exploitation probability (LEV) complementary to EPSS/KEV | y | y | y | n | y | n | n | y (relevance) | n | y | MEDIUM | Government LEV metric is recent; must cite as state-of-practice |
| P13 | VulRG — *Multi-Level Explainable Vulnerability Patch Ranking for Complex Systems Using Graphs* (arXiv **2502.11143**, 2025) | https://arxiv.org/abs/2502.11143 | academic | Network-communication + system-dependency graphs for asset-context-aware patch ranking | partial | y | partial | **y** | n | y (vs SOTA) | partial | n | n | y | MEDIUM | Context-aware-ranking-with-graphs is occupied; we don't use graphs, so direct collision is partial |
| P14 | VulnScore (Alqahtani, Almukaynizi) — *VulnScore: A Deployed System for Patch Prioritization* (Springer IJIS, 2025, doi 10.1007/s10207-025-01164-3) `[VERIFY]` | https://link.springer.com/article/10.1007/s10207-025-01164-3 | academic + deployed | Integrates EPSS+CVSS+Vulners-AI+user criticality; deployed in Reconmap | y | y | n | y (user-defined) | n | partial | n | n | n | y | LOW–MEDIUM | Deployed-system contribution different from our methodology focus |
| P15 | *Vulnerability Management Chaining* (arXiv **2506.01220**, Jun 2025) | https://arxiv.org/abs/2506.01220 | academic | Integration framework KEV+EPSS+context; identifies 57 extra exploited CVEs; claims 14-18× efficiency, 85 %+ coverage, 95 % workload cut | y | y | y | y | n | y | y (efficiency) | n | n | y | **MEDIUM-HIGH** | Integration-for-efficiency framing also occupied |
| P16 | NIST LEV (web doc) `[VERIFY]` | https://riskbasedprioritization.github.io/epss/LEV/ | community/gov-derived | Companion to CSWP 41; risk-based-prioritization writeup | y | partial | y | n | y | n | n | y | n | y | LOW | Useful framing reference |
| P17 | Empirical Security — *EPSS historical scores repo* | https://github.com/empiricalsec/epss_scores | dataset | Historical EPSS scores | y | n | n | n | y | n | n | n | n | y | LOW (dataset, not paper) | Useful artefact citation |
| P18 | Vendor blogs (Orange Cyberdefense, Splunk, Wiz, Cloudsmith, Picus, runZero KEVology) | various | vendor | Practitioner-oriented EPSS/KEV/CVSS commentary | y | y | y | y | partial | n | n | partial | n | y | LOW (non-academic) | Useful context, not novelty competitors |

`[VERIFY-DOI]` = DOI string verified via SERP but the full ACM DL page returned HTTP 403; re-verify before Step 4 manuscript stage.
`[VERIFY]` = source listed in SERP and consistent across multiple results but not fetched in full this turn.

## 4. High-threat prior art (the ones that meaningfully constrain the pivot)
- **VULCON** (Farris et al. 2018) — capacity-constrained prioritization, mixed-integer multi-objective optimization on real SOC scan data; **owns** capacity-constrained scheduling.
- **Deep VULMAN** (Hore et al. 2023) — DRL + integer programming under resource constraints with fluctuating arrivals; **owns** dynamic resource allocation.
- **Capacity is King** (Roytman, Empirical Security) — sensitivity sweep across capacity × strategy showing "strategy dominates capacity" and CVSS≈random on real data; **owns** the "strategy choice matters" headline.
- **Sherif et al. 2026** (KRI) — ablation of CVSS/EPSS/context (threat+impact+exposure) on 280,694 CVEs with AUPRC/ROC-AUC reporting; **owns** ablation of context features against EPSS.
- **Ravalico et al. 2025** — EPSS temporal dynamics on 45 k+ vulnerabilities; **owns** EPSS temporal-stability axis.
- **Jiang et al. 2025 survey** — comprehensive taxonomy of 82 studies; **field is mature**; anything we publish must situate inside this taxonomy and identify the surviving gap honestly.

## 5. Medium-threat prior art
- **Koscinski et al. 2025** — empirical CVSS/SSVC/EPSS/Exploitability-Index disagreement on 600 CVEs; closes the "cross-system disparity" headline.
- **Vulnerability Management Chaining** (arXiv 2506.01220, 2025) — KEV+EPSS+context integration with efficiency claims.
- **Jacobs et al. 2021 / 2023** — EPSS foundation + v3 model paper. Required baseline citations.
- **Allodi & Massacci 2014** — case-control; foundational; cite, not compete.
- **SSVC v2.0** (CISA/CMU SEI) — established standard for stakeholder-specific categorization; required citation.
- **NIST CSWP 41 LEV** `[VERIFY]` — recent (2025) government-proposed metric; must be situated.
- **VulRG 2025** — graph-based context-aware ranking; partial collision (we use no graphs).

## 6. Low-threat / context sources
- **VulnScore** (Alqahtani, Almukaynizi 2025) `[VERIFY]` — deployed system, different focus.
- **Empirical Security EPSS-scores repo** — useful artefact.
- Practitioner blogs (Orange Cyberdefense, Splunk, Wiz, Cloudsmith, Picus, runZero) — non-academic context only.

## 7. Falsification-question answers

**A. Has someone already published a sensitivity/robustness study of context-aware vulnerability prioritization under sparse exploit labels?**
*Answer:* **partial yes.** Sherif et al. 2026 ablate context-aware (KRI) features against CVSS/EPSS; Koscinski et al. 2025 show cross-system disagreement; Capacity-is-King runs strategy sweeps. The *exact* phrase "under sparse exploit labels" is not the headline of any of these; all use large CVE corpora (280 k, 45 k, 600). **Impact:** the "sensitivity / robustness" headline is largely occupied; the "under sparse labels" qualifier is what survives — but as a finding, not as a banner topic.

**B. Has someone already shown EPSS/CVSS/KEV rankings under capacity constraints with sensitivity sweeps?**
*Answer:* **yes, substantially.** VULCON (2018), Deep VULMAN (2023), and Capacity-is-King all cover capacity-constrained prioritization with strategy sweeps; CVSS-vs-random and "strategy dominates capacity" are already established findings. **Impact:** the capacity-axis cannot be a primary contribution claim.

**C. Has someone already evaluated asset criticality / exposure / remediation-complexity ablations against EPSS under sparse labels?**
*Answer:* **partial yes.** Sherif et al. 2026 ablate KRI components (threat+impact+exposure) against EPSS. VulRG (2025) ranks with asset-context graphs. *Under sparse labels specifically:* no direct hit — the closest is Sherif's full-CVE-population ablation, which does NOT restrict to KEV-only labels intersected with a small product catalog. **Impact:** the specific sparse-label-restricted ablation is uncovered, but it is also weak as a stand-alone contribution because the same ablation on a larger label set is already published.

**D. Has someone already used a public-feed + synthetic endpoint benchmark to test prioritization robustness?**
*Answer:* **no direct hit found.** Most academic work uses real CVE corpora (Sherif, Jacobs, Koscinski), real SOC scan data (VULCON, Roytman), or simulated arrivals (Deep VULMAN). The public-feed + synthetic-endpoint combination is not standard. **Impact:** this is *differentiating* but not necessarily *good* — reviewers are likely to view synthetic-endpoint as a limitation versus VULCON's real scan data, not as a novelty.

**E. Has someone already made the core finding that calibration of per-feature context-aware weights fails due to sparse KEV/PoC positives on a catalog-restricted slice?**
*Answer:* **no direct hit found.** Allodi & Massacci show classifiers stabilise ~85 % accuracy on broader exploit telemetry; EPSS itself is calibrated on broader exploit-attempt data; Sherif's KRI ablation succeeds on 280 k unrestricted CVEs. Our specific negative finding ("on a 31-product public-sector-typical catalog, KEV-only Label A over 18 monthly t0 windows in the EPSS v3 era yields 7 unique positive CVEs — too few for per-feature weight calibration") is, as best the F1 search can determine, **novel as a documented negative result**. **Impact:** this is the strongest surviving novelty piece.

## 8. Surviving novelty gap (honest, narrow)
Of the original Step-3.9 contribution list (C1–C5), the F1 sweep eliminates or de-rates most:
- **C1** (empirical sparsity characterisation) — **survives, narrowly**: the specific (catalog × KEV-label × EPSS-v3-era × monthly-t0) sparsity figure (7 unique positive CVEs / 2,688 catalog CVEs / 18 windows) is uncovered as a published number. It is a small but defensible empirical contribution if framed as *a public-feed feasibility data point*, not as *the result of the paper*.
- **C2** (real-feed extension of Paper 1 benchmark) — **engineering, not novelty**.
- **C3** (multi-axis sensitivity sweep) — **largely eliminated**: capacity (VULCON, Deep VULMAN, Roytman), ablation (Sherif), temporal stability (Ravalico), scoring-system disagreement (Koscinski) are all covered. Survives only as *secondary confirmatory tables*, not as the primary claim.
- **C4** (failure-aware calibration-gate methodology) — **survives as primary**: the multi-t0 distinct-positive-CVE gate + decision rubric + the Step-3.5→3.8 reproducible-decision-trail artefact is not a published methodology, and it cleanly addresses the question *"when is per-feature weight calibration on public feeds not statistically justified?"* — a question others (Jacobs, Sherif, Allodi) have *not* asked in this form.
- **C5** (reproducible public-feed pipeline) — **engineering artefact**, valuable for reproducibility appendix; not a research novelty.

### Surviving novelty statement (exact, for use as the Step-4 contribution anchor)
> **"A failure-aware calibration-gate methodology — the multi-t0 distinct-positive-CVE gate with chunked / resumable / paced public-feed acquisition — applied to a public-sector-typical 31-product catalog over the EPSS v3 era, producing a documented negative result (7 unique positive Label-A CVEs over 18 monthly t0 windows) that establishes when per-feature context-aware weight calibration on public-feed labels is not statistically justified. Confirmatory secondary sensitivity sweeps (capacity, blackout, feature-ablation, label-source) on a real-feed extension of a frozen synthetic-fleet benchmark situate the finding within the established sensitivity literature."**

That sentence is the *most* the pivot can honestly claim after F1.

## 9. Required framing changes (must land in `STEP4_PREREGISTRATION.md` before Step 4)
1. **Drop "Robustness of Context-Aware Vulnerability Prioritization" as the title/headline.** Sensitivity-of-prioritization is occupied. Replace with a methodology-/negative-result-led title, e.g. **"When Public-Feed Calibration Fails: A Failure-Aware Multi-t0 Gate for Vulnerability-Prioritization Weight Learning Under Sparse KEV Labels."**
2. **Reposition all sensitivity sweeps from primary to *confirmatory secondary* contributions.** They cite VULCON / Capacity-is-King / Sherif / Deep VULMAN / Ravalico / Koscinski as prior art and add *confirmation under the catalog-restricted slice*, not novelty.
3. **Add the negative-result feasibility finding as the primary contribution** (the 7-positive number is the headline empirical observation).
4. **Reframe the multi-t0 gate as a methodology contribution** (Section 3 of the eventual paper), citing Jacobs/Allodi/EPSS literature as the comparators *not* using such a gate.
5. **Acknowledge the synthetic-fleet limitation explicitly** as a Section "Limitations / Threats to Validity" item, not as a novelty claim. Reviewers will compare to VULCON's real scan data.
6. **Required citations (no `[CITATION]` placeholder in the final paper).** All 15 P1–P15 sources above must appear; the differentiation in §7 must be visible in the Related Work section.
7. **Drop "fixed/published weights" wording from the pivot title.** There is no widely-published prior weight set for our 7-feature scheme; "placeholder weights, transparently documented" is the honest description.

## 10. Kill / keep decision
- **NOT KILL.** The negative feasibility finding + the failure-aware-gate methodology + the reproducible probe artefact are not in the published literature in this combination (F1 search). The Paper 1 → Paper 2 reproducibility story is also coherent.
- **NOT KEEP-as-is.** The original pivot ("sensitivity/robustness of context-aware vulnerability prioritization") collides head-on with VULCON / Capacity-is-King / Deep VULMAN / Sherif 2026 / Ravalico 2025 and would not survive peer review without major reframing.
- **NOT PIVOT-2 (yet).** A second pivot is premature: the narrowed framing in §8–§9 is defensible and uses the existing Step-3.5 → 3.8 artefacts.
- **→ CONDITIONAL KEEP** with the seven framing changes in §9, executed *before* the Step-4 pre-registration document is opened.

### Honest scoring update (post-F1, vs Step-3.9)
| | Step 3.9 | After F1 |
|---|---:|---:|
| Publishability | 5/10 | **4/10** (negative-result + methodology track; field-mature; workshop/short-paper realistic) |
| Novelty | 4/10 | **3/10** (sensitivity/ablation/capacity-constrained largely occupied; only the gate + sparsity data-point survive) |
| EB1A value | 4/10 | **3/10** (smaller surviving contribution; engineering artefact remains valuable) |

### F1 status
- **F1 complete.** Prior-art `[VERIFY]` pass executed; 15 verified academic / standard sources catalogued; 5 high-threat sources identified; surviving novelty statement written; required framing changes enumerated.
- **Step 4 NOT allowed.** The remaining fixes F2–F9 (lock fixed-weight source, metric→claim binding, MDE/power, kill-criteria-as-STOP-rules, minimal factorial, freeze invariant, compute estimate, venue plan) must still land in `STEP4_PREREGISTRATION.md`.

## Invariants honored (re-asserted)
Paper 1 frozen outputs untouched. No experiments run. No paper drafted. No
calibration or superiority claims. No catalog expansion. No PoC/ExploitDB use.
No fabricated citations (`[VERIFY]` / `[VERIFY-DOI]` retained where appropriate).
No employer / production data. Step 4 remains NOT allowed pending F2–F9.
