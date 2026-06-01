<!--
Paper 2 — Step 3: Data Acquisition Runbook for the public-feed feasibility probe.
Run in a NETWORK-ENABLED environment (or with cached snapshots). Uses public
feeds only (NVD/EPSS/KEV); PoC/ExploitDB stays OFF (license-gated). Paper 1 frozen
outputs are never touched. No counts may be fabricated; if blocked, report the
blocker honestly.
-->

# Paper 2 — Data Acquisition Runbook (Feasibility Probe)

Goal: obtain real (or cached) public-feed data so the probe can measure the
distinct-positive-CVE count that gates Paper 2.

Window (defaults): NVD CVEs `2023-06-01 .. 2024-09-30`; `t0 = 2024-09-01`,
`H = 30` (label horizon `(2024-09-01, 2024-10-01]`); single EPSS era (v3:
2023-03-07 .. 2025-03-16). EPSS-as-of-t0 needs the snapshot for `2024-09-01`
(sample a few prior days for coverage stability).

## 1. Network-enabled command path

```bash
# Optional but recommended for NVD rate limits:
export NVD_API_KEY=<your_key>        # if scripts/fetch_nvd.py supports it; else omit

make fetch-nvd  START=2023-06-01 END=2024-09-30
make fetch-kev  AS_OF=2024-10-01      # AS_OF >= t0+H so labels are observable
make fetch-epss START=2024-08-30 END=2024-09-01
make validate-snapshots
make paper2-feasibility-probe PYTHON=.venv/bin/python
```

Notes:
- KEV is cumulative; fetching as-of `2024-10-01` ensures in-horizon KEV additions
  are present for Label A. The probe separately uses KEV as-of `t0` for the K
  feature (no future leakage).
- PoC/ExploitDB stays OFF. To include Label B locally (NOT redistributable), set
  `PAPER1_ENABLE_POC_FETCH=true` and pass `--include-poc`; never commit PoC data.

## 2. Offline cached path

If snapshots/cache already exist (e.g., a prior fetch):

```bash
.venv/bin/python scripts/paper2_feasibility_probe.py \
  --use-cached-only \
  --out paper2/feasibility/probe_v1
```

`--use-cached-only` (and `--skip-fetch`) make the probe load only cached data and
**fail clearly** if the cache is missing — it never silently fabricates.

## 3. Failure handling

| Symptom | Likely cause | Action |
| --- | --- | --- |
| NVD `HTTP 403` / `429` / throttling | rate limit / no API key | set `NVD_API_KEY`; reduce window; retry with backoff; NVD limits unauthenticated requests |
| NVD `HTTP 404` / network refused | no/blocked network | run in a networked environment, or use the cached path |
| Missing NVD API key warning | key not set | proceed unauthenticated for a small window, or set the key for the full window |
| EPSS snapshot unavailable for a date | weekend/gap or pre-2021-04-14 | pick an adjacent available date in the same EPSS era; never cross a model-version boundary |
| KEV fetch issue | endpoint change / network | retry; or supply a cached `kev.json` |
| `make validate-snapshots` fails | checksum/manifest mismatch | re-fetch the offending snapshot; do not proceed on a corrupt cache |
| Insufficient positive CVEs (<20) | KEV rarity / catalog too small | expand date window and/or product catalog; if still low → PIVOT (see gate) |
| `PoCLicenseGateError` | `--include-poc` without the env gate | leave PoC off (default), or set `PAPER1_ENABLE_POC_FETCH=true` and keep PoC data local |

If any feed is blocked and no cache exists, the probe writes a `blocked` summary
and exits non-zero (code 3). That is the correct, honest outcome — **do not fake
counts**.

## 4. Expected output files (on a successful run)

```
paper2/feasibility/probe_v1/summary.json          # params, counts, calibration, decision
paper2/feasibility/probe_v1/summary.md            # human-readable summary
paper2/feasibility/probe_v1/cve_match_counts.csv  # NVD->normalized->cpe->catalog-matched
paper2/feasibility/probe_v1/label_counts.csv      # positive/negative CVEs & pairs, KEV future-label
paper2/feasibility/probe_v1/epss_coverage.csv     # EPSS coverage of paired CVEs per sampled day
paper2/feasibility/probe_v1/calibration_status.json  # attempted? reason / non-degenerate / weights
```

On a blocked run, only `summary.json` + `summary.md` are written (marked
`blocked: true`).

## 5. After the run — apply the decision gate

Read `summary.json -> counts.label_a_positive_cves` and
`calibration.non_degenerate`:
- **≥ 50 + non-degenerate → GO** to pre-registration (Step 4).
- **20–49 → CONDITIONAL GO**: widen window / expand catalog; re-run.
- **< 20 → PIVOT** away from calibration (robustness/sensitivity-only study).

Then update `PAPER2_DECISION_LOG.md` with the measured counts and the resulting
decision. Do not draft the paper or run calibration beyond the probe until the gate
is satisfied.
