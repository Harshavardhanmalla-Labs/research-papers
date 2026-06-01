<!--
Paper 2 — Step 3.7: Full multi-t0 feasibility run with NVD_API_KEY and gate.
HONEST STATUS: NVD_API_KEY was NOT actually present in this environment (verified
three ways), so the unauthenticated full-window fetch hit HTTP 429 after 2/11 chunks.
No feasibility counts are fabricated. The gate remains UNRESOLVED (blocked on the key).
Paper 1 (results/primary_full_v1/) untouched and freeze-verified.
-->

# Paper 2 — Step 3.7: Full Multi-t0 Feasibility Run (NVD key) — Result

**Decision: CONDITIONAL GO — gate UNRESOLVED, still blocked on `NVD_API_KEY`.**
Step 4 pre-registration is **NOT** allowed.

## Environment reality vs. task premise
The task said to *assume* `NVD_API_KEY` is available. **It is not present in this
environment** — verified three independent ways and no `.env` file exists:

| Check | Result |
| --- | --- |
| `echo ${NVD_API_KEY:+NVD_API_KEY_SET}` | empty (unset) |
| `python -c "os.environ.get('NVD_API_KEY')"` | `UNSET` |
| `printenv NVD_API_KEY` | absent |
| `.env` / `.env.local` | none |
| probe-internal `api_key_present` | `False` |

Per the hard rule **"do not fake counts,"** I did not invent a key or any feasibility
numbers. I ran the real target; without a key it fetched unauthenticated and blocked.

## Step 1 — environment
- `NVD_API_KEY`: **UNSET** (see table above).
- `make verify-primary-freeze`: **OK** (390 audit logs valid; freeze verification OK).

## Step 2 — full multi-t0 run (`make paper2-multit0-probe`)
Real, paced (6 s), unauthenticated fetch of the universe `2021-09-01 .. 2025-02-01`
(730-day lookback, **11** ≤120-day chunks). It reached **HTTP 429 on chunk 3**:

| Chunk | Window | Status | Records |
| --- | --- | --- | --- |
| 1 | 2021-09-01 .. 2021-12-29 | fetched (cached) | 7,634 |
| 2 | 2021-12-30 .. 2022-04-28 | fetched (cached) | 8,375 |
| 3 | 2022-04-29 .. 2022-08-26 | **FAILED — HTTP 429** | — |
| 4–11 | … | not attempted | — |

The hardened acquisition behaved exactly as designed:
- **Partial cache preserved**: `data/cache/paper2_probe/nvd_chunk_2021-09-01_2021-12-29.json`
  (38 MB) and `…_2021-12-30_2022-04-28.json` (42 MB) are on disk — real data, reusable.
- **Exact chunk reached** reported: chunk 3 `2022-04-29..2022-08-26`.
- **Resume command** written to `nvd_acquisition_status.json` (see below).
- Exit code **3**; no fabricated success.

This reproduces, at the multi-year scale, the Step 3.5 finding: **unauthenticated NVD
cannot fetch the full universe** — a key is mandatory.

## Step 3 — outputs read
Only the acquisition-stage artifacts exist (the probe blocks **during NVD acquisition**,
before the per-window labelling pass, so the downstream files are intentionally not
written — their absence is honest, not an error):

- `summary.json` → `blocked: true`, `decision: CONDITIONAL_GO_pending_data_acquisition`.
- `summary.md` → blocked notice.
- `nvd_acquisition_status.json` → `api_key_present: false`, `completed_chunks: 2`,
  `total_chunks: 11`, per-chunk statuses, and:
  `resume_command: "NVD_API_KEY=<your_key> .venv/bin/python scripts/paper2_feasibility_probe.py --resume --start-date 2021-09-01 --end-date 2025-02-01  # add --multi-t0 and the same t0/lookback flags"`.
- **Absent (acquisition blocked first):** `per_t0_counts.csv`, `aggregate_counts.csv`,
  `label_counts.csv`, `epss_coverage.csv`, `calibration_status.json`, `decision_gate.json`.

## Step 4 — extracted values
| Item | Value |
| --- | --- |
| NVD acquisition status | **BLOCKED (HTTP 429, unauthenticated)** |
| chunks completed / total | **2 / 11** (chunks 1–2 cached; chunk 3 failed) |
| t0 windows evaluated | **0** (per-window pass never started) |
| total matched CVEs | **not measured** |
| unique distinct CVEs | **not measured** |
| unique positive distinct CVEs | **not measured** (NOT 0 — unmeasured) |
| per-window positive CVE distribution | **not measured** |
| positive pair count | **not measured** |
| EPSS coverage | **not measured** |
| calibration attempted | **no** (gate not reached) |
| logistic calibration status | not attempted |
| ridge calibration status | not attempted |
| non-degenerate weights | n/a |
| leakage warnings | none (no labels were constructed; leakage-safe design unchanged) |
| Paper 1 freeze status | **OK** (verified before and after; probe is read-only w.r.t. Paper 1) |

## Step 5 — decision gate (reasoned)
The gating metric — **unique positive distinct CVEs** — is **unmeasured** because NVD
acquisition blocked on the unauthenticated rate limit. Mapping to the rubric:

- **Not GO**: the positive count is unknown; no non-degenerate calibration exists.
- **Not PIVOT**: the design was never exercised at scale; there is no 0/<20 measurement
  to act on (the only positive-count we have is the Step-3.6 *narrow-universe artifact*).
- **Not NO-GO**: public feeds **are** acquirable — chunks 1–2 fetched cleanly, KEV/EPSS
  fetch fine, and leakage-safe labels are constructible. The blocker is solely the
  *unauthenticated* rate limit, removed by a key.
- **→ CONDITIONAL GO**, blocked on the single dependency **`NVD_API_KEY`**
  (= "public-feed fetch blocked → CONDITIONAL GO pending data acquisition; do not fake
  success").

**Step 4 pre-registration is NOT allowed** — the feasibility gate has not passed.

## To resolve (one command, once a real key is in the environment)
```bash
export NVD_API_KEY=<your_key>          # must be visible to the probe's process
make verify-primary-freeze PYTHON=.venv/bin/python
make paper2-multit0-probe PYTHON=.venv/bin/python
# Chunks 1–2 (2021-09-01..2022-04-28) are already cached; add --resume to reuse them:
#   NVD_API_KEY=<key> .venv/bin/python scripts/paper2_feasibility_probe.py --resume \
#     --multi-t0 --t0-start 2023-09-01 --t0-end 2025-02-01 --t0-frequency monthly \
#     --nvd-lookback-days 730 --h-days 30 --fleet-size 500 --seed 20260601 \
#     --nvd-sleep-seconds 0.6 --out paper2/feasibility/probe_v2_multit0 --min-positive-cves 50
```
With a key, NVD recommends ~0.6 s pacing (`--nvd-sleep-seconds 0.6`). Then re-apply the
gate on `aggregate.unique_positive_cves`: ≥50 + non-degenerate → GO (Step 4); 20–49 →
CONDITIONAL; <20 → PIVOT to a robustness/sensitivity-only Paper 2.

## Invariants honored
Paper 1 frozen outputs untouched (freeze OK before/after). PoC/ExploitDB license-gated
and off. No fabricated counts or citations. Feasibility probe only — not a calibrated
result, not a paper claim. **Step 4 not started.**
