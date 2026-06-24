# Graph Report - research-papers  (2026-06-23)

## Corpus Check
- 354 files · ~694,478 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3045 nodes · 8324 edges · 46 communities detected
- Extraction: 55% EXTRACTED · 45% INFERRED · 0% AMBIGUOUS · INFERRED: 3754 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]

## God Nodes (most connected - your core abstractions)
1. `GET()` - 139 edges
2. `path()` - 105 edges
3. `Evaluation metrics + statistical analysis layer (Phases 9-10).  Ranking-quality` - 97 edges
4. `HygienePrioScorer` - 92 edges
5. `copy()` - 86 edges
6. `EEHDAFleetGenerator` - 85 edges
7. `make_rng()` - 74 edges
8. `Vulnerability` - 71 edges
9. `HygieneRiskScore` - 70 edges
10. `FleetGenerator` - 67 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `copy()`  [INFERRED]
  paper19/src/make_figures.py → viewer/components/CitePanel.tsx
- `main()` --calls--> `path()`  [INFERRED]
  archived/HygieneContinuation_Paper7_OnlineRecalibration/src/run_online_calib.py → paper1-vuln-prioritization/src/paper1/audit/hash_chain.py
- `main()` --calls--> `copy()`  [INFERRED]
  paper19/src/analyze.py → viewer/components/CitePanel.tsx
- `main()` --calls--> `GET()`  [INFERRED]
  paper19/src/analyze.py → viewer/app/api/tracking/route.ts
- `_score_p50()` --calls--> `copy()`  [INFERRED]
  archived/HygieneContinuation_Paper7_OnlineRecalibration/src/paper7/online_calib.py → viewer/components/CitePanel.tsx

## Communities

