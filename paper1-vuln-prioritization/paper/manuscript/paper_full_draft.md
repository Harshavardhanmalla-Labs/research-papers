<!--
FULL MANUSCRIPT (Phase 20 assembly).
- Sections 1-12 reconstructed as full prose from repository artifacts (README,
  configs, code modules, generated tables/figures) in Phase 20.
- Sections 13-17 + Abstract are the Phase 18 draft, inlined verbatim; every number
  traces to a Phase 17 frozen table/figure.
Citations are placeholders ([CITATION: ...], [VERIFY]); none are fabricated.
No external-process or immigration language appears in this manuscript. The
empirical result is neutral: under toy fixtures + placeholder weights,
proposed_full does not meaningfully outperform EPSS or random.
-->

# Context-Aware Vulnerability Prioritization for Government Endpoint Fleets: Integrating Exploit Intelligence, Asset Criticality, and Endpoint Telemetry

**Author:** Harshavardhan Malla, Independent Researcher

---

## Abstract

Government endpoint fleets face more disclosed vulnerabilities than they can
remediate within operational capacity, and prioritization decisions are often made
without traceable, reviewable evidence. We present an open, reproducible benchmark
framework for context-aware vulnerability-host *pair* prioritization that
integrates exploit-intelligence (EPSS, KEV, public proof-of-concept signals),
asset-criticality, and endpoint-exposure features, and that couples ranking with a
capacity-constrained scheduler and an append-only, hash-chained audit log of every
decision. We evaluate the framework on a deterministic, public-sector-shaped
synthetic fleet using a frozen 30-seed primary artifact spanning 13 prioritization
strategies and a simulated expected-exploited-host-days (EHD) operational metric,
with strict output inspection and a content-addressed freeze/verify protocol. The
evaluation validates artifact integrity end to end — 4,290 metric rows with no
missing or non-finite values, 390 audit logs that all verify, feasible scheduling
within capacity — and computes operational and ranking metrics reproducibly from
the frozen outputs. Under the current synthetic fixtures and uncalibrated
(placeholder) weights, the strategies are statistically indistinguishable on EHD:
the proposed context-aware model neither beats the EPSS baseline nor a random
ordering, and all inter-strategy differences fall within seed-to-seed variation.
These results expose capacity-driven and base-rate trade-offs and, rather than
establishing real-world superiority, provide a falsifiable, audit-evidence-
producing benchmark on which calibrated and externally validated prioritization
studies can be built. *(Numeric values re-verified against the frozen tables;
reconfirm at camera-ready.)*

---

## Manuscript assembly status (delete before submission)

| Section | Source | Status |
| --- | --- | --- |
| 1-12 | reconstructed in Phase 20 from repo artifacts | **complete (prose below)** |
| 13-17 + Abstract | Phase 18 draft (inlined) | **complete** |

All section prose is now present. Citations remain placeholders pending Phase 21
verification; numeric values trace to the frozen Phase 17 tables.

---

## 1. Introduction

Public-sector endpoint fleets — the workstations, servers, domain controllers,
and special-purpose hosts operated by government agencies — accumulate disclosed
vulnerabilities far faster than constrained operations teams can remediate them.
The publication rate of Common Vulnerabilities and Exposures (CVEs) continues to
grow, while each maintenance window admits only a bounded number of changes under
change-advisory, blackout, and approval constraints. The practical question is
therefore not *which vulnerabilities are severe* but *which vulnerability-host
pairs should consume the next unit of limited remediation capacity*, and *can that
decision be explained and reviewed afterward*.

Existing signals each address part of the problem but none addresses the whole.
The Common Vulnerability Scoring System (CVSS) [@first_cvss_v31]
quantifies intrinsic severity but is widely noted to be a weak predictor of
real-world exploitation [@allodi2014comparing]. The Exploit Prediction
Scoring System (EPSS) [@jacobs2021epss] estimates exploitation likelihood but
is asset-agnostic: it does not know whether a vulnerable host is a domain
controller or a kiosk. The CISA Known Exploited Vulnerabilities (KEV) catalog
[@cisa_kev] and Binding Operational Directive 22-01 [@cisa_bod2201] impose deadlines on confirmed-exploited CVEs but cover a small fraction of
the backlog. Commercial risk-based vulnerability management (RBVM) products combine
such signals with proprietary asset context, but their scoring is closed and not
independently reproducible. Prior research on machine-learning prioritization
(Section 3) advances modeling but typically reports a single tuned result on
private or non-reproducible data and rarely produces per-decision audit evidence.

