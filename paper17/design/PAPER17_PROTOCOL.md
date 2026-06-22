# Paper 17: Pre-Registration and Research Protocol

**Title:** Ring Rollout of Script-Based Endpoint Enforcement: Bounding the Blast Radius of a Faulty
Policy at a Quantified Convergence Cost
**Short title:** Ring Rollout Blast Radius
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management / government practitioner track
**Pre-registration date:** 2026-06-20
**Date locked:** 2026-06-20, before any result on the evaluation seeds (1100 to 1124) was inspected.

---

## 1. Motivation

Government endpoint teams enforce configuration compliance at scale with scripts: PowerShell,
Desired State Configuration, and management-platform scripts that run across thousands of
endpoints. Script-based enforcement is powerful, but a faulty enforcement script, one with a bug
that breaks or misconfigures the endpoints it touches, is dangerous precisely because it runs
everywhere. Deploying such a script to the whole fleet at once maximizes both convergence speed and
blast radius.

The standard mitigation, drawn from reliability engineering, is a staged or ring rollout: deploy to
a small canary ring first, observe for failures, and expand only if the canary is healthy. A faulty
script is then caught at the canary and contained. This safety comes at a cost: each stage adds a
soak delay, so a healthy enforcement campaign reaches the fleet more slowly. This paper quantifies
the tradeoff. It measures how much ring rollout reduces the expected blast radius of a faulty
script, the convergence cost it pays on every campaign, how the protection depends on the
probability that the canary actually detects a fault, and how finer ring staging shifts the
tradeoff.

---

## 2. Hypotheses

**H1 (Primary).** At the reference canary detection probability, a four-ring rollout reduces the
expected blast radius of a faulty enforcement script by at least 80 percent relative to a big-bang
rollout, across 25 evaluation seeds, with a BCa interval excluding zero.

**H2 (Convergence cost).** Ring rollout pays a fixed convergence cost on every campaign equal to
the soak time multiplied by the number of inter-ring stages, independent of whether the script is
faulty. The four-ring rollout's time to full deployment exceeds the big-bang's by exactly three
soak periods.

**H3 (Observability mechanism).** The blast-radius reduction scales with the canary detection
probability. As the probability that a fault is detected at a ring falls, the expected blast radius
of the ring rollout rises monotonically toward the big-bang value; a canary that rarely detects
faults provides little containment.

**H4 (Ring granularity).** Finer ring staging (more, smaller rings) further reduces the expected
blast radius but at a growing convergence cost. The marginal blast-radius reduction per added ring
diminishes while the convergence cost per added ring is constant, so there is an interior
sweet spot rather than unbounded benefit from more rings.

**Rationale.** A faulty script harms every endpoint it has reached when it is detected. Ring rollout
caps that reach at the cumulative ring size at detection, which is small when early rings are small
and detection is likely; the expected blast radius therefore falls sharply with detection
probability (H3) and with finer early rings (H4), while the soak cost grows linearly with the
number of stages (H2).

---

## 3. Model

A fleet of 10,000 endpoints. An enforcement script is faulty with probability 0.05. A rollout
configuration is a sequence of cumulative deployment fractions ending at 1.0; a big-bang rollout is
the single-stage sequence [1.0], and a ring rollout has several stages. After each non-final stage,
a fault present in the script is detected with the canary detection probability and the campaign is
halted; the blast radius is then the cumulative fraction of the fleet reached at the detection
stage, or the whole fleet if no stage detects the fault before full deployment.

The reference configuration is a four-ring rollout with cumulative fractions [0.01, 0.10, 0.50,
1.00] and a canary detection probability of 0.80. The detection probability is swept over {0.2, 0.5,
0.8, 0.95}, and ring granularity is swept over big-bang [1.00], two-ring [0.05, 1.00], four-ring
[0.01, 0.10, 0.50, 1.00], and six-ring [0.005, 0.02, 0.08, 0.25, 0.60, 1.00]. Each non-final stage
adds one soak period to the time to full deployment. The expected blast radius for a configuration
is estimated by Monte Carlo over faulty campaigns per seed. No employer, operational, or deployment
data is used; all quantities are synthetic with documented parameters.

---

## 4. Metrics

Expected blast radius is the mean fraction of the fleet harmed by a faulty campaign. Convergence
cost is the number of soak periods to reach full deployment, equal to the number of inter-ring
stages. Blast-radius reduction is one minus the ratio of the ring rollout's expected blast radius to
the big-bang's. Mean with 95 percent BCa bootstrap interval (10,000 resamples) over 25 seeds;
interval non-overlap is the evidentiary standard; no significance testing.

---

## 5. Failure Criteria

If the four-ring rollout does not reduce the expected blast radius by at least 50 percent at the
reference detection probability, declare H1 null. If the convergence cost is not exactly the number
of inter-ring stages, the model is in error and the run is halted. If the expected blast radius does
not rise as the detection probability falls, H3 is rejected. Do not re-tune the ring fractions,
fault rate, or detection probability to reach any threshold.

---

## 6. Reproducibility

A self-contained code and frozen-result artifact accompanies this paper in its own public
repository. All randomness is seeded; the run manifest records seeds, the fault rate, the ring
configurations, the detection-probability sweep, and the Monte Carlo trial count.

---

## 7. Threats and Limitations

The fault rate, ring fractions, and detection probability are synthetic with documented parameters,
so absolute blast-radius values are not field measurements; the comparative reduction, the
observability scaling, and the granularity tradeoff are the contribution. Real faults may be
detected with a delay rather than at a stage boundary, and real canary populations may not be
representative of the fleet; the structural findings follow from the rollout accounting and are more
robust than the magnitudes. Convergence cost is reported in soak periods rather than netted against
blast radius, since the two are different units that an operator must weigh.

---

## 8. Pre-Registration Attestation

Locked 2026-06-20 before any result on the evaluation seeds 1100 to 1124 was inspected. The model
constants are fixed; no parameter is tuned on any seed. No real deployment data is used.
