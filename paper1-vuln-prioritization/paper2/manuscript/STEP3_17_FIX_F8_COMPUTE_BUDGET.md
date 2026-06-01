<!--
Paper 2 — Step 3.17: Fix F8 — Compute budget + fallback locked.
Locks the compute envelope, selects the F8-f pilot-then-primary plan, sets the
fallback escalation order, fixes the shared-computation architecture
requirements, and lists the planned batches. F6 source-of-truth CSV/YAML is
NOT mutated; this report's companion file is paper2/design/STEP3_17_PLANNED_BATCHES.yaml.
No code, no experiments, no F2..F7 changes; Paper 1 frozen outputs untouched.
-->

# Paper 2 — Step 3.17: Fix F8 — Compute Budget and Fallback Lock

**F8 status: COMPLETE.**
**Step 4 still NOT allowed** (F9 owed; F1-mandated framing changes owed).

This document locks the compute envelope, evaluates the F6 fallback options,
selects **F8-f pilot-then-primary**, and freezes the planned-batches selection
(materialised at `paper2/design/STEP3_17_PLANNED_BATCHES.yaml`). F6
(`paper2/design/STEP3_15_MINIMAL_FACTORIAL_CELLS.{csv,yaml}`) is **not** mutated.

---

## 1. Compute envelope (locked)

| Field | Value | Notes |
|---|---|---|
| Target wall-clock | **≤ 12 h** | soft target for combined pilot + primary |
| Hard maximum wall-clock | **18 h** | absolute ceiling; pilot gate enforces against this |
| Per-batch abort factor | **×1.5** | any batch exceeding 1.5 × estimated max pauses for review |
| Max CPU utilisation | **≤ 90 %** | reserves headroom for the OS / freeze verification calls |
| Memory budget | **≤ 16 GB** | sized for a developer laptop |
| Disk budget (incremental) | **≤ 25 GB** | under `paper2/results`, `paper2/audit`, `data/cache/` |
| Parallelism policy | **seed-level**, `max_workers = 4` (2 if `mem < 16 GB`) | distinct seeds in parallel; cells inside one seed run serially to *reuse* per-t0 feature frames |
| Checkpoint cadence | acquisition (once/run) · per-t0 feature frame (once/seed×t0) · per-cell result · per-batch summary | enables resume from finest practical granularity |
| Abort threshold | batch runtime > 1.5 × estimated maximum | pause + manual approval (per §6) |
| Resume policy | skip completed seed / cell checkpoints; re-verify Paper-1 freeze at every resumed batch boundary (F7); re-emit fresh witness | `--force` required for any recomputation |
| Acceptable overnight runs | **2** | tolerates spanning two evenings; refuse anything beyond |

---

## 2. F6 option evaluation

| Option | Description | Cost reduction vs FULL | Impact on claims |
|---|---|---|---|
| **FULL** | F6 verbatim: 48 cells × 30 seeds = 1,440 seed-runs | 0 % | none; baseline |
| **F8-a** | seed reduction n=30 → n=15 | ≈ 50 % | F4 MDE-d at n=15 ≈ 0.78 → MDE-hd ≈ 1,965 hd (×1.0), 2,948 hd (×1.5); still clears 5,000 hd meaningful threshold, **but margin thins**; SM-2 escalation more likely to bind |
| **F8-b** | collapse capacity sweep to {0.01 reused, 0.05} | ≈ 20 % | CLM-C2 Holm family collapses to 1 pair per strategy |
| **F8-c** | collapse blackout sweep to {primary reused, strict} | ≈ 15 % | CLM-C3 Holm family collapses to 1 pair per strategy |
| **F8-d** | collapse ablation set to {`remove_E`, `remove_K`, `remove_C`, `remove_X`} (defer `remove_S`, `remove_R`) | ≈ 30 % of ablation cells | CLM-C4 loses S/R ablation cells; report explicitly |
| **F8-e** | collapse weight vectors to {`w_paper1_placeholder`, `w_epss_dominant`, `w_context_dominant`} | ≈ 50 % of `proposed_fixed_prior` primary + ablation cells | CLM-C1 Holm family shrinks from C(6,2) = 15 to C(3,2) = 3 pairs; CLM-B1 still has its 5-pair baseline family |
| **F8-f** | **pilot-then-primary** — 6-seed pilot across all 48 runnable cells, then 30-seed primary if pilot projects within budget | 0 % scope reduction; runtime risk-managed | preserves F6 design; allows fallback only if measured projection exceeds the hard ceiling |

