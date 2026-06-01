# Paper 2 — CSET LaTeX scaffold

This directory holds the LaTeX scaffold for the USENIX **CSET** submission
target (primary venue per F9). It is a self-contained directory: `main.tex`
+ section files + figures + tables + `references.bib`.

## Template status

**[VERIFY with current CSET CFP/template].** `main.tex` uses a neutral
`\documentclass[11pt,letterpaper]{article}` preamble with a conservative
package list (`geometry`, `graphicx`, `booktabs`, `hyperref`, `microtype`,
`cite`, `xcolor`). The current CSET `.cls` / `.sty` was **not** swapped in
during Step 11 because the venue template must be downloaded fresh at
submission time and may not be the same artifact carried in this repo.

To finalize for submission:

1. Download the current CSET document class from the venue site.
2. Replace the `\documentclass` line and the preamble package list with the
   venue-required equivalents.
3. Re-check that no section file uses an environment that the venue class
   forbids. The section files only use: `\section`, `\subsection`,
   `\subsubsection`, `itemize`, `\textbf`, `\emph`, `\texttt`, the standard
   LaTeX escapes (`\&`, `\%`, `\$`, `\#`, `\_`, `\{`, `\}`,
   `\textasciitilde`, `\textasciicircum`), and `\input{sections/...}` in
   `main.tex`. No custom commands or hand-rolled environments are used.
4. Decide on the author-block / anonymization mode required by the
   submission round; replace `\author{Anonymous (submission scaffold)}` in
   `main.tex` accordingly.

## Compile status

**Not compiled in Step 11.** No LaTeX engine was invoked during packaging.
A human reviewer must run the compile pass at submission time.

Recommended compile recipe (from this directory):

```
pdflatex main.tex
bibtex   main
pdflatex main.tex
pdflatex main.tex
```

If `pdflatex` complains about missing packages, the first place to check is
the package list at the top of `main.tex`; all of `geometry`, `graphicx`,
`booktabs`, `hyperref`, `microtype`, `cite`, `xcolor` are standard TeX Live
packages.

## Sections included

| File | Source | Role |
|---|---|---|
| `sections/00_abstract.tex` | `paper2_full_draft.md §1` | Abstract (wrapped in `abstract` environment) |
| `sections/01_introduction.tex` | `§2` | Introduction |
| `sections/02_background.tex` | `§3` | Background |
| `sections/03_related_work.tex` | `§4` | Related Work |
| `sections/04_problem_statement.tex` | `§5` | Problem Statement |
| `sections/05_failure_aware_gate.tex` | `§6` | The failure-aware multi-t0 calibration gate |
| `sections/06_study_design.tex` | `§7` | Study Design |
| `sections/07_public_feed_data.tex` | `§8` | Public Feed Data |
| `sections/08_fixed_prior_sensitivity.tex` | `§9` | Fixed-Prior Sensitivity Study |
| `sections/09_metrics_inference.tex` | `§10` | Metrics and Inference |
| `sections/10_results.tex` | `§11` | Results |
| `sections/11_discussion.tex` | `§12` | Discussion |
| `sections/12_limitations.tex` | `§13` | Limitations |
| `sections/13_future_work.tex` | `§14` | Future Work |
| `sections/14_conclusion.tex` | `§15` | Conclusion |
| `sections/15_reproducibility.tex` | `§16` | Reproducibility |

Section 17 (References) is handled by `references.bib` via `\bibliography`,
not by a section file.

Each section file starts with a header comment recording the source markdown
section number and noting that wording was preserved verbatim.

## Wording preservation

The 16 section files were produced from `paper2/manuscript/paper2_full_draft.md`
by `scripts/paper2_md_to_latex.py`. The converter:

- Splits on `## N. Title` H2 headings.
- Converts `### X` / `#### X` headings to `\subsection{...}` / `\subsubsection{...}`.
- Converts `**bold**` / `*italic*` / `` `code` `` to `\textbf{...}` /
  `\emph{...}` / `\texttt{...}`.
- Converts `-` / `*` bullets to `\begin{itemize}...\end{itemize}`.
- LaTeX-escapes the special characters listed above.
- Does NOT alter wording.

The claim audit ran on the concatenated section files (see
`paper2/submission/CLAIM_AUDIT_REPORT.md`) and reports 0 violations, which
verifies that wording survived the conversion intact.

## Copy counts

| Artifact | Source | Count copied |
|---|---|---|
| Figures (PNG) | `paper2/figures/` | 7 |
| Figures (PDF) | `paper2/figures/` | 7 |
| Tables (CSV) | `paper2/tables/` | 10 |
| Tables (MD) | `paper2/tables/` | 10 |
| Wide table CSV | `paper2/tables/primary_per_seed_wide.csv` | 1 |
| Inference (CSV) | `paper2/tables/inference/` | 6 |
| Inference (MD) | `paper2/tables/inference/` | 6 |
| Bibliography | (this directory) | 15 entries in `references.bib` |
| LaTeX section files | (this directory) | 16 |

**Total in `figures/`:** 14 files.
**Total in `tables/` (including `tables/inference/`):** 33 files.

## Formatting TODOs (deferred to submission time)

- [ ] Swap `\documentclass{article}` for the venue document class.
- [ ] Confirm preamble package list matches venue defaults.
- [ ] Replace `\author{Anonymous (submission scaffold)}` with the venue's
      required author / affiliation block (or anonymized equivalent).
- [ ] Run the compile recipe above and resolve any environment-specific
      errors.
- [ ] Re-check figure widths if the venue column width differs from the
      default 6.5"; figures may need `\includegraphics[width=\columnwidth]{...}`
      qualifiers that are not present in the current scaffold.
- [ ] Confirm `\bibliographystyle{plain}` matches the venue style (CSET has
      historically used `plain`; verify against the current CFP).
