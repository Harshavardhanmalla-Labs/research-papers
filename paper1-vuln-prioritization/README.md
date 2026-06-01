# paper1-vuln-prioritization

Reference implementation accompanying the paper:

**Context-Aware Vulnerability Prioritization for Government Endpoint Fleets:
Integrating Exploit Intelligence, Asset Criticality, and Endpoint Telemetry.**

## Purpose

This repository will host an open, reproducible, audit-evidence-producing
framework for ranking vulnerability-host pairs in public-sector-shaped
endpoint environments. The framework integrates:

- exploit-intelligence signals (EPSS, CISA KEV)
- CVE severity (CVSS)
- telemetry-derived asset criticality (role, identity, network, data)
- per-pair local exposure
- capacity-constrained remediation scheduling
- hash-chained audit-decision records

Evaluation is conducted on synthetic fleets generated from documented
parameter distributions combined with real public vulnerability and
exploit-intelligence feeds. No production data, no employer-specific
data, and no real public-sector environment data is included.

## Data warning

No real production fleet data is included in this repository.
Every host, every fleet, every criticality value, and every exposure
indicator used in evaluation is synthetic and generated from documented
parameter files. Real data from external feeds (NVD, FIRST EPSS, CISA
KEV, and optionally ExploitDB subject to upstream license terms) is
fetched by scripts in `scripts/` and cached locally; the cached
snapshots are bundled with the artifact release subject to the
respective upstream licenses.

## Installation

Python 3.11 is required.

```bash
make install-dev
```

This installs the `paper1` package in editable mode together with
development dependencies (pytest, ruff).

A Docker image is provided:

```bash
docker build -t paper1 .
docker run --rm paper1
```

## Tests

```bash
make test
```

## Reproducibility philosophy

Every result reported in the paper is to be reproducible from this
repository at a fixed commit, with bundled feed snapshots and pinned
dependencies, by running the documented experiment commands. Every
random choice is seeded from a master seed declared in the experiment
configuration. Every audit record is hash-chained for tamper evidence.

## Current implementation status

**Phase 17 (this commit): paper tables and figures from the frozen artifact.**

- `paper1.reporting.load_frozen_primary_results(output_dir)` — verifies the
  freeze manifest, then loads ONLY the frozen aggregate metric frames
  (`per_seed_metrics`, `aggregated_metrics`, `eehda_report`) + manifest. It
  refuses to read an unverified/missing freeze and never touches raw
  per-strategy files.
- `paper1.reporting.primary_tables` — 7 paper tables (CSV + Markdown +
  LaTeX): metric summary, per-strategy EHD, strategy-vs-`epss_only`
  comparison (EHD encoded consistently as **lower-is-better**), ranking
  metrics, operational metrics, audit metrics, and an acceptance/integrity
  table.
- `paper1.reporting.primary_figures` — 5 matplotlib (no seaborn, Agg
  backend) figures saved as PNG + PDF: EHD-by-strategy bar, fraction-of-
  oracle, relative-to-`epss_only`, selected-strategy EHD boxplot, and a
  per-seed proposed_full-vs-`epss_only` scatter. Titles are neutral and
  descriptive (no claims).
- `paper1.reporting.generate_primary_report_bundle(...)` — writes everything
  under `results/primary_full_v1/report/{tables,figures}` and mirrors it into
  `paper/{tables,figures,report}`, plus `summary.md` and
  `report_manifest.json` (source dir, freeze SHA, row counts, file lists,
  warnings). The derived `report/` subtree is excluded from the freeze set,
  so the freeze still verifies after a report is generated.

```bash
make verify-primary-freeze PYTHON=.venv/bin/python
make primary-report        PYTHON=.venv/bin/python
```

**These are reproducible renderings of the frozen numbers, not paper
claims.** Interpretation/Results prose belongs to Phase 18. Robustness
re-runs and sensitivity sweeps remain out of scope.

**Phase 14: primary result inspector, freeze manifest, comparison.**

- `paper1.experiments.inspect.inspect_primary_output(output_dir, strict)` —
  reads a primary output *from disk* and returns an `InspectionReport`
  (`passed`, per-severity issue counts, audit-log validity). Catches silent
  pipeline failures: missing manifest/metrics/summary, missing strategy
  files, broken audit-log hash chains, duplicate ranking `pair_id`,
  non-contiguous ranks, scheduled pairs absent from the ranking, infinite
  metric values, undocumented NaNs, oracle EHD worse than random, non-finite
  `proposed_full` EHD, and EEHDA column/finiteness problems. `strict` makes
  warnings fail too. Documented NaN cases (KEV breach / capacity efficiency /
  ranking metrics with a zero denominator) are accepted.
