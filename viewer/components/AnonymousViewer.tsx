"use client";
import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Loader2, AlertCircle, EyeOff, Download, ExternalLink, FileText } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT, paperFileName } from "@/lib/papers";

interface Props { paper: Paper }

/* Author identifiers to redact for the markdown fallback (paper21 has no LaTeX). */
const EMAIL_RE  = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const AFFIL_RE  = /Independent Researcher|Arizona Department of Transportation|Information Systems Security Engineer|\bADOT\b/gi;
const WITHHELD  = "*[Author name and affiliation withheld for double-blind peer review]*";

function anonymize(md: string): string {
  let out = md;
  out = out.replace(/^[^\n]*Harshavardhan\s+Malla[^\n]*$/gim, WITHHELD);
  out = out.replace(/https?:\/\/github\.com\/Harshavardhanmalla-Labs\/[^\s)>\]`"']*/gi, "[anonymized repository link]");
  out = out.replace(/Harshavardhanmalla(?:-Labs)?|Harshavardhan\s+Malla|H\.\s*Malla/gi, "[Author]");
  out = out.replace(EMAIL_RE, "[email withheld]");
  out = out.replace(AFFIL_RE, "[affiliation withheld]");
  out = out.replace(
    /^(#{1,4}\s*Acknowledge?ments?\s*)$([\s\S]*?)(?=^#{1,4}\s|$(?![\s\S]))/gim,
    "$1\n\n*[Withheld for double-blind peer review.]*\n",
  );
  return out;
}

export default function AnonymousViewer({ paper }: Props) {
  // Compiled anonymous PDF lives next to the submission PDF, named anonymous.pdf.
  const anonPdfAbs = paper.submissionPdf
    ? `${PAPERS_ROOT}/${paper.root}/${paper.submissionPdf.replace(/[^/]+\.pdf$/, "anonymous.pdf")}`
    : null;
  const serveUrl = anonPdfAbs ? `/api/serve?path=${encodeURIComponent(anonPdfAbs)}` : null;
  const dlName   = `${paperFileName(paper.title, "anonymous")}.pdf`;

  const [pdfExists, setPdfExists] = useState<boolean | null>(anonPdfAbs ? null : false);
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    if (!serveUrl) { setPdfExists(false); return; }
    let alive = true;
    setPdfExists(null);
    fetch(serveUrl, { method: "HEAD" })
      .then((r) => { if (alive) setPdfExists(r.ok); })
      .catch(() => { if (alive) setPdfExists(false); });
    return () => { alive = false; };
  }, [serveUrl]);

  const banner = (
    <div className="flex items-center gap-2 min-w-0">
      <EyeOff size={13} className="text-amber-600 dark:text-amber-400 flex-shrink-0" />
      <span className="text-[11px] text-fg-2 truncate">
        <span className="font-semibold">Anonymized for double-blind review</span>
        <span className="text-fg-4"> — author, affiliation, email, and identifying repo links redacted.</span>
      </span>
    </div>
  );

  // ── Checking ──
  if (pdfExists === null) {
    return (
      <div className="flex flex-col items-center gap-3 mt-24 text-fg-4">
        <Loader2 size={24} className="animate-spin text-accent/50" />
        <span className="text-sm">Loading anonymized PDF…</span>
      </div>
    );
  }

  // ── Compiled anonymous PDF ──
  if (pdfExists && serveUrl) {
    const iframeSrc = `${serveUrl}#toolbar=1&navpanes=0&zoom=${zoom}`;
    return (
      <div className="flex flex-col h-full min-h-0">
        <div className="flex items-center gap-3 px-5 py-2.5 border-b border-border flex-shrink-0 bg-amber-500/10">
          {banner}
          <div className="flex items-center gap-1 ml-auto flex-shrink-0">
            <button onClick={() => setZoom((z) => Math.max(50, z - 10))} className="p-1.5 rounded-lg hover:bg-surface-4 text-fg-4 hover:text-fg" title="Zoom out">–</button>
            <span className="text-[11px] text-fg-3 w-10 text-center font-mono tabular-nums select-none">{zoom}%</span>
            <button onClick={() => setZoom((z) => Math.min(200, z + 10))} className="p-1.5 rounded-lg hover:bg-surface-4 text-fg-4 hover:text-fg" title="Zoom in">+</button>
            <div className="w-px h-5 bg-border mx-1" />
            <a href={serveUrl} download={dlName}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] text-fg-3 hover:text-fg hover:bg-surface-3 border border-transparent hover:border-border transition-all" title={`Download ${dlName}`}>
              <Download size={12} />Download blind PDF
            </a>
            <a href={serveUrl} target="_blank" rel="noreferrer"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] text-fg-3 hover:text-fg hover:bg-surface-3 border border-transparent hover:border-border transition-all" title="Open in new tab">
              <ExternalLink size={12} />New tab
            </a>
          </div>
        </div>
        <div className="flex-1 min-h-0 bg-surface-0">
          <iframe key={iframeSrc} src={iframeSrc} className="w-full h-full border-0" title={`${paper.title} — anonymized PDF`} />
        </div>
        <div className="px-5 py-1.5 border-t border-border flex-shrink-0 bg-surface-1/60 flex items-center gap-2">
          <FileText size={11} className="text-fg-5" />
          <span className="text-[10px] text-fg-5">Recompiled from LaTeX with author set to “Anonymous”; acknowledgments and identifying links stripped. Submission-ready for double-blind venues.</span>
        </div>
      </div>
    );
  }

  // ── Markdown fallback (papers without a LaTeX/PDF submission) ──
  return <AnonymousMarkdown paper={paper} banner={banner} dlBase={paperFileName(paper.title, "anonymous")} />;
}

