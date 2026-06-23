import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import os from "os";
import { execFile } from "child_process";
import { promisify } from "util";
import { PAPERS, PAPERS_ROOT, paperFileName } from "@/lib/papers";

// On-demand peer-review export: a Word .docx with figures/tables placed inline
// (via pandoc), or a .zip of the LaTeX sources + figures/tables for compilation.
export const dynamic = "force-dynamic";
export const maxDuration = 120;

const run = promisify(execFile);
const PANDOC = process.env.PANDOC_BIN || `${os.homedir()}/.local/bin/pandoc`;
const ZIP = "/usr/bin/zip";

function submissionDir(paper: { root: string; submissionPdf?: string }) {
  if (!paper.submissionPdf) return null;
  return path.join(PAPERS_ROOT, paper.root, path.dirname(paper.submissionPdf));
}

export async function GET(req: NextRequest) {
  const id = req.nextUrl.searchParams.get("id") || "";
  const format = req.nextUrl.searchParams.get("format") || "";
  const paper = PAPERS.find((p) => p.id === id);
  if (!paper) return NextResponse.json({ error: "unknown paper" }, { status: 404 });

  const dir = submissionDir(paper);
  if (!dir) return NextResponse.json({ error: "this paper has no LaTeX submission to export" }, { status: 400 });
  try { await fs.access(path.join(dir, "main.tex")); }
  catch { return NextResponse.json({ error: "no main.tex found for this paper" }, { status: 404 }); }

  const base = paperFileName(paper.title);
  const stamp = `${id}-${process.hrtime.bigint()}`;

  try {
    if (format === "docx") {
      const out = path.join(os.tmpdir(), `export-${stamp}.docx`);
      // figures/tables resolve relative to the submission dir; pull a .bib in if present
      const bibs = (await fs.readdir(dir)).filter((f) => f.endsWith(".bib"));
      const args = ["main.tex", "-o", out, "--resource-path", ".:figures:tables:images"];
      if (bibs.length) args.push("--citeproc", ...bibs.flatMap((b) => ["--bibliography", b]));
      await run(PANDOC, args, { cwd: dir, timeout: 110_000, maxBuffer: 1 << 26 });
      const buf = await fs.readFile(out);
      fs.unlink(out).catch(() => {});
      return new NextResponse(new Uint8Array(buf), {
        headers: {
          "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "Content-Disposition": `attachment; filename="${base}.docx"`,
        },
      });
    }

    if (format === "zip") {
      const out = path.join(os.tmpdir(), `export-${stamp}.zip`);
      await run(ZIP, [
        "-r", "-q", out, ".",
        "-x", "*.aux", "*.log", "*.out", "*.blg", "*.synctex.gz", "*.fls",
        "*.fdb_latexmk", "*.toc", "anonymous.pdf",
      ], { cwd: dir, timeout: 60_000, maxBuffer: 1 << 26 });
      const buf = await fs.readFile(out);
      fs.unlink(out).catch(() => {});
      return new NextResponse(new Uint8Array(buf), {
        headers: {
          "Content-Type": "application/zip",
          "Content-Disposition": `attachment; filename="${base}_latex.zip"`,
        },
      });
    }

    return NextResponse.json({ error: "format must be docx or zip" }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json(
      { error: "export failed", detail: String(e?.stderr || e?.message || e).slice(0, 500) },
      { status: 500 },
    );
  }
}
