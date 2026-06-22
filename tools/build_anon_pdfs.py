#!/usr/bin/env python3
"""Compile a double-blind (anonymized) PDF for every paper.

For each paper's submission main.tex we produce an anonymized copy:
  - \\author{...}  -> \\author{Anonymous}
  - \\thanks{...}, \\email{...}, \\affiliation{...}, \\orcid{...} removed
  - acknowledgment sections / acks environments blanked
  - the name-bearing GitHub org URL + any residual name redacted
Then compile it with tectonic into <submission_dir>/anonymous.pdf.

Compiles in a temp copy of the submission dir so figures/.bib/.cls resolve and no
aux files pollute the repo. Prints a per-paper result line.
"""
import os, re, sys, shutil, subprocess, tempfile, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TECTONIC = os.path.expanduser("~/.local/bin/tectonic")


def parse_papers():
    src = open(os.path.join(ROOT, "viewer/lib/papers.ts")).read()
    rows = []
    for blk in src.split('id: "')[1:]:
        pid = re.match(r'([^"]+)', blk).group(1)
        root = (re.search(r'root:\s*"([^"]+)"', blk) or [None, None])[1]
        pdf = (re.search(r'submissionPdf:\s*"([^"]+)"', blk) or [None, None])[1]
        rows.append((pid, root, pdf))
    return rows


def find_brace(s, open_idx):
    """Given index of '{', return index of the matching '}'."""
    depth = 0
    i = open_idx
    while i < len(s):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def replace_command(tex, cmd, replacement=None):
    """Replace every \\cmd[..]{..} (balanced) with `replacement` (or remove). Skips % comments."""
    out, i = [], 0
    token = '\\' + cmd
    while True:
        idx = tex.find(token, i)
        if idx == -1:
            out.append(tex[i:]); break
        # not a longer command name (\\authorrunning etc.)
        after = idx + len(token)
        if after < len(tex) and (tex[after].isalpha()):
            out.append(tex[i:after]); i = after; continue
        line_start = tex.rfind('\n', 0, idx) + 1
        if '%' in tex[line_start:idx]:
            out.append(tex[i:after]); i = after; continue
        j = after
        while j < len(tex) and tex[j] in ' \t\n':
            j += 1
        # skip an optional [..]
        if j < len(tex) and tex[j] == '[':
            close = tex.find(']', j)
            if close != -1:
                j = close + 1
                while j < len(tex) and tex[j] in ' \t\n':
                    j += 1
        if j < len(tex) and tex[j] == '{':
            end = find_brace(tex, j)
            if end != -1:
                out.append(tex[i:idx])
                if replacement is not None:
                    out.append(replacement)
                i = end + 1
                continue
        out.append(tex[i:after]); i = after
    return ''.join(out)


def redact_text(s):
    """Blanket author-identifier redaction — applied to EVERY .tex/.bib source file.
    Handles all separators (space, ~, \\,, comma order) and the org-slug URL."""
    # name-bearing repo URL -> anonymized review link
    s = re.sub(r'https?://github\.com/Harshavardhanmalla-Labs/[^\s}\)>\]`"\']*',
               'https://anonymous.4open.science/r/anonymous', s, flags=re.IGNORECASE)
    s = re.sub(r'Harshavardhanmalla-?Labs', 'anonymous', s, flags=re.IGNORECASE)
    s = re.sub(r'Harshavardhanmalla', 'anonymous', s, flags=re.IGNORECASE)
    # initial form "H.~Malla" / "H. Malla" / "H.\,Malla"  (any LaTeX spacing)
    s = re.sub(r'H\.[~\s\\,]*Malla', 'Anonymous', s, flags=re.IGNORECASE)
    # distinctive given/surname tokens in any order ("Malla, Harshavardhan", bib fields, etc.)
    s = re.sub(r'\bHarshavardhan\b', 'Anonymous', s, flags=re.IGNORECASE)
    s = re.sub(r'\bMalla\b', 'Anonymous', s, flags=re.IGNORECASE)
    # author emails
    s = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', 'anonymous@example.com', s)
    return s