This gap motivates our work. We do not claim a better predictor; we ask whether an
*open, reproducible, audit-evidence-producing benchmark* can be built that ranks
vulnerability-host pairs under public-sector-shaped operational constraints, and
whether combining exploit intelligence with asset criticality and endpoint
exposure improves prioritization over EPSS-style baselines. We treat the latter as
an open empirical question and do not assume the answer.

Our contributions are (i) a framework that integrates feed normalization, exploit
enrichment, synthetic endpoint telemetry, asset-criticality and local-exposure
modeling, vulnerability-host pair construction, scoring/ranking strategies, a
capacity-constrained scheduling simulation, and append-only hash-chained audit
records; (ii) a deterministic, public-sector-shaped synthetic evaluation with a
frozen 30-seed primary artifact and an explicit freeze/verify integrity protocol;
and (iii) an honest empirical baseline. We state plainly that, under the current
toy fixtures and uncalibrated (placeholder) weights, the proposed model is
statistically indistinguishable from the EPSS baseline and does not outperform a
random ordering. The value of the work is the reproducible, falsifiable evaluation
structure, not a superiority claim.

## 2. Background

**CVSS.** CVSS [@first_cvss_v31] provides a base score for the
intrinsic characteristics of a vulnerability. We use a normalized base score as
the severity feature and as a `cvss_only` baseline, while recognizing its limited
exploitation-predictive value [@allodi2014comparing].

**EPSS.** EPSS [@jacobs2021epss] outputs a probability that a CVE will be
exploited in the near term. It is the strongest single public exploitation signal
available and serves as our primary comparison baseline. EPSS is asset-agnostic by
design, which is precisely the limitation that asset-context features attempt to
complement.

**CISA KEV.** The KEV catalog [@cisa_kev] lists CVEs with confirmed
in-the-wild exploitation and, under BOD 22-01 [@cisa_bod2201], assigns
remediation deadlines for federal agencies. KEV membership and due dates are used
both as features and as operational deadlines in the scheduler.

**The vulnerability-host pair.** Severity and exploitation likelihood are
CVE-level, but remediation is performed on a *host*. We therefore adopt the
vulnerability-host pair (v, h) as the unit of decision and explanation: the same
CVE on a domain controller and on a kiosk are different decisions with different
exposure and criticality. This pair-level granularity is what makes per-decision
audit evidence meaningful.

**Remediation capacity constraints.** Operations teams remediate within bounded
maintenance windows subject to blackout periods, change-advisory-board (CAB)
cadence, and approval gates. Any realistic evaluation must rank *and* schedule
under a fixed capacity, because the binding constraint frequently dominates
outcomes regardless of ranking quality.

**Public-sector audit and compliance context.** Government environments operate
under frameworks such as NIST SP 800-40 [@nist80040r4], NIST SP
800-53 [@nist80053r5], CIS Controls [@cis_controls_v8],
and, for criminal-justice data, the CJIS Security Policy [VERIFY: CJIS Security Policy version]. These frameworks emphasize documented, reviewable
processes. Producing per-decision evidence that *supports compliance review* is
thus a first-class design goal, distinct from any claim of compliance itself.

**Why synthetic benchmarking.** Real agency fleet telemetry is sensitive and
rarely shareable, which impedes reproducibility. A deterministic synthetic fleet
generated from documented parameter distributions, combined with real public
vulnerability/exploit feeds, allows open, repeatable evaluation without exposing
production data. We are explicit that synthetic evaluation bounds external validity
(Section 11).

## 3. Related Work

**CVSS, EPSS, and exploit prediction.** A body of work establishes that CVSS alone
poorly predicts exploitation [@allodi2014comparing] and motivates
data-driven exploitation scoring, including the lineage leading to EPSS
[@jacobs2021epss] and earlier signal-based early-warning approaches
[@sabottke2015vulnerability]. Our framework consumes these scores as features and
baselines rather than proposing a new exploitation predictor.

**Risk-based vulnerability management and commercial RBVM.** Commercial RBVM
products — Microsoft Defender Vulnerability Management [VERIFY: Microsoft Defender VM docs], Tenable VPR/ACR [VERIFY: Tenable VPR/ACR docs], Qualys TruRisk
[VERIFY: Qualys TruRisk docs], and Cisco/Kenna [VERIFY: Cisco/Kenna docs] — combine
exploit signals with proprietary asset context. They are acknowledged as
industry practice but are **not** benchmarked here: their models are closed and
their scores are not independently reproducible, which is incompatible with the
reproducibility goal of this work.

