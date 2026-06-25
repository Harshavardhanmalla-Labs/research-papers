// NovusAI collaboration — honeypot & cyber-deception research track.
// Private working pipeline. Edit `status` as each paper advances:
//   "proposed" -> "drafting" -> "review" -> "done"
export type NovusStatus = "proposed" | "drafting" | "review" | "done";

export interface NovusPaper {
  n: number;
  title: string;
  category: string;
  status: NovusStatus;
  note?: string;   // free-form working note
  link?: string;   // draft / repo / doc link
}

export const NOVUS_STATUS: { key: NovusStatus; label: string }[] = [
  { key: "proposed", label: "Proposed" },
  { key: "drafting", label: "Drafting" },
  { key: "review",   label: "In review" },
  { key: "done",     label: "Done" },
];

export const NOVUS_PAPERS: NovusPaper[] = [
  { n: 1,  category: "Deception modeling",    status: "proposed",
    title: "BCI-Honey: A Behavioral-Cognitive Intelligence Layer for Adaptive Honeypot Deception and Attacker Intent Modeling" },
  { n: 2,  category: "Adaptive deception",    status: "proposed",
    title: "Adaptive Cyber Deception Using Behavioral-Cognitive Signals from Honeypot Interaction Sequences" },
  { n: 3,  category: "Intent modeling",       status: "proposed",
    title: "Intent-Aware Honeypots: Modeling Attacker Decision Progression from SSH/Telnet Command Telemetry" },
  { n: 4,  category: "LLM deception",         status: "proposed",
    title: "LLM-Guided Deception in Honeypots: Safe Dynamic Response Generation with Policy Guardrails" },
  { n: 5,  category: "Detection engineering", status: "proposed",
    title: "From Honeypot Sessions to Detection Rules: Automated Sigma/YARA-L Generation Using Attacker Behavior Traces" },
  { n: 6,  category: "Threat intelligence",   status: "proposed",
    title: "Threat-Intelligence-Enriched Honeypots for Real-Time Attacker Scoring and Infrastructure Attribution" },
  { n: 7,  category: "Explainable ML",        status: "proposed",
    title: "Session-Level Attack Classification in Low-Interaction Honeypots Using Behavioral Features and Explainable Machine Learning" },
  { n: 8,  category: "Anti-reconnaissance",   status: "proposed",
    title: "Deception Persona Mutation: Dynamic Honeypot Fingerprint Adaptation Against Adversarial Reconnaissance" },
  { n: 9,  category: "Benchmark",             status: "proposed",
    title: "A MITRE ATT&CK-Aligned Benchmark for Evaluating Honeypot-Derived Detection Intelligence" },
  { n: 10, category: "Human-in-the-loop",     status: "proposed",
    title: "Human-in-the-Loop AI Deception Systems for Cyber Threat Collection and Defensive Rule Authoring" },
  { n: 11, category: "Autonomous pipelines",  status: "proposed",
    title: "Autonomous Threat Intelligence Pipelines from Honeypot Telemetry for Critical Infrastructure Defense" },
  { n: 12, category: "Evaluation",            status: "proposed",
    title: "Measuring Deception Efficacy in AI-Native Honeypots: Precision, Engagement Depth, and Detection Yield" },
];

// ── Patents & IP ───────────────────────────────────────────────────────────
export type PatentStatus = "draft" | "filed" | "pending" | "granted";

export interface NovusPatent {
  id: string;
  title: string;
  kind: string;          // e.g. "Provisional patent application"
  status: PatentStatus;
  inventor: string;
  assignee: string;
  claims: number;        // total claims
  independentClaims: number;
  abstract: string;
  docPath: string;       // markdown, relative to the repo root (PAPERS_ROOT)
}

export const PATENT_STATUS: Record<PatentStatus, string> = {
  draft: "Draft for filing",
  filed: "Filed",
  pending: "Pending",
  granted: "Granted",
};

export const NOVUS_PATENTS: NovusPatent[] = [
  {
    id: "novus-aegis-dynamic-honeypot",
    title:
      "Systems and Methods for Threat-Intelligence-Driven Dynamic Deployment and Adaptive Configuration of Deception Honeypots",
    kind: "Provisional patent application",
    status: "draft",
    inventor: "Harshavardhan Malla",
    assignee: "NovusAI",
    claims: 14,
    independentClaims: 3,
    abstract:
      "An AI decision engine ingests live threat intelligence and, under enforceable cost/region/compliance policies, generates an explainable instruction to deploy and configure honeypots whose deception surface is randomized so no two deployments share a fingerprint; a monitoring loop turns attacker interaction into enriched alerts and attacker profiles that feed back to continuously adapt the deception.",
    docPath: "novus/patents/novus_aegis_dynamic_honeypot.md",
  },
];
