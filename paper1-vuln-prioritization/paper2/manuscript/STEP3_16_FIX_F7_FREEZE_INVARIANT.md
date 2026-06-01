<!--
Paper 2 — Step 3.16: Fix F7 — Paper-1 Freeze Invariant Contract.
Locks the wrap pattern, audit-record schema, CI/manuscript gate, and weight-
registry test that every Paper-2 run must obey so Paper 1's frozen artefact
(results/primary_full_v1/) is never corrupted, mutated, re-frozen, or
reinterpreted. No code, no experiments, no F2..F6 changes; Paper 1 frozen
outputs untouched.
-->

# Paper 2 — Step 3.16: Fix F7 — Paper-1 Freeze Invariant Contract

**F7 status: COMPLETE.**
**Step 4 still NOT allowed** (F8, F9 owed; F1-mandated framing changes owed).

This document formalises the Paper-1 freeze-invariant contract every Paper-2
run must obey. It restates K6 / SM-6 / S-F2 verbatim in Paper-2 operational
terms, defines the pre-flight / post-run wrap pattern, the per-batch witness
policy, the audit-record schema, the CI / manuscript gate, the forbidden
operations, and the Paper-1 weight-registry lock test that the Step-4
implementation must encode.

---

## 1. The freeze invariant (verbatim restatement of K6 / SM-6 / S-F2)

For every Paper-2 batch B (where a "batch" is the smallest unit a single
`paper2_runtime` invocation runs end-to-end; one batch contains one or more
F6 cells):

- **Pre-flight gate (`G_pre(B)`):** `make verify-primary-freeze PYTHON=.venv/bin/python` exits 0;
  the freeze manifest at `results/primary_full_v1/FREEZE_MANIFEST.json` exists
  and is readable; its SHA-256 is recorded.
- **Post-run gate (`G_post(B)`):** the same command exits 0; the manifest
  SHA-256 is recorded again.
- **Invariant:** `G_pre(B) == OK` AND `G_post(B) == OK` AND
  `sha256(FREEZE_MANIFEST.json) at G_pre == sha256(FREEZE_MANIFEST.json) at G_post`.
- **No path under any Paper-1 territory may be written by B** (see §4 list).
- **No file under `results/primary_full_v1/` (frozen-set members) may be
  modified by B** even by name — addition, deletion, rename, chmod, content
  edit, or atime/mtime touch all count as "modified" if they alter the
  content-addressed verification.

Failure of any clause is a **K6 hard halt**: the batch is invalid, no result
table or figure may be generated from B's output, and the failure must be
recorded with the witness JSON in §6.

### 1.1 Reference manifest (captured at the start of Step 3.16, read-only)
```
results/primary_full_v1/FREEZE_MANIFEST.json
size:       201,491 bytes
sha256:     750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833
status:     freeze verification OK (390 audit logs, valid)
```
This SHA is the *reference checkpoint* used by Step-4 tests to detect any drift
prior to a Paper-2 run; if it disappears or changes for reasons unrelated to a
deliberate, documented Paper-1 re-freeze (which is forbidden during Paper-2
work), the Step-4 implementation halts before any cell runs.

---

## 2. Exact commands (locked)

| Purpose | Command |
|---|---|
| **Freeze verification** (called by both gates) | `make verify-primary-freeze PYTHON=.venv/bin/python` |
| Manifest SHA-256 (POSIX) | `shasum -a 256 results/primary_full_v1/FREEZE_MANIFEST.json` |
| Manifest SHA-256 (Python fallback) | `python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('results/primary_full_v1/FREEZE_MANIFEST.json').read_bytes()).hexdigest())"` |
| Git status snapshot | `git status --porcelain -- results/primary_full_v1 paper/` (output captured short, never includes diffs) |
| **Forbidden (never invoked by Paper-2 code or tests)** | `make freeze-primary`, `make inspect-primary` with `--freeze`, any direct write under `results/primary_full_v1/` |

These commands are the only mechanisms a Paper-2 batch may use to talk to the
Paper-1 freeze. No alternate verifier may be substituted.

