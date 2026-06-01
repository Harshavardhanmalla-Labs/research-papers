# ACM `acmart` scaffold — Paper 1

Structural LaTeX scaffold for the manuscript
**"Context-Aware Vulnerability Prioritization for Government Endpoint Fleets:
Integrating Exploit Intelligence, Asset Criticality, and Endpoint Telemetry."**

Generated (Phase 22A) from `../manuscript/paper_submission_draft.md`. This is a
starting point for venue formatting, **not** a camera-ready file.

## Layout

- `main.tex` — `acmart` document: title, author, abstract, `\input` of all 17
  sections, generated table/figure floats, bibliography, and a reproducibility
  appendix.
- `sections/00_abstract.tex` … `17_conclusion.tex` — section prose ported to
  LaTeX (markdown emphasis/code/citations converted; identifiers escaped).
- `references.bib` — copy of the Tier-1 bibliography (each entry flagged
  "CONFIRM at camera-ready"; not independently verified).
- `figures/*.pdf` — 5 generated figures (copied from `../figures/`).
- `tables/*.tex` — 7 generated LaTeX tabulars (copied from `../tables/`).

## Compile status

**Not compiled here.** No LaTeX toolchain is installed in the authoring
environment (`pdflatex`, `latexmk`, and `acmart.cls` are absent). Per the build
plan this is expected and is **not** a failure. To compile elsewhere:

```bash
# requires a TeX distribution with the ACM acmart class
latexmk -pdf main.tex      # or: pdflatex main.tex; bibtex main; pdflatex x2
```

## Required cleanup before submission (TODO)

1. **Citations.** Resolve every in-text `\textbf{[VERIFY: ...]}` marker (adjacent
   ML works, commercial RBVM vendor docs, exact CJIS version). Do **not**
   fabricate. Confirm all Tier-1 `references.bib` entries against the publisher of
   record. See `../manuscript/references_todo.md` and `citation_audit.md`.
2. **Table widths.** Several tabulars are wide; wrap with `\resizebox`, switch to
   `booktabs`, or use landscape. Floats are currently `table*` with `\small`.
3. **Cross-references.** The prose uses literal "Table N"/"Figure N"; optionally
   convert to `\ref{}` against the labels in `main.tex`
   (`tab:acceptance`, `tab:ehd`, …, `fig:ehd`, …).
4. **CCS concepts / rights / venue.** Add `\ccsdesc`, set `\setcopyright`, and the
   conference/journal metadata (recommended venue: ACM DTRAP).
5. **Author metadata.** Country, contact email, ORCID.

## Guardrails honored

- **Framing:** benchmark/framework with a **neutral** empirical result — the
  proposed model does not outperform EPSS or a random ordering under toy fixtures
  and placeholder weights. No superiority, real-world-validation, autonomous-
  remediation, or compliance-proof claims.
- **No immigration / external-process language** anywhere in this scaffold.
- **No fabricated citations**; unverified works remain visibly flagged.
- **Numbers** trace to the frozen artifact (`../../results/primary_full_v1/`),
  re-verified in Phase 22A.
