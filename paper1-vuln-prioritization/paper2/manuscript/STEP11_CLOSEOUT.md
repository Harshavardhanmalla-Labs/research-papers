# Paper 2 — Step 11 Closeout Report

**Step:** 11 (Final claim / citation audit + submission packaging)
**Date (UTC):** 2026-05-28
**Status:** COMPLETE — packaging finished, all final checks PASS.
**Submission status:** **NOT submitted.** No paper has been sent to any venue
and no submission portal was contacted. Per the standing rule "Do NOT submit
the paper."

## Files created in Step 11

### Submission tree (`paper2/submission/`)
- `README.md` — package overview, target venue (CSET), backups (LASER,
  DTRAP), remaining blockers, compile instructions, what-not-to-claim.
- `REPRODUCIBILITY_APPENDIX.md` — 26-row table mapping every major numeric
  claim to its source file and field.
- `CLAIM_AUDIT_REPORT.md` — audit script invocations, PASS result, files
  scanned, forbidden vocabulary, waivers (none).
- `CITATION_AUDIT_REPORT.md` — re-verification of three carried [VERIFY]
  blockers, 15-entry verified table, items requiring human review, risk
  assessment.

### LaTeX scaffold (`paper2/submission/cset/`)
- `README.md` — template status, compile recipe, section table, copy counts,
  formatting TODOs.
- `main.tex` — neutral `\documentclass{article}` scaffold with 16
  `\input{sections/...}` lines + `\bibliography{references}`.
- `references.bib` — 15 verified BibTeX entries.
- `sections/00_abstract.tex` ... `sections/15_reproducibility.tex` — 16
  auto-converted section files (wording preserved verbatim).
- `figures/` — 14 figures (7 PNG + 7 PDF) copied from `paper2/figures/`.
- `tables/` — 19 top-level table files + `tables/inference/` 12 inference
  table files = 33 total.

### Scripts (`scripts/`)
- `paper2_md_to_latex.py` — markdown → LaTeX converter (split-on-H2,
  conservative inline conversion, LaTeX-escaping). Created in Step 11.
- `paper2_claim_audit.py` — already present from Step 10; not modified in
  Step 11.

### Manuscript draft (`paper2/manuscript/`)
- `paper2_full_draft.md` — minor metadata corrections only (VULCON author
  Jajodia, NIST CSWP 41 authors Mell & Spring, VulnScore full title,
  removal of `[VERIFY]` markers). No claims added, no semantic change.
- `STEP11_CLOSEOUT.md` — this file.

## Citation status

| Citation | Step 10 status | Step 11 outcome |
|---|---|---|
| VULCON (Farris et al., ACM TOPS 2018) | `[VERIFY]` blocker | VERIFIED via Crossref `10.1145/3196884`; author Jajodia corrected. |
| NIST CSWP 41 (Mell & Spring, May 2025) | `[VERIFY]` blocker | VERIFIED via NIST press release + official PDF. |
| VulnScore (Alqahtani & Almukaynizi, IJIS 2025) | `[VERIFY]` blocker | VERIFIED via Crossref `10.1007/s10207-025-01164-3`; full title resolved. |
| Other 12 entries | already verified | unchanged, copied into `references.bib`. |

