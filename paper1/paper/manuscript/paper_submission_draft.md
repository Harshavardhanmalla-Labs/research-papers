# Auditable Autonomy: Tamper-Evident, Cryptographically Verifiable Decision Provenance for Autonomous Vulnerability Remediation in Regulated Fleets

**Harshavardhan Malla**, Independent Researcher

## Abstract

As vulnerability remediation in large regulated fleets becomes automated, the
security question shifts from *which vulnerability to patch first* to *whether
the record of what was decided, and why, can be trusted after the fact*.
Regulatory regimes (FISMA, FedRAMP, the FBI CJIS Security Policy) require audit
trails that survive a privileged insider, yet the append-only hash chains
commonly used for decision logging carry a structural blind spot: they certify
internal consistency, not completeness. We make this precise with an
adversarial evaluation of an automated remediation log under two adversaries
and eight tampering classes (200 trials each). A naive SHA-256 hash chain
detects point edits, reordering, interior deletion, and insertion against a
restricted adversary, but is *blind to tail truncation and wholesale
replacement* (detection rate 0.00 for both); against a realistic insider who
can recompute downstream hashes it detects *nothing* (0.00 across all eight
classes). We then present a verifiable provenance ledger that augments the
chain with per-window Merkle commitments and periodic Ed25519-signed
checkpoints anchored by an independently held latest checkpoint, in the style
of a Certificate Transparency signed tree head. The ledger detects all eight
attacks under both adversaries (detection rate 1.00) while adding 0.21% space
overhead and verifying a 50,000-record log in under one second; append
throughput remains 68,000 to 110,000 records per second. We map the
construction to NIST SP 800-53 audit controls (AU-9, AU-10) and release the
ledger, the adversarial harness, and the frozen results. The contribution is a
deployable accountability layer for autonomous security decisions whose
integrity guarantees are stated in advance and verified adversarially, not
asserted.

## 1. Introduction

Enterprise and government fleets increasingly delegate vulnerability
remediation to automated pipelines: a scorer ranks (host, CVE) pairs, a
capacity-constrained scheduler selects what to patch within finite windows and
mandatory regulatory deadlines, and an executor applies or defers each action.
Automation raises a question that ranking accuracy does not answer. When an
auditor, an inspector general, or opposing counsel later asks *why* a specific
exploited host was deferred, the answer is only as trustworthy as the log that
recorded the decision, the feature values it used, and the policy version in
force at the time. In regulated settings this is mandatory: FISMA, FedRAMP, and
the FBI CJIS Security Policy require audit records that remain attributable and
intact even against insiders with administrative access.

The common engineering answer is an append-only, hash-chained log: each record
carries the cryptographic hash of its predecessor, so editing any stored record
breaks the chain. This is necessary but not sufficient. A hash chain certifies
that the records *present* are mutually consistent; it says nothing about
records that are *absent*. An adversary who deletes the most recent k records
leaves a chain that still verifies. An insider who can run the logging code can
recompute every downstream hash and rewrite history into a different,
internally consistent narrative.

Binding operational directives impose hard remediation deadlines for
known-exploited vulnerabilities, and missing one is a reportable event. When
automation makes the deferral that leads to a breach, the resulting review is
adversarial: the operator has both the access and the incentive to make the log
support whatever account is least damaging. An audit trail that any
sufficiently privileged party can silently rewrite is not evidence; it is a
liability dressed as one.

**Contributions.**

- A precise, adversarial characterization of the hash-chain blind spot. Under a
  restricted adversary the naive chain misses tail truncation and wholesale
  replacement; under a realistic insider it provides *no* tamper-evidence at
  all.
- A verifiable provenance ledger that augments the chain with per-window Merkle
  commitments and periodic Ed25519-signed checkpoints, anchored by an
  independently held latest checkpoint as in Certificate Transparency. Its
  guarantees are stated in advance.
- A reproducible adversarial evaluation: eight tampering classes, two
  adversaries, 200 trials each, plus runtime and space overhead at fleet scale.
  The ledger detects every attack under both adversaries at 0.21% space overhead
  and sub-second verification.
- A mapping to NIST SP 800-53 audit controls and a discussion of what the
  construction does and does not guarantee.

## 2. Preliminaries

We use four standard primitives. **SHA-256** maps arbitrary input to a 256-bit
digest and is collision- and second-preimage-resistant. A **hash chain** links
each record to the digest of its predecessor, making the head a commitment to
the entire prefix; it proves internal consistency of the records present but
does not commit to how many records there should be. A **Merkle tree** yields a
single root committing to the exact set and order of leaves with O(log n)
membership proofs. **Ed25519 (EdDSA)** signatures let a private-key holder
produce commitments verifiable with the public key; binding a signature to a
Merkle root and a record count produces a commitment a log holder cannot later
repudiate or silently change, the mechanism transparency logs use to make
omission detectable.

