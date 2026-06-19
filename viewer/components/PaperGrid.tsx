"use client";
import { useState } from "react";
import {
  Search, Shield, Scale, FlaskConical, Flame, Clock,
  TrendingDown, RefreshCw, Activity, Target, Zap, ArrowRight,
} from "lucide-react";
import type { Paper } from "@/lib/papers";
import { STATUS_COLORS } from "@/lib/papers";
import clsx from "clsx";

const PAPER_ICONS = [Shield, Scale, FlaskConical, Flame, Clock, TrendingDown, RefreshCw, Activity, Target, Zap];
const PAPER_ICON_CLS = [
  "paper-icon-p1", "paper-icon-p2", "paper-icon-p3", "paper-icon-p4", "paper-icon-p5",
  "paper-icon-p6", "paper-icon-p7", "paper-icon-p8", "paper-icon-p9", "paper-icon-p10",
];

const VENUES: Record<string, string> = {
  paper1: "IEEE",
  paper2: "CSET",
  paper3: "ACM AISec",
  paper4: "IEEE TNSM",
  paper5: "IEEE TNSM",
  paper6: "IEEE TNSM",
  paper7: "IEEE TNSM",
  paper8: "IEEE TNSM",
  paper9: "IEEE TNSM",
  paper10: "IEEE TNSM",
};

const SERIES = [
  {
    label: "Vulnerability Prioritization",
    desc: "EPSS-based exploit scoring and calibration",
    pill: "bg-sky-500/12 text-sky-700 border-sky-200 dark:text-sky-400 dark:border-sky-800 dark:bg-sky-500/10",
    ids: ["paper1", "paper2"],
  },
  {
    label: "Hygiene-Augmented Prioritization",
    desc: "Cyber-hygiene signals layered on EPSS scoring",
    pill: "bg-violet-500/12 text-violet-700 border-violet-200 dark:text-violet-400 dark:border-violet-800 dark:bg-violet-500/10",
    ids: ["paper3", "paper4", "paper5", "paper6", "paper7", "paper8", "paper9"],
  },
  {
    label: "Synthesis",
    desc: "Integrated self-healing framework",
    pill: "bg-amber-500/12 text-amber-700 border-amber-200 dark:text-amber-400 dark:border-amber-800 dark:bg-amber-500/10",
    ids: ["paper10"],
  },
];

interface Props {
  papers: Paper[];
  onSelect: (id: string) => void;
}

export default function PaperGrid({ papers, onSelect }: Props) {
  const [query, setQuery] = useState("");

  const allIdx = (id: string) => papers.findIndex((p) => p.id === id);

  const filtered = papers.filter(
    (p) =>
      !query ||
      p.title.toLowerCase().includes(query.toLowerCase()) ||
      p.subtitle.toLowerCase().includes(query.toLowerCase()) ||
      p.shortTitle.toLowerCase().includes(query.toLowerCase())
  );

  const complete  = papers.filter((p) => p.status === "complete").length;
  const packaging = papers.filter((p) => p.status === "packaging").length;

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto px-8 py-8">

        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-fg tracking-tight mb-1">Research Papers</h1>
          <p className="text-[13px] text-fg-4">EB-1A portfolio · 10 papers across 3 research series</p>

          {/* Summary pills */}
          <div className="flex gap-3 mt-4 flex-wrap">
            <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
              {complete} complete
            </span>
            <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              {packaging} packaging
            </span>
            <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-surface-3 text-fg-3 border border-border">
              {papers.length} total
            </span>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-8 max-w-sm">
          <Search size={13} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-fg-4 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search papers…"
            className="search-input w-full pl-10 pr-4 py-2.5 text-[12px] bg-surface-1 border border-border rounded-xl text-fg placeholder:text-fg-5 transition-all"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-fg-4 hover:text-fg text-[10px]"
            >
              ✕
            </button>
          )}
        </div>

        {/* Content */}
        {query ? (
          <div>
            <p className="text-[11px] text-fg-4 mb-4">{filtered.length} result{filtered.length !== 1 ? "s" : ""}</p>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filtered.map((p) => (
                <PaperCard key={p.id} paper={p} idx={allIdx(p.id)} onSelect={onSelect} />
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-10">
            {SERIES.map((series) => {
              const seriesPapers = papers.filter((p) => series.ids.includes(p.id));
              return (
                <section key={series.label}>
                  {/* Series heading */}
                  <div className="flex items-center gap-3 mb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={clsx("text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border", series.pill)}>
                          {series.label}
                        </span>
                        <span className="text-[10px] text-fg-5">{seriesPapers.length} paper{seriesPapers.length !== 1 ? "s" : ""}</span>
                      </div>
                      <p className="text-[11px] text-fg-4 mt-1 ml-0.5">{series.desc}</p>
                    </div>
                    <div className="flex-1 h-px bg-border ml-2" />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {seriesPapers.map((p) => (
                      <PaperCard key={p.id} paper={p} idx={allIdx(p.id)} onSelect={onSelect} />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function PaperCard({ paper, idx, onSelect }: { paper: Paper; idx: number; onSelect: (id: string) => void }) {
  const Icon  = PAPER_ICONS[idx]    ?? Shield;
  const icCls = PAPER_ICON_CLS[idx] ?? "paper-icon-p1";
  const venue = VENUES[paper.id]    ?? "Preprint";

  return (
    <button
      onClick={() => onSelect(paper.id)}
      className="group text-left bg-surface-1 border border-border rounded-2xl p-5 card-hover w-full flex flex-col gap-4 hover:border-accent/40"
    >
      {/* Top row: icon + venue badge */}
      <div className="flex items-start justify-between">
        <div className={clsx("w-10 h-10 rounded-xl flex items-center justify-center shadow-sm flex-shrink-0", icCls)}>
          <Icon size={17} className="text-white drop-shadow-sm" />
        </div>
        <span className="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-md bg-surface-3 text-fg-4 border border-border flex-shrink-0">
          {venue}
        </span>
      </div>

      {/* Paper number + title + subtitle */}
      <div className="flex-1 min-w-0">
        <p className="text-[9px] font-black text-fg-5 tracking-[0.15em] uppercase mb-1">P{idx + 1}</p>
        <h3 className="text-[13px] font-bold text-fg leading-snug line-clamp-2 group-hover:text-accent transition-colors duration-150">
          {paper.shortTitle}
        </h3>
        <p className="text-[11px] text-fg-4 leading-snug mt-1.5 line-clamp-3">
          {paper.subtitle}
        </p>
      </div>

      {/* Footer: status + arrow */}
      <div className="flex items-center justify-between pt-1">
        <span className={clsx(
          "inline-block px-2 py-0.5 rounded-full text-[9px] font-bold border uppercase tracking-wider",
          STATUS_COLORS[paper.status]
        )}>
          {paper.statusLabel}
        </span>
        <ArrowRight
          size={14}
          className="text-fg-5 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all duration-150"
        />
      </div>
    </button>
  );
}
