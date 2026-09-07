#!/usr/bin/env python3
"""
Count DUPLICATE headings and duplicate table rows -- the damage a re-landed consolidation makes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-07
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-05_markdown_structure_check.py`, which cannot see this class

`markdown_structure_delta.py` gates STRUCTURE: unbalanced fences, swallowed headings, a table
header with no separator. All three are damage to a document's SHAPE, and a re-landed
consolidation does not damage the shape -- it duplicates the CONTENT. Every heading is still
balanced, every table still has its separator, and the same section now appears twice.

So the gate that just shipped is not the instrument for this question, and saying so is the
point: measured 2026-09-07, `main` scores 0 structural problems on the five consolidated
documents immediately after #1799 re-landed six PRs #1797 had already carried.

This asks the adjacent question the other screen cannot: which `##` / `###` headings, and which
table rows keyed on their first cell, now appear more than once in one file?

A duplicate is not automatically a defect -- `### Operator pitfalls` closes every operator
section by design, and a row key can legitimately recur across two different tables. So this
reports and ranks; it does not judge. What it is for is telling a re-land apart from a no-op.

Usage:
    2026-09-07_duplicate_section_census.py <file> [<file> ...]

Exit: 0 always -- a count is not a verdict.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

HEADING = re.compile(r"^(#{2,6})\s+(.*\S)\s*$")
TABLE_ROW = re.compile(r"^\s*\|(.*)\|\s*$")
FENCE = re.compile(r"^\s*(?:```|~~~)")


def census(path: Path) -> tuple[Counter[str], Counter[str]]:
    headings: Counter[str] = Counter()
    rows: Counter[str] = Counter()
    in_fence = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or line[:4] == "    ":
            continue
        m = HEADING.match(line)
        if m:
            headings[f"{m.group(1)} {m.group(2)}"] += 1
            continue
        m = TABLE_ROW.match(line)
        if m:
            first = m.group(1).split("|")[0].strip()
            if first and not set(first) <= set("-: "):
                rows[re.sub(r"[`*_ ]+", "", first).lower()] += 1
    return headings, rows


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    total_h = total_r = 0
    for arg in args:
        path = Path(arg)
        if not path.is_file():
            continue
        headings, rows = census(path)
        dup_h = {k: n for k, n in headings.items() if n > 1}
        dup_r = {k: n for k, n in rows.items() if n > 1}
        if not dup_h and not dup_r:
            continue
        # COUNT first, then display. Accumulating inside a display-capped loop made the total
        # count only what it printed -- it reported 149 duplicate rows against a real 397, and
        # the baseline 148 against a real 361, so even the DELTA looked plausible.
        total_h += sum(n - 1 for n in dup_h.values())
        total_r += sum(n - 1 for n in dup_r.values())
        print(f"=== {arg}")
        for k, n in sorted(dup_h.items(), key=lambda kv: -kv[1]):
            print(f"   heading x{n}: {k[:110]}")
        shown = sorted(dup_r.items(), key=lambda kv: -kv[1])
        for k, n in shown[:15]:
            print(f"   row     x{n}: {k[:110]}")
        if len(shown) > 15:
            print(f"   ... {len(shown) - 15} more duplicated row key(s), counted but not listed")
    print()
    print(f"duplicate headings beyond the first: {total_h}")
    print(f"duplicate row keys beyond the first: {total_r}")
    print()
    print("Neither is automatically a defect -- `### Operator pitfalls` closes every operator")
    print("section by design. This tells a RE-LAND apart from a no-op; it does not judge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
