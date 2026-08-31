#!/usr/bin/env python3
"""Find hazard-shaped directives in SOURCE that have no counterpart in AGENTS.md.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (plan §P5 step e — cut prerequisite, second pass)
Author:      Paul Calnon
License:     MIT

Why this exists, and why it is a different tool from the hazard triage.

`2026-08-28_hazard_triage.py` reads AGENTS.md and asks "which of these directives must stay
resident through the cut". That question can only ever rank text that is ALREADY there. The
canopy session then produced the strongest hazard in its whole repo — and it is not in AGENTS.md
at all. It is a comment at `dashboard_manager.py:3869`:

    # CRITICAL (Dash execution model): ws-metrics-buffer is deliberately NOT an Input here.
    # Its clientside producer returns ``no_update`` whenever the WS is quiet, and a chained
    # Input whose producer no_updates makes Dash SKIP this interval-only callback for that
    # tick -- which silently re-creates the I-1 starvation

`grep -icE "no_update|execution model|starv" AGENTS.md` -> 0. A directive its own author labelled
CRITICAL, whose violation is silent, which already cost a P0/P1, discoverable only by reading a
comment 3,869 lines into a 7,000-line file.

So a cut that only decides where existing text goes will never surface it. This asks the
complementary question: **what is hazard-shaped in the code and resident nowhere?**

Method. Scan source comments and docstrings for hazard markers (CRITICAL / NEVER / MUST NOT /
"deliberately not" / "silently" / "do not remove"). For each hit, extract its distinctive
identifiers -- `backtick_quoted`, snake_case, dotted.paths, CONSTANT_CASE -- and ask whether ANY of
them appears in AGENTS.md. A hit whose identifiers are entirely absent is a candidate: the code
knows something the always-resident file does not.

Reads a LOCAL checkout, read-only. Safe to point at a primary with a live service running out of
it; nothing is written and no git state is touched.

Usage:
    python3 util/ad-hoc/2026-08-28_resident_gap_scan.py /path/to/juniper-canopy
    python3 util/ad-hoc/2026-08-28_resident_gap_scan.py /path/to/repo --glob 'src/**/*.py' --max 40
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Directory names that hold COPIES of the repo (or of other projects), not source to scan.
#
# ``.claude/worktrees`` is the one that matters and the one that bit: juniper-ml keeps its
# session worktrees INSIDE the repo, so the default ``*/**/*.py`` glob walked ~60 full copies
# of the tree. A 2026-08-31 run reported 23,120 files / 15,285 candidates, the top hits being
# the same ``util/experiments/run_experiment.py`` counted once per worktree. That is not a
# large result, it is one result multiplied -- the sort of number a reader trusts because it
# is big. Scoped to real source the same repo yields 419 files / 294 candidates.
SKIP_DIRS = frozenset({
    ".git",
    ".claude",          # session worktrees live under .claude/worktrees/ in juniper-ml
    "worktrees",        # and directly under <repo>/worktrees/ elsewhere
    "backups",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "legacy",
    "juniper-legacy",
})

MARKER = re.compile(
    r"\b(CRITICAL|IMPORTANT|WARNING|HAZARD|NEVER|MUST NOT|DO NOT|deliberately not|"
    r"silently|silent|never be|must never|do not remove|do not change|gotcha|footgun|"
    r"load-bearing|breaks? silently|no error)\b", re.I)

# Identifiers worth asking AGENTS.md about. Bare English words are useless here -- the question is
# whether the SPECIFIC thing the comment names is mentioned anywhere resident.
#
# The backtick arm must look like CODE, not prose. A first version accepted any `...` span up to 60
# chars, and these comments quote whole clauses in backticks -- so "names:" filled with fragments
# like "), and the verbatim rejection detail (". Those are unmatchable against AGENTS.md by
# construction, which inflates every candidate's score and buries the real ones.
IDENT = re.compile(
    r"`([A-Za-z_][\w.]*(?:\([^`]{0,20}\))?|[A-Z][A-Z0-9_]{2,})`"   # `foo_bar`, `a.b.c`, `f()`, `CONST`
    r"|\b([a-z][a-z0-9]*(?:_[a-z0-9]+){1,})\b"                      # snake_case
    r"|\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+){1,})\b"                      # CONSTANT_CASE
)

COMMENT = re.compile(r"^\s*#\s?(.*)$")
STOP = {
    "no_update", "self_", "__init__", "__main__", "type_", "id_",
}


def comment_blocks(path: Path) -> list[tuple[int, str]]:
    """Contiguous `#` comment runs, as (start_line, joined_text). Docstrings are included crudely
    by treating a line inside a triple-quoted block as prose."""
    out: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    cur: list[str] = []
    start = 0
    in_doc = False
    for i, ln in enumerate(lines):
        ticks = ln.count('"""') + ln.count("'''")
        if ticks % 2 == 1:
            in_doc = not in_doc
        m = COMMENT.match(ln)
        if m:
            if not cur:
                start = i + 1
            cur.append(m.group(1))
            continue
        if in_doc and ln.strip():
            if not cur:
                start = i + 1
            cur.append(ln.strip())
            continue
        if cur:
            out.append((start, " ".join(cur)))
            cur = []
    if cur:
        out.append((start, " ".join(cur)))
    return out


