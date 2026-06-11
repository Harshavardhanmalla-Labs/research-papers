# AutoHeal: A Pre-Registered Self-Healing Framework for Autonomous Vulnerability Remediation

**Authors:** Harshavardhan Malla, Independent Researcher
**Target venue:** IEEE Transactions on Network and Service Management (TNSM)
**Date:** June 2026
**Status:** Draft v0.1

---

## Abstract

Papers 4–9 of the VulnPrio research sequence developed components for hygiene-augmented vulnerability prioritization — a calibrated scorer, a deployable online recalibration recipe, a capacity-arrival operating regime characterisation, and a closed-loop signal-exhaustion theorem. None of these papers addresses the operational integration question: *can the components be assembled into an autonomous remediation framework with pre-registered safety bounds?*

This paper builds and evaluates that framework. **AutoHeal** is a six-stage closed-loop pipeline (detect, score, triage, plan, act, verify+rollback, learn) parameterised by Papers 4–9's findings and locked under pre-registered safety bounds. We evaluate it on a 2,700-row frozen sweep across K ∈ {50, 100, 200}, λ = 3, 12 windows, 25 evaluation seeds, against a human-in-loop baseline and a fixed-policy control, with CVE attributes drawn from the real EPSS/KEV public corpus from Paper 4 §12.

The pre-registration locked four hypotheses. **The mixed-outcome rejection pattern is the substantive finding.**

**H1 (Coverage) — supported.** AutoHeal eventually remediates 97.8% of high-EPSS pairs by Window 6 at both K = 50 and K = 100. The core purpose of autonomous remediation is achieved.

**H2 (Safety) — rejected.** The pre-registered safety bound (≤ 5% rollback rate per window) is violated at 300 of 900 post-W1 windows. The hard-stop fires 134 times across the sweep; cascading failures detected three times. The safety mechanism works as designed, but it fires more often than the pre-registered tolerance contemplated.

**H3 (MTTR Reduction) — not analysable.** An instrumentation issue produces degenerate MTTR estimates. We report the issue honestly per the pre-registration stop rule and qualify the abstract accordingly.

**H4 (Per-Pair Dominance over Human-in-Loop) — rejected.** AutoHeal beats Human-in-loop in only 2% of (cell, seed, window) triples. The mechanism is structural: at the pre-registered conservative triage threshold (0.80 score for AUTO classification), AutoHeal trades equality for safety-bounded automation rather than for throughput.

The deployable conclusion is honestly conditional: at the pre-registered conservative thresholds, AutoHeal achieves automation parity with human-in-loop, not throughput superiority. A future evaluation with a pre-registered less conservative triage threshold (or with a fixed instrumentation for MTTR) could change H3 and H4. The H1 success and the H2 safety-bound rejection are robust to those changes.

All results are bounded to the synthetic EEHDA evaluation context with real CVE attribute distributions. External validation on real fleet telemetry, with the framework's pre-registered safety bounds preserved, is the most consequential remaining direction.

**Keywords:** self-healing systems; autonomous remediation; vulnerability management; EPSS; HygienePrio; safety bounds; pre-registration; reproducibility.

---

The full submission manuscript is at `submission/ieee/main.tex` (compiles to 8 pages via tectonic).
The pre-registration protocol is at `design/PAPER10_PROTOCOL.md`.
Frozen results: `results/primary_v1/autoheal_results.csv` (2,700 rows).
