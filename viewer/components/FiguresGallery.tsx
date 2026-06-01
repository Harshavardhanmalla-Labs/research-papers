"use client";
import { useEffect, useState } from "react";
import { Loader2, ZoomIn, X, ImageOff, FileText, Download, ExternalLink, Images } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT } from "@/lib/papers";

interface FigFile { name: string; path: string; ext: string }
interface Props    { paper: Paper }

const IMG_EXTS = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]);
const PDF_EXT  = ".pdf";

export default function FiguresGallery({ paper }: Props) {
  const [figures, setFigures]   = useState<FigFile[]>([]);
  const [loading, setLoading]   = useState(true);
  const [lightbox, setLightbox] = useState<FigFile | null>(null);
  const [filter, setFilter]     = useState<"all" | "png" | "pdf">("png");

  const figDir = `${PAPERS_ROOT}/${paper.root}/${paper.figures}`;

  useEffect(() => {
    setLoading(true);
    fetch(`/api/tree?path=${encodeURIComponent(figDir)}`)
      .then((r) => r.json())
      .then((nodes: { name: string; path: string; ext: string; type: string }[]) => {
        const figs = nodes
          .filter((n) => n.type === "file" && (IMG_EXTS.has(n.ext) || n.ext === PDF_EXT))
          .map((n) => ({ name: n.name, path: n.path, ext: n.ext }));
        setFigures(figs);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [figDir]);

  const displayed = figures.filter((f) => {
    if (filter === "png") return IMG_EXTS.has(f.ext);
    if (filter === "pdf") return f.ext === PDF_EXT;
    return true;
  });

  const serveUrl    = (f: FigFile) => `/api/serve?path=${encodeURIComponent(f.path)}`;
  const pdfViewUrl  = (f: FigFile) => `${serveUrl(f)}#toolbar=1&navpanes=1&scrollbar=1`;
  const imgCount    = figures.filter((f) => IMG_EXTS.has(f.ext)).length;
  const pdfCount    = figures.filter((f) => f.ext === PDF_EXT).length;

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-5 py-3 border-b border-border flex-shrink-0 bg-surface-2/40">
        <Images size={14} className="text-fg-4" />
        <div className="flex gap-1.5">
          {(["all", "png", "pdf"] as const).map((v) => {
            const count = v === "all" ? figures.length : v === "png" ? imgCount : pdfCount;
            return (
              <button
                key={v}
                onClick={() => setFilter(v)}
                className={`px-3 py-1 rounded-lg text-[11px] font-medium border transition-all ${
                  filter === v
                    ? "bg-accent/20 text-accent border-accent/40 shadow-sm"
                    : "text-fg-3 border-transparent hover:border-border hover:text-fg-2 hover:bg-surface-4"
                }`}
              >
                {v === "all" ? "All" : v.toUpperCase()}
                <span className={`ml-1.5 text-[10px] ${filter === v ? "text-accent/70" : "text-fg-5"}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
        <span className="ml-auto text-[11px] text-fg-5">
          {displayed.length} figure{displayed.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto p-5 min-h-0">
        {loading && (
          <div className="flex flex-col items-center gap-3 mt-20 text-fg-4">
            <Loader2 size={24} className="animate-spin text-accent/50" />
            <span className="text-sm">Loading figures…</span>
          </div>
        )}
        {!loading && displayed.length === 0 && (
          <div className="flex flex-col items-center justify-center mt-20 text-fg-4 gap-3">
            <div className="w-14 h-14 rounded-full bg-surface-3 border border-border flex items-center justify-center">
              <ImageOff size={24} className="opacity-50" />
            </div>
            <span className="text-sm">No figures found in <code className="text-xs text-fg-3">{paper.figures}</code></span>
          </div>
        )}
        <div className="grid grid-cols-2 gap-5 xl:grid-cols-3 2xl:grid-cols-4">
          {displayed.map((fig) => (
            <div
              key={fig.path}
              className="group relative bg-surface-2 border border-border rounded-xl overflow-hidden cursor-pointer fig-card"
              onClick={() => setLightbox(fig)}
            >
              {IMG_EXTS.has(fig.ext) ? (
                <div className="aspect-[4/3] flex items-center justify-center bg-surface-3 overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={serveUrl(fig)}
                    alt={fig.name}
                    className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-[1.03]"
                  />
                </div>
              ) : (
                <div className="aspect-[4/3] flex flex-col items-center justify-center bg-surface-3 gap-2">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center
                    bg-red-50 border border-red-200
                    dark:bg-red-900/20 dark:border-red-800/30">
                    <FileText size={22} className="text-red-500 dark:text-red-400" />
                  </div>
                  <span className="text-xs text-fg-4 font-medium">PDF Figure</span>
                </div>
              )}
              {/* Hover overlay */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-200 flex items-center justify-center">
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/10">
                  <ZoomIn size={13} className="text-white" />
                  <span className="text-[11px] text-white font-medium">Open</span>
                </div>
              </div>
              {/* Label */}
              <div className="px-3 py-2.5 border-t border-border bg-surface-1/80">
                <p className="text-[11px] text-fg-2 truncate font-medium" title={fig.name}>{fig.name}</p>
                <p className="text-[10px] text-fg-5 mt-0.5 uppercase tracking-wide">{fig.ext.slice(1)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lightbox */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center p-6"
          onClick={() => setLightbox(null)}
        >
          <div className="absolute top-5 right-5 flex items-center gap-2 z-10">
            <a
              href={serveUrl(lightbox)}
              download={lightbox.name}
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-3/90 backdrop-blur-sm border border-border rounded-lg text-fg-2 hover:text-fg hover:border-accent/40 transition-colors text-xs font-medium"
            >
              <Download size={13} /> Download
            </a>
            <a
              href={serveUrl(lightbox)}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-3/90 backdrop-blur-sm border border-border rounded-lg text-fg-2 hover:text-fg hover:border-accent/40 transition-colors text-xs font-medium"
            >
              <ExternalLink size={13} /> New tab
            </a>
            <button
              className="p-2 bg-surface-3/90 backdrop-blur-sm border border-border rounded-lg text-fg-3 hover:text-white hover:bg-red-500/80 hover:border-red-500 transition-all duration-150"
              onClick={() => setLightbox(null)}
            >
              <X size={16} />
            </button>
          </div>

          <div
            className="max-w-6xl w-full max-h-[90vh] bg-surface-1 rounded-2xl overflow-hidden border border-border shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 px-5 py-3 border-b border-border flex-shrink-0">
              {IMG_EXTS.has(lightbox.ext)
                ? <Images size={14} className="text-accent" />
                : <FileText size={14} className="text-red-400" />
              }
              <span className="text-sm text-fg font-medium flex-1 truncate">{lightbox.name}</span>
              <span className="text-[10px] text-fg-4 uppercase tracking-wide bg-surface-3 px-2 py-0.5 rounded">
                {lightbox.ext.slice(1)}
              </span>
            </div>

            {IMG_EXTS.has(lightbox.ext) ? (
              <div className="flex items-center justify-center p-6 overflow-auto flex-1 min-h-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={serveUrl(lightbox)}
                  alt={lightbox.name}
                  className="max-w-full max-h-full object-contain rounded-lg"
                  style={{ maxHeight: "calc(90vh - 7rem)" }}
                />
              </div>
            ) : (
              <div className="flex flex-col flex-1 min-h-0">
                <iframe
                  src={pdfViewUrl(lightbox)}
                  className="flex-1 w-full border-0"
                  style={{ minHeight: "75vh" }}
                  title={lightbox.name}
                />
                <div className="px-4 py-2 border-t border-border bg-surface-2/60 flex-shrink-0 flex items-center justify-between">
                  <span className="text-[10px] text-fg-5">Browser PDF viewer · Use toolbar above to navigate</span>
                  <a
                    href={serveUrl(lightbox)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-[10px] text-accent hover:underline"
                  >
                    <ExternalLink size={10} /> Open in new tab
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
