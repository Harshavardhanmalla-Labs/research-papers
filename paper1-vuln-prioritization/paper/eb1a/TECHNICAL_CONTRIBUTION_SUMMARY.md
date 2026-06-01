# Technical Contribution Summary

This work contributes a reproducible, audit-evidence-producing **benchmark and
framework** for context-aware vulnerability prioritization under operational
capacity constraints. The technical contribution is the evaluation infrastructure
and methodology, not a claim of superior predictive performance.

## Vulnerability-host pair prioritization

Severity (CVSS) and exploitation-likelihood (EPSS) scores are defined at the CVE
level, but remediation happens on a specific host. The framework therefore treats
the **vulnerability-host pair** `(v, h)` as the unit of decision and explanation:
the same CVE on a domain controller and on a kiosk are distinct decisions with
distinct exposure and criticality. Each pair carries a seven-feature vector —
EPSS, KEV status, CVSS severity, telemetry-derived asset criticality, per-pair
local exposure, an urgency term derived from KEV deadlines, and remediation
complexity — and a linear scoring function ranks pairs, with a family of
strategies (baselines, ablations, and an evaluation-only oracle) for comparison.

## Capacity-constrained scheduling

Prioritization is only actionable under limits. A five-phase scheduler consumes a
ranking and fills a maintenance window subject to a fixed per-window capacity,
blackout windows, an approval policy, and documented risk acceptance. This is a
scheduling *simulation* that models approval and timing; it does not execute or
guarantee patches. Evaluating ranking jointly with scheduling exposes effects that
ranking-only studies miss — for example, when capacity, not the ranking policy,
dominates an operational outcome.

## Synthetic public-sector-shaped fleet

Because real agency telemetry is sensitive and rarely shareable, the framework
generates a deterministic synthetic fleet from documented parameter distributions:
host roles, OS/software inventory, identity tiering (including an identity-privilege
exposure component), network zones, data-sensitivity proxies, patch state, and
configurable telemetry staleness/missingness. This enables open, repeatable
evaluation without exposing any real data, while bounding external-validity claims.

## EPSS / CVSS / KEV comparison

The framework compares thirteen strategies, including CVSS-only, EPSS-only,
KEV-first, several combined and CVE-aggregated heuristics, the proposed
context-aware linear model and its ablations, and an oracle. EPSS is the primary
baseline. Exploit-intelligence inputs are consumed as features and baselines under
strict no-future-leakage (date-parameterized as-of queries and a temporal
train/gap/test split), not re-derived.

## Audit hash-chain decision records

Every score and scheduling decision is written to an append-only, SHA-256
hash-chained audit log, making the decision trail tamper-evident and independently
verifiable. This supports after-the-fact review; it is evidence-producing, not a
compliance determination.

## Frozen 30-seed artifact and reproducibility

The reported results come from a single frozen artifact: 30 seeds across 13
strategies, 4,290 per-seed metric rows, and 390 audit logs that all verify. The
output passes strict structural inspection (no duplicate rankings, contiguous
ranks, schedules within capacity, no infinite or undocumented-missing values) and
is sealed with a content-addressed freeze manifest of per-file SHA-256 hashes;
tables and figures are generated only from the freeze-verified artifact.
Determinism comes from SHA-256-based sub-seed derivation, and the reference
implementation ships with an automated test suite, configurations, and Make
targets.

## Neutral empirical findings

Under the current synthetic fixtures and uncalibrated (placeholder) weights, the
strategies are statistically indistinguishable on the primary operational metric
(simulated expected exploited-host-days): the proposed context-aware model neither
beats the EPSS baseline nor a random ordering, with all inter-strategy differences
inside seed-to-seed variation. This neutral result is reported plainly. It is
scientifically useful — it establishes a falsification condition and a clean
baseline — and it motivates the calibrated, larger-scale, and externally validated
studies that the framework is built to support.