def identifiers(text: str) -> set[str]:
    found = set()
    for a, b, c in IDENT.findall(text):
        for tok in (a, b, c):
            t = tok.strip()
            if len(t) >= 4 and t.lower() not in STOP:
                found.add(t)
    return found


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("--glob", action="append", default=None,
                    help="source globs (repeatable); default src/**/*.py and <pkg>/**/*.py")
    ap.add_argument("--agents", default="AGENTS.md")
    ap.add_argument("--max", type=int, default=30, help="max candidates to print")
    ap.add_argument("--min-len", type=int, default=60, help="ignore comment blocks shorter than this")
    ns = ap.parse_args(argv)

    repo = ns.repo.resolve()
    agents_path = repo / ns.agents
    if not agents_path.is_file():
        print(f"no {ns.agents} in {repo}")
        return 2
    agents = agents_path.read_text(encoding="utf-8", errors="replace")
    agents_low = agents.lower()

    globs = ns.glob or ["src/**/*.py", "*/**/*.py"]
    seen: set[Path] = set()
    for g in globs:
        for p in repo.glob(g):
            if not p.is_file() or "test" in p.name:
                continue
            if SKIP_DIRS.intersection(p.parts):
                continue
            seen.add(p)
    files = sorted(seen)

    cands = []
    scanned = 0
    for f in files:
        for lno, text in comment_blocks(f):
            if len(text) < ns.min_len or not MARKER.search(text):
                continue
            scanned += 1
            idents = identifiers(text)
            if not idents:
                continue
            present = {i for i in idents if i.lower() in agents_low}
            if present:
                continue                       # AGENTS.md already names something specific here
            marks = sorted({m.group(0).upper() for m in MARKER.finditer(text)})
            cands.append((len(idents), f.relative_to(repo), lno, text, marks, sorted(idents)[:8]))

    cands.sort(key=lambda c: -c[0])
    print(f"repo      : {repo}")
    print(f"source    : {len(files)} file(s) over {globs}")
    print(f"marked    : {scanned} hazard-marked comment block(s) >= {ns.min_len} chars")
    print(f"CANDIDATES: {len(cands)} whose identifiers are ENTIRELY ABSENT from {ns.agents}\n")
    for n, rel, lno, text, marks, idents in cands[: ns.max]:
        print(f"  [{n:>2} idents] {rel}:{lno}   {','.join(marks)}")
        print(f"      {text[:220]}")
        print(f"      names: {', '.join(idents)}")
        print()
    if len(cands) > ns.max:
        print(f"  ... {len(cands) - ns.max} more not shown (--max)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
