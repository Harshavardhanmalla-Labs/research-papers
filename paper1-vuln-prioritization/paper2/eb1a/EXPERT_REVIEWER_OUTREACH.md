# Paper 2 — Expert Reviewer Outreach Template

This file is a *template* for asking a domain expert to read the Paper 2
manuscript informally, before any venue submission. It does not assert that
any expert has accepted, reviewed, or endorsed the work. Each outreach
message must be customised to the recipient and sent only after attorney /
mentor sign-off on the recipient list.

## Audience criteria

A useful expert reviewer for Paper 2 is someone whose own peer-reviewed
research is in one or more of the following areas:

- vulnerability scoring / prioritization research (CVSS / EPSS / KEV /
  SSVC / NIST LEV);
- empirical evaluation methodology in security;
- sparse-label statistical methodology in applied machine learning;
- multi-time-origin evaluation in cybersecurity datasets.

Avoid contacting people who would have an obvious conflict of interest with
the manuscript's positioning (e.g., direct co-authors of a method that
Paper 2 differentiates against). Avoid contacting reviewers who are likely
to be assigned by the eventual target venue, to preserve double-blind
integrity.

## Outreach message template (≤ 250 words)

> Subject: Informal methodology review request — failure-aware gate for
> sparse-label vulnerability prioritization
>
> Dear Dr. {LastName},
>
> I'm writing to ask, if your schedule allows, whether you would be open to
> reading a methodology draft I've prepared on vulnerability prioritization
> under sparse public-feed exploit labels.
>
> The paper is a methodology contribution and an honest negative result.
> It documents a failure-aware multi-time-origin calibration gate that
> measures unique-positive-CVE density across windows and refuses to fit
> per-feature weights when the density is below a pre-registered minimum.
> On my synthetic 31-product catalog across 18 monthly time-origin windows
> I observed 7 unique positive CVEs out of 2,688 catalog-matched CVEs; the
> gate fired and I did not fit. The remainder of the paper is a 48-cell
> fixed-prior sensitivity sweep with stop-rule-driven demotion.
>
> The manuscript is at draft stage and has not been submitted anywhere. I
> am specifically interested in feedback on the methodology, on the stop-
> rule design, and on the framing of the negative result, rather than on
> presentation polish. Estimated reading time: roughly 30–45 minutes.
>
> If you do not have bandwidth, no need to respond; I will not follow up.
> If you are open to it, I can share a private read-only link.
>
> Thank you for your time.
>
> Best regards,
> {AuthorName}

## What this message does NOT do

- It does not state or imply that the recipient has agreed to review.
- It does not state or imply that the paper has been accepted, peer-
  reviewed, or cited.
- It does not state or imply that any other expert has reviewed or
  endorsed the work.
- It does not ask for a written endorsement, a referee letter, or any
  artefact that the recipient may later be asked to repeat in a formal
  context. It asks for informal methodology feedback only.

## Logging discipline

If a recipient does respond and does provide feedback, the author should
record the response privately, not in this repository, and should not use
the recipient's name in any public-facing document without explicit
written permission. The default record is: *I asked N experts; M
declined or did not respond; K provided informal feedback under a
no-attribution understanding.*

The author may not represent informal feedback as peer review.