---

## 3. Wrap pattern every Paper-2 batch must execute

### 3.1 PRE-FLIGHT
1. Run **`make verify-primary-freeze PYTHON=.venv/bin/python`**; capture stdout / stderr / exit code.
2. Compute SHA-256 of `results/primary_full_v1/FREEZE_MANIFEST.json`.
3. Compute `git status --porcelain -- results/primary_full_v1 paper/` short summary.
4. Write `freeze_witness_before.json` (schema §6.1) with:
   - `freeze_status_before`
   - `freeze_manifest_sha_before`
   - `timestamp_utc`
   - `command`
   - `git_status_short`
   - `paper2_output_dir`
   - `batch_id`
   - `cell_ids` (list)
5. **If `freeze_status_before != "OK"` → K6 HARD HALT** (do not run any cell).

### 3.2 RUN
6. Execute the Paper-2 batch (one or more F6 cells); Paper-2 code may write
   only under the allowed write set (§4); attempted writes outside that set
   raise immediately.

### 3.3 POST-RUN
7. Re-run **`make verify-primary-freeze PYTHON=.venv/bin/python`**; capture exit code.
8. Re-compute SHA-256 of `results/primary_full_v1/FREEZE_MANIFEST.json`.
9. Re-compute `git status --porcelain -- results/primary_full_v1 paper/` short summary.
10. Write `freeze_witness_after.json` (schema §6.2) with the same fields plus
    `output_paths` and any cell-level summary.
11. **Assertions** (all required for a "valid" batch):
    - `freeze_status_before == "OK"`
    - `freeze_status_after == "OK"`
    - `freeze_manifest_sha_before == freeze_manifest_sha_after`
    - `git_status_short` shows **no** path under `results/primary_full_v1/`,
      `paper/tables/`, `paper/figures/`, `paper/manuscript/`, `paper/acm/`,
      `paper/eb1a/` in M / A / D / R / C / U / ?? lines.
    - `freeze-primary` was not executed during the batch (assert via a
      sentinel: a sigil file `paper2/audit/freeze_primary_invocation_count.txt`
      is initialised to `0` at batch start and re-read at end; if any value
      other than `0` is observed, the batch is invalid).
12. Write `freeze_invariant_result.json` (schema §6.3) recording the
    assertion outcome and write `freeze_invariant_result.md` (schema §6.4) as
    a human-readable companion.
13. **If any assertion fails → K6 HARD HALT**: mark the batch invalid, refuse
    to update the Paper-2 result manifest, refuse to emit any paper table or
    figure for the batch, and surface the failing artefact path in the
    abort message.

This pattern is the contract; it must appear verbatim in the Step-4 runner's
test suite.

---

## 4. Allowed vs forbidden write paths

### 4.1 Allowed (Paper 2 may create / write / read)
- `paper2/` and everything under it (`paper2/design/`, `paper2/manuscript/`,
  `paper2/feasibility/`, `paper2/audit/`, future `paper2/results/`,
  `paper2/figures/`, `paper2/tables/`).
- `results/paper2/` (preferred location for the Step-4 per-cell artefacts if
  the team chooses `results/`-rooted layout).
- `data/cache/paper2_probe/` and `data/snapshots/{kev,epss,nvd}/` (existing
  public-feed caches; per Step 3.5–3.8).

### 4.2 Forbidden (Paper 2 code MUST NOT write, mutate, rename, chmod, or touch)
- `results/primary_full_v1/` (Paper-1 frozen artefact; **K6 territory**).
- `paper/tables/`, `paper/figures/`, `paper/manuscript/`, `paper/acm/`,
  `paper/eb1a/` (Paper-1 manuscript / submission / EB1A territory).
- The freeze manifest itself: `results/primary_full_v1/FREEZE_MANIFEST.json`
  is read-only for Paper 2.
- Any path that `git status --porcelain` lists as `M / A / D / R / C / U / ??`
  under the above prefixes at post-run time (a hash match alone is not enough;
  rename / new-file / delete must also be zero).
