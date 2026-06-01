# Paper 2 — Claim Boundaries

This file is the enforceable wording rule for every other document in
`paper2/eb1a/`, for any recommender letter drawing from this folder, and for
any media or social-media post about Paper 2. It is *internal*. Read it
before writing or signing off on any external-facing artefact.

## The single sentence the discipline reduces to

**Paper 2 is a methodology paper and an honest negative result that has not
been peer-reviewed, accepted, cited, or used outside this repository.**

If a sentence in a draft cannot survive that single-sentence summary as a
backdrop, the sentence must be rewritten.

## What MAY be claimed

The following statements are honest and supported by repository artefacts.

1. **"The author built a reproducible methodology."**
   Supported by: `paper2_runtime/` package + 154 passing tests +
   pre-registration in `STEP4_PREREGISTRATION.md` and F1–F9 fix documents.

2. **"The author produced public-feed sparse-label feasibility evidence."**
   Supported by: `paper2/feasibility/probe_v2_multit0/summary.json` showing
   7 unique positive CVEs across 18 monthly time-origin windows and 2,688
   catalog-matched CVEs.

3. **"The author created a failure-aware calibration gate."**
   Supported by: the pre-registered K1 stop rule and the runtime's refusal
   to fit weights when K1 fires.

4. **"The author's gate prevented a statistically unjustified
   calibration step."**
   Supported by: `feasibility/probe_v2_multit0/summary.json`
   `calibration.attempted = false`, reason "unique positive distinct CVEs
   7 < min 50".

5. **"The author generated an audited primary run."**
   Supported by: `audit/primary_complete.json` `status =
   PRIMARY_COMPLETE_VALID`, 48 cells, 1,440 seed-runs, 8,640 metric rows,
   per-row freeze-witness coverage 100%.

6. **"The author generated a submission scaffold."**
   Supported by: `paper2/submission/cset/` LaTeX scaffold and the four
   top-level submission documents.

7. **"The author reported a negative result honestly."**
   Supported by: claim-audit report (`PASS  0 violations`) and
   citation-audit report (15 verified entries, 0 unresolved `[VERIFY]`).

## What MUST NOT be claimed

The following statements are not supported by repository artefacts and must
not appear in any document in this folder, in any letter drawing from this
folder, or in any media artefact about Paper 2.

| Forbidden claim | Why it is forbidden |
|---|---|
| "The paper has been accepted" | No paper has been sent to any venue. |
| "The paper is published" | Same. |
| "The paper is peer-reviewed" | Same. |
| "The paper is cited" | No external citations exist. |
| "The methodology is used / installed / running anywhere" | It exists only in this repository. |
| "The methodology has been adopted" | No external adoption has occurred. |
| "The methodology has been proven" | "Proven" overstates what an audited run shows. |
| "The methodology is guaranteed" | Negative-result methodology guarantees nothing. |
| "Our model is superior to EPSS / CVSS / ..." | No fitted model exists in this study, and K8 fires on every measured axis. |
| "Our model has been validated" | The word "validated" overstates an internal audit; use "audited" or "verified". |
| "The methodology meets a government / agency standard" | No agency engagement has occurred. |
| "The work is production-grade" | This is a research artefact, not a runtime artefact. |
| "The work achieves compliance" | No compliance regime has been engaged. |
| "Our calibrated model improves on the baseline" | No calibrated model was fit. |

## Vocabulary substitution table

When in doubt about a word, substitute as follows.

| Risky word | Safer substitute |
|---|---|
| "validated" | "audited" / "verified" / "documented" |
| "proven" | "shown" / "documented" / "audited" |
| "guaranteed" | (no substitute — rewrite the sentence) |
| "adopted" | (no substitute — do not claim adoption) |
| "deployed" | "built" / "constructed" / "implemented in the repository" |
| "production" | "experimental" / "research" / "manuscript" |
| "in use" | (no substitute — do not claim use) |
| "endorsed" | (no substitute — do not claim endorsement) |
| "superior to" | "differs from" / "differentiates against" |
| "outperforms" | (forbidden — do not use even with negation) |
| "calibrated model" | "fixed-prior sensitivity sweep" (since no calibration was fit) |
| "government" | (no substitute — do not invoke an agency role) |
| "compliance" | (no substitute — do not invoke a compliance regime) |
| "first ever" | "the first instance in this repository of" (or rewrite) |

## How this file is enforced

1. An overclaim scan runs across `paper2/eb1a/` for the substring set
   {`accepted`, `published`, `cited`, `deployed`, `adopted`, `proven`,
   `guaranteed`, `superior`, `validated`, `government`, `production`,
   `compliance`, `calibrated model improves`}. Any hit is reviewed
   manually before the file ships.
2. The claim-audit script `scripts/paper2_claim_audit.py` continues to
   gate the manuscript.
3. Any letter, post, or pitch drawing from this folder must be re-checked
   against this file by both the author and the author's attorney /
   mentor before going public.