**Machine-learning vulnerability prioritization.** Research systems such as Deep
VULMAN [VERIFY: Deep VULMAN source], VulRG [VERIFY: VulRG source], VulnScore
[VERIFY: VulnScore source], and V-REx [VERIFY: V-REx source] apply learning and
graph/risk modeling to prioritization. These works advance modeling quality but
typically report a single tuned configuration on private or non-reproducible data
and do not emphasize per-decision audit evidence or an open freeze/verify protocol.
We position our contribution as complementary infrastructure — a reproducible,
public-sector-shaped benchmark with auditable decision records — and we do **not**
claim to be first.

**Resource-constrained remediation.** Prioritization is only actionable under
capacity limits. Our scheduler models bounded per-window capacity, blackout
windows, approval policies, and risk acceptance, so that strategies are evaluated
jointly with the operational constraints that shape real outcomes.

**Public-sector compliance and auditability.** Guidance such as NIST SP 800-40
[@nist80040r4] and SP 800-53 [@nist80053r5],
together with CISA directives [@cisa_bod2201], frames remediation as a
documented, reviewable process. Prior prioritization research rarely produces the
tamper-evident decision records those processes call for; our append-only,
hash-chained audit log targets that gap as an evidence-producing mechanism (not a
compliance determination).

## 4. Problem Statement

Let `V` be the set of disclosed vulnerabilities observable as of a decision time
`t0`, and `H` the set of hosts in a fleet. We define the candidate set of
**vulnerability-host pairs** `P = {(v, h) : v in V, h in H, v applies to h}`, where
applicability is determined by software/configuration matching. Each pair carries
exploit-intelligence, severity, asset-criticality, and local-exposure attributes
observable at `t0` (with strict no-future-leakage; Section 7).

A prioritization **strategy** induces a total order (ranking) over `P`. A
maintenance window admits at most a fixed **capacity** `c` pair-actions, subject to
blackout windows, operational constraints, and human-approval gates. The
**objective** of the benchmark is to *evaluate and compare* prioritization
strategies under this capacity constraint using operational and ranking metrics
(Section 9), with each scheduling decision recorded as tamper-evident audit
evidence.

Explicit **non-goals**: (i) we do not perform autonomous patching — the scheduler
is a capacity-constrained scheduling *simulation* that models approval and timing,
not patch execution or success; (ii) we do not perform production validation — the
evaluation is on a public-sector-shaped synthetic fleet; (iii) we do not benchmark
commercial RBVM products; and (iv) we do not claim that the framework guarantees or
proves compliance — it produces evidence that *supports* review.

## 5. Proposed Framework

The framework is a pipeline of composable components.

**Feed normalization.** Public feeds (NVD/CVE, FIRST EPSS, CISA KEV, and optionally
ExploitDB proof-of-concept indices subject to upstream license) are fetched by
scripts and cached as local snapshots. All access is date-parameterized as-of
queries so that no feature observed at `t0` can incorporate information published
after `t0`.

**Exploit enrichment.** Each CVE is enriched with an EPSS score (feature `E`), KEV
status and due date (features `K` and the urgency component `U`), and public
proof-of-concept observations used for labeling.

**Synthetic endpoint telemetry, asset criticality, and local exposure.** A
deterministic generator produces hosts with roles, OS/software inventory, identity
tiering, network zone, and data-sensitivity proxies. From telemetry we derive an
asset-criticality feature `C` (incorporating an Identity Privilege Exposure Score,
IPES) and a per-pair local-exposure feature `X`. A remediation-complexity feature
`R` captures the operational cost/risk of applying a fix.

**Pair construction.** Applicable (v, h) pairs are built with explicit
match-method and match-confidence provenance, excluding future-disclosure
vulnerabilities relative to `t0`.

**Scoring and ranking.** A linear model scores each pair as
`w_E·E + w_K·K + w_S·S + w_C·C + w_X·X + w_U·U − w_R·R`, where `R` is *subtracted*
because higher remediation complexity should lower priority. Weights come from a
registry that contains both placeholder weights and (when fitted) calibrated
weights. A family of strategies (Section 7) provides baselines, ablations, an
evaluation-only oracle, and the proposed model.

**Capacity-constrained scheduler.** A five-phase scheduler consumes the ranking and
fills a window under capacity: (1) KEV-deadline override (bypasses blackout but
respects hard constraints), (2) reawaken expired/triggered risk acceptances,
(3) greedy fill under blackout windows, operational constraints, and an approval
policy, (4) patch-bundle expansion, and (5) a summary record.

