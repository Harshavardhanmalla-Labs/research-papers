# Field Significance Statement

This work targets a recurring, practical gap across several communities. The
statements below describe *why the problem and the approach matter*; they do not
assert adoption, citation, or measured real-world impact, none of which is claimed.

## Public-sector cybersecurity

Government-style endpoint environments operate under remediation deadlines (e.g.,
KEV-driven timelines) and documented-process expectations while facing more
disclosed vulnerabilities than capacity allows. A reproducible, public-sector-
shaped benchmark that ranks *and* schedules under those constraints — without using
sensitive data — gives this community a transparent way to study prioritization
trade-offs.

## Vulnerability management

The field has strong CVE-level signals (CVSS, EPSS, KEV) but fewer open, repeatable
tools that evaluate prioritization at the host level and under capacity limits. A
pair-level benchmark with an evaluation-only oracle and clearly defined baselines
offers a common yardstick for comparing strategies.

## Security operations

Operations teams live with blackout windows, change-advisory cadence, and approval
gates. By coupling ranking to a capacity-constrained scheduling simulation, the
framework surfaces effects — such as a binding capacity constraint dominating a
deadline-breach metric — that ranking-only evaluations cannot show.

## Compliance review

Audit-event and flaw-remediation expectations call for documented, reviewable
decisions. Tamper-evident, per-decision audit records illustrate how prioritization
tooling can *produce evidence that supports review*. (This supports review; it does
not establish compliance.)

## Reproducible cybersecurity research

Much security research is hard to reproduce because data and code are private.
This artifact contributes a fully deterministic, freeze-verified evaluation
pipeline and an honest, neutral baseline — modeling falsifiable practice. The
willingness to report that the proposed model did not beat its baselines is itself
a contribution to research integrity in a field prone to overclaiming.

## Summary

The significance is methodological and infrastructural: a transparent, extensible
foundation for evaluating vulnerability-host pair prioritization under realistic
constraints, accompanied by a candid neutral result that defines a baseline for
future calibrated and externally validated studies.
