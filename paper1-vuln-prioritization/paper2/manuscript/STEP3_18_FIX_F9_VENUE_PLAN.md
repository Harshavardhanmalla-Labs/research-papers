<!--
Paper 2 — Step 3.18: Fix F9 — Venue Plan and "Change Our Minds" Clause.
Locks the final framing, target venue + backups, the KILL/PIVOT/KEEP change-our-
minds clause, the Step-4 entry criteria, and the carried [VERIFY] citation
blockers. No code; no experiments; no F2..F8 changes; Paper 1 frozen outputs
untouched.
-->

# Paper 2 — Step 3.18: Fix F9 — Venue Plan and "Change Our Minds" Clause

**F9 status: COMPLETE.**
**Step 4 pre-registration: ALLOWED** (as a pre-registration document only — no
experiment execution; F1–F9 all complete; Step-3.10 framing changes committed
in §2 below; carried `[VERIFY]` items tracked in §6).

This document locks the manuscript framing the Step-4 pre-registration must use,
selects the publication venue + two backups, fixes the conditions that would
KILL / PIVOT / KEEP Paper 2, enumerates the entry criteria Step 4 must satisfy,
and tracks the three unresolved citation items.

---

## 1. Surviving novelty anchor (re-asserted, from Step 3.10 verbatim)

> "A failure-aware calibration-gate methodology — the multi-t0 distinct-positive-CVE
> gate with chunked / resumable / paced public-feed acquisition — applied to a
> public-sector-typical 31-product catalog over the EPSS v3 era, producing a
> documented negative result (7 unique positive Label-A CVEs over 18 monthly t0
> windows) that establishes when per-feature context-aware weight calibration on
> public-feed labels is not statistically justified. Confirmatory secondary
> sensitivity sweeps (capacity, blackout, feature-ablation, label-source) on a
> real-feed extension of a frozen synthetic-fleet benchmark situate the finding
> within the established sensitivity literature."

The Step-4 pre-registration's "contributions" section must restate that
sentence verbatim. No upgrade of the contribution scope is allowed.

---

## 2. Final framing changes (committed; carried into `STEP4_PREREGISTRATION.md`)

The Step-3.10 §9 list, ratified here:

1. **Drop** "Robustness of Context-Aware Vulnerability Prioritization …" as a
   title / abstract / Section-1 headline. (Replaced — see §3.)
2. **Elevate** the failure-aware multi-t0 calibration gate **+** the negative
   feasibility result as the *primary* contribution (C-primary).
3. **Demote** the four sensitivity sweeps (capacity / blackout / weight-vector /
   feature-ablation) to **confirmatory / secondary** contributions
   (C-secondary), citing prior art (Sherif 2026 KRI; VULCON 2018; Deep VULMAN
   2023; Roytman *Capacity is King*; Ravalico 2025 EPSS dynamics; Koscinski
   2025) as the comparators.
4. **Acknowledge the synthetic fleet** as a Limitations / Threats-to-Validity
   item, *not* a novelty. The eventual paper's Limitations section must include
   the literal sentence: "the synthetic fleet limits external validity; real-
   host generalisation is not claimed."
5. **Cite P1–P15** from Step-3.10's table with **visible differentiation** in
   the Related Work section — each cited paper must be followed by exactly one
   sentence stating what Paper 2 does *differently* (not just *additionally*).
6. **Drop** "fixed/published weights" wording everywhere. The correct phrase
   is "pre-registered design priors over fixed weight vectors" (per F2).
7. **No `[CITATION]` placeholders** in the eventual manuscript. Any reference
   not fully verified at manuscript stage must either be (a) re-verified
   inline, (b) replaced with the next-best verified source, or (c) removed
   entirely — never left as a placeholder.

The Step-3.14 K1 + K3 already-triggered status must appear in the
pre-registration's Abstract and §1 with the measured number (7 unique
positives) — not hidden, not paraphrased.

---

## 3. Title candidates (locked; one chosen for pre-registration, others held)