**Audit log.** Every score and scheduling decision is written as an append-only,
hash-chained `AuditDecisionRecord` (SHA-256 chained), making the decision trail
tamper-evident and independently verifiable.

**Metrics and reporting.** An evaluation layer computes ranking, operational, and
audit metrics; a reporting layer renders tables and figures from a frozen,
verified result artifact.

## 6. System Architecture

The end-to-end pipeline is:

```
public feeds (NVD/EPSS/KEV/PoC, cached snapshots)
   → synthetic fleet generation (hosts, criticality, exposure, complexity)
      → vulnerability-host pair builder (no-future-leakage)
         → seven-feature frame (E, K, S, C, X, U, R)
            → prioritization strategies (ranking)
               → capacity-constrained scheduler (blackout/approval/risk)
                  → append-only hash-chained audit logs
                     → evaluation metrics
                        → freeze + reporting (tables/figures)
```

Two architectural properties are central. First, **tamper-evident audit logs**:
each decision record's hash chains to its predecessor, so any post-hoc
modification breaks verification; the integrity of every run is checked across all
strategies and seeds. Second, **frozen outputs**: a completed result set is sealed
with a content-addressed freeze manifest (per-file SHA-256), and all downstream
tables and figures are generated only from a freeze-verified artifact. Controlled
execution is guarded so that large runs require explicit confirmation, and
per-seed checkpointing allows deterministic resume.

## 7. Methodology

**Evaluation mode.** The reported primary evaluation uses bundled toy fixtures
(a small CVE/KEV/PoC set) together with the deterministic synthetic fleet
generator; no live feeds are called and no production data is used.

**Labels and temporal discipline.** Pairs are labeled over the half-open window
`(t0, t0 + H]`. Label A is positive if the CVE enters KEV or a public
proof-of-concept is first observed within the window; Label B is positive only on
proof-of-concept observation (bounding EPSS-KEV entanglement). Features are
observation-only at `t0`; a temporal train/gap/test split with an `H`-day gap
prevents label leakage across the boundary. The primary cell uses Label A.

**Calibration.** When fitted, weights are calibrated with regularized logistic /
ridge regression under time-block cross-validation, and negative coefficients are
clipped to zero. The reported primary run uses **placeholder weights**, not
calibrated weights; this is a deliberate, disclosed limitation (Sections 11, 15).

**Primary configuration.** The primary cell comprises a 10,000-host
public-sector-shaped fleet; a capacity ratio of 0.01, i.e. capacity
`= max(1, floor(0.01 × 10,000)) = 100` pair-actions per window; Label A; approver
Policy A; the primary blackout configuration; the AD/Entra default identity
configuration; and 30 random seeds. Thirteen strategies are evaluated: `random`,
`cvss_only`, `epss_only`, `kev_first`, `cvss_x_epss`, `cvss_plus_epss_plus_kev`,
`cve_max`, `cve_mean`, `cve_sum`, `proposed_full`, `proposed_no_criticality`,
`proposed_no_exposure`, and an evaluation-only `oracle`. The gradient-boosted-tree
comparator is excluded from the primary cell because no fitted model artifact was
supplied.

**Determinism and integrity.** All randomness derives from a master seed via
SHA-256-based sub-seed derivation; runs are reproducible. The 30-seed result is
sealed with a freeze manifest and passes strict structural inspection before any
table or figure is generated.

## 8. Synthetic Dataset Design

The synthetic fleet is generated from documented parameter distributions, not from
any real environment.

- **Host types and roles.** Hosts are allocated across roles (e.g. standard
  workstation, member server, domain controller, kiosk) with documented
  proportions, each carrying network-zone, identity-tier, and data-sensitivity
  attributes.
- **OS and software inventory.** Each host is assigned an OS and a software
  inventory drawn from catalogs, which determines vulnerability applicability and
  thus pair construction.
- **Patch state.** Hosts carry patch/remediation state so that already-remediated
  CVEs can be excluded from candidate pairs.
- **Criticality and IPES.** Telemetry-derived asset criticality combines role,
  identity privilege (an Identity Privilege Exposure Score), network exposure, and
  data sensitivity into the `C` feature.
- **Local exposure.** A per-pair local-exposure feature `X` reflects how reachable
  and exploitable the vulnerable component is on that specific host.
- **Remediation complexity.** A per-pair complexity feature `R` captures the
  operational cost and rollback risk of remediation.
