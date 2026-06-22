# Paper 19: Pre-Registration and Research Protocol

**Title:** The Two-Sided Cost of CMDB Error: Ghost Assets, Phantom Assets, and the
Matching-Precision Ceiling of Self-Healing Reconciliation
**Short title:** Self-Healing CMDB
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management / government practitioner track
**Pre-registration date:** 2026-06-20
**Date locked:** 2026-06-20, before any result on the evaluation seeds (1300 to 1324) was inspected.

---

## 1. Motivation

A configuration management database (CMDB) is the asset inventory on which security and cost
management both depend (NIST SP 800-53 control CM-8; CISA BOD 23-01). A CMDB is never perfectly
accurate, because the real fleet churns: assets are provisioned and retired faster than the
inventory is reconciled. Its errors are two-sided and have opposite remedies. A ghost asset is a
real asset missing from the CMDB; it is a security problem, because an asset the inventory does not
know about is not patched, monitored, or protected. A phantom asset is a CMDB record with no
corresponding real asset; it is a cost and noise problem, because the organization pays for licenses
and agents on assets that no longer exist and chases alerts that mean nothing.

The two remedies conflict. Aggressively retiring records that have not been seen recently removes
phantoms but risks deleting real-but-quiet assets, creating ghosts. Aggressively adding every
discovered asset removes ghosts but, when the matching that links a discovered asset to its existing
record is imperfect, creates duplicate records, which are phantoms. Self-healing reconciliation,
continuous discovery with confidence-based matching, promises to reduce both, but its accuracy is
bounded by the precision of that matching. This paper quantifies the reduction self-healing
reconciliation achieves, the ghost-phantom tradeoff that retirement aggressiveness controls, the
floor that matching precision places on accuracy, and how the optimal operating point depends on the
relative cost of a ghost versus a phantom.

---

## 2. Hypotheses

**H1 (Primary).** Continuous self-healing reconciliation reduces total CMDB error (ghost rate plus
phantom rate) relative to quarterly periodic reconciliation by at least 30 percent, at the reference
retirement threshold and matching precision, across 25 evaluation seeds, with a BCa interval
excluding zero.

**H2 (Ghost-phantom tradeoff).** Retirement aggressiveness trades ghosts for phantoms. As the
retirement threshold shortens, the phantom rate falls and the ghost rate rises; the two move in
opposite directions across the sweep, so total error is minimized at an interior threshold rather
than at either extreme.

**H3 (Matching-precision ceiling).** The minimum achievable total error is bounded below by a floor
proportional to the matching-failure rate. Duplicate records created by failed matches cannot be
removed by any cadence or retirement threshold; as matching precision rises, the floor falls
proportionally.

**H4 (Cost-weighted optimum).** The optimal retirement threshold depends on the relative cost of a
ghost (security) and a phantom (cost). Weighting ghosts more heavily shifts the cost-minimizing
threshold toward more lenient retirement, accepting more phantoms to avoid deleting real assets;
weighting phantoms more heavily shifts it toward aggressive retirement.

**Rationale.** Ghost and phantom errors arise from opposite reconciliation actions, so no single
aggressiveness eliminates both (H2), and the duplicate records from imperfect matching set a floor
independent of cadence (H3). Continuous reconciliation shrinks the lag-driven components of both
errors (H1), and the best operating point depends on which error the organization considers more
costly (H4).

---

## 3. Model

A fleet whose assets have a mean lifetime of 365 days; an asset's lifetime is exponential, and
arrivals keep the live population in steady state. Reconciliation runs a discovery scan every
reconciliation cadence (continuous self-healing at 1 day, periodic at 90 days); each scan observes a
live asset with observability probability 0.70. A CMDB record is created when an asset is first
observed and is retired when it has not been observed for the retirement threshold. At each
observation, the discovery matches the asset to its existing record with the matching precision
(reference 0.95); with the complementary probability the match fails and a duplicate record is
created that persists until it is itself retired.

Two errors are measured at steady state. The ghost rate is the fraction of the live fleet with no
active CMDB record (undiscovered new assets and wrongly-retired quiet assets). The phantom rate is
the number of CMDB records with no corresponding live asset (records of retired assets not yet
removed, and duplicate records), expressed as a fraction of the live fleet. Total error is the sum.
The retirement threshold is swept over 7, 14, 30, 60, and 120 days; the matching precision over 0.80,
0.90, 0.95, and 0.99. No employer, operational, or inventory data is used; all quantities are
synthetic with documented parameters.

---

## 4. Metrics

Ghost rate, phantom rate, and total error as defined above, estimated by per-asset Monte Carlo over
the fleet. The cost-weighted error is the ghost rate times a ghost weight plus the phantom rate
times a phantom weight. Mean with 95 percent BCa bootstrap interval (10,000 resamples) over 25
seeds; interval non-overlap is the evidentiary standard; no significance testing.

---

## 5. Failure Criteria

If continuous reconciliation does not reduce total error by at least 15 percent over quarterly
reconciliation at the reference settings, declare H1 null. If the ghost and phantom rates do not
move in opposite directions across the retirement-threshold sweep, H2 is rejected. If the minimum
total error does not fall as matching precision rises, H3 is rejected. Do not re-tune the lifetime,
observability, cadence, threshold, or precision to reach any threshold.

---

## 6. Reproducibility

A self-contained code and frozen-result artifact accompanies this paper in its own public
repository. All randomness is seeded; the run manifest records seeds, the lifetime, observability,
cadences, and the threshold and precision sweeps.

---

## 7. Threats and Limitations

The fleet dynamics, observability, and matching precision are synthetic with documented parameters,
so absolute ghost and phantom rates are not field measurements; the comparative reduction, the
ghost-phantom tradeoff, the matching-precision floor, and the cost-weighted optimum are the
contribution. Real asset churn may be bursty or correlated with asset type, and real matching is a
record-linkage problem whose precision depends on the attributes available [Fellegi and Sunter
1969]; the structural findings follow from the reconciliation accounting and are more robust than
the magnitudes. Ghost and phantom costs are different in kind and are reported separately, with the
cost-weighted view offered as a parameterized lens rather than a single score.

---

## 8. Pre-Registration Attestation

Locked 2026-06-20 before any result on the evaluation seeds 1300 to 1324 was inspected. The model
constants are fixed; no parameter is tuned on any seed. No real inventory data is used.