- `freeze_primary_results(output_dir)` / `verify_freeze_manifest(output_dir)`
  — write/verify a content-addressed `FREEZE_MANIFEST.json` (per-file
  SHA-256, deterministic order). Verification fails on any changed, missing,
  or extra file (extras can be allowed via an explicit ignore list). Refuses
  to overwrite an existing freeze without `overwrite=True`; never modifies
  result files.
- `compare_primary_runs(a, b)` — compares seed sets, strategies, audit
  validity, and per-(seed, strategy, metric) determinism on common seeds
  (one-seed vs three-seed, or two reruns).
- `scripts/inspect_primary_results.py` — `--strict`, `--freeze`,
  `--verify-freeze`, `--compare-other`; exits nonzero under `--strict` when
  the report does not pass, or when freeze verification fails.

Safe workflow (frozen outputs are what later tables/figures consume):

```bash
make primary-one-seed        # then:
make inspect-primary
make primary-three-seeds     # then:
make inspect-primary
# only then the full pre-registered controlled run, then:
make inspect-primary
make freeze-primary          # writes FREEZE_MANIFEST.json
make verify-primary-freeze   # before generating any table/figure
```

`make inspect-primary` inspects `results/primary_full_v1` if it exists, and
fails clearly ("run primary-one-seed first") otherwise. **No paper claims or
Results text are produced here.** Robustness re-runs and sensitivity sweeps
remain out of scope.

**Phase 13: controlled primary execution behind a confirm flag.**

Non-dry-run primary execution is now enabled, but only behind two locks: the
config must set `confirm_full_run=true` AND the caller must pass an explicit
`confirm` plus an explicit `max_seeds`. A confirmed run **never defaults to
all seeds**, runs of more than three seeds require `allow_large_run`, and a
30-seed run requires `allow_large_run` explicitly. There is deliberately
**no full-30-seed Makefile target**.

- `paper1.experiments.primary.run_primary_confirmed(config, max_seeds, ...)` —
  executes a controlled cell via the shared per-seed pipeline (the Phase 11
  smoke pipeline, reused). Resumes completed seeds from checkpoints; a
  checkpoint whose output files are missing is re-run (with a warning), not
  trusted. Returns `seeds_requested` / `seeds_run` /
  `seeds_skipped_from_checkpoint` / `runtime_seconds` and a note that the
  output is not a final result until all pre-registered seeds complete.
- `plan_primary_run(config, max_seeds)` — result-free validation + estimate;
  creates no directories and runs nothing.
- `run_primary_experiment(..., confirm, max_seeds, allow_large_run)` — routes
  dry-run configs to the dry-run; a non-dry config without `confirm` raises
  `RuntimeError`; with `confirm` it runs the controlled cell.
- `configs/primary_full_template.yaml` — the intended 30-seed / 10,000-host
  cell (`confirm_full_run: true`); executable only with `--confirm-full-run`
  and `--max-seeds`.

Safe run order (no automatic full run, no live feeds):

```bash
make primary-plan          # validate + estimate; runs nothing
make primary-one-seed      # 1 seed; inspect results/primary_full_v1/
make primary-three-seeds   # 3 seeds; inspect again
# only then, manually and intentionally:
python scripts/run_primary_experiment.py \
    --config configs/primary_full_template.yaml \
    --confirm-full-run --max-seeds 30 --allow-large-run
```

**No paper result exists** until the full pre-registered run completes and
outputs are frozen. Robustness re-runs and sensitivity sweeps are still
out of scope.

**Phase 12: primary experiment runner skeleton with guardrails.**

