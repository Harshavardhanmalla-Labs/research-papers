import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { PAPERS_ROOT } from "@/lib/papers";

// Returns plain text content of a file (markdown, JSON, CSV, etc.)
export async function GET(req: NextRequest) {
  const filePath = req.nextUrl.searchParams.get("path");
  if (!filePath) {
    return NextResponse.json({ error: "Missing path" }, { status: 400 });
  }

  // Security: must stay within PAPERS_ROOT
  const resolved = path.resolve(filePath);
  if (!resolved.startsWith(path.resolve(PAPERS_ROOT))) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  try {
    const content = fs.readFileSync(resolved, "utf-8");
    return new NextResponse(content, {
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  } catch {
    return NextResponse.json({ error: "File not found" }, { status: 404 });
  }
}
