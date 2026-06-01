# Paper 2 — LinkedIn Post (Internal Draft)

**Status.** Internal draft for the author's personal channel. Do not post
until (a) attorney / mentor review and (b) any decisions about when to
disclose the manuscript publicly. The post makes no claim of acceptance,
publication, citation, or external use.

## Version A — short (≤ 600 chars)

I just wrapped a piece of methodology work I'm pretty proud of: a
*failure-aware* multi-time-origin calibration gate for vulnerability
prioritization. The short version: before fitting per-feature weights on
public exploit data, count the unique positive CVEs. On the dataset I
studied — 18 monthly time-origin windows, 2,688 catalog-matched CVEs — the
count was 7. Pre-registered stop rule fired. I did not fit. The paper is a
methodology paper and an honest negative result; manuscript draft and
reproducible artefact chain in the repo.

## Version B — slightly longer (≤ 1300 chars)

Quick note on a piece of methodology work I just finished.

Vulnerability prioritization papers often fit per-feature weights using
public exploit feeds (NVD, EPSS, KEV). The implicit assumption is that the
positive-label density on public feeds is high enough for that fitting to
mean something. I built a methodology that measures the density first and
refuses to fit if it's too low.

On a 31-product synthetic catalog, 18 monthly time-origin windows from
2023-09 to 2025-02, with a leakage-safe 30-day label horizon, I found 7
unique positive CVEs across 2,688 catalog-matched CVEs. The pre-registered
stop rule said: don't fit. So I didn't.

The remaining study is a 48-cell fixed-prior sensitivity sweep (1,440
seed-runs, 8,640 metric rows). Every metric row carries a freeze-witness
identifier tying it back to a prior frozen artefact, and the manuscript
has a claim-audit script that I run over it.

This is a methodology paper and a negative result. Manuscript draft + an
end-to-end reproducible artefact chain are in the repo. No venue
submission yet.

## Hashtags (use sparingly)

`#cybersecurity` `#vulnerabilitymanagement` `#methodology` `#opensource`
`#negativeresult`

## What this post does NOT say

- It does not say the paper has been peer-reviewed, accepted, or cited.
- It does not say any organization has taken up or used the methodology.
- It does not say any prioritization strategy beats EPSS or another
  comparator.
- It does not say the calibration step succeeded.
- It does not mention any agency, vendor, or standards body in an
  endorsement role.
- It does not claim the methodology is finished or ready-to-run.

## Pre-post checklist

- [ ] Manuscript visibility decision made (private repo vs. preprint)
- [ ] Attorney / mentor sign-off on this exact wording
- [ ] No client / employer NDA conflict
- [ ] No reference to any organization that has not been contacted
- [ ] Hashtags include nothing that implies external recognition
