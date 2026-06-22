# Paper 13: Pre-Registration and Research Protocol

**Title:** Policy-as-Code for CJIS Compliance: Prevention versus Detection for Recurring Control
Violations on Law-Enforcement Endpoint Fleets
**Short title:** CJIS Policy-as-Code
**Author:** Harshavardhan Malla
**Target venue:** IEEE Transactions on Network and Service Management / government practitioner track
**Pre-registration date:** 2026-06-20
**Date locked:** 2026-06-20, before any result on the evaluation seeds (900 to 924) was inspected.

---

## 1. Motivation

Endpoints that handle Criminal Justice Information are bound by the FBI CJIS Security Policy, which
mandates controls such as advanced authentication, session lock, full-disk encryption, audit
logging, and password complexity. These controls drift out of compliance when a configuration is
changed: an administrator disables a setting, a software update reverts a policy, a script loosens
a permission. The standard automated response is detective: continuously detect the violation and
auto-remediate it. A stronger posture is preventive policy-as-code (for example, Open Policy Agent
guardrails), in which a non-compliant change is blocked at the moment it is attempted, so the
violation never takes effect.

The question this paper answers is when prevention is worth it. Prevention removes the exposure
window entirely for the violations it can block, and it blocks every recurrence of the same
misconfiguration rather than paying a detection-and-remediation cost each time. But prevention has
two limits: it can only block violations that arrive as an interceptable configuration change, not
emergent violations such as an expiring certificate, and it imposes a false-block cost when a
benign change is wrongly rejected. This paper quantifies the exposure reduction prevention
achieves, the ceiling that blockability places on it, how the advantage scales with violation
recurrence, and the false-block cost.

---

## 2. Hypotheses

**H1 (Primary).** Preventive policy-as-code reduces Criminal Justice Information exposure
(control-days out of compliance) relative to detective auto-remediation by at least 50 percent, at
the reference recurrence rate, across 25 evaluation seeds, with a BCa interval excluding zero.

**H2 (Blockability ceiling).** The fractional exposure reduction is bounded above by the share of
exposure attributable to blockable violations; emergent violations form a floor. The realized
reduction does not exceed the blockable-exposure share by more than 0.03.

**H3 (Recurrence amplification).** The absolute exposure that prevention eliminates grows
monotonically with the violation recurrence rate. The more a misconfiguration recurs, the more
prevention saves over detection, which pays a detection-and-remediation window on every
recurrence.

**H4 (False-block cost is recurrence-independent).** The false-block cost of prevention (benign
changes wrongly blocked) is driven by benign change volume and the guardrail false-positive rate,
not by recurrence. It is therefore approximately constant across the recurrence sweep, while the
security benefit grows with recurrence; the benefit-to-cost ratio of prevention increases with
recurrence. We report false blocks per endpoint-month and confirm they do not trend with
recurrence.

**Rationale.** Detection pays an exposure window on each violation occurrence; prevention pays
nothing for blockable violations and blocks every recurrence at the door. The fractional reduction
is therefore bounded by the blockable share (H2), the absolute saving grows with recurrence (H3),
and the operational cost is set by benign change volume independent of recurrence (H4), so
high-recurrence environments most favor prevention.

---

## 3. Model

A law-enforcement fleet of 500 CJI-handling endpoints per seed over a 365-day horizon. Two
processes generate control violations:

- **Blockable violations** arrive as configuration changes. A fraction of configuration changes
  are violating; the rest are benign. A violating change is interceptable by a policy-as-code
  guardrail at change time. Each violating root cause recurs as a Poisson process at the
  recurrence rate (swept).
- **Emergent violations** are not change-driven (for example, certificate expiry or a time-based
  session-policy lapse) and arrive at a fixed lower rate; a guardrail cannot block them.

Detection cadence is 1 day and remediation takes 1 day, so each detected violation is
non-compliant for about 2 days. Benign configuration changes arrive at a high rate; a guardrail
with false-positive rate 0.02 wrongly blocks that fraction of benign changes.

Two regimes are compared. **Detective:** every violation, blockable or emergent, is detected within
the cadence and auto-remediated, and recurs. **Preventive:** blockable violations are blocked at
change time (zero exposure, every recurrence blocked); emergent violations are still detected and
remediated as in the detective regime; benign changes are blocked at the false-positive rate.

The recurrence rate is swept over {0, 1, 3, 6, 12} per year, with 6 as the reference. No employer,
operational, or CJIS audit data is used; all events are synthetic with documented rates.

---

## 4. Metrics

CJI exposure is total control-days out of compliance over the horizon. Exposure reduction is the
fractional decrease from detective to preventive. The blockable-exposure share is the fraction of
detective exposure attributable to blockable violations (the H2 ceiling). False blocks per
endpoint-month is the count of benign changes wrongly blocked, normalized. Mean with 95 percent
BCa bootstrap interval (10,000 resamples) over 25 seeds; interval non-overlap is the evidentiary
standard; no significance testing.

---

## 5. Failure Criteria

If prevention does not reduce exposure by at least 25 percent at the reference recurrence rate,
declare H1 null. If the realized reduction exceeds the blockable-exposure share by more than 0.03,
H2 is rejected. If false blocks per endpoint-month show a clear monotone trend with recurrence,
H4 is rejected. Do not re-tune the violation, recurrence, or false-positive rates to reach any
threshold.

---

## 6. Reproducibility

A self-contained code and frozen-result artifact accompanies this paper in its own public
repository. All randomness is seeded; the run manifest records seeds, event rates, the recurrence
sweep, and the false-positive rate.

---

## 7. Threats and Limitations

The fleet and its event rates are synthetic with documented priors, so absolute exposure and
false-block values are not field measurements; the comparative reduction, the ceiling, the
recurrence scaling, and the recurrence-independence of false blocks are the contribution. Real
violations may be correlated or bursty rather than Poisson, and real guardrail precision depends
on the rule set; the structural findings are more robust than the magnitudes. Security exposure and
operational false blocks are different units and are reported separately rather than netted into a
single score.

---

## 8. Pre-Registration Attestation

Locked 2026-06-20 before any result on the evaluation seeds 900 to 924 was inspected. The model
constants are fixed; no parameter is tuned on any seed. No real CJIS or operational data is used.
