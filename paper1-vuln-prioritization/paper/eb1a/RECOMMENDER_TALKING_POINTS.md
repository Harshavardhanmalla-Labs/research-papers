# Recommender Talking Points

> For a recommender to adapt **only to the extent it reflects their own, direct
> knowledge.** Do not state or imply that the recommender observed any private,
> production, or government deployment unless they personally did — no such
> deployment exists or is claimed here. Remove any point you cannot personally
> attest to.

## Technical maturity

- Designed and implemented an end-to-end research framework spanning feed
  normalization, synthetic data generation, feature engineering, ranking, a
  multi-phase scheduler, audit logging, evaluation, statistics, and reporting.
- Engineered for determinism and integrity: SHA-256-based seeding, an automated
  test suite, and configuration-driven runs.

## Reproducibility discipline

- Built a content-addressed freeze-and-verify protocol so every reported number is
  traceable to an integrity-checked, immutable artifact.
- Generated all tables and figures programmatically from the frozen result — no
  hand-entered numbers.

## No-overclaiming integrity

- Reported a **neutral** empirical result honestly: the proposed model did not beat
  the EPSS baseline or a random ordering under the tested conditions.
- Maintained explicit claim-safety and citation audits; declined to overstate
  significance, deployment, or compliance.

## Relevance to cyber hygiene

- Addresses a core cyber-hygiene problem: choosing which fixes to apply first when
  capacity is limited, with reviewable justification for each choice.

## Ability to build complex research artifacts

- Delivered a large, well-tested software artifact and a complete manuscript with
  disciplined, phased engineering and verifiable outputs.

## Relationship to public-sector security operations

- Modeled public-sector-shaped operational constraints (capacity, blackout windows,
  approval gates, KEV deadlines) in a synthetic, non-sensitive setting — relevant to
  how such teams reason about prioritization, without using or claiming any real
  environment.
