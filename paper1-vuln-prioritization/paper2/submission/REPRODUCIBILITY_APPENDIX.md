# Paper 2 — Reproducibility Appendix (Step 11)

This appendix maps every major numeric claim in the Paper 2 manuscript to its
source file and field. Every row is verified against artifacts produced by the
pre-registered Step 7 (pilot), Step 8 (primary), and Step 9 (aggregation +
inference + post-run stop rules) runs. No claim in the manuscript exceeds what
these artifacts support.

Paths are relative to the repository root
`/Users/sowmyasreeogiboyina/Research Papers/paper1-vuln-prioritization/`.

## Major numeric claims

| # | Claim | Value | Source file | Source field / table column | Notes |
|---|---|---|---|---|---|
| 1 | Unique positive distinct CVEs across all 18 t0 windows | 7 | `paper2/feasibility/probe_v2_multit0/summary.json` | `aggregate.unique_positive_cves` | Gating quantity for K1 (calibration infeasibility). Manuscript phrasing: "7 unique positive CVEs". |
| 2 | Catalog-matched CVEs (intersection of synthetic 31-product catalog with normalized NVD universe) | 2,688 | `paper2/feasibility/probe_v2_multit0/summary.json` | `aggregate.catalog_matched_cves` | Also equals `aggregate.union_distinct_cves_in_pairs`. |
| 3 | Number of t0 windows | 18 | `paper2/feasibility/probe_v2_multit0/summary.json` | `aggregate.n_windows` | Multi-t0 design; `h_days = 30`. |
| 4 | Pilot batches completed | 4 | `paper2/audit/pilot_gate_decision.json` | `pilot_batches_completed` | Matches `pilot_batches_total`. |
| 5 | Pilot seed-runs completed | 288 | `paper2/audit/pilot_gate_decision.json` | `pilot_seed_runs_completed` | Matches `pilot_seed_runs_planned`. |
| 6 | Primary batches completed | 4 | `paper2/audit/primary_complete.json` | `primary_batches_completed` | Matches `expected_batches`. |
| 7 | Primary seed-runs completed | 1,440 | `paper2/audit/primary_complete.json` | `total_seed_runs_completed` | Matches `expected_seed_runs`. |
| 8 | Primary cells completed | 48 | `paper2/audit/primary_complete.json` | `total_cells_completed` | F6 cell enumeration locked. |
| 9 | Primary metric rows | 8,640 | sum of `per_batch[*].per_row_total` in `paper2/audit/primary_complete.json` | computed: 2,160 + 2,700 + 1,620 + 2,160 = 8,640 | Each row carries a freeze-witness ID (`all_rows_have_freeze_witness_id = true`). |
| 10 | Primary wallclock seconds (total) | 2,143.21 | `paper2/audit/primary_complete.json` | `total_wallclock_seconds` | Measured. |
| 11 | Measured per-seed-run seconds (primary) | 1.488 | `paper2/audit/primary_complete.json` | `measured_per_seed_run_seconds` | Used by F8 compute plan; under 18 h budget. |
| 12 | Stop rules triggered during primary execution | K1, K3, S-A | `paper2/audit/primary_complete.json` | `stop_rules_triggered` | Identical set fires in every per-batch entry. |
| 13 | Hard-halt rules triggered | none | `paper2/audit/primary_complete.json` | `hard_halt_triggered` | Empty list. |
| 14 | Primary completion status | PRIMARY_COMPLETE_VALID | `paper2/audit/primary_complete.json` | `status` | Reason field documents validity criteria. |
| 15 | Freeze status on every primary batch | OK | `paper2/audit/primary_complete.json` | `freeze_status_all_batches` and `per_batch[*].freeze_status` | All four batches OK. |
| 16 | Paper 1 freeze manifest SHA-256 | `750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833` | `paper/report/report_manifest.json` | `freeze_manifest_sha` | Carried as `freeze_witness_id` on every per-batch entry in `paper2/audit/primary_complete.json` and on every metric row. |
| 17 | Step-9 tables generated | 19 (10 CSV/MD pairs + `primary_per_seed_wide.csv`) | `paper2/audit/step9_aggregation_complete.json` | `tables_generated` (array of 19 paths) | All copied into `paper2/submission/cset/tables/`. |
| 18 | Step-9 inference files generated | 12 | `paper2/audit/step9_aggregation_complete.json` | `inference_files_generated` | 5 family pairs (B1, C1, C2, C3, C4) + 1 policy-drops pair = 12 files. |
| 19 | Step-9 figures generated | 14 (7 PNG + 7 PDF) | `paper2/audit/step9_aggregation_complete.json` | `figures_generated` | All 14 copied into `paper2/submission/cset/figures/`. |
| 20 | Post-run stop rule K2 fires on any primary axis | false | `paper2/audit/post_run_stop_rule_evaluation.json` | `K2.fires_on_every_primary_axis = false`; per-axis `fires_K2 = false` for A1, A3, A5, A6 | K2 does NOT fire on any axis at the cell-mean test. |
| 21 | Post-run stop rule K7 evaluation | SKIPPED (no perturbation data) | `paper2/audit/post_run_stop_rule_evaluation.json` | `K7.evaluated = false`, `K7.status = "SKIPPED"` | Catalog stability not measured at scale; recorded as limitation. |
| 22 | Post-run stop rule K8 fires on every measured axis | true | `paper2/audit/post_run_stop_rule_evaluation.json` | `K8.any_axis_fires_K8 = true`; per-axis `fires_K8 = true` for A1, A3, A5, A6 | All four axes demoted to descriptive-only per pre-registered action. |
| 23 | Pilot stop rules triggered | K1, K3, S-A | `paper2/audit/pilot_gate_decision.json` | `stop_rules_triggered` | Same as primary; pilot decision = `PROCEED_TO_PRIMARY_NO_FALLBACK`. |
| 24 | Projected primary runtime with safety factor | 0.83 h | `paper2/audit/pilot_gate_decision.json` | `projected_primary_runtime_with_safety_factor` | Under F8 18.0 h budget; safety factor 1.3. |
| 25 | No primary forbidden operations | true | `paper2/audit/primary_complete.json` | `no_primary_forbidden_operations` | No re-fit / no re-tune / no re-weight during primary. |
| 26 | No learned or calibrated cells | n/a (none exist) | `paper2/audit/primary_complete.json` (`status = PRIMARY_COMPLETE_VALID` with K1 / K3 / S-A triggered); `paper2/feasibility/probe_v2_multit0/summary.json` (`calibration.attempted = false`, `calibration.reason = "unique positive distinct CVEs 7 < min 50"`) | n/a | The pre-registered design defines no learned/calibrated cell; the calibration stage was infeasible and was not attempted. All 48 cells are fixed-prior. |

