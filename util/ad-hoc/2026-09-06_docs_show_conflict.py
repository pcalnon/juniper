#!/usr/bin/env python3
"""
Show a refused docs conflict compactly enough to decide OURS vs OURS-THEN-THEIRS.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-06_docs_take_ours.py`, which applies the decision

The decision on a fenced hunk turns on one question -- does OURS already cover what THEIRS
says? -- and the fastest way to answer it is the HEADINGS each side carries, not their prose.
A heading theirs has and ours lacks means new material. A heading both carry means a rewrite,
and then ours is the descendant.

So this prints each side's headings first, then the opening line of every paragraph, truncated.
Full text is one `sed -n` away when a case is genuinely ambiguous; most are not.

Usage:
    2026-09-06_docs_show_conflict.py <file> [--width N]

Exit: 0 when the file had at least one conflict; 1 when it had none.
"""

from __future__ import annotations

import sys
from pathlib import Path


def headings(block: list[str]) -> list[str]:
    return [ln.strip() for ln in block if ln.lstrip().startswith("#")]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    width = 120
    if "--width" in args:
        idx = args.index("--width")
        width = int(args[idx + 1])
        args = args[:idx] + args[idx + 2 :]

    found = 0
    for arg in args:
        lines = Path(arg).read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            if not lines[i].startswith("<<<<<<< "):
                i += 1
                continue
            j = i
            while j < len(lines) and not lines[j].startswith("======="):
                j += 1
            k = j
            while k < len(lines) and not lines[k].startswith(">>>>>>> "):
                k += 1
            ours, theirs = lines[i + 1 : j], lines[j + 1 : k]
            found += 1
            print(f"=== {arg} @{i+1}  ours={len(ours)} theirs={len(theirs)}")
            our_h, their_h = headings(ours), headings(theirs)
            print(f"  ours headings   : {our_h or '(none)'}")
            print(f"  theirs headings : {their_h or '(none)'}")
            only_theirs = [h for h in their_h if h not in our_h]
            print(f"  ONLY in theirs  : {only_theirs or '(none -- theirs is a rewrite of ours)'}")
            for label, block in (("O", ours), ("T", theirs)):
                print(f"  --- {label} ---")
                for ln in block:
                    if ln.strip():
                        print(f"  {label}| {ln[:width]}")
            i = k + 1
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
