# Table and Figure Index

Numbering used throughout `paper_full_draft.md` and `paper_submission_draft.md`.
All sources are generated from the frozen artifact `results/primary_full_v1/`
(freeze verified); see `reproducibility_appendix.md`. Captions are drafts.

## Tables

| No. | Source file (`paper/tables/`) | Caption (draft) | Referenced in | Inserted into final format |
| --- | --- | --- | --- | --- |
| Table 1 | `table_acceptance_checks.{csv,md,tex}` | Acceptance and integrity checks for the frozen 30-seed primary run (seeds, strategies, metric rows, audit-log validity, NaN/infinite counts, max scheduled count vs capacity, freeze verification). | §13.1 | pending |
| Table 2 | `table_ehd_primary.{csv,md,tex}` | Per-strategy simulated expected exploited-host-days (EHD): absolute mean and standard deviation plus EEHDA reporting forms (relative to random, relative to EPSS, fraction of oracle). Lower EHD is better. | §13.2, §13.4 | pending |
| Table 3 | `table_strategy_comparison_vs_epss.{csv,md,tex}` | Each non-oracle strategy versus the `epss_only` baseline on mean EHD: absolute delta, relative delta, and lower-is-better direction. | §13.3 | pending |
| Table 4 | `table_ranking_metrics.{csv,md,tex}` | Ranking-quality metrics by strategy: precision@k, recall@k, nDCG@k (k = 10), mean and standard deviation. | §13.5 | pending |
| Table 5 | `table_operational_metrics.{csv,md,tex}` | Operational metrics by strategy: KEV-deadline breach rate, capacity efficiency, scheduled count, scheduler feasibility, risk-acceptance rate. | §13.6 | pending |
| Table 6 | `table_audit_metrics.{csv,md,tex}` | Audit-trail metrics by strategy: hash-chain validity (all 1.0) and mean audit record count. | §13.6 | pending |
| Supplementary Table A1 | `table_primary_metric_summary.{csv,md,tex}` | Full per-(strategy, metric) mean / std / count summary (superset of Tables 2-6). | §13 intro | pending (supplementary) |

## Figures

| No. | Source file (`paper/figures/`) | Caption (draft) | Referenced in | Inserted into final format |
| --- | --- | --- | --- | --- |
| Figure 1 | `fig_ehd_by_strategy.{png,pdf}` | Mean absolute EHD by strategy with standard-deviation error bars (lower = fewer simulated exploited-host-days). | §13.2 | pending |
| Figure 2 | `fig_fraction_of_oracle.{png,pdf}` | EEHDA fraction-of-oracle by strategy (observed values; some fall outside [0, 1] and are reported as observed). | §13.4 | pending |
| Figure 3 | `fig_relative_to_epss.{png,pdf}` | EEHDA relative-to-`epss_only` by strategy; the zero line marks parity with EPSS. | §13.3 | pending |
| Figure 4 | `fig_ehd_distribution_selected.{png,pdf}` | Distribution of absolute EHD across the 30 seeds for selected strategies (random, epss_only, proposed_full, oracle). | §13.2 | pending |
| Figure 5 | `fig_proposed_vs_epss_by_seed.{png,pdf}` | Per-seed EHD scatter of `proposed_full` versus `epss_only` with a y = x reference line. | §13.3 (provenance) | pending |

## Notes

- The in-text references in `paper_full_draft.md` and `paper_submission_draft.md`
  use the numbers above (e.g., "Table 2", "Figure 1"); source-file provenance lives
  here and in `results/primary_full_v1/report/report_manifest.json`.
- `table_primary_metric_summary` is the full superset and is treated as a
  supplementary table (A1); Tables 2-6 are projections of it for readability.
- "Inserted into final format" stays `pending` until the venue template is applied
  (Phase 22+); this is a tracking column, not a claim of completion.
