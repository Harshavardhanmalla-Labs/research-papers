# Paper 2 — Field Significance Statement

This file explains why the methodology contribution of Paper 2 matters to
the vulnerability-prioritization research field, without claiming external
recognition, citations, take-up, peer-review status, or use outside this
repository.

## The problem the field has

Vulnerability prioritization is a sub-field of applied cybersecurity that
asks which software flaws should be addressed first. Many recent research
threads in this sub-field fit per-feature weights — combining CVSS, EPSS,
KEV, asset-context, and other signals — using whatever exploit-positive
labels happen to be available on public feeds. The implicit assumption is
that the positive-label density on public feeds is high enough for
defensible per-feature weight fitting.

That assumption is rarely measured, and when it is measured the answer is
sensitive to:

- which time origin the analyst picks (single `t0` vs. multiple);
- whether the label is leakage-safe (after `t0` only) or leak-prone
  (anywhere in history);
- which signal counts as a positive (KEV membership; ExploitDB; EPSS-above-a-
  threshold);
- which product catalog the analyst is scoring against.

When the answer is low, fitting per-feature weights produces brittle outputs
that look impressive on the fitted slice and degrade under any of the four
shifts above.

## Why a failure-aware methodology matters

A failure-aware methodology surfaces the label-density question *before* it
allows weight fitting. It either fits (when the data justifies it) or it
refuses to fit and records the reason. Two practical consequences follow:

1. **Negative results become first-class outputs.** A study that decides
   not to fit because the data is too sparse is a useful study; the
   community learns where the public-feed boundary actually lies for a
   given catalog and time window.
2. **Sensitivity work is honestly framed.** Once fitting is off the table,
   the fixed-prior sensitivity sweep is exactly what it is — a description
   of how outputs move under design knobs — and is not mis-presented as a
   ranking of strategies.

## Why this particular execution matters

The Paper 2 execution couples a failure-aware gate with a pre-registered,
machine-readable design (locked across nine fix documents before any data
was collected), a freeze invariant tying every metric row back to a prior
artefact's SHA-256 manifest, and a claim-audit harness that scans the
manuscript for overclaim patterns. The result is a single, reproducible
artefact chain that other researchers can follow when they want to ask the
same label-density question on a different catalog, a different time window,
or a different label definition.

The specific numerical findings on this dataset — 7 unique positive CVEs
across 18 monthly `t0` windows and 2,688 catalog-matched CVEs — are not the
contribution. The contribution is the *methodology that produces the
finding* and the *discipline that prevents it from being overclaimed*.

## What this section does not claim

- It does not claim that the field has recognized this contribution.
- It does not claim that the methodology has been taken up or used outside
  this repository.
- It does not claim that the manuscript has been peer-reviewed or
  accepted at any venue.
- It does not claim impact, citations, or downstream influence.
- It does not claim that any agency, standards body, or vendor has
  endorsed or evaluated the methodology.

The field-significance argument here is structural, not reputational: a
failure-aware gate is a useful primitive *because the field needs negative-
result discipline under sparse public-feed labels*, regardless of whether
this particular execution is later recognized externally.
