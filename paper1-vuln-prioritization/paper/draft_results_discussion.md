<!--
Phase 18 draft: Results, Discussion, Limitations, Future Work, Conclusion, Abstract.
Drafted ONLY from the frozen primary artifact (results/primary_full_v1) and the
Phase 17 generated tables/figures (paper/tables/, paper/figures/). No numbers are
hand-invented; every quantitative statement traces to a named table/figure.
Citations are placeholders ([CITATION], [VERIFY]); none are fabricated.
This is a software/benchmark research draft. No EB1A/USCIS language appears here.

IMPORTANT CONTEXT (carried into the prose as a limitation, not hidden):
The frozen run uses bundled toy fixtures and PLACEHOLDER linear weights
(w_logit_placeholder), not calibrated weights. Inter-strategy EHD differences are
sub-0.5% of the mean and well within per-seed standard deviation, i.e. not
distinguishable from noise. proposed_full does NOT dominate the baselines here.
-->

# 13. Results

All quantitative statements below are taken directly from the Phase 17 report
artifacts generated from the frozen primary result
(`results/primary_full_v1/`, freeze verified): `table_acceptance_checks`,
`table_ehd_primary`, `table_strategy_comparison_vs_epss`,
`table_ranking_metrics`, `table_operational_metrics`, `table_audit_metrics`, and
the figures `fig_ehd_by_strategy`, `fig_ehd_distribution_selected`,
`fig_relative_to_epss`, `fig_fraction_of_oracle`, `fig_proposed_vs_epss_by_seed`.
Expected Exploited-Host-Days (EHD) is a *simulated* operational quantity for
which **lower is better**.

## 13.1 Experimental Integrity and Artifact Validation

The primary evaluation comprises 30 random seeds, 13 prioritization strategies,
and 11 metrics per (seed, strategy) cell, yielding 4,290 per-seed metric rows
(Table `table_acceptance_checks`). The run produced 390 hash-chained audit logs
(30 seeds x 13 strategies), all of which verify (`audit_logs_valid = True`).
Strict structural inspection of the frozen output reported zero issues, and the
content-addressed freeze manifest verifies. There are no `NaN` and no infinite
metric values across the 4,290 rows. The per-window scheduling capacity (100
pair-actions) is respected by every strategy in every seed
(`max_scheduled_count = 100`, `scheduled_within_capacity = True`). These checks
establish that the downstream results are computed over a complete, integrity-
verified artifact rather than partial or corrupted output.

## 13.2 Operational EHD Outcomes

Table `table_ehd_primary` reports mean and standard deviation of absolute EHD per
strategy across the 30 seeds; `fig_ehd_by_strategy` and
`fig_ehd_distribution_selected` visualize the same quantities. Mean absolute EHD
clusters tightly around ~1.12 x 10^6 simulated host-days for all strategies. The
nominal ordering (lowest/best first) places `cvss_only` (1.1190 x 10^6) and
`oracle` (1.1193 x 10^6) at the low end and `proposed_no_criticality`
(1.1243 x 10^6) at the high end. The **total spread across all 13 strategies is
about 5.3 x 10^3 host-days, i.e. under 0.5% of the mean**, while per-strategy
standard deviations are ~3.4 x 10^3 - 5.2 x 10^3 (roughly 0.3-0.5% of the mean).
Consequently, the strategies are **not separable by absolute EHD** in this run:
the between-strategy differences are comparable to or smaller than the within-
strategy seed-to-seed variation.

`proposed_full` has a mean absolute EHD of 1.1217 x 10^6, which is marginally
*above* (worse than) `random` (1.1213 x 10^6) and marginally *below* (better
than) `epss_only` (1.1219 x 10^6). We do **not** interpret either gap as
meaningful given the noise scale above. Notably, `cvss_only` records a slightly
lower mean EHD than the `oracle` strategy; because the oracle here is a label-
prioritizing ranker rather than a closed-form EHD minimizer under capacity
constraints, and because the gap (~0.03%) is far inside the noise band, we treat
the oracle/non-oracle ordering as effectively flat in this configuration and
flag it as a metric/artifact caveat (Section 15).

## 13.3 Relative Performance Against EPSS