- `paper1.experiments.primary` — the *infrastructure* for the primary
  experiment cell (10,000-host fleet, capacity ratio 0.01, 30 seeds), but
  the full workload is **intentionally not runnable** in this phase.
  - `PrimaryRunConfig` — validated config with hard guardrails: a non-dry
    run requires `confirm_full_run`; the seed count may not exceed
    `max_seeds_allowed_without_confirm`; `fleet_size` may not reach
    `primary_target_fleet_size`; `allow_live_fetch` must be false;
    `gbt_comparator` requires a fitted `gbt_model_artifact`. Capacity =
    `max(capacity_min, floor(fleet_size * capacity_ratio))`.
  - `estimate_primary_runtime` — heuristic compute footprint (seeds,
    strategies, windows, scheduler invocations, output files, pair-count
    band) with warnings. Runs no workload.
  - `validate_primary_inputs` — no live fetch, local snapshots when
    required, toy fixtures present for a dry-run, safe output dir,
    supported strategies, excluded strategies not re-included.
  - `make_primary_output_layout` + checkpoint helpers
    (`checkpoint_path` / `write_checkpoint` / `read_checkpoint` /
    `checkpoint_exists` / `clear_checkpoint`) — a checkpoint/resume
    skeleton (a completed seed is read back from its checkpoint).
  - `run_primary_dryrun` — a tiny, guardrailed dry-run (250-host fleet,
    1 seed, capacity 2) that **reuses the Phase 11 smoke per-seed
    pipeline** (`run_smoke_seed`) and writes the primary output layout.
  - `run_primary_experiment` — routes dry-run configs to the dry-run; a
    non-dry-run without `confirm` raises `RuntimeError`. (In Phase 12 a
    confirmed non-dry run raised `NotImplementedError`; Phase 13 replaces
    that with controlled execution — see above.)
- `configs/primary_dryrun.yaml` — dry-run config; documents the intended
  full primary cell in comments (not runnable).

Output layout (`results/primary_dryrun_v1/`): `manifest.json`,
`checkpoints/`, `metrics/{per_seed,aggregated,eehda_report}.csv`,
`summary.md`, and per-seed artifacts identical to the smoke layout.

**Dry-run infrastructure only — NOT a paper result.** No robustness re-runs,
no sensitivity sweeps, no full primary execution. No live feeds.

```bash
make primary-dryrun
```

**Phase 11: end-to-end smoke experiment runner.**

- `paper1.experiments.smoke` — a tiny, deterministic runner that wires the
  full pipeline on bundled toy fixtures with **no live feeds**:
  synthetic fleet → toy vulnerabilities → pair construction → Label A/B →
  temporal-split assignment → seven-feature frame → ranking strategies →
  capacity-constrained scheduler → evaluation metrics → per-seed metric
  frame → statistical-frame validation.
  - `run_smoke_seed(seed, config, output_dir)` runs one seed and writes
    per-seed artifacts; `run_smoke_experiment(config_path)` runs all seeds,
    writes the manifest / aggregated metrics / EEHDA report / summary, and
    re-verifies every audit log.
- `paper1.experiments.common` — result-directory layout, a provenance
  `ExperimentManifest` (config + fixture SHA-256 hashes, code version), a
  parquet-or-CSV writer, and output validators (`validate_strategy_outputs`,
  `validate_audit_logs`). The runner fails loudly on any validation error.
- `configs/experiment_smoke.yaml` — 3 seeds, 100-host fleet, capacity 20,
  Label A, Policy A, primary blackout, strategies `random / epss_only /
  kev_first / proposed_full / oracle`.

Outputs (under `results/smoke_experiment_v1/`): `manifest.json`,
`summary.md`, `metrics/{per_seed_metrics,aggregated_metrics,eehda_report}.csv`,
and per-seed `pairs/features/labels` plus per-strategy
`ranking/schedule_history/audit_log/metrics`.

**This is a pipeline verification, NOT a paper result.** No primary
experiment, robustness re-runs, or sensitivity sweeps are run here, and no
results are fabricated. Each audit log's hash chain is verified, scheduling
never exceeds capacity, and rankings carry no duplicate pair IDs.

Fixture-date note: the toy fixtures are pinned to `t0 = 2025-06-01` (the toy
KEV/PoC events fall in `(2025-06-01, 2025-07-01]`), so the smoke window is
shifted forward one year from the Phase-11 brief's `2024` suggestion to stay
fixture-consistent — otherwise every toy vulnerability would be a future
disclosure and yield zero pairs. Documented `np.nan` metric cases: KEV breach
rate / capacity efficiency when no eligible pairs exist, and ranking metrics
when all top-k items are censored.

```bash
make experiment-smoke
```

**Phase 10 (previous commit): statistical analysis helpers.**

