# Cover letter — Computers & Security (Elsevier)

**Manuscript:** Auditable Autonomy: Tamper-Evident, Cryptographically Verifiable
Decision Provenance for Autonomous Vulnerability Remediation in Regulated Fleets

**Author:** Harshavardhan Malla (Independent Researcher) — harshavardhanmalla75@gmail.com

---

Dear Editor-in-Chief,

I am pleased to submit the enclosed manuscript for consideration as an original
research article in *Computers & Security*.

**The problem.** As vulnerability remediation in large regulated fleets becomes
automated, the security question shifts from *which vulnerability to patch first*
to *whether the record of what was decided, and why, can be trusted after the
fact*. Regulatory regimes such as FISMA, FedRAMP, and the FBI CJIS Security Policy
require audit trails that survive a privileged insider, yet the append-only hash
chains commonly used for decision logging carry a structural blind spot: they
certify the internal consistency of the records present, not the completeness of
the records that should exist. An adversary who truncates the tail, or an insider
who recomputes downstream hashes, can leave a log that still verifies perfectly.

**The contribution.** We make this gap precise with an adversarial evaluation of an
automated remediation log under two adversaries and eight tampering classes (200
trials each). A naive SHA-256 hash chain is *blind to tail truncation and wholesale
replacement* (detection rate 0.00 for both) against a restricted adversary, and
detects *nothing* (0.00 across all eight classes) against a realistic insider who
recomputes hashes. We then present a verifiable provenance ledger that augments the
chain with per-window Merkle commitments and periodic Ed25519-signed checkpoints,
anchored by an independently held latest checkpoint in the style of a Certificate
Transparency signed tree head. The ledger detects all eight attacks under both
adversaries (detection rate 1.00) at only 0.21% space overhead, verifies a 50,000-
record log in under one second (925 ms), and sustains append throughput of 68,000
to 110,000 records per second. Guarantees are stated in advance as checkable
properties, proven, then verified adversarially across all 1,600 trials with zero
false positives. We map the construction to NIST SP 800-53 audit controls (AU-9,
AU-10, AU-9(3)).

**Fit to Computers & Security.** The work sits squarely within the journal's core
scope: tamper-evident logging, cryptographic provenance, and dependable,
independently auditable security for high-consequence systems. It combines a
cryptographic construction (hash chaining, Merkle commitments, EdDSA signed
checkpoints with an external anchor) with an adversarial security evaluation and a
concrete compliance mapping, delivering a deployable accountability layer for
autonomous security decisions whose integrity is verified rather than asserted.
The emphasis on auditability that does not require trusting the party holding the
log makes it directly relevant to practitioners building dependable security
operations.

**Assurances.** This manuscript is original, is not under consideration elsewhere,
and has not been published before. The evaluation uses synthetic logs built on the
production decision-record schema (no proprietary or personal data); the ledger
implementation, the adversarial harness, and the frozen result tables are released
so every reported number regenerates deterministically from fixed seeds. The
author declares no conflict of interest and received no funding.

Thank you for considering this submission.

Sincerely,
Harshavardhan Malla

---

## Suggested reviewers
Researchers with directly relevant expertise in tamper-evident logging,
transparency logs, and cryptographic auditing. None are collaborators of the author.
*(Please verify current affiliations and obtain contact emails before submission —
the names and institutions below are public, but emails should not be guessed.)*

- **Dan S. Wallach**, Rice University — efficient tamper-evident logging and history trees.
- **Bryan Ford**, EPFL — distributed systems security, transparency and accountable logging (e.g., CoSi/cothority).
- **Josh Benaloh / Melissa Chase**, Microsoft Research — verifiable data structures and key transparency (CONIKS lineage).
- **Charalampos (Babis) Papamanthou**, Yale University — authenticated data structures and transparency logs.
- **Gene Tsudik**, University of California, Irvine — secure logging and forward-secure log authentication.
- **Ben Laurie**, Google — Certificate Transparency and signed-tree-head transparency systems.

## Opposed reviewers
None.
