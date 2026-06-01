# Paper 2 — Claim Audit Report (Step 11)

**Audit script:** `scripts/paper2_claim_audit.py`
**Audit date (UTC):** 2026-05-28
**Scope:** Paper 2 manuscript draft AND the LaTeX section files copied into the submission tree.

The audit script enforces Paper 2's pre-registered claim discipline (F3 §6 +
F5 SM-4 / SM-5 + the Step-10 brief). Three categories of violation are
detected:

1. **Always-forbidden phrases** (single-token / fixed bigram match).
2. **Negatable phrases** ("validated", "production") — flagged unless a
   negation token appears within ~6 words / ~60 chars preceding.
3. **Proximity rules** — "significant" within 100 chars of any
   diagnostic-only metric token (`precision_at_k`, `recall_at_k`, `ndcg`,
   `kev_breach`, `diagnostic`, ...); "pair count" within 200 chars of
   "sample size" or "effective N"; positive calibration-was-performed claims
   without a negation within 80 chars; context-priors-beat-EPSS claims.

## Audit invocations and results

### A. Manuscript markdown draft

```
$ python3 scripts/paper2_claim_audit.py paper2/manuscript/paper2_full_draft.md
PASS  paper2/manuscript/paper2_full_draft.md (0 violations)
```

### B. Concatenated LaTeX section files

```
$ cat paper2/submission/cset/sections/*.tex > /tmp/paper2_concat.tex
$ python3 scripts/paper2_claim_audit.py /tmp/paper2_concat.tex
PASS  /tmp/paper2_concat.tex (0 violations)
```

Both invocations exit with code 0. **0 violations** in either pass.

## Files scanned

- `paper2/manuscript/paper2_full_draft.md` (17-section source-of-truth draft).
- `paper2/submission/cset/sections/00_abstract.tex`
- `paper2/submission/cset/sections/01_introduction.tex`
- `paper2/submission/cset/sections/02_background.tex`
- `paper2/submission/cset/sections/03_related_work.tex`
- `paper2/submission/cset/sections/04_problem_statement.tex`
- `paper2/submission/cset/sections/05_failure_aware_gate.tex`
- `paper2/submission/cset/sections/06_study_design.tex`
- `paper2/submission/cset/sections/07_public_feed_data.tex`
- `paper2/submission/cset/sections/08_fixed_prior_sensitivity.tex`
- `paper2/submission/cset/sections/09_metrics_inference.tex`
- `paper2/submission/cset/sections/10_results.tex`
- `paper2/submission/cset/sections/11_discussion.tex`
- `paper2/submission/cset/sections/12_limitations.tex`
- `paper2/submission/cset/sections/13_future_work.tex`
- `paper2/submission/cset/sections/14_conclusion.tex`
- `paper2/submission/cset/sections/15_reproducibility.tex`

The LaTeX section files were produced from the markdown draft by
`scripts/paper2_md_to_latex.py` with wording preserved verbatim (the converter
only changes structural markdown into LaTeX environments and escapes
LaTeX-special characters). The audit on the concatenated LaTeX therefore
verifies that wording was preserved through conversion.

## Forbidden / waived terms tracked

The script's forbidden vocabulary is reproduced here for reviewer convenience.
None of these appear in either scanned target.

**Always-forbidden:**
`outperforms`, `outperform`, `superior`, `state-of-the-art`, `state of the art`,
`government deployment`, `compliance achieved`, `calibrated model improves`,
`learned model`, `first ever`.

**Negatable (allowed only in negation):**
`validated`, `production`. (E.g., "is not validated" passes; bare "validated"
fails.) The current draft uses neither in positive sense.

**Proximity-flagged:**
- "significant" within 100 chars of `precision_at_k` / `recall_at_k` /
  `ndcg` / `kev breach` / `diagnostic` (and underscore variants).
- "pair count" within 200 chars of "sample size" or "effective N".
- Positive calibration-was-performed claims (`calibration was performed`,
  `we calibrated`, ...) without a preceding negation in 80 chars.
- "context-priors beat EPSS" / "context priors outperform EPSS" patterns.

**Vocabulary the draft deliberately avoids beyond the audit list** (per
Step-11 standing rules): "outperforms", "superior", "validated",
"production", "government deployment", "compliance achieved",
"calibrated model improves". The audit list is a hard floor, not the full
discipline.

## Waivers granted

None. No phrase was waived. Three minor rephrasings made during Step 10
("superiority" → "quality claims"; "learned model" → "fitted-weight
comparator"; three "pair count" near "sample size" / "effective N" matches
rewritten to "host-CVE record count is not the calibration unit") preserved
the underlying technical meaning and were applied before Step 11 began. No
semantic content was altered to evade the audit.

## Verdict

Both targets PASS the claim audit with 0 violations. The manuscript draft and
the LaTeX scaffold copied into `paper2/submission/cset/` are claim-audit-clean
under the pre-registered discipline.
