"use client";
import { BookMarked, FlaskConical, Shield, Layers, Flame, Clock } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { STATUS_COLORS } from "@/lib/papers";
import clsx from "clsx";
import ThemeToggle from "./ThemeToggle";

/* Per-paper gradient icon + accent colour */
const PAPER_META = [
  {
    Icon: BookMarked,
    iconCls: "paper-icon-p1",            // sky → blue gradient
    dotCls: "bg-sky-500",
    borderCls: "border-l-sky-500",
    activeBg: "bg-sky-500/10 dark:bg-sky-500/8",
    activeRing: "border-sky-500/35",
    activeShadow: "shadow-[inset_2px_0_0_0_#0ea5e9,0_0_20px_rgba(14,165,233,0.10)]",
  },
  {
    Icon: FlaskConical,
    iconCls: "paper-icon-p2",            // teal → cyan gradient
    dotCls: "bg-teal-500",
    borderCls: "border-l-teal-500",
    activeBg: "bg-teal-500/10 dark:bg-teal-500/8",
    activeRing: "border-teal-500/35",
    activeShadow: "shadow-[inset_2px_0_0_0_#14b8a6,0_0_20px_rgba(20,184,166,0.10)]",
  },
  {
    Icon: Shield,
    iconCls: "paper-icon-p3",            // violet → purple gradient
    dotCls: "bg-violet-500",
    borderCls: "border-l-violet-500",
    activeBg: "bg-violet-500/10 dark:bg-violet-500/8",
    activeRing: "border-violet-500/35",
    activeShadow: "shadow-[inset_2px_0_0_0_#a78bfa,0_0_20px_rgba(167,139,250,0.10)]",
  },
  {
    Icon: Flame,
    iconCls: "paper-icon-p4",            // rose → coral gradient
    dotCls: "bg-rose-500",
    borderCls: "border-l-rose-500",
    activeBg: "bg-rose-500/10 dark:bg-rose-500/8",
    activeRing: "border-rose-500/35",
    activeShadow: "shadow-[inset_2px_0_0_0_#f43f5e,0_0_20px_rgba(244,63,94,0.10)]",
  },
  {
    Icon: Clock,
    iconCls: "paper-icon-p5",            // amber → orange gradient
    dotCls: "bg-amber-500",
    borderCls: "border-l-amber-500",
    activeBg: "bg-amber-500/10 dark:bg-amber-500/8",
    activeRing: "border-amber-500/35",
    activeShadow: "shadow-[inset_2px_0_0_0_#f59e0b,0_0_20px_rgba(245,158,11,0.10)]",
  },
];

const STATUS_DOT: Record<string, string> = {
  complete:      "bg-emerald-500",
  packaging:     "bg-violet-500 pulse-dot",
  drafting:      "bg-amber-500",
  "in-progress": "bg-sky-500 pulse-dot",
};

interface Props {
  papers: Paper[];
  activeId: string;
  onSelect: (id: string) => void;
}

export default function Sidebar({ papers, activeId, onSelect }: Props) {
  return (
    <aside className="w-[272px] flex-shrink-0 bg-surface-1 border-r border-border flex flex-col h-full overflow-hidden">

      {/* ── Brand ── */}
      <div className="sidebar-brand px-5 py-5 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-3">
          {/* Gradient icon */}
          <div className="brand-icon w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg transition-all duration-500">
            <Layers size={17} className="text-white drop-shadow-sm" />
          </div>
          <div>
            <span className="text-[13px] font-bold text-fg tracking-tight leading-none">
              Research Portal
            </span>
            <p className="text-[10px] text-fg-4 mt-1 leading-none">{papers.length} papers · EB-1A portfolio</p>
          </div>
        </div>
      </div>

      {/* ── Paper list ── */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-2 min-h-0">
        <div className="flex items-center justify-between px-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-fg-4">Papers</p>
          <span className="text-[9px] font-bold bg-surface-3 border border-border px-2 py-0.5 rounded-full text-fg-3">
            {papers.length}
          </span>
        </div>

        {papers.map((p, i) => {
          const meta   = PAPER_META[i] ?? PAPER_META[2];
          const { Icon } = meta;
          const active = p.id === activeId;
          return (
            <button
              key={p.id}
              onClick={() => onSelect(p.id)}
              className={clsx(
                "w-full text-left rounded-xl px-3 py-3.5 transition-all duration-200 group relative border",
                active
                  ? [meta.activeBg, meta.activeRing, meta.activeShadow]
                  : "border-transparent hover:bg-surface-3 hover:border-border hover:shadow-sm"
              )}
            >
              <div className="flex items-start gap-3">
                {/* Gradient icon badge */}
                <div className="flex flex-col items-center gap-1.5 flex-shrink-0 pt-0.5">
                  <div className={clsx(
                    "w-[32px] h-[32px] rounded-xl flex items-center justify-center shadow-md transition-all duration-200",
                    meta.iconCls,
                    active ? "opacity-100 shadow-lg" : "opacity-35 group-hover:opacity-65"
                  )}>
                    <Icon
                      size={15}
                      className="text-white drop-shadow-sm"
                    />
                  </div>
                  <span className={clsx(
                    "text-[8px] font-black tracking-widest uppercase",
                    active ? "text-fg-3" : "text-fg-5"
                  )}>
                    P{i + 1}
                  </span>
                </div>

                {/* Text content */}
                <div className="min-w-0 flex-1">
                  <p className={clsx(
                    "text-[12px] font-semibold leading-tight",
                    active ? "text-fg" : "text-fg-2 group-hover:text-fg"
                  )}>
                    {p.shortTitle}
                  </p>
                  <p className="text-[10px] text-fg-4 leading-snug mt-0.5 line-clamp-2">
                    {p.subtitle}
                  </p>

                  {/* Status badge with dot */}
                  <div className="mt-2.5 flex items-center gap-1.5">
                    <span className={clsx(
                      "w-1.5 h-1.5 rounded-full flex-shrink-0",
                      STATUS_DOT[p.status] ?? "bg-fg-4"
                    )} />
                    <span className={clsx(
                      "inline-block px-2 py-0.5 rounded-full text-[9px] font-bold border uppercase tracking-wider",
                      STATUS_COLORS[p.status]
                    )}>
                      {p.statusLabel}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </nav>

      {/* ── Footer ── */}
      <div className="px-4 py-3 border-t border-border flex-shrink-0 flex items-center justify-between gap-2 bg-surface-1/90 backdrop-blur-sm">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/60 flex-shrink-0" />
          <p className="text-[10px] text-fg-4 truncate">Read-only · Local</p>
        </div>
        <ThemeToggle />
      </div>
    </aside>
  );
}
