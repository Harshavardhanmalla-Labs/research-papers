// Repository root, relative to where the viewer runs (the `viewer/` directory).
// Paths built from this are resolved server-side against the app's working
// directory, so the portal works on ANY machine and clone location — no
// hardcoded user path. Override with NEXT_PUBLIC_PAPERS_ROOT if needed.
export const PAPERS_ROOT = process.env.NEXT_PUBLIC_PAPERS_ROOT ?? "..";

export type PaperStatus = "complete" | "drafting" | "packaging" | "in-progress";

export interface ResultsConfig {
  dir: string;
  primaryCSV?: string;
  secondaryCSVs?: { label: string; path: string }[];
}

export interface Paper {
  id: string;
  title: string;
  shortTitle: string;
  subtitle: string;
  status: PaperStatus;
  statusLabel: string;
  root: string;
  manuscript: {
    main: string;
    supplemental?: string;
    extras?: { label: string; path: string }[];
  };
  submissionPdf?: string;
  figures: string;
  results: ResultsConfig;
  artifacts: string[];
}

export const PAPERS: Paper[] = [
  {
    id: "paper1",
    title: "Evidence-Based Vulnerability Prioritization",
    shortTitle: "VulnPrio",
    subtitle: "Exploit likelihood, healthcare data, & EPSS-weighted ranking",
    status: "packaging",
    statusLabel: "Packaging",
    root: "paper1-vuln-prioritization",
    manuscript: {
      main: "paper/manuscript/paper_submission_draft.md",
      supplemental: "paper/manuscript/reproducibility_appendix.md",
      extras: [
        { label: "Full draft",           path: "paper/manuscript/paper_full_draft.md" },
        { label: "Citation audit",       path: "paper/manuscript/citation_audit.md" },
        { label: "Claim safety audit",   path: "paper/manuscript/claim_safety_audit.md" },
        { label: "Submission checklist", path: "paper/manuscript/submission_checklist.md" },
      ],
    },
    submissionPdf: "paper/submission/ieee/main.pdf",
    figures: "paper/figures",
    results: {
      dir: "results/primary_full_v1",
      primaryCSV: "results/primary_full_v1/metrics/aggregated_metrics.csv",
      secondaryCSVs: [
        { label: "Per-seed metrics", path: "results/primary_full_v1/metrics/per_seed_metrics.csv" },
        { label: "EEHDA report",     path: "results/primary_full_v1/metrics/eehda_report.csv" },
      ],
    },
    artifacts: ["paper/manuscript","paper/figures","paper/tables","results/primary_full_v1","src","design"],
  },
  {
    id: "paper2",
    title: "When Calibration Fails",
    shortTitle: "CalibScore",
    subtitle: "Failure-aware public-feed gate for vulnerability prioritization under sparse exploit labels",
    status: "packaging",
    statusLabel: "Packaging",
    root: "paper1-vuln-prioritization/paper2",
    manuscript: {
      main: "manuscript/paper2_full_draft.md",
      supplemental: "manuscript/STEP11_CLOSEOUT.md",
      extras: [
        { label: "Decision log",      path: "manuscript/PAPER2_DECISION_LOG.md" },
        { label: "Step 1 validation", path: "manuscript/STEP1_RESEARCH_VALIDATION.md" },
        { label: "Step 2 feasibility",path: "manuscript/STEP2_DATA_FEASIBILITY.md" },
        { label: "Pre-registration",  path: "manuscript/STEP4_PREREGISTRATION.md" },
        { label: "Venue CFP status",  path: "manuscript/VENUE_CFP_STATUS.md" },
      ],
    },
    submissionPdf: "submission/cset/main.pdf",
    figures: "figures",
    results: {
      dir: "results/B-primary-primary",
      primaryCSV: "results/B-primary-primary/per_seed_metrics.csv",
      secondaryCSVs: [
        { label: "Downgraded claims", path: "results/B-primary-primary/downgraded_claims.csv" },
        { label: "Triggered rules",   path: "results/B-primary-primary/triggered_rules.csv" },
        { label: "Excluded cells",    path: "results/B-primary-primary/excluded_cells.csv" },
      ],
    },
    artifacts: ["manuscript","figures","results","design","audit"],
  },
  {
    id: "paper3",
    title: "HygieneBench",
    shortTitle: "HygBench",
    subtitle: "Reproducible synthetic benchmark for cyber-hygiene anomaly detection",
    status: "packaging",
    statusLabel: "Packaging",
    root: "paper3",
    manuscript: {
      main: "manuscript/paper_draft_v0.1.md",
      supplemental: "manuscript/supplemental_appendix_v0.1.md",
      extras: [
        { label: "Decision log",           path: "manuscript/PAPER3_DECISION_LOG.md" },
        { label: "Submission checklist",   path: "manuscript/PAPER3_SUBMISSION_CHECKLIST.md" },
        { label: "Figure quality check",   path: "manuscript/FIGURE_QUALITY_CHECK.md" },
        { label: "Repo release checklist", path: "REPOSITORY_RELEASE_CHECKLIST.md" },
        { label: "GitHub README",          path: "README.md" },
      ],
    },
    submissionPdf: "submission/acm/main.pdf",
    figures: "manuscript/figures",
    results: {
      dir: "results/primary_full_v1",
      primaryCSV: "results/primary_full_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Failure flags",  path: "results/primary_full_v1/failure_flags.csv" },
        { label: "Rank stability", path: "results/primary_full_v1/rank_stability.csv" },
      ],
    },
    artifacts: ["manuscript","src","datasets","results/primary_full_v1","design","submission/acm"],
  },
  {
    id: "paper4",
    title: "HygienePrio: Cyber-Hygiene Signal Augmentation for EPSS-Weighted Vulnerability Prioritization",
    shortTitle: "HygienePrio",
    subtitle: "Integrating patch posture, AD exposure & telemetry freshness into exploit-weighted scoring",
    status: "packaging",
    statusLabel: "Packaging",
    root: "paper4",
    manuscript: {
      main: "manuscript/paper4_draft_v0.1.md",
      extras: [
        { label: "Protocol",     path: "design/PAPER4_PROTOCOL.md" },
        { label: "Decision log", path: "manuscript/PAPER4_DECISION_LOG.md" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "manuscript/figures",
    results: {
      dir: "results/primary_results_v1",
      primaryCSV: "results/primary_results_v1/primary_results.csv",
    },
    artifacts: ["manuscript","src","design","results"],
  },
  {
    id: "paper5",
    title: "Temporal Stability of Hygiene-Augmented Vulnerability Prioritization Across Rolling Maintenance Windows",
    shortTitle: "HygienePrio-Temporal",
    subtitle: "EPSS-only decays, hygiene signals persist: a six-window pre-registered evaluation",
    status: "packaging",
    statusLabel: "Packaging",
    root: "paper5",
    manuscript: {
      main: "manuscript/paper5_draft_v0.1.md",
      extras: [
        { label: "Protocol", path: "design/PAPER5_PROTOCOL.md" },
        { label: "Artifact README", path: "README.md" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_full_v1",
      primaryCSV: "results/primary_full_v1/temporal_results.csv",
      secondaryCSVs: [
        { label: "Recalibration ablation", path: "results/primary_full_v1/recalibration_ablation.csv" },
        { label: "Recalibration summary",  path: "results/primary_full_v1/recalibration_summary.json" },
        { label: "Run manifest",           path: "results/primary_full_v1/run_manifest.json" },
      ],
    },
    artifacts: ["manuscript","src","design","submission/ieee","results"],
  },
];

/* ─────────────────────────────────────────────────────────
   Status badge colours — proper light AND dark variants
   light: bg-{colour}-100 text-{colour}-800 border-{colour}-300
   dark:  bg-{colour}-900/50 text-{colour}-300 border-{colour}-700
   ───────────────────────────────────────────────────────── */
export const STATUS_COLORS: Record<PaperStatus, string> = {
  complete:
    "bg-emerald-100  text-emerald-800  border-emerald-300 " +
    "dark:bg-emerald-900/50 dark:text-emerald-300 dark:border-emerald-700",
  packaging:
    "bg-indigo-100   text-indigo-800   border-indigo-300  " +
    "dark:bg-indigo-900/50  dark:text-indigo-300  dark:border-indigo-700",
  drafting:
    "bg-amber-100    text-amber-800    border-amber-300   " +
    "dark:bg-amber-900/50   dark:text-amber-300   dark:border-amber-700",
  "in-progress":
    "bg-sky-100      text-sky-800      border-sky-300     " +
    "dark:bg-sky-900/50     dark:text-sky-300     dark:border-sky-700",
};