### Community 0 - "Community 0"
Cohesion: 0.02
Nodes (248): ActionOutcome, Stage 5: Actuator — simulate patch application with realistic failure modes.  Th, Simulate one patch action.      The distribution is pre-registered; in_kev is lo, simulate_action(), _advance(), _cache_states(), _compute_hrs(), _grid_search() (+240 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (218): main_validate(), collect_artifact_versions(), dataframe_to_parquet_or_csv(), ensure_result_dirs(), ExperimentManifest, load_manifest(), Shared experiment-runner helpers (Phase 11).  Result-directory layout, a provena, SHA-256 of the on-disk config bytes (stable across runs). (+210 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (231): load_service_catalog(), CPEParseError, Raised when a string cannot be parsed as a CPE 2.3 URI., auth_precondition_factor(), compute_exposure(), _extract_av(), _extract_pr(), installed_vuln_factor() (+223 more)

### Community 3 - "Community 3"
Cohesion: 0.02
Nodes (143): bootstrap_ci(), main(), per_seed_slopes(), Analyse Paper 6 sweep_results.csv: per-cell means, decay slopes, Spearman correl, Return cell_K, cell_lambda, method, seed, slope for P@50 over windows 1..6., BaseModel, make_dataset_card(), make_run_manifest() (+135 more)

### Community 4 - "Community 4"
Cohesion: 0.02
Nodes (159): ABC, BaseFeedClient, FutureDataError, BaseFeedClient — common interface for NVD / EPSS / KEV / PoC clients., Default: load the snapshot for `as_of_date`.          Subclasses may override to, Raised when a record's published/added date exceeds the as-of cutoff., Common surface area for all feed clients.      Subclasses must set ``source_name, verify_no_future() (+151 more)

### Community 5 - "Community 5"
Cohesion: 0.03
Nodes (139): _check_priors(), load_host_type_defaults(), load_mitigation_catalog(), load_os_catalog(), load_product_catalog(), load_yaml_catalog(), Catalog loaders and shape validators for the synthetic generator., _repo_root() (+131 more)

### Community 6 - "Community 6"
Cohesion: 0.03
Nodes (61): _comp_split(), _crit_ord(), _freshness_score(), Deterministic 60/20/20 split for computers (no split column in computers table)., Extracts per-task features and labels from a loaded dataset directory., TaskFeatureExtractor, BaseMethod, get_method() (+53 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (100): ApprovalDecision, ApproverPolicyA, ApproverPolicyB, BaseApproverPolicy, _complexity(), _kev_override(), load_approver_policy(), make_approver() (+92 more)

### Community 8 - "Community 8"
Cohesion: 0.03
Nodes (104): compute_feature_contributions(), Linear scoring with decomposable per-feature contributions.      score = w_E*E +, Raise if required feature columns are absent or contain NaN., Per-feature contribution; R enters negative., Score every pair; return contributions and the priority score.      The input fr, Deterministic sort: priority_score (desc) then pair_id (asc)., score_pairs_linear(), sort_ranking() (+96 more)

### Community 9 - "Community 9"
Cohesion: 0.04
Nodes (94): all_constraints_satisfied(), check_dependency(), check_domain_controller_staging(), check_group_cap(), ConstraintResult, dc_first_succeeded(), dependency_satisfied(), group_cap_violated() (+86 more)

### Community 10 - "Community 10"
Cohesion: 0.03
Nodes (77): main(), _ehd_rows(), fig_ehd_by_strategy(), fig_ehd_distribution_selected(), fig_fraction_of_oracle(), fig_proposed_vs_epss_by_seed(), fig_relative_to_epss(), generate_all_figures() (+69 more)

### Community 11 - "Community 11"
Cohesion: 0.04
Nodes (86): capacity_efficiency(), kev_deadline_breach_rate(), kev_remediation_latency(), Compliance / operational-efficacy metrics: KEV deadlines, capacity efficiency., Fraction of scheduled (non-censored) pairs that are positives., Fraction of KEV pairs (with a due date) not remediated by the deadline., Median / p95 / count of days from KEV addition to remediation.      When ``criti, _remediated_map() (+78 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (71): anonymize_tex(), find_brace(), main(), parse_papers(), Given index of '{', return index of the matching '}'., Replace every \\cmd[..]{..} (balanced) with `replacement` (or remove). Skips % c, Blanket author-identifier redaction — applied to EVERY .tex/.bib source file., redact_text() (+63 more)

### Community 13 - "Community 13"
Cohesion: 0.05
Nodes (74): main(), _make_data(), _sigmoid(), bootstrap_weight_ci(), class_weight_from_labels(), coefficients_to_weights(), _is_na(), make_time_block_folds() (+66 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (55): audit_file(), find_violations(), _has_negation_before(), _line_for_offset(), main(), Return a list of {line, type, phrase, snippet} violations., _has(), Tests for scripts/paper2_claim_audit.py. (+47 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (61): bootstrap_ci(), bootstrap_ci_bca(), clean_numeric_array(), compare_many_to_baseline(), compare_to_baseline(), holm_bonferroni(), minimum_detectable_effect(), paired_arrays() (+53 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (52): accept_risk(), Risk-acceptance / POA&M pathway.  Records the operational practice of consciousl, Raise ValueError if any required risk-acceptance field is missing/empty., Build an accepted-risk record from an ApprovalDecision., Return records whose acceptance expired on or before `now`., Whether a record's review trigger has fired (excluding expiration)., reawaken_expired_acceptances(), review_trigger_fired() (+44 more)

### Community 17 - "Community 17"
Cohesion: 0.1
Nodes (33): _bca_ci(), _ci(), feats(), fig1_ceiling(), fig1_confidence(), fig1_config(), fig1_crossover(), fig1_methods() (+25 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (43): add_observations(), _channel_cov(), _class_probs(), convergence_cost(), _drift_times(), evaluate_cell(), evaluate_seed(), evaluate_seed_overlap() (+35 more)

### Community 19 - "Community 19"
Cohesion: 0.1
Nodes (48): _load_vulns(), main(), _parse_args(), censor_mask(), _coerce_date(), _earliest_events_in_window(), ensure_no_label_future_leakage(), label_a() (+40 more)

### Community 20 - "Community 20"
Cohesion: 0.1
Nodes (42): _filtered_times(), fit_gbt(), GBTResult, load_gbt_config(), load_gbt_result(), _model_params(), predict_gbt(), rank_pairs_gbt() (+34 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (34): average_precision(), _bca_ci(), bca_ci_mean(), blind_labels(), compute_metrics(), cwer_at_k(), failure_flag(), false_positive_burden() (+26 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (33): AnomalyConfig, c_base(), config_sha256(), large(), load_config(), load_yaml(), medium(), _normalized_config_sha256() (+25 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (37): _compare_versions(), cpe_to_product_key(), extract_affected_ranges(), normalize_cpe(), parse_cpe23(), ParsedCPE, CPE 2.3 parsing and version-range helpers.  Conservative implementation: this mo, Parse and re-emit a CPE in canonical form. Raises on malformed input. (+29 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (13): _best(), _ci(), main(), _mean(), _mean_ci(), _paired(), _paired_delta_ci(), Analyse Paper 10 AutoHeal results: H1-H4 outcomes + LaTeX tables. (+5 more)

### Community 25 - "Community 25"
Cohesion: 0.26
Nodes (32): build_feature_frame(), _by_pair(), _clip01(), _compute_u(), _criticality_lookup(), _impute_fill(), _signal_lookups(), _to_date() (+24 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (30): blackout_active(), BlackoutDecision, _in_hours(), is_business_hours(), is_cab_blackout(), is_first_saturday_maintenance(), is_in_maintenance_window(), _kev_override_active() (+22 more)

### Community 27 - "Community 27"
Cohesion: 0.14
Nodes (25): assign_split(), filter_pairs_by_split(), make_temporal_split(), Temporal train / gap / test split with an H-day leakage gap.  Windows (all bound, Raise if the gap is shorter than H_days., Return rows of `pair_frame` whose 'split' column equals split_name., Compute split window boundaries; optionally tally decision_times.      Uses ``pa, Assign a decision time to one of train / gap / test / censored. (+17 more)

### Community 28 - "Community 28"
Cohesion: 0.07
Nodes (10): fake_full_universe(), fake_shared(), isolated_dirs(), Tests for paper2_runtime.batch_runner (Step 6).  Heavy components (cached-data l, Stub the heavy `_load_full_universe` + `_catalog_match_full` paths., A tiny deterministic shared context that side-steps the cached-data load., Redirect RESULT_DIR and AUDIT_DIR to tmp so tests never write under repo., Skip the real `make verify-primary-freeze` subprocess in unit tests. (+2 more)

### Community 29 - "Community 29"
Cohesion: 0.18
Nodes (19): audit_explanation_completeness(), audit_record_count_by_type(), _has_all_features(), imputation_rate_per_feature(), _normalize_records(), Audit-trail metrics: explanation completeness, imputation rate, integrity., Fraction of score records with complete features/contributions/provenance., Per-feature fraction of score records where that feature was imputed. (+11 more)

### Community 30 - "Community 30"
Cohesion: 0.14
Nodes (1): Tests for paper2_runtime.inference_policy — F4 SM-1/3/5 shim.

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (5): Tests for paper2_runtime.freeze_invariant (F7).  These tests do NOT shell out to, The freeze_invariant module must never `make freeze-primary`., Simulate K6 by tampering with the before-witness mid-batch., test_context_manager_marks_failed_batch_invalid(), test_does_not_invoke_freeze_primary()

### Community 32 - "Community 32"
Cohesion: 0.47
Nodes (9): Tests for paper2_runtime.pilot_gate (Step 7)., _redirect_dirs(), test_fallback_when_projection_too_long(), test_proceed_decision_when_projection_fits(), test_stop_on_freeze_failure(), test_stop_on_K5_K6_hard_halt(), test_stop_on_missing_batch_summary(), test_write_pilot_gate_decision_creates_both_files() (+1 more)

### Community 33 - "Community 33"
Cohesion: 0.2
Nodes (1): Tests for paper2_runtime.stop_rules — F5 registry loader + static evaluator.

### Community 34 - "Community 34"
Cohesion: 0.25
Nodes (1): Tests for paper2_runtime.run_planner — F6 + F8 read-only summariser.

### Community 35 - "Community 35"
Cohesion: 0.29
Nodes (1): Tests for paper2_runtime.cell_loader — F6 cell enumeration.

### Community 36 - "Community 36"
Cohesion: 0.67
Nodes (5): anonymizeAux(), anonymizeMainTex(), redactText(), replaceCommand(), stripAcks()

### Community 37 - "Community 37"
Cohesion: 0.5
Nodes (2): bibtex(), citeKey()

### Community 38 - "Community 38"
Cohesion: 0.4
Nodes (2): useTheme(), ThemeToggle()

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (2): pdfViewUrl(), serveUrl()

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): PatchPosture(h) = unpatched CVEs on h / total applicable CVEs on h.          Hig

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): ADExposure(h) — three-component composite for the host's primary user:

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): TelemetryFreshness(h) = min(days_since_last_checkin, 30) / 30.         0 = fully

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Fetch raw upstream data for the as-of date.          Implementations may return

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Convert raw upstream data into the canonical per-feed DataFrame.

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Raise FutureDataError if any row's `date_column` exceeds `as_of_date`.

## Knowledge Gaps
- **357 isolated node(s):** `CLI entry point for the Paper 7 online-calibration evaluation.  Usage (from pape`, `Bias-corrected percentile bootstrap CI (good-enough proxy for full BCa).      Fo`, `Per-seed std-dev of P@50 across windows, by method.`, `CLI entry point: run the Paper 5 multi-window evaluation and freeze results.  Us`, `Multi-window fleet-state evolution for Paper 5.  The simulator takes a Window-1` (+352 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 30`** (14 nodes): `test_paper2_inference_policy.py`, `Tests for paper2_runtime.inference_policy — F4 SM-1/3/5 shim.`, `test_diagnostic_metric_blocks_wilcoxon()`, `test_diagnostic_metrics_set_contains_expected()`, `test_kev_breach_rate_diagnostic_only()`, `test_kev_first_pair_dropped_for_inference()`, `test_kev_first_pair_dropped_via_sm1_degeneracy_when_std_zero()`, `test_oracle_inference_disabled_for_CLM_B3()`, `test_oracle_pair_gates_off_wilcoxon()`, `test_precision_recall_ndcg_diagnostic_only()`, `test_sm1_allows_non_degenerate_diffs()`, `test_sm5_accepts_bare_metric_name()`, `test_sm5_accepts_neutral_text()`, `test_sm5_rejects_significance_near_diagnostic_metric()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (10 nodes): `test_paper2_stop_rules.py`, `Tests for paper2_runtime.stop_rules — F5 registry loader + static evaluator.`, `test_K1_triggers_for_step_3_8_measurement()`, `test_K3_per_window_share_branch()`, `test_K5_K5a_trigger_on_leakage_warning()`, `test_K6_triggers_when_freeze_status_false()`, `test_no_unknown_enforcement_or_severity_values()`, `test_registry_loads_and_validates_closed_set()`, `test_write_refuses_paper1_paths()`, `test_write_stop_rule_evaluation_creates_all_artefacts()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (8 nodes): `test_paper2_run_planner.py`, `Tests for paper2_runtime.run_planner — F6 + F8 read-only summariser.`, `test_pilot_plan_has_four_batches()`, `test_primary_allowed_only_on_proceed_decision()`, `test_primary_blocked_without_pilot_pass()`, `test_primary_plan_has_four_batches()`, `test_seed_run_totals_match_F8()`, `test_summary_has_required_keys()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (7 nodes): `test_paper2_cell_loader.py`, `Tests for paper2_runtime.cell_loader — F6 cell enumeration.`, `test_cell_counts_match_F6_locks()`, `test_deferred_cells_excluded_from_planned()`, `test_group_by_table_group_matches_F6_summary()`, `test_loads_and_validates_cells()`, `test_no_duplicate_runnable_cells()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (5 nodes): `bibtex()`, `citeKey()`, `ieeeCitation()`, `isPublished()`, `cite.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (5 nodes): `ThemeProvider()`, `useTheme()`, `ThemeToggle()`, `ThemeProvider.tsx`, `ThemeToggle.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (3 nodes): `pdfViewUrl()`, `serveUrl()`, `FiguresGallery.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `PatchPosture(h) = unpatched CVEs on h / total applicable CVEs on h.          Hig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `ADExposure(h) — three-component composite for the host's primary user:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `TelemetryFreshness(h) = min(days_since_last_checkin, 30) / 30.         0 = fully`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Fetch raw upstream data for the as-of date.          Implementations may return`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Convert raw upstream data into the canonical per-feed DataFrame.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Raise FutureDataError if any row's `date_column` exceeds `as_of_date`.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GET()` connect `Community 9` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 11`, `Community 13`, `Community 16`, `Community 20`, `Community 22`, `Community 23`, `Community 24`, `Community 25`, `Community 26`, `Community 29`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `run_smoke_seed()` connect `Community 1` to `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 7`, `Community 8`, `Community 9`, `Community 11`, `Community 14`, `Community 16`, `Community 19`, `Community 23`, `Community 25`, `Community 27`, `Community 29`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `path()` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 12`, `Community 14`, `Community 20`, `Community 22`, `Community 28`, `Community 31`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 130 inferred relationships involving `GET()` (e.g. with `main()` and `_resolve_dataset_dir()`) actually correct?**
  _`GET()` has 130 INFERRED edges - model-reasoned connections that need verification._
- **Are the 125 inferred relationships involving `ValueError` (e.g. with `_rank_with_method()` and `get_method()`) actually correct?**
  _`ValueError` has 125 INFERRED edges - model-reasoned connections that need verification._
- **Are the 106 inferred relationships involving `str` (e.g. with `main()` and `main()`) actually correct?**
  _`str` has 106 INFERRED edges - model-reasoned connections that need verification._
- **Are the 102 inferred relationships involving `path()` (e.g. with `main()` and `run()`) actually correct?**
  _`path()` has 102 INFERRED edges - model-reasoned connections that need verification._