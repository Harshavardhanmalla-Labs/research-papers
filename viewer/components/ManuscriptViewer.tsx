"use client";
import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Loader2, AlertCircle, BookOpen, Clock, AlignLeft } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT } from "@/lib/papers";

interface Props { paper: Paper }
type DocKey = "main" | "supplemental" | string;

function readingStats(text: string) {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return { words, minutes: Math.max(1, Math.round(words / 200)) };
}

export default function ManuscriptViewer({ paper }: Props) {
  const [activeDoc, setActiveDoc] = useState<DocKey>("main");
  const [content, setContent]     = useState<string>("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);

  const resolvedRoot = `${PAPERS_ROOT}/${paper.root}`;

  const docs: { key: DocKey; label: string; path: string }[] = [
    { key: "main", label: "Main draft", path: paper.manuscript.main },
    ...(paper.manuscript.supplemental
      ? [{ key: "supplemental", label: "Supplemental", path: paper.manuscript.supplemental }]
      : []),
    ...(paper.manuscript.extras ?? []).map((e) => ({ key: e.label, label: e.label, path: e.path })),
  ];

  const activeDocPath = docs.find((d) => d.key === activeDoc)?.path ?? docs[0].path;
  const absolutePath = activeDocPath.startsWith("/")
    ? activeDocPath
    : `${resolvedRoot}/${activeDocPath}`;

  const docDir = absolutePath.substring(0, absolutePath.lastIndexOf("/"));

  const markdownComponents = useMemo(() => ({
    // eslint-disable-next-line @next/next/no-img-element
    img: ({ src, alt }: { src?: string; alt?: string }) => {
      if (!src) return null;
      const resolvedSrc =
        src.startsWith("http") || src.startsWith("/api/")
          ? src
          : `/api/serve?path=${encodeURIComponent(
              src.startsWith("/") ? src : `${docDir}/${src}`
            )}`;
      return (
        <span className="block my-6">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={resolvedSrc}
            alt={alt ?? ""}
            className="rounded-lg border border-border shadow-lg max-w-full mx-auto block"
          />
          {alt && <span className="block text-center text-xs text-fg-4 mt-2 italic">{alt}</span>}
        </span>
      );
    },
  }), [docDir]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/file?path=${encodeURIComponent(absolutePath)}`)
      .then(async (r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.text();
      })
      .then((t) => { setContent(t); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [absolutePath]);

  const stats = content ? readingStats(content) : null;

  return (
    <div className="flex flex-col h-full min-h-0">

      {/* ── Doc selector bar ── fixed single row, scrollable tabs */}
      <div className="flex items-center border-b border-border flex-shrink-0 bg-surface-2/40">
        {/* Icon — never wraps */}
        <div className="pl-4 pr-2 py-2.5 flex-shrink-0">
          <BookOpen size={13} className="text-accent" />
        </div>

        {/* Scrollable tab strip */}
        <div className="flex-1 min-w-0 overflow-x-auto">
          <div className="flex gap-1 py-2.5 pr-4" style={{ width: "max-content" }}>
            {docs.map((d) => (
              <button
                key={d.key}
                onClick={() => setActiveDoc(d.key)}
                className={`px-3 py-1 rounded-lg text-[11px] font-medium whitespace-nowrap transition-all duration-100 flex-shrink-0 ${
                  activeDoc === d.key
                    ? "bg-accent/20 text-accent border border-accent/40 shadow-sm"
                    : "text-fg-3 hover:text-fg-2 hover:bg-surface-4 border border-transparent"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Reading stats — always far right, never pushed */}
        {stats && !loading && (
          <div className="flex items-center gap-3 px-4 flex-shrink-0 border-l border-border py-2.5">
            <span className="flex items-center gap-1 text-[10px] text-fg-5 whitespace-nowrap">
              <AlignLeft size={10} />
              {stats.words.toLocaleString()}w
            </span>
            <span className="flex items-center gap-1 text-[10px] text-fg-5 whitespace-nowrap">
              <Clock size={10} />
              {stats.minutes}m
            </span>
          </div>
        )}
      </div>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto px-6 py-8 min-h-0">
        {loading && (
          <div className="flex flex-col items-center gap-3 mt-20 text-fg-4">
            <Loader2 size={24} className="animate-spin text-accent/50" />
            <span className="text-sm">Loading document…</span>
          </div>
        )}
        {error && (
          <div className="flex flex-col items-center gap-3 mt-20">
            <div className="w-12 h-12 rounded-full bg-red-900/20 border border-red-800/40 flex items-center justify-center">
              <AlertCircle size={20} className="text-red-400" />
            </div>
            <span className="text-sm text-fg-3">Could not load file</span>
            <code className="text-xs text-red-400/80 bg-red-900/10 px-3 py-1 rounded border border-red-900/30">
              {error}
            </code>
          </div>
        )}
        {!loading && !error && !content && (
          <div className="flex flex-col items-center gap-3 mt-20 text-fg-4">
            <BookOpen size={32} className="opacity-40" />
            <span className="text-sm">Empty document</span>
          </div>
        )}
        {!loading && !error && content && (
          <div className="max-w-4xl mx-auto">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={markdownComponents}
              className="prose prose-sm max-w-none
                prose-headings:font-bold prose-headings:tracking-tight
                prose-h1:text-2xl
                prose-h2:text-xl
                prose-h3:text-base
                prose-p:leading-7
                prose-a:no-underline hover:prose-a:underline
                prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-[11px] prose-code:border
                prose-pre:border prose-pre:text-[11px] prose-pre:rounded-xl
                prose-blockquote:not-italic prose-blockquote:rounded-r-lg
                prose-table:text-xs prose-table:border-collapse prose-table:rounded-lg
                prose-th:px-3 prose-th:py-2 prose-th:font-semibold
                prose-td:px-3 prose-td:py-2 prose-td:border prose-td:border-border
                prose-hr:my-8
                prose-li:leading-7
                prose-ul:my-3 prose-ol:my-3
                prose-img:rounded-lg prose-img:shadow-lg"
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
