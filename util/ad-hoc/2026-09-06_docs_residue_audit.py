#!/usr/bin/env python3
"""
Ask, of every line the consolidation held back: did an equivalent one land anyway?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-06_docs_consolidate.py`, whose residue report this reads

The consolidation writes nothing it cannot address, and prints what it held back. 337 lines is
too many to read one by one AND too many to wave through, so split them first.

A held-back line falls into one of three buckets, and only the third needs a human:

  LANDED     the same text is in the merged tree. The line was refused as unkeyable in ITS hunk
             while a keyed sibling carrying it landed from another PR -- 35 PRs describe
             overlapping ground, so this is the common case.
  NEAR       a line sharing its distinctive tokens is in the tree. Usually the same claim in
             different words; worth a glance, not a decision.
  ABSENT     nothing like it is in the tree. This is the real residue.

"Distinctive tokens" are the backticked identifiers and link anchors -- prose gets reworded,
paths and anchors do not. A line with none of those cannot be matched this way and is reported
ABSENT, which is the conservative direction.

Usage:
    2026-09-06_docs_residue_audit.py <residue-file> [<residue-file> ...]

Exit: 0 when nothing is ABSENT; 1 when something is.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TOKEN = re.compile(r"`([^`]+)`|\]\(([^)]+)\)")
DOCS = ("docs/REFERENCE.md", "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "docs/DOCUMENTATION_OVERVIEW.md", "docs/QUICK_START.md", "util/ad-hoc/README.md")


def tokens(line: str) -> set[str]:
    return {(a or b).strip() for a, b in TOKEN.findall(line) if (a or b).strip()}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2

    corpus = "\n".join(Path(d).read_text(encoding="utf-8") for d in DOCS if Path(d).exists())
    corpus_lines = corpus.splitlines()

    absent: list[tuple[str, str]] = []
    counts = {"LANDED": 0, "NEAR": 0, "ABSENT": 0}
    pr = ""
    for arg in args:
        for raw in Path(arg).read_text(encoding="utf-8").splitlines():
            if raw.startswith("=== #"):
                pr = raw[4:]
                continue
            if not raw.startswith("        |"):
                continue
            line = raw[10:]
            if not line.strip():
                continue
            if line.strip() in corpus:
                counts["LANDED"] += 1
                continue
            want = tokens(line)
            if want and any(want <= tokens(c) for c in corpus_lines):
                counts["NEAR"] += 1
                continue
            counts["ABSENT"] += 1
            absent.append((pr, line))

    for key in ("LANDED", "NEAR", "ABSENT"):
        print(f"{key:<7} {counts[key]}")
    print()
    for pr, line in absent:
        print(f"{pr[:60]:<60} | {line[:160]}")
    return 1 if counts["ABSENT"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
