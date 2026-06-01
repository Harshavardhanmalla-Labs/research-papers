"use client";
import { useState } from "react";
import { BookOpen, Image, BarChart2, FolderOpen, FileText } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { STATUS_COLORS } from "@/lib/papers";
import clsx from "clsx";
import ManuscriptViewer from "./ManuscriptViewer";
import FiguresGallery    from "./FiguresGallery";
import ResultsExplorer   from "./ResultsExplorer";
import ArtifactBrowser   from "./ArtifactBrowser";
import PdfViewer         from "./PdfViewer";

interface Props { paper: Paper }

/* PDF badge per paper — P1,P2 are IEEE; P3 is ACM; P4 TBD */
const PDF_BADGE: Record<string, string> = {
  paper1: "IEEE",
  paper2: "CSET",
  paper3: "ACM",
  paper4: "Draft",
};

const TABS = [
  { key: "pdf",        label: "Submission PDF", Icon: FileText,   badge: null    },
  { key: "manuscript", label: "Manuscript",     Icon: BookOpen,   badge: null    },
  { key: "figures",    label: "Figures",         Icon: Image,      badge: null    },
  { key: "results",    label: "Results",          Icon: BarChart2,  badge: null    },
  { key: "files",      label: "Files",            Icon: FolderOpen, badge: null    },
] as const;

type Tab = typeof TABS[number]["key"];

/* Left-rail colour per paper index */
const PAPER_RAIL = [
  "border-l-sky-500",
  "border-l-teal-500",
  "border-l-violet-500",
  "border-l-rose-500",
];
const PAPER_RAIL_BG = [
  "from-sky-500/5",
  "from-teal-500/5",
  "from-violet-500/5",
  "from-rose-500/5",
];

export default function PaperViewer({ paper }: Props) {
  const [tab, setTab] = useState<Tab>("pdf");

  const paperIdx  = ["paper1","paper2","paper3","paper4"].indexOf(paper.id);
  const railColor = PAPER_RAIL[paperIdx]  ?? PAPER_RAIL[2];
  const railBg    = PAPER_RAIL_BG[paperIdx] ?? PAPER_RAIL_BG[2];

  return (
    <div className="flex flex-col h-full min-h-0">

      {/* ── Paper header ── */}
      <div className={clsx(
        "px-7 pt-5 pb-0 flex-shrink-0 border-b border-border backdrop-blur-md",
        "border-l-4 bg-gradient-to-r to-transparent bg-surface-1/80",
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
          <span className={clsx(
            "flex-shrink-0 mt-0.5 px-3 py-1 rounded-full text-[10px] font-bold border uppercase tracking-widest",
            STATUS_COLORS[paper.status]
          )}>
            {paper.statusLabel}
          </span>
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
        {tab === "figures"    && <FiguresGallery   paper={paper} />}
        {tab === "results"    && <ResultsExplorer  paper={paper} />}
        {tab === "files"      && <ArtifactBrowser  paper={paper} />}
      </div>
    </div>
  );
}
