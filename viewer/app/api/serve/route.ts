import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { PAPERS_ROOT } from "@/lib/papers";

const MIME: Record<string, string> = {
  ".pdf":  "application/pdf",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg":  "image/svg+xml",
  ".gif":  "image/gif",
  ".webp": "image/webp",
  ".csv":  "text/csv",
  ".json": "application/json",
  ".md":   "text/markdown",
  ".txt":  "text/plain",
};

// Serves binary/media files (PDFs, images) — for use in <iframe> and <img>
export async function GET(req: NextRequest) {
  const filePath = req.nextUrl.searchParams.get("path");
  if (!filePath) {
    return NextResponse.json({ error: "Missing path" }, { status: 400 });
  }

  const resolved = path.resolve(filePath);
  if (!resolved.startsWith(path.resolve(PAPERS_ROOT))) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  try {
    const buf = fs.readFileSync(resolved);
    const ext = path.extname(resolved).toLowerCase();
    const mime = MIME[ext] ?? "application/octet-stream";
    return new NextResponse(buf, {
      headers: {
        "Content-Type": mime,
        "Content-Disposition": "inline",
        "Cache-Control": "private, max-age=3600",
      },
    });
  } catch {
    return NextResponse.json({ error: "File not found" }, { status: 404 });
  }
}
