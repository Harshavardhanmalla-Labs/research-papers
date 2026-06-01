<!--
Paper 2 — Step 3.8: Resumed full multi-t0 feasibility run with NVD_API_KEY.
Real public-feed measurement (NVD/EPSS/KEV); no counts fabricated; key value never
echoed or written to any artifact. Paper 1 (results/primary_full_v1/) untouched and
freeze-verified.
-->

# Paper 2 — Step 3.8: Full Multi-t0 Feasibility Result (NVD key) — PIVOT

**Decision: PIVOT.** The full-scale multi-t0 run completed cleanly with real
public-feed data. The gating metric — UNIQUE distinct positive CVEs — is **7**,
below the PIVOT threshold of 20. **Step 4 pre-registration for the
calibrated-prioritization Paper 2 is NOT allowed.** The recommended path is to
pivot Paper 2 to a robustness/sensitivity-only study (real-feed features with
fixed/published weights; Label A/B, capacity, blackout, imputation sweeps),
*or* — as an optional explore-first step — attempt CONDITIONAL territory by
expanding the product catalog and re-running before pivoting.

## Step 1 — key check
`echo ${NVD_API_KEY:+NVD_API_KEY_SET}` printed empty in the agent's shell (the
key was provided in-message, not in env). Per user intent it was inlined into the
probe process only; **its value was never echoed, logged, or written to any
artifact.** The probe records the boolean `api_key_present: true` and nothing more.
*(Recommend rotating the key since it appeared in the chat transcript.)*

## Step 2 — Paper 1 freeze
`make verify-primary-freeze` → **OK** (390 audit logs valid; verification OK) both
**before** the run and **after** the run.

## Step 3 — resumed multi-t0 run
`make paper2-multit0-probe`-equivalent CLI with `--resume`, key in env, 0.6 s pacing.
Real fetch + leakage-safe per-window pass over 18 monthly t0s in the EPSS v3 era.
Exit code **0**.

### NVD acquisition
| | |
|---|---|
| API key present | **yes** |
| Universe window | 2021-09-01 .. 2025-02-01 (730-day lookback) |
| Chunks completed / total | **11 / 11** |
| Chunks reused from Step-3.7 cache | **2** (`2021-09-01..2021-12-29` 7,634 recs; `2021-12-30..2022-04-28` 8,375 recs) |
| Chunks fetched this run | **9** (chunks 3–11, ~8.5k–14k recs each) |
| Total NVD records | **110,224** |
| HTTP 429 retries | **0** (keyed + 0.6 s pacing held throughout) |

### Per-window labels (real)
18 monthly t0 windows; `H=30`; fleet=500; seed=20260601. Positive CVEs per window:

| t0 | distinct CVEs in pairs | positive CVEs | positive pairs |
|---|---:|---:|---:|
| 2023-09-01 | 1,673 | 0 | 0 |
| 2023-10-01 | 1,733 | **2** | 592 |
| 2023-11-01 | 1,812 | 0 | 0 |
| 2023-12-01 | 1,860 | **2** | 20 |
| 2024-01-01 | 1,899 | **1** | 293 |
| 2024-02-01 | 1,963 | **1** | 293 |
| 2024-03-01..2025-01-01 (11 windows) | 2,015–2,635 | **0** each | 0 |
| 2025-02-01 | 2,688 | **1** | 295 |
| **Aggregate** | **2,688 union** | **7 event total** | **1,493** |

