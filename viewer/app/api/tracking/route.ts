import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { PAPERS_ROOT } from "@/lib/papers";

// Persisted submission-tracking store (separate from build-time papers.ts).
// Edited from the board cards; written to a JSON file under PAPERS_ROOT.
export const dynamic = "force-dynamic";

const FILE = path.join(PAPERS_ROOT, ".paper-tracking.json");

type Entry = { submittedTo?: string; stage?: string; dataRepo?: string; repoName?: string; updatedAt?: string };
type Store = Record<string, Entry>;

async function read(): Promise<Store> {
  try {
    return JSON.parse(await fs.readFile(FILE, "utf8")) as Store;
  } catch {
    return {};
  }
}

export async function GET() {
  return NextResponse.json(await read());
}

export async function POST(req: Request) {
  let body: any;
  try { body = await req.json(); } catch { return NextResponse.json({ error: "bad json" }, { status: 400 }); }

  const id = typeof body?.id === "string" ? body.id.replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 40) : "";
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });

  const data = await read();
  const entry: Entry = { ...(data[id] || {}) };
  if (typeof body.submittedTo === "string") entry.submittedTo = body.submittedTo.slice(0, 200);
  if (typeof body.stage === "string")       entry.stage       = body.stage.slice(0, 60);
  if (typeof body.dataRepo === "string")    entry.dataRepo    = body.dataRepo.slice(0, 300);
  if (typeof body.repoName === "string")    entry.repoName    = body.repoName.slice(0, 80);
  entry.updatedAt = new Date().toISOString();
  data[id] = entry;

  try {
    await fs.writeFile(FILE, JSON.stringify(data, null, 2), "utf8");
  } catch (e: any) {
    return NextResponse.json({ error: "write failed", detail: String(e?.message ?? e) }, { status: 500 });
  }
  return NextResponse.json({ ok: true, id, entry });
}