- Any reuse-only consumer (per F6 §12.4) bypassing the wrap is forbidden — even
  if a batch only reads previously-produced primary cell outputs and produces
  no new EHD numbers, it must still run the pre-flight + post-run wrap.

### 4.3 Forbidden operations (regardless of path)
- Invoking `make freeze-primary` or any `freeze-primary`-equivalent (refreezing
  is a deliberate, Paper-1-only operation).
- Invoking `make inspect-primary` with `--freeze` from inside Paper-2 code or
  CI.
- Calling `paper1.experiments.inspect.freeze(...)` programmatically.
- Editing `FREEZE_MANIFEST.json` for any reason.
- Pickling / re-serialising the Paper-1 metric frames and writing them back
  under `results/primary_full_v1/` even at the same content.

---

## 5. Per-batch vs per-cell policy

F6 enumerates **48 planned runnable cells** + 10 reused references; a batch may
contain one cell, several cells, or all of them. The wrap policy is:

1. **Freeze verification runs once per batch start and once per batch end.**
   It does **not** run before/after every cell — that would be wasteful and
   would tempt operators to skip it.
2. **Every cell record carries the batch's `freeze_witness_id`** (the SHA-256
   of `freeze_witness_before.json` is the witness ID). Step-4 per-cell metric
   rows include `freeze_witness_id` as a required column; tests must reject
   rows missing it.
3. **All cells in a batch inherit the same witness.** If a batch contains
   cells C1..Ck, the witness is shared; if the post-run gate fails, **all**
   C1..Ck are invalid (no partial credit).
4. **Long-running batches may include optional periodic read-only freeze
   checks** every `N` cells (suggested default `N = 8`) as a cheap drift
   sentinel. The optional checks **do not** replace the mandatory pre/post
   gates; they only catch silent corruption earlier so a failed batch can be
   restarted faster. A periodic check that fails immediately triggers
   K6 HARD HALT for the in-progress batch.
5. **Batches must be sized to fit one freeze witness lifecycle.** Splitting the
   1,440 planned seed-runs across multiple batches is allowed; a recommended
   minimum split (decided in F8, not here) is at most one batch per F6 table
   group — i.e., one batch for the 12 primary cells, one for the 15 capacity
   sweep, one for the 9 blackout sweep, one for the 12 ablation sweep. The
   reused references do not run a separate batch; they reference the relevant
   primary batch's witness.

---

## 6. Audit-record schemas

All four files below are written under
`paper2/audit/batches/<batch_id>/` and listed in the per-batch index
`paper2/audit/batches/index.json`. JSON files use the same atomic-write pattern
as Paper 1 (write to `*.tmp` then rename).

### 6.1 `freeze_witness_before.json`
```json
{
  "schema_version": 1,
  "kind": "freeze_witness_before",
  "batch_id": "<short_id, e.g. 'batch-2026-06-15T08-30Z-primary'>",
  "cell_ids": ["<F6 cell_id>", "..."],
  "command": "make verify-primary-freeze PYTHON=.venv/bin/python",
  "timestamp_utc": "<ISO 8601 UTC>",
  "paper1_freeze_manifest_path": "results/primary_full_v1/FREEZE_MANIFEST.json",
  "paper1_freeze_manifest_sha256": "<hex64>",
  "verify_primary_freeze_exit_code": 0,
  "git_status_short": "<output of `git status --porcelain -- results/primary_full_v1 paper/`>",
  "paper2_output_dir": "<dir to which batch results will be written>",
  "freeze_status_before": "OK"
}
```

