"use client";
import { useState, useEffect, useMemo } from "react";
import {
  Search, Shield, Scale, FlaskConical, Flame, Clock,
  TrendingDown, RefreshCw, Activity, Target, Zap, ArrowRight,
  Building2, FileCheck, Lock, CalendarClock, Network,
  Brain, Terminal, LifeBuoy, Database, Send, Github, Copy, Check,
  LayoutGrid, Rows3, ExternalLink, X,
} from "lucide-react";
import type { Paper } from "@/lib/papers";
import clsx from "clsx";
import PortfolioHero from "./PortfolioHero";

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
  paper20: "Critical Infra", paper21: "JENRS", paper22: "ESWA",
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
    bar: "border-t-rose-500",    pill: "text-rose-700 dark:text-rose-400",     ids: ["paper20", "paper21", "paper22"] },
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
// Solid dot color per stage, for the pipeline summary + row markers.
const STAGE_DOT: Record<string, string> = {
  "Not submitted": "bg-fg-4/50",
  "Submitted":     "bg-sky-500",
  "Under review":  "bg-amber-500",
  "Revision":      "bg-orange-500",
  "Accepted":      "bg-emerald-500",
  "Published":     "bg-emerald-600",
};

type Entry = { submittedTo?: string; stage?: string; dataRepo?: string; repoName?: string; updatedAt?: string };
type Store = Record<string, Entry>;
const REPO_BASE = "https://github.com/Harshavardhanmalla-Labs/research-papers/tree/main";

const stageOf = (p: Paper, e?: Entry) =>
  e?.stage ?? (p.status === "published" ? "Published" : "Not submitted");