- `paper1.evaluation.statistical_tests` — pure, deterministic functions
  for paired comparison of per-seed metric results. These functions only
  *compute* statistics; interpretation of significance and the
  metric-dependent direction of "better" belong to the reporting layer.
  - `clean_numeric_array`, `paired_arrays` — coerce/align per-seed values;
    `paired_arrays` pivots seed × strategy, drops seeds missing either
    arm (with a warning), and requires ≥2 paired seeds.
  - `paired_mean_difference`, `relative_difference`, `paired_cohens_d` —
    paired difference summaries; `relative_difference` returns NaN on a
    zero baseline; `paired_cohens_d` returns 0 (zero diffs) or ±inf
    (constant non-zero diff).
  - `wilcoxon_signed_rank` — paired Wilcoxon signed-rank test; returns
    `(0.0, 1.0)` when all differences are zero.
  - `holm_bonferroni` — family-wise Holm-Bonferroni correction over a
    dict of comparison p-values.
  - `bootstrap_ci` (percentile), `bootstrap_ci_bca` (scipy BCa with
    percentile fallback on degeneracy), and `paired_bootstrap_ci`
    (resamples paired rows together) — all seeded via `make_rng` and
    therefore deterministic.
  - `compare_to_baseline` / `compare_many_to_baseline` — assemble a
    `StatTestResult` (or a DataFrame across candidates with Holm-adjusted
    p-values) for one metric against a baseline strategy.
  - `minimum_detectable_effect` — approximate standardized paired effect
    size detectable at a given n, alpha, and power (statsmodels
    `TTestPower`).
  - `validate_per_seed_metric_frame` — guard for the per-seed metric
    frame (required columns, no nulls in keys, numeric values, no
    duplicate (seed, strategy, metric[, cell]) rows).

**Experiment runners and real experiment aggregation are NOT in this
phase** — Phase 10 ships statistical *helpers* only, exercised on a
synthetic toy frame. No primary experiments have been run and no paper
results have been produced.

```bash
make stats-smoke
```

**Phase 9 (previous commit): evaluation metrics layer.**

- `paper1.evaluation.ranking_metrics` — precision@k, recall@k, nDCG@k,
  a multi-k ranking curve, and rank churn. Censored (`pd.NA`) labels are
  excluded from numerator and denominator.
- `paper1.evaluation.eehda` — **simulated** expected exploited-host-days:
  `compute_pair_ehd`, `compute_ehd`, and an `eehda_report` with the four
  reporting forms (absolute, relative-to-random, relative-to-EPSS,
  fraction-of-oracle). Positive pairs not remediated within the window
  are charged to the evaluation end; non-positive/censored pairs
  contribute zero.
- `paper1.evaluation.compliance_metrics` — KEV-deadline breach rate,
  KEV-remediation latency (median/p95/count, optional criticality
  filter), and capacity efficiency.
- `paper1.evaluation.audit_metrics` — audit explanation completeness,
  per-feature imputation rate, hash-chain validity, and record-count by
  type (accepts `AuditDecisionRecord` objects, dicts, or a JSONL path).
- `paper1.evaluation.scheduler_metrics` — scheduler feasibility rate,
  risk-acceptance rate, POA&M review-trigger compliance, and count
  helpers.
- `paper1.evaluation.metrics` — shared helpers plus simple per-seed
  aggregation (mean / std / count).

The "expected" in EEHDA is the expectation under the simulation; every
metric here is computed on synthetic/toy inputs. Statistical tests over
these metrics arrive in Phase 10 (above).

```bash
make metrics-smoke
```

**Phase 8 (previous commit): capacity-constrained scheduler.**

- `paper1.scheduler.schedule_window` — a five-phase greedy scheduler:
  (1) KEV-deadline override (bypasses blackout, still respects group caps
  and domain-controller staging); (2) reawaken expired or trigger-fired
  risk acceptances; (3) greedy fill under blackout windows, operational
  constraints, and a human-approval policy; (4) patch-bundle expansion;
  (5) a window-summary audit record.
