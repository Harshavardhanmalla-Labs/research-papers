# EB1A Evidence Summary — Paper 1

> This document is supporting material *about* the research artifact. It is not
> part of the academic manuscript and contains no language inserted into the paper.
> All statements are factual as of this writing; nothing here asserts publication,
> peer review, citation, deployment, compliance, or model superiority.

- **Title:** Context-Aware Vulnerability Prioritization for Government Endpoint
  Fleets: Integrating Exploit Intelligence, Asset Criticality, and Endpoint
  Telemetry.
- **Author:** Harshavardhan Malla, Independent Researcher.
- **Research area:** cybersecurity / vulnerability management; reproducible
  security-research methodology; security operations under resource constraints.

## Problem addressed

Organizations — especially public-sector-style endpoint environments — disclose
more vulnerabilities than they can remediate within limited maintenance capacity,
and prioritization decisions are often made without traceable, reviewable evidence.
The work asks whether a reproducible, auditable benchmark can be built to compare
prioritization strategies under realistic operational constraints, and whether
adding asset context to exploit-intelligence signals helps — treated as an open
question, not an assumed result.

## What was built

A complete, open research artifact: a Python framework that normalizes
exploit-intelligence inputs (EPSS, CISA KEV, public proof-of-concept signals) and
CVSS severity, generates a deterministic public-sector-shaped synthetic fleet,
constructs vulnerability-host pairs, scores and ranks them, schedules remediation
under a fixed per-window capacity with blackout windows and approval gates (a
scheduling *simulation*), and records every decision in an append-only,
hash-chained audit log. An evaluation and reporting layer computes operational and
ranking metrics and renders tables and figures from a frozen, integrity-verified
result.

## Artifact summary

- 30-seed frozen primary artifact across 13 prioritization strategies;
  4,290 per-seed metric rows; 390 hash-chain-valid audit logs; 0 missing and 0
  non-finite values; scheduling within the configured capacity (100); strict
  structural inspection passed with zero issues; content-addressed freeze manifest
  verified.
- Reference implementation with an automated test suite (currently 743 passing
  tests), configuration files, Make targets, and a freeze/verify integrity
  protocol.
- Generated tables (7) and figures (5), an index, and a reproducibility appendix.

## Manuscript status

A complete manuscript (Abstract + 17 sections) exists in clean submission-style
Markdown and as an ACM `acmart` LaTeX scaffold. **It has not been submitted,
accepted, peer-reviewed, or published.** Citation placeholders are still being
verified.

## Why it matters

It contributes reproducible, audit-evidence-producing evaluation infrastructure for
a problem of real operational importance, and it models scientific integrity by
reporting a neutral result rather than tuning toward a positive one.

## What it does NOT claim

It does not claim deployment in any real government or production system; does not
claim the proposed scoring model outperformed EPSS or a random baseline (it did
not, under the current synthetic fixtures and uncalibrated weights); does not claim
compliance was achieved; and does not claim acceptance, publication, or citation.

## Evidence files available

`paper/manuscript/` (drafts, citation/claim audits, checklist, reproducibility
appendix), `paper/acm/` (LaTeX scaffold), `paper/tables/` and `paper/figures/`
(generated artifacts), `results/primary_full_v1/` (frozen artifact + freeze
manifest), `paper/closeout/` (closeout package), and the `paper1` source repository
with its test suite.
