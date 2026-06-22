"use client";
import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Loader2, AlertCircle, EyeOff, Download } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT, paperFileName } from "@/lib/papers";

interface Props { paper: Paper }

/* Author identifiers to redact for double-blind review. */
const NAME_RE   = /Harshavardhan\s+Malla|H\.\s*Malla/gi;
const EMAIL_RE  = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const AFFIL_RE  = /Independent Researcher|Arizona Department of Transportation|Information Systems Security Engineer|\bADOT\b/gi;
const WITHHELD  = "*[Author name and affiliation withheld for double-blind peer review]*";

/** Strip author-identifying content from a manuscript so it can be shown / exported blind. */
function anonymize(md: string): string {
  let out = md;
  // 1. The author byline (a standalone line that carries the name) → withheld notice.
  out = out.replace(/^[^\n]*(?:Harshavardhan\s+Malla|H\.\s*Malla)[^\n]*$/gim, WITHHELD);
  // 2. Any residual inline name / email / affiliation mentions.
  out = out.replace(NAME_RE, "[Author]");
  out = out.replace(EMAIL_RE, "[email withheld]");
  out = out.replace(AFFIL_RE, "[affiliation withheld]");
  // 3. Acknowledgments sections often name people/employers — blank the body.
  out = out.replace(
    /^(#{1,4}\s*Acknowledge?ments?\s*)$([\s\S]*?)(?=^#{1,4}\s|$(?![\s\S]))/gim,
    "$1\n\n*[Withheld for double-blind peer review.]*\n",
  );
  return out;
}

export default function AnonymousViewer({ paper }: Props) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const mainPath = paper.manuscript.main;
  const absolutePath = mainPath.startsWith("/") ? mainPath : `${PAPERS_ROOT}/${paper.root}/${mainPath}`;
  const docDir = absolutePath.substring(0, absolutePath.lastIndexOf("/"));

  const anon = useMemo(() => (content ? anonymize(content) : ""), [content]);

  const markdownComponents = useMemo(() => ({
    img: ({ src, alt }: { src?: string; alt?: string }) => {
      if (!src) return null;
      const resolvedSrc =
        src.startsWith("http") || src.startsWith("/api/")
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
    a.href = url;
    a.download = `${paperFileName(paper.title, "anonymous")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Blind-review banner */}
      <div className="flex items-center justify-between gap-3 px-5 py-2.5 border-b border-border flex-shrink-0 bg-amber-500/10">
        <div className="flex items-center gap-2 min-w-0">
          <EyeOff size={13} className="text-amber-600 dark:text-amber-400 flex-shrink-0" />
          <span className="text-[11px] text-fg-2 truncate">
            <span className="font-semibold">Anonymized for double-blind review</span>
            <span className="text-fg-4"> — author name, affiliation, and email redacted from the manuscript.</span>
          </span>
        </div>
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
            <Loader2 size={24} className="animate-spin text-accent/50" />
            <span className="text-sm">Anonymizing manuscript…</span>
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
                prose-p:leading-7
                prose-a:no-underline hover:prose-a:underline
                prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-[11px] prose-code:border
                prose-pre:border prose-pre:text-[11px] prose-pre:rounded-xl
                prose-blockquote:not-italic prose-blockquote:rounded-r-lg
                prose-table:text-xs prose-table:border-collapse prose-table:rounded-lg
                prose-th:px-3 prose-th:py-2 prose-th:font-semibold
                prose-td:px-3 prose-td:py-2 prose-td:border prose-td:border-border
                prose-hr:my-8 prose-li:leading-7 prose-ul:my-3 prose-ol:my-3
                prose-img:rounded-lg prose-img:shadow-lg"
            >
              {anon}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
