#!/usr/bin/env python3
"""
Resolve the conflicts a docs merge REFUSED to ours, after they have been read.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-06_docs_conflict_resolve.py`, which refuses these on purpose

`2026-09-06_docs_conflict_resolve.py` refuses a hunk whose theirs-side carries a code fence,
because a fence is structure and dropping one unbalances every fence after it. Those hunks are
read by hand, and the read has produced two different answers:

  OURS (default)  main REWROTE the section the parked branch still describes, so ours is the
                  descendant and theirs is its ancestor. Measured on #1628, where theirs still
                  claimed `summarise` drops None before uniqueness -- the fail-open ml#1776 fixed.
  --both          the two sides are ADJACENT sections git could not align. #1635's ours is
                  `## Ruleset Context Audit` and its theirs is a `Related:` sentence plus an
                  entirely new `## Ruleset Scope Guard` that main has nowhere. Dropping theirs
                  there loses a whole operator surface.

Either way it prints what it drops, because a tool that discards text silently is how the last
consolidation shipped two superseded security bounds. The printout IS the record; capture it.

Usage:
    2026-09-06_docs_take_ours.py [--both] <file> [<file> ...]

Exit: 0 when at least one conflict was resolved; 1 when a file had none.
"""

from __future__ import annotations

import sys
from pathlib import Path


def take_ours(path: Path, both: bool = False) -> tuple[int, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    dropped: list[str] = []
    n = 0
    i = 0
    while i < len(lines):
        if not lines[i].startswith("<<<<<<< "):
            out.append(lines[i])
            i += 1
            continue
        i += 1
        while i < len(lines) and not lines[i].startswith("======="):
            out.append(lines[i])
            i += 1
        i += 1
        while i < len(lines) and not lines[i].startswith(">>>>>>> "):
            (out if both else dropped).append(lines[i])
            i += 1
        i += 1
        n += 1
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n, dropped


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    both = "--both" in args
    total = 0
    for arg in (a for a in args if a != "--both"):
        p = Path(arg)
        n, dropped = take_ours(p, both=both)
        mode = "ours THEN theirs" if both else "ours"
        print(f"{p}: {n} conflict(s) resolved to {mode}, {len(dropped)} line(s) of theirs dropped")
        for line in dropped:
            print(f"    | {line}")
        total += n
    return 0 if total else 1


if __name__ == "__main__":
    raise SystemExit(main())
