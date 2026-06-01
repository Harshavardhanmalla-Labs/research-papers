# Plain-English Summary

Most organizations, including government-style technology environments, discover
far more security weaknesses than their teams can fix at once. Deciding which
weaknesses to fix first — and being able to show later why each decision was made —
is a hard, practical problem. This research studied that problem in a careful,
repeatable way.

The author built a complete software framework and a public benchmark to compare
different ways of ranking which "vulnerability on which computer" should be fixed
first, while respecting real limits such as how many fixes can be approved in one
maintenance window. The framework also keeps a tamper-evident record of every
decision, so the reasoning can be reviewed afterward. To avoid using any sensitive
real data, the study used a realistic but artificial ("synthetic") fleet of
computers shaped like a public-sector environment.

Importantly, the work is honest about its limits. It does not claim the software
was installed in any real government system, and it does not claim the author's new
scoring method beat the existing industry signals — in these controlled tests, the
methods performed about the same. Reporting that result openly, instead of
overstating it, is part of doing trustworthy research: serious cybersecurity work
should be testable and reproducible by others.

The contribution is a reusable, transparent foundation that other researchers and
practitioners can run, check, and build on. It demonstrates disciplined, original
research engineering applied to an important, practical security challenge.
