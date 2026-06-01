<!--
Paper 2 — Step 3: Feasibility Probe build + execution report.
Internal planning document. No fabricated counts. Paper 1 (../paper/,
results/primary_full_v1/) is NOT touched by this work.
-->

# Paper 2 — Step 3: Feasibility Probe Report

**Outcome: CONDITIONAL GO — pending data acquisition.** The probe is built and
test-verified, but the live public-feed fetch was network-blocked here, so the
real positive-CVE counts are unmeasured. No counts were fabricated; no calibration
was run.

## Probe build status
- `scripts/paper2_feasibility_probe.py` — built. Read-only w.r.t. Paper 1; writes
  only under `--out`, `data/snapshots/`, `data/cache/`. Fetches/normalizes
  NVD/EPSS/KEV (PoC OFF by default; `--include-poc` requires
  `PAPER1_ENABLE_POC_FETCH=true`), matches CVEs to the 31-product catalog, builds a
  synthetic fleet + pairs at t0, attaches **real EPSS/KEV as-of-t0**, computes
  **Label A over (t0, t0+H]**, counts distinct/positive CVEs, and attempts minimal
  logistic/ridge calibration only if positives ≥ `--min-positive-cves`.
- `tests/test_paper2_feasibility_probe.py` — 10 tests, network-free (monkeypatched
  feeds + deterministic hosts; calibration path stubbed at `_build_features`).
- `Makefile` target `paper2-feasibility-probe` added.
- Bug fixed during build: `label_a` returns nullable-boolean values
  (`numpy.bool_`); a strict `is True/is False` check dropped all labels in the
  calibration path — fixed with a robust `_label_bool` coercion.
- Cache-isolation fix: tests now redirect `_CACHE_DIR` to a temp dir so they never
  write fake fixtures into the real `data/cache/paper2_probe` (which was purged;
  `data/cache/**` is gitignored).

## Tests passed
- Probe tests: **10 / 10 passed.**
- Full suite: **753 passed.**
- `ruff check src tests scripts`: All checks passed.
- `compileall -q src scripts`: OK.

## Network fetch blocker
`make paper2-feasibility-probe` attempted a live NVD fetch and received
`HTTP Error 404: Not Found` (restricted sandbox network). The probe **did not fake
success**: it wrote `paper2/feasibility/probe_v1/summary.json` with
`{"blocked": true, "decision": "CONDITIONAL_GO_pending_data_acquisition", ...}` and
exited code 3.

## Exact missing counts (unmeasured — fetch blocked)
- total NVD CVEs in window — unmeasured
- catalog-matched CVEs — unmeasured
- distinct CVEs in pairs — unmeasured
- positive distinct CVEs (Label A) — unmeasured
- positive pairs — unmeasured
- EPSS coverage — unmeasured
- KEV future-label count — unmeasured
- calibration attempted — no (data gate not reached); non-degenerate — n/a

## Decision gate (apply after a real/cached probe run)
- **≥ 50 positive distinct CVEs AND non-degenerate calibration → GO** to
  pre-registration (Step 4).
- **20–49 positives → CONDITIONAL GO**: expand the date window and/or the product
  catalog, then re-probe.
- **< 20 positives → PIVOT** away from calibration to a robustness/sensitivity-only
  study (Label A/B, capacity, blackout, imputation sweeps on real-feed features with
  fixed/published weights).

## Paper 1 integrity
**Untouched / freeze verified.** `make verify-primary-freeze` → OK; 0 files modified
under `results/primary_full_v1/` during this work. The probe is read-only w.r.t.
Paper 1.

## Next required action
Run the probe in a network-enabled environment (or with pre-fetched/cached
snapshots) per `STEP3_DATA_ACQUISITION_RUNBOOK.md`, then apply the decision gate
above. Do not proceed to calibration/pre-registration on unproven data.