const fmtDate = (iso?: string) => {
  if (!iso) return "";
  try { return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" }); }
  catch { return ""; }
};

interface Props { papers: Paper[]; onSelect: (id: string) => void; }

export default function PaperGrid({ papers, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [track, setTrack] = useState<Store>({});
  const [view, setView]   = useState<"board" | "submissions">("board");
  const [stageFilter, setStageFilter] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/tracking").then((r) => r.ok ? r.json() : {}).then(setTrack).catch(() => {});
  }, []);

  const save = (id: string, patch: Entry) => {
    setTrack((prev) => ({ ...prev, [id]: { ...prev[id], ...patch, updatedAt: new Date().toISOString() } }));
    fetch("/api/tracking", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, ...patch }),
    }).catch(() => {});
  };

  const idx = (id: string) => papers.findIndex((p) => p.id === id);

  // Stage counts across the pipeline (drives the summary chips).
  const stageCounts = useMemo(() => {
    const c: Record<string, number> = Object.fromEntries(STAGES.map((s) => [s, 0]));
    papers.forEach((p) => { c[stageOf(p, track[p.id])] = (c[stageOf(p, track[p.id])] ?? 0) + 1; });
    return c;
  }, [papers, track]);

  const matchesQuery = (p: Paper) =>
    !query ||
    p.title.toLowerCase().includes(query.toLowerCase()) ||
    p.subtitle.toLowerCase().includes(query.toLowerCase()) ||
    p.shortTitle.toLowerCase().includes(query.toLowerCase()) ||
    (track[p.id]?.submittedTo ?? "").toLowerCase().includes(query.toLowerCase());

  const matchesStage = (p: Paper) => !stageFilter || stageOf(p, track[p.id]) === stageFilter;
  const filtered = papers.filter((p) => matchesQuery(p) && matchesStage(p));
  const isFiltering = !!query || !!stageFilter;

  const card = (p: Paper) => (
    <PaperCard key={p.id} paper={p} n={idx(p.id)} onSelect={onSelect}
      entry={track[p.id]} onSave={(patch) => save(p.id, patch)} />
  );

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-[1500px] mx-auto px-6 md:px-8 py-8">

        {/* Portfolio hero — landing only (hidden while searching/filtering) */}
        {!isFiltering && (
          <PortfolioHero
            total={papers.length}
            peerReviewed={papers.filter((p) => p.status === "published").length}
            series={SERIES.length}
          />
        )}

        {/* Header */}
        <div className="flex items-end justify-between gap-4 flex-wrap mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="w-5 h-px bg-accent/60" />
              <span className="text-[10.5px] font-bold uppercase tracking-[0.16em] text-accent">Research Portfolio</span>
            </div>
            <h1 className="text-[28px] leading-none font-extrabold text-fg tracking-tight">Research Papers</h1>
            <p className="text-[13px] text-fg-4 mt-2">
              <span className="font-semibold text-fg-3">{papers.length}</span> papers ·
              <span className="font-semibold text-fg-3"> {SERIES.length}</span> research series ·
              <span className="font-semibold text-emerald-600 dark:text-emerald-400"> {stageCounts["Published"] ?? 0}</span> peer-reviewed
            </p>
          </div>
          {/* View toggle */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-surface-2 border border-border">
            {([
              { k: "board", label: "Series board", Icon: LayoutGrid },
              { k: "submissions", label: "Submissions", Icon: Rows3 },
            ] as const).map(({ k, label, Icon }) => (
              <button key={k} onClick={() => setView(k)}
                className={clsx(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11.5px] font-semibold transition-all",
                  view === k ? "bg-surface-0 text-fg shadow-sm border border-border" : "text-fg-4 hover:text-fg-2"
                )}>
                <Icon size={13} /> {label}
              </button>
            ))}
          </div>
        </div>

        {/* Submission pipeline summary — proportional bar + click a stage to filter */}
        <div className="mb-6 rounded-2xl border border-border bg-surface-1 p-4 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-fg-4">Submission pipeline</span>
            {stageFilter && (
              <button onClick={() => setStageFilter(null)}
                className="inline-flex items-center gap-1 text-[10.5px] font-semibold text-accent hover:underline">
                <X size={11} /> Clear filter
              </button>
            )}
          </div>

          {/* Proportional progress bar — instant read of where everything stands */}
          <div className="flex h-2 w-full rounded-full overflow-hidden bg-surface-3 mb-3.5">
            {STAGES.map((s) => {
              const n = stageCounts[s] ?? 0;
              if (n === 0) return null;
              const pct = (n / Math.max(papers.length, 1)) * 100;
              return (
                <button key={s} onClick={() => setStageFilter(stageFilter === s ? null : s)}
                  title={`${s}: ${n}`}
                  style={{ width: `${pct}%` }}
                  className={clsx("h-full transition-all hover:brightness-110", STAGE_DOT[s],
                    stageFilter && stageFilter !== s && "opacity-30")} />
              );
            })}
          </div>

          <div className="flex flex-wrap gap-2">
            {STAGES.map((s) => {
              const n = stageCounts[s] ?? 0;
              const active = stageFilter === s;
              return (
                <button key={s} onClick={() => setStageFilter(active ? null : s)}
                  className={clsx(
                    "group inline-flex items-center gap-2 pl-2.5 pr-3 py-1.5 rounded-lg border text-[11.5px] font-medium transition-all",
                    active ? "border-accent ring-1 ring-accent/40 bg-accent/5 text-fg"
                           : "border-border bg-surface-0 hover:border-accent/40 hover:-translate-y-px",
                    n === 0 && "opacity-40"
                  )}>
                  <span className={clsx("w-2 h-2 rounded-full flex-shrink-0", STAGE_DOT[s])} />
                  <span className="text-fg-2 group-hover:text-fg">{s}</span>
                  <span className="text-fg font-bold tabular-nums">{n}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-6 max-w-sm">
          <Search size={13} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-fg-4 pointer-events-none" />
          <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search title or journal…"
            className="search-input w-full pl-10 pr-4 py-2.5 text-[12px] bg-surface-1 border border-border rounded-xl text-fg placeholder:text-fg-5 transition-all" />
          {query && <button onClick={() => setQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-fg-4 hover:text-fg text-[10px]">✕</button>}
        </div>

        {/* SUBMISSIONS TABLE VIEW */}
        {view === "submissions" ? (
          <SubmissionsTable
            papers={filtered} allIdx={idx} track={track} onSelect={onSelect} onSave={save}
          />
        ) : isFiltering ? (
          /* Filtered flat grid (board view, with query/stage filter active) */
          <div>
            <p className="text-[11px] text-fg-4 mb-4">
              {filtered.length} {filtered.length === 1 ? "paper" : "papers"}
              {stageFilter && <> · stage <span className="font-semibold text-fg-3">{stageFilter}</span></>}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">{filtered.map(card)}</div>
          </div>
        ) : (
          /* SERIES BOARD VIEW */
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

/* ---------------- Submissions table ---------------- */
function SubmissionsTable({ papers, allIdx, track, onSelect, onSave }: {
  papers: Paper[]; allIdx: (id: string) => number; track: Store;
  onSelect: (id: string) => void; onSave: (id: string, patch: Entry) => void;
}) {
  if (papers.length === 0) {
    return <p className="text-[12px] text-fg-4 py-10 text-center">No papers match the current filter.</p>;
  }
  return (
    <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
      {/* header */}
      <div className="hidden md:grid grid-cols-[2.4rem_minmax(0,1fr)_minmax(0,1fr)_10rem_4.5rem_2.5rem] gap-3 px-4 py-2.5 border-b border-border bg-surface-2 text-[10px] font-bold uppercase tracking-wider text-fg-4">
        <span>#</span><span>Paper</span><span>Submitted to</span><span>Stage</span><span>Updated</span><span>Repo</span>
      </div>
      <div className="divide-y divide-border">
        {papers.map((p) => (
          <SubmissionRow key={p.id} paper={p} n={allIdx(p.id)} entry={track[p.id]}
            onSelect={onSelect} onSave={(patch) => onSave(p.id, patch)} />
        ))}
      </div>
    </div>
  );
}

function SubmissionRow({ paper, n, entry, onSelect, onSave }: {
  paper: Paper; n: number; entry?: Entry; onSelect: (id: string) => void; onSave: (patch: Entry) => void;
}) {
  const Icon  = PAPER_ICONS[n]    ?? Shield;
  const icCls = PAPER_ICON_CLS[n] ?? "paper-icon-p1";
  const stage = stageOf(paper, entry);
  const [venueVal, setVenueVal] = useState(entry?.submittedTo ?? "");
  useEffect(() => { setVenueVal(entry?.submittedTo ?? ""); }, [entry?.submittedTo]);
  const repo = entry?.dataRepo ?? `${REPO_BASE}/${paper.root}`;

  return (
    <div className="grid grid-cols-[2.4rem_minmax(0,1fr)] md:grid-cols-[2.4rem_minmax(0,1fr)_minmax(0,1fr)_10rem_4.5rem_2.5rem] gap-3 px-4 py-2.5 items-center hover:bg-[var(--table-hover)] transition-colors">
      {/* number + icon */}
      <div className="flex items-center gap-2">
        <span className={clsx("w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0", icCls)}>
          <Icon size={11} className="text-white" />
        </span>
      </div>
      {/* title (click → open) */}
      <button onClick={() => onSelect(paper.id)} className="text-left min-w-0 group">
        <span className="block text-[12.5px] font-semibold text-fg group-hover:text-accent truncate transition-colors">{paper.shortTitle}</span>
        <span className="block text-[10.5px] text-fg-4 truncate">P{n + 1} · {paper.title}</span>
      </button>
      {/* submitted-to (inline edit) */}
      <div className="flex items-center gap-1.5 min-w-0">
        <Send size={11} className="text-fg-5 flex-shrink-0" />
        <input
          value={venueVal}
          onChange={(e) => setVenueVal(e.target.value)}
          onBlur={() => { if ((entry?.submittedTo ?? "") !== venueVal) onSave({ submittedTo: venueVal }); }}
          onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }}
          placeholder="Journal / venue…"
          className="w-full bg-transparent text-[11.5px] text-fg-2 placeholder:text-fg-5 focus:outline-none border-b border-transparent focus:border-border py-0.5"
        />
      </div>
      {/* stage (inline edit) */}
      <select
        value={stage}
        onChange={(e) => onSave({ stage: e.target.value })}
        className={clsx("text-[10px] font-semibold uppercase tracking-wide rounded-md border px-2 py-1 cursor-pointer focus:outline-none appearance-none", STAGE_CLS[stage] ?? STAGE_CLS["Not submitted"])}
      >
        {STAGES.map((s) => <option key={s} value={s} className="bg-surface-1 text-fg normal-case">{s}</option>)}
      </select>
      {/* updated */}
      <span className="hidden md:block text-[10.5px] text-fg-4 tabular-nums">{fmtDate(entry?.updatedAt)}</span>
      {/* repo */}
      <a href={repo} target="_blank" rel="noreferrer" title="Open data repository"
        className="hidden md:inline-flex text-fg-5 hover:text-accent justify-self-start">
        <ExternalLink size={13} />
      </a>
    </div>
  );
}

/* ---------------- Board card ---------------- */
function PaperCard({ paper, n, onSelect, entry, onSave }: {
  paper: Paper; n: number; onSelect: (id: string) => void;
  entry?: Entry; onSave: (patch: Entry) => void;
}) {
  const Icon  = PAPER_ICONS[n]    ?? Shield;
  const icCls = PAPER_ICON_CLS[n] ?? "paper-icon-p1";
  const venue = VENUES[paper.id]  ?? "Preprint";

  const [venueVal, setVenueVal] = useState(entry?.submittedTo ?? "");
  useEffect(() => { setVenueVal(entry?.submittedTo ?? ""); }, [entry?.submittedTo]);
  const stage = stageOf(paper, entry);

  const defaultRepo = `${REPO_BASE}/${paper.root}`;
  const [repoVal, setRepoVal] = useState(entry?.dataRepo ?? defaultRepo);
  useEffect(() => { setRepoVal(entry?.dataRepo ?? defaultRepo); }, [entry?.dataRepo]); // eslint-disable-line react-hooks/exhaustive-deps
  const [repoName, setRepoName] = useState(entry?.repoName ?? "GitHub");
  useEffect(() => { setRepoName(entry?.repoName ?? "GitHub"); }, [entry?.repoName]);
  const [copied, setCopied] = useState(false);
  const copyRepo = () => { navigator.clipboard?.writeText(repoVal).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1400); }).catch(() => {}); };

  return (
    <div className="bg-surface-0 border border-border rounded-xl p-3.5 transition-all duration-150 hover:border-accent/50 hover:shadow-[0_6px_20px_-6px_rgba(0,0,0,0.12)] hover:-translate-y-0.5">
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
          {/* live stage dot + venue */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <span className={clsx("w-1.5 h-1.5 rounded-full", STAGE_DOT[stage])} title={stage} />
            <span className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-2 text-fg-4 border border-border">{venue}</span>
          </div>
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
