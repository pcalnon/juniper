#!/usr/bin/env python3
"""2026-09-08_version_collision_recency.py -- which row of a colliding version pair landed later?

Project: juniper-ml
Sub-Project: docs/REFERENCE.md version-history repair
Application: ad-hoc analysis (documentation integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`docs/REFERENCE.md`'s Version History has four doubly-claimed version numbers (0.6.19,
0.6.27, 0.6.40, 0.6.59 -- eight rows), an artifact of concurrent PR authorship during the
Cursor-fleet consolidation.

The obvious disambiguation rule -- "mark the LATER-DATED row of each pair" -- cannot be
applied: **both rows of all four pairs carry the SAME date.** Document order is no better,
because the table is not sorted (0.6.60 and 0.6.61 precede 0.6.22).

So recency has to come from the only record that actually holds it: git history. For each
row this runs `git log -S<row substring>` over docs/REFERENCE.md and reports the commit
that introduced it, oldest-first. That converts "which one do I mark" from an invention
into a recovered fact.

Usage:
    python3 util/ad-hoc/2026-09-08_version_collision_recency.py
"""

from __future__ import annotations

import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from collections import defaultdict
from pathlib import Path

DOC = Path("docs/REFERENCE.md")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603 -- fixed argv, no shell
        ["git", *args], capture_output=True, text=True
    )


def main() -> int:
    if not DOC.is_file():
        print(f"{DOC} not found -- run from the repo root", file=sys.stderr)
        return 2

    lines = DOC.read_text(encoding="utf-8").splitlines()
    fence = re.compile(r"^\s*(```|~~~)")
    in_fence = False
    rows: list[tuple[str, str, int, str]] = []
    for i, ln in enumerate(lines):
        if fence.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^\|\s*(\d+\.\d+\.\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|", ln)
        if m:
            rows.append((m.group(1), m.group(2), i + 1, ln))

    by_version: dict[str, list] = defaultdict(list)
    for version, date, lineno, text in rows:
        by_version[version].append((date, lineno, text))

    collisions = {v: rs for v, rs in by_version.items() if len(rs) > 1}
    if not collisions:
        print("no colliding version numbers")
        return 0

    print(f"{len(collisions)} colliding version(s), {sum(len(r) for r in collisions.values())} rows\n")
    for version in sorted(collisions, key=lambda s: [int(x) for x in s.split(".")]):
        print(f"=== {version}")
        for date, lineno, text in collisions[version]:
            # A distinctive slice of the Changes cell: enough to be unique, short enough
            # to survive the reflow a later edit may have applied.
            cell = text.split("|")[3] if text.count("|") >= 4 else text
            needle = cell.strip()[:60]
            res = git("log", "--follow", "--format=%h %ad %s", "--date=short",
                      f"-S{needle}", "--", str(DOC))
            hits = [h for h in res.stdout.splitlines() if h.strip()]
            introduced = hits[-1] if hits else "(not located)"
            print(f"  line {lineno}  date-col {date}")
            print(f"     changes : {needle}")
            print(f"     added by: {introduced}")
        print()

    print("The Date column ties in every pair, so it cannot order them; the 'added by'")
    print("commit is the only recovered recency signal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
