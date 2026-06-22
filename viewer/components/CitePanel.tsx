"use client";
import { useState, useRef, useEffect } from "react";
import { Quote, Copy, Check, X } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { ieeeCitation, bibtex } from "@/lib/cite";

export default function CitePanel({ paper }: { paper: Paper }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onEsc = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  const copy = async (text: string, which: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(which);
      setTimeout(() => setCopied(null), 1500);
    } catch (_) { /* clipboard unavailable */ }
  };

  const ieee = ieeeCitation(paper);
  const bib = bibtex(paper);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Cite this paper"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-[13px] font-medium border border-border bg-surface-1 text-fg-2 hover:border-accent/50 hover:text-accent transition-colors"
      >
        <Quote size={15} /> Cite
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-[min(92vw,470px)] z-50 bg-surface-1 border border-border rounded-xl shadow-2xl p-4 text-left">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[12px] font-bold text-fg">Cite this paper</span>
            <button onClick={() => setOpen(false)} aria-label="Close" className="text-fg-4 hover:text-fg">
              <X size={14} />
            </button>
          </div>

          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-fg-4">IEEE</span>
              <button onClick={() => copy(ieee, "ieee")} className="inline-flex items-center gap-1 text-[10px] text-fg-3 hover:text-accent transition-colors">
                {copied === "ieee" ? <Check size={11} /> : <Copy size={11} />}
                {copied === "ieee" ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="text-[11px] text-fg-2 leading-relaxed bg-surface-2 border border-border rounded-lg p-2.5">{ieee}</p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-fg-4">BibTeX</span>
              <button onClick={() => copy(bib, "bib")} className="inline-flex items-center gap-1 text-[10px] text-fg-3 hover:text-accent transition-colors">
                {copied === "bib" ? <Check size={11} /> : <Copy size={11} />}
                {copied === "bib" ? "Copied" : "Copy"}
              </button>
            </div>
            <pre className="text-[10px] text-fg-2 leading-relaxed bg-surface-2 border border-border rounded-lg p-2.5 overflow-x-auto font-mono whitespace-pre">{bib}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
