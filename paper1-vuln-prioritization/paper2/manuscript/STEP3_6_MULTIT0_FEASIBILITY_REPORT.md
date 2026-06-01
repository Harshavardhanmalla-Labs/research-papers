<!--
Paper 2 — Step 3.6: Full-Window Acquisition Fix and Multi-t0 Feasibility Probe.
Implements the two Step-3.5 fixes (hardened NVD acquisition + multi-t0 aggregation),
validates the mechanics on REAL cached public data, and records the honest blocker
for the full-scale measurement (NVD_API_KEY). No counts are fabricated. Paper 1
(results/primary_full_v1/) untouched and freeze-verified.
-->

# Paper 2 — Step 3.6: Multi-t0 Feasibility & Hardened Acquisition Report

**Decision: CONDITIONAL GO — gate still UNRESOLVED, blocked on a single dependency
(`NVD_API_KEY`).** The two fixes Step 3.5 demanded are now implemented and tested,
and the multi-t0 pipeline is validated end-to-end on real cached public data. The
full-scale feasibility number cannot be measured in this sandbox because the full
multi-year NVD disclosure universe requires an API key (unauthenticated full-window
fetch hits HTTP 429). **No counts are fabricated.**

## What Step 3.5 required vs. what Step 3.6 delivered
| Step 3.5 required fix | Step 3.6 status |
| --- | --- |
| (1) `NVD_API_KEY` to fetch the full multi-year disclosure universe | **Code ready** (key wired through acquisition); **key absent in sandbox** → full run BLOCKED honestly |
| (2) Redesign to aggregate KEV positives across many monthly t0 windows (not a single 30-day horizon) | **Done**: `--multi-t0` mode aggregates UNIQUE distinct positive CVEs across monthly t0s in the EPSS v3 era |

## Code changes (all in `scripts/paper2_feasibility_probe.py`)

### A. Hardened NVD acquisition (`_obtain_nvd`)
- **≤120-day chunking** with **per-chunk cache** `nvd_chunk_{cs}_{ce}.json` (NVD's
  CVE 2.0 API caps `pubStartDate/pubEndDate` ranges at 120 days).
- **`--resume`**: completed per-chunk caches are reused, so an interrupted fetch
  continues without re-fetching prior chunks.
- **`NVD_API_KEY`** support (`--nvd-api-key` or env) forwarded to
  `fetch_nvd_window(api_key=...)`; **`--nvd-sleep-seconds`** (default 6s, NVD's
  recommended unauthenticated pace) between chunks.
- **HTTP 429 / fetch error → no fabrication**: completed chunks are preserved on
  disk, an actionable `nvd_acquisition_status.json` (requested window, completed
  vs. total chunks, **exact resume command**, remediation) is written, and the
  probe raises `ProbeBlocked` (exit 3).
- **CVE-id dedup** across chunks (`_dedup_by_cve`).

### B. Multi-t0 feasibility mode (`run_multi_t0`)
- Flags: `--multi-t0 --t0-start 2023-09-01 --t0-end 2025-02-01 --t0-frequency
  monthly --nvd-lookback-days 730 --aggregate-positive-cves`.
- Fetches **one** NVD universe `[min(t0)-lookback .. max(t0)]` and generates **one**
  synthetic fleet, then loops monthly t0 windows.
- **The gating metric is UNIQUE distinct positive CVEs** across windows — explicitly
  **not** the pair count and **not** the per-window event sum (a CVE that becomes
  KEV-listed inside several overlapping horizons is **one** calibration unit). Both
  `unique_positive_cves` and `event_positive_cves_across_windows` are reported so the
  distinction is auditable.
- EPSS is treated as an **optional per-window feature**: a missing snapshot for a t0
  does not block the label measurement (it is KEV-driven); coverage is recorded as
  `missing`.
- **CVE-level-deduped calibration smoke** (`_attempt_calibration_multi`) runs **only**
  if unique positives ≥ `--min-positive-cves`: builds features per window, dedups to
  one row per CVE, labels by membership in the aggregated positive set, and fits
  logit/ridge. Records **non-degeneracy only — no performance/superiority claims.**

### C. Outputs (written under `--out`)
`summary.json`, `summary.md`, `per_t0_counts.csv`, `aggregate_counts.csv`,
`cve_match_counts.csv`, `label_counts.csv`, `epss_coverage.csv`,
`calibration_status.json`, `nvd_acquisition_status.json`, `decision_gate.json`.

## Tests & checks
- `tests/test_paper2_feasibility_probe.py`: **+9 tests** (now 19/19 pass) covering
  chunk-splitting ≤120 days + CVE dedup; HTTP-429 preserving completed chunks +
  resume command; `--resume` reusing caches without re-fetch; multi-t0 unique-vs-event
  positive counting; aggregation of distinct positives across windows; CVE-level dedup
  preventing N-inflation; insufficient-positives blocking calibration; EPSS-optional;
  Paper 1 freeze untouched.