- **Telemetry freshness and missingness.** Configurable CMDB staleness and
  telemetry-missingness rates model incomplete observability; missing continuous
  features are imputed and a missing KEV status defaults to zero with a recorded
  warning.

Synthetic data is necessary because real public-sector fleet telemetry is
sensitive and non-shareable; a documented generator makes the evaluation open and
repeatable while we explicitly bound the resulting external-validity claims.

## 9. Evaluation Metrics

- **Simulated expected exploited-host-days (EHD) and EEHDA.** For a positive pair,
  EHD is the number of days the pair remains open after its label fires, bounded by
  the evaluation end; lower is better. EEHDA reporting expresses each strategy in
  absolute terms and relative to random, relative to EPSS, and as a fraction of the
  oracle's headroom.
- **Ranking quality.** Precision@k, recall@k, and nDCG@k, with censored labels
  excluded from numerator and denominator.
- **KEV-deadline breach rate.** Fraction of KEV-due pairs not remediated by their
  deadline.
- **Capacity efficiency.** Fraction of scheduled (non-censored) pairs that are
  labeled positives.
- **Scheduler feasibility.** Whether windows are feasible (no infeasible
  escalations and capacity respected).
- **Risk-acceptance rate.** Share of decisions resolved as documented risk
  acceptance (POA&M-style).
- **Audit integrity.** Hash-chain validity of every audit log and per-strategy
  audit record counts.
- **Freeze/inspection checks.** Structural inspection (no duplicate rankings,
  contiguous ranks, schedules subset of rankings, capacity respected, no
  infinite/undocumented-NaN metrics) plus content-addressed freeze verification.

## 10. Compliance Mapping

The framework is designed to *support evidence for review* under common
public-sector control families; it does not *satisfy* or *prove* any control. We
map cautiously:

- **NIST SP 800-53 RA-5 (vulnerability monitoring/scanning)** [@nist80053r5]: pair-level prioritization and per-decision records support
  evidence for how scan findings are triaged.
- **NIST SP 800-53 SI-2 (flaw remediation)**: scheduling and remediation-timing
  records support evidence for remediation handling under capacity.
- **NIST SP 800-53 CM-8 (system component inventory)**: the synthetic fleet's
  host/software inventory models the asset context such evidence depends on.
- **NIST SP 800-53 AU-2 / AU-3 (audit events / content of records)**: the
  append-only, hash-chained decision records support evidence for auditable event
  capture with defined content.
- **NIST SP 800-40 Rev. 4 (patch management)** [@nist80040r4]:
  the capacity-constrained scheduling simulation reflects documented
  patch-management process structure.
- **CISA BOD 22-01** [@cisa_bod2201]: KEV-deadline handling and breach
  metrics support evidence for directive-driven prioritization.
- **CIS Controls v8** [@cis_controls_v8] and **CJIS Security Policy**
  [VERIFY: CJIS Security Policy version]: relevant control intent is
  acknowledged for context.

In every case the framing is "supports evidence for review," not "satisfies,"
"achieves," or "proves." Audit evidence is necessary for, but not equivalent to,
compliance.

## 11. Threats to Validity

- **Synthetic data and toy fixtures.** Results are produced on a synthetic fleet
  and a small bundled CVE/KEV/PoC fixture set; absolute magnitudes are properties
  of these inputs, not field measurements.
- **Placeholder weights.** The proposed model used uncalibrated placeholder
  weights; no method-quality conclusion can be drawn until calibration on
  historical exploitation data is performed.
- **No real production validation.** No live feeds were called and no real-world
  exploitation outcomes were used to validate predictions.
- **No commercial benchmark.** Commercial RBVM tools are acknowledged but not
  compared.
- **No sensitivity/robustness sweeps yet.** Only the single primary cell was run;
  Label B, alternative policies/blackouts, and parameter sweeps remain future work.
- **Feed caveats.** EPSS/KEV/PoC signals carry coverage, timing, and labeling
  biases; KEV/PoC-derived labels are proxies for exploitation, not ground-truth
  compromise.
- **Local-exposure observability.** Exposure and criticality assume telemetry/CMDB
  observability that may be incomplete or stale in practice.
- **Public-sector generalization.** The synthetic fleet may not reflect any
  specific agency's topology, identity tiering, or software mix.
- **Metric/oracle interpretation.** Under capacity constraints and the current EHD
  accounting, the label-prioritizing oracle is not a strict EHD lower bound, which
  is why some strategies report fraction-of-oracle values outside [0, 1]; these are
  reported as observed and treated as a metric/artifact caveat.