### Aggregate feasibility (REAL, full scale)
| Metric | Value |
|---|---:|
| n_windows | **18** |
| total NVD records | 110,224 |
| normalized CVEs | 104,495 |
| CVEs with CPE | 95,006 |
| catalog-matched CVEs | **2,688** (≈2.8 % of CPE'd) |
| union distinct CVEs in pairs | 2,688 |
| **unique positive distinct CVEs** | **7** |
| event positive CVEs across windows | 7 (each unique positive appears in exactly one window) |
| unique negative distinct CVEs | 2,681 |
| EPSS coverage | 17/18 windows ≥ 99.3 %; 1 window (2024-12-01) missing snapshot (graceful) |
| calibration attempted | **no** (7 < 50) |
| logistic / ridge | not attempted |
| non-degenerate weights | n/a |
| leakage warnings | **none** (Label A strictly over `(t0, t0+H]`; KEV-as-of-t0 used only as feature) |
| Paper 1 freeze | **OK** (verified before and after) |

## Step 5 — decision gate (applied)
The literal rubric:
- **GO**: unique positives ≥ 50 + non-degenerate calibration + EPSS coverage acceptable
  + both classes + no leakage warnings.
- **CONDITIONAL GO**: 20–49 positives, OR calibration unstable but fixable, OR catalog
  matching promising but needs expansion.
- **PIVOT**: < 20 positives after full multi-t0, OR calibration degenerate despite
  enough positives, OR Label A too sparse.
- **NO-GO**: feeds unacquirable / leakage-safe labels impossible / mapping unusable.

Applied to the real result:

| Criterion | Observed | Verdict |
|---|---|---|
| unique positive distinct CVEs ≥ 50 | **7** | fails GO |
| 20–49 positives | **7** | fails CONDITIONAL on counts |
| < 20 positives after full multi-t0 | **7** | **fires PIVOT** |
| Label A too sparse | 7 events across 18 monthly windows × 2,688 CVEs (≈0.014 % event rate) | also fires PIVOT |
| feeds acquirable | all 110,224 NVD recs + 18 monthly EPSS snapshots + KEV | NO-GO ruled out |
| leakage-safe labels | yes, `(t0, t0+H]` enforced | NO-GO ruled out |

**Final decision: PIVOT.** This is the **honest, leakage-safe, full-scale**
verdict — not an artifact of universe truncation, missing keys, or rate limits
(all of which are now resolved). Calibrating per-feature weights against a future-KEV
label is structurally infeasible for our 31-product catalog over the EPSS v3 era:
KEV additions intersected with our catalog and our 30-day horizons yield only ~7
labelable positive CVEs in 17 months.

**Step 4 pre-registration for the calibrated-prioritization Paper 2 is NOT allowed.**

## Pivot options (in priority order; ALL still require explicit user GO and a fresh Step 4)
1. **Robustness / sensitivity-only Paper 2** (recommended): real public-feed features
   (E, K, S) with **fixed / published weights** (no calibration claim). Study label
   sensitivity (A vs. B), capacity sensitivity, blackout-window sensitivity, and EPSS
   imputation/coverage sensitivity on a real-public-fleet-shaped extension of Paper 1's
   frozen benchmark. No superiority claim required; framed as a sensitivity analysis.
2. **Explore CONDITIONAL territory before pivoting** (optional, one-shot):
   expand the product catalog from 31 to ~100+ public-sector-typical products
   (e.g., add jenkins, gitlab, atlassian suite, vmware, citrix, fortinet, cisco
   ios/asa, microsoft exchange/sharepoint, oracle weblogic, ivanti, solarwinds,
   wordpress, drupal, …). Re-run the same multi-t0 probe. If unique positives
   then land in 20–49 → **CONDITIONAL GO** path opens (still not GO). Likely
   ceiling at this monthly cadence: tens, not hundreds. **Do not** attempt this
   without an explicit user OK because it asks the gate question a second time
   (a known weak-evidence move).
3. **Paper 3 alternative** entirely (e.g., the KEV-prediction or scheduler-policy
   framing previously discussed).

## What CANNOT now be claimed
- Calibration feasibility on public feeds for this catalog/era — **disproven** at scale.
- Any model-superiority result — there is no calibration to compare.
- Public-feed positivity for our catalog — empirically ~7 CVEs / 17 months / 18 windows.

## Invariants honored
Paper 1 frozen outputs untouched (`verify-primary-freeze` OK before and after; probe
remains read-only w.r.t. `results/primary_full_v1/`). PoC/ExploitDB license-gated and
off. No fabricated counts. No paper drafting. **Step 4 not started.** The provided
API key value was never echoed, logged, or written to any artifact — only the boolean
`api_key_present: true` is recorded.