def strip_acks(tex):
    tex = re.sub(
        r'\\section\*?\s*\{\s*Acknowledg[^}]*\}.*?(?=\\section|\\bibliography|\\begin\{thebibliography\})',
        '', tex, flags=re.DOTALL | re.IGNORECASE)
    tex = re.sub(r'\\begin\{acks\}.*?\\end\{acks\}', '', tex, flags=re.DOTALL | re.IGNORECASE)
    return tex


def anonymize_tex(tex):
    # author block -> Anonymous (covers \IEEEauthorblockN/A, \affiliation nested inside)
    tex = replace_command(tex, 'author', r'\author{Anonymous}')
    for cmd in ('thanks', 'email', 'affiliation', 'orcid', 'authornote', 'IEEEauthorblockA'):
        tex = replace_command(tex, cmd, '')
    return redact_text(strip_acks(tex))


def main():
    rows = parse_papers()
    results = []
    for pid, root, pdf in rows:
        if not pdf:
            results.append((pid, "skip", "markdown-only (no submissionPdf)")); continue
        sub_dir = os.path.join(ROOT, root, os.path.dirname(pdf))
        main_tex = os.path.join(sub_dir, "main.tex")
        if not os.path.isfile(main_tex):
            # fall back to the actual pdf basename's .tex
            cand = os.path.join(ROOT, root, pdf[:-4] + ".tex")
            main_tex = cand if os.path.isfile(cand) else main_tex
        if not os.path.isfile(main_tex):
            results.append((pid, "FAIL", "no main.tex")); continue
        tmp = tempfile.mkdtemp()
        try:
            for f in os.listdir(sub_dir):
                s = os.path.join(sub_dir, f)
                if os.path.isfile(s):
                    shutil.copy2(s, tmp)
                elif os.path.isdir(s):
                    shutil.copytree(s, os.path.join(tmp, f), dirs_exist_ok=True)
            # Anonymize EVERY source file in the temp tree: main.tex gets the full
            # structural pass; other .tex/.bib (sections, references.bib, .bbl) get
            # acks-strip + blanket name/URL/email redaction.
            for dirpath, _, fnames in os.walk(tmp):
                for fn in fnames:
                    fp = os.path.join(dirpath, fn)
                    if fn == "main.tex" and os.path.samefile(dirpath, tmp):
                        body = open(fp, encoding="utf-8", errors="ignore").read()
                        open(fp, "w", encoding="utf-8").write(anonymize_tex(body))
                    elif fn.endswith((".tex", ".bib", ".bbl")):
                        body = open(fp, encoding="utf-8", errors="ignore").read()
                        open(fp, "w", encoding="utf-8").write(redact_text(strip_acks(body)))
            p = subprocess.run([TECTONIC, "main.tex"], cwd=tmp, capture_output=True, text=True, timeout=300)
            outpdf = os.path.join(tmp, "main.pdf")
            if os.path.isfile(outpdf):
                dest = os.path.join(sub_dir, "anonymous.pdf")
                shutil.copy2(outpdf, dest)
                # quick leak check on the produced PDF text
                txt = subprocess.run(["pdftotext", dest, "-"], capture_output=True, text=True).stdout
                leak = bool(re.search(r'Harshavardhan|Malla|Harshavardhanmalla', txt, re.IGNORECASE))
                results.append((pid, "LEAK" if leak else "ok", os.path.relpath(dest, ROOT)))
            else:
                err = (p.stderr or p.stdout).strip().splitlines()[-1:] or ["unknown"]
                results.append((pid, "FAIL", err[0][:120]))
        except Exception as e:
            results.append((pid, "FAIL", str(e)[:120]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(f"{pid:9} {results[-1][1]:5} {results[-1][2]}", flush=True)
    ok = sum(1 for _, s, _ in results if s == "ok")
    print(f"\nSUMMARY: {ok} ok / {len(results)} papers; "
          f"fails={[r[0] for r in results if r[1]=='FAIL']}; leaks={[r[0] for r in results if r[1]=='LEAK']}")
    json.dump(results, open(os.path.join(ROOT, "tools/anon_build_report.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
