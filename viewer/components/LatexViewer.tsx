"use client";
import { useState, useEffect, useMemo } from "react";
import { FileCode2, Copy, Check, Download } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT } from "@/lib/papers";
import clsx from "clsx";

interface Node { name: string; path: string; type: "file" | "dir"; ext?: string; children?: Node[] }
interface TexFile { name: string; path: string; rel: string }

const TEX_EXT = new Set([".tex", ".bib", ".cls", ".bst", ".sty"]);

function flatten(nodes: Node[], base: string, acc: TexFile[] = []): TexFile[] {
  for (const n of nodes) {
    if (n.type === "dir") flatten(n.children || [], base, acc);
    else if (TEX_EXT.has(n.ext || "")) acc.push({ name: n.name, path: n.path, rel: n.path.replace(base + "/", "") });
  }
  return acc;
}

export default function LatexViewer({ paper }: { paper: Paper }) {
  const baseDir = useMemo(() => {
    const sub = paper.submissionPdf ? paper.submissionPdf.split("/").slice(0, -1).join("/") : "";
    return `${PAPERS_ROOT}/${paper.root}${sub ? "/" + sub : ""}`;
  }, [paper]);

  const [files, setFiles] = useState<TexFile[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/tree?path=${encodeURIComponent(baseDir)}`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        const arr: Node[] = Array.isArray(data) ? data : [];
        const fs = flatten(arr, baseDir);
        fs.sort((a, b) => {
          const rank = (x: TexFile) => (x.name === "main.tex" ? 0 : x.name.endsWith(".tex") ? 1 : 2);
          return rank(a) - rank(b) || a.rel.localeCompare(b.rel);
        });
        setFiles(fs);
        const first = fs.find((f) => f.name === "main.tex") ?? fs[0];
        setSel(first?.path ?? null);
        setLoading(false);
      })
      .catch(() => { setFiles([]); setLoading(false); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseDir]);

  useEffect(() => {
    if (!sel) { setContent(""); return; }
    fetch(`/api/file?path=${encodeURIComponent(sel)}`).then((r) => (r.ok ? r.text() : "")).then(setContent).catch(() => setContent(""));
  }, [sel]);

  const copy = async () => {
    try { await navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch (_) {}
  };

  if (loading) return <div className="flex items-center justify-center h-full text-fg-4 text-sm">Loading LaTeX source…</div>;
  if (!files.length) return <div className="flex items-center justify-center h-full text-fg-4 text-sm">No LaTeX source found for this paper.</div>;

  const cur = files.find((f) => f.path === sel);

  return (
    <div className="flex h-full min-h-0">
      <div className="w-56 flex-shrink-0 border-r border-border overflow-y-auto bg-surface-1/40 p-2">
        <p className="text-[9px] font-bold uppercase tracking-widest text-fg-5 px-2 mb-2">Source files · {files.length}</p>
        {files.map((f) => (
          <button
            key={f.path}
            onClick={() => setSel(f.path)}
            className={clsx(
              "w-full text-left px-2.5 py-1.5 rounded-lg text-[11px] font-mono truncate transition-colors flex items-center gap-1.5",
              sel === f.path ? "bg-accent/15 text-accent" : "text-fg-3 hover:bg-surface-3/50 hover:text-fg"
            )}
          >
            <FileCode2 size={12} className="flex-shrink-0" />
            <span className="truncate">{f.rel}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 min-w-0 flex flex-col">
        <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface-2/40 flex-shrink-0">
          <span className="text-[11px] font-mono text-fg-3 truncate">{cur?.rel}</span>
          <div className="flex items-center gap-3 flex-shrink-0">
            <button onClick={copy} className="inline-flex items-center gap-1 text-[10px] text-fg-3 hover:text-accent transition-colors">
              {copied ? <Check size={12} /> : <Copy size={12} />}{copied ? "Copied" : "Copy"}
            </button>
            <a href={`/api/file?path=${encodeURIComponent(sel || "")}`} download={cur?.name}
              className="inline-flex items-center gap-1 text-[10px] text-fg-3 hover:text-accent transition-colors">
              <Download size={12} />Download
            </a>
          </div>
        </div>
        <pre className="flex-1 min-h-0 overflow-auto p-4 text-[11.5px] leading-[1.55] font-mono text-fg-2 whitespace-pre">{content}</pre>
      </div>
    </div>
  );
}