## Cross-cuts

- **Stop-rule registry**: 28 rules total (K1–K8 plus S-A..S-G1 plus SM-1..SM-6), source-of-truth at `paper2_runtime/stop_rules.py`. Triggers recorded in `paper2/tables/post_run_stop_rules.csv` and `paper2/audit/post_run_stop_rule_evaluation.json`.
- **F2 design-prior weight vectors**: six vectors (`w_uniform`, `w_paper1_placeholder`, `w_epss_dominant`, `w_cvss_dominant`, `w_kev_dominant`, `w_context_dominant`), source-of-truth at `paper2_runtime/weights.py`. No weight was re-fit during the primary run.
- **F4 inference policy**: meaningful-effect threshold = 5,000 host-days; MDE-d = 0.5292 at n = 30 per cell. Drops recorded in `paper2/tables/inference/inference_policy_drops.csv`.
- **F7 freeze invariant**: every per-batch summary records the witness ID equal to the SHA-256 above; metric rows carry the same ID.

## Files copied into the submission tree

- 14 figures (PNG + PDF for 7 figures) copied to `paper2/submission/cset/figures/`.
- 33 tables (CSV + MD for 16 tables, plus `primary_per_seed_wide.csv`, plus 12 inference files under `tables/inference/`) copied to `paper2/submission/cset/tables/`.
- LaTeX scaffold: `paper2/submission/cset/main.tex` + 16 section files under `paper2/submission/cset/sections/`.
- Verified-only BibTeX file: `paper2/submission/cset/references.bib` (15 entries).

## Verification commands

The values in this appendix can be regenerated from raw artifacts by running:

```
python -c "import json,pathlib; \
  d=json.load(open('paper2/audit/primary_complete.json')); \
  print('seed_runs', d['total_seed_runs_completed']); \
  print('cells', d['total_cells_completed']); \
  print('status', d['status']); \
  print('stop_rules', d['stop_rules_triggered'])"

python -c "import json; \
  d=json.load(open('paper2/feasibility/probe_v2_multit0/summary.json')); \
  print('unique_pos', d['aggregate']['unique_positive_cves']); \
  print('catalog', d['aggregate']['catalog_matched_cves']); \
  print('windows', d['aggregate']['n_windows'])"
```

Both invocations reproduce the figures listed above. Any drift between the
manuscript and these artifacts is a packaging bug and must be fixed in the
manuscript, never by re-running the pre-registered pipeline.
