# Paper 3 — HygieneBench Submission Checklist

**Venue:** ACM CCS Workshop on Artificial Intelligence and Security (AISec)
**Simultaneous release:** arXiv cs.CR + Zenodo
**Prepared:** 2026-05-28
**Status:** READY FOR HUMAN REVIEW — NOT YET SUBMITTED

---

## Manuscript

- [x] **Manuscript complete** — `manuscript/paper_draft_v0.1.md` covers Abstract, Introduction (C1–C5), Related Work, HygieneBench Design (Tables 1–3), Experimental Setup (Table 4), Results (Tables 5–9, Figures 1–4), Discussion, Limitations, Conclusion, References
- [x] **Abstract accurate** — numbers match `results/primary_full_v1/primary_results.csv`
- [x] **All section claims sourced** — AP, P@k, and failure-rate numbers verified against CSV before writing
- [x] **Contribution list complete** — C1–C5 stated in §1; each addressed in paper body
- [x] **Supplemental appendix written** — `manuscript/supplemental_appendix_v0.1.md` covers Appendices A–F
- [ ] **LaTeX PDF compiled** — scaffold at `submission/acm/` requires ACM template download and compile; NOT YET COMPILED

---

## References

- [x] **All 11 references verified** — citation revision pass completed 2026-05-28
- [x] **[7] DARPA TC** — updated to confirmed GitHub data release URL
- [x] **[8]** — unverified Ma et al. VLDB removed; replaced with DOMINANT (Ding et al. SDM 2019)
- [x] **[9] PyGOD** — author list corrected; JMLR 25(141) URL confirmed
- [x] **[11] Noonan et al.** — removed (not found in AISec 2020 proceedings)
- [x] **Reference renumbering** — old [12] → new [11]; all in-text citations updated
- [x] **BibTeX file created** — `submission/acm/references.bib` with all 11 entries
- [ ] **BibTeX entries spot-checked against ACM DL** — human review required before submission

---

## Appendix

- [x] **Appendix A** — method hyperparameter grids (M1–M8) complete
- [x] **Appendix B.1–B.5** — per-condition AP tables verified against `primary_results.csv`
- [x] **Appendix C** — failure-flag detail by method × task × condition
- [x] **Appendix D** — schema reference (table descriptions, structural priors)
- [x] **Appendix E** — reproducibility checklist
- [x] **Appendix F** — citation verification status updated (all items resolved)
- [ ] **Venue formatting** — supplemental appendix must be formatted per CCS AISec CFP instructions (separate PDF or within page limit)

---

## Figures

- [x] **Figure 1** — AP heatmap (fig1_ap_heatmap.pdf) — vector PDF, acceptable
- [x] **Figure 2** — Failure-flag heatmap (fig2_failure_heatmap.pdf) — vector PDF; **annotations require visual inspection before submission**
- [x] **Figure 3** — AP by condition (fig3_ap_by_condition.pdf) — vector PDF, acceptable; verify column-width fit
- [x] **Figure 4** — T2/T5 ML gain (fig4_t2_t5_ml_gain.pdf) — vector PDF; use `\begin{figure*}` for two-column span
- [x] **Figures copied to** `submission/acm/figures/`
- [ ] **Figure 2 annotation visual inspection** — open PDF and confirm all text labels render correctly
- [ ] **All figures tested in LaTeX layout** — requires ACM template compile
- [x] **PNG versions** — 150 DPI; NOT for submission use; PDFs used instead
- [ ] **300 DPI PNGs** — regeneration optional (for arXiv preprint only; not needed for ACM submission)

---

## ACM LaTeX Scaffold