Unresolved `[VERIFY]` markers in the draft or bibliography: **0.**
Items flagged for routine pre-submission human review: 4 (see
`paper2/submission/CITATION_AUDIT_REPORT.md` §"Items requiring human review
before submission"). None of these block packaging.

## Claim audit

Both targets PASS with **0 violations**:

```
$ python3 scripts/paper2_claim_audit.py paper2/manuscript/paper2_full_draft.md
PASS  paper2/manuscript/paper2_full_draft.md (0 violations)

$ cat paper2/submission/cset/sections/*.tex > /tmp/paper2_concat.tex
$ python3 scripts/paper2_claim_audit.py /tmp/paper2_concat.tex
PASS  /tmp/paper2_concat.tex (0 violations)
```

The second invocation verifies wording was preserved through the markdown →
LaTeX conversion.

## LaTeX scaffold status

- Template class: NEUTRAL `\documentclass[11pt,letterpaper]{article}` with a
  conservative package list. Marked `[VERIFY with current CSET CFP/template]`
  in `main.tex` and in `paper2/submission/cset/README.md`.
- Section files: 16 produced by `scripts/paper2_md_to_latex.py`.
- Compile pass: **NOT performed** in Step 11. The repository does not
  guarantee a `pdflatex` toolchain and the brief flagged the compile step as
  optional ("record status; do not fail Step 11"). Human reviewer must run
  the compile recipe in `cset/README.md` at submission time.

## Reproducibility appendix

`paper2/submission/REPRODUCIBILITY_APPENDIX.md` contains a 26-row table
mapping each major numeric claim to source file + source field:

- 7 unique positive distinct CVEs → `feasibility/probe_v2_multit0/summary.json`
- 2,688 catalog-matched CVEs → same file
- 18 t0 windows → same file
- 4 pilot batches / 288 pilot seed-runs → `audit/pilot_gate_decision.json`
- 4 primary batches / 1,440 primary seed-runs / 48 cells → `audit/primary_complete.json`
- 8,640 metric rows → sum of `per_batch[*].per_row_total` (audit JSON)
- K1 / K3 / S-A triggers → primary + pilot audit JSON
- PRIMARY_COMPLETE_VALID → primary audit JSON
- Step-9 tables / inference / figures counts → `audit/step9_aggregation_complete.json`
- Freeze manifest SHA → `paper/report/report_manifest.json`
- K2 (does not fire) / K7 (SKIPPED) / K8 (fires every axis) →
  `audit/post_run_stop_rule_evaluation.json`
- No learned/calibrated cells → primary audit + feasibility summary
  (`calibration.attempted = false`, reason field).

## Paper 1 freeze invariant

Verified at the close of Step 11:

```
freeze_manifest_sha = 750e144ba9567b5255b27ce40279643bdf7418d53b15edce5d72c515eb022833
```

Recorded at `paper/report/report_manifest.json` AND carried as
`freeze_witness_id` on every per-batch summary in
`paper2/audit/primary_complete.json` (all 4 batches verified). Paper 1
manuscript / output directories were not modified in Step 11. Standing rule
"Do NOT modify Paper 1 frozen outputs" / "Do NOT modify Paper 1 manuscript /
output directories" held.

## Final checks

| Check | Result |
|---|---|
| `python -m compileall -q scripts/ paper2_runtime/` | PASS (no output) |
| `ruff check scripts/paper2_md_to_latex.py scripts/paper2_claim_audit.py paper2_runtime/` | PASS — "All checks passed!" |
| `pytest tests/test_paper2_*.py` | PASS — **154 passed in 26.71s** |
| Paper 1 freeze SHA matches expected | PASS |
| Paper 2 primary witness IDs match Paper 1 SHA on all 4 batches | PASS |
| Claim audit on draft markdown | PASS — 0 violations |
| Claim audit on concatenated LaTeX sections | PASS — 0 violations |

## Attorney / mentor review readiness

The package contains the artifacts a reviewer would need to confirm scope,
discipline, and reproducibility without re-running the pipeline:

- **What the paper claims**: visible in `paper2/manuscript/paper2_full_draft.md`.
- **What the paper does NOT claim**: enumerated in `paper2/submission/README.md`
  §"What this paper does NOT claim".
- **How every number is sourced**: in `paper2/submission/REPRODUCIBILITY_APPENDIX.md`.
- **Citation provenance**: in `paper2/submission/CITATION_AUDIT_REPORT.md`.
- **Forbidden-phrase enforcement**: in `paper2/submission/CLAIM_AUDIT_REPORT.md`
  (with the audit script at `scripts/paper2_claim_audit.py`).
- **Stop-rule discipline**: pre-registered in `paper2_runtime/stop_rules.py`,
  triggers in `paper2/tables/post_run_stop_rules.csv`.

## Submission readiness

**Packaging:** complete. **Submission:** held. The package is ready for a
human reviewer to lock the venue template, replace the placeholder author
block, address the four human-review citation items, run the LaTeX compile
recipe, and submit. None of those operations were performed in Step 11.

## Remaining manual tasks (deferred to human reviewer)

1. Lock the current USENIX CSET document class and swap it into `main.tex`.
2. Decide on anonymization mode for the current CSET round; replace
   `\author{Anonymous (submission scaffold)}` accordingly.
3. Replace the two `{...authors}` placeholders in `references.bib` (VulRG,
   VMChaining) with author lists confirmed against the arXiv preprint PDFs.
4. Confirm `Sherif2026KRI` arXiv identifier and publication month.
5. If `Ravalico2025EPSSDynamics` has a peer-reviewed venue version available
   before submission, prefer that.
6. Run the LaTeX compile recipe in `paper2/submission/cset/README.md` and
   resolve any environment-specific errors.
7. (Optional) Prepare LASER and DTRAP backup scaffolds by repeating the
   template-substitution step against those venue classes.

No code or data changes are required to complete any of these tasks.
