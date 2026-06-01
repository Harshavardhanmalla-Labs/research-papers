<!--
Paper 2 — Step 3.5: Public-feed feasibility probe EXECUTION report.
Real public data (NVD/EPSS/KEV) was fetched and the probe was run. No counts are
fabricated. Paper 1 (results/primary_full_v1/) untouched and freeze-verified.
-->

# Paper 2 — Step 3.5: Feasibility Probe Execution Report

**Decision: CONDITIONAL GO** — pipeline validated on real public data, but the
**positive-CVE gate is UNRESOLVED** (not passed and not validly failed). Two
concrete fixes are required before re-measuring: (1) an `NVD_API_KEY` to fetch the
full multi-year disclosure universe, and (2) a probe redesign to aggregate KEV/PoC
positives across many monthly t0 windows instead of a single 30-day horizon.

## Commands run
```
make verify-primary-freeze PYTHON=.venv/bin/python      # OK (before/after)
find data/snapshots / data/cache                        # empty (only .gitkeep)
make fetch-kev  AS_OF=2024-10-01                         # OK: 1,184 KEV records
make fetch-epss START=2024-08-30 END=2024-09-01          # OK: 3 daily snapshots (~258k rows each)
make fetch-nvd  START=2023-06-01 END=2024-09-30          # FAILED: HTTP 404 (range > 120 days)
# bug fix: probe now chunks NVD requests into <=120-day windows
make paper2-feasibility-probe                            # BLOCKED: HTTP 429 (unauthenticated rate limit) mid-fetch
# real partial measurement on a single 120-day window:
scripts/paper2_feasibility_probe.py --start-date 2024-05-04 --end-date 2024-08-31 \
   --t0 2024-09-01 --h-days 30 --fleet-size 500 --seed 20260601 \
   --out paper2/feasibility/probe_v1_partial120 --min-positive-cves 50   # COMPLETED
```

## Fetch status
- **KEV:** OK — 1,184 records as-of 2024-10-01 (CISA, public domain).
- **EPSS:** OK — daily snapshots 2024-08-30/31, 09-01 (~258k rows each; v3 era).
- **NVD (full 487-day window):** FAILED. Two real issues found:
  1. **120-day range cap** — NVD CVE 2.0 API rejects `pubStartDate/pubEndDate`
     ranges > 120 days (HTTP 404). *Fixed:* the probe now chunks into ≤120-day
     windows (`_NVD_MAX_RANGE_DAYS=120`, dedup by CVE id, polite inter-chunk pause).
  2. **Unauthenticated rate limit** — after ~14 rapid paginated requests the full
     487-day fetch hit **HTTP 429 Too Many Requests**. Needs `NVD_API_KEY`.
- **NVD (single 120-day window):** OK — fetched 13,050 records; this enabled a real
  partial measurement.

## Probe status
- Configured full-window run (`probe_v1/`): **BLOCKED (429)** — wrote a `blocked`
  summary, exited 3, **did not fabricate counts**. Preserved at
  `paper2/feasibility/probe_v1/summary.json`.
- Single-120-day real-data run (`probe_v1_partial120/`): **COMPLETED** — full
  outputs written.

## Extracted counts (real, from `probe_v1_partial120`; NVD window 2024-05-04..2024-08-31, t0=2024-09-01, H=30)
| Metric | Value |
| --- | --- |
| total NVD records | 13,050 |
| normalized CVEs | 12,635 |
| CVEs with CVSS | 12,635 (normalize requires CVSS) |
| CVEs with CPE | 10,337 |
| catalog-matched CVEs | **281** |
| hosts generated | 500 |
| vulnerability-host pairs built | 54,717 |
| distinct CVEs in pairs | 281 |
| Label A positive distinct CVEs | **0** |
| Label A negative distinct CVEs | 281 |
| positive pairs | 0 |
| negative pairs | 54,717 |
| EPSS coverage @ t0 | **281 / 281 = 1.00** |
| KEV as-of-t0 count (feature K) | 1,159 |
| KEV future-label count | 0 |
| calibration attempted | no (0 < 50) |
| logistic / ridge status | not attempted |
| non-degenerate weights | n/a |
| warnings/errors | none (leakage-safe; EPSS/KEV as-of-t0 enforced) |

## Decision gate — reasoned application
Literal rule C (positives < 20 → PIVOT) would fire on this single run. **But the 0
is not a valid feasibility measurement**:
- The NVD universe here is only a 120-day disclosure window (forced by the 429 on
  the full window). KEV additions in (2024-09-01, 2024-10-01] are dominated by CVEs
  disclosed *years* earlier, whose disclosure records are excluded from this window
  → they cannot form pairs → cannot be positive. Hence 0 is largely a
  **universe-truncation artifact**.
- A single 30-day KEV horizon is also inherently sparse (KEV adds ~tens/month;
  catalog-matched, recently-disclosed subset ≈ 0).

What IS validly established (real data):
- The end-to-end pipeline works: NVD→normalize→CPE→**catalog match (281)**, real
  **EPSS attach (100% coverage)**, real **KEV as-of-t0 (1,159)**, leakage-safe
  Label A. Catalog match rate ≈ 281/10,337 ≈ 2.7% of CPE'd CVEs.

Therefore the honest decision is **CONDITIONAL GO** (feasible after specific fixes),
**not** a clean PIVOT (the 0 is an artifact) and **not** GO (the positive gate is
unproven). NO-GO is also rejected: feeds ARE acquirable (KEV/EPSS fully; NVD in
≤120-day chunks).

## Required fixes before re-measuring (and the PIVOT fallback)
1. **NVD_API_KEY** → fetch the full multi-year disclosure universe (so older
   KEV-listed CVEs are present), respecting NVD's recommended request pacing.
2. **Probe/measurement redesign** → aggregate KEV(/PoC) positives across **many
   monthly t0 windows** over the EPSS v3 era (2023-03-07 .. 2025-03-16), counting
   **distinct positive CVEs** across windows (effective N ≠ pair count).
3. Re-run and re-apply the gate:
   - ≥50 distinct positive CVEs + non-degenerate calibration → GO (Step 4).
   - 20–49 → CONDITIONAL GO (widen further / expand catalog).
   - <20 even after fixes → **PIVOT** to a robustness/sensitivity-only Paper 2
     (Label A/B, capacity, blackout, imputation sweeps on real-feed features with
     fixed/published weights), or Paper 3 alternative.

## Paper 1 integrity
**Untouched / freeze verified.** `verify-primary-freeze` → OK; 0 files modified
under `results/primary_full_v1/`. Probe is read-only w.r.t. Paper 1.

## Code-change checks (probe chunking fix)
Full suite **753 passed**; `ruff` clean; `compileall` OK; 10/10 probe tests pass.

## Artifacts
- `paper2/feasibility/probe_v1/` — blocked full-window result (preserved).
- `paper2/feasibility/probe_v1_partial120/` — real 120-day measurement
  (summary.json/md, cve_match_counts.csv, label_counts.csv, epss_coverage.csv,
  calibration_status.json).
- Real cached public data under `data/snapshots/{kev,epss}` and
  `data/cache/paper2_probe/` (gitignored) — enables offline `--use-cached-only`.
