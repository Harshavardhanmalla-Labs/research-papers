# Original Contribution Statement

> The original contribution is **not** a claim of superior predictive performance;
> it is the construction of a reproducible, audit-evidence-producing benchmark
> framework that evaluates vulnerability-host pair prioritization under operational
> capacity constraints.

Under the current synthetic fixtures and uncalibrated weights, the proposed scoring
model did not outperform the EPSS baseline or a random ordering. The originality is
in the *evaluation infrastructure, methodology, and integrity*, which stand
independent of any single model's score.

## Original elements

1. **Pair-level decision unit.** Modeling and explaining prioritization at the
   vulnerability-host pair `(v, h)` level — not the CVE level — so the same
   vulnerability on different hosts is a different, separately justified decision.

2. **Audit-evidence layer.** An append-only, SHA-256 hash-chained record of every
   score and scheduling decision, making the decision trail tamper-evident and
   independently verifiable for after-the-fact review.

3. **Capacity-constrained scheduler.** A five-phase scheduling simulation
   (KEV-deadline handling, risk-acceptance reawakening, greedy fill under blackout
   and approval constraints, bundle expansion, summary) that evaluates ranking
   *jointly* with the operational limits that shape real outcomes.

4. **Freeze / inspection pipeline.** A strict structural inspector plus a
   content-addressed freeze-and-verify protocol, so every reported number is
   traceable to an integrity-checked, immutable result set.

5. **Open synthetic fleet generator.** A deterministic, documented generator of a
   public-sector-shaped fleet (roles, identity tiering, exposure, complexity,
   telemetry imperfections) that enables open, repeatable evaluation without
   sensitive real data.

6. **Neutral benchmark result, reported honestly.** A falsifiable finding that
   uncalibrated context-aware weights do not separate from EPSS under the tested
   conditions — a clean baseline and a falsification condition, rather than an
   overstated positive.

7. **Reproducibility package.** A reference implementation with an automated test
   suite, configurations, Make targets, generated tables/figures, and a frozen
   artifact that others can run, inspect, and extend.

Together these constitute an original methodological foundation for evaluating
vulnerability prioritization in resource-constrained, audit-sensitive environments.
