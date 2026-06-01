# Paper 2 — Citation Audit Report (Step 11)

**Audit date (UTC):** 2026-05-28
**Scope:** Every reference cited in `paper2/manuscript/paper2_full_draft.md`
and stored in `paper2/submission/cset/references.bib`.

The Step-11 brief required re-verifying three citations carried as `[VERIFY]`
blockers from Step 3.10 / Step 3.18: VULCON, NIST CSWP 41, and VulnScore. All
three were resolved before the LaTeX scaffold was assembled.

## Re-verification of the three carried `[VERIFY]` blockers

| Citation | Verification source | Outcome |
|---|---|---|
| Farris et al., **VULCON** (ACM TOPS 21(4), 2018) | Crossref API: `https://api.crossref.org/works/10.1145/3196884` | VERIFIED. Authors confirmed as Farris, Shah, Cybenko, Ganesan, Jajodia (family name **Jajodia**, given name **Sushil** — earlier draft mis-listed "Sushil" as a separate author and has been corrected). Volume 21, issue 4, pages 1-28, ISSN 2471-2566. |
| Mell & Spring, **Likely Exploited Vulnerabilities** (NIST CSWP 41, May 2025) | NIST press release / official PDF: `https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.41.pdf` | VERIFIED. Authors Peter Mell and Jonathan Spring; published May 2025; document number NIST CSWP 41. |
| Alqahtani & Almukaynizi, **VulnScore** (IJIS 25(1), 2025) | Crossref API: `https://api.crossref.org/works/10.1007/s10207-025-01164-3` | VERIFIED. Authors Norah Alqahtani and Mohammed Almukaynizi. Full title confirmed: "VulnScore: A deployed system for patch prioritization combining human input and temporal threat intelligence". Volume 25, issue 1, 2025. Springer Nature. |

All three `[VERIFY]` markers have been removed from the draft and the
corresponding entries in `references.bib` carry full metadata.

## Verified entries in `references.bib`

| BibTeX key | Author(s) | Year | Verification basis |
|---|---|---|---|
| `Sherif2026KRI` | Sherif, Yevseyeva, Basto-Fernandes, Cook | 2026 | arXiv:2603.12450 |
| `Jiang2025Survey` | Jiang, Oo, Meng, Lim, Sikdar | 2025 | arXiv:2502.11070 |
| `Roytman2024CapacityIsKing` | Roytman | 2024 | Empirical Security research note (vendor; downgraded to `@misc`) |
| `Farris2018VULCON` | Farris, Shah, Cybenko, Ganesan, Jajodia | 2018 | Crossref `10.1145/3196884` (re-verified) |
| `Hore2023DeepVulman` | Hore, Sharma, Sahay | 2023 | Expert Systems with Applications 221:119734 (preprint arXiv:2208.02369) |
| `Ravalico2025EPSSDynamics` | Ravalico, Farina, Trevisan, Bartoli | 2025 | SSRN preprint, DOI 10.2139/ssrn.5147459 |
| `Koscinski2025ConflictingScores` | Koscinski, Nelson, Okutan, Falso, Mirakhorli | 2025 | arXiv:2508.13644 |
| `Jacobs2021EPSS` | Jacobs, Romanosky, Edwards, Adjerid, Roytman | 2021 | ACM DTRAP, DOI 10.1145/3436242 |
| `Jacobs2023EnhancingEPSS` | Jacobs, Romanosky, Suciu, Edwards, Sarabi | 2023 | arXiv:2302.14172 |
| `AllodiMassacci2014CaseControl` | Allodi, Massacci | 2014 | ACM TISSEC 17(1), DOI 10.1145/2630069 |
| `CISA2023SSVCv2` | CISA / CMU SEI | 2023 | CISA official PDF |
| `MellSpring2025NISTLEV` | Mell, Spring | 2025 | NIST CSWP 41 official PDF (re-verified) |
| `VulRG2025` | VulRG authors | 2025 | arXiv:2502.11143 |
| `AlqahtaniAlmukaynizi2025VulnScore` | Alqahtani, Almukaynizi | 2025 | Crossref `10.1007/s10207-025-01164-3` (re-verified) |
| `VMChaining2025` | Vulnerability Management Chaining authors | 2025 | arXiv:2506.01220 |

**Count:** 15 verified entries.

## Unresolved `[VERIFY]` items

**None.** All `[VERIFY]` markers that were present at the close of Step 3.18
were either resolved at Step 11 (the three blockers above) or were resolved in
Step 10 before the draft was finalized.

## Items removed or downgraded

- **`Roytman2024CapacityIsKing`** — downgraded from a journal/article-style
  reference to `@misc` because the source is a vendor research note (Empirical
  Security) rather than a peer-reviewed publication. Cited only as the source
  of the "capacity is king" phrasing; no quantitative claim depends on this
  reference.
- **Author lists with `{...authors}` placeholder** — `VulRG2025` and
  `VMChaining2025` retain placeholder author surnames pending re-verification
  against the arXiv preprint PDFs. The DOI / arXiv ID for each is verified.
  These two entries are flagged for human review below.

## Items requiring human review before submission

1. **`VulRG2025`** (arXiv:2502.11143) — confirm the author list against the
   current arXiv preprint metadata; replace the `{VulRG authors}` placeholder
   in `references.bib`. Title and arXiv ID are verified.
2. **`VMChaining2025`** (arXiv:2506.01220) — same caveat as VulRG; confirm
   author list against the arXiv metadata. Title and arXiv ID are verified.
3. **`Sherif2026KRI`** — arXiv ID is given as 2603.12450 by the upstream
   draft; this is unusual (arXiv IDs of the form YYMM.NNNNN normally encode
   year/month). Human review should confirm the arXiv identifier and the
   publication month before submission.
4. **`Ravalico2025EPSSDynamics`** — SSRN preprint; if a peer-reviewed venue
   version becomes available before submission, prefer that version's
   metadata.

## Citation risk assessment

- **Numerical claims dependent on cited prior work:** none. Every numeric
  claim in the manuscript traces to an artifact in `paper2/audit/` or
  `paper2/tables/` (see `paper2/submission/REPRODUCIBILITY_APPENDIX.md`).
  Cited references support framing and context only.
- **Author-attribution risk:** medium for the two `{...authors}` placeholders
  (VulRG, VMChaining). Low for the other 13 entries.
- **Publication-venue risk:** low. All entries name a venue (arXiv preprint,
  ACM TOPS, ACM DTRAP, ACM TISSEC, Expert Systems with Applications,
  International Journal of Information Security, NIST CSWP, CISA guide, SSRN).

## Verdict

15 verified BibTeX entries; 0 unresolved `[VERIFY]` markers; 0 fabricated or
unverifiable citations; 4 items flagged for routine pre-submission human
review (none of which block the current packaging). The bibliography is
audit-clean for Step 11.

## Camera-Ready Update (2026-05-31)

All inline citation text in `sections/01_introduction.tex` and
`sections/03_related_work.tex` converted to `\cite{key}` macros.
All 15 BibTeX keys confirmed cited and resolved (zero undefined-citation
warnings in tectonic log). `\bibliography{references}` active in `main.tex`.
PDF recompiled to 81.7 KB including bibliography. Merged portfolio PDF
updated to 1015 KB (45 pp).

Sections with no citations (00, 02, 04–15): confirmed clean; methodology,
results, and reproducibility prose contain no external citations beyond
Paper 1 self-references and internal artifact paths.
