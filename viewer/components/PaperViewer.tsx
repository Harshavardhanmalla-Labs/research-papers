"use client";
import { useState, useEffect } from "react";
import { BookOpen, Image, BarChart2, FolderOpen, FileText, Code2, Github, Copy, Check, EyeOff } from "lucide-react";
import type { Paper } from "@/lib/papers";
import clsx from "clsx";
import AnonymousViewer from "./AnonymousViewer";

const REPO_BASE = "https://github.com/Harshavardhanmalla-Labs/research-papers/tree/main";
import ManuscriptViewer from "./ManuscriptViewer";
import FiguresGallery    from "./FiguresGallery";
import ResultsExplorer   from "./ResultsExplorer";
import ArtifactBrowser   from "./ArtifactBrowser";
import PdfViewer         from "./PdfViewer";
import LatexViewer       from "./LatexViewer";

interface Props { paper: Paper }

/* PDF badge per paper — P1,P2 are IEEE; P3 is ACM; P4 TBD */
const PDF_BADGE: Record<string, string> = {
  paper1: "IEEE",
  paper2:  "IEEE",
  paper3:  "IEEE",
  paper4: "Draft",
};

const TABS = [
  { key: "pdf",        label: "Submission PDF", Icon: FileText,   badge: null    },
  { key: "manuscript", label: "Manuscript",     Icon: BookOpen,   badge: null    },
  { key: "anonymous",  label: "Manuscript (anonymous)", Icon: EyeOff, badge: null },
  { key: "latex",      label: "LaTeX",           Icon: Code2,      badge: null    },
  { key: "figures",    label: "Figures",         Icon: Image,      badge: null    },
  { key: "results",    label: "Results",          Icon: BarChart2,  badge: null    },
  { key: "files",      label: "Files",            Icon: FolderOpen, badge: null    },
] as const;

type Tab = typeof TABS[number]["key"];

/* Top-rail colour per paper index (full-width layout, no sidebar) */
const PAPER_RAIL = [
  "border-t-sky-500",
  "border-t-teal-500",
  "border-t-violet-500",
  "border-t-rose-500",
  "border-t-amber-500",
  "border-t-emerald-500",
  "border-t-indigo-500",
  "border-t-fuchsia-500",
  "border-t-lime-500",
  "border-t-red-500",
];
const PAPER_RAIL_BG = [
  "from-sky-500/4",
  "from-teal-500/4",
  "from-violet-500/4",
  "from-rose-500/4",
  "from-amber-500/4",
  "from-emerald-500/4",
  "from-indigo-500/4",
  "from-fuchsia-500/4",
  "from-lime-500/4",
  "from-red-500/4",
];

