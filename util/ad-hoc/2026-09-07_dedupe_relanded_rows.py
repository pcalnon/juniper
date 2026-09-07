#!/usr/bin/env python3
"""
Remove table rows a re-land duplicated, by comparing against the file as a BASELINE ref had it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-07
Status: ad-hoc -- one-off (cursor-fleet PR disposition, #1799 re-land repair)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-07_dedupe_relanded_sections.py`, which repaired the section level first

Deduping section headings is not enough. After five whole `##` sections were resolved, the
duplicate-row count still read 397 against the pre-#1799 baseline's 361: rows the re-land added
OUTSIDE those sections, including version-history entries like `| 0.6.27 | 2026-09-04 | ... |`
twice, byte-identical.

WHY THIS COMPARES AGAINST A REF RATHER THAN JUST DEDUPING

A repeated row is not automatically wrong. Two different tables can each carry a `| Task |`
header, and `| aggregate.csv |` can legitimately appear in a pitfalls table and an inputs table.
Deduping on "appears twice" would delete real content.

What IS wrong is a row appearing MORE times than it did before the re-land. So the unit is the
exact row text, the question is the delta against `--base`, and only the EXCESS occurrences go --
last-first, so the earliest copy (the one that was already there) survives.

Usage:
    2026-09-07_dedupe_relanded_rows.py <file> --base <ref> [--apply]

Exit: 0 when the file matches the baseline's duplicate profile; 1 when excess rows remain or
      the baseline could not be read.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from collections import Counter
from pathlib import Path

TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
FENCE = re.compile(r"^\s*(?:```|~~~)")
SEPARATOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def rows_of(lines: list[str]) -> Counter[str]:
    """Every non-separator table row OUTSIDE a fence, counted by its exact text."""
    counts: Counter[str] = Counter()
    in_fence = False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or line[:4] == "    ":
            continue
        if TABLE_ROW.match(line) and not SEPARATOR.match(line):
            counts[line.rstrip()] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--base", required=True, help="ref whose copy of the file is the baseline")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.path)
    blob = subprocess.run(["git", "show", f"{args.base}:{path}"], capture_output=True, text=True, timeout=300, check=False)
    if blob.returncode != 0:
        print(f"cannot read {args.path} at {args.base}", file=sys.stderr)
        return 1

    lines = path.read_text(encoding="utf-8").splitlines()
    before, now = rows_of(blob.stdout.splitlines()), rows_of(lines)
    # `max(..., 1)`: a row the baseline never had is an ADDITION, not an excess. Without it
    # the whole of a newly-added section reads as duplication -- and on docs/REFERENCE.md it
    # cost a genuine version-history row, caught only by the after-the-fact branch-vs-result
    # comparison. Same bug the region-level sibling had; written from memory, not from the fix.
    excess = {row: now[row] - max(before.get(row, 0), 1) for row in now if now[row] > max(before.get(row, 0), 1)}
    if not excess:
        print(f"{path}: no row appears more often than at {args.base}")
        return 0

    print(f"{path}: {len(excess)} row text(s) appear more often than at {args.base}, {sum(excess.values())} excess occurrence(s)")
    for row, n in sorted(excess.items(), key=lambda kv: -kv[1])[:12]:
        print(f"   +{n}  {row.strip()[:120]}")
    if len(excess) > 12:
        print(f"   ... {len(excess) - 12} more")

    if not args.apply:
        print("\n(dry run -- pass --apply to write)")
        return 1

    # Drop the LAST occurrences, so the copy that was already there keeps its position.
    seen: Counter[str] = Counter()
    order = {row: [i for i, ln in enumerate(lines) if ln.rstrip() == row] for row in excess}
    drop: set[int] = set()
    for row, n in excess.items():
        for idx in order[row][-n:]:
            drop.add(idx)
        seen[row] = n
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    path.write_text("\n".join(kept).rstrip("\n") + "\n", encoding="utf-8")
    print(f"\nwrote {path}: {len(drop)} row(s) removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
