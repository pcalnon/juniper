#!/usr/bin/env python3
"""Markdown STRUCTURE damage a line-level diff check cannot see.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc verification tooling (docs consolidation)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- verification (run after every docs consolidation)
Retire when: the consolidator runs this itself, or docs stop being merged N-way.
Related:     util/ad-hoc/2026-09-05_fleet_docs_consolidate.py (--verify checks
             LINES; this checks STRUCTURE),
             util/ad-hoc/2026-09-05_verify_consolidation_carried.py.

WHY -- THREE REAL DEFECTS, NONE OF THEM A MISSING LINE

Consolidating flood-2 docs PRs on 2026-09-05 produced, across two batches:

  1. a ```bash PAIR removed (batch 1, #1628; twice) -- 17 lines of shell left as
     bare prose;
  2. an UNCLOSED ```text fence (batch 2, #1639) -- flips fence parity for the
     REST OF THE FILE, so the unfenced-command count went 6 -> 78;
  3. a `### Operator pitfalls` heading AND its table header removed, orphaning
     seven table rows -- a table with no header does not render as a table.

The consolidator's own `--verify` passed all three: every one is present as
LINES and absent only as STRUCTURE. Nor does markdownlint catch (1) or (3).

WHY FENCE BALANCE IS NOT ENOUGH -- both halves of the lesson

  removing a matched PAIR   -> count stays EVEN, balance check passes  (batch 1)
  removing ONE fence        -> count goes ODD, but says nothing about where (batch 2)

So parity is necessary and not sufficient. The load-bearing check is C2:
command-looking lines OUTSIDE any fence, COMPARED TO THE BASE -- because the base
may legitimately have some (juniper-ml's REFERENCE.md carries 6 in a
pre-existing `memory_index_check` block), an absolute threshold would either
fail always or never.

CHECKS

  C1  fence parity is even
  C2  no NEW command-looking line outside a fence, vs the base
  C3  no NEW table row whose table has no header row above it
  C4  heading count did not DROP (the swallowed-heading signature of #1749)

Usage
-----
    python3 util/ad-hoc/2026-09-05_md_structure_check.py --base origin/main \
        docs/REFERENCE.md docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys

FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
CODEY = re.compile(
    r"^(python3?|bash|gh|pip|cd|export|make|sudo|npm|curl|"
    r"LD_LIBRARY_PATH=|LIBTORCH=|JUNIPER_|CASCOR_)\b"
)
ROW = re.compile(r"^\s*\|.*\|\s*$")
SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
HEADING = re.compile(r"^#{1,6}\s")


def base_text(base: str, path: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{base}:{path}"],
                          capture_output=True, text=True, check=False)
    return proc.stdout if proc.returncode == 0 else None


def analyse(text: str) -> dict:
    """Structure of the OUT-OF-FENCE prose.

    The table rule needs LOOKAHEAD, not lookbehind. A header row is legitimately
    the first row of its block, so "first row of a block" is not the defect --
    an earlier version of this check used exactly that and flagged every
    well-formed table in the file. What makes a table orphaned is that its block
    has no `|---|---|` SEPARATOR as its second line. So: group contiguous rows
    into blocks and judge the block.
    """
    lines = text.splitlines()
    inside = False
    unfenced, headless_rows, headings, fences = [], [], 0, 0
    i = 0
    while i < len(lines):
        ln = lines[i]
        if FENCE.match(ln):
            fences += 1
            inside = not inside
            i += 1
            continue
        if inside:
            i += 1
            continue
        if HEADING.match(ln):
            headings += 1
        if CODEY.match(ln):
            unfenced.append(" ".join(ln.split()))
        if ROW.match(ln):
            block_start = i
            while i < len(lines) and ROW.match(lines[i]):
                i += 1
            block = lines[block_start:i]
            has_sep = len(block) >= 2 and SEP.match(block[1])
            if not has_sep:
                headless_rows.append(" ".join(block[0].split()))
            continue
        i += 1
    return {
        "fences": fences,
        "unfenced": unfenced,
        "headless_rows": headless_rows,
        "headings": headings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    rc = 0
    for path in args.paths:
        bt = base_text(args.base, path)
        try:
            ht = open(path).read()
        except OSError as exc:
            print(f"[SKIP] {path}: {exc}")
            continue
        if bt is None:
            print(f"[NEW ] {path}: not on {args.base}; structure checks need a base")
            continue

        b, h = analyse(bt), analyse(ht)
        fails = []

        if h["fences"] % 2:
            fails.append(f"C1 fence parity ODD ({h['fences']}) — an unclosed fence "
                         f"unfences the rest of the file")

        new_unfenced = [x for x in h["unfenced"] if x not in b["unfenced"]]
        if new_unfenced:
            fails.append(f"C2 {len(new_unfenced)} NEW command line(s) outside a fence "
                         f"(base has {len(b['unfenced'])})")
            for x in new_unfenced[:5]:
                fails.append(f"      {x[:110]}")

        new_headless = [x for x in h["headless_rows"] if x not in b["headless_rows"]]
        if new_headless:
            fails.append(f"C3 {len(new_headless)} NEW table row(s) with no header above")
            for x in new_headless[:5]:
                fails.append(f"      {x[:110]}")

        if h["headings"] < b["headings"]:
            fails.append(f"C4 heading count DROPPED {b['headings']} -> {h['headings']} "
                         f"(the #1749 swallowed-heading signature)")

        if fails:
            rc = 1
            print(f"[FAIL] {path}")
            for f in fails:
                print(f"   {f}")
        else:
            print(f"[ OK ] {path}  fences={h['fences']} headings={h['headings']} "
                  f"unfenced={len(h['unfenced'])} (base {len(b['unfenced'])})")

    print()
    print("FAIL: markdown structure regressed." if rc else
          "OK: no structural regression against the base.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
