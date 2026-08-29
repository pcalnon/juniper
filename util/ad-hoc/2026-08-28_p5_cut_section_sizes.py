#!/usr/bin/env python3
"""Size every top-level section of a repo's AGENTS.md, to scope the P5 cut.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (plan §P5 step e — the cut)
Author:      Paul Calnon
License:     MIT

The cut relocates reference material out of AGENTS.md into docs/REFERENCE.md.
Deciding WHAT to move needs per-section char counts, which no existing tool
reports: `measure-growth` measures the file over time, and the census measures
the whole file. This prints one row per `## ` section with its char count and
share of the file, plus the running total if you cut from the largest down.

Chars, not bytes -- that is the ceiling's unit (the byte/char confusion already
produced one wrong census on 2026-08-25).

Usage:
    python3 util/ad-hoc/2026-08-28_p5_cut_section_sizes.py juniper-cascor [...]
    python3 util/ad-hoc/2026-08-28_p5_cut_section_sizes.py --all
"""
from __future__ import annotations

import argparse
import base64
import re
import subprocess  # nosec B404 -- fixed-argv `gh api` calls only; nothing is shell-interpolated
import sys

GOVERNED = [
    "juniper-canopy",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-recurrence",
    "juniper-data-client",
    "juniper-data",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-ml",
]


def contents(repo: str, path: str) -> str | None:
    """Decoded file text on main, or None only on a genuine 404."""
    p = subprocess.run(  # nosec B603 B607 -- fixed argv, gh on PATH by policy
        ["gh", "api", f"repos/pcalnon/{repo}/contents/{path}?ref=main", "--jq", ".content"],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        err = (p.stderr or p.stdout).strip()
        if "HTTP 404" in err or '"status":"404"' in err:
            return None
        raise RuntimeError(f"gh api {repo}/{path}: {err[:300]}")
    return base64.b64decode(p.stdout.strip()).decode("utf-8", "replace")


def fence_mask(lines: list[str]) -> list[bool]:
    """True for each line that sits INSIDE a fenced code block.

    Naive `startswith("```")` toggling is wrong and fails loudly on real files: juniper-canopy's
    AGENTS.md wraps three-backtick examples in FOUR-backtick fences, so the inner ``` flip the
    parity and every heading after the first such block is mis-classified. That file has 189 fence
    lines (odd), and a naive tracker swallowed 13 real `## ` headings while promoting two markdown
    examples into 15K "sections".

    CommonMark rule, which this implements: a fence opens with >= 3 of ` or ~ and may carry an info
    string; it is closed only by a fence of the SAME character, at least as long, carrying NO info
    string. An unclosed fence runs to EOF.
    """
    mask = [False] * len(lines)
    char: str | None = None
    count = 0
    for i, raw in enumerate(lines):
        s = raw.lstrip()
        indent = len(raw) - len(s)
        m = re.match(r"^(`{3,}|~{3,})(.*)$", s) if indent <= 3 else None
        if m is None:
            mask[i] = char is not None
            continue
        run, info = m.group(1), m.group(2).strip()
        if char is None:
            char, count = run[0], len(run)
            mask[i] = False          # the opening fence itself is not "inside"
        elif run[0] == char and len(run) >= count and not info:
            char, count = None, 0
            mask[i] = False          # nor is the closing fence
        else:
            mask[i] = True           # a fence-looking line inside an open block is content
    return mask


def sections(text: str) -> list[tuple[str, int, int]]:
    """(title, chars, start_line) for each top-level `## ` section, fenced blocks excluded."""
    lines = text.splitlines(keepends=True)
    inside = fence_mask([ln.rstrip("\n") for ln in lines])
    marks: list[tuple[str, int]] = []
    for i, line in enumerate(lines):
        if inside[i]:
            continue
        if line.startswith("## "):
            marks.append((line[3:].strip(), i))
    out = []
    for n, (title, start) in enumerate(marks):
        end = marks[n + 1][1] if n + 1 < len(marks) else len(lines)
        out.append((title, len("".join(lines[start:end])), start + 1))
    return out


def report(repo: str) -> None:
    agents = contents(repo, "AGENTS.md")
    if agents is None:
        print(f"\n### {repo}: no AGENTS.md")
        return
    ref = contents(repo, "docs/REFERENCE.md")
    total = len(agents)
    secs = sections(agents)
    preamble = total - sum(s[1] for s in secs)
    print(f"\n### {repo}  AGENTS.md {total:,} chars  "
          f"docs/REFERENCE.md {('%s chars' % f'{len(ref):,}') if ref is not None else 'ABSENT -- create first'}")
    print(f"    {len(secs)} top-level sections; {preamble:,} chars of preamble before the first one")
    print(f"    {'chars':>8} {'share':>6} {'cum':>6}  L{'':<5} section")
    cum = 0
    for title, chars, line in sorted(secs, key=lambda s: -s[1]):
        cum += chars
        print(f"    {chars:>8,} {chars / total * 100:>5.1f}% {cum / total * 100:>5.1f}%  L{line:<5} {title[:64]}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repos", nargs="*", help="repo names; default: the two lacking a REFERENCE.md")
    ap.add_argument("--all", action="store_true", help="every governed repo")
    ns = ap.parse_args(argv)
    repos = GOVERNED if ns.all else (ns.repos or ["juniper-cascor", "juniper-recurrence"])
    for r in repos:
        report(r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
