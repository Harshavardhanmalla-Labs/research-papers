// Author-identity redaction for LaTeX/BibTeX sources, mirroring tools/build_anon_pdfs.py.
// Used by /api/export to produce double-blind .docx / .zip bundles.

function redactText(s: string): string {
  // De-anonymizing repo link -> withheld for double-blind review (no dead/fake URL).
  s = s.replace(/repository\s+at\s+\\url\{https?:\/\/github\.com\/Harshavardhanmalla-Labs\/[^}]*\}/gi,
                "repository (anonymized for double-blind review; the link is provided upon acceptance)");
  s = s.replace(/\\url\{https?:\/\/github\.com\/Harshavardhanmalla-Labs\/[^}]*\}/gi,
                "[repository link withheld for double-blind review]");
  s = s.replace(/https?:\/\/github\.com\/Harshavardhanmalla-Labs\/[^\s}\)>\]`"']*/gi,
                "[repository link withheld for double-blind review]");
  s = s.replace(/Harshavardhanmalla-?Labs/gi, "anonymous");
  s = s.replace(/Harshavardhanmalla/gi, "anonymous");
  s = s.replace(/H\.[~\s\\,]*Malla/gi, "Anonymous");
  s = s.replace(/\bHarshavardhan\b/gi, "Anonymous");
  s = s.replace(/\bMalla\b/gi, "Anonymous");
  s = s.replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, "anonymous@example.com");
  return s;
}

function stripAcks(t: string): string {
  t = t.replace(/\\section\*?\s*\{\s*Acknowledg[^}]*\}[\s\S]*?(?=\\section|\\bibliography|\\begin\{thebibliography\})/gi, "");
  t = t.replace(/\\begin\{acks\}[\s\S]*?\\end\{acks\}/gi, "");
  return t;
}

// Replace every \cmd[..]{..} (balanced braces) with `repl` (or remove). Skips % comments.
function replaceCommand(tex: string, cmd: string, repl: string | null): string {
  const token = "\\" + cmd;
  let out = "", i = 0;
  for (;;) {
    const idx = tex.indexOf(token, i);
    if (idx === -1) { out += tex.slice(i); break; }
    const after = idx + token.length;
    if (/[a-zA-Z]/.test(tex[after] || "")) { out += tex.slice(i, after); i = after; continue; }
    const lineStart = tex.lastIndexOf("\n", idx) + 1;
    if (tex.slice(lineStart, idx).includes("%")) { out += tex.slice(i, after); i = after; continue; }
    let j = after;
    while (j < tex.length && /\s/.test(tex[j])) j++;
    if (tex[j] === "[") { const c = tex.indexOf("]", j); if (c !== -1) { j = c + 1; while (j < tex.length && /\s/.test(tex[j])) j++; } }
    if (tex[j] === "{") {
      let depth = 0, k = j;
      for (; k < tex.length; k++) { if (tex[k] === "{") depth++; else if (tex[k] === "}") { depth--; if (depth === 0) break; } }
      if (k < tex.length) { out += tex.slice(i, idx); if (repl !== null) out += repl; i = k + 1; continue; }
    }
    out += tex.slice(i, after); i = after;
  }
  return out;
}

export function anonymizeMainTex(tex: string): string {
  tex = replaceCommand(tex, "author", "\\author{Anonymous}");
  for (const c of ["thanks", "email", "affiliation", "orcid", "authornote", "IEEEauthorblockA"]) {
    tex = replaceCommand(tex, c, "");
  }
  return redactText(stripAcks(tex));
}

export function anonymizeAux(text: string): string {
  return redactText(stripAcks(text));
}
