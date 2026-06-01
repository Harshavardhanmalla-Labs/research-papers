# Submission Checklist

Updated through Phase 21. ☐ = open, ☑ = done, ◑ = partial.

| Item | Status | Notes |
| --- | --- | --- |
| Manuscript structurally complete? | ☑ | All Sections 1-17 + Abstract present in `paper_full_draft.md` and `paper_submission_draft.md`. |
| Citations verified? | ☐ | **0 independently verified in this environment.** Tier-1 drafted in `references.bib` with "CONFIRM at camera-ready"; must be checked against publishers. |
| Unverified citations remaining? | ☑ (tracked) | `[VERIFY]` retained for Deep VULMAN, VulRG, VulnScore, V-REx, Microsoft Defender VM, Tenable VPR/ACR, Qualys TruRisk, Cisco/Kenna, CJIS version, + Abstract numeric re-check. |
| Tables/figures generated? | ☑ | 7 tables (CSV/MD/LaTeX) + 5 figures (PNG/PDF) in `paper/tables/`, `paper/figures/`. |
| Tables/figures referenced + numbered? | ☑ | Numbered Table 1-6 (+ Supplementary A1) and Figure 1-5 in both drafts; mapping in `table_figure_index.md`. Physical placement in template still pending. |
| Freeze manifest verified? | ☑ | `make verify-primary-freeze` OK; provenance in `report_manifest.json` and `reproducibility_appendix.md`. |
| Claim safety clean? | ☑ | Extended 14-term scan: all occurrences safe/negated. See `claim_safety_audit.md` (Phase 21 update). |
| No confidential/employer data? | ☑ | Synthetic fleet + toy fixtures only. |
| No production-validation claims? | ☑ | Explicitly negated in §4, §11, §13, §14; "no production data". |
| Limitations explicit? | ☑ | Section 11 + Section 15. |
| Reproducibility artifact described? | ☑ | `reproducibility_appendix.md` + Appendix A in the submission draft; `docs/REPRODUCIBILITY.md`. Public-release statement in Future Work. |
| Negative/neutral findings disclosed? | ☑ | Abstract, §13.2/13.3/13.7, §14, §17. |
| Target venue selected? | ◑ | Recommended primary: **ACM DTRAP** (fallbacks IEEE Access, Computers & Security); see `venue_formatting_plan.md`. Final author decision pending. |
| Ready for formatting? | ☑ | Submission-style Markdown (`paper_submission_draft.md`) ready to port into a venue template. |
| Formatting template applied? | ☐ | Not yet (Markdown only). |
| Ready for submission? | ☐ | **No** — blocked on citation verification, template application, and the calibrated-weights decision. |
| Author/affiliation finalized? | ◑ | "Harshavardhan Malla, Independent Researcher"; confirm contact/ORCID at submission. |
| No EB1A/USCIS language in manuscript? | ☑ | None present. |
| Statistical tests applied to results? | ☐ | Helpers implemented but not applied (differences within noise); decide descriptive-only vs paired tests/CIs. |
| Calibrated-weights rerun before submission? | ☐ | **Decision needed** — placeholder weights used; a calibrated rerun likely strengthens any outcome but the paper is submittable as a benchmark/feasibility contribution without it. |

## Gating decision

The manuscript is **structurally complete and ready for venue formatting** as a
reproducible benchmark / framework paper with a neutral empirical result. It is
**not** ready for submission until: (1) all Tier-1 citations are confirmed against
publishers and the `[VERIFY]` works are resolved or removed; (2) a venue template
is applied with tables/figures placed; and (3) the calibrated-weights and
statistical-testing decisions are made.
