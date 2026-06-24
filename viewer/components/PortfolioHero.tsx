"use client";
import { Github, Linkedin, FileText, Award, Layers, ArrowDown } from "lucide-react";
import LinkedInBadge from "./LinkedInBadge";

interface Props {
  total: number;
  peerReviewed: number;
  series: number;
}

const FOCUS = [
  "Vulnerability Prioritization",
  "Tamper-Evident Systems",
  "ML for Security",
  "Cyber-Hygiene",
  "Critical Infrastructure",
];

const REPO = "https://github.com/Harshavardhanmalla-Labs/research-papers";
const LINKEDIN = "https://www.linkedin.com/in/harshavardhanmalla";

export default function PortfolioHero({ total, peerReviewed, series }: Props) {
  return (
    <section className="mb-8 rounded-2xl border border-border bg-surface-1/70 overflow-hidden">
      <div className="grid lg:grid-cols-[1fr_auto]">
        {/* Identity */}
        <div className="p-6 md:p-8 min-w-0">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-5 h-px bg-accent/60" />
            <span className="text-[10.5px] font-bold uppercase tracking-[0.16em] text-accent">
              Research Portfolio
            </span>
          </div>
          <h1 className="text-[26px] md:text-[30px] leading-[1.05] font-extrabold text-fg tracking-tight">
            Harshavardhan Malla
          </h1>
          <p className="text-[13.5px] font-semibold text-fg-3 mt-1.5">
            Independent Researcher · Security &amp; Machine Learning
          </p>
          <p className="text-[13px] text-fg-4 leading-relaxed mt-3 max-w-xl">
            I build reproducible, adversarially-tested systems at the
            intersection of vulnerability management, machine learning, and
            verifiable security. Every paper below ships with its full source,
            data-generation code, and frozen result tables, so every reported
            number can be regenerated from a fixed seed.
          </p>

          {/* Focus chips */}
          <div className="flex flex-wrap gap-1.5 mt-4">
            {FOCUS.map((f) => (
              <span key={f}
                className="text-[10.5px] font-medium px-2.5 py-1 rounded-full bg-surface-3/70 text-fg-3 border border-border">
                {f}
              </span>
            ))}
          </div>

          {/* Stats */}
          <div className="flex flex-wrap gap-x-6 gap-y-3 mt-6">
            {[
              { Icon: FileText, n: total, label: "papers" },
              { Icon: Award, n: peerReviewed, label: "peer-reviewed", accent: true },
              { Icon: Layers, n: series, label: "research series" },
            ].map(({ Icon, n, label, accent }) => (
              <div key={label} className="flex items-center gap-2">
                <Icon size={15} className={accent ? "text-emerald-600 dark:text-emerald-400" : "text-fg-4"} />
                <span className="text-[17px] font-extrabold text-fg tabular-nums">{n}</span>
                <span className="text-[11.5px] text-fg-4">{label}</span>
              </div>
            ))}
          </div>

          {/* Links */}
          <div className="flex flex-wrap items-center gap-2.5 mt-6">
            <a href={LINKEDIN} target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-[12px] font-semibold bg-accent text-white hover:opacity-90 transition-opacity">
              <Linkedin size={14} /> Connect on LinkedIn
            </a>
            <a href={REPO} target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-[12px] font-semibold border border-border text-fg-2 hover:border-accent/50 hover:text-fg transition-colors">
              <Github size={14} /> Source &amp; data
            </a>
            <span className="inline-flex items-center gap-1.5 text-[11px] text-fg-4 ml-1">
              <ArrowDown size={12} /> Browse the papers below
            </span>
          </div>
        </div>

        {/* Official LinkedIn badge */}
        <div className="hidden lg:flex items-center justify-center border-l border-border bg-surface-2/40 p-6">
          <LinkedInBadge />
        </div>
      </div>
    </section>
  );
}
