# Paper 12: Pre-Registration and Research Protocol

**Title:** NIST 800-53 as Code: Quantifying the Compliance-Exposure Reduction of Continuous
Automated Evidence Collection and Its Automatability Ceiling
**Short title:** Compliance as Code
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management / government practitioner track
**Pre-registration date:** 2026-06-20
**Date locked:** 2026-06-20, before any result on the evaluation seeds (800 to 824) was inspected.

---

## 1. Motivation

Federal systems must demonstrate that their security controls remain effective over time, not
only at an annual audit. Continuous monitoring guidance (NIST SP 800-137) and machine-readable
control formats (NIST OSCAL) make it possible to collect control evidence automatically and
continuously rather than through periodic manual assessment. The promise of compliance as code is
that a control which drifts out of compliance, a disabled audit log, an expired certificate, a
loosened firewall rule, is caught in days rather than at the next assessment.

The question this paper answers is quantitative: how much does continuous automated evidence
collection actually reduce compliance exposure relative to periodic assessment, and what bounds
that reduction. The bound matters because not every NIST 800-53 control is machine-checkable; a
policy-documentation control or a physical-security control still requires manual assessment.
Continuous monitoring can only act on the automatable subset, so the un-automatable remainder sets
a floor on the achievable reduction. We measure both the gain and the floor.

---

## 2. Hypotheses

**H1 (Primary).** On automatable controls, where continuous monitoring applies, continuous
automated evidence collection reduces the mean time to detect control drift by at least a factor
of 10 relative to annual (365-day) assessment, across 25 evaluation seeds, with a BCa interval
excluding a factor of 10. The overall reduction across all controls is reported descriptively and
is bounded by the automatable fraction (H2).

**H2 (Automatability ceiling).** The fractional reduction in compliance exposure (control-days out
of compliance) is bounded above by the share of baseline exposure attributable to automatable
controls. The realized exposure reduction does not exceed that automatable-exposure share by more
than 0.03. Even instantaneous detection of automatable controls cannot reduce exposure below the
non-automatable remainder.

**H3 (Diminishing returns versus cadence).** The absolute compliance exposure that continuous
monitoring eliminates (control-days saved) is smaller when the manual baseline is quarterly than
when it is annual: days saved over quarterly is less than days saved over annual. The tighter the
manual cadence, the fewer control-days continuous monitoring adds, even though the fractional
reduction stays near the automatable share.

**H4 (Drift concentration).** Restricting automation to the highest-drift quartile of controls
captures at least 70 percent of the exposure reduction achievable by automating all automatable
controls. The value of compliance as code is concentrated in the controls that drift most often.

**Rationale.** Compliance exposure for a control is the product of how often it drifts and how long
each drift goes undetected. Continuous detection collapses the undetected time for automatable
controls toward the collection cadence, but leaves the manual controls on the periodic cadence,
and leaves rarely-drifting controls contributing little exposure regardless. The gain is therefore
large but bounded by automatability (H2) and concentrated in high-drift controls (H4), and it
shrinks as the manual cadence tightens (H3).

---

## 3. Model

A control catalog of 200 control instances per seed. Each control has:

- **Drift hazard** lambda_i (drift events per year), drawn from a mixture: 30 percent
  high-drift technical controls (mean 6 per year: logging, certificates, configuration, access),
  70 percent low-drift controls (mean 0.5 per year: policy, documentation, physical).
- **Automatable** flag, true with probability that is higher for high-drift technical controls
  (0.85) than for low-drift controls (0.35), reflecting that technical controls are both more
  drift-prone and more machine-checkable. The overall automatable fraction is a model output,
  reported per seed.
- **Remediation time** of 7 days after detection (fixed).

Over a 730-day horizon, drift events for each control are a Poisson process at rate lambda_i. A
drift event makes the control non-compliant until it is detected and then remediated.

**Monitoring regimes.** (i) Periodic-T: every control is assessed every T days; a drift is detected
at the next assessment. (ii) Continuous: automatable controls are detected within a 1-day
collection cadence; non-automatable controls remain on the periodic cadence T. We evaluate
continuous against annual (T = 365) and quarterly (T = 90).

No employer, operational, or audit data is used; all control attributes are synthetic with
documented distributions.

---

## 4. Metrics

- **Mean time to detect (MTTD):** mean over drift events of the time from drift to detection.
- **Compliance exposure:** total control-days out of compliance over the horizon, per control-year.
- **Exposure reduction:** (exposure_periodic minus exposure_continuous) divided by
  exposure_periodic.
- **Automatable-exposure share:** fraction of baseline (periodic) exposure attributable to
  automatable controls (the H2 ceiling).

Mean with 95 percent BCa bootstrap interval (10,000 resamples) over 25 seeds; interval
non-overlap is the evidentiary standard; no significance testing.

---

## 5. Failure Criteria

If continuous monitoring does not reduce MTTD on automatable controls by at least a factor of 5
over annual assessment, declare H1 null. If the realized exposure reduction exceeds the automatable-exposure share by more
than 0.03, H2 is rejected and the ceiling is reported as not binding. Do not re-tune the drift or
automatability distributions to reach any threshold.

---

## 6. Reproducibility

A self-contained code and frozen-result artifact accompanies this paper in its own public
repository. All randomness is seeded; the run manifest records seeds, the drift and automatability
distributions, the horizon, and the cadences.

---

## 7. Threats and Limitations

The control catalog and its drift and automatability distributions are synthetic with documented
priors, so absolute exposure values are not field measurements; the comparative reductions and the
ceiling relationship are the contribution. Real control drift may be bursty or correlated rather
than Poisson, and real automatability depends on the available tooling; the structural findings
(an automatability ceiling, drift concentration, diminishing returns versus cadence) are more
robust than the magnitudes. A fixed remediation time is assumed; variable remediation would shift
absolute exposure but not the comparative structure.

---

## 8. Pre-Registration Attestation

Locked 2026-06-20 before any result on the evaluation seeds 800 to 824 was inspected. The model
constants are fixed; no parameter is tuned on any seed. No real compliance or audit data is used.
