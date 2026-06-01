# Reproducibility Appendix

All reported numbers derive from a single frozen artifact; nothing in the
manuscript is hand-entered. Confirm the values below against the released artifact
before camera-ready.

## Frozen artifact

- **Frozen artifact path:** `results/primary_full_v1/`
- **Freeze manifest path:** `results/primary_full_v1/FREEZE_MANIFEST.json`
  (content-addressed, per-file SHA-256; verifies via
  `make verify-primary-freeze`)
- **Report manifest:** `results/primary_full_v1/report/report_manifest.json`
  (records the freeze SHA and the generated table/figure file list)

## Run configuration

- **Seed count:** 30
- **Strategy count:** 13 (random, cvss_only, epss_only, kev_first, cvss_x_epss,
  cvss_plus_epss_plus_kev, cve_max, cve_mean, cve_sum, proposed_full,
  proposed_no_criticality, proposed_no_exposure, oracle)
- **Fleet size:** 10,000 hosts (public-sector-shaped synthetic)
- **Capacity:** 100 pair-actions per window (capacity ratio 0.01)
- **Label:** A; **Approver policy:** A; **Blackout:** primary; **Identity:**
  AD/Entra default
- **Weights:** placeholder (uncalibrated) — disclosed limitation

## Integrity status

- **Metric rows:** 4,290 (30 × 13 × 11)
- **Audit log count:** 390 (30 × 13), **all hash-chain valid**
- **Strict inspection:** passed with **zero issues**
- **NaN values:** 0; **infinite values:** 0
- **Max scheduled count:** 100 (equals capacity); scheduling feasible for all
  strategies and seeds
- **Freeze verification:** OK

## Generated tables and figures

- **Tables:** `paper/tables/*.{csv,md,tex}` and
  `results/primary_full_v1/report/tables/` (7 tables; see `table_figure_index.md`)
- **Figures:** `paper/figures/*.{png,pdf}` and
  `results/primary_full_v1/report/figures/` (5 figures)

## Data provenance and caveats

- **No live feeds:** the reported run calls no live feed clients and fetches no
  external data; it uses bundled toy fixtures plus the deterministic synthetic
  generator.
- **Synthetic / toy-fixture caveat:** the fleet is synthetic and the
  vulnerability/KEV/PoC fixtures are a small bundled toy set; absolute magnitudes
  are properties of these inputs, not field measurements. Results are a benchmark
  validation under synthetic conditions, not real-world validation.
- **Reproduction:** the run is deterministic from a master seed via SHA-256-based
  sub-seed derivation; documented commands regenerate the artifact, and the freeze
  manifest detects any drift.