## 12. Original Contribution

The contribution of this work is methodological infrastructure for falsifiable
evaluation, framed conservatively:

- **A reproducible vulnerability-host pair benchmark** for public-sector-shaped
  endpoint fleets, integrating exploit intelligence, asset criticality, and
  endpoint exposure at the pair level, with deterministic seeding and a frozen,
  verifiable result artifact.
- **Audit-evidence-producing decision records.** Every score and scheduling
  decision is captured in an append-only, hash-chained log whose integrity is
  independently verifiable — supporting after-the-fact review (not a compliance
  determination).
- **A capacity-constrained scheduling simulation** with blackout windows, an
  approval policy, and documented risk acceptance, so that prioritization is
  evaluated jointly with operational limits (not autonomous remediation).
- **A frozen result artifact and freeze/verify protocol** that make every reported
  number traceable to a content-addressed, integrity-checked output set.
- **An honest, neutral empirical finding.** Under toy fixtures and placeholder
  weights, the proposed context-aware model is statistically indistinguishable
  from the EPSS baseline and does not outperform a random ordering; we report this
  plainly rather than tuning toward a positive result.

This work is explicitly **not** a claim of a superior prioritization model, **not**
autonomous remediation, and **not** a proof of compliance.

---

<!-- ===== Sections 13-17 + Abstract: Phase 18 draft, inlined verbatim ===== -->

## 13. Results

All quantitative statements below are taken directly from the Phase 17 report
artifacts generated from the frozen primary result
(`results/primary_full_v1/`, freeze verified): Table 1,
Table 2, Table 3,
Table 4, Table 5, Table 6, and
the figures Figure 1, Figure 4,
Figure 3, Figure 2, Figure 5.
Expected Exploited-Host-Days (EHD) is a *simulated* operational quantity for
which **lower is better**.

### 13.1 Experimental Integrity and Artifact Validation

The primary evaluation comprises 30 random seeds, 13 prioritization strategies,
and 11 metrics per (seed, strategy) cell, yielding 4,290 per-seed metric rows
(Table 1). The run produced 390 hash-chained audit logs
(30 seeds x 13 strategies), all of which verify (`audit_logs_valid = True`).
Strict structural inspection of the frozen output reported zero issues, and the
content-addressed freeze manifest verifies. There are no `NaN` and no infinite
metric values across the 4,290 rows. The per-window scheduling capacity (100
pair-actions) is respected by every strategy in every seed
(`max_scheduled_count = 100`, `scheduled_within_capacity = True`).

### 13.2 Operational EHD Outcomes

Table 2 reports mean and standard deviation of absolute EHD per
strategy across the 30 seeds; Figure 1 and
Figure 4 visualize the same quantities. Mean absolute EHD
clusters around ~1.12 x 10^6 simulated host-days for all strategies. The nominal
ordering (lowest/best first) places `cvss_only` (1.1190 x 10^6) and `oracle`
(1.1193 x 10^6) at the low end and `proposed_no_criticality` (1.1243 x 10^6) at
the high end. The total spread across all 13 strategies is about 5.3 x 10^3 host-
days (under 0.5% of the mean), while per-strategy standard deviations are
~3.4 x 10^3 - 5.2 x 10^3 (≈0.3-0.5% of the mean). The strategies are therefore
**not separable by absolute EHD** in this run. `proposed_full` (1.1217 x 10^6) is
marginally above (worse than) `random` (1.1213 x 10^6) and marginally below
(better than) `epss_only` (1.1219 x 10^6); neither gap is meaningful at this noise
scale. `cvss_only` records a slightly lower mean EHD than the `oracle` strategy;
because the oracle is a label-prioritizing ranker rather than a closed-form EHD
minimizer under capacity constraints, and the gap (~0.03%) is far inside the noise
band, we treat the oracle/non-oracle ordering as effectively flat here (Section 15).

### 13.3 Relative Performance Against EPSS

Table 3 and Figure 3 express each
non-oracle strategy relative to `epss_only`. Because lower EHD is better, a
negative `delta_vs_epss` (fewer host-days) is an improvement and a positive delta
is a regression. Several strategies show nominally lower EHD than `epss_only`
(`cvss_only` -0.26%, `cve_sum` -0.11%, `random` -0.056%, `cve_max` -0.050%,
`proposed_no_exposure` -0.030%, `proposed_full` -0.017%); others are nominally
worse; `kev_first` equals `epss_only`. `proposed_full`'s nominal improvement
(~0.017%, ~186 host-days) is an order of magnitude smaller than the seed standard
deviation and is **not evidence of beating EPSS**; `random` also appears nominally
"better than EPSS" by a similar margin, confirming these sub-0.1% gaps are noise.

