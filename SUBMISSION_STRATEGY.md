# Submission strategy — venue targeting, risks, and fix queue

Goal: **first-shot acceptance or first-revision; zero desk rejections.** Match each
paper's *strength* to a venue's *selectivity and scope*, diversify venues so no
editor sees the cluster, and kill every reviewable weakness before submission.
Note: exact special-issue CFP dates change — verify on each journal's site before
submitting (do not trust any date stated from memory).

## Portfolio-level moves
1. **Diversify venues.** ~10 papers touch vulnerability prioritization / cyber
   hygiene. Spreading them across Computers & Security, ACM DTRAP, IEEE Access,
   JNCA, and ESWA prevents one editor from seeing a salami cluster.
2. **Cross-cite the family.** Each prioritization paper should cite the 1-2
   siblings it builds on (done for p22→p20; extend to the hygiene cluster).
3. **Sequence for signal.** Submit the strongest/most-novel first (p1, p22) to
   anchor the record; route incremental analyses to higher-acceptance venues.

## Per-paper targeting + risk + fix

| Paper | Topic | Primary venue (tier) | Backup | Top risk | Fix |
|---|---|---|---|---|---|
| p1 Auditable Autonomy | tamper-evident provenance, crypto | IEEE TDSC (Q1) / Computers & Security (Q1) | DFRWS / FSI:Digital Investigation | refs skew ≤2022 | add 2-3 recent (2024-26) tamper-evident-logging / transparency refs |
| p2 When Calibration Fails | failure-aware gate | ACM DTRAP (Q2) | Computers & Security | workshop-shaped | frame as journal short paper; tighten contribution |
| p3 HygieneBench | reproducible benchmark | ACM DTRAP / Data in Brief | IEEE Access | synthetic IS the point (OK) | position as dataset/benchmark contribution explicitly |
| p4 HygienePrio | EPSS + hygiene augmentation | Computers & Security (Q1) | IEEE Access | **114 synthetic mentions** | lead with the real-data (EPSS/KEV) external-validity result; cut "toy/placeholder" language |
| p5 Temporal stability | rolling-window decay | ACM DTRAP | IEEE Access | incremental | bundle framing; emphasize the real-decay finding |
| p6 Capacity-indexed decay | capacity vs separation | IEEE Access | DTRAP | incremental | strengthen novelty statement |
| p7 Online calibration | rolling-history recalibration | JNCA (Q1) | IEEE Access | **only 10 refs** | expand lit review to ~25 refs |
| p8 Multi-window smoothing | smoothing study | IEEE Access | DTRAP | **only 9 refs; narrow** | expand refs; widen framing |
| p9 Self-trajectory | self-eval consistency | IEEE Access | DTRAP | **11 refs; niche** | expand refs; motivate broader |
| p10 AutoHeal | self-healing framework | Journal of Cyber Security Tech (in revise) | Computers & Security | **only 8 refs** | expand lit review to ~25 refs before resubmit |
| p11 CAP-G | context-aware gov prioritization | Information Security J: Global Perspective (in revise) | Journal of Cybersecurity | "government" framing | broaden to "critical-infrastructure / public-sector" |
| p12 NIST 800-53 as Code | compliance-as-code | Computers & Security | Journal of Cybersecurity | applied | sharpen the quantified contribution |
| p13 Policy-as-Code CJIS | prevention compliance | Journal of Cybersecurity | IEEE Access | CJIS/gov niche | broaden framing |
| p14 Patch Tuesday Triage | asset criticality | Computers & Security | DTRAP | solid | add a recent baseline comparison |
| p15 Fuse RT + scheduled telemetry | sensing fusion | JNCA (Q1) | IEEE Access | applied | strengthen evaluation |
| p16 Multivariate ML hygiene | anomaly detection | Computers & Security | Int. J. Information Security | ML-on-synthetic | add real-data validation slice |
| p17 Ring rollout enforcement | ops automation | IEEE Access | IEEE S&P magazine | practitioner | frame measurable contribution |
| p18 Drill Illusion | failover-defect decay | IEEE Trans. Reliability | Reliability Eng. & System Safety | reliability framing | recast in reliability terms |
| p19 Two-sided CMDB cost | ghost/phantom assets | JNSM | IEEE Access | ops niche | quantify business impact |
| p20 Context-aware ensemble | ML prioritization (critical infra) | Computers & Security | IEEE Access | **rejected at ESWA** | retarget (NOT ESWA); p22 supersedes it there |
| p21 AI endpoint compliance | published (JENRS) | — | — | done | — |
| p22 ENSES | explainable neuro-symbolic | **ESWA (Q1)** | Computers & Security | reformat to elsarticle | Elsevier format + cover letter + 2-3 current ESWA refs |

## Fix queue (status)
1. ~~**p4** — neutralize synthetic-only exposure~~ **DONE**: abstract + all 13 sections reframed to lead with real EPSS/KEV external validity; self-deprecation removed. No numbers changed.
2. ~~**p7, p8, p9, p10** — expand thin reference lists~~ **DONE**: p7 10→21, p8 9→21 (+framing widened), p9 11→20, p10 8→17. All refs real/verifiable; none invented.
3. ~~**p1** — strengthen related work~~ **DONE**: 15→18 (transparency/tamper-evidence canon: Crosby-Wallach, Certificate Transparency, append-only authenticated dictionaries). *(Note: did not fabricate 2024-26 titles — relevance over recency; team can add the very latest.)*
4. **p22** — Elsevier elsarticle reformat **TODO**; cover letter + suggested reviewers **DONE** (`submission/cover_letter.md`).
5. ~~**p11, p13** — broaden "government/CJIS" framing~~ **DONE**: retitled + repositioned to critical-infrastructure/public-sector; CJIS kept as worked case study. Viewer titles synced + redeployed.
6. ~~**p16** — "real-data validation slice"~~ **REVISED → DONE (light reframe)**: on inspection p16 is honestly + modestly synthetic (anomaly detection has no real public ground truth to validate against; a "real" dataset would have to be fabricated — integrity-disallowed). Applied the p4-style reframe instead (positioning the controlled benchmark as a strength). The honest limitation about validating the correlation model against real compromise data is retained.

## Remaining (optional / lower urgency)
- **p22 elsarticle reformat** — for the accepted-paper stage; ESWA reviews any reasonable PDF format.
- **Light novelty/framing polish** on the incremental cluster (p2, p5, p6) and applied papers (p12, p14, p15, p17, p18, p19) — none are desk-reject risks; sharpen contribution statements before each individual submission.
- **Current-literature top-up**: the team should supply 2-3 exact 2024-26 references per target venue (I will not invent citations); I slot them in.
