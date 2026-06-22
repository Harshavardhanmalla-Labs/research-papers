// PAPERS_ROOT must be IDENTICAL on the server (API route security check in
// app/api/{file,serve,tree}/route.ts) and on the client (absolute paths built in
// PdfViewer / ManuscriptViewer). Next.js only inlines NEXT_PUBLIC_* env vars into the
// client bundle, so set NEXT_PUBLIC_PAPERS_ROOT at build time and PAPERS_ROOT at runtime
// to the SAME path.
export const PAPERS_ROOT: string =
  process.env.NEXT_PUBLIC_PAPERS_ROOT ||
  process.env.PAPERS_ROOT ||
  "/home/sasi/Desktop/dev/RM Orbit/research-papers";

export type PaperStatus = "published" | "ready" | "complete" | "drafting" | "packaging" | "in-progress";

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
    shortTitle: "EvidencePrio",
    subtitle: "Exploit likelihood, healthcare data, & EPSS-weighted ranking",
    status: "ready",
    statusLabel: "Ready for Publication",
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
      dir: "paper/tables",
      primaryCSV: "paper/tables/table_primary_metric_summary.csv",
      secondaryCSVs: [
        { label: "Ranking metrics",     path: "paper/tables/table_ranking_metrics.csv" },
        { label: "Operational metrics", path: "paper/tables/table_operational_metrics.csv" },
        { label: "Audit metrics",       path: "paper/tables/table_audit_metrics.csv" },
      ],
    },
    artifacts: ["paper/manuscript","paper/figures","paper/tables","src","design"],
  },
  {
    id: "paper2",
    title: "When Calibration Fails",
    shortTitle: "CalibGate",
    subtitle: "Failure-aware public-feed gate for vulnerability prioritization under sparse exploit labels",
    status: "ready",
    statusLabel: "Ready for Publication",
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
    status: "ready",
    statusLabel: "Ready for Publication",
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
    status: "ready",
    statusLabel: "Ready for Publication",
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
    shortTitle: "HygieneTempo",
    subtitle: "EPSS-only decays, hygiene signals persist: a six-window pre-registered evaluation",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "archived/HygieneContinuation_Paper5_TemporalStability",
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
    shortTitle: "CapDecay",
    subtitle: "Two-dimensional (K, λ) sweep characterising the regime-dependence of EPSS-only ranking",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "archived/HygieneContinuation_Paper6_CapacityDecay",
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
    shortTitle: "RollCal",
    subtitle: "Deployable lag-1 substitute for the offline-peek H3 ceiling: works at K≤100, harms at K=200",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "archived/HygieneContinuation_Paper7_OnlineRecalibration",
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
    shortTitle: "SmoothTest",
    subtitle: "EWMA-3 and trail-3 amplify Paper 7's K=200 hazard rather than fixing it; naive smoothing prior falsified",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "archived/HygieneContinuation_Paper8_Smoothing",
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
    shortTitle: "SelfTraj",
    subtitle: "Paper 6's K=200 collapse re-attributed to closed-loop selection coupling + Closed-Loop Signal Exhaustion Theorem",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "archived/HygieneContinuation_Paper9_SelfTrajectory",
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
    subtitle: "Six-stage closed-loop pipeline integrating Papers 3 to 9 with pre-registered safety bounds: H1 ✓ / H2 ✗ / H3 N/A / H4 ✗",
    status: "ready",
    statusLabel: "Ready for Publication",
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
  {
    id: "paper11",
    title: "Context-Aware Vulnerability Prioritization for Government Endpoint Fleets",
    shortTitle: "CAP-G",
    subtitle: "Asset criticality + network zone + data sensitivity layered on HygienePrio: +9.5pp mission precision at triage, H1 partial / H2 ✓ / H3 ✓ / H4 ✓",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper11",
    manuscript: {
      main: "manuscript/paper11_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER11_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Cell means",          path: "results/primary_v1/cell_means.csv" },
        { label: "Homogeneous control", path: "results/primary_v1/homogeneous_control.csv" },
        { label: "Hypothesis summary",  path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper12",
    title: "NIST 800-53 as Code: Quantifying the Compliance-Exposure Reduction of Continuous Automated Evidence Collection and Its Automatability Ceiling",
    shortTitle: "ComplianceCeiling",
    subtitle: "Continuous monitoring cuts drift detection on automatable controls from 272 days to 1, but the un-automatable remainder caps overall reduction at the automatable share. H1-H4 all supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper12",
    manuscript: {
      main: "manuscript/paper12_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER12_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper13",
    title: "Policy-as-Code for CJIS Compliance: Prevention versus Detection for Recurring Control Violations on Law-Enforcement Endpoint Fleets",
    shortTitle: "PolicyGate",
    subtitle: "Preventive guardrails cut CJI exposure 70% over detection, growing to 81% as violations recur, while the false-block cost stays fixed. H1-H4 all supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper13",
    manuscript: {
      main: "manuscript/paper13_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER13_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper14",
    title: "Patch Tuesday Triage: Asset Criticality, Not Early Exploit Signal, Drives Emergent-Risk Vulnerability Prioritization on Government Fleets",
    shortTitle: "PTI",
    subtitle: "At disclosure time, asset criticality drives mission precision (+6.5pp) while the immature day-0 EPSS adds almost nothing. H1-H4 all supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper14",
    manuscript: {
      main: "manuscript/paper14_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER14_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper15",
    title: "Fusing Real-Time and Scheduled Endpoint Telemetry for Vulnerability Visibility: Coverage Gains, the Freshness Mechanism, and the Blind-Spot Floor",
    shortTitle: "FusionView",
    subtitle: "Fusing a real-time and a scheduled endpoint feed lifts vuln recall 0.75 to 0.87; the gain is exactly the scheduled-only fresh coverage, bounded by the blind-spot floor. H1-H4 all supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper15",
    manuscript: {
      main: "manuscript/paper15_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER15_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper16",
    title: "Multivariate Machine Learning for Cyber-Hygiene Anomaly Detection Across Active Directory, Endpoint, and Patch Telemetry",
    shortTitle: "HygieneAD",
    subtitle: "Joint detection beats per-feature rules by +0.61 AP on cross-channel anomalies but loses on single-channel ones; Isolation Forest fails where Mahalanobis wins. H1-H4 all supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper16",
    manuscript: {
      main: "manuscript/paper16_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER16_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper17",
    title: "Ring Rollout of Script-Based Endpoint Enforcement: Bounding the Blast Radius of a Faulty Policy at a Quantified Convergence Cost",
    shortTitle: "RingGuard",
    subtitle: "A four-ring rollout cuts a faulty enforcement script's blast radius 95% at a fixed soak cost; containment scales with canary observability, with diminishing returns to finer staging. H1-H4 supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper17",
    manuscript: {
      main: "manuscript/paper17_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER17_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper18",
    title: "The Drill Illusion: Latent Failover-Defect Decay and the Recovery-Confidence Gain of Continuous Chaos Testing in Hybrid Government Infrastructure",
    shortTitle: "DrillGap",
    subtitle: "Annual DR drills overstate real recovery confidence by 31 points (0.69 true vs ~1.0 at drill); continuous chaos lifts it to 0.95, bounded by coverage. H1-H4 all supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper18",
    manuscript: {
      main: "manuscript/paper18_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER18_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper19",
    title: "The Two-Sided Cost of CMDB Error: Ghost Assets, Phantom Assets, and the Matching-Precision Ceiling of Self-Healing Reconciliation",
    shortTitle: "ReconGuard",
    subtitle: "Continuous reconciliation cuts CMDB error 78%; ghost (security) and phantom (cost) errors trade off via retirement aggressiveness, bounded by a matching-precision floor. H1-H4 all supported.",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper19",
    manuscript: {
      main: "manuscript/paper19_draft_v0.1.md",
      extras: [
        { label: "Protocol",          path: "design/PAPER19_PROTOCOL.md" },
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
        { label: "Run manifest",       path: "results/primary_v1/run_manifest.json" },
      ],
    },
    submissionPdf: "submission/ieee/main.pdf",
    figures: "submission/ieee/figures",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Hypothesis summary", path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["design","src","results/primary_v1","submission/ieee","manuscript"],
  },
  {
    id: "paper20",
    title: "A Context-Aware Ensemble Learning Framework for Vulnerability Prioritization in Critical Infrastructure",
    shortTitle: "EnsemblePrio",
    subtitle: "Random Forest + XGBoost ensemble fusing CVE metadata, threat intelligence, and environmental context; on a reproducible, pre-registered synthetic 50,000-endpoint benchmark (25 seeds) it reaches Precision@50 0.74 vs 0.22 for CVSS-only and cuts MTTR 62% (6.2 to 2.3 days). All 5 pre-registered hypotheses supported (BCa CIs exclude zero).",
    status: "ready",
    statusLabel: "Ready for Publication",
    root: "paper20",
    manuscript: {
      main: "manuscript/paper20.md",
    },
    submissionPdf: "submission/main.pdf",
    figures: "",
    results: {
      dir: "results/primary_v1",
      primaryCSV: "results/primary_v1/primary_results.csv",
      secondaryCSVs: [
        { label: "Metrics by method",   path: "results/primary_v1/metrics_by_method.csv" },
        { label: "Hypothesis summary",   path: "results/primary_v1/hypothesis_summary.json" },
      ],
    },
    artifacts: ["src", "results/primary_v1", "submission", "manuscript"],
  },
  {
    id: "paper21",
    title: "AI-Enhanced Endpoint Compliance and Automated Vulnerability Management Framework for Essential Government Infrastructure",
    shortTitle: "AI Endpoint Compliance",
    subtitle: "Published in JENRS 3(1), 2024. Hybrid rule + XGBoost compliance detection, automated SCCM/PowerShell remediation, and predictive disaster recovery: 92% compliance accuracy, 40% faster patching, 70% lower DR delay across 10,000 endpoints.",
    status: "published",
    statusLabel: "Published",
    root: "paper21",
    manuscript: {
      main: "manuscript/paper21.md",
    },
    submissionPdf: "submission/main.pdf",
    figures: "submission/figures",
    results: { dir: "submission" },
    artifacts: ["submission/figures", "submission", "manuscript"],
  },
];

/* Status badge colours — light AND dark variants. */
export const STATUS_COLORS: Record<PaperStatus, string> = {
  published:
    "bg-emerald-500  text-white        border-emerald-600 " +
    "dark:bg-emerald-500    dark:text-white       dark:border-emerald-400",
  ready:
    "bg-violet-100   text-violet-800   border-violet-300  " +
    "dark:bg-violet-900/50  dark:text-violet-300  dark:border-violet-700",
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

/* Headline result per paper — verified against frozen results. */
export const KEY_RESULTS: Record<string, string> = {
  paper1:  "EPSS-weighted ranking on a synthetic government fleet",
  paper2:  "Failure-aware gate downgrades unsafe public-feed claims",
  paper3:  "7-task reproducible cyber-hygiene anomaly benchmark",
  paper4:  "Hygiene signals augment EPSS on emergent risk",
  paper5:  "Hygiene signal persists where EPSS-only decays",
  paper6:  "Capacity-indexed decay of exploit-likelihood ranking",
  paper7:  "Rolling-history online calibration",
  paper8:  "High-capacity smoothing hazard falsified",
  paper9:  "Self-trajectory evaluation isolates the mechanism",
  paper10: "Pre-registered self-healing remediation loop",
  paper11: "+9.5pp mission precision@50",
  paper12: "272× faster drift detection",
  paper13: "70% CJI exposure cut via prevention",
  paper14: "+6.5pp precision; day-0 EPSS adds ~0",
  paper15: "Detection recall 0.75 → 0.87",
  paper16: "+0.61 AP on cross-channel anomalies",
  paper17: "95% smaller blast radius (4-ring)",
  paper18: "Annual drills overstate recovery by 31 pts",
  paper19: "78% less CMDB inventory error",
  paper20: "Precision@50 0.74 vs 0.22; MTTR -62% (reproducible synthetic eval)",
  paper21: "92% compliance accuracy, 40% faster patching",
};