### 6.2 `freeze_witness_after.json`
```json
{
  "schema_version": 1,
  "kind": "freeze_witness_after",
  "batch_id": "<same as before>",
  "cell_ids": ["<F6 cell_id>", "..."],
  "command": "make verify-primary-freeze PYTHON=.venv/bin/python",
  "timestamp_utc": "<ISO 8601 UTC at batch end>",
  "paper1_freeze_manifest_path": "results/primary_full_v1/FREEZE_MANIFEST.json",
  "paper1_freeze_manifest_sha256": "<hex64; must equal before>",
  "verify_primary_freeze_exit_code": 0,
  "git_status_short": "<output at batch end>",
  "paper2_output_dir": "<dir>",
  "output_paths": ["<absolute or repo-rooted paths>"],
  "freeze_status_after": "OK",
  "freeze_primary_invocation_count": 0
}
```

### 6.3 `freeze_invariant_result.json`
```json
{
  "schema_version": 1,
  "kind": "freeze_invariant_result",
  "batch_id": "<same>",
  "freeze_witness_before_sha256": "<sha256 of freeze_witness_before.json>",
  "freeze_witness_after_sha256":  "<sha256 of freeze_witness_after.json>",
  "freeze_witness_id":            "<freeze_witness_before_sha256, propagated to per-cell rows>",
  "status": "OK | FAIL",
  "failure_reason": null,
  "assertions": {
    "before_status_ok": true,
    "after_status_ok": true,
    "manifest_sha_equal": true,
    "no_paper1_paths_modified": true,
    "no_freeze_primary_invocation": true
  }
}
```
On failure, `status: "FAIL"` and `failure_reason` is a short string from a
closed set: `"before_status_not_ok"`, `"after_status_not_ok"`,
`"manifest_sha_mismatch"`, `"paper1_path_modified"`,
`"freeze_primary_was_invoked"`. The exact failing artefact path is included
in the abort log.

### 6.4 `freeze_invariant_result.md` (human-readable companion)
A short markdown summary suitable for inclusion in batch reports: title,
batch id, before/after timestamps, manifest SHA before/after (side-by-side),
exit codes, status, and a one-line statement of either "Paper 1 freeze
invariant held" or "Paper 1 freeze invariant violated; batch invalid; no
tables/figures derived". No additional content; this is a deterministic
template the runner emits.

### 6.5 `paper2/audit/batches/index.json`
Append-only registry of all batches, one row per batch: `batch_id`,
`status`, `freeze_witness_id`, `cell_ids`, `paper2_output_dir`,
`witnesses` (paths to the four files above). Used by the CI gate (§7) to
find every batch that contributed to a paper table.

---

## 7. CI / manuscript gate (Step 4 implementation contract)

Manuscript tables and figures may be regenerated only from batches whose
freeze witnesses pass. The CI step (extending the Paper-1 Phase-21/22A
claim-audit precedent) **must fail the build** if any of the following hold
for any source row of any Paper-2 table / figure:

1. `freeze_witness_before.json` missing for the row's batch.
2. `freeze_witness_after.json` missing for the row's batch.
3. `manifest_sha_before != manifest_sha_after` for the row's batch.
4. `verify_primary_freeze_exit_code != 0` at either gate.
5. `git_status_short` at either gate contains any path under the §4.2
   forbidden write set.
6. `freeze_primary_invocation_count != 0` at the post-run gate.
7. Any source row lacks the `freeze_witness_id` column (rows missing the
   witness cannot be trusted).
8. The paper table is regenerated from a Paper-2 metric frame whose
   per-row `freeze_witness_id` does not appear in
   `paper2/audit/batches/index.json` with `status == "OK"`.

CI must also fail if a manuscript markdown source includes any of the F3 §6
forbidden phrases (F3-forbidden-phrase guard) or any SM-4 / SM-5
significance-language misuse near a CLM-D1 / CLM-G1 metric name (SM-5).

Re-use case: if a Paper-2 reused-cell consumer (F6 §12.4) builds a table
from a primary cell's output without re-running it, the consumer's batch
witness still applies; the consumer batch must itself wrap; "the primary
already wrapped" is not a substitute.

---

## 8. Paper-1 weight-registry lock test (Step 4 implementation must include)

