# Paper 18: Pre-Registration and Research Protocol

**Title:** The Drill Illusion: Latent Failover-Defect Decay and the Recovery-Confidence Gain of
Continuous Chaos Testing in Hybrid Government Infrastructure
**Short title:** Drill Illusion
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management / government practitioner track
**Pre-registration date:** 2026-06-20
**Date locked:** 2026-06-20, before any result on the evaluation seeds (1200 to 1224) was inspected.

---

## 1. Motivation

Federal contingency planning [NIST SP 800-34] requires agencies to maintain the ability to fail
over and recover their information systems after a disruption. The traditional assurance is a
periodic disaster-recovery drill: once a year, the team exercises the failover, confirms it works,
and records success. The problem is that a failover configuration silently rots between drills. A
replication link breaks, a failover script's dependency changes, a credential expires, a routing
rule is altered. Each such latent defect sits undetected until the next drill, so the probability
that the failover would actually work, if a real disaster struck at a random moment, decays between
drills even though the last drill passed.

Chaos engineering [Basiri et al. 2016; Beyer et al. 2016] offers an alternative: continuously and
automatically inject the failure modes and validate that failover still works, catching latent
defects within days rather than at the annual drill. This paper quantifies the recovery-confidence
gain of continuous chaos testing over periodic drills, the ceiling that chaos-suite coverage places
on it, the diminishing returns of higher chaos frequency, and the central illusion: that a passing
annual drill overstates the true recovery probability at a random disaster time.

---

## 2. Hypotheses

**H1 (Primary).** Continuous chaos testing at the reference cadence and coverage raises the recovery
success probability at a random disaster time over annual-drill-only assurance by at least 0.10,
across 25 evaluation seeds, with a BCa interval excluding zero.

**H2 (Coverage ceiling).** The recovery-confidence gain is bounded by the chaos suite's failure-mode
coverage; failure modes the chaos suite does not exercise remain on the annual cadence and form a
floor. The realized gain does not exceed the gain that perfect freshness on covered modes would
provide.

**H3 (Diminishing returns).** The gain saturates as the chaos cadence tightens relative to the
latent-defect arrival rate. Once chaos runs frequently enough that covered modes are almost always
fresh, further increases in frequency add little recovery confidence.

**H4 (The drill illusion).** The recovery success probability measured at drill time, immediately
after a validation, overstates the recovery success probability at a random disaster time, and the
overstatement grows with the validation interval. Under annual drills the at-drill figure is near
one while the at-random figure is materially lower; shortening the drill interval shrinks the
illusion.

**Rationale.** A latent defect on a mode validated every T days is present, in expectation, for a
time that grows with T, so the at-random recovery probability falls as T grows while the at-drill
probability stays near one (H4). Continuous chaos shortens T for covered modes, raising at-random
recovery (H1) up to the coverage ceiling (H2), with diminishing returns once covered modes are
almost always fresh (H3).

---

## 3. Model

A hybrid infrastructure with 12 failover modes (for example region failover, database failover,
network failover, dependency failover). Latent defects arrive on each mode as a Poisson process: 4
fragile modes at 3 defects per year and 8 robust modes at 0.3 per year. A validation of a mode
clears any latent defect on it. Two assurance regimes are compared. Under annual drills, every mode
is validated every 365 days. Under continuous chaos plus annual drills, the chaos-covered modes are
validated every chaos cadence (reference 7 days) while uncovered modes remain on the 365-day drill.

Chaos-suite coverage is the fraction of failover modes the chaos suite exercises (reference 0.70,
swept over 0.3, 0.5, 0.7, 0.9). The chaos cadence is swept over 1, 7, 30, and 90 days. Over a
multi-year horizon, each mode's healthy and defective intervals are simulated from its defect
arrivals and validation schedule. A disaster strikes a mode uniformly at random; failover succeeds
if that mode is healthy at the disaster time. No employer, operational, or recovery-test data is
used; all quantities are synthetic with documented parameters.

---

## 4. Metrics

Recovery success at a random disaster time is the weighted fraction of failover modes healthy,
averaged over random disaster times. Recovery success at drill time is the same quantity evaluated
immediately after a scheduled validation. The recovery-confidence gain is the difference in
at-random recovery between regimes. The drill illusion is the difference between the at-drill and
at-random recovery for a regime. Mean with 95 percent BCa bootstrap interval (10,000 resamples)
over 25 seeds; interval non-overlap is the evidentiary standard; no significance testing.

---

## 5. Failure Criteria

If continuous chaos does not raise at-random recovery by at least 0.05 over annual drills at the
reference cadence and coverage, declare H1 null. If the realized gain exceeds the perfect-freshness
coverage ceiling, H2 is rejected. If the at-drill recovery does not exceed the at-random recovery
under annual drills, H4 is rejected. Do not re-tune the defect rates, coverage, or cadence to reach
any threshold.

---

## 6. Reproducibility

A self-contained code and frozen-result artifact accompanies this paper in its own public
repository. All randomness is seeded; the run manifest records seeds, the defect-rate mixture, the
coverage and cadence sweeps, and the horizon.

---

## 7. Threats and Limitations

The failover modes, defect rates, coverage, and cadence are synthetic with documented parameters,
so absolute recovery probabilities are not field measurements; the comparative gain, the coverage
ceiling, the diminishing returns, and the drill illusion are the contribution. Real defects may be
correlated across modes or bursty rather than Poisson, and a real chaos experiment carries its own
operational risk that this model does not charge; the structural findings follow from the
defect-decay accounting and are more robust than the magnitudes.

---

## 8. Pre-Registration Attestation

Locked 2026-06-20 before any result on the evaluation seeds 1200 to 1224 was inspected. The model
constants are fixed; no parameter is tuned on any seed. No real recovery-test data is used.
