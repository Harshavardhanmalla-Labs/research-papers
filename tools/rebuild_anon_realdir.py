#!/usr/bin/env python3
"""Rebuild every paper's anonymous.pdf by compiling in its REAL submission dir.

The temp-dir path in build_anon_pdfs.py is flaky for some papers (tectonic
"halted on potentially-recoverable error"); compiling in the real dir is
reliable. We anonymize main.tex via anonymize_tex, and for any \\input section
or .bib/.bbl file that carries an author identifier we redact it IN PLACE,
compile, then RESTORE the original. Verifies no name leak and no dead link.
"""
import os, re, sys, glob, subprocess, importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__)).replace("/tools", "")
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "tools/build_anon_pdfs.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
TECTONIC = b.TECTONIC

ID_RE = re.compile(r"harshavardhan|malla|@gmail|github\.com/Harshavardhanmalla", re.I)
DEAD = "anonymous.4open.science"

def papers():
    src = open(os.path.join(ROOT, "viewer/lib/papers.ts")).read()
    for blk in src.split('id: "')[1:]:
        pid = re.match(r'([^"]+)', blk).group(1)
        root = (re.search(r'root:\s*"([^"]+)"', blk) or [None, None])[1]
        pdf = (re.search(r'submissionPdf:\s*"([^"]+)"', blk) or [None, None])[1]
        if pdf:
            yield pid, os.path.join(ROOT, root, os.path.dirname(pdf))

def build(pid, d):
    main = os.path.join(d, "main.tex")
    if not os.path.isfile(main):
        return pid, "no main.tex"
    # aux source files that leak identifiers -> redact in place, remember to restore
    backups = {}
    for f in glob.glob(os.path.join(d, "**", "*.tex"), recursive=True) + \
             glob.glob(os.path.join(d, "**", "*.bib"), recursive=True) + \
             glob.glob(os.path.join(d, "**", "*.bbl"), recursive=True):
        if os.path.abspath(f) == os.path.abspath(main):
            continue
        body = open(f, encoding="utf-8", errors="ignore").read()
        if ID_RE.search(body) or DEAD in body:
            backups[f] = body
            open(f, "w", encoding="utf-8").write(b.redact_text(b.strip_acks(body)))
    anon = os.path.join(d, "_anon.tex")
    try:
        open(anon, "w", encoding="utf-8").write(b.anonymize_tex(open(main, encoding="utf-8").read()))
        p = subprocess.run([TECTONIC, "_anon.tex"], cwd=d, capture_output=True, text=True, timeout=300)
        outpdf = os.path.join(d, "_anon.pdf")
        if p.returncode != 0 or not os.path.isfile(outpdf):
            err = (p.stderr or p.stdout).strip().splitlines()[-1:] or ["?"]
            return pid, "FAIL " + err[0][:80]
        import shutil
        shutil.copy2(outpdf, os.path.join(d, "anonymous.pdf"))
        txt = subprocess.run(["pdftotext", os.path.join(d, "anonymous.pdf"), "-"],
                             capture_output=True, text=True).stdout
        leak = bool(re.search(r"harshavardhan|malla|@gmail", txt, re.I))
        dead = DEAD in txt
        return pid, ("LEAK" if leak else "DEADLINK" if dead else "ok")
    finally:
        for f in (anon, os.path.join(d, "_anon.pdf"), os.path.join(d, "_anon.log"),
                  os.path.join(d, "_anon.aux"), os.path.join(d, "_anon.out")):
            try: os.remove(f)
            except OSError: pass
        for f, body in backups.items():
            open(f, "w", encoding="utf-8").write(body)  # restore original

def main():
    only = set(sys.argv[1:])
    results = []
    for pid, d in papers():
        if only and pid not in only:
            continue
        r = build(pid, d)
        results.append(r)
        print(f"{r[0]:9} {r[1]}", flush=True)
    bad = [r[0] for r in results if r[1] not in ("ok",)]
    print(f"\n{sum(1 for r in results if r[1]=='ok')}/{len(results)} ok; problems={bad}")

if __name__ == "__main__":
    main()
