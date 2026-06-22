# Design Brief — Research Portfolio (research.freedomlabs.in)

**For:** UI/UX Designer (Figma)
**From:** Harshavardhan Malla, Independent Researcher
**Deliverable wanted:** High-fidelity Figma designs + a small design system (tokens + components), light **and** dark themes as first-class.

---

## 1. What this is
A web portfolio that presents **21 peer-quality research papers** (cyber-hygiene, vulnerability prioritization, compliance automation) by a single independent researcher. Each paper has a manuscript, a compiled PDF, figures, frozen/reproducible results, and source code. The site is the canonical home for this body of work.

## 2. Why it exists (the one goal that overrides everything)
This is **evidence for a US EB-1A "extraordinary ability" immigration petition.** The design must make a reviewer (an immigration officer, an expert writing a recommendation letter, an academic peer) conclude within seconds: *"This is a serious, prolific, independent researcher producing original, rigorous, citable work."*

Every design decision should be judged against that. Impressive-but-gimmicky loses to **credible, restrained, and substantive.**

## 3. Audiences (in priority order)
1. **EB-1A reviewers / immigration officers / recommendation-letter writers** — non-specialist or semi-specialist; need to grasp scope, rigor, and impact fast, and to trust it.
2. **Academic & industry peers** — may cite or reference the work; need clean access to manuscripts, results, and citations.
3. **Recruiters / journalists / collaborators** — skim for headline contributions.

## 4. Aesthetic direction — "Authoritative / Academic"
Calm, credible, journal-like. Think a blend of **arXiv's seriousness, Stripe Press's typographic care, and Distill.pub's clarity.** Not a startup landing page.

- Generous whitespace; content breathes.
- Strong typographic hierarchy does the heavy lifting (not color or effects).
- One restrained accent color; the rest is ink, paper, and neutrals.
- Data-forward: results and numbers are first-class visual citizens.
- Motion is minimal and functional (no parallax, no flashy gradients).
- It should feel like it could be a university research group's site — but for one person.

## 5. Themes — light AND dark, both first-class
- **Light** is likely the default (prints/screenshots cleanly into petition packets, reads as academic). Background = warm off-white / paper, not stark white.
- **Dark** must be equally polished (current site uses `#0a0e1a`). Deep navy/ink, not pure black.
- Provide a clear toggle; remember the user's choice.
- Deliver full token sets for both (see §10).

## 6. Information architecture
```
/                      Landing — the body of work (portfolio)
/#paperN               Paper detail (deep-linked; opens specific paper)
/#paperN/<tab>         Paper detail at a specific tab (manuscript|pdf|figures|results|code)
```
Two core screens: **(A) Portfolio landing** and **(B) Paper detail.** Plus global chrome (top bar, theme toggle, cite affordance) and a few supporting modules.

---

## 7. Screen A — Portfolio landing
The single most important screen for credibility. Must communicate **scope + rigor + a coherent research program** immediately.

**Must include:**
1. **Header / identity block** — Name "Harshavardhan Malla", "Independent Researcher", one-line positioning of the research program (e.g., "Reproducible, pre-registered research on cyber-hygiene and vulnerability prioritization"). Quiet, confident, no avatar gimmicks.
2. **At-a-glance credibility stats** — e.g., *21 papers · 1 published · 20 submission-ready · N reproducible result sets · pre-registered methodology.* These are trust signals; design them as restrained stat blocks, not glowing chips.
3. **The research program narrative** — a short visual that shows these aren't 21 random papers but a connected program (themes / a progression / clusters). This is a key EB-1A signal ("sustained body of work"). Could be a labeled timeline, a thematic grouping, or a small map. Designer's call on form.
4. **Featured work** — highlight the published paper and 2–3 strongest results. One hero-level card is fine; keep it dignified.
5. **The full paper list/grid** — all 21, scannable. Each card shows: title, short/citable name, status, target venue, and the **headline result** (e.g., "272× faster drift detection", "94% Precision@50, 70% faster MTTR"). Cards must make the *result* legible at a glance.
6. **Filter + sort + search** — filter by status (published/ready), sort (by topic, by impact), and a keyboard-accessible search ("/" to focus). Keep controls subtle and secondary to content.
7. **Footer** — author, contact-free (no email per author preference), links to the code org, a one-line reproducibility statement.

**Tone check:** a reviewer scrolling this page should think "rigorous and prolific," not "marketing site."

## 8. Screen B — Paper detail
Where a reviewer evaluates an individual paper. Needs to balance *reading the manuscript* with *quickly verifying rigor* (results, figures, code).

**Header region (per paper):**
- Title (full, citable), short name, status badge (Published / Submission-ready), target venue.
- **Headline result chip** prominently (the single number that matters).
- Primary actions: **Open PDF**, **Cite**, **Copy link** (deep link), **Code/Reproduce**.
- Keep author = "Harshavardhan Malla · Independent Researcher" (no email).

**Tabbed content** (deep-linkable; keep these tabs):
- **Manuscript** — long-form reading view. This is critical: comfortable measure (~70–75 chars), academic typography, proper headings, figure/caption styling, table styling, math support. Should feel like reading a well-set journal article in the browser.
- **PDF** — embedded compiled PDF with zoom; download.
- **Figures** — gallery of the paper's figures with captions.
- **Results** — the frozen/quantitative results (tables, key metrics, confidence intervals). Design these to look trustworthy and precise.
- **Code / Reproduce** — link to source + frozen results; a short "how to reproduce" affordance.

