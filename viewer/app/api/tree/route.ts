import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { PAPERS_ROOT } from "@/lib/papers";

export interface TreeNode {
  name: string;
  path: string;       // absolute path
  type: "file" | "dir";
  ext?: string;
  size?: number;
  children?: TreeNode[];
}

const SKIP = new Set(["node_modules", ".git", "__pycache__", ".next", ".venv", "venv", ".DS_Store"]);
const MAX_DEPTH = 4;

function buildTree(dirPath: string, depth = 0): TreeNode[] {
  if (depth > MAX_DEPTH) return [];
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dirPath, { withFileTypes: true });
  } catch {
    return [];
  }

  const nodes: TreeNode[] = [];
  for (const e of entries) {
    if (SKIP.has(e.name) || e.name.startsWith(".")) continue;
    const fullPath = path.join(dirPath, e.name);
    if (e.isDirectory()) {
      nodes.push({
        name: e.name,
        path: fullPath,
        type: "dir",
        children: buildTree(fullPath, depth + 1),
      });
    } else {
      let size = 0;
      try { size = fs.statSync(fullPath).size; } catch { /* ignore */ }
      nodes.push({
        name: e.name,
        path: fullPath,
        type: "file",
        ext: path.extname(e.name).toLowerCase(),
        size,
      });
    }
  }
  // dirs first, then files, alphabetical
  return nodes.sort((a, b) => {
    if (a.type !== b.type) return a.type === "dir" ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
}

export async function GET(req: NextRequest) {
  const dirPath = req.nextUrl.searchParams.get("path");
  if (!dirPath) return NextResponse.json({ error: "Missing path" }, { status: 400 });

  const resolved = path.resolve(dirPath);
  if (!resolved.startsWith(path.resolve(PAPERS_ROOT))) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  return NextResponse.json(buildTree(resolved));
}