### 2.1 Why **F8-f** is the right call
- Preserves the entire F6 design (no claims weakened a priori).
- The pilot measures *actual* per-seed-run wall-clock under the planned
  shared-computation architecture, so the runtime projection that drives any
  fallback decision is empirical, not speculative.
- Cost of the pilot itself is bounded: **288 seed-runs ≈ 2–4 h**.
- A failed pilot still surfaces real blockers (cache-miss, scheduler bug,
  freeze-verify regression) before they amplify across 1,440 seed-runs.
- Fallback escalation is *deterministic* (§3), so a pilot-driven fallback
  cannot become a post-hoc cherry-pick.

---

## 3. Chosen plan (locked)

**Plan: F8-f pilot-then-primary.** Pilot runs first; if and only if the pilot's
projected primary runtime fits the hard ceiling, the primary runs against the
full F6 cell set; otherwise the fallback escalation in §4 fires.

| Stage | Batches | Cells | Seeds / cell | Seed-runs | Estimated wall-clock (h) |
|---|---:|---:|---:|---:|---:|
| **Pilot** | 4 | 48 | **6** | **288** | **2.0 – 4.0** |
| **Primary** | 4 | 48 | **30** | **1,440** | **9.8 – 19.5** *(serial estimate; ÷ 4 with seed-level parallelism)* |
| **Combined** | 8 | — | — | **1,728** | **11.8 – 23.5** *(serial)* / **~3 – 6** *(with `max_workers = 4`)* |

The mid-estimate (~19.5 h primary, serial) is just above the 18-h hard ceiling;
parallelism (max_workers = 4) is expected to bring this to 3–6 h on the
optimistic end. **The pilot exists precisely to measure this** before
committing to the primary.

---

## 4. Fallback escalation order (locked, deterministic)

Applied **only if** the pilot's projected primary runtime exceeds
`compute_envelope.hard_max_wallclock_hours = 18`. Stop at the first option that
brings the projection back within budget.

| Order | Option | Description | Why this order |
|---:|---|---|---|
| 1 | **F8-e** | collapse weights to 3 | biggest savings without seed reduction (≈ 50 % of `proposed_fixed_prior` rows); F4 MDE still clears the meaningful threshold for the C(3,2)=3 Holm pairs |
| 2 | **F8-d** | collapse ablation to {`remove_E`, `remove_K`, `remove_C`, `remove_X`} | second-biggest savings; report drops S/R ablation cells explicitly |
| 3 | **F8-c** | collapse blackout sweep to {primary, strict} | small but easy; CLM-C3 family collapses to 1 pair per strategy |
| 4 | **F8-b** | collapse capacity sweep to {0.01 reused, 0.05} | similar to F8-c; CLM-C2 family collapses to 1 pair per strategy |
| 5 | **F8-a** | seed reduction n=30 → n=15 | **LAST RESORT**; weakens paired-seed power |

**Pilot-only fallback is closed by default** (`pilot_only_fallback.enabled =
false` in the YAML). Pilot does NOT replace primary unless a written
`STEP3_17.x_*.md` supplement and a new decision-log row explicitly enable it.

---

## 5. Shared-computation architecture requirements (locked; binding)

These requirements are what make the optimistic ~3–6 h primary runtime
achievable. They are binding on the Step-4 runner.

**Must**:
- Build NVD universe **once per run** (cache hits on
  `data/cache/paper2_probe/nvd_chunk_*.json` from Step 3.7 / 3.8).
- Build **EPSS / KEV as-of maps once per t0** (per the 18-window set).
- **Generate fleet once per seed** (using `FleetGenerator`).
- **Build vulnerability-host pair frames once per seed × t0**.
- **Compute feature frames once per seed × t0**.
- **Reuse feature frames** across all strategies, weight vectors, capacities,
  blackouts, approvers, and ablations within the same `(seed, t0)`.
