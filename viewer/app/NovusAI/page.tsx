"use client";
import { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, ShieldHalf, ExternalLink, StickyNote, Scale, X, Loader2, FileText, AlignLeft, User2, Building2, ListChecks } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ThemeToggle from "@/components/ThemeToggle";
import { NOVUS_PAPERS, NOVUS_STATUS, NOVUS_PATENTS, type NovusStatus, type NovusPaper, type NovusPatent } from "@/lib/novus";
import { PAPERS_ROOT } from "@/lib/papers";

const PATENT_STATUS_CLS: Record<string, string> = {
  draft: "text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-800 bg-amber-500/10",
  filed: "text-sky-700 dark:text-sky-400 border-sky-300 dark:border-sky-800 bg-sky-500/10",
  pending: "text-violet-700 dark:text-violet-400 border-violet-300 dark:border-violet-800 bg-violet-500/10",
  granted: "text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800 bg-emerald-500/10",
};

/* Extract a "## Heading" section (through the next "## ") from the patent markdown. */
function grabSection(md: string, name: string): string {
  const re = new RegExp(`(^|\\n)##\\s+${name}[^\\n]*[\\s\\S]*?(?=\\n##\\s|$)`, "i");
  const m = md.match(re);
  return m ? m[0].trim() : "";
}

const PATENT_TABS = [
  { key: "full",     label: "Full document", Icon: FileText },
  { key: "claims",   label: "Claims",        Icon: ListChecks },
  { key: "abstract", label: "Abstract",      Icon: AlignLeft },
] as const;
type PatentTab = typeof PATENT_TABS[number]["key"];

/* Full-screen patent reader styled like the papers viewer: rail-coloured header
   (title, kind, status, metadata) + tab strip + scrolling content pane. */
function PatentReader({ patent, onClose }: { patent: NovusPatent; onClose: () => void }) {
  const [md, setMd] = useState<string | null>(null);
  const [err, setErr] = useState(false);
  const [tab, setTab] = useState<PatentTab>("full");

  useEffect(() => {
    const abs = `${PAPERS_ROOT}/${patent.docPath}`;
    fetch(`/api/file?path=${encodeURIComponent(abs)}`)
      .then((r) => (r.ok ? r.text() : Promise.reject()))
      .then(setMd)
      .catch(() => setErr(true));
  }, [patent.docPath]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const body = useMemo(() => {
    if (!md) return "";
    if (tab === "claims")   return grabSection(md, "Claims") || md;
    if (tab === "abstract") return grabSection(md, "Abstract") || md;
    return md;
  }, [md, tab]);

  const statusLabel = PATENT_STATUS_CLS[patent.status] ?? "";

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-surface-0">
      {/* Header — mirrors the papers viewer */}
      <div className="px-7 pt-5 pb-0 flex-shrink-0 border-b border-border backdrop-blur-md border-t-2 border-t-violet-500 bg-gradient-to-b from-violet-500/[0.04] to-transparent bg-surface-1/80">
        <div className="flex items-start justify-between gap-6 mb-3">
          <div className="min-w-0 flex-1">
            <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-fg-4 mb-1.5">
              <Scale size={12} className="text-violet-500" /> {patent.kind}
            </span>
            <h1 className="text-[17px] font-bold text-fg leading-tight tracking-tight line-clamp-2">{patent.title}</h1>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border ${statusLabel}`}>{patent.status}</span>
            <button onClick={onClose} title="Close (Esc)" className="inline-flex items-center justify-center w-7 h-7 rounded-md border border-border text-fg-4 hover:text-fg hover:border-accent/50 transition-colors">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Metadata row — like the papers viewer's data-repo strip */}
        <div className="flex items-center gap-x-5 gap-y-1 mb-3 flex-wrap text-[11px] text-fg-4">
          <span className="inline-flex items-center gap-1.5"><User2 size={12} /> Inventor: <span className="text-fg-3 font-medium">{patent.inventor}</span></span>
          <span className="inline-flex items-center gap-1.5"><Building2 size={12} /> Assignee: <span className="text-fg-3 font-medium">{patent.assignee}</span></span>
          <span className="inline-flex items-center gap-1.5"><ListChecks size={12} /> <span className="text-fg-3 font-semibold">{patent.claims}</span> claims ({patent.independentClaims} independent)</span>
        </div>

        {/* Tab strip */}
        <div className="flex gap-0 -mb-px overflow-x-auto hide-scrollbar">
          {PATENT_TABS.map(({ key, label, Icon }) => {
            const active = tab === key;
            return (
              <button key={key} onClick={() => setTab(key)}
                className={`flex items-center gap-2 px-5 py-3 text-[11px] font-semibold border-b-2 whitespace-nowrap transition-all duration-150 flex-shrink-0 ${active ? "border-accent text-accent" : "border-transparent text-fg-4 hover:text-fg-2 hover:bg-surface-3/40"}`}>
                <Icon size={13} className={active ? "text-accent" : "text-fg-4"} /> {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-7 py-8">
          {err ? (
            <p className="text-[13px] text-red-500">Could not load the patent document.</p>
          ) : md === null ? (
            <p className="flex items-center gap-2 text-[13px] text-fg-4"><Loader2 size={14} className="animate-spin" /> Loading…</p>
          ) : (
            <article className="prose-patent">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
            </article>
          )}
        </div>
      </div>
    </div>
  );
}

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
  const [openPatent, setOpenPatent] = useState<NovusPatent | null>(null);

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

        {/* Patents & IP */}
        {NOVUS_PATENTS.length > 0 && (
          <section className="mb-12">
            <div className="flex items-center gap-2.5 mb-4">
              <Scale size={16} className="text-accent" />
              <h2 className="font-serif text-[20px] font-semibold text-fg">Patents &amp; Intellectual Property</h2>
              <span className="text-[11px] font-mono text-fg-4">{String(NOVUS_PATENTS.length).padStart(2, "0")}</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {NOVUS_PATENTS.map((pt) => (
                <button
                  key={pt.id}
                  onClick={() => setOpenPatent(pt)}
                  className="text-left group border border-border bg-surface-1 rounded-xl p-5 hover:border-accent/45 hover:shadow-[0_4px_18px_-6px_rgba(0,0,0,0.12)] transition-all"
                >
                  <div className="flex items-center justify-between gap-3 mb-2.5">
                    <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-fg-4">
                      <FileText size={12} /> {pt.kind}
                    </span>
                    <span className={`text-[9.5px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${PATENT_STATUS_CLS[pt.status] ?? ""}`}>
                      {pt.status}
                    </span>
                  </div>
                  <h3 className="font-serif text-[15px] leading-snug text-fg group-hover:text-accent transition-colors">
                    {pt.title}
                  </h3>
                  <p className="text-[12px] text-fg-4 leading-relaxed mt-2 line-clamp-4">{pt.abstract}</p>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3.5 pt-3 border-t border-border text-[11px] text-fg-4">
                    <span>Inventor: <span className="text-fg-3 font-medium">{pt.inventor}</span></span>
                    <span>Assignee: <span className="text-fg-3 font-medium">{pt.assignee}</span></span>
                    <span><span className="text-fg-3 font-semibold">{pt.claims}</span> claims ({pt.independentClaims} independent)</span>
                    <span className="inline-flex items-center gap-1 text-accent font-medium ml-auto group-hover:underline">Read full patent <ExternalLink size={11} /></span>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

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

      {openPatent && <PatentReader patent={openPatent} onClose={() => setOpenPatent(null)} />}
    </div>
  );
}