| # | Title | Notes |
|---|---|---|
| **1 (recommended)** | **"When Calibration Fails: A Failure-Aware Public-Feed Gate for Vulnerability Prioritization Under Sparse Exploit Labels"** | leads with the negative finding; "failure-aware gate" surfaces the methodological hook; "public-feed" + "sparse exploit labels" mark scope |
| 2 | "Sparse Exploit Labels and the Limits of Calibrated Vulnerability Prioritization" | leads with the empirical sparsity; quieter on the methodology contribution |
| 3 | "A Failure-Aware Methodology for Vulnerability Prioritization Under Public-Feed Label Sparsity" | leads with the methodology; the sparsity finding is the supporting evidence |

Step-4 pre-registration uses **Title #1**. Titles #2 and #3 are held as
alternates for venue-fit considerations (workshop blurb / single-line CFP) and
may be selected at submission time without a new fix; substantive subtitle
changes require a Step-3.18.1 supplement.

---

## 4. Venue strategy

### 4.1 Primary target — **USENIX CSET** (Workshop on Cyber Security Experimentation and Test)

| Field | Value |
|---|---|
| Name | USENIX CSET (Cyber Security Experimentation and Test) |
| Fit | **Strong**. CSET explicitly seeks work on "reliability, validity, reproducibility, and scalability in cybersecurity research" (verified in workshop scope summary). A failure-aware calibration gate that says *when* per-feature weight calibration is not statistically justified is a methodological / reproducibility contribution that maps cleanly to the workshop's stated charter. |
| Risk | Acceptance competitiveness varies year to year; CSET selectivity is reasonable but not guaranteed for negative-result papers. The 2026 cycle's exact deadlines and proceedings format are not yet public. |
| Format / page limit | typically ~10 pages USENIX 2-column `[VERIFY]` from the specific year's CFP at submission time |
| Why neutral/negative fits | CSET's charter explicitly covers experiment validity and methodology; a negative feasibility result + a documented gate is exactly the kind of paper this workshop publishes. |
| Required next formatting step | Use the standard USENIX `.tex` template when the year's CFP confirms it. Do **not** start LaTeX work until Step 4 / pre-registration completes. |
| URL / CFP | Workshop landing page: https://www.usenix.org/conferences/byname/135 (workshop series) `[VERIFY 2026 cycle URL]` |

### 4.2 Backup 1 — **LASER** (Learning from Authoritative Security Experiment Results)

| Field | Value |
|---|---|
| Name | LASER — Learning from Authoritative Security Experiment Results |
| Fit | **Strong**. LASER's stated mission is to "improve the overall quality and reporting of practiced science" in security and to discuss "experimental methodologies, execution, and results" — directly aligned with a negative feasibility finding + a methodological gate. |
| Risk | Smaller venue; co-location pattern (NDSS / ACSAC) means the 2026 colocation is not yet definite. |
| Format / page limit | typically short workshop-paper format `[VERIFY at submission time]` |
| Why neutral/negative fits | LASER explicitly accepts null and negative results and emphasises rigorous reporting. |
| URL | Recent edition pages: https://www.ndss-symposium.org/ndss2023/co-located-events/laser/ (2023), https://sphere-project.net/events/5846/learning-from-authoritative-security-experiment-results-workshop-2025/ (2025 at ACSAC) `[VERIFY 2026 colocation + CFP URL]` |

### 4.3 Backup 2 — **ACM Digital Threats: Research and Practice (DTRAP)**

| Field | Value |
|---|---|
| Name | ACM Digital Threats: Research and Practice (DTRAP) |
| Fit | **Medium-strong**. DTRAP is a journal that explicitly publishes measurement / methodology / applied-security work; the foundational EPSS paper (Jacobs et al., DTRAP 2021, doi 10.1145/3436242) landed here. |
| Risk | Journal review tends to be longer than workshop; the surviving novelty may be considered narrow by reviewers expecting either a measurement at-scale or a new model. |
| Format / page limit | journal format (no fixed page limit; expects a complete contribution) |
| Why neutral/negative fits | DTRAP's scope explicitly includes empirical security measurements and methodology — a documented public-feed sparsity finding + a reusable failure-aware gate fits. |
| URL | https://dl.acm.org/journal/dtrap (journal home) `[VERIFY current author guidelines + open-call status]` |