- **Scheduler runs per cell** (different capacity / blackout / approver per
  cell).
- **Metrics run per cell**.
- **Freeze witness wraps every batch** (F7 contract).
- **Stop-rule evaluation runs per batch and per_run gates** per F5 registry.

**Must not**:
- Re-fetch any NVD chunk during pilot or primary (forbidden inside the wrap).
- Mutate F6 source-of-truth CSV/YAML (this F8 YAML is the *only* selector).
- Bypass the freeze wrap for reuse-only consumers (F7 §5).

---

## 6. Planned batches summary

Sourced from F6 via `cell_filter` strings; the F6 CSV/YAML is not mutated.
Each batch carries its own F7 freeze witness; checkpoints are required;
stop-rule gates are pre-registered per stage.

### 6.1 Pilot batches (6 seeds each; 4 batches)

| `batch_id` | F6 group | Cells | Seed-runs | Est. h | Stop-rule gates (post-run) |
|---|---|---:|---:|---|---|
| **B-pilot-primary** | primary | 12 | 72 | 0.5–1.0 | K5, S-C3, F4 pilot-runtime projection |
| **B-pilot-capacity** | capacity_sensitivity | 15 | 90 | 0.6–1.2 | K5 |
| **B-pilot-blackout** | blackout_sensitivity | 9 | 54 | 0.4–0.8 | K5 |
| **B-pilot-ablation** | feature_ablation | 12 | 72 | 0.5–1.0 | K5 |
| **Pilot total** | — | **48** | **288** | **2.0–4.0** | — |

Pre-flight gates on every pilot batch: K1, K3, K6. Per-cell gates: K3, K4,
S-C3, S-E1, S-E2. Per-comparison inferential gates are deferred to primary
batches (pilot uses descriptives only).

### 6.2 Pilot gate (decides whether primary launches)

| Field | Source | Decision rule |
|---|---|---|
| `measured_per_seed_run_seconds` | mean wall-clock across the 288 pilot seed-runs | computed at pilot end |
| `projected_primary_runtime_hours` | `measured_per_seed_run_seconds × 1,440 ÷ 3,600 ÷ effective_parallelism` | derived |
| **Decision** | `PROCEED_TO_PRIMARY_NO_FALLBACK` if projection ≤ 18 h | else `APPLY_FALLBACK_ORDER_AND_REPLAN` |

Required pilot passes (any failure blocks primary):
- K6 freeze invariant held at every pilot batch.
- K5 audit chain valid on every pilot batch.
- K4 `scheduler_feasibility_rate ≥ 0.95` on every primary-group pilot cell.
- K3 status confirmed (already TRIGGERED — informational only, never blocking).

### 6.3 Primary batches (30 seeds each; 4 batches; only if pilot passes)

| `batch_id` | F6 group | Cells | Seed-runs | Est. h (serial) | Stop-rule gates (post-run) |
|---|---|---:|---:|---|---|
| **B-primary-primary** | primary | 12 | 360 | 2.5–5.0 | K2, K5, K7, K8, S-B1, S-B3, S-C1, S-C2, S-C4 |
| **B-primary-capacity** | capacity_sensitivity | 15 | 450 | 3.0–6.0 | K2, K5, K8, S-C2 |
| **B-primary-blackout** | blackout_sensitivity | 9 | 270 | 1.8–3.5 | K2, K5, K8, S-C3 |
| **B-primary-ablation** | feature_ablation | 12 | 360 | 2.5–5.0 | K2, K5, K8, S-C4 |
| **Primary total** | — | **48** | **1,440** | **9.8–19.5** *(serial; ÷ 4 with seed-parallelism)* | — |

Per-comparison gates: SM-1, SM-2, SM-3 (only on B-primary-primary; SM-3 binds
CLM-B3 oracle inference to *disabled*). Manuscript gates: SM-4, SM-5,
F3-forbidden-phrase-guard.

---

## 7. Abort / resume semantics (locked)

