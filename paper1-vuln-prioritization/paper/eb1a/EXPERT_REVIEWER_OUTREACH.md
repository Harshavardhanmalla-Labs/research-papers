# Expert Reviewer Outreach (draft message)

> Purpose: request honest technical feedback. This is **not** a request for an
> endorsement, a recommendation letter, a citation, or any statement the reviewer
> does not independently hold. Personalize before sending.

---

**Subject:** Request for technical feedback — reproducible vulnerability-prioritization benchmark

Dear Dr. [Name],

I'm an independent researcher working on reproducible methodology for vulnerability
prioritization, and I'd value your technical perspective if you have the time.

I've built an open **benchmark and framework** that ranks vulnerability-host pairs
and simulates remediation scheduling under operational capacity constraints
(blackout windows, approval gates, KEV-style deadlines), with an append-only,
hash-chained audit record of every decision. To avoid sensitive data, evaluation
runs on a deterministic, **public-sector-shaped synthetic fleet**, and the results
come from a frozen, integrity-verified 30-seed artifact with a freeze/verify
protocol.

I want to be upfront about the findings: this is a **neutral result**. Under the
current synthetic fixtures and uncalibrated weights, my context-aware model does
**not** outperform the EPSS baseline or a random ordering; the differences are
within seed-to-seed noise. I'm treating the contribution as the reproducible
evaluation infrastructure and an honest baseline, not a superiority claim.

If you're willing, I'd appreciate candid technical feedback on any of: the
pair-level evaluation design, the metric definitions (including the simulated
expected-exploited-host-days measure and the oracle's behavior under capacity), the
no-future-leakage and freeze/verify methodology, or the synthetic-fleet
assumptions. Critical feedback is especially welcome — including reasons the
approach may not generalize.

I'm happy to share the manuscript draft, the code, and the frozen artifact. Thank
you for considering this; I understand if your schedule doesn't allow it.

With appreciation,
Harshavardhan Malla
Independent Researcher
[contact]
