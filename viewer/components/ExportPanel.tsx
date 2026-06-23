"use client";
import { useState } from "react";
import { FileText, FileArchive, Loader2, Download, AlertCircle, CheckCircle2 } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { paperFileName } from "@/lib/papers";

interface Props { paper: Paper }
type Fmt = "docx" | "zip";

export default function ExportPanel({ paper }: Props) {
  const [busy, setBusy] = useState<Fmt | null>(null);
  const [done, setDone] = useState<Fmt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const base = paperFileName(paper.title);

  async function download(fmt: Fmt) {
    setBusy(fmt); setError(null); setDone(null);
    try {
      const r = await fetch(`/api/export?id=${encodeURIComponent(paper.id)}&format=${fmt}`);
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.detail || j.error || `${r.status} ${r.statusText}`);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fmt === "docx" ? `${base}.docx` : `${base}_latex.zip`;
      a.click();
      URL.revokeObjectURL(url);
      setDone(fmt);
    } catch (e: any) {
      setError(e.message || "export failed");
    } finally {
      setBusy(null);
    }
  }

  if (!paper.submissionPdf) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-fg-4">
        <FileText size={28} className="opacity-40" />
        <p className="text-sm">This paper has no LaTeX submission to export.</p>
      </div>
    );
  }

  const cards: { fmt: Fmt; Icon: typeof FileText; title: string; sub: string; out: string }[] = [
    { fmt: "docx", Icon: FileText, title: "Word document (.docx)",
      sub: "Editable manuscript with every figure and table placed inline in the body where it is referenced. For reviewers who annotate in Word.",
      out: `${base}.docx` },
    { fmt: "zip", Icon: FileArchive, title: "LaTeX bundle (.zip)",
      sub: "Full LaTeX sources with figures and tables, ready to compile to a camera-ready PDF for peer review.",
      out: `${base}_latex.zip` },
  ];

  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-[15px] font-bold text-fg mb-1">Export for peer review</h2>
        <p className="text-[12px] text-fg-4 mb-6">
          Generated on demand from the LaTeX source. Figures and tables are embedded — no manual assembly.
        </p>

        <div className="grid sm:grid-cols-2 gap-4">
          {cards.map(({ fmt, Icon, title, sub, out }) => (
            <div key={fmt} className="rounded-xl border border-border bg-surface-1/60 p-5 flex flex-col">
              <div className="flex items-center gap-2.5 mb-2">
                <span className="w-9 h-9 rounded-lg bg-accent/12 border border-accent/30 flex items-center justify-center flex-shrink-0">
                  <Icon size={16} className="text-accent" />
                </span>
                <span className="text-[13px] font-semibold text-fg">{title}</span>
              </div>
              <p className="text-[11.5px] text-fg-4 leading-relaxed flex-1 mb-4">{sub}</p>
              <code className="text-[10px] font-mono text-fg-5 truncate mb-3" title={out}>{out}</code>
              <button
                onClick={() => download(fmt)}
                disabled={busy !== null}
                className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-[12px] font-medium border transition-all
                  disabled:opacity-50 disabled:cursor-not-allowed
                  bg-accent/10 text-accent border-accent/30 hover:bg-accent/20"
              >
                {busy === fmt ? <Loader2 size={14} className="animate-spin" />
                  : done === fmt ? <CheckCircle2 size={14} />
                  : <Download size={14} />}
                {busy === fmt ? "Generating…" : done === fmt ? "Downloaded" : "Download"}
              </button>
            </div>
          ))}
        </div>

        {error && (
          <div className="mt-5 flex items-start gap-2 rounded-lg border border-red-800/40 bg-red-900/10 px-3 py-2.5">
            <AlertCircle size={14} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div className="min-w-0">
              <p className="text-[11.5px] text-red-300 font-medium">Export failed</p>
              <code className="text-[10px] text-red-400/80 break-words">{error}</code>
            </div>
          </div>
        )}

        <p className="text-[10.5px] text-fg-5 mt-6 leading-relaxed">
          Note: the Word conversion is a faithful automatic render of the LaTeX. Complex math and
          custom macros may need a light touch-up; the LaTeX bundle remains the source of truth.
        </p>
      </div>
    </div>
  );
}