## 3. Threat Model and Requirements

**System.** An automated remediation pipeline emits one decision record per
action (scoring, scheduling, approval, deferral, risk acceptance, outcome). Each
record carries the (host, CVE) pair, the maintenance window, the decision type,
the feature values used, the policy (weights) version, the threat-feed snapshot
versions, and the framework version. Records are written to an append-only log.

**Adversary.** The goal is post-hoc repudiation: to make the log tell a story
other than what happened, undetectably. Two capability levels:

- *Restricted (W):* can overwrite stored bytes but does not recompute chain
  hashes (partial/forensic tamper, append-only medium, no chain code).
- *Insider (S):* has log-write access and runs the logging code, so recomputes
  every downstream hash to restore internal consistency. This is the realistic
  regulated-fleet threat.

In both cases the adversary cannot forge a signature under a key it does not
hold, and cannot alter an independently retained checkpoint.

**Tampering classes (8):** field modification, reordering, interior deletion,
tail truncation, forged insertion, policy (weight) rollback, threat-feed
forgery, and wholesale replacement.

**Worked scenario.** A public-facing server with a known-exploited
vulnerability is deferred past its BOD 22-01 deadline because the scheduler
exhausted its patch capacity, then is compromised. During review the operator
has motive to (a) truncate the log so the deferral is the last surviving entry,
or (b) rewrite the deferred record's feature values or weights version. Under a
naive chain both edits can be made to verify. The reviewer cannot distinguish
the doctored log from the truth. This is what the ledger prevents.

**Requirements.** (R1) Any tampering class, under either adversary, must be
detectable by an independent verifier. (R2) Detection must not require trusting
the log holder. (R3) Overhead must suit fleet scale.

## 4. The Verifiable Provenance Ledger

Three layers; layer 1 is the construction already present in the remediation
framework, layers 2-3 are the contribution.

- **Layer 1 — append-only hash chain.** Each record's `record_hash` is the
  SHA-256 of its canonical JSON (keys sorted, `record_hash` excluded);
  `prior_record_hash` links to the predecessor; genesis is 64 zeros.
- **Layer 2 — per-window Merkle commitment.** Within each window the record
  hashes are leaves of a binary SHA-256 Merkle tree; the root commits to the
  exact multiset and order of records.
- **Layer 3 — signed checkpoints with an external anchor.** Periodically (every
  window, and at the head) the auditor signs a checkpoint over (record count,
  head hash, window id, Merkle root) under an Ed25519 private key; verifiers
  hold only the public key. The latest checkpoint is retained independently or
  published, as a CT monitor retains a signed tree head.

Verification (i) replays the chain, (ii) checks every checkpoint signature, and
(iii) checks that the presented log reproduces the independently held latest
checkpoint's count, head hash, and Merkle root. Step (iii) defeats truncation
and replacement: a short or rewritten log cannot reproduce a count and root it
never signed, and the adversary cannot re-sign.

## 5. Security Analysis

Assuming SHA-256 collision-resistance and Ed25519 unforgeability, and an honest
auditor holding the genuine latest checkpoint a and public key pk:

- **P1 (content integrity).** Any modification, reordering, or interior deletion
  of retained records changes a leaf hash, hence the Merkle root, and fails
  verification step (iii).
- **P2 (completeness / truncation resistance).** The anchor binds the true count
  and head; a truncated or extended log fails the count/head/root check. The
  residual is bounded by the inter-checkpoint interval.
- **P3 (non-repudiation of policy context).** Weights and feed versions are
  inside the hashed payload, so rolling them back is a content edit and is
  caught — making the evidence about *why*, not only *that*.
- **P4 (independence).** Verification compares against the signature and the
  externally held anchor, never the log holder, satisfying R2.

## 6. Evaluation

**Setup.** Both schemes and an adversarial harness mirror the framework's
hash-chain semantics exactly. For each of the eight classes and each adversary
(W, S) we run 200 trials on seeded logs of 400 records across 8 windows,
injecting the tamper at random positions. Overhead is measured on logs of 1,000
to 50,000 records.

**Detection (rate over 200 trials).**

