"use client";
import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import PaperGrid from "@/components/PaperGrid";
import PaperViewer from "@/components/PaperViewer";
import { PAPERS } from "@/lib/papers";

export default function Home() {
  const [activeId, setActiveId] = useState<string | null>(null); // null = grid/home view

  const paper = activeId ? (PAPERS.find((p) => p.id === activeId) ?? null) : null;

  /* Sync active paper → HTML data-paper attribute so per-paper accent CSS vars cascade */
  useEffect(() => {
    document.documentElement.dataset.paper = activeId ?? "";
    try {
      if (activeId) localStorage.setItem("rp-paper", activeId);
    } catch (_) {}
  }, [activeId]);

  const handleSelect = (id: string) => setActiveId(id);
  const handleBack   = () => setActiveId(null);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-surface-0">
      <TopBar papers={PAPERS} activePaper={paper} onBack={handleBack} />
      <main className="flex-1 min-h-0 overflow-hidden">
        {paper ? (
          <PaperViewer key={paper.id} paper={paper} papers={PAPERS} onSelect={handleSelect} />
        ) : (
          <PaperGrid papers={PAPERS} onSelect={handleSelect} />
        )}
      </main>
    </div>
  );
}