### 13.4 Fraction-of-Oracle Analysis

Figure 2 and the `fraction_of_oracle_mean` column report each
strategy on the random(0)-to-oracle(1) scale. Observed values fall outside [0, 1]
for several strategies (`cvss_only` 1.18; `proposed_full` -0.23). Values below 0
indicate worse-than-random behavior under this metric; a value above 1 would
indicate better-than-oracle behavior, most plausibly a metric/artifact effect (the
oracle is not a strict EHD lower bound under capacity constraints here) rather than
a genuine result. The reporting layer surfaces these as a warning and reports them
**as observed** without clipping. Given the within-noise EHD spread, the
fraction-of-oracle ordering is not a reliable ranking signal in this run and is
reported for transparency only.

### 13.5 Ranking Metrics

Table 4 reports precision@k, recall@k, nDCG@k (k = 10).
`oracle` and `cvss_only` achieve perfect precision@10 and nDCG@10 (1.0);
`proposed_full` records precision@10 = 0.687 and nDCG@10 = 0.690, between
`epss_only` (0.633) and `random` (0.727). `random`'s top-10 precision exceeds
`proposed_full`'s, indicating that under the current toy fixtures (small CVE
catalog, high positive base rate) top-k precision does not discriminate between
methods. Recall@10 is uniformly small (~5 x 10^-4) by construction. No
ranking-quality superiority claim is drawn for the proposed model.

### 13.6 Operational and Audit Metrics

From Table 5: scheduler feasibility is 1.0 for every
strategy and seed; scheduled count equals capacity (100) throughout (capacity was
binding); capacity efficiency ranges 0.30-1.0 with `proposed_full` at 0.65 (below
`random` 0.73 and `cvss_only`/`oracle` 1.0); KEV-deadline breach rate is uniformly
high (~0.985-0.996), dominated by the capacity constraint rather than the policy;
risk-acceptance rate is near zero. From Table 6: every
strategy's audit log has a valid hash chain (`audit_hash_chain_valid = 1.0`); audit
record counts vary (~101-292). Per-record explanation completeness and per-feature
imputation rate were not included in this run's per-seed metric set and are noted
in Future Work.

### 13.7 Summary of Findings

- The benchmark **executes reproducibly** across 30 seeds (4,290 integrity-verified
  rows, 390 valid audit logs).
- The **audit and scheduler pipeline behaves correctly** end to end.
- The oracle/random reference bounds are **nearly flat**; with sub-0.5% inter-
  strategy spread, metrics are dominated by the capacity constraint and the
  toy-fixture positive base rate.
- The proposed linear model **did not dominate** the baselines: it is
  indistinguishable from `epss_only` and nominally worse than `random` on absolute
  EHD, capacity efficiency, and top-10 precision, under toy fixtures and
  placeholder weights.
- The artifact nonetheless **exposes measurable operational trade-offs** and
  provides a reproducible, auditable basis for the calibrated and sensitivity
  studies required to make any method-quality claim.

## 14. Discussion

**What the results support.** The evaluation demonstrates the feasibility of an
end-to-end, audit-evidence-producing benchmark for vulnerability-host pair
prioritization under capacity constraints. A 30-seed simulation runs
deterministically and reproducibly; the scheduler and append-only hash-chained
audit log operate correctly across all strategies and seeds; and operational
quantities (EHD/EEHDA, KEV breach, capacity efficiency, ranking metrics) are
computed from a frozen, integrity-verified artifact.

**What the results do not support.** They do **not** establish real-world
superiority of any strategy, do **not** show that `proposed_full` beats EPSS or
random, do **not** demonstrate autonomous remediation (the scheduler simulates
approval and timing, not patch execution), do **not** prove compliance, and do
**not** constitute production validation.

**Why neutral/negative results are still useful.** A benchmark that can show *when
added host context does not help* is more valuable than one tuned to confirm a
hypothesis. The finding that uncalibrated context-aware weights do not separate
from EPSS under toy inputs sets a clear falsification condition and motivates
calibrated, larger-window evaluation before any superiority claim.

