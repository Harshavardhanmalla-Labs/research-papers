"use client";
import { useEffect, useState, useMemo } from "react";
import Papa from "papaparse";
import { Loader2, AlertCircle, Search, ArrowUpDown, ArrowUp, ArrowDown, BarChart2, Rows, Columns } from "lucide-react";
import type { Paper } from "@/lib/papers";
import { PAPERS_ROOT } from "@/lib/papers";

interface Props { paper: Paper }
type SortDir = "asc" | "desc" | null;

/** Format a raw CSV cell value for display */
function fmtCell(raw: string): { display: string; isNum: boolean; isBool: boolean; boolVal?: boolean } {
  const v = raw.trim();
  const isTrue  = v === "True"  || v === "true"  || v === "1";
  const isFalse = v === "False" || v === "false" || v === "0";
  if (isTrue)  return { display: v, isNum: false, isBool: true, boolVal: true  };
  if (isFalse) return { display: v, isNum: false, isBool: true, boolVal: false };

  const n = parseFloat(v);
  if (!isNaN(n) && v !== "") {
    // Round long decimals to 5 significant figures for display
    let display = v;
    if (v.includes(".") && (v.split(".")[1]?.length ?? 0) > 6) {
      display = parseFloat(n.toPrecision(5)).toString();
    }
    return { display, isNum: true, isBool: false };
  }
  return { display: v, isNum: false, isBool: false };
}

