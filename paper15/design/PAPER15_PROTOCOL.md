# Paper 15: Pre-Registration and Research Protocol

**Title:** Fusing Real-Time and Scheduled Endpoint Telemetry for Vulnerability Visibility:
Coverage Gains, the Freshness Mechanism, and the Blind-Spot Floor
**Short title:** Endpoint Telemetry Fusion
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management / government practitioner track
**Pre-registration date:** 2026-06-20
**Date locked:** 2026-06-20, before any result on the evaluation seeds (1000 to 1024) was inspected.

---

## 1. Motivation

State agency cyber-operations teams rarely have a single source of truth for endpoint state. They
typically run two endpoint-management tools with different strengths: a real-time agent (such as
Tanium) that reports fresh state for the assets it covers, and a scheduled management platform
(such as Microsoft SCCM) that covers a different, overlapping set of assets but reports on a scan
cadence and is often stale. Building a real-time vulnerability heatmap of the fleet means fusing
these two partial, differently-fresh feeds.

Fusion is intuitively better, but the magnitude and its limits are not obvious. Each tool covers
only part of the fleet, the two coverage sets overlap to a degree that varies by agency, and the
scheduled feed is stale a fraction of the time. This paper quantifies how much fusing the two feeds
improves current-vulnerability visibility over the better single tool, identifies the mechanism
(coverage breadth from the scheduled feed plus freshness from the real-time feed), and measures the
floor that assets covered by neither tool place on visibility.

---

## 2. Hypotheses

**H1 (Primary).** At the reference coverage overlap, fusing the two feeds detects current
vulnerabilities at a recall at least 0.10 higher than the better single tool, across 25 evaluation
seeds, with a BCa interval excluding zero.

**H2 (Blind-spot floor).** Assets covered by neither tool form a hard floor on missed
vulnerabilities: the fusion miss rate is at least the blind-spot rate, and no freshness improvement
can reduce it below that floor. The residual miss above the floor is attributable to stale
coverage from the scheduled feed alone.

**H3 (Freshness mechanism).** Fusion's recall gain over the real-time feed alone equals the
fresh coverage that only the scheduled feed provides (assets the real-time feed does not cover but
the scheduled feed reports fresh). The real-time feed already supplies full freshness on its own
coverage, so fusion adds exactly the scheduled-only fresh assets.

**H4 (Overlap dependence).** Fusion's recall gain over the better single tool decreases as the
coverage overlap between the two tools increases. Complementary tools (low overlap) gain the most
from fusion; redundant tools (high overlap) gain the least, and high overlap also enlarges the
blind spot.

**Rationale.** The real-time feed contributes freshness, the scheduled feed contributes additional
coverage, and fusion takes the freshest signal per asset. The gain is therefore the
scheduled-only fresh coverage (H3), it shrinks as the tools overlap and become redundant (H4), and
it is bounded by the assets neither tool covers (H2).

---

## 3. Model

A fleet of 5{,}000 assets per seed. Each asset is assigned to a coverage class, both tools,
real-time only, scheduled only, or neither, from fixed marginal coverages (real-time 0.75,
scheduled 0.70) and a both-tools probability that sets the overlap (swept over 0.45, 0.50, 0.55,
0.60, 0.70, with 0.50 as the reference). The blind-spot rate (neither tool) follows as one minus
the coverage union.

Each asset has a true current vulnerability with prevalence 0.30 (this only sizes the sample; recall
is computed over current-vulnerability assets). The real-time feed reports fresh state wherever it
covers. The scheduled feed reports fresh state with probability 0.60 where it covers (40 percent
stale, reflecting a scan cadence slower than the vulnerability change rate). A current vulnerability
is detected by a feed if the feed covers the asset and its report is fresh.

Three regimes are compared: real-time only, scheduled only, and fusion (freshest-wins union: a
vulnerability is detected if the real-time feed covers the asset, or the scheduled feed covers it
and is fresh). No employer, operational, or telemetry data is used; all assignments are synthetic
with documented probabilities.

---

## 4. Metrics

Detection recall is the fraction of current-vulnerability assets a regime detects. Coverage union
is the fraction of assets covered by at least one tool. Blind-spot rate is one minus coverage
union. Mean with 95 percent BCa bootstrap interval (10,000 resamples) over 25 seeds; interval
non-overlap is the evidentiary standard; no significance testing.

---

## 5. Failure Criteria

If fusion does not exceed the better single tool by at least 0.05 recall at the reference overlap,
declare H1 null. If the fusion miss rate falls below the blind-spot rate, H2 is rejected (which
would indicate a model error, since blind-spot assets cannot be detected). If fusion's gain over
the better single tool does not decrease across the overlap sweep, H4 is rejected. Do not re-tune
the coverage, overlap, or freshness probabilities to reach any threshold.

---

## 6. Reproducibility

A self-contained code and frozen-result artifact accompanies this paper in its own public
repository. All randomness is seeded; the run manifest records seeds, coverage and freshness
probabilities, and the overlap sweep.

---

## 7. Threats and Limitations

The fleet and its coverage, overlap, and freshness probabilities are synthetic with documented
priors, so absolute recall values are not field measurements; the comparative gain, the freshness
mechanism, the blind-spot floor, and the overlap dependence are the contribution. Real coverage may
be correlated with asset type, and real staleness depends on scan cadence and vulnerability
dynamics; the structural findings are more robust than the magnitudes. The model treats detection
as a coverage-and-freshness event and does not model false positives in either feed.

---

## 8. Pre-Registration Attestation

Locked 2026-06-20 before any result on the evaluation seeds 1000 to 1024 was inspected. The model
constants are fixed; no parameter is tuned on any seed. No real telemetry data is used.
