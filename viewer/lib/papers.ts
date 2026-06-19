// On a server: set PAPERS_ROOT env var to the absolute path where the
// research-papers repo is mounted (e.g. /data/research-papers).
// Locally it auto-resolves to the repo root two levels above viewer/.
import path from "path";
export const PAPERS_ROOT: string =
  process.env.PAPERS_ROOT ??
  path.resolve(__dirname, "..", "..", "..");

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
  {
    id: "paper6",
    title: "Capacity-Indexed Decay of Exploit-Likelihood Vulnerability Prioritization",
    shortTitle: "Capacity-Decay",
    subtitle: "Two-dimensional (K, λ) sweep characterising the regime-dependence of EPSS-only ranking",
    status: "complete",
    statusLabel: "Complete",
    root: "paper6",
    manuscript: {
      main: "manuscript/paper6_draft_v0.1.md",
      extras: [
        { label: "Protocol",        path: "design/PAPER6_PROTOCOL.md" },
        { label: "Artifact README", path: "README.md" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_sweep_v1",
      primaryCSV: "results/primary_sweep_v1/sweep_results.csv",
      secondaryCSVs: [
        { label: "Cell summary",          path: "results/primary_sweep_v1/cell_summary.csv" },
        { label: "Persistence",           path: "results/primary_sweep_v1/persistence.csv" },
        { label: "Hypothesis summary",    path: "results/primary_sweep_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_sweep_v1","submission/ieee"],
  },
  {
    id: "paper7",
    title: "Rolling-History Online Calibration for Hygiene-Augmented Vulnerability Prioritization",
    shortTitle: "Online-Calibration",
    subtitle: "Deployable lag-1 substitute for the offline-peek H3 ceiling: works at K≤100, harms at K=200",
    status: "complete",
    statusLabel: "Complete",
    root: "paper7",
    manuscript: {
      main: "manuscript/paper7_draft_v0.1.md",
      extras: [
        { label: "Protocol",                  path: "design/PAPER7_PROTOCOL.md" },
        { label: "Artifact README",           path: "README.md" },
        { label: "Supplementary experiments", path: "experiments/SUPPLEMENTARY.md" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/online_calib_results.csv",
      secondaryCSVs: [
        { label: "Cell-window means",   path: "results/primary_v1/cell_window_means.csv" },
        { label: "Hypothesis summary",  path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","experiments"],
  },
  {
    id: "paper8",
    title: "Multi-Window-History Calibration: Does Smoothing Reverse the High-Capacity Hazard of Lag-1?",
    shortTitle: "Smoothing-Falsified",
    subtitle: "EWMA-3 and trail-3 amplify Paper 7's K=200 hazard rather than fixing it — naive smoothing prior falsified",
    status: "complete",
    statusLabel: "Complete",
    root: "paper8",
    manuscript: {
      main: "manuscript/paper8_draft_v0.1.md",
      extras: [
        { label: "Protocol",        path: "design/PAPER8_PROTOCOL.md" },
        { label: "Artifact README", path: "README.md" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/multi_history_results.csv",
      secondaryCSVs: [
        { label: "Cell-window means",  path: "results/primary_v1/cell_window_means.csv" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee"],
  },
  {
    id: "paper9",
    title: "Self-Trajectory Evaluation of Hygiene-Augmented Vulnerability Prioritization",
    shortTitle: "Self-Trajectory",
    subtitle: "Paper 6's K=200 collapse re-attributed to closed-loop selection coupling + Closed-Loop Signal Exhaustion Theorem",
    status: "complete",
    statusLabel: "Complete",
    root: "paper9",
    manuscript: {
      main: "manuscript/paper9_draft_v0.1.md",
      extras: [
        { label: "Protocol",        path: "design/PAPER9_PROTOCOL.md" },
        { label: "Artifact README", path: "README.md" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/self_traj_results.csv",
      secondaryCSVs: [
        { label: "Cell means",        path: "results/primary_v1/cell_means.csv" },
        { label: "Hypothesis summary",path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee"],
  },
  {
    id: "paper10",
    title: "AutoHeal: A Pre-Registered Self-Healing Framework for Autonomous Vulnerability Remediation",
    shortTitle: "AutoHeal",
    subtitle: "Six-stage closed-loop pipeline integrating Papers 3–9 with pre-registered safety bounds — H1 ✓ / H2 ✗ / H3 N/A / H4 ✗",
    status: "complete",
    statusLabel: "Complete",
    root: "paper10",
    manuscript: {
      main: "manuscript/paper10_draft_v0.1.md",
      extras: [
        { label: "Protocol",        path: "design/PAPER10_PROTOCOL.md" },
        { label: "Artifact README", path: "README.md" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/autoheal_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee"],
  },

  /* ── PROGRAM B — Government / Practitioner (9 topics, not yet written) ── */
  {
    id: "paper11",
    title: "Context-Aware Vulnerability Prioritization for Government Endpoint Fleets",
    shortTitle: "GovVulnPrio",
    subtitle: "Exploit intelligence + asset criticality + endpoint telemetry for public-sector CVE prioritization",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper11",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper12",
    title: "NIST 800-53 as Code: Automated Evidence Collection for Continuous Public-Sector Compliance",
    shortTitle: "NIST-as-Code",
    subtitle: "Policy-as-code pipeline for automated NIST 800-53 evidence collection and continuous compliance monitoring",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper12",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper13",
    title: "CJIS Compliance Automation: A Policy-as-Code Framework for Law-Enforcement Endpoint Fleets",
    shortTitle: "CJIS-as-Code",
    subtitle: "Automated policy enforcement and audit trail generation for CJIS Security Policy across law-enforcement endpoints",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper13",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper14",
    title: "Patch Tuesday Intelligence: Predictive CVE Prioritization Using Exploit Signals and Asset Criticality",
    shortTitle: "PatchTuesday-Intel",
    subtitle: "Exploit signal fusion with asset criticality and endpoint telemetry for Patch Tuesday triage at scale",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper14",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper15",
    title: "Tanium + SCCM Fusion: Real-Time Vulnerability Heatmaps for State Agency Cyber Operations",
    shortTitle: "Tanium-SCCM",
    subtitle: "Unified telemetry fusion from Tanium and SCCM for real-time vulnerability heatmaps in state agency SOCs",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper15",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper16",
    title: "Machine Learning for Cyber Hygiene: Anomaly Detection Across AD, Endpoint, and Patch Telemetry",
    shortTitle: "ML-CyberHygiene",
    subtitle: "Supervised and unsupervised ML for multi-source hygiene anomaly detection in government endpoint environments",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper16",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper17",
    title: "PowerShell as Policy: Script-Based Guardrails for Large-Scale Government Endpoint Compliance",
    shortTitle: "PS-Policy",
    subtitle: "Declarative PowerShell guardrails for enforcing compliance baselines across large government endpoint fleets",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper17",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper18",
    title: "Disaster Recovery 2.0: Automated Failover Validation and Chaos Testing for Hybrid Government Infrastructure",
    shortTitle: "DR-2.0",
    subtitle: "Pre-registered chaos engineering framework for automated failover validation in hybrid government infrastructure",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper18",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
  },
  {
    id: "paper19",
    title: "Self-Healing CMDBs: AI-Driven Asset Intelligence for Public-Sector Security and Cost Optimization",
    shortTitle: "SelfHeal-CMDB",
    subtitle: "AI-driven CMDB reconciliation and self-healing for public-sector asset intelligence, security posture, and cost",
    status: "in-progress",
    statusLabel: "In Progress",
    root: "gov-paper19",
    manuscript: { main: "manuscript/draft.md" },
    figures: "figures",
    results: { dir: "results" },
    artifacts: [],
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