**Cite experience** — a popover/panel giving **IEEE citation + BibTeX**, each with one-click copy. Citability is a priority; make this obvious and frictionless.

**In-paper navigation** — a section/heading outline (table of contents) for the manuscript on wide screens; "back to all papers" always reachable.

## 9. Components to design (Figma component set)
- App top bar (logo/identity, theme toggle, summary stats, search entry)
- Stat block / credibility metric
- Paper card (with status badge, venue tag, headline-result treatment) — design all states
- Status badge (Published, Submission-ready) — two clear, dignified variants
- Headline-result chip / metric callout
- Filter chips + sort control + search field
- Research-program module (timeline/cluster/map — your proposal)
- Paper-detail header
- Tab bar + tab panels (manuscript, pdf, figures, results, code)
- Manuscript typographic styles (h1–h4, body, blockquote, figure+caption, table, code/inline-code, math)
- Figure gallery item + lightbox
- Results table + metric/CI display
- Cite popover (IEEE + BibTeX, copy buttons, copied-state)
- Buttons (primary/secondary/ghost), links, copy-to-clipboard control
- Footer
- Empty / loading / error states for PDF and data

## 10. Design system / tokens (deliver for BOTH themes)
- **Color:** background, surface, elevated surface, border, ink (text) primary/secondary/tertiary, one accent + its hover/active, status colors (published, ready), success/copy feedback. Provide light + dark values. WCAG AA contrast minimum (AAA for body text where feasible).
- **Typography:** a credible serif for headings/display (e.g., a Charter/Tiempos/Source Serif feel) and a clean sans or the same serif for body — designer's choice, but it must read "scholarly." Define a full type scale, line-heights, and the reading measure for manuscripts.
- **Spacing & layout:** base spacing scale, max content widths (wide for landing, narrow ~720px for manuscript reading), grid for the paper list.
- **Radius, borders, shadows:** restrained; prefer hairline borders over heavy shadows for the academic feel.
- **Motion:** durations/easing for the few transitions (tab change, popover, theme switch). Keep subtle.

## 11. Responsive
- Desktop-first (reviewers mostly on laptops) but must be fully usable on tablet and phone.
- Manuscript reading view must be excellent on mobile.
- Define breakpoints and how the paper grid, tabs, and TOC reflow.

## 12. Accessibility (non-negotiable for credibility)
- WCAG 2.1 AA. Keyboard navigable throughout; visible focus states; semantic headings; alt text patterns for figures; respects reduced-motion; both themes meet contrast.

## 13. Content / data each design must accommodate (real data model)
Per paper: full title; short citable name; status (`published` | `submission-ready`); target venue; one **headline result** string; abstract; N figures (with captions); results tables / key metrics with confidence intervals; link to source code + frozen results; IEEE citation + BibTeX. The author across all papers is **Harshavardhan Malla, Independent Researcher** (no email shown).
Counts to design around: **21 papers, 1 published, ~3–8 tables and 1–6 figures per paper, 6–19 pages each.**

## 14. Hard constraints (please honor)
- Keep **deep-linking** to a paper and to a specific tab (URL drives state).
- Keep an **embedded PDF** view and a **separate readable manuscript** view (both matter).
- Keep **IEEE + BibTeX** citation export.
- **Both light and dark** themes delivered.
- **No author email** anywhere; author is always "Harshavardhan Malla · Independent Researcher."
- Tone: authoritative/academic. When in doubt, choose restraint.

## 15. Deliverables requested
1. Figma file with: landing, paper detail (each tab state), cite popover, and key components.
2. Light + dark for the above.
3. A tokens page (color, type, spacing, radius, motion) for both themes.
4. Mobile + desktop frames for the two core screens.
5. A short rationale note on the research-program module and the typographic system.

## 16. Inspiration / references (direction, not to copy)
- **arXiv / journal article pages** — seriousness, citation-first.
- **Stripe Press** — typographic care, restraint, both light/dark done well.
- **Distill.pub** — research clarity, figure/result presentation.
- **Linear / Vercel docs** — only for the *quality bar* of light/dark theming and component polish (not the startup tone).

---

### One-paragraph version (if your tool wants a single prompt)
> Design a credible, authoritative academic research portfolio for a single independent researcher (Harshavardhan Malla) presenting 21 rigorous, reproducible papers on cybersecurity. The site's purpose is to serve as evidence of extraordinary research ability for a US EB-1A petition, so it must read as serious and scholarly, not as a startup landing page. Deliver polished light AND dark themes, a restrained academic visual system (credible serif headings, strong typographic hierarchy, one accent color, generous whitespace, data-forward results), and two core screens: (A) a portfolio landing that conveys scope and a coherent research *program* with at-a-glance credibility stats, headline results per paper, and filter/sort/search; and (B) a paper-detail view with deep-linkable tabs (readable manuscript, embedded PDF, figures, frozen results, code) plus one-click IEEE + BibTeX citation. Keep deep-linking, never show an email, meet WCAG AA, and when in doubt choose restraint.
