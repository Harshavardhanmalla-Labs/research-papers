# LinkedIn Post

---

I built a reproducible benchmark for one of security operations' most stubborn
questions: when you can't patch everything, which vulnerability — on which host —
should you fix first?

The framework integrates exploit-intelligence signals (EPSS, CISA KEV, public
proof-of-concept data) with CVSS severity, telemetry-derived asset criticality, and
per-host exposure. It ranks vulnerability-host *pairs*, then simulates scheduling
those fixes under real constraints — capacity limits, blackout windows, and
approval gates — and writes a tamper-evident, hash-chained record of every
decision. To avoid using any sensitive data, it runs on a deterministic,
public-sector-shaped synthetic fleet, with a 30-seed frozen artifact and a
freeze/verify protocol so every number is reproducible.

Here's the honest part: my context-aware model did **not** magically beat every
baseline. Under these controlled, uncalibrated tests it performed on par with
EPSS — and even with a random ordering — with differences inside the noise.

That's not a disappointment. That's the point. Serious cybersecurity research
should be falsifiable and reproducible, and it should report neutral results
plainly instead of tuning toward a press release. The contribution here is the
transparent benchmark and audit-evidence framework — a clean, extensible baseline
for the calibrated and externally validated studies that come next.

If you work in vulnerability management, security operations, or reproducible
security research, I'd welcome technical feedback.

#VulnerabilityManagement #SecurityOperations #ReproducibleResearch #Cybersecurity