A Paper-2 unit test (proposed location: `tests/test_paper1_weights_locked.py`)
must assert that the existing Paper-1 built-in vectors have **exact** keys,
**exact** numeric values, and the correct `R`-as-cost semantics, so any
future Step-4 edit to `src/paper1/model/weights.py` that drifts a Paper-1
weight value is detected immediately. The test is **read-only** w.r.t. the
registry: it imports `get_weights` (which returns a normalised copy) and the
internal `_BUILTIN` dictionary, and asserts:

```python
from paper1.model.weights import _BUILTIN, FEATURE_COLUMNS, get_weights

# (i) keys
assert FEATURE_COLUMNS == ["E", "K", "S", "C", "X", "U", "R"]
for name in ("w_uniform", "w_hand", "w_logit_placeholder", "w_lin_placeholder"):
    assert set(_BUILTIN[name].keys()) == set(FEATURE_COLUMNS)

# (ii) exact raw values (un-normalised; mirrors the registry literal)
assert _BUILTIN["w_uniform"] == dict.fromkeys(FEATURE_COLUMNS, 1.0)
EXPECTED_HAND = {"E": 0.20, "K": 0.20, "S": 0.10, "C": 0.20, "X": 0.15, "U": 0.10, "R": 0.05}
assert _BUILTIN["w_hand"]              == EXPECTED_HAND
assert _BUILTIN["w_logit_placeholder"] == EXPECTED_HAND   # placeholder mirrors w_hand
assert _BUILTIN["w_lin_placeholder"]   == EXPECTED_HAND

# (iii) sum-to-1 after normalisation (registry contract)
for name in ("w_uniform", "w_hand", "w_logit_placeholder", "w_lin_placeholder"):
    w = get_weights(name)
    assert abs(sum(w.values()) - 1.0) < 1e-12

# (iv) R remains a non-negative magnitude (cost handled by paper1.model.scoring
#     via sign-flip; the registry never makes R negative)
for name in ("w_uniform", "w_hand", "w_logit_placeholder", "w_lin_placeholder"):
    assert get_weights(name)["R"] >= 0.0

# (v) Paper-1 built-ins cannot be overwritten by Paper 2.
import pytest
from paper1.model.weights import register_weights
with pytest.raises(ValueError):
    register_weights("w_hand", {**EXPECTED_HAND}, overwrite=True)
with pytest.raises(ValueError):
    register_weights("w_logit_placeholder", {**EXPECTED_HAND}, overwrite=True)

# (vi) Paper 2 may register new F2 vectors at non-built-in names without
# mutating any Paper-1 built-in. (Round-trip via list_weights.)
from paper1.model.weights import list_weights
names_before = set(list_weights())
register_weights("w_epss_dominant",
                 {"E":0.50,"K":0.15,"S":0.10,"C":0.10,"X":0.05,"U":0.05,"R":0.05})
assert "w_epss_dominant" in list_weights()
# Built-ins are unchanged after the new registration:
assert _BUILTIN["w_hand"] == EXPECTED_HAND
assert _BUILTIN["w_logit_placeholder"] == EXPECTED_HAND
assert _BUILTIN["w_lin_placeholder"] == EXPECTED_HAND
assert _BUILTIN["w_uniform"] == dict.fromkeys(FEATURE_COLUMNS, 1.0)
```

The test must run in the Paper-2 CI pipeline on every push touching `src/`,
`paper2/`, or `tests/`. Failure blocks Paper-2 work until the registry is
restored to the locked values.

Step 4 implementation will additionally register the four new F2 vectors —
`w_epss_dominant`, `w_cvss_dominant`, `w_kev_dominant`, `w_context_dominant` —
using `register_weights` (not `register_calibrated_weights`, which K1
forbids). The locks above ensure those additions cannot collide with or
overwrite the Paper-1 built-ins.

---

## 9. Forbidden operations summary (no ambiguity for future readers)

Paper-2 code, tests, scripts, notebooks, CI workflows, and manuscript build
steps **may not**:

