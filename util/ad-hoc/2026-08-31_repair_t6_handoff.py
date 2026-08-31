#!/usr/bin/env python3
"""Diagnose and repair the self-duplicated T6 handoff archive file.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc archive repair
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-31
Status:      ad-hoc -- one-shot repair of
             prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-24_t6-rebaseline-campaign.md
Retire when: the file is repaired and merged.

The corruption
--------------
Found by an independent instrument audit while auditing a length census: this is
the ONLY file of 148 with a repeated ``##`` heading (16 headings, 8 unique) and
the only one with an odd fence-marker count, which is what made a naive
prose/code splitter understate it by >100%.

The file is not "two copies". It is THREE fragments, joined without newlines:

  1. lines 1 .. 475a  -- a TRUNCATED prefix of the document. It stops mid-way
     through a ``grep`` command in the section 5 verification block.
  2. line 475b .. 997 -- the COMPLETE document, title through section 7. Its
     title lost its leading ``# `` because it was concatenated onto the tail of
     fragment 1's grep command:
         grep -n "NOT AVAILABLE" ...nrot3.yaml HANDOFF 2026-08-24 - T6: ...
  3. lines 998 .. EOF -- a second copy of sections 6 and 7 only.

Why the repair is not simply "delete the duplicates"
----------------------------------------------------
Discarding fragment 1 is only safe if it is genuinely a prefix of fragment 2. If
it carried a single line fragment 2 lacks, a naive dedup would destroy archival
content while every heading-count check reported success. So this script REFUSES
to write unless it has proved, line by line, that fragment 1 is contained in
fragment 2 and that fragment 3 matches fragment 2's own sections 6-7.

Absence of a difference is asserted, not assumed: --check prints the comparison
and exits non-zero on any mismatch.

Usage:
    python3 util/ad-hoc/2026-08-31_repair_t6_handoff.py --check
    python3 util/ad-hoc/2026-08-31_repair_t6_handoff.py --write
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "prompts" / "thread-handoff_automated-prompts" / "HANDOFF_2026-08-24_t6-rebaseline-campaign.md"

TITLE = "# HANDOFF 2026-08-24 — T6: the E-A/E-I/E-C re-baseline, still owed"
TITLE_BARE = TITLE[2:]  # the concatenated copy lost its "# "


def split_fragments(text: str):
    """Return (frag1_lines, frag2_lines, frag3_lines) or raise on unexpected shape."""
    lines = text.split("\n")

    # The seam: the one line that contains the bare title but is not the real title.
    seams = [i for i, l in enumerate(lines) if TITLE_BARE in l and not l.startswith("# ")]
    if len(seams) != 1:
        raise SystemExit(f"expected exactly 1 seam line, found {len(seams)}: {seams}")
    s = seams[0]

    head, sep, tail = lines[s].partition(TITLE_BARE)
    if not sep:
        raise SystemExit("seam partition failed")

    frag1 = lines[:s] + [head.rstrip()]
    rest = [TITLE] + lines[s + 1 :]
    if tail.strip():
        raise SystemExit(f"unexpected trailing text on the seam line: {tail!r}")

    # Fragment 3 starts at the SECOND "## 6." within `rest`.
    sixes = [i for i, l in enumerate(rest) if l.startswith("## 6. ")]
    if len(sixes) != 2:
        raise SystemExit(f"expected 2 occurrences of '## 6.', found {len(sixes)}")
    frag2, frag3 = rest[: sixes[1]], rest[sixes[1] :]
    return frag1, frag2, frag3, sixes[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply the repair (default: check only)")
    args = ap.parse_args()

    text = TARGET.read_text(encoding="utf-8")
    frag1, frag2, frag3, six_idx = split_fragments(text)

    print(f"file            : {TARGET.name}")
    print(f"  fragment 1    : {len(frag1):5d} lines (truncated prefix?)")
    print(f"  fragment 2    : {len(frag2):5d} lines (candidate complete document)")
    print(f"  fragment 3    : {len(frag3):5d} lines (duplicate sections 6-7?)")

    problems = []

    # 1. fragment 1 must be a prefix of fragment 2, line for line.
    if len(frag1) > len(frag2):
        problems.append(f"fragment 1 ({len(frag1)}) is LONGER than fragment 2 ({len(frag2)})")
    else:
        diffs = [
            (i, frag1[i], frag2[i]) for i in range(len(frag1)) if frag1[i] != frag2[i]
        ]
        if diffs:
            problems.append(f"fragment 1 is NOT a prefix of fragment 2: {len(diffs)} differing line(s)")
            for i, a, b in diffs[:5]:
                print(f"    line {i+1}:\n      frag1: {a[:110]!r}\n      frag2: {b[:110]!r}")
        else:
            print(f"  OK  fragment 1 is a line-for-line prefix of fragment 2 "
                  f"(covers {len(frag1)}/{len(frag2)} lines); it carries nothing unique")

    # 2. fragment 3 must match fragment 2's own sections 6-7.
    #
    # Fragment 2's tail carries FOUR extra lines that fragment 3 does not: two
    # blanks, a `---` rule, and a blank. That rule is the separator the corrupting
    # write emitted BEFORE appending fragment 3 -- it is part of the join, not part
    # of the document, and fragment 3 (an independent copy of the same ending) not
    # having it is the evidence. It is stripped explicitly here, and named, rather
    # than absorbed by a looser comparison: a check relaxed until it passes proves
    # nothing.
    def norm(lines: list[str]) -> list[str]:
        out = [line.rstrip() for line in lines]
        while out and not out[-1]:
            out.pop()
        if out and out[-1] == "---":
            out.pop()
        while out and not out[-1]:
            out.pop()
        return out

    tail2 = frag2[six_idx:]
    a, b = norm(tail2), norm(frag3)
    if a != b:
        problems.append(f"fragment 3 does NOT match fragment 2's sections 6-7 ({len(a)} vs {len(b)} lines)")
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                print(f"    first diff at offset {i}:\n      frag2: {a[i][:110]!r}\n      frag3: {b[i][:110]!r}")
                break
    else:
        print(f"  OK  fragment 3 is identical to fragment 2's sections 6-7 ({len(a)} lines); redundant")

    if problems:
        print("\nREFUSING to write -- the repair is not provably lossless:")
        for p in problems:
            print(f"  - {p}")
        return 1

    # Emit fragment 2 with the join separator removed, so the repaired document
    # ends where fragment 3 independently shows the real document ends.
    body = frag2[:six_idx] + norm(tail2)
    repaired = "\n".join(body) + "\n"

    print(f"\n  repaired      : {len(body):5d} lines "
          f"({len(text.split(chr(10)))} -> {len(body)} lines, "
          f"{len(text)} -> {len(repaired)} bytes)")

    if not args.write:
        print("\nCHECK ONLY -- nothing written. Pass --write to apply.")
        return 0

    TARGET.write_text(repaired, encoding="utf-8")
    print("\nWROTE the repaired file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
