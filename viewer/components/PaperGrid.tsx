"use client";
import { useState, useEffect } from "react";
import {
  Search, Shield, Scale, FlaskConical, Flame, Clock,
  TrendingDown, RefreshCw, Activity, Target, Zap, ArrowRight,
  Building2, FileCheck, Lock, CalendarClock, Network,
  Brain, Terminal, LifeBuoy, Database, Send, Github, Copy, Check,
} from "lucide-react";
import type { Paper } from "@/lib/papers";
import clsx from "clsx";

const PAPER_ICONS = [
  Shield, Scale, FlaskConical, Flame, Clock,
  TrendingDown, RefreshCw, Activity, Target, Zap,
  Building2, FileCheck, Lock, CalendarClock, Network,
  Brain, Terminal, LifeBuoy, Database,
  Zap, FileCheck,
];
const PAPER_ICON_CLS = [
  "paper-icon-p1",  "paper-icon-p2",  "paper-icon-p3",  "paper-icon-p4",  "paper-icon-p5",
  "paper-icon-p6",  "paper-icon-p7",  "paper-icon-p8",  "paper-icon-p9",  "paper-icon-p10",
  "paper-icon-p11", "paper-icon-p12", "paper-icon-p13", "paper-icon-p14", "paper-icon-p15",
  "paper-icon-p16", "paper-icon-p17", "paper-icon-p18", "paper-icon-p19",
  "paper-icon-p20", "paper-icon-p21",
];

const VENUES: Record<string, string> = {
  paper1: "IEEE", paper2: "IEEE", paper3: "IEEE",
  paper4: "IEEE TNSM", paper5: "IEEE TNSM", paper6: "IEEE TNSM", paper7: "IEEE TNSM",
  paper8: "IEEE TNSM", paper9: "IEEE TNSM", paper10: "IEEE TNSM",
  paper11: "Gov / Practitioner", paper12: "Gov / Practitioner", paper13: "Gov / Practitioner",
  paper14: "Gov / Practitioner", paper15: "Gov / Practitioner", paper16: "Gov / Practitioner",
  paper17: "Gov / Practitioner", paper18: "Gov / Practitioner", paper19: "Gov / Practitioner",
  paper20: "Critical Infra", paper21: "JENRS",
};

const SERIES = [
  { label: "Vulnerability Prioritization", desc: "EPSS-based exploit scoring & calibration",
    bar: "border-t-sky-500",     pill: "text-sky-700 dark:text-sky-400",       ids: ["paper1", "paper2"] },
  { label: "Hygiene-Augmented Prioritization", desc: "Cyber-hygiene signals layered on EPSS scoring",
    bar: "border-t-violet-500",  pill: "text-violet-700 dark:text-violet-400", ids: ["paper3","paper4","paper5","paper6","paper7","paper8","paper9"] },
  { label: "Synthesis", desc: "Integrated self-healing framework",
    bar: "border-t-amber-500",   pill: "text-amber-700 dark:text-amber-400",   ids: ["paper10"] },
  { label: "Government & Practitioner", desc: "Applied security frameworks for the public sector",
    bar: "border-t-emerald-500", pill: "text-emerald-700 dark:text-emerald-400", ids: ["paper11","paper12","paper13","paper14","paper15","paper16","paper17","paper18","paper19"] },
  { label: "Critical-Infrastructure Frameworks", desc: "AI-native frameworks; one peer-reviewed (JENRS)",
    bar: "border-t-rose-500",    pill: "text-rose-700 dark:text-rose-400",     ids: ["paper20", "paper21"] },
];

// Submission lifecycle stages (editable per paper, persisted server-side).
const STAGES = ["Not submitted", "Submitted", "Under review", "Revision", "Accepted", "Published"];
const STAGE_CLS: Record<string, string> = {
  "Not submitted": "text-fg-4 border-border bg-surface-2",
  "Submitted":     "text-sky-700 dark:text-sky-400 border-sky-300 dark:border-sky-800 bg-sky-500/10",
  "Under review":  "text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-800 bg-amber-500/10",
  "Revision":      "text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-800 bg-orange-500/10",
  "Accepted":      "text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800 bg-emerald-500/10",
  "Published":     "text-white border-emerald-600 bg-emerald-500",
};

