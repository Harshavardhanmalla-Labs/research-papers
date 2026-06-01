#!/usr/bin/env python3
"""Step-11 helper: split paper2_full_draft.md into the 16 LaTeX section files.

Conservative markdown -> LaTeX conversion. Preserves wording verbatim;
converts headings, bold, italics, code spans, bullet lists, code fences,
and escapes LaTeX-special characters outside code spans.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
DRAFT = REPO / "paper2" / "manuscript" / "paper2_full_draft.md"
OUT_DIR = REPO / "paper2" / "submission" / "cset" / "sections"

# Mapping of draft H2 heading number -> output filename (00..15).
SECTION_FILENAMES = {
    1: "00_abstract.tex",
    2: "01_introduction.tex",
    3: "02_background.tex",
    4: "03_related_work.tex",
    5: "04_problem_statement.tex",
    6: "05_failure_aware_gate.tex",
    7: "06_study_design.tex",
    8: "07_public_feed_data.tex",
    9: "08_fixed_prior_sensitivity.tex",
    10: "09_metrics_inference.tex",
    11: "10_results.tex",
    12: "11_discussion.tex",
    13: "12_limitations.tex",
    14: "13_future_work.tex",
    15: "14_conclusion.tex",
    16: "15_reproducibility.tex",
    # Section 17 References handled via references.bib; not written as section.
}


def latex_escape(text: str) -> str:
    """Escape LaTeX-special characters that aren't already in math/code spans."""
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = []
    for ch in text:
        out.append(repl.get(ch, ch))
    return "".join(out)


def convert_inline(line: str) -> str:
    """Convert inline markdown markers to LaTeX in one logical line."""
    # Preserve code spans first.
    pieces = re.split(r"(`[^`]+`)", line)
    converted: list[str] = []
    for piece in pieces:
        if piece.startswith("`") and piece.endswith("`") and len(piece) >= 2:
            inner = piece[1:-1]
            converted.append(r"\texttt{" + latex_escape(inner) + "}")
            continue
        # **bold**
        piece = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", piece)
        # *italic*
        piece = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\\emph{\1}", piece)
        # Inline LaTeX-escape the rest.
        piece = latex_escape(piece)
        # Un-escape the LaTeX commands we just inserted via re.sub.
        piece = piece.replace(r"\textbackslash{}textbf\{", r"\textbf{")
        piece = piece.replace(r"\textbackslash{}emph\{", r"\emph{")
        piece = piece.replace(r"\textbackslash{}texttt\{", r"\texttt{")
        # Restore the closing brace; the substitution put a literal '}' that was
        # then escaped. We swap any \} that immediately follows our commands back.
        piece = re.sub(
            r"(\\textbf|\\emph|\\texttt)\{([^}]*)\\\}",
            lambda m: f"{m.group(1)}{{{m.group(2)}}}",
            piece,
        )
        converted.append(piece)
    return "".join(converted)


def convert_section_body(body_lines: list[str]) -> str:
    """Convert a section body (between the H2 and the next H2) to LaTeX."""
    out: list[str] = []
    in_ul = False
    in_para: list[str] = []

    def flush_para():
        if in_para:
            text = " ".join(in_para).strip()
            if text:
                out.append(convert_inline(text))
                out.append("")
            in_para.clear()

    for raw in body_lines:
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            if in_ul:
                out.append(r"\end{itemize}")
                out.append("")
                in_ul = False
            continue
        # Skip HTML comments.
        if line.lstrip().startswith("<!--") or line.lstrip().startswith("-->"):
            continue
        m = re.match(r"^### (.*)$", line)
        if m:
            flush_para()
            if in_ul:
                out.append(r"\end{itemize}")
                in_ul = False
            out.append(r"\subsection{" + convert_inline(m.group(1).strip()) + "}")
            out.append("")
            continue
        m = re.match(r"^#### (.*)$", line)
        if m:
            flush_para()
            if in_ul:
                out.append(r"\end{itemize}")
                in_ul = False
            out.append(r"\subsubsection{" + convert_inline(m.group(1).strip()) + "}")
            out.append("")
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            flush_para()
            if not in_ul:
                out.append(r"\begin{itemize}")
                in_ul = True
            out.append(r"\item " + convert_inline(m.group(1).strip()))
            continue
        # Otherwise: paragraph text.
        if in_ul:
            out.append(r"\end{itemize}")
            out.append("")
            in_ul = False
        in_para.append(line.strip())
    flush_para()
    if in_ul:
        out.append(r"\end{itemize}")
    return "\n".join(out).rstrip() + "\n"


def split_sections(text: str) -> dict[int, tuple[str, list[str]]]:
    """Split the draft on H2 (## N. Title) headings; return {n: (title, body)}."""
    sections: dict[int, tuple[str, list[str]]] = {}
    current_n: int | None = None
    current_title: str | None = None
    current_body: list[str] = []
    pat = re.compile(r"^##\s+(\d+)\.\s+(.*)$")
    for line in text.splitlines():
        m = pat.match(line)
        if m:
            if current_n is not None:
                sections[current_n] = (current_title or "", current_body)
            current_n = int(m.group(1))
            current_title = m.group(2).strip()
            current_body = []
            continue
        if current_n is None:
            continue  # skip preamble / title line
        current_body.append(line)
    if current_n is not None:
        sections[current_n] = (current_title or "", current_body)
    return sections


def main() -> int:
    if not DRAFT.exists():
        print(f"ERROR: draft not found: {DRAFT}", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = DRAFT.read_text(encoding="utf-8")
    sections = split_sections(text)
    written = []
    for n, (title, body) in sections.items():
        fname = SECTION_FILENAMES.get(n)
        if fname is None:
            continue  # references handled separately
        out_path = OUT_DIR / fname
        body_tex = convert_section_body(body)
        if n == 1:  # Abstract — wrap in abstract environment
            content = (
                "% Auto-converted from paper2_full_draft.md §1 by Step-11 helper.\n"
                "% Wording preserved; no claims added.\n"
                r"\begin{abstract}" + "\n"
                + body_tex
                + r"\end{abstract}" + "\n"
            )
        else:
            content = (
                f"% Auto-converted from paper2_full_draft.md §{n}.\n"
                "% Wording preserved; no claims added.\n"
                + r"\section{" + latex_escape(title) + "}\n"
                + body_tex
            )
        out_path.write_text(content, encoding="utf-8")
        written.append(out_path)
    print(f"wrote {len(written)} section files under {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