### 4.4 Venues considered and rejected (transparency)

| Venue | Why not |
|---|---|
| USENIX Security / IEEE S&P / ACM CCS / NDSS (top tier) | Step-3.10 honest assessment: top-tier venues are unlikely to accept a sensitivity / negative-feasibility / methodology paper without a larger empirical lift than this work attempts. Listed for completeness; not pursued. |
| WOOT (Offensive Technologies) | Attack-focused; wrong scope. |
| EuroUSEC / SOUPS | Usable security; wrong scope. |
| MLHat (KDD) | Expects a positive ML result; our finding is the opposite. |
| WTMC | Traffic-measurement focus; only tangentially related to vulnerability-prioritization sparsity. |
| arXiv-only | Preprint hosting is a valid intermediate step but is not a peer-reviewed venue and cannot, on its own, satisfy the Paper-2 publishability claim. arXiv may host a preprint *in parallel* with venue submission. |

### 4.5 Honest disclosure

If CSET 2026 and LASER 2026 both fail to materialise (CFPs not opened, or
acceptance miss) and DTRAP review pushes back on novelty, the surviving
options shrink to (a) a smaller security/measurement workshop yet to be
identified, (b) a longer DTRAP revision cycle, or (c) **invoke KILL clause
A.1** below. The venue strategy does *not* depend on inventing a venue that
does not exist; failure to find a home is a real outcome that must be reported
honestly to the user.

---

## 5. Change-our-minds clause (KILL / PIVOT / KEEP)

This section enumerates the precise conditions that flip the Paper-2 decision
*after* Step 4 begins. Each condition has a trigger that is computable from
existing artefacts; none of them are vague review-style judgments.

### 5.1 KILL conditions (any one → abandon Paper 2)