- `paper1.scheduler.constraints` — group caps (keyed by `group_id`,
  falling back to `host_role`), dependency-group prerequisites, and
  domain-controller staged rollout (first DC schedulable; later DCs await
  the first's success).
- `paper1.scheduler.blackout` — kiosk/public-facing business-hours
  windows (public-facing honors a KEV emergency override), member-server
  CAB-day blackout, restricted-zone maintenance-only windows, and the
  strict-monthly first-Saturday window. Times are UTC; a configured
  `local` zone is treated as UTC (documented approximation).
- `paper1.scheduler.approver` — human-approval **Policy A** (individual
  reviewer) and **Policy B** (CAB cadence with business-day delays),
  both deterministic per `(seed, pair_id)`.
- `paper1.scheduler.risk_acceptance` — the POA&M pathway: accept residual
  risk with compensating controls, an expiration date, and a review
  trigger; reawaken on expiry or trigger. **This records the pathway; it
  does not assert compliance.**
- Every scheduling decision (`schedule` / `defer` / `accept_risk`) is
  written as a hash-chained `AuditDecisionRecord` via the Phase 1
  `AuditLogger`, and the chain is verifiable.
- **No remediation is performed.** The scheduler only schedules and
  records decisions; deployment of patches happens outside this system,
  gated on the recorded human approval.

```bash
make scheduler-smoke
```

**Phase 7 (previous commit): LightGBM reference comparator.**

- `paper1.model.gbt_comparator` — `load_gbt_config` (validates
  `configs/gbt.yaml`), `fit_gbt`, `predict_gbt`, `rank_pairs_gbt`, and
  `GBTResult` artifact save/load.
- The comparator uses the **same seven features** (E, K, S, C, X, U, R)
  and the **same temporal no-leakage discipline** as the linear
  calibrator: training touches only the `train` split and non-censored
  labels; a chronological last-20% validation block drives early
  stopping. Determinism is enforced (`deterministic=True`,
  `force_row_wise=True`, single-threaded, seeded).
- **Reference only — not the deployed model.** A gradient-boosted-tree
  model does not emit the decomposable per-feature contributions that
  the linear scorer produces for NIST 800-53 AU-3 / CJIS audit records,
  so it is excluded from deployment recommendations. SHAP-based
  explanation is out of scope. The comparator exists to quantify the
  cost of the auditable linear design.
- The `gbt_comparator` strategy slot in `rank_pairs` now accepts a
  fitted `gbt_model`; calling it without a model raises `ValueError`.

```bash
make gbt-smoke
```

**Phase 6 (previous commit): linear weight calibration.**

- `paper1.model.linear_model.fit_weights_logit` /
  `fit_weights_linear` — calibrate the seven scoring weights via
  L2-regularized logistic regression and L2 ridge regression. The
  regularization strength is chosen by temporal cross-validation
  (average precision) inside the **train** split only; gap and test
  rows and censored (`pd.NA`) labels are never seen during fitting.
- `paper1.model.calibration` — `prepare_training_frame` (split- and
  censoring-aware), `make_time_block_folds` (no shuffling; validation
  block is chronologically later), `class_weight_from_labels`,
  `coefficients_to_weights`, and `bootstrap_weight_ci`.
- **Negative-coefficient handling (Phase 6 design choice):** model
  coefficients that come out negative are clipped to zero and the
  remaining weights renormalized. Because the label is "exploited within
  the horizon", the remediation-complexity feature `R` typically draws a
  non-positive coefficient and is therefore clipped — its operational
  cost penalty is a policy choice, not a learned quantity. If every
  coefficient clips to zero the weights fall back to `w_hand` with a
  warning.
- Calibrated weights are saved as JSON artifacts under `data/artifacts/`
  and registered under `w_logit_calibrated` / `w_lin_calibrated`. The
  uncalibrated `w_logit_placeholder` / `w_lin_placeholder` vectors are
  **not** overwritten and remain available until calibration artifacts
  are produced for a real run.

```bash
make calibrate-smoke
```

**Phase 5 (previous commit): features, weights, linear scoring, strategies.**

- `paper1.model.features.build_feature_frame` — assembles the seven
  features per pair: `E` (EPSS), `K` (KEV status), `S` (CVSS base / 10),
  `C` (asset criticality), `X` (local exposure), `U` (remediation
  urgency from KEV due date, else `0.25·K + 0.75·E`), `R` (remediation
  complexity). Features are observation-only at `t0` (KEV-future and
  disclosure-future inputs raise). Missing continuous features are
  imputed (median / mean / zero); a missing KEV status defaults to 0
  with a recorded warning. Audit fields `feature_imputed`,
  `imputed_features`, `feature_warnings` accompany every row.
- `paper1.model.weights` — registry with `w_uniform`, `w_hand`, and the
  `w_logit_placeholder` / `w_lin_placeholder` vectors. **The
  placeholders mirror `w_hand` and are NOT calibrated; Phase 6 replaces
  them with regression-fit weights.** `get_weights` returns a normalized
  copy; `ablate_weight` zeroes one feature and renormalizes.
- `paper1.model.scoring` — linear score
  `w_E·E + w_K·K + w_S·S + w_C·C + w_X·X + w_U·U − w_R·R` with
  per-feature contributions that sum back to the score (R stored
  negative). Deterministic sort: score desc, `pair_id` asc.
- `paper1.model.strategies.rank_pairs` — 13 strategies (random,
  cvss_only, epss_only, kev_first, cvss_x_epss, cvss_plus_epss_plus_kev,
  cve_max/mean/sum, proposed_full, proposed_no_criticality,
  proposed_no_exposure, oracle). `oracle` is **evaluation-only** (reads
  the future label) and must never be deployed. `gbt_comparator` raises
  `NotImplementedError` until the GBT phase.
- `scripts/score_pairs_smoke.py` — builds features and runs a subset of
  strategies on a 100-host synthetic fleet. No scheduler, no metrics.

```bash
make score-smoke
```

**Phase 4 (previous commit): pairs, labels, temporal splits, frames.**

- `paper1.model.pairs` — builds `VulnerabilityHostPair` objects by
  matching vulnerability CPEs to host software. Concrete-version CPE
  matches are `cpe_exact` (confidence 1.0), wildcard matches are
  `cpe_fuzzy` (0.7), and explicit overrides are `manual` (0.6).
  Future-disclosed CVEs and explicitly remediated CVEs are excluded.
- `paper1.model.labels` — Label A (KEV addition OR public PoC within
  the window) and Label B (PoC only). The window is half-open
  `(t0, t0 + H_days]`: an event on exactly `t0` does NOT count; an event
  on exactly `t0 + H_days` DOES. When `t0 + H_days > data_window_end`
  the labels are censored to `pd.NA`. Malformed event dates raise.
- `paper1.model.splits` — train / gap / test partition with an
  `H`-day leakage gap between train and test, computed with
  `pandas.DateOffset(months=...)` to avoid month-length bugs.
- `paper1.model.frames` — conversion of pairs, vulnerabilities, and
  hosts to DataFrames, plus `attach_labels` / `attach_split` and
  `validate_pair_frame` (required-column and pair_id-uniqueness checks).
- `data/fixtures/` — tiny synthetic toy CVEs, KEV catalog, and PoC CSV
  exercising every timing edge case.
- `scripts/build_pairs_smoke.py` — composes a synthetic fleet with the
  toy vulnerabilities and prints pair / label counts. No live feeds.

### Label and leakage philosophy

Features are observation-only at `t0`; labels look strictly into the
future window `(t0, t0 + H_days]`. The temporal split's `H`-day gap
prevents any test-window decision time from sharing a label horizon with
the training window. `ensure_no_label_future_leakage` is a guard that
trips if data intended as a feature postdates `t0`.

To smoke pair construction:

```bash
make pairs-smoke
# or
python scripts/build_pairs_smoke.py --size 100 --seed 1 --t0 2025-06-01 --h-days 30
```

**Phase 3 (previous commit): synthetic fleet generator.**

- `paper1.synthetic.fleet_generator.FleetGenerator` — deterministic
  synthetic endpoints from `(fleet_size, seed, t0)`. Output hosts are
  sorted by `host_id`, and two runs with the same seed produce
  byte-identical Pydantic serializations.
- `paper1.synthetic.software_inventory` — per-host inventory sampled
  from `data/catalog/products.yaml` with role-aware install priors and
  patch-lag-aware version selection.
- `paper1.synthetic.patch_state` — lognormal patch lag capped at
  365 days; scan times always `<= t0`.
- `paper1.synthetic.criticality` — IPES (Identity Privilege Exposure
  Score) generalizes the identity sub-score across Microsoft AD/Entra
  and federated configurations; the default aggregate weights
  renormalize when CMDB is missing.
- `paper1.synthetic.exposure` — per-pair local exposure with
  configurable precondition completeness; unknown preconditions default
  to 0.5 and are recorded.
- `paper1.synthetic.remediation_complexity` — per-pair complexity with
  documented host modifiers (kiosk, DC, public server, mobile).
- `paper1.synthetic.telemetry` — per-source last-seen sampling with
  staleness flags.
- `data/catalog/*.yaml` — public/common product, OS, mitigation, and
  service catalogs used as fixture inputs. No employer-specific data.
- `scripts/generate_synthetic_fleet.py` — CLI smoke driver.

To smoke the generator:

```bash
make synthetic-smoke
# or
python scripts/generate_synthetic_fleet.py --size 100 --seed 1 --out results/synthetic
```

The catalogs are fixture inputs that the paper publishes as the
test-bed configuration. Sensitivity sweeps over the catalog parameters
are part of the experimental plan but do not affect Phase 3.

**Phase 2 (previous commit): feed clients, snapshot cache, provenance.**

- `paper1.feeds.base.BaseFeedClient` — abstract base with snapshot
  read/write, manifest registration, and no-future-leakage verification.
- `paper1.feeds.nvd_client.NVDClient` — NVD JSON 2.0 normalization;
  CVSS v4 preferred, v3.1 fallback; CPE extraction with warnings.
- `paper1.feeds.cve_client` — CPE 2.3 parsing and version-range helpers.
- `paper1.feeds.epss_client.EPSSClient` — FIRST EPSS historical client
  with date-parameterized snapshots; rejects dates before 2021-04-14.
- `paper1.feeds.kev_client.KEVClient` — CISA KEV catalog client with
  reconstructed point-in-time queries.
- `paper1.feeds.poc_client.POCClient` — ExploitDB / PoC client with
  license gate (`PAPER1_ENABLE_POC_FETCH=true` required for live fetch).
- `paper1.feeds.snapshots` and `paper1.feeds.provenance` — single-file
  JSON snapshots with SHA-256 manifest provenance.
- Live-fetch scripts under `scripts/` (`fetch_nvd.py`, `fetch_epss.py`,
  `fetch_kev.py`, `fetch_poc.py`, `validate_snapshots.py`).

Unit tests do not perform live network calls. Every feed test uses
in-memory fixtures or monkeypatched substitutes.

**Phase 1 (previous): foundation.**

Repository scaffold, build, environment, Dockerfile, YAML
configurations, Pydantic v2 schemas, deterministic seeds, UTC time and
simulation-clock utilities, atomic IO and checksums, JSON-structured
logging, YAML config loading and shape validation, append-only
hash-chained audit logger.

Subsequent phases will add: synthetic fleet generation, label
construction with leakage prevention, scoring strategies (linear and
LightGBM reference comparator), the capacity-constrained scheduler,
evaluation metrics including expected exploited-host-days avoided,
statistical analysis, and experiment drivers.

## Live fetching feeds

Unit tests never call the network. To populate real snapshots, use the
scripts in `scripts/`:

```bash
# NVD (CVE 2.0 API; optionally export NVD_API_KEY beforehand)
python scripts/fetch_nvd.py --start 2024-06-01 --end 2024-06-30 --out data/snapshots

# EPSS (daily snapshots; resumable)
python scripts/fetch_epss.py --start 2024-06-01 --end 2024-06-30 --out data/snapshots

# KEV (reconstructed as-of from current catalog)
python scripts/fetch_kev.py --as-of 2024-06-30 --out data/snapshots

# ExploitDB / PoC — license-gated
export PAPER1_ENABLE_POC_FETCH=true   # only after confirming ExploitDB license
python scripts/fetch_poc.py --as-of 2024-06-30 --out data/snapshots

# Verify the snapshot manifest
python scripts/validate_snapshots.py --manifest data/snapshots/MANIFEST.json
```

## Data licensing warnings

- **FIRST EPSS** — license terms are [VERIFY]; the artifact ships
  retrieval scripts and will bundle cached snapshots only after license
  text is recorded in `LICENSE_DATA.md`.
- **ExploitDB** — redistribution terms are unresolved. Live fetch is
  refused unless `PAPER1_ENABLE_POC_FETCH=true`. Cached PoC snapshots
  are not bundled with the artifact pending license review.

## Snapshot manifest philosophy

Every snapshot file written by the framework is registered in
`data/snapshots/MANIFEST.json` with its SHA-256 hash, record count,
license note, and source/date identifier. `verify_manifest()`
re-confirms every file's checksum and reports any mismatch. Every
audit record produced by the framework carries the manifest hashes of
the snapshots it consulted, so historical decisions remain
reproducible after a fresh checkout.

## Layout

See `docs/REPRODUCIBILITY.md` for the full layout description.
