# Claim Boundaries

The single source of truth for what may and may not be stated about Paper 1 in any
EB1A, outreach, or public material. When in doubt, use the "CAN claim" wording.

## CAN claim (accurate, supportable today)

- Independently designed and built a **reproducible benchmark and framework** for
  context-aware vulnerability-host pair prioritization under capacity constraints.
- Produced a **frozen 30-seed primary artifact** (13 strategies; 4,290 per-seed
  metric rows) sealed with a content-addressed freeze manifest that **verifies**.
- Implemented an **append-only, SHA-256 hash-chained audit log**; all 390 audit
  logs in the frozen run verify.
- Evaluated **13 prioritization strategies** (incl. CVSS-only, EPSS-only,
  KEV-first, combined heuristics, the proposed model and ablations, and an oracle).
- Generated **7 tables and 5 figures** programmatically from the frozen artifact.
- Wrote a **complete manuscript** (Abstract + 17 sections) plus an ACM LaTeX
  scaffold and a reproducibility/closeout package.
- Built a tested reference implementation (currently **743 passing tests**) with a
  deterministic, freeze/verify pipeline and strict output inspection.
- Reported a **neutral result honestly**: under the tested synthetic, uncalibrated
  conditions, the proposed model is statistically indistinguishable from EPSS and a
  random ordering.

## CANNOT claim (not true / not supported)

- **Accepted** for publication — it is not.
- **Published** — it is not.
- **Peer-reviewed** or **cited** — it is not; there is no citation impact.
- **Deployed** or **adopted** in any real, government, or production system — it is
  not.
- **Compliance achieved / proven** — the work *supports compliance review* only.
- **Superior model performance** — the proposed model did **not** outperform EPSS
  or a random ordering under the tested conditions.
- **Commercial benchmark superiority** — no commercial RBVM tool was benchmarked.
- **Real-world / government validated** — evaluation is synthetic
  (public-sector-*shaped*), not a real-world or government validation.
- Media interest, endorsements, awards, or external recognition — none claimed.

## Standard safe phrasings

| Instead of | Use |
| --- | --- |
| "published / accepted research" | "completed research manuscript (not yet submitted)" |
| "deployed in government" | "evaluated on a public-sector-shaped synthetic fleet" |
| "outperforms EPSS" | "evaluated against EPSS; result was neutral" |
| "proves/achieves compliance" | "produces audit evidence that supports compliance review" |
| "validated in the real world" | "validated the reproducible artifact's integrity under synthetic conditions" |
| "autonomous remediation" | "capacity-constrained scheduling simulation" |
| "state-of-the-art / first ever" | "original, reproducible benchmark framework" |

## Review note

All EB1A materials require independent **attorney review** before use, and any
recommender/expert statement must reflect only that person's own direct knowledge.
