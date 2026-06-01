# Paper 2 — Short Media Pitch (Internal Draft)

**Status.** Internal draft for possible use with technical-press contacts
*only after* the manuscript has been submitted and the author's attorney /
mentor has reviewed this file. The pitch makes no claim of acceptance,
publication, citation, or external use. It describes a methodology artefact
and an honest negative result.

## Headline options (rank in order of safety)

1. *"When calibration shouldn't be attempted: a failure-aware methodology
   for vulnerability prioritization under sparse exploit labels."*
2. *"A negative-result methodology for vulnerability prioritization."*
3. *"How to build a sparse-label feasibility gate for vulnerability
   prioritization research."*

(Do not use headlines with words like "beats", "best", "ready", "accepted",
"published", "in use", "endorsed", "approved".)

## Two-sentence pitch

A common pattern in vulnerability-prioritization research fits per-feature
weights using whatever exploit-positive labels public feeds happen to
contain. The author built a failure-aware multi-time-origin methodology that
measures the label density first and refuses to fit when the density is too
low, and reports a real example in which the density was indeed too low
(7 unique positive CVEs across 18 monthly time-origin windows on a 2,688-CVE
catalog).

## Longer pitch (≤ 200 words)

Vulnerability prioritization decides which software flaws an organization
should patch first. Many recent papers combine CVSS, EPSS, and KEV signals
by fitting per-feature weights on public exploit data. A pre-condition for
that kind of fitting is having enough unique positive examples — CVEs that
were actually exploited — under a leakage-safe label window. The author
built a methodology that measures the count first.

On a 31-product synthetic catalog, 18 monthly time-origin windows from
2023-09 through 2025-02, and a leakage-safe horizon of 30 days, the
methodology found 7 unique positive CVEs across 2,688 catalog-matched CVEs.
A pre-registered stop rule then refused to fit per-feature weights and
recorded the reason. The remaining work is a 48-cell fixed-prior
sensitivity sweep whose across-cell deltas the author honestly demotes to
descriptive only, on the basis of a pre-registered noise-versus-signal
criterion.

The artefact is reproducible end-to-end: a pre-registration, a runner, an
audit chain, a manuscript draft, a submission scaffold, and a claim-audit
script that the author runs over the manuscript itself. The report exists
to make a negative result legible.

## What the journalist may ask, and a safe answer to each

**Q: Did you publish this?**
A: There is a manuscript draft and a submission scaffold. No paper has been
sent to a venue at this time. No external party has accepted, peer-reviewed,
or cited the work.

**Q: Is your method better than EPSS?**
A: The paper does not make that claim. The methodology refuses to fit
weights on this dataset, so no fitted comparator exists. The fixed-prior
sensitivity sweep reports across-cell deltas as descriptive only.

**Q: Could a company use this tomorrow?**
A: This is a methodology paper. Anyone who wants to ask the same label-
density question on their own catalog can re-run the pre-registered pipeline
and get an answer; the artefact does not assert it is a finished or
ready-to-run system.

**Q: Has any agency endorsed this?**
A: No. The author has not sought and does not claim endorsement from any
agency, vendor, standards body, or other organization.

## Boilerplate the journalist may use

The author is a researcher working on cybersecurity methodology. The
artefact described here is a public-feed sparse-label feasibility study and
a failure-aware calibration gate for vulnerability prioritization, written
up as a manuscript with a reproducible end-to-end artefact chain.