| ID | Trigger | Action |
|---|---|---|
| **K9-KILL-A.1** (venue) | F9 venue search and 2 follow-on attempts find **no plausible home** for a negative / methodology result (CSET + LASER + DTRAP all return reject decisions in the same submission cycle) | KILL Paper 2; do **not** rewrite for a stretch-fit venue |
| **K9-KILL-A.2** (compute) | Pilot runtime measurement gives a projected primary runtime that **exceeds F8 hard max even after the full F8-e → F8-a fallback escalation** (F8-a halves seeds; if that still doesn't fit 18 h, the design is infeasible on the available hardware) | KILL Paper 2 unless explicit user OK to expand the compute envelope |
| **K9-KILL-A.3** (K2 + judgment) | K2 fires on **every** primary axis **and** an independent reviewer regards the negative finding as "trivial" (i.e., the failure-aware-gate methodology is rejected as "standard ML feasibility analysis") | KILL Paper 2; the surviving novelty has collapsed |
| **K9-KILL-A.4** (degeneracy) | Sparsity makes **every** outcome degenerate (per-cell paired-Δ identically zero on every primary cell, every sensitivity axis, every metric — beyond `kev_first` alone) | KILL Paper 2; nothing to report beyond the sparsity figure itself |
| **K9-KILL-A.5** (insight) | After the primary completes, the paper produces **no meaningful difference and no methodological insight** beyond Step 3.8's sparsity number itself, and that number alone is insufficient for *any* of the §4 venues | KILL Paper 2 |
| **K9-KILL-A.6** (prior art) | A *later-discovered* prior-art source (post-F1) is found to publish the same failure-aware gate methodology under public-feed labels with a comparable sparsity figure | KILL Paper 2 unless a sharper differentiation can be written without inventing novelty |

### 5.2 PIVOT conditions (any one → reshape, not abandon)

| ID | Trigger | Action |
|---|---|---|
| **K9-PIVOT-B.1** | Pilot runs end-to-end but all sensitivity Δs are effectively zero (every primary axis fires K2 / K8) | Paper becomes pure "failure-aware methodology + sparsity number" — drop the sensitivity tables to an appendix; manuscript is shorter / methodology-focused |
| **K9-PIVOT-B.2** | Catalog expansion turns out to be necessary to make any sensitivity claim meaningful — but catalog expansion is **deferred** by Step 3.9 / F6 | Pivot to a Paper-2.5 / Paper-3 catalog-expansion preregistration; Paper 2 publishes as currently scoped only if the failure-aware gate alone holds up |
| **K9-PIVOT-B.3** | `epss_only` dominates every fixed-prior cell with no stability insight remaining | Pivot the headline to *"EPSS-only is hard to beat with fixed context-aware weights at this sparsity"* — an honest but smaller-impact finding; sensitivity sweeps become the supporting evidence rather than the claim |
| **K9-PIVOT-B.4** | Only the acquisition pipeline + decision-gate methodology is publishable; everything downstream is degenerate | Pivot to an artefact/methodology paper (potentially DTRAP) focused on the reproducible public-feed acquisition + gate; drop sensitivity narrative entirely |

### 5.3 KEEP conditions (all must hold to keep the current pivot intact)

| ID | Condition |
|---|---|
| **K9-KEEP-C.1** | Failure-aware gate **remains novel enough** under post-F1 spot checks (no later-discovered prior art duplicates it) |
| **K9-KEEP-C.2** | Pilot confirms primary runtime feasible (projected ≤ 18 h or fallback fits) |
| **K9-KEEP-C.3** | At least one primary / secondary sensitivity axis (A1 capacity / A3 weight vector / A5 ablation / A6 blackout) yields either *interpretable variation* (Δ > meaningful threshold with CI) *or* a *useful negative result* (K2-style "all axes equivalent" framed as a finding) |
| **K9-KEEP-C.4** | Stop-rule framework (F5 + F7) produces a reproducible methodological artefact — runnable by an outside reader against the same public feeds (verified by Step-4 reproducibility appendix) |
| **K9-KEEP-C.5** | Venue fit remains plausible — CSET / LASER / DTRAP review cycle accepts the framing without forcing a superiority claim, a calibration claim, or a real-host generalisation |

A KILL or PIVOT trigger is recorded in `PAPER2_DECISION_LOG.md` immediately
when it fires; KEEP is the default. No KEEP claim survives a violated KEEP
condition.

---

## 6. Carried `[VERIFY]` items (re-verification attempts + remaining blockers)

| Item | Status | Notes / next action |
|---|---|---|
| VULCON DOI **10.1145/3196884** (Farris et al., ACM TOPS 21(4), 2018) | `[VERIFY-DOI]` retained | Re-attempt at manuscript stage; ACM DL page returned HTTP 403 in two attempts (Step 3.10, Step 3.18 not re-attempted). DOI string is widely cross-referenced; the canonical record will be visible at submission via ACM's institutional access. Block on confirming year + page numbers before final manuscript. |
| NIST CSWP 41 — Likely Exploited Vulnerabilities (LEV) | `[VERIFY]` partial | URL `https://nvlpubs.nist.gov/nistpubs/cswp/NIST.CSWP.41.pdf` confirmed to return a real PDF this turn (981 KB) but the WebFetch text-extraction returned corrupted/unparseable content. The URL is real; the title-and-authors confirmation must be done by a human reader at manuscript stage. |
| VulnScore (Alqahtani & Almukaynizi, Springer IJIS 2025, **10.1007/s10207-025-01164-3**) | `[VERIFY]` retained | Not re-fetched this turn; used only as soft-context in Step-3.11 F2 table for composite-scoring framing. If retained in Paper 2's Related Work, re-verify at submission. |
| CSET 2026 / LASER 2026 colocation + CFP URLs | `[VERIFY at submission time]` | Venue series is real (CSET in USENIX system since 2008; LASER since ~2014). 2026-specific CFP URLs are not yet public. Tracked here; re-verified before any submission. |

None of these block F9. All four are re-verified or replaced before any final
manuscript text is produced (per §2.7 — "no `[CITATION]` placeholders").

---

## 7. Step-4 entry criteria (all must hold)

Step 4 pre-registration may begin **iff every one** of the following holds:

| # | Criterion | Source |
|---|---|---|
| 1 | F9 complete | this file |
| 2 | Decision log says F1–F9 all complete | `PAPER2_DECISION_LOG.md` |
| 3 | Step-4 pre-registration document includes the §2 framing changes verbatim | F1 / Step 3.10 §9 |
| 4 | Pre-registration cites or queues P1–P15 with visible differentiation | F1 / Step 3.10 table |
| 5 | Pre-registration does **not** add new metrics / axes / weights | F3 / F4 / F5 / F6 immutable |
| 6 | Pre-registration adopts the F8-f pilot-then-primary plan, with the F8 fallback order verbatim | F8 / `STEP3_17_PLANNED_BATCHES.yaml` |
| 7 | Pre-registration includes K1 + K3 **already-triggered** status with the measured number (7 unique positive CVEs) in the abstract and §1 | F5 |
| 8 | Pre-registration contains **no learned / calibrated model claims** | K1 forbid-list |
| 9 | Pre-registration commits to the §3 title (Title #1 or held alternates #2/#3) | this file |
| 10 | Pre-registration includes the §5 change-our-minds clause verbatim | this file |
| 11 | Pre-registration declares Step-4 produces a **document only** — no experiment execution, no code | task brief |

Failure of any of 1–11 keeps Step 4 blocked until the missing item is
resolved with a written supplement and a decision-log row.

---

## 8. Implementation implications for Step 4 (PRE-REGISTRATION DOCUMENT ONLY)

When Step 4 begins, the deliverable is exactly one file:
`paper2/manuscript/STEP4_PREREGISTRATION.md`. It must contain:

1. **Title** (one of §3); **Abstract** that surfaces the negative finding (7
   unique positives) and the failure-aware gate as the contribution;
   **Authors** placeholder (real authorship deferred to manuscript stage).
2. **Surviving novelty statement** (§1 verbatim).
3. **Framing changes** (§2 items 1–7 each ticked off with a one-line statement
   of how the eventual paper will honor them).
4. **Title decision** (§3 chosen title locked, alternates listed).
5. **Venue strategy** (§4 verbatim, with `[VERIFY at submission time]`
   markers preserved).
6. **Change-our-minds clause** (§5 verbatim — KILL A.1–A.6, PIVOT B.1–B.4,
   KEEP C.1–C.5).
7. **Pre-registered design** referencing F2 weight vectors, F3 metric→claim
   bindings, F4 MDE table + inference-status, F5 stop-rule registry, F6 cell
   enumeration, F7 freeze-invariant contract, F8 planned-batches +
   pilot-gate; the pre-registration **does not duplicate** those documents,
   only references them.
8. **Step-5 entry conditions** — explicit handoff to the Step-4 implementation
   step ("Step 5: implement the runner per F2–F8 invariants; experiments
   remain not-yet-run until Step 6 pilot launch").
9. **Carried `[VERIFY]` blocker list** (§6 verbatim).
10. **No `[CITATION]` placeholders** — every citation either resolved or
    queued for re-verification with a tracked task entry.

Step 4 produces no code, runs no experiment, modifies no Paper-1 frozen
output, and changes no F2–F8 binding.

---

## 9. F9 status & decision-flow summary
- **F9: COMPLETE.** Framing locked; titles chosen + alternates; primary venue
  + 2 backups identified with honest fit/risk; KILL / PIVOT / KEEP clause
  enumerated with computable triggers; Step-4 entry criteria locked at 11
  items; carried `[VERIFY]` items tracked with explicit re-verification
  triggers; Step-4 implementation implications committed.
- **Step 4 pre-registration:** **ALLOWED** (document-only; no experiment
  execution; pre-registration deliverable is exactly
  `paper2/manuscript/STEP4_PREREGISTRATION.md`).

## Invariants honored
Paper 1 frozen outputs untouched. No experiments; no code; no F2/F3/F4/F5/F6/F7/F8
changes. No calibration claim; no superiority claim. The calibration-feasibility
claim remains anchored to unique positive distinct CVEs (Step-3.8: 7 < 20). PoC
license-gated and off. No fabricated citations (`[VERIFY]` / `[VERIFY-DOI]` /
`[VERIFY at submission time]` retained where appropriate).