- [x] **`submission/acm/main.tex`** — ACM two-column structure; awaits official `acmart.cls`
- [x] **`submission/acm/references.bib`** — 11 BibTeX entries
- [x] **`submission/acm/sections/abstract.tex`** — converted from Markdown
- [x] **`submission/acm/sections/introduction.tex`** — converted; `\label{sec:related}` etc. added
- [x] **`submission/acm/sections/related.tex`** — converted; cite keys linked
- [x] **`submission/acm/sections/design.tex`** — converted; table `\input` commands linked
- [x] **`submission/acm/sections/setup.tex`** — converted; failure equation in `\begin{equation}`
- [x] **`submission/acm/sections/results.tex`** — converted; figure environments included
- [x] **`submission/acm/sections/discussion.tex`** — converted
- [x] **`submission/acm/sections/conclusion.tex`** — URL placeholder marked `[ACTION REQUIRED]`
- [x] **`submission/acm/tables/`** — all 8 tables as separate `.tex` files
- [x] **`submission/acm/figures/`** — all 4 PDFs copied
- [ ] **Download ACM `acmart.cls`** from https://www.acm.org/publications/proceedings-template
- [ ] **Set `\documentclass[sigconf,anonymous]{acmart}`** for double-blind review
- [ ] **Compile:** `pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex`
- [ ] **Page count verified** — target 6–8 pages body + references (check against CCS AISec CFP)
- [ ] **ACM rights form** — complete after acceptance; not required at submission
- [ ] **CCS concepts verified** — use ACM CCS tool at https://dl.acm.org/ccs

---

## Repository / Zenodo

- [x] **`REPOSITORY_RELEASE_CHECKLIST.md` created** — lists include/exclude files, verification steps
- [ ] **GitHub repository created** — `[TO BE FILLED]`
- [ ] **README.md written** — not yet drafted; required before Zenodo deposit
- [ ] **Zenodo deposit created** — `[TO BE FILLED AFTER DEPOSIT]`
- [ ] **Zenodo DOI obtained** — `[TO BE FILLED AFTER DEPOSIT]`
- [ ] **Conclusion URL updated** — replace `[TO BE FILLED AFTER ZENODO DEPOSIT]` in `sections/conclusion.tex` and `paper_draft_v0.1.md`
- [ ] **Zenodo record set to public** before paper submission

---

## Claim Safety

- [x] **Claim audit completed** — 2026-05-28; one fix applied ("published" → "openly released" in §6.3 / conclusion)
- [x] **No superiority claim** over Defender for Identity, Sentinel, Splunk UBA, or any commercial product
- [x] **No production deployment claim**
- [x] **No government validation claim**
- [x] **No ADOT/employer data claim**
- [x] **No real attack detection claim**
- [x] **ATT&CK mappings** annotated as enabling-condition correlations, not technique detection
- [x] **All numbers sourced** from `primary_results.csv` (no manual estimates)
- [x] **Synthetic-data limitation** disclosed in Abstract, §6.2 Limitations, and dataset card
- [x] **M6 and M8 approximations** disclosed in §4 and §6.2
- [x] **"first benchmark, to our knowledge"** — properly hedged with "to our knowledge"
- [x] **Negative-result framing** — 86.2% failure rate correctly framed as benchmark-specific, not a general ML claim
- [ ] **Final human read-through** — recommended before submission to catch any remaining tone issues

---

## Submission Status

| Item | Status |
|---|---|
| Manuscript complete | ✅ Yes |
| References verified | ✅ Yes (11/11) |
| Appendix updated | ✅ Yes |
| Figures checked | ✅ PDFs acceptable; fig2 annotations need visual inspection |
| ACM scaffold created | ✅ Yes (awaits template compile) |
| Repository checklist created | ✅ Yes |
| Zenodo DOI | ⏳ Pending deposit |
| Claim audit passed | ✅ Yes (1 fix applied) |
| No overclaims | ✅ Yes |
| **Submitted** | ❌ NOT YET SUBMITTED |

---

## Remaining blockers before submission

1. **[BLOCKER]** Zenodo deposit → obtain DOI → update Conclusion URL placeholder
2. **[BLOCKER]** Download ACM `acmart.cls` → compile LaTeX → verify page count against CFP
3. **[REQUIRED]** Visual inspection of fig2 PDF annotations
4. **[REQUIRED]** Set anonymous mode (`\documentclass[sigconf,anonymous]{acmart}`) if venue uses double-blind review — verify CCS AISec review model
5. **[REQUIRED]** Write `README.md` for artifact before Zenodo deposit
6. **[RECOMMENDED]** Final human read-through of compiled PDF

---

*Internal document — do not include in artifact release.*
