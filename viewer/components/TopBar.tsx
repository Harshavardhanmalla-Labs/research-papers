"use client";
import { Layers, ChevronLeft } from "lucide-react";
import type { Paper } from "@/lib/papers";
import ThemeToggle from "./ThemeToggle";

interface Props {
  papers: Paper[];
  activePaper: Paper | null;
  onBack: () => void;
}

export default function TopBar({ papers, activePaper, onBack }: Props) {
  const complete = papers.filter(p => p.status === "complete").length;

  return (
    <header className="flex-shrink-0 h-14 border-b border-border bg-surface-1/95 backdrop-blur-md flex items-center px-6 gap-3 z-10">

      {/* Left group: logo + divider + breadcrumb — takes all remaining space */}
      <div className="flex items-center gap-3 min-w-0 flex-1 overflow-hidden">
        {/* Logo */}
        <div className="brand-icon w-7 h-7 rounded-lg flex items-center justify-center shadow-sm flex-shrink-0">
          <Layers size={14} className="text-white" />
        </div>
        <span className="text-[13px] font-bold text-fg tracking-tight leading-none flex-shrink-0">
          Research Portal
        </span>
        <div className="w-px h-5 bg-border flex-shrink-0" />

        {/* Breadcrumb or subtitle */}
        {activePaper ? (
          <div className="flex items-center gap-1.5 min-w-0 overflow-hidden">
            <button
              onClick={onBack}
              className="flex items-center gap-1 text-[12px] text-fg-3 hover:text-fg transition-colors flex-shrink-0"
            >
              <ChevronLeft size={13} />
              All papers
            </button>
            <span className="text-fg-5 text-[12px] flex-shrink-0">/</span>
            <span className="text-[12px] font-semibold text-fg truncate">{activePaper.shortTitle}</span>
          </div>
        ) : (
          <span className="text-[12px] text-fg-4 truncate">
            {papers.length} papers · {complete} complete · EB-1A
          </span>
        )}
      </div>

      {/* Right group: status + toggle */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="hidden sm:flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/60" />
          <span className="text-[10px] text-fg-4">Local</span>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
