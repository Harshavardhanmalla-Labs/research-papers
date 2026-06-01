# Paper 1 — Next Actions

Concrete, ordered manual steps. Nothing here is started in Phase 22A.

## A. Before submission (manuscript)

1. **Verify citations.** Confirm each Tier-1 entry in `paper/acm/references.bib`
   against the publisher; fill any missing fields. Resolve every `[VERIFY: ...]`
   marker (Deep VULMAN, VulRG, VulnScore, Microsoft Defender VM, Tenable VPR/ACR,
   Qualys TruRisk, Cisco/Kenna) with a real reference, or soften/remove (V-REx,
   exact CJIS version). Do not fabricate.
2. **Decide calibrated-weights vs neutral-benchmark framing** (see
   `PAPER1_BLOCKERS.md` item 3). If calibrating: add a new controlled run + freeze +
   inspect + regenerate tables/figures in a *new* results directory; never modify
   `results/primary_full_v1/`.
3. **Compile the ACM build.** Install a TeX distribution with `acmart`; run
   `latexmk -pdf paper/acm/main.tex`; fix table widths, add CCS concepts, set
   rights/venue, add author country/email/ORCID.
4. **Re-verify numbers** in the compiled PDF against the frozen tables
   (`results/primary_full_v1/report/tables/`) — they were re-verified in Phase 22A;
   reconfirm after any calibrated rerun.
5. **Choose venue** (recommended ACM DTRAP) and apply its exact submission template
   and length/format rules.
6. **Final claim-safety pass** on the compiled PDF (same 14-term scan).

## B. For an EB1A evidence package (DEFERRED — do not embed in the paper)

- This is out of scope for the manuscript and must stay out of the paper text.
- Prerequisite: a submitted and ideally peer-reviewed/published artifact plus
  independent external evidence.
- When undertaken separately: collect submission/acceptance records, citation/usage
  evidence, and an independent reproducibility statement — assembled in a *separate*
  package, never inside the manuscript.

## C. For Paper 2 reuse

- Reuse the existing infrastructure without disturbing Paper 1's frozen result:
  feed clients + snapshot cache (`src/paper1/feeds/`), synthetic generator
  (`src/paper1/synthetic/`), scheduler + audit log (`src/paper1/scheduler/`,
  `audit/`), evaluation + statistics (`src/paper1/evaluation/`), reporting
  (`src/paper1/reporting/`), and the controlled-run + freeze/verify protocol
  (`src/paper1/experiments/`).
- Start Paper 2 in its own results namespace (e.g. a new `results/` subtree and
  config) so Paper 1's `results/primary_full_v1/` freeze remains untouched.
- Candidate Paper 2 directions already implied by Future Work: calibrated-weights
  study, Label B robustness, sensitivity sweeps, or point-in-time public-feed
  snapshots.
