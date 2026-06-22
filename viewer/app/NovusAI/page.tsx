"use client";
import { useState, useMemo } from "react";
import Link from "next/link";
import { ArrowLeft, ShieldHalf, ExternalLink, StickyNote } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import { NOVUS_PAPERS, NOVUS_STATUS, type NovusStatus, type NovusPaper } from "@/lib/novus";

const COL_ACCENT: Record<NovusStatus, string> = {
  proposed: "border-t-fg-4",
  drafting: "border-t-amber-500",
  review:   "border-t-accent",
  done:     "border-t-emerald-500",
};

function Card({ p }: { p: NovusPaper }) {
  return (
    <div className="group border border-border bg-surface-0 rounded p-3.5 hover:border-accent/40 hover:shadow-[0_2px_12px_rgba(0,0,0,0.05)] transition-all">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-mono text-fg-4">#{String(p.n).padStart(2, "0")}</span>
        <span className="text-[10px] uppercase tracking-wider text-fg-4 bg-surface-2 border border-border rounded px-1.5 py-0.5">
          {p.category}
        </span>
      </div>
      <p className="font-serif text-[14px] leading-snug text-fg group-hover:text-accent transition-colors">
        {p.title}
      </p>
      {(p.note || p.link) && (
        <div className="mt-2.5 pt-2.5 border-t border-border flex items-center gap-3 text-[11px] text-fg-4">
          {p.note && <span className="inline-flex items-center gap-1"><StickyNote size={11} />{p.note}</span>}
          {p.link && (
            <a href={p.link} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent hover:underline">
              <ExternalLink size={11} /> draft
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default function NovusAIPage() {
  const [q, setQ] = useState("");

  const byStatus = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const match = (p: NovusPaper) =>
      !needle || p.title.toLowerCase().includes(needle) || p.category.toLowerCase().includes(needle);
    const map: Record<NovusStatus, NovusPaper[]> = { proposed: [], drafting: [], review: [], done: [] };
    NOVUS_PAPERS.filter(match).forEach((p) => map[p.status].push(p));
    return map;
  }, [q]);

  return (
    <div className="min-h-screen flex flex-col bg-surface-0">
      {/* Top bar */}
      <header className="sticky top-0 z-20 h-16 border-b border-border bg-surface-0/90 backdrop-blur-md">
        <div className="h-full max-w-[1400px] mx-auto px-5 md:px-8 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link href="/" className="flex items-center gap-1.5 text-[13px] text-fg-3 hover:text-fg transition-colors">
              <ArrowLeft size={15} /> Portfolio
            </Link>
            <span className="text-fg-5">/</span>
            <span className="flex items-center gap-1.5 font-serif text-[18px] font-semibold text-fg">
              <ShieldHalf size={17} className="text-accent" /> NovusAI
            </span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-5 md:px-8 py-12">
        {/* Heading */}
        <div className="mb-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-accent bg-accent/10 border border-accent/25 rounded px-2.5 py-1 mb-4">
            Private · collaboration track
          </div>
          <h1 className="font-serif text-display text-fg mb-4">Honeypot & Cyber-Deception Research</h1>
          <p className="font-serif text-[18px] leading-[30px] text-fg-3">
            A joint research program with <span className="text-fg font-medium">NovusAI</span> on
            AI-native honeypots, behavioral-cognitive attacker modeling, and turning deception
            telemetry into deployable detection intelligence. {NOVUS_PAPERS.length} papers in the pipeline.
          </p>
        </div>

        {/* Search + counts */}
        <div className="flex flex-wrap items-center gap-3 mb-6 pb-4 border-b border-border">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Filter topics…"
            className="search-input w-full sm:w-72 px-3 py-2 bg-surface-1 border border-border rounded text-[14px] text-fg placeholder:text-fg-4 focus:outline-none"
          />
          <div className="flex items-center gap-4 text-[12px] text-fg-4">
            {NOVUS_STATUS.map((s) => (
              <span key={s.key}>{s.label}: <span className="text-fg font-semibold">{byStatus[s.key].length}</span></span>
            ))}
          </div>
        </div>

        {/* Kanban */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
          {NOVUS_STATUS.map((s) => (
            <section key={s.key} className={`border-t-2 ${COL_ACCENT[s.key]} bg-surface-1 rounded-b border-x border-b border-border`}>
              <div className="flex items-center justify-between px-3.5 py-3 border-b border-border">
                <h2 className="text-[12px] font-semibold uppercase tracking-wider text-fg-2">{s.label}</h2>
                <span className="text-[11px] font-mono text-fg-4">{byStatus[s.key].length}</span>
              </div>
              <div className="p-3 space-y-3 min-h-[120px]">
                {byStatus[s.key].map((p) => <Card key={p.n} p={p} />)}
                {byStatus[s.key].length === 0 && (
                  <p className="text-[12px] text-fg-5 italic px-1 py-4">—</p>
                )}
              </div>
            </section>
          ))}
        </div>

        <p className="mt-10 text-[12px] text-fg-4">
          Working board · update <code className="text-fg-3">lib/novus.ts</code> to advance a paper’s status, add notes, or link a draft.
        </p>
      </main>
    </div>
  );
}
