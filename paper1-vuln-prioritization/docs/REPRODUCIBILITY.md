# Reproducibility guide

## Current phase

**Phase 1 — foundation.** The repository currently contains schemas,
utilities, and the audit hash chain. Subsequent phases (feed clients,
synthetic generator, scoring strategies, scheduler, metrics,
experiments) are not yet implemented.

## Determinism contract

- All randomness is seeded from a master seed declared in the
  experiment config. Sub-seeds are derived from `(master_seed, name)`
  via SHA-256 (`paper1.utils.seeds.derive_subseed`). The derivation is
  deterministic across machines and Python versions.
- All datetimes are timezone-aware UTC. Naive datetimes are rejected at
  schema-load time (`paper1.utils.time.ensure_utc`).
- Simulation time is advanced exclusively through
  `paper1.utils.time.SimulationClock`; no code reads `datetime.now()`
  while a simulation is in progress.

## Audit trail

- Every decision produced by the framework is written to an append-only
  JSONL audit log via `paper1.audit.AuditLogger`.
- Each record carries an SHA-256 `record_hash` of its canonical payload
  (excluding `record_hash` itself) and a `prior_record_hash` chained
  to the previous record. The genesis prior hash is 64 zeros.
- `paper1.audit.verify_chain(path)` returns `(ok, issues)` for a log
  file; tampering with any record's content invalidates that record's
  self-hash and breaks the chain at the next record.

## File integrity

- `paper1.utils.io.compute_file_sha256(path)` streams a checksum that
  is recorded in run manifests so that downstream consumers can verify
  inputs match the configuration the run was committed to.

## Repository layout

```
configs/    Pre-registered experiment + sensitivity configurations
src/        paper1 package (Phase 1: audit/, utils/)
tests/      pytest suite (Phase 1: schema, hash chain, utils, configs)
data/       Runtime caches and bundled snapshots; mostly gitignored
results/    Experiment outputs (gitignored)
figures/    Generated figures (gitignored)
scripts/    One-off fetch / validation scripts (Phase 2+)
```

## Verifying a fresh clone

```bash
make install-dev
make test         # 101 tests pass on Phase 1
make compile      # byte-compile to surface SyntaxError
make lint         # ruff lint
```

## Data licensing

No real production fleet data is included. Real public feeds (NVD,
FIRST EPSS, CISA KEV, optionally ExploitDB) are fetched by scripts in
`scripts/` (to be added in Phase 2) and cached locally. Bundled snapshot
inclusion in releases is subject to the upstream license of each feed
and is documented in `LICENSE_DATA.md` (to be added before release).