**Implications for public-sector security operations.** (i) Per-decision audit
records and verifiable hash chains provide a traceable basis for review. (ii)
Capacity constraints and approval gates materially shape outcomes — here capacity,
not policy, dominated KEV breach. (iii) The vulnerability-host pair is a useful,
traceable unit of decision and explanation.

**Relationship to prior work.** This work does not claim to be first. It
complements prior context-aware/learning-based prioritization efforts such as Deep
VULMAN [VERIFY: Deep VULMAN source], VulRG [VERIFY: VulRG source], and VulnScore
[VERIFY: VulnScore source] by emphasizing a reproducible, public-sector-shaped benchmark
with per-decision audit evidence and an explicit freeze/verify protocol, rather
than a single tuned model result. [VERIFY scope/claims of each cited system in
citation finalization.]

## 15. Limitations

- **Synthetic, toy-fixture evaluation** — small bundled fixtures and a synthetic
  fleet, not real agency data; absolute magnitudes are fixture properties.
- **Placeholder (uncalibrated) weights** — no method-quality conclusion is possible
  until calibration on historical exploitation data is performed.
- **Differences within noise** — sub-0.5% inter-strategy spread, smaller than
  per-seed std; the study is not powered to separate strategies here.
- **No live or production data** — no live feeds called; no real exploitation
  outcomes used.
- **No commercial RBVM baseline** benchmarked.
- **No robustness or sensitivity sweeps yet** — only the single primary cell ran.
- **Feed caveats** — EPSS/KEV/PoC carry coverage/timing/labeling bias; labels are
  exploitation proxies, not ground-truth compromise.
- **Local-exposure observability assumptions** — telemetry/CMDB may be incomplete
  or stale in practice.
- **Synthetic fleet generalization** — may not reflect any specific agency.
- **Audit evidence is not compliance.**
- **Scheduler models timing, not patch success** — approvals/timing are simulated;
  patch success/rollback are not modeled in the EHD accounting.
- **Oracle is not a strict lower bound** under capacity + current EHD accounting,
  which is why some strategies report fraction-of-oracle outside [0, 1].
- **GBT comparator excluded** — no fitted model artifact was supplied.

## 16. Future Work

- Calibrated weights over larger historical windows (protocol already implemented).
- Label B / PoC-only robustness runs.
- Sensitivity sweeps (capacity ratio, blackout, approver policy, identity, CMDB
  staleness, telemetry missingness).
- Public-source point-in-time feed snapshots beyond toy fixtures (no-future-leakage
  preserved).
- Real-agency pilot under anonymized, approved telemetry with governance review.
- Additional learning-to-rank baselines and the GBT comparator (once fitted).
- Audit-quality metrics in the primary set; automated model-card / audit-report
  generation.
- Richer blackout/CAB models; patch-success/rollback in the EHD accounting; a
  corrected/clearly-bounded oracle.
- Power analysis to size seeds/effect once calibrated.
- Public release of the reproducibility artifact (code, configs, frozen result,
  freeze manifest).

## 17. Conclusion

We proposed and implemented an open, audit-evidence-producing benchmark framework
for context-aware vulnerability-host pair prioritization under capacity
constraints, integrating exploit-intelligence, asset-criticality, and
endpoint-exposure signals into a traceable, pair-level decision unit. The
evaluation demonstrates reproducible end-to-end execution across 30 seeds and
validates the artifact's inspection, scheduling, and append-only audit pipeline:
390 audit logs verify, scheduling stays within capacity, and the frozen result
passes strict inspection with zero issues. The empirical results should be read as
benchmark validation under synthetic, toy-fixture conditions with uncalibrated
weights, not as evidence of real-world superiority; in this configuration the
proposed model is indistinguishable from the EPSS baseline and does not outperform
a random ordering, with all inter-strategy differences inside seed-to-seed noise.
The primary contribution is therefore the reproducible, auditable evaluation
structure itself — a falsifiable basis on which calibrated, production-scale
studies can build. Establishing whether context-aware prioritization yields
operational benefit over EPSS-style baselines remains future work requiring
calibration, robustness and sensitivity analysis, and external validation.

---

## Tables and Figures (generated; insert at final formatting)

Tables (CSV/Markdown/LaTeX in `paper/tables/`):
Supplementary Table A1, Table 2,
Table 3, Table 4,
Table 5, Table 6, Table 1.

Figures (PNG/PDF in `paper/figures/`): Figure 1,
Figure 4, Figure 3, Figure 2,
Figure 5.

Provenance: `results/primary_full_v1/report/report_manifest.json`
(freeze SHA recorded; freeze verified).