- Run `make freeze-primary`, or `make inspect-primary` with `--freeze`.
- Call `paper1.experiments.inspect.freeze(...)` or any equivalent re-freezer.
- Write under `results/primary_full_v1/`, `paper/tables/`, `paper/figures/`,
  `paper/manuscript/`, `paper/acm/`, `paper/eb1a/` for any reason.
- Edit `FREEZE_MANIFEST.json` even at the same content.
- Bypass the pre-flight or post-run wrap, even for reuse-only batches or
  diagnostic-only outputs.
- Treat a hash-match alone as success — both the freeze verification exit and
  the `git status --porcelain` "no Paper-1 paths modified" assertion must
  also hold.
- Generate paper tables / figures from a Paper-2 metric frame whose per-row
  `freeze_witness_id` is not registered as `status == "OK"` in
  `paper2/audit/batches/index.json`.
- Use `register_calibrated_weights` anywhere in Paper-2 (K1 forbid-list).

---

## 10. Implementation implications for Step 4 (NOT executed here)

1. Create `paper2_runtime.freeze_invariant` (new module under `paper2_runtime`,
   **not** under `src/paper1/`) implementing:
   - `pre_flight(batch_id, cell_ids, paper2_output_dir) -> WitnessBefore`
   - `post_run(witness_before, batch_id, output_paths) -> InvariantResult`
   - context manager `wrap(batch_id, cell_ids, paper2_output_dir)` that calls
     pre/post and raises `Paper1FreezeInvariantViolation` on any failure.
2. The Step-4 runner shells out to `make verify-primary-freeze PYTHON=.venv/bin/python` (no
   re-implementation of the verifier in Paper-2 code); records exit code,
   manifest SHA, `git status --porcelain` short.
3. A sigil file `paper2/audit/freeze_primary_invocation_count.txt` is
   initialised to `0` at pre-flight; any call to `make freeze-primary`
   anywhere in the process tree under the wrap must increment it (the
   recommended enforcement is a wrapper shell that intercepts the target),
   so post-run can assert `== 0`. If integrating that intercept is
   impractical, the equivalent guard is a `chmod -w` on the freeze manifest
   for the batch lifetime; either is acceptable, both must be tested.
4. Per-cell metric rows include `freeze_witness_id` as a required column;
   `validate_per_seed_metric_frame` (in `paper1.evaluation.statistical_tests`)
   must be wrapped by a Paper-2-side validator that additionally asserts
   the witness id exists in the batches index with `status == OK`.
5. The CI workflow re-uses the Paper-1 Phase-21/22A pattern: scan
   `paper2/audit/batches/index.json`, cross-reference with table source
   metric frames, fail the build if §7 (1)–(8) is violated.
6. The Paper-1 weight-registry lock test (§8) lands in `tests/` and runs in
   the same `pytest` invocation as Paper 2's own tests.
7. **No edits to `src/paper1/`.** All Paper-2 wiring lives under a new
   `paper2_runtime/` package (or `scripts/paper2_*`); the Paper-1 freeze
   set is read-only forever.
8. No test in Step 4 may register a calibrated weight via
   `register_calibrated_weights`; CI must scan for that symbol in
   `paper2_runtime/` and `tests/` (excluding `tests/test_paper1_weights_locked.py`
   which references it only to ensure the symbol still exists in Paper-1
   API).

---

## 11. F7 status & open items
- **F7: COMPLETE.** Freeze-invariant contract locked (commands, wrap pattern,
  per-batch witness policy, audit-record schemas, CI gate, weight-registry
  lock test, forbidden operations). Reference manifest SHA recorded.
- **Step 4 still NOT allowed.** F8 (compute budget + fallback selection from
  F6 §8), F9 (venue plan + change-our-minds clause) remain owed; Step-3.10
  framing changes remain owed.

## Invariants honored
Paper 1 frozen outputs untouched (this step only **read** the manifest path,
its size, and its SHA-256 — no write). No experiments; no code; no metric or
axis or cell changes; no F2/F3/F4/F5/F6 changes; no calibration claim. PoC
license-gated and off. `[VERIFY]` items from F1/F2 still pending pre-manuscript.