function AnonymousMarkdown({ paper, banner, dlBase }: { paper: Paper; banner: JSX.Element; dlBase: string }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  const mainPath = paper.manuscript.main;
  const absolutePath = mainPath.startsWith("/") ? mainPath : `${PAPERS_ROOT}/${paper.root}/${mainPath}`;
  const docDir = absolutePath.substring(0, absolutePath.lastIndexOf("/"));
  const anon = useMemo(() => (content ? anonymize(content) : ""), [content]);

  const markdownComponents = useMemo(() => ({
    img: ({ src, alt }: { src?: string; alt?: string }) => {
      if (!src) return null;
      const resolvedSrc = src.startsWith("http") || src.startsWith("/api/")
        ? src
        : `/api/serve?path=${encodeURIComponent(src.startsWith("/") ? src : `${docDir}/${src}`)}`;
      return (
        <span className="block my-6">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={resolvedSrc} alt={alt ?? ""} className="rounded-lg border border-border shadow-lg max-w-full mx-auto block" />
          {alt && <span className="block text-center text-xs text-fg-4 mt-2 italic">{alt}</span>}
        </span>
      );
    },
  }), [docDir]);

  useEffect(() => {
    setLoading(true); setError(null);
    fetch(`/api/file?path=${encodeURIComponent(absolutePath)}`)
      .then(async (r) => { if (!r.ok) throw new Error(`${r.status} ${r.statusText}`); return r.text(); })
      .then((t) => { setContent(t); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [absolutePath]);

  const download = () => {
    const blob = new Blob([anon], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${dlBase}.md`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex items-center justify-between gap-3 px-5 py-2.5 border-b border-border flex-shrink-0 bg-amber-500/10">
        {banner}
        {anon && !loading && (
          <button onClick={download}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] text-fg-3 hover:text-accent hover:bg-surface-3 border border-transparent hover:border-border transition-all flex-shrink-0">
            <Download size={12} />Download blind copy
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto px-6 py-8 min-h-0">
        {loading && (
          <div className="flex flex-col items-center gap-3 mt-20 text-fg-4">
            <Loader2 size={24} className="animate-spin text-accent/50" /><span className="text-sm">Anonymizing manuscript…</span>
          </div>
        )}
        {error && (
          <div className="flex flex-col items-center gap-3 mt-20">
            <div className="w-12 h-12 rounded-full bg-red-900/20 border border-red-800/40 flex items-center justify-center">
              <AlertCircle size={20} className="text-red-400" />
            </div>
            <span className="text-sm text-fg-3">Could not load manuscript</span>
            <code className="text-xs text-red-400/80 bg-red-900/10 px-3 py-1 rounded border border-red-900/30">{error}</code>
          </div>
        )}
        {!loading && !error && anon && (
          <div className="max-w-4xl mx-auto">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={markdownComponents}
              className="prose prose-sm max-w-none
                prose-headings:font-bold prose-headings:tracking-tight
                prose-h1:text-2xl prose-h2:text-xl prose-h3:text-base
                prose-p:leading-7 prose-a:no-underline hover:prose-a:underline
                prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-[11px] prose-code:border
                prose-pre:border prose-pre:text-[11px] prose-pre:rounded-xl
                prose-blockquote:not-italic prose-blockquote:rounded-r-lg
                prose-table:text-xs prose-table:border-collapse prose-table:rounded-lg
                prose-th:px-3 prose-th:py-2 prose-th:font-semibold
                prose-td:px-3 prose-td:py-2 prose-td:border prose-td:border-border
                prose-hr:my-8 prose-li:leading-7 prose-ul:my-3 prose-ol:my-3 prose-img:rounded-lg prose-img:shadow-lg"
            >
              {anon}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
