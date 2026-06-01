# References To Verify

## Phase 21 status

- **Drafted in `references.bib` (Tier-1), CONFIRM fields before submission — NOT
  re-verified in authoring environment:** CVSS spec, EPSS (Jacobs et al.), Allodi &
  Massacci, Sabottke et al., CISA KEV, CISA BOD 22-01, NIST SP 800-40r4 / 800-53r5 /
  800-30r1, CIS Controls v8, Wilcoxon 1945, Holm 1979, Efron 1987 (BCa).
- **Still UNRESOLVED — no bib entry, remain `[VERIFY]` in the manuscript:** Deep
  VULMAN, VulRG, VulnScore, V-REx, Microsoft Defender VM, Tenable VPR/ACR, Qualys
  TruRisk, Cisco/Kenna, exact CJIS Security Policy version, and the Abstract numeric
  re-check.

The original worklist below remains the master list; "drafted" items still require
a confirmation pass against the publisher of record.

---

# References To Verify (original worklist)

Clean worklist of every reference still needing verification before submission.
No exact citations are invented here. Resolve each, then move into the manuscript
bibliography. See `citation_audit.md` for where each is used and the claim it
supports.

Format: Reference/topic | Section(s) | Search target/source | Priority

## High priority (block submission)

- CVSS specification (v3.1 and/or v4.0) | §2,§5,§9 | FIRST.org CVSS spec pages | high
- EPSS model/documentation | §2,§3,§5,§9,§13.3 | FIRST.org EPSS; EPSS paper (Jacobs et al.) | high
- CISA KEV catalog | §2,§5,§8,§9 | cisa.gov KEV catalog page | high
- CISA BOD 22-01 | §2,§10 | cisa.gov directives | high
- Deep VULMAN | §3,§14 | original paper (verify authors/venue/year) | high
- VulRG | §3,§14 | original paper | high
- VulnScore | §3,§14 | original paper | high

## Medium priority

- Allodi & Massacci (exploitation in the wild) | §2,§3 | ACM/journal | medium
- Jacobs et al. (exploit prediction / EPSS lineage) | §2,§3 | paper/DOI | medium
- NIST SP 800-40 Rev. 4 | §2,§10 | csrc.nist.gov | medium
- NIST SP 800-53 Rev. 5 | §10 | csrc.nist.gov | medium
- Wilcoxon signed-rank (standard reference) | §9 | classic stats reference | medium
- Holm (1979) Holm-Bonferroni | §9 | Scandinavian J. Statistics | medium

## Low / conditional priority

- Sabottke et al. (early-warning exploit prediction) | §3 | USENIX Security | low-med
- NIST SP 800-30 Rev. 1 | §4,§10 | csrc.nist.gov | low-med
- CIS Controls v8/v8.1 | §10 | cisecurity.org | low-med
- CJIS Security Policy (version used) | §10 | FBI CJIS | low (only if §10 cites)
- V-REx | §3 | original paper | medium
- Other ML-prioritization papers (earlier review) | §3 | prior lit review | low-med
- Efron — bootstrap / BCa | §9 | classic stats reference | low-med
- Microsoft Defender VM | §3 | vendor docs | low
- Tenable VPR / ACR | §3 | vendor docs | low
- Qualys TruRisk | §3 | vendor docs | low
- Cisco / Kenna risk model | §3 | vendor docs | low
- Synthetic-benchmarking / reproducibility methodology refs | §7,§8 | as applicable | low

## Verification rules

1. Confirm authors, year, venue, and a stable identifier (DOI/URL) before use.
2. For standards (NIST/CISA/CIS/CJIS), pin the exact revision/version cited.
3. For commercial RBVM, cite vendor documentation and label as "acknowledged, not
   benchmarked."
4. Do not paste any reference into the manuscript while still marked `[VERIFY]`.
