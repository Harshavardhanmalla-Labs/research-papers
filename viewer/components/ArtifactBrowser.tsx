"use client";
import { useEffect, useState } from "react";
import {
  Folder, FolderOpen, FileText, FileCode, FileType, Image as ImageIcon,
  ChevronRight, ChevronDown, Loader2, Eye, X, ExternalLink,
  Database, FileJson, FileSpreadsheet, ScrollText, Archive
} from "lucide-react";
import type { Paper } from "@/lib/papers";
import type { TreeNode } from "@/app/api/tree/route";
import { PAPERS_ROOT } from "@/lib/papers";

interface Props { paper: Paper }

const IMG_EXTS  = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]);
const TEXT_EXTS = new Set([".md", ".txt", ".json", ".csv", ".py", ".ts", ".tsx", ".js", ".tex", ".bib", ".yml", ".yaml", ".toml"]);

function formatSize(size: number | undefined | null): string {
  if (size == null) return "";
  if (size > 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`;
  if (size > 1024)         return `${(size / 1024).toFixed(0)} KB`;
  return `${size} B`;
}

function fileIcon(ext: string) {
  if (IMG_EXTS.has(ext))                        return <ImageIcon       size={13} className="text-sky-500  flex-shrink-0" />;
  if (ext === ".pdf")                            return <FileType        size={13} className="text-red-400  flex-shrink-0" />;
  if (ext === ".csv")                            return <FileSpreadsheet size={13} className="text-emerald-500 flex-shrink-0" />;
  if (ext === ".json")                           return <FileJson        size={13} className="text-amber-500 flex-shrink-0" />;
  if ([".py",".ts",".tsx",".js"].includes(ext))  return <FileCode        size={13} className="text-accent    flex-shrink-0" />;
  if ([".md",".txt",".tex"].includes(ext))       return <ScrollText      size={13} className="text-fg-2     flex-shrink-0" />;
  if ([".bib",".yml",".yaml",".toml"].includes(ext)) return <Database   size={13} className="text-teal-500 flex-shrink-0" />;
  if ([".zip",".tar",".gz"].includes(ext))       return <Archive         size={13} className="text-orange-400 flex-shrink-0" />;
  return <FileText size={13} className="text-fg-4 flex-shrink-0" />;
}

function FileNode({ node, onOpen }: { node: TreeNode; onOpen: (n: TreeNode) => void }) {
  const [open, setOpen] = useState(false);

  if (node.type === "dir") {
    const childCount = node.children?.length ?? 0;
    return (
      <div>
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1.5 w-full text-left px-2 py-1 rounded-lg hover:bg-surface-4 text-fg-2 group transition-colors"
        >
          <span className="flex-shrink-0 text-fg-5">
            {open ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
          </span>
          {open
            ? <FolderOpen size={13} className="text-amber-500 flex-shrink-0" />
            : <Folder     size={13} className="text-amber-500 flex-shrink-0" />
          }
          <span className="text-[11px] truncate flex-1 font-medium">{node.name}</span>
          <span className="ml-auto text-[10px] text-fg-5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
            {childCount}
          </span>
        </button>
        {open && node.children && (
          <div className="ml-3.5 border-l border-border/40 pl-2 mt-0.5 space-y-0.5">
            {node.children.map((child) => (
              <FileNode key={child.path} node={child} onOpen={onOpen} />
            ))}
          </div>
        )}
      </div>
    );
  }

  const canPreview = TEXT_EXTS.has(node.ext ?? "") || IMG_EXTS.has(node.ext ?? "") || node.ext === ".pdf";
  const sizeStr = formatSize(node.size);

  return (
    <div
      className={`flex items-center gap-1.5 px-2 py-0.5 rounded-lg group transition-colors ${
        canPreview ? "hover:bg-surface-3 cursor-pointer" : "hover:bg-surface-4"
      }`}
      onClick={canPreview ? () => onOpen(node) : undefined}
      title={canPreview ? `Preview ${node.name}` : node.name}
    >
      {fileIcon(node.ext ?? "")}
      <span className="text-[11px] text-fg-3 truncate flex-1 group-hover:text-fg-2 transition-colors">
        {node.name}
      </span>
      {sizeStr && <span className="text-[9px] text-fg-5 ml-1 flex-shrink-0 font-mono">{sizeStr}</span>}
      {canPreview && <Eye size={11} className="text-fg-5 group-hover:text-accent transition-colors flex-shrink-0 ml-1" />}
    </div>
  );
}

export default function ArtifactBrowser({ paper }: Props) {
  const [trees, setTrees]                   = useState<{ label: string; nodes: TreeNode[] }[]>([]);
  const [loading, setLoading]               = useState(true);
  const [preview, setPreview]               = useState<TreeNode | null>(null);
  const [previewContent, setPreviewContent] = useState<string>("");
  const [previewLoading, setPreviewLoading] = useState(false);

  const root = `${PAPERS_ROOT}/${paper.root}`;

  useEffect(() => {
    setLoading(true);
    Promise.all(
      paper.artifacts.map((rel) => {
        const absPath = `${root}/${rel}`;
        return fetch(`/api/tree?path=${encodeURIComponent(absPath)}`)
          .then((r) => r.json())
          .then((nodes) => ({ label: rel, nodes: nodes as TreeNode[] }))
          .catch(() => ({ label: rel, nodes: [] as TreeNode[] }));
      })
    ).then((results) => { setTrees(results); setLoading(false); });
  }, [root, paper.artifacts]);

  const openPreview = (node: TreeNode) => {
    setPreview(node); setPreviewContent(""); setPreviewLoading(true);
    const ext = node.ext ?? "";
    if (IMG_EXTS.has(ext) || ext === ".pdf") { setPreviewLoading(false); return; }
    fetch(`/api/file?path=${encodeURIComponent(node.path)}`)
      .then((r) => r.text())
      .then((t) => { setPreviewContent(t); setPreviewLoading(false); })
      .catch(() => { setPreviewContent("Could not load file."); setPreviewLoading(false); });
  };

  const serveUrl    = (node: TreeNode) => `/api/serve?path=${encodeURIComponent(node.path)}`;
  const pdfViewUrl  = (node: TreeNode) => `${serveUrl(node)}#toolbar=1&navpanes=1&scrollbar=1`;

  return (
    <div className="flex h-full min-h-0 overflow-hidden">
      {/* Tree pane */}
      <div className="w-72 flex-shrink-0 border-r border-border overflow-y-auto bg-surface-1/50">
        {loading && (
          <div className="flex items-center gap-2 text-fg-4 mt-8 justify-center">
            <Loader2 size={14} className="animate-spin text-accent/50" />
            <span className="text-xs">Loading tree…</span>
          </div>
        )}
        <div className="p-3 space-y-5">
          {trees.map((tree) => (
            <div key={tree.label}>
              <div className="text-[10px] font-bold text-fg-4 uppercase tracking-widest px-2 mb-2 flex items-center gap-2">
                <Folder size={10} className="text-amber-600" />
                {tree.label}
              </div>
              {tree.nodes.length === 0 ? (
                <p className="text-[10px] text-fg-5 px-2 italic">Empty or not found</p>
              ) : (
                <div className="space-y-0.5">
                  {tree.nodes.map((n) => (
                    <FileNode key={n.path} node={n} onOpen={openPreview} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Preview pane */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-0">
        {!preview && (
          <div className="flex flex-col items-center justify-center h-full text-fg-4 gap-3">
            <div className="w-14 h-14 rounded-full bg-surface-3 border border-border flex items-center justify-center">
              <Eye size={22} className="opacity-40" />
            </div>
            <span className="text-sm">Click any file to preview</span>
            <span className="text-[11px] text-fg-5">Supports text, images, and PDFs</span>
          </div>
        )}
        {preview && (
          <>
            <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border flex-shrink-0 bg-surface-2/40">
              {fileIcon(preview.ext ?? "")}
              <span className="text-xs text-fg-2 flex-1 truncate font-medium">{preview.name}</span>
              {preview.size != null && (
                <span className="text-[10px] text-fg-4 bg-surface-3 px-2 py-0.5 rounded border border-border font-mono flex-shrink-0">
                  {formatSize(preview.size)}
                </span>
              )}
              {preview.ext === ".pdf" && (
                <a
                  href={serveUrl(preview)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-[10px] text-accent hover:text-accent/80 transition-colors flex-shrink-0 border border-accent/30 bg-accent/10 px-2 py-0.5 rounded"
                >
                  <ExternalLink size={10} /> New tab
                </a>
              )}
              <button
                onClick={() => setPreview(null)}
                className="text-fg-5 hover:text-fg-2 transition-colors flex-shrink-0 ml-1"
              >
                <X size={14} />
              </button>
            </div>

            <div className="flex-1 overflow-auto min-h-0 flex flex-col">
              {previewLoading && (
                <div className="flex items-center gap-2 justify-center mt-12 text-fg-4">
                  <Loader2 size={16} className="animate-spin text-accent/50" />
                  <span className="text-xs">Loading…</span>
                </div>
              )}

              {!previewLoading && IMG_EXTS.has(preview.ext ?? "") && (
                <div className="flex items-center justify-center p-6 flex-1">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={serveUrl(preview)}
                    alt={preview.name}
                    className="max-w-full object-contain rounded-lg border border-border shadow-lg"
                    style={{ maxHeight: "calc(100vh - 14rem)" }}
                  />
                </div>
              )}

              {!previewLoading && preview.ext === ".pdf" && (
                <iframe
                  src={pdfViewUrl(preview)}
                  className="flex-1 w-full border-0"
                  style={{ minHeight: 0 }}
                  title={preview.name}
                />
              )}

              {!previewLoading && preview.ext !== ".pdf" && !IMG_EXTS.has(preview.ext ?? "") && (
                <pre className="flex-1 p-5 text-[11px] text-fg-2 font-mono leading-[1.75] whitespace-pre-wrap break-words overflow-auto bg-surface-0 selection:bg-accent/20">
                  {previewContent}
                </pre>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