export default function ResultsExplorer({ paper }: Props) {
  const [activeCSV, setActiveCSV] = useState(0);
  const [rows, setRows]           = useState<Record<string, string>[]>([]);
  const [headers, setHeaders]     = useState<string[]>([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [search, setSearch]       = useState("");
  const [sortCol, setSortCol]     = useState<string | null>(null);
  const [sortDir, setSortDir]     = useState<SortDir>(null);

  const csvOptions = [
    ...(paper.results.primaryCSV
      ? [{ label: "Primary results", path: paper.results.primaryCSV }]
      : []),
    ...(paper.results.secondaryCSVs ?? []),
  ];

  const currentCSVPath = csvOptions[activeCSV]?.path;
  const absolutePath   = currentCSVPath
    ? (currentCSVPath.startsWith("/") ? currentCSVPath : `${PAPERS_ROOT}/${paper.root}/${currentCSVPath}`)
    : null;

  useEffect(() => {
    if (!absolutePath) return;
    setLoading(true);
    setError(null);
    setSearch("");
    setSortCol(null);
    setSortDir(null);

    fetch(`/api/file?path=${encodeURIComponent(absolutePath)}`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.text(); })
      .then((text) => {
        const result = Papa.parse<Record<string, string>>(text, {
          header: true, skipEmptyLines: true, dynamicTyping: false,
        });
        setHeaders(result.meta.fields ?? []);
        setRows(result.data);
        setLoading(false);
      })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [absolutePath]);

  const filtered = useMemo(() => {
    let r = rows;
    if (search.trim()) {
      const q = search.toLowerCase();
      r = r.filter((row) => Object.values(row).some((v) => v?.toLowerCase().includes(q)));
    }
    if (sortCol && sortDir) {
      r = [...r].sort((a, b) => {
        const av = a[sortCol] ?? "", bv = b[sortCol] ?? "";
        const an = parseFloat(av), bn = parseFloat(bv);
        const cmp = !isNaN(an) && !isNaN(bn) ? an - bn : av.localeCompare(bv);
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return r;
  }, [rows, search, sortCol, sortDir]);

  const toggleSort = (col: string) => {
    if (sortCol !== col)       { setSortCol(col); setSortDir("asc"); }
    else if (sortDir === "asc") setSortDir("desc");
    else                        { setSortCol(null); setSortDir(null); }
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sortCol !== col) return <ArrowUpDown size={10} className="text-fg-5 ml-1 flex-shrink-0 opacity-0 group-hover/th:opacity-100 transition-opacity" />;
    if (sortDir === "asc")  return <ArrowUp   size={10} className="text-accent ml-1 flex-shrink-0" />;
    return <ArrowDown size={10} className="text-accent ml-1 flex-shrink-0" />;
  };

  if (csvOptions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-fg-4 gap-3">
        <div className="w-14 h-14 rounded-full bg-surface-3 border border-border flex items-center justify-center">
          <BarChart2 size={24} className="opacity-40" />
        </div>
        <span className="text-sm">No results CSV configured</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0">

      {/* ── Toolbar ── */}
      <div className="flex items-center gap-3 px-5 py-3 border-b border-border flex-shrink-0 bg-surface-2/40 flex-wrap gap-y-2">
        {/* CSV selector pills */}
        <div className="flex gap-1.5 flex-wrap">
          {csvOptions.map((opt, i) => (
            <button
              key={i}
              onClick={() => setActiveCSV(i)}
              className={`px-3 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
                activeCSV === i
                  ? "bg-accent/15 text-accent border-accent/40 shadow-sm"
                  : "text-fg-3 border-transparent hover:border-border hover:text-fg-2 hover:bg-surface-4"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Stats + search */}
        <div className="ml-auto flex items-center gap-3">
          {!loading && headers.length > 0 && (
            <>
              <span className="flex items-center gap-1.5 text-[10px] text-fg-3 bg-surface-3 border border-border px-2.5 py-1 rounded-full">
                <Rows size={10} className="text-fg-4" />
                {filtered.length.toLocaleString()}
                {filtered.length !== rows.length && <span className="text-fg-5">/{rows.length}</span>}
                <span className="text-fg-5 ml-0.5">rows</span>
              </span>
              <span className="flex items-center gap-1.5 text-[10px] text-fg-3 bg-surface-3 border border-border px-2.5 py-1 rounded-full">
                <Columns size={10} className="text-fg-4" />
                {headers.length}
                <span className="text-fg-5 ml-0.5">cols</span>
              </span>
            </>
          )}
          <div className="relative">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-4 pointer-events-none" />
            <input
              type="text"
              placeholder="Search…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="search-input pl-8 pr-3 py-1.5 bg-surface-3 border border-border rounded-lg text-[11px] text-fg-2 placeholder-fg-5 focus:outline-none w-44 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* ── Table ── */}
      <div className="flex-1 overflow-auto min-h-0">
        {loading && (
          <div className="flex flex-col items-center gap-3 mt-20 text-fg-4">
            <Loader2 size={24} className="animate-spin text-accent/50" />
            <span className="text-sm">Parsing CSV…</span>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center gap-3 mt-20">
            <div className="w-12 h-12 rounded-full bg-red-900/20 border border-red-800/40 flex items-center justify-center">
              <AlertCircle size={20} className="text-red-400" />
            </div>
            <span className="text-sm text-fg-3">Error loading CSV: {error}</span>
          </div>
        )}

        {!loading && !error && headers.length > 0 && (
          <table className="results-table w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr>
                {headers.map((h) => (
                  <th
                    key={h}
                    onClick={() => toggleSort(h)}
                    className="group/th px-3 py-2.5 text-left font-semibold text-fg-2 cursor-pointer select-none whitespace-nowrap hover:text-fg transition-colors"
                  >
                    <span className="flex items-center gap-0.5">
                      {h}
                      <SortIcon col={h} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, ri) => (
                <tr key={ri} className="transition-colors">
                  {headers.map((h) => {
                    const raw  = row[h] ?? "";
                    const cell = fmtCell(raw);
                    return (
                      <td key={h} className="px-3 py-1.5 border-b border-border/30 whitespace-nowrap">
                        {cell.isBool ? (
                          <span className={`inline-flex items-center gap-1 font-medium ${cell.boolVal ? "text-red-500 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cell.boolVal ? "bg-red-500" : "bg-emerald-500"}`} />
                            {cell.display}
                          </span>
                        ) : cell.isNum ? (
                          <span className="num-val font-mono" title={raw}>{cell.display}</span>
                        ) : (
                          <span className="text-fg-2 max-w-[200px] truncate block" title={raw}>{cell.display}</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && !error && headers.length === 0 && (
          <div className="flex flex-col items-center gap-3 mt-20 text-fg-4">
            <BarChart2 size={28} className="opacity-40" />
            <span className="text-sm">No data to display</span>
          </div>
        )}
      </div>
    </div>
  );
}