| Trigger | Action | Source |
|---|---|---|
| Batch runtime > 1.5 × estimated max | pause at next checkpoint; `batch_status = paused_runtime_exceeded`; require manual approval before next batch | §1 envelope |
| K6 or K5 fires at pre-flight or post-run | hard halt; mark in-progress cells invalid; no resume without freeze-restoration ticket | F5 / F7 |
| K2 fires across **every** primary axis after primary completes | paper reframed as failure-aware methodology only; do **not** re-tune to manufacture a robustness signal | F5 K2 |
| K4 fires (any cell `scheduler_feasibility_rate < 0.95`) | exclude that cell from primary operational claims with a written footnote; record `cell_excluded` audit row | F5 K4 / S-C3 |
| Resume after pause / halt | skip completed seed/cell checkpoints; re-verify Paper-1 freeze at every resumed batch boundary; re-load F6 + F8 YAMLs; emit a fresh freeze witness for the resumed batch | F7 |
| `--force` recompute of a completed cell | requires explicit flag **and** a new decision-log row before the rerun is accepted | conservative default |

---

## 8. Implementation implications for Step 4 (NOT executed here)

1. **Runner loads two YAMLs at startup**: F6 cell enumeration (immutable) and
   F8 planned-batches (this file's YAML). It refuses to launch any batch
   whose `cell_filter` resolves to cells not present in F6.
2. **Seed-level parallelism**: `max_workers = 4` (or `2` on low-memory hosts).
   Workers fan out across distinct seeds within a batch; cells within a
   `(worker, seed)` run serially to reuse the per-t0 feature frame.
3. **Acquisition checkpoint**: the runner checks `data/cache/paper2_probe/`
   for the 11 NVD chunk caches at startup; if all present, acquisition is a
   no-op; if any missing, it falls back to Step 3.8's keyed chunked
   acquisition (NOT a fresh full-window fetch — the F8 wrap forbids that
   inside a batch).
4. **Per-cell result checkpoint**: each finished cell writes
   `paper2/results/<batch_id>/<cell_id>/per_seed_metrics.csv` (atomic) and
   `…/_meta.json` carrying the F7 `freeze_witness_id`. Resumption logic skips
   checkpoints that already exist with a verified `_meta.json`.
5. **Pilot-gate evaluator**: a small post-pilot script computes
   `measured_per_seed_run_seconds` and the projection; writes
   `paper2/audit/pilot_gate_decision.json` (`PROCEED_TO_PRIMARY_NO_FALLBACK`
   or `APPLY_FALLBACK_ORDER_AND_REPLAN` with the option to apply). The primary
   runner refuses to start without this file present and `status == PROCEED`.
6. **Fallback re-planner**: if the pilot decision is fallback, the
   re-planner re-emits **only** the F8 planned-batches YAML (a new file
   `STEP3_17.x_PLANNED_BATCHES_FALLBACK_<id>.yaml`) and a decision-log row.
   F6 stays unchanged.
7. **Resume semantics** are enforced by the runner's startup check: it loads
   `paper2/audit/batches/index.json`, lists completed cells, and never
   recomputes them unless `--force` is passed.
8. **No Paper-1 path is ever written** (F7 contract); the runner's filesystem
   wrapper raises on any attempted write outside the allowed set.

---

## 9. F8 status & open items
- **F8: COMPLETE.** Compute envelope locked; fallback order locked; pilot +
  primary batch layout committed; shared-computation requirements binding;
  abort / resume semantics enumerated. The Step-4 implementation contract
  identifies exactly which file (`STEP3_17_PLANNED_BATCHES.yaml`) the runner
  loads alongside F6.
- **Step 4 still NOT allowed.** F9 (venue plan + change-our-minds clause)
  remains owed. The Step-3.10 framing changes (drop "Robustness" headline,
  demote sensitivity sweeps to confirmatory, elevate the failure-aware gate
  to primary, cite P1–P15 with visible differentiation, drop "fixed/published
  weights" wording, acknowledge synthetic-fleet limitation, no `[CITATION]`
  placeholders) remain owed.

## Invariants honored
Paper 1 frozen outputs untouched (no writes anywhere under
`results/primary_full_v1/` or `paper/`). No experiments run; no code written;
no F2/F3/F4/F5/F6/F7 changes. No calibration claim, no superiority claim. The
calibration-feasibility claim remains anchored to unique positive distinct
CVEs (not pair count). PoC license-gated and off.
