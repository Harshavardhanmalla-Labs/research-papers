"use client";
import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Loader2, AlertCircle, Mail, Building2, Copy, Check } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT } from "@/lib/papers";

interface Props { paper: Paper }

/** Pull the target venue out of the first heading: "# Cover letter — <Venue>". */
function parseVenue(md: string): string | null {
  const m = md.match(/^#\s*Cover letter\s*[—–-]\s*(.+)$/im);
  return m ? m[1].trim() : null;
}

export default function CoverLetterViewer({ paper }: Props) {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [copied, setCopied]   = useState(false);

  const path = paper.coverLetter
    ? `${PAPERS_ROOT}/${paper.root}/${paper.coverLetter}`
    : null;

  useEffect(() => {
    if (!path) return;
    setLoading(true);
    setError(null);
    fetch(`/api/file?path=${encodeURIComponent(path)}`)
      .then(async (r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.text();
      })
      .then((t) => { setContent(t); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [path]);

  const venue = useMemo(() => (content ? parseVenue(content) : null), [content]);
  // Drop the leading "# Cover letter — Venue" heading; it's shown in the letterhead.
  const body  = useMemo(
    () => content.replace(/^#\s*Cover letter\s*[—–-].*$/im, "").replace(/^\s+/, ""),
    [content]
  );

  const copyAll = () =>
    navigator.clipboard?.writeText(content)
      .then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); })
      .catch(() => {});

  if (!path) {
    return (
      <div className="flex flex-col items-center gap-3 mt-24 text-fg-4">
        <Mail size={32} className="opacity-30" />
        <span className="text-sm">No cover letter for this paper yet.</span>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-surface-2/30">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {loading && (
          <div className="flex flex-col items-center gap-3 mt-20 text-fg-4">
            <Loader2 size={24} className="animate-spin text-accent/50" />
            <span className="text-sm">Loading cover letter…</span>
          </div>
        )}
        {error && (
          <div className="flex flex-col items-center gap-3 mt-20">
            <div className="w-12 h-12 rounded-full bg-red-900/20 border border-red-800/40 flex items-center justify-center">
              <AlertCircle size={20} className="text-red-400" />
            </div>
            <span className="text-sm text-fg-3">Could not load cover letter</span>
            <code className="text-xs text-red-400/80 bg-red-900/10 px-3 py-1 rounded border border-red-900/30">
              {error}
            </code>
          </div>
        )}
        {!loading && !error && content && (
          /* Letter "page" — a sheet floating on the surface */
          <div className="rounded-2xl border border-border bg-surface-1 shadow-xl overflow-hidden">
            {/* Letterhead */}
            <div className="flex items-center justify-between gap-4 px-8 py-5 border-b border-border bg-gradient-to-b from-accent/[0.06] to-transparent">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-accent/12 border border-accent/30 flex items-center justify-center flex-shrink-0">
                  <Mail size={16} className="text-accent" />
                </div>
                <div className="min-w-0">
                  <div className="text-[10px] font-bold uppercase tracking-widest text-fg-4">
                    Submission cover letter
                  </div>
                  {venue && (
                    <div className="flex items-center gap-1.5 mt-0.5 text-[13px] font-semibold text-fg truncate">
                      <Building2 size={12} className="text-accent flex-shrink-0" />
                      {venue}
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={copyAll}
                title="Copy cover letter"
                className="inline-flex items-center gap-1.5 text-[10px] font-medium text-fg-4 hover:text-accent transition-colors flex-shrink-0 px-2.5 py-1.5 rounded-lg border border-border hover:border-accent/40"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}{copied ? "Copied" : "Copy"}
              </button>
            </div>

            {/* Letter body */}
            <div className="px-8 py-7">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="prose prose-sm max-w-none
                  prose-headings:font-bold prose-headings:tracking-tight
                  prose-h2:text-base prose-h2:mt-7 prose-h2:mb-2
                  prose-h3:text-sm
                  prose-p:leading-7 prose-p:text-fg-2
                  prose-strong:text-fg
                  prose-a:no-underline hover:prose-a:underline prose-a:text-accent
                  prose-hr:my-6 prose-hr:border-border
                  prose-li:leading-7 prose-li:text-fg-2
                  prose-ul:my-2"
              >
                {body}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
