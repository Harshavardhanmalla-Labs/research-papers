# Paper 2 — Plain-English Summary (USCIS-Friendly)

**One-sentence summary.** The author designed, ran, and audited a study that
asked whether public exploit-signal feeds are dense enough to support
defensible per-feature weight fitting for vulnerability prioritization, and
honestly reported that on this dataset they are not.

## Why this kind of summary matters

Vulnerability prioritization is the cybersecurity sub-field that decides
which software flaws an organization should patch first. The field has many
tools (CVSS, EPSS, KEV, SSVC, and others), and many recent papers fit
per-feature weights on public exploit signals. A pre-condition for that kind
of fitting is having enough positive examples — CVEs that were actually
exploited — to support statistical inference. Paper 2 measured how many
positive examples are actually available on public feeds under a leakage-safe
labelling scheme and found the count was far below the threshold needed for
defensible weight fitting.

## What the author built

1. **A failure-aware multi-t0 calibration gate.** Before any weight fitting
   would run, the gate counts unique positive CVEs across multiple time
   windows under a leakage-safe label. If the count is below a pre-registered
   minimum, the gate refuses to fit weights and records the reason. This
   prevents a fragile calibration step from being attempted on insufficient
   data.

2. **A reproducible sparse-label methodology.** A pre-registered design
   (locked across nine fix documents, F1–F9, before any data was collected)
   that records every stop rule, every weight vector, every metric binding,
   every inference threshold, and every freeze invariant in machine-readable
   form. Every metric row in the run carries a freeze-witness identifier
   that ties it back to the Paper 1 frozen artefact.

3. **A confirmatory sensitivity framework.** With the calibration step
   blocked by the gate, the author ran a 48-cell sensitivity study using
   fixed (non-fitted) priors to characterise how outcome quantities move
   under changes in capacity, blackout schedule, weight family, and feature
   ablation. The framework reports its own stop-rule triggers and
   demotes any axis where within-cell seed noise exceeds across-cell signal.

## What the author honestly reports

- **7 unique positive CVEs** across **18 monthly t0 windows**.
- **2,688 catalog-matched CVEs** from a synthetic 31-product catalog.
- **Calibration was not attempted.** The pre-registered K1 stop rule fired
  because 7 < 50.
- **48 primary cells × 30 seeds = 1,440 seed-runs**; **8,640 metric rows**.
- Across-cell deltas are reported as **descriptive only** because the K8
  stop rule (within-cell seed noise > across-cell signal) fired on every
  measured axis.
- Per-feature weight fitting was not attempted; therefore no learned model
  exists in this study.

## What this work does NOT claim

- It does not claim the manuscript has been peer-reviewed or accepted.
- It does not claim any prioritization strategy beats another on this
  dataset.
- It does not claim the methodology is in use anywhere outside this
  repository.
- It does not claim any role for any agency, vendor, or external
  organization.
- It does not claim compliance with any external standard.

## What the work shows

- That an author can design, run, audit, and honestly report on a
  cybersecurity experiment whose primary purpose is to surface a negative
  result.
- That a failure-aware methodology can prevent a community-common pattern
  (fit weights on whatever public exploit data is available) from producing
  statistically unjustified outputs.
- That a reproducible artefact chain (pre-registration → runner → audit →
  manuscript → submission scaffold) can be built end-to-end while keeping a
  prior frozen artefact (Paper 1) byte-equal throughout.

## Status

- Manuscript draft exists at `paper2/manuscript/paper2_full_draft.md`.
- Submission scaffold exists at `paper2/submission/`.
- **No paper has been sent to any venue. No external party has reviewed,
  accepted, or used the work.**