export default function PaperViewer({ paper }: Props) {
  const [tab, setTab] = useState<Tab>("pdf");

  // Data-repository link + name (shared with the board tracker; defaults to the GitHub path).
  const defaultRepo = `${REPO_BASE}/${paper.root}`;
  const [repoUrl, setRepoUrl] = useState(defaultRepo);
  const [repoName, setRepoName] = useState("GitHub");
  const [copiedRepo, setCopiedRepo] = useState(false);
  useEffect(() => {
    setRepoUrl(defaultRepo); setRepoName("GitHub");
    fetch("/api/tracking").then((r) => (r.ok ? r.json() : {})).then((d: Record<string, any>) => {
      const e = d?.[paper.id];
      if (e?.dataRepo) setRepoUrl(e.dataRepo);
      if (e?.repoName) setRepoName(e.repoName);
    }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paper.id]);
  const copyRepo = () => { navigator.clipboard?.writeText(repoUrl).then(() => { setCopiedRepo(true); setTimeout(() => setCopiedRepo(false), 1500); }).catch(() => {}); };

  const paperIdx  = ["paper1","paper2","paper3","paper4","paper5","paper6","paper7","paper8","paper9","paper10"].indexOf(paper.id);
  const railColor = PAPER_RAIL[paperIdx]    ?? PAPER_RAIL[2];
  const railBg    = PAPER_RAIL_BG[paperIdx] ?? PAPER_RAIL_BG[2];

  return (
    <div className="flex flex-col h-full min-h-0">

      {/* ── Paper header ── */}
      <div className={clsx(
        "px-7 pt-5 pb-0 flex-shrink-0 border-b border-border backdrop-blur-md",
        "border-t-2 bg-gradient-to-b to-transparent bg-surface-1/80",
        railColor, railBg
      )}>
        <div className="flex items-start justify-between gap-6 mb-4">
          <div className="min-w-0 flex-1">
            <h1 className="text-[17px] font-bold text-fg leading-tight tracking-tight line-clamp-2">
              {paper.title}
            </h1>
            <p className="text-[11px] text-fg-3 mt-1.5 leading-snug line-clamp-2 font-medium">
              {paper.subtitle}
            </p>
          </div>
          <span
            className="flex-shrink-0 mt-0.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border"
            style={{
              backgroundColor: "rgb(var(--accent) / 0.12)",
              color: "rgb(var(--accent))",
              borderColor: "rgb(var(--accent) / 0.40)",
            }}
          >
            {paper.statusLabel}
          </span>
        </div>

        {/* ── Data repository (link + name) for journal submission forms ── */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <Github size={13} className="text-fg-4 flex-shrink-0" />
          <span className="text-[9px] font-bold uppercase tracking-widest text-fg-4 flex-shrink-0">Data repo</span>
          <a href={repoUrl} target="_blank" rel="noreferrer"
            className="text-[11px] font-mono text-accent hover:underline truncate max-w-[55%]" title={repoUrl}>
            {repoUrl.replace(/^https?:\/\//, "")}
          </a>
          <span className="text-fg-5 text-[11px]">·</span>
          <span className="text-[11px] text-fg-3">{repoName}</span>
          <button onClick={copyRepo} title="Copy data repository link"
            className="inline-flex items-center gap-1 text-[10px] text-fg-4 hover:text-accent transition-colors flex-shrink-0">
            {copiedRepo ? <Check size={12} /> : <Copy size={12} />}{copiedRepo ? "Copied" : "Copy"}
          </button>
        </div>

        {/* ── Tab strip ── */}
        <div className="flex gap-0 -mb-px overflow-x-auto hide-scrollbar">
          {TABS.map(({ key, label, Icon }) => {
            if (key === "pdf" && !paper.submissionPdf) return null;
            const active = tab === key;
            const badge = key === "pdf" ? (PDF_BADGE[paper.id] ?? "PDF") : null;
            return (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={clsx(
                  "flex items-center gap-2 px-5 py-3 text-[11px] font-semibold",
                  "border-b-2 whitespace-nowrap transition-all duration-150 flex-shrink-0",
                  active
                    ? ["border-accent text-accent", "tab-active-glow"]
                    : "border-transparent text-fg-4 hover:text-fg-2 hover:bg-surface-3/40"
                )}
              >
                <Icon size={13} className={active ? "text-accent" : "text-fg-4"} />
                {label}
                {badge && (
                  <span className={clsx(
                    "px-1.5 py-px rounded text-[8px] font-black uppercase tracking-wider",
                    active
                      ? "bg-accent/20 text-accent border border-accent/40"
                      : "bg-surface-3 text-fg-4 border border-border"
                  )}>
                    {badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Content ── */}
      <div key={tab} className="flex-1 min-h-0 overflow-hidden tab-content">
        {tab === "pdf"        && <PdfViewer       paper={paper} />}
        {tab === "manuscript" && <ManuscriptViewer paper={paper} />}
        {tab === "anonymous"  && <AnonymousViewer   paper={paper} />}
        {tab === "latex"      && <LatexViewer      paper={paper} />}
        {tab === "figures"    && <FiguresGallery   paper={paper} />}
        {tab === "results"    && <ResultsExplorer  paper={paper} />}
        {tab === "files"      && <ArtifactBrowser  paper={paper} />}
      </div>
    </div>
  );
}