- Full suite **762 passed**; `ruff check src tests scripts` clean; `compileall` OK;
  `make verify-primary-freeze` OK (before and after).

## Execution

### Real cached multi-t0 demo (mechanics validation, real public data)
`paper2/feasibility/probe_v2_multit0_cacheddemo/` — universe **2024-05-04..2024-08-31**
(the one cached NVD window), 4 monthly t0s, `--use-cached-only`:

| Metric | Value |
| --- | --- |
| n_windows | 4 |
| total NVD records | 13,050 |
| catalog-matched CVEs | 281 |
| union distinct CVEs in pairs | 281 |
| **unique positive CVEs** | **0** |
| event positive CVEs across windows | 0 |
| calibration | not attempted (0 < 50) |
| decision | PIVOT (on this narrow universe) |

Per-window (real): as t0 advances, catalog-matched disclosed CVEs grow
56 → 118 → 192 → 281 and KEV-as-of-t0 grows 1,117 → 1,159, but
`positive_cves_this_window` is **0** in every window.

**Why 0 here is an artifact, not a feasibility verdict** (same root cause as Step 3.5):
the cached universe spans only ~120 days of *disclosures*. KEV additions in the four
30-day horizons are dominated by CVEs disclosed *years* earlier, whose disclosure
records are absent from this narrow window → they cannot form pairs → cannot be
positive. The demo's purpose is to prove the multi-t0 mechanics run correctly on real
data, which it does.

### Full-scale config — BLOCKED (honest)
`paper2/feasibility/probe_v2_multit0/` — universe **2021-09-01..2025-02-01** (730-day
lookback, 11 chunks), `--use-cached-only` (no key to fetch, no full cache):
- `summary.json`: `blocked: true`, `decision: CONDITIONAL_GO_pending_data_acquisition`.
- `nvd_acquisition_status.json`: `api_key_present: false`, `total_chunks: 11`,
  `completed_chunks: 0`, plus an exact **resume command** and remediation
  ("set `NVD_API_KEY` and re-run without `--use-cached-only`").
- Exit code **3**. No counts fabricated.

We deliberately did **not** hammer NVD with a doomed unauthenticated full-window fetch
(Step 3.5 already established it 429s after ~14 rapid requests). Per the runbook, the
correct outcome is to **stop with a clear blocker: `NVD_API_KEY` required for
full-window feasibility.**

## Decision gate — reasoned application
The literal rule (unique positives < 20 → PIVOT) would fire on the cached demo, but
**0 here is a universe-truncation artifact, not a valid full-scale measurement** — the
narrow 120-day cached universe structurally cannot contain the older disclosure records
of the CVEs that become KEV-listed in the horizons. The full-scale measurement (the one
the gate is meant to judge) is **BLOCKED on `NVD_API_KEY`**, so the gate is **UNRESOLVED**.

- **Not GO** — the positive count is unmeasured at full scale.
- **Not a clean PIVOT** — the 0 is an artifact; the design is sound and untested at scale.
- **Not NO-GO** — feeds are acquirable (KEV/EPSS fully; NVD in ≤120-day paced chunks
  with a key).
- **→ CONDITIONAL GO**, blocked on the single dependency `NVD_API_KEY`.

## To resolve (one command, with a key)
```bash
export NVD_API_KEY=<your_key>
make paper2-multit0-probe        # 2023-09-01..2025-02-01, monthly t0, 730-day lookback
# (interrupted? re-run the same command with --resume; per-chunk caches are reused)
```
Then re-apply the gate on `aggregate.unique_positive_cves`:
- **≥50 + non-degenerate calibration → GO** to Step 4 (pre-registration).
- **20–49 → CONDITIONAL GO** (widen t0 range / lookback / expand catalog).
- **<20 even at full scale → PIVOT** to a robustness/sensitivity-only Paper 2
  (Label A/B, capacity, blackout, imputation sweeps on real-feed features with
  fixed/published weights), or a Paper 3 alternative.

## Invariants honored
Paper 1 frozen outputs untouched (`verify-primary-freeze` OK before and after; probe is
read-only w.r.t. `results/primary_full_v1/`). PoC/ExploitDB stays license-gated and off.
No fabricated counts or citations. This remains a **feasibility probe**, not a calibrated
result and not a paper claim. **Step 4 not started.**

## Artifacts
- `scripts/paper2_feasibility_probe.py` — hardened acquisition + multi-t0 mode.
- `tests/test_paper2_feasibility_probe.py` — 19 tests.
- `Makefile` — new `paper2-multit0-probe` target.
- `paper2/feasibility/probe_v2_multit0_cacheddemo/` — real cached 4-window demo.
- `paper2/feasibility/probe_v2_multit0/` — full-scale BLOCKED artifact (resume command).
