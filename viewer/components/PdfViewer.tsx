"use client";
import { useState } from "react";
import { ExternalLink, FileText, ZoomIn, ZoomOut, RotateCcw, Download } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT } from "@/lib/papers";

interface Props { paper: Paper }

const FORMAT_BADGE: Record<string, { label: string; format: string }> = {
  paper1: { label: "IEEE",  format: "Two-column IEEEtran · tectonic / XeTeX" },
  paper2: { label: "CSET",  format: "IEEE IEEEtran compsoc · tectonic / XeTeX" },
  paper3: { label: "ACM",   format: "ACM sigconf · tectonic / XeTeX" },
  paper4: { label: "Draft", format: "Two-column IEEEtran · tectonic / XeTeX" },
};

export default function PdfViewer({ paper }: Props) {
  const [zoom, setZoom] = useState(100);
  const fmt = FORMAT_BADGE[paper.id] ?? { label: "PDF", format: "Compiled with tectonic / XeTeX" };

  if (!paper.submissionPdf) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-fg-4">
        <div className="w-16 h-16 rounded-2xl bg-surface-3 border border-border flex items-center justify-center">
          <FileText size={28} className="opacity-40" />
        </div>
        <p className="text-sm">No submission PDF configured for this paper</p>
      </div>
    );
  }

  const absPath = `${PAPERS_ROOT}/${paper.root}/${paper.submissionPdf}`;
  const serveUrl = `/api/serve?path=${encodeURIComponent(absPath)}`;
  // #zoom=N forces the browser PDF viewer zoom (Chrome/Edge support it; Firefox ignores)
  const iframeSrc = `${serveUrl}#toolbar=1&navpanes=0&zoom=${zoom}`;

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-5 py-2.5 border-b border-border flex-shrink-0 bg-surface-2/40">
        <FileText size={14} className="text-accent flex-shrink-0" />

        {/* File label */}
        <span className="text-[11px] text-fg-3 font-mono truncate flex-1">
          {paper.submissionPdf}
        </span>

        {/* Format badge */}
        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider flex-shrink-0
          bg-accent-muted text-accent-dim border border-accent/30
          dark:bg-accent-muted dark:text-accent dark:border-accent/30">
          {fmt.label}
        </span>

        {/* Zoom controls */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => setZoom((z) => Math.max(50, z - 10))}
            className="p-1.5 rounded-lg hover:bg-surface-4 text-fg-4 hover:text-fg transition-colors"
            title="Zoom out"
          >
            <ZoomOut size={13} />
          </button>
          <span className="text-[11px] text-fg-3 w-10 text-center font-mono tabular-nums select-none">
            {zoom}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(200, z + 10))}
            className="p-1.5 rounded-lg hover:bg-surface-4 text-fg-4 hover:text-fg transition-colors"
            title="Zoom in"
          >
            <ZoomIn size={13} />
          </button>
          <button
            onClick={() => setZoom(100)}
            className="p-1.5 rounded-lg hover:bg-surface-4 text-fg-4 hover:text-fg transition-colors"
            title="Reset zoom"
          >
            <RotateCcw size={12} />
          </button>
        </div>

        <div className="w-px h-5 bg-border flex-shrink-0" />

        {/* Download */}
        <a
          href={serveUrl}
          download={`${paper.id}_submission.pdf`}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] text-fg-3 hover:text-fg hover:bg-surface-3 border border-transparent hover:border-border transition-all"
          title="Download PDF"
        >
          <Download size={12} />
          Download
        </a>

        {/* Open in new tab */}
        <a
          href={serveUrl}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] text-fg-3 hover:text-fg hover:bg-surface-3 border border-transparent hover:border-border transition-all"
          title="Open in new tab"
        >
          <ExternalLink size={12} />
          New tab
        </a>
      </div>

      {/* PDF iframe — takes all remaining height */}
      <div className="flex-1 min-h-0 bg-surface-0">
        <iframe
          key={iframeSrc}
          src={iframeSrc}
          className="w-full h-full border-0"
          title={`${paper.title} — IEEE Submission PDF`}
        />
      </div>

      {/* Footer note */}
      <div className="px-5 py-1.5 border-t border-border flex-shrink-0 bg-surface-1/60 flex items-center justify-between">
        <span className="text-[10px] text-fg-5">
          {fmt.format}
        </span>
        <span className="text-[10px] text-fg-5 font-mono">
          {paper.root}/{paper.submissionPdf}
        </span>
      </div>
    </div>
  );
}