type Entry = { submittedTo?: string; stage?: string; dataRepo?: string; repoName?: string };
type Store = Record<string, Entry>;
const REPO_BASE = "https://github.com/Harshavardhanmalla-Labs/research-papers/tree/main";

interface Props { papers: Paper[]; onSelect: (id: string) => void; }

export default function PaperGrid({ papers, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [track, setTrack] = useState<Store>({});

  useEffect(() => {
    fetch("/api/tracking").then((r) => r.ok ? r.json() : {}).then(setTrack).catch(() => {});
  }, []);

  const save = (id: string, patch: Entry) => {
    setTrack((prev) => ({ ...prev, [id]: { ...prev[id], ...patch } }));
    fetch("/api/tracking", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, ...patch }),
    }).catch(() => {});
  };

  const idx = (id: string) => papers.findIndex((p) => p.id === id);
  const filtered = papers.filter(
    (p) => !query ||
      p.title.toLowerCase().includes(query.toLowerCase()) ||
      p.subtitle.toLowerCase().includes(query.toLowerCase()) ||
      p.shortTitle.toLowerCase().includes(query.toLowerCase())
  );
  const published = papers.filter((p) => p.status === "published").length;
  const ready     = papers.filter((p) => p.status === "ready").length;

  const card = (p: Paper) => (
    <PaperCard key={p.id} paper={p} n={idx(p.id)} onSelect={onSelect}
      entry={track[p.id]} onSave={(patch) => save(p.id, patch)} />
  );

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-[1500px] mx-auto px-6 md:px-8 py-8">

        <div className="mb-7">
          <h1 className="text-2xl font-bold text-fg tracking-tight mb-1">Research Papers</h1>
          <p className="text-[13px] text-fg-4">EB-1A portfolio · {papers.length} papers across {SERIES.length} research series</p>
          <div className="flex gap-3 mt-4 flex-wrap">
            <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">{published} peer-reviewed</span>
            <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-violet-500/10 text-violet-700 dark:text-violet-400 border border-violet-200 dark:border-violet-800">{ready} submission-ready</span>
            <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-surface-3 text-fg-3 border border-border">{papers.length} total</span>
          </div>
        </div>

        <div className="relative mb-7 max-w-sm">
          <Search size={13} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-fg-4 pointer-events-none" />
          <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search papers…"
            className="search-input w-full pl-10 pr-4 py-2.5 text-[12px] bg-surface-1 border border-border rounded-xl text-fg placeholder:text-fg-5 transition-all" />
          {query && <button onClick={() => setQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-fg-4 hover:text-fg text-[10px]">✕</button>}
        </div>

        {query ? (
          <div>
            <p className="text-[11px] text-fg-4 mb-4">{filtered.length} result{filtered.length !== 1 ? "s" : ""}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">{filtered.map(card)}</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 items-start">
            {SERIES.map((s) => {
              const sp = papers.filter((p) => s.ids.includes(p.id));
              return (
                <section key={s.label} className={clsx("border-t-2 bg-surface-1 rounded-b-xl border-x border-b border-border", s.bar)}>
                  <div className="px-3.5 py-3 border-b border-border">
                    <div className="flex items-center justify-between gap-2">
                      <h2 className={clsx("text-[11px] font-bold uppercase tracking-wider leading-tight", s.pill)}>{s.label}</h2>
                      <span className="text-[11px] font-mono text-fg-4 flex-shrink-0">{String(sp.length).padStart(2, "0")}</span>
                    </div>
                    <p className="text-[10px] text-fg-4 mt-1 leading-snug">{s.desc}</p>
                  </div>
                  <div className="p-3 space-y-3">{sp.map(card)}</div>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function PaperCard({ paper, n, onSelect, entry, onSave }: {
  paper: Paper; n: number; onSelect: (id: string) => void;
  entry?: Entry; onSave: (patch: Entry) => void;
}) {
  const Icon  = PAPER_ICONS[n]    ?? Shield;
  const icCls = PAPER_ICON_CLS[n] ?? "paper-icon-p1";
  const venue = VENUES[paper.id]  ?? "Preprint";

  const [venueVal, setVenueVal] = useState(entry?.submittedTo ?? "");
  useEffect(() => { setVenueVal(entry?.submittedTo ?? ""); }, [entry?.submittedTo]);
  const stage = entry?.stage ?? (paper.status === "published" ? "Published" : "Not submitted");

  const defaultRepo = `${REPO_BASE}/${paper.root}`;
  const [repoVal, setRepoVal] = useState(entry?.dataRepo ?? defaultRepo);
  useEffect(() => { setRepoVal(entry?.dataRepo ?? defaultRepo); }, [entry?.dataRepo]); // eslint-disable-line react-hooks/exhaustive-deps
  const [repoName, setRepoName] = useState(entry?.repoName ?? "GitHub");
  useEffect(() => { setRepoName(entry?.repoName ?? "GitHub"); }, [entry?.repoName]);
  const [copied, setCopied] = useState(false);
  const copyRepo = () => { navigator.clipboard?.writeText(repoVal).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1400); }).catch(() => {}); };

  return (
    <div className="bg-surface-0 border border-border rounded-xl p-3.5 hover:border-accent/45 transition-colors">
      {/* Clickable identity → opens the paper */}
      <div role="button" tabIndex={0} onClick={() => onSelect(paper.id)}
        onKeyDown={(e) => { if (e.key === "Enter") onSelect(paper.id); }}
        className="group cursor-pointer">
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2 min-w-0">
            <div className={clsx("w-7 h-7 rounded-lg flex items-center justify-center shadow-sm flex-shrink-0", icCls)}>
              <Icon size={13} className="text-white drop-shadow-sm" />
            </div>
            <span className="text-[10px] font-mono text-fg-5 tracking-wide">P{n + 1}</span>
          </div>
          <span className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-2 text-fg-4 border border-border flex-shrink-0">{venue}</span>
        </div>
        <h3 className="text-[13px] font-bold text-fg leading-snug group-hover:text-accent transition-colors line-clamp-2">{paper.shortTitle}</h3>
        <p className="text-[11px] text-fg-4 leading-snug mt-1 line-clamp-2">{paper.subtitle}</p>
      </div>

      {/* Editable submission tracker */}
      <div className="mt-2.5 pt-2.5 border-t border-border space-y-2">
        <div className="flex items-center gap-1.5">
          <Send size={11} className="text-fg-5 flex-shrink-0" />
          <input
            value={venueVal}
            onChange={(e) => setVenueVal(e.target.value)}
            onBlur={() => { if ((entry?.submittedTo ?? "") !== venueVal) onSave({ submittedTo: venueVal }); }}
            onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }}
            placeholder="Submitted to…"
            className="w-full bg-transparent text-[11px] text-fg placeholder:text-fg-5 focus:outline-none border-b border-transparent focus:border-border py-0.5"
          />
        </div>
        <select
          value={stage}
          onChange={(e) => onSave({ stage: e.target.value })}
          className={clsx("w-full text-[10px] font-semibold uppercase tracking-wide rounded-md border px-2 py-1 cursor-pointer focus:outline-none appearance-none", STAGE_CLS[stage] ?? STAGE_CLS["Not submitted"])}
        >
          {STAGES.map((s) => <option key={s} value={s} className="bg-surface-1 text-fg normal-case">{s}</option>)}
        </select>

        {/* Data repository (link + name) for journal submission forms */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <Github size={11} className="text-fg-5 flex-shrink-0" />
            <input
              value={repoVal}
              onChange={(e) => setRepoVal(e.target.value)}
              onBlur={() => { if ((entry?.dataRepo ?? defaultRepo) !== repoVal) onSave({ dataRepo: repoVal }); }}
              onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }}
              placeholder="Data repository URL…"
              title={repoVal}
              className="w-full bg-transparent text-[10px] font-mono text-fg-3 placeholder:text-fg-5 focus:outline-none border-b border-transparent focus:border-border py-0.5 truncate"
            />
            <button onClick={copyRepo} title="Copy data repository link" className="text-fg-5 hover:text-accent flex-shrink-0">
              {copied ? <Check size={11} /> : <Copy size={11} />}
            </button>
          </div>
          <div className="flex items-center gap-1.5 pl-[18px]">
            <span className="text-[9px] uppercase tracking-wider text-fg-5 flex-shrink-0">Repo name</span>
            <input
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              onBlur={() => { if ((entry?.repoName ?? "GitHub") !== repoName) onSave({ repoName }); }}
              onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }}
              placeholder="GitHub"
              className="w-full bg-transparent text-[10px] text-fg-3 placeholder:text-fg-5 focus:outline-none border-b border-transparent focus:border-border py-0.5"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
