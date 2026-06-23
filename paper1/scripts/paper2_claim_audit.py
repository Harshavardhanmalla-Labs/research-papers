#!/usr/bin/env python3
"""Paper 2 manuscript claim-audit script.

Scans a markdown file for forbidden phrases per F3 §6 + F5 SM-4/SM-5 + Step-10
brief. Exit code 0 = PASS; non-zero = FAIL. Lists each violation with line
number, file path, and offending phrase.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

# Always-forbidden phrases.
ALWAYS_FORBIDDEN: tuple[str, ...] = (
    "outperforms",
    "outperform",  # variant
    "superior",
    "state-of-the-art",
    "state of the art",
    "government deployment",
    "compliance achieved",
    "calibrated model improves",
    "learned model",
    "first ever",  # avoid "first" overclaims
)

# Conditional-forbidden phrases: forbidden UNLESS preceded by a negation token
# within ~6 words (~60 chars).
NEGATABLE_PHRASES: tuple[str, ...] = (
    "validated",
    "production",
)
NEGATION_PREFIX_RE = re.compile(
    r"\b(not|no|never|does not|did not|is not|are not|was not|were not|"
    r"cannot|can not|won't|will not|without)\b",
    re.IGNORECASE,
)

# "significant" within 100 characters of any of these diagnostic-only metric tokens.
DIAGNOSTIC_TOKENS: tuple[str, ...] = (
    "precision_at_k", "precision@k", "precision at k",
    "recall_at_k", "recall@k", "recall at k",
    "ndcg_at_k", "ndcg@k", "ndcg",
    "kev breach", "kev_breach", "kev deadline",
    "diagnostic",
)
DIAGNOSTIC_WINDOW_CHARS = 100

# "pair count" within 200 chars of "sample size" OR "effective N".
PAIR_COUNT_WINDOW_CHARS = 200

# Claim-that-calibration-was-performed: positive claims that must NOT appear.
# Each pattern is a regex requiring positive sense (NOT preceded by negation
# within ~80 chars).
POSITIVE_CALIBRATION_CLAIMS: tuple[str, ...] = (
    r"calibration was performed",
    r"we calibrated",
    r"the calibrated weights",
    r"after calibration",
    r"calibration succeeded",
    r"the model was calibrated",
)
CALIBRATION_NEGATION_WINDOW_CHARS = 80

# Forbidden "context-priors beat EPSS" superiority claims.
SUPERIORITY_OVER_EPSS_RE = re.compile(
    r"\b(context[\s\-]?(?:aware|prior|priors)\b.{0,80}\b(?:beat|beats|"
    r"outperform|outperforms|surpass|surpasses|dominate|dominates)\b.{0,40}\bepss\b)",
    re.IGNORECASE | re.DOTALL,
)


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _has_negation_before(text: str, idx: int, window: int) -> bool:
    start = max(0, idx - window)
    snippet = text[start:idx]
    return bool(NEGATION_PREFIX_RE.search(snippet))


def find_violations(text: str) -> list[dict]:
    """Return a list of {line, type, phrase, snippet} violations."""
    violations: list[dict] = []
    lowered = text.lower()

    for phrase in ALWAYS_FORBIDDEN:
        for m in re.finditer(re.escape(phrase.lower()), lowered):
            ln = _line_for_offset(text, m.start())
            violations.append({
                "line": ln, "type": "always_forbidden", "phrase": phrase,
                "snippet": text[max(0, m.start() - 40):m.end() + 40].replace("\n", " "),
            })

    for phrase in NEGATABLE_PHRASES:
        for m in re.finditer(rf"\b{re.escape(phrase)}\b", lowered):
            if _has_negation_before(text, m.start(), 60):
                continue
            ln = _line_for_offset(text, m.start())
            violations.append({
                "line": ln, "type": "negatable_phrase_unnegated", "phrase": phrase,
                "snippet": text[max(0, m.start() - 40):m.end() + 40].replace("\n", " "),
            })

    for m in re.finditer(r"\bsignificant(?:ly)?\b", lowered):
        start, end = m.start(), m.end()
        window_start = max(0, start - DIAGNOSTIC_WINDOW_CHARS)
        window_end = min(len(lowered), end + DIAGNOSTIC_WINDOW_CHARS)
        window = lowered[window_start:window_end]
        for token in DIAGNOSTIC_TOKENS:
            if token in window:
                ln = _line_for_offset(text, start)
                violations.append({
                    "line": ln, "type": "significant_near_diagnostic",
                    "phrase": f"'significant' near '{token}'",
                    "snippet": text[window_start:window_end].replace("\n", " "),
                })
                break

    for m in re.finditer(r"\bpair[\s\-]?count\b", lowered):
        start, end = m.start(), m.end()
        ws = max(0, start - PAIR_COUNT_WINDOW_CHARS)
        we = min(len(lowered), end + PAIR_COUNT_WINDOW_CHARS)
        window = lowered[ws:we]
        if (
            re.search(r"\bsample[\s\-]?size\b", window)
            or re.search(r"\beffective\s+n\b", window)
        ):
            ln = _line_for_offset(text, start)
            violations.append({
                "line": ln, "type": "pair_count_as_sample_size",
                "phrase": "pair count used as sample size / effective N",
                "snippet": text[ws:we].replace("\n", " "),
            })

    for pattern in POSITIVE_CALIBRATION_CLAIMS:
        for m in re.finditer(pattern, lowered):
            if _has_negation_before(text, m.start(), CALIBRATION_NEGATION_WINDOW_CHARS):
                continue
            ln = _line_for_offset(text, m.start())
            violations.append({
                "line": ln, "type": "positive_calibration_claim",
                "phrase": pattern,
                "snippet": text[max(0, m.start() - 40):m.end() + 40].replace("\n", " "),
            })

    for m in SUPERIORITY_OVER_EPSS_RE.finditer(text):
        ln = _line_for_offset(text, m.start())
        violations.append({
            "line": ln, "type": "superiority_over_epss",
            "phrase": "context-priors superiority over EPSS",
            "snippet": text[max(0, m.start() - 20):m.end() + 20].replace("\n", " "),
        })

    return violations


def audit_file(path: pathlib.Path) -> int:
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    violations = find_violations(text)
    if not violations:
        print(f"PASS  {path} (0 violations)")
        return 0
    print(f"FAIL  {path} ({len(violations)} violations)")
    for v in violations:
        print(f"  L{v['line']:>4}  [{v['type']}]  {v['phrase']}")
        print(f"          …{v['snippet']}…")
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Paper 2 claim-audit scanner.")
    p.add_argument("path", help="markdown file to scan")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])
    return audit_file(pathlib.Path(args.path))


if __name__ == "__main__":
    raise SystemExit(main())