| Tampering class | Chain (W) | Chain (S) | Ledger (W) | Ledger (S) |
|---|---|---|---|---|
| Modify field | 1.00 | 0.00 | 1.00 | 1.00 |
| Reorder | 1.00 | 0.00 | 1.00 | 1.00 |
| Delete (interior) | 1.00 | 0.00 | 1.00 | 1.00 |
| Truncate tail | **0.00** | 0.00 | 1.00 | 1.00 |
| Insert forged | 1.00 | 0.00 | 1.00 | 1.00 |
| Weight rollback | 1.00 | 0.00 | 1.00 | 1.00 |
| Feed-version forge | 1.00 | 0.00 | 1.00 | 1.00 |
| Wholesale replace | **0.00** | 0.00 | 1.00 | 1.00 |

The naive chain behaves as promised only against the restricted adversary, and
even then is blind to tail truncation and wholesale replacement. Against the
insider it detects nothing. The ledger detects every class under both
adversaries. Across 1,600 clean verifications neither scheme produced a single
false positive.

**Overhead.** Appending sustains 68,000-110,000 records/s. Full verification is
linear: 10.5 ms at 1,000 records, 925 ms at 50,000. At 50,000 records the naive
replay is 505 ms and the augmented verification 925 ms, so the added integrity
machinery is ~420 ms (a single Merkle pass plus a small constant of 200 Ed25519
checks). Signed checkpoints add 0.21% space, effectively constant in log size.

**Checkpoint-interval tradeoff (10,000-record log).**

| Interval | Checkpoints | Residual (<=) | Sign time (s) | Space (%) |
|---|---|---|---|---|
| 10 | 1000 | 9 | 4.01 | 5.19 |
| 50 | 200 | 49 | 0.75 | 1.04 |
| 100 | 100 | 99 | 0.40 | 0.52 |
| 250 | 40 | 249 | 0.15 | 0.21 |
| 500 | 20 | 499 | 0.08 | 0.10 |

The P2 residual (recent records not yet anchored) is a tunable knob: tighter
intervals shrink it at modest, bounded cost. Streaming anchoring drives it to
zero at the highest signing cost.

## 7. Compliance Mapping

NIST SP 800-53 **AU-9 (Protection of Audit Information)** requires protection
from unauthorized modification and deletion: P1 and P2 detect both, including by
privileged users. **AU-10 (Non-repudiation)** is served by the Ed25519
signatures binding each checkpoint to the auditor key. **AU-9(3)** (cryptographic
protection) is met by SHA-256 plus EdDSA. The same evidence supports FedRAMP
audit requirements and the CJIS Security Policy's logging and accountability
provisions, and because verification is independent of the log holder, it is
meaningful to an external assessor.

## 8. Related Work

Hash-linked records for tamper-evident timestamping originate with Haber and
Stornetta; Schneier and Kelsey applied chaining to audit logs on untrusted
machines. Crosby and Wallach introduced history trees for efficient
tamper-evident logging; our per-window Merkle commitment is in this lineage.
Certificate Transparency contributes the operational pattern we adopt: a signed
commitment to log state, held independently, that makes omission detectable. Our
contribution is to instantiate these ideas for autonomous remediation decision
provenance, characterize the hash-chain blind spot adversarially in that
setting, bind policy and feed context into the evidence, and quantify the cost
of closing the gap at fleet scale. This is orthogonal to the prioritization
decision itself: we make the *record* of any such decision trustworthy,
whatever scorer produced it.

## 9. Limitations

The completeness guarantee holds only up to the most recent anchored
checkpoint; the inter-checkpoint interval bounds the undetectable truncation
window. The evaluation uses synthetic logs with the production record schema; it
exercises the integrity machinery faithfully but does not model key compromise
or clock manipulation, which compose with standard key-management and
trusted-time defenses. The trust anchor must genuinely be independent; if the
adversary controls both the log and the retained checkpoint, no log-only scheme
can help.

## 10. Conclusion

Automating remediation moves the trust boundary from the decision to its record.
We showed adversarially that the append-only hash chains used for that record
have a structural blind spot — undetectable to a restricted adversary for
truncation and replacement, and useless against a realistic insider — and closed
it with a verifiable provenance ledger combining per-window Merkle commitments
and independently anchored Ed25519 checkpoints. The ledger detects all eight
tampering classes under both adversaries at 0.21% space overhead and sub-second
verification for 50,000 records. The result is an accountability layer for
autonomous security operations whose guarantees are pre-stated, adversarially
tested, and reproducible.

## Data Availability

The data and code that support the findings of this study are openly available
in the research-papers repository (paper1 directory). The ledger implementation,
the adversarial harness (`scripts/provenance_eval.py`), and the frozen result
tables (`results/provenance_v1/`) regenerate every reported number
deterministically from the fixed seeds.