Table `table_strategy_comparison_vs_epss` and `fig_relative_to_epss` express each
non-oracle strategy relative to the `epss_only` baseline. Direction convention:
because lower EHD is better, a **negative `delta_vs_epss` (fewer host-days) is an
improvement over EPSS**, and a positive delta is a regression. Under this
convention, several strategies show nominally lower EHD than `epss_only`
(`cvss_only` -0.26%, `cve_sum` -0.11%, `random` -0.056%, `cve_max` -0.050%,
`proposed_no_exposure` -0.030%, `proposed_full` -0.017%), while others are
nominally worse (`cvss_plus_epss_plus_kev`, `cvss_x_epss`, `cve_mean`,
`proposed_no_criticality`). `kev_first` is identical to `epss_only` in this run.

Two honest observations follow. First, `proposed_full`'s nominal improvement over
EPSS (~0.017%, ~186 host-days) is an order of magnitude smaller than the seed
standard deviation and is therefore **not evidence that the proposed model beats
EPSS**. Second, `random` also appears nominally "better than EPSS" by a similar
tiny margin, which by itself demonstrates that these sub-0.1% gaps reflect noise
rather than method quality.

## 13.4 Fraction-of-Oracle Analysis

`fig_fraction_of_oracle` and the `fraction_of_oracle_mean` column of
`table_ehd_primary` report each strategy's position on the random-to-oracle
scale, defined as (random_EHD - strategy_EHD) / (random_EHD - oracle_EHD), where
0 corresponds to random and 1 to oracle. Observed values fall outside [0, 1] for
several strategies: `cvss_only` reads 1.18 (above 1, nominally "better than
oracle") and `proposed_full` reads -0.23 (below 0, nominally "worse than
random"). Values below 0 indicate worse-than-random behavior under this metric;
a value above 1 would indicate better-than-oracle behavior, which is most
plausibly a metric/artifact effect (the oracle is not a strict EHD lower bound
under capacity constraints in this configuration) rather than a genuine result.
The Phase 17 reporting layer surfaces these out-of-range values as a warning and
reports them **as observed** without rescaling or clipping. Because the
underlying EHD spread is within noise (Section 13.2), the fraction-of-oracle
ordering is not a reliable ranking signal in this run and is reported for
completeness and transparency only.

## 13.5 Ranking Metrics

Table `table_ranking_metrics` reports precision@k, recall@k, and nDCG@k (with
k = 10) per strategy. `oracle` and `cvss_only` achieve perfect precision@10 and
nDCG@10 (1.0); `proposed_full` records precision@10 = 0.687 and nDCG@10 = 0.690,
which sits between `epss_only` (0.633) and `random` (0.727). `random`'s top-10
precision exceeds `proposed_full`'s, again indicating that, under the current
toy fixtures (a small CVE catalog with a high positive base rate), top-k
precision is not discriminating between methods. Recall@10 is uniformly small
(~5 x 10^-4) by construction, because the positive set is far larger than k = 10.
We therefore do not draw any ranking-quality superiority claim for the proposed
model from this run.

## 13.6 Operational and Audit Metrics

Operational metrics (Table `table_operational_metrics`):

- **Scheduler feasibility** is 1.0 for every strategy and seed: scheduling
  completed within capacity with no infeasible escalations.
- **Scheduled count** equals the configured capacity (100) for every strategy,
  i.e. capacity was the binding constraint throughout.
- **Capacity efficiency** (fraction of scheduled pairs that are labeled
  positives) ranges from 0.30 (`proposed_no_criticality`) to 1.0 (`cvss_only`,
  `oracle`); `proposed_full` is 0.65 and `random` is 0.73. Here too
  `proposed_full` does not exceed `random`.
- **KEV-deadline breach rate** is uniformly high (~0.985-0.996) across all
  strategies, because the per-window capacity (100) is far below the number of
  KEV-due pairs; the binding capacity constraint, not the prioritization policy,
  dominates this metric in the current configuration.
- **Risk-acceptance rate** is near zero for all strategies (0-0.004).

Audit metrics (Table `table_audit_metrics`): every strategy's audit log has a
valid hash chain (`audit_hash_chain_valid = 1.0` for all 13 strategies x 30
seeds). Audit record counts vary by strategy (≈101-292 records on average),
reflecting differing numbers of logged decisions. Two audit-quality metrics
defined in the evaluation layer (per-record explanation completeness and
per-feature imputation rate) were not included in the per-seed metric set written
by this run and are therefore not reported here; their inclusion is noted in
Future Work.

## 13.7 Summary of Findings

- The benchmark **executes reproducibly** across 30 seeds, producing 4,290
  integrity-verified metric rows and 390 valid hash-chained audit logs.
- The **audit and scheduler pipeline behaves correctly** end to end: chains
  verify, scheduling is feasible, and capacity is never exceeded.
- The oracle/random reference bounds are **nearly flat** in this configuration;
  combined with sub-0.5% inter-strategy spread, this shows the metrics are
  dominated by the capacity constraint and the toy-fixture positive base rate.
- The proposed linear model (`proposed_full`) **did not dominate** the baselines:
  it is statistically indistinguishable from `epss_only` and nominally worse than
  `random` on absolute EHD, capacity efficiency, and top-10 precision, under
  toy-fixture inputs and placeholder (uncalibrated) weights.
- The artifact nonetheless **exposes measurable operational trade-offs** and
  provides a reproducible, auditable basis for the calibrated and sensitivity
  studies required to make any method-quality claim.

---

# 14. Discussion

**What the results support.** The evaluation demonstrates the *feasibility* of an
end-to-end, audit-evidence-producing benchmark for vulnerability-host pair
prioritization under capacity constraints. A 30-seed simulation runs
deterministically and reproducibly; the scheduler and append-only hash-chained
audit log operate correctly across all strategies and seeds; and operational
quantities such as simulated EHD/EEHDA, KEV-deadline breach rate, capacity
efficiency, and ranking metrics can be computed from a frozen, integrity-verified
artifact. The freeze-and-verify workflow makes the reported numbers traceable to
a specific, content-addressed result set.

**What the results do not support.** The results do **not** establish real-world
superiority of any strategy, do **not** show that `proposed_full` beats EPSS or
random, do **not** demonstrate autonomous remediation (the scheduler simulates
approval and timing, not patch execution), do **not** prove compliance, and do
**not** constitute production validation. The current inter-strategy differences
are within seed-to-seed noise and were produced with placeholder weights on toy
fixtures.

**Why neutral/negative results are still useful.** A benchmark that can show *when
added host context does not help* is more scientifically valuable than one tuned
to confirm a hypothesis. The finding that uncalibrated context-aware weights do
not separate from EPSS under toy inputs is itself informative: it sets a clear
falsification condition and motivates calibrated, larger-window evaluation before
any superiority claim. Reporting the out-of-range fraction-of-oracle values and
the near-flat oracle bound, rather than hiding them, is part of the framework's
intended discipline.

**Implications for public-sector security operations.** Three structural points
hold independent of the (currently inconclusive) method comparison. (i)
Decision-level audit records and verifiable hash chains provide a traceable basis
for after-the-fact review. (ii) Capacity constraints and approval gates
materially shape outcomes — here capacity, not policy, dominated KEV breach — so
prioritization must be evaluated jointly with operational limits. (iii) The
vulnerability-host *pair* is a useful, traceable unit of decision and explanation.

**Relationship to prior work.** This work does not claim to be first. It
complements prior context-aware and learning-based prioritization efforts such as
Deep VULMAN [CITATION], VulRG [CITATION], and VulnScore [CITATION] by emphasizing
a reproducible, public-sector-shaped *benchmark* with per-decision audit evidence
and an explicit freeze/verify protocol, rather than a single tuned model result.
The contribution is methodological infrastructure for falsifiable evaluation, not
a new state-of-the-art score. [VERIFY: confirm scope/claims of each cited system
during Phase 19 citation finalization.]

---

# 15. Limitations

- **Synthetic, toy-fixture evaluation.** The frozen run uses a small bundled toy
  vulnerability/KEV/PoC fixture set and a deterministic synthetic fleet, not real
  agency data. Absolute EHD magnitudes and base rates are properties of these
  fixtures, not field measurements.
- **Placeholder (uncalibrated) weights.** The proposed linear model used
  placeholder weights (`w_logit_placeholder`), not weights calibrated on
  historical exploitation data. No method-quality conclusion can be drawn until
  calibration is performed.
- **Differences within noise.** Inter-strategy EHD differences are sub-0.5% and
  smaller than per-seed standard deviation; the study is not powered to separate
  strategies in this configuration.
- **No live or production data.** No live feed clients were called and no external
  real-world exploitation outcomes were used to validate predictions.
- **No commercial RBVM baseline.** The comparison set is limited to documented
  open strategies; commercial risk-based vulnerability-management tools are not
  benchmarked.
- **No robustness or sensitivity sweeps yet.** Only the single primary cell
  (Label A, Policy A, primary blackout, AD/Entra identity) was executed; Label B,
  alternative policies/blackouts, and parameter sweeps are not yet run.
- **Feed caveats.** EPSS, KEV, and PoC signals carry their own coverage, timing,
  and labeling biases; the KEV/PoC-derived labels are proxies for exploitation,
  not ground-truth compromise.
- **Local-exposure observability assumptions.** Exposure and criticality features
  assume telemetry/CMDB observability that may be incomplete or stale in practice.
- **Synthetic fleet generalization.** The public-sector-shaped synthetic fleet may
  not reflect any specific agency's topology, identity tiering, or software mix.
- **Audit evidence is not compliance.** Verifiable audit logs support review but do
  not by themselves establish conformance with any regulation or framework.
- **Scheduler models timing, not patch success.** Approvals and remediation timing
  are simulated; actual patch deployment success/failure and rollback are not
  modeled in the EHD accounting used here.
- **Oracle is not a strict lower bound.** Under capacity constraints and the
  current EHD accounting, the label-prioritizing oracle is not guaranteed to be
  EHD-minimal, which is why some strategies report fraction-of-oracle outside
  [0, 1]. This is a metric/artifact limitation to address before relying on the
  fraction-of-oracle scale.
- **GBT comparator excluded.** The gradient-boosted-tree comparator was excluded
  from the primary cell because no fitted model artifact was supplied; it is not
  part of these results.

---

# 16. Future Work

- **Calibrated weights over larger historical windows**, replacing placeholder
  weights, with the calibration protocol and temporal splits already implemented.
- **Label B / PoC-only robustness** runs to bound EPSS-KEV entanglement.
- **Sensitivity sweeps** over capacity ratio, blackout configuration, approver
  policy, identity configuration, CMDB staleness, and telemetry missingness.
- **Public-source feed snapshots** (point-in-time NVD/EPSS/KEV/PoC) beyond the toy
  fixtures, preserving the no-future-leakage discipline.
- **Real-agency pilot** under anonymized and approved telemetry, with governance
  review, to test external validity.
- **Additional learning-to-rank baselines** and the **GBT comparator** once a
  fitted model artifact is available, for a fuller comparison.
- **Audit-quality metrics in the primary set**: per-record explanation
  completeness and per-feature imputation rate, plus automated model-card and
  audit-report generation.
- **Richer operational models**: more realistic blackout/CAB calendars,
  patch-success/rollback modeling in the EHD accounting, and a corrected or
  clearly-bounded oracle for the fraction-of-oracle scale.
- **Power analysis** to determine the seed count and effect size needed to
  separate strategies once calibrated.
- **Public release of the reproducibility artifact** (code, configs, frozen
  result, freeze manifest) to enable independent verification.

---

# 17. Conclusion

We proposed and implemented an open, audit-evidence-producing benchmark framework
for context-aware vulnerability-host pair prioritization under capacity
constraints, integrating exploit-intelligence, asset-criticality, and
endpoint-exposure signals into a traceable, pair-level decision unit. The
evaluation demonstrates reproducible end-to-end execution across 30 seeds and
validates the artifact's inspection, scheduling, and append-only audit pipeline:
390 audit logs verify, scheduling stays within capacity, and the frozen result
passes strict inspection with zero issues. The empirical results should be read
as **benchmark validation under synthetic, toy-fixture conditions with
uncalibrated weights**, not as evidence of real-world superiority; in this
configuration the proposed model is indistinguishable from the EPSS baseline and
does not outperform a random ordering, with all inter-strategy differences inside
seed-to-seed noise. The primary contribution is therefore the reproducible,
auditable evaluation structure itself — a falsifiable basis on which calibrated,
production-scale studies can build. Establishing whether context-aware
prioritization yields operational benefit over EPSS-style baselines remains future
work requiring calibration, robustness and sensitivity analysis, and external
validation.

---

# Abstract (draft)

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
studies can be built. [VERIFY all numeric values against the frozen Phase 17
tables before submission.]
