"use client";
import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import PaperViewer from "@/components/PaperViewer";
import { PAPERS } from "@/lib/papers";

export default function Home() {
  const [activeId, setActiveId] = useState(PAPERS[2].id); // default; overridden by localStorage effect
  const paper = PAPERS.find((p) => p.id === activeId) ?? PAPERS[0];

  /* Restore last-viewed paper from localStorage on mount */
  useEffect(() => {
    try {
      const saved = localStorage.getItem('rp-paper');
      if (saved && PAPERS.some((p) => p.id === saved)) setActiveId(saved);
    } catch (_) {}
  }, []);

  /* Sync active paper → HTML data-paper attribute so CSS vars cascade */
  useEffect(() => {
    document.documentElement.dataset.paper = activeId;
    try { localStorage.setItem('rp-paper', activeId); } catch (_) {}
  }, [activeId]);

  return (
    <div className="flex h-screen overflow-hidden bg-surface-0">
      <Sidebar papers={PAPERS} activeId={activeId} onSelect={setActiveId} />
      <main className="flex-1 min-w-0 overflow-hidden flex flex-col bg-surface-0">
        <PaperViewer key={paper.id} paper={paper} />
      </main>
    </div>
  );
}
