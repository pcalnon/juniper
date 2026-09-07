#!/usr/bin/env python3
"""2026-09-05_markdown_structure_check.py -- catch the markdown damage a line check cannot see.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc analysis (documentation structural integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

Consolidating ten fleet docs PRs into juniper-ml#1746 dropped a single closing ``` fence
in `docs/REFERENCE.md`, and that one line swallowed **36 H2 headings** into a code block
on `main`. Three separate checks all passed on the way in:

  * the consolidator's own line-presence verifier -- blind by construction, because it
    asks "is this added line present in the result?" via a SUBSTRING test, and ``` occurs
    hundreds of times in the file. A lost fence is never "missing";
  * `juniper-docs-additions-check` -- it looks for DELETED content, and a lost fence is a
    deletion of three characters that its magnitude heuristic ignores;
  * `markdownlint` -- juniper-ml's config does not enable the link-fragment rule that
    would have flagged the now-unreachable anchors (juniper-canopy's does, which is how
    the same defect surfaced there).

The damage is invisible until someone follows a `#anchor` that no longer resolves, or a
tool like `util/soak_ledger.py verify-probes` fails on a pointer.

WHAT IT CHECKS

  * fence balance per file, naming the opening line of any unclosed fence;
  * H2 headings that sit INSIDE a fenced block (the actual symptom -- a file can have an
    even fence count and still swallow headings if two closes were lost);
  * markdown tables whose header row lost its `| --- | --- |` separator, which renders the
    table as plain text and is likewise invisible to a substring check.

Exit 1 if anything is found, so it can be wired as a gate.

Usage:
    python util/ad-hoc/2026-09-05_markdown_structure_check.py docs/*.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


MARKDOWN_INFO_STRINGS = {"markdown", "md"}


def _is_markdown_example(opener_line: str) -> bool:
    """Does this fence declare that its CONTENT is markdown?

    ```markdown / ```md hold sample documents, so H2s inside them are the point, not a
    symptom. Anything else -- ```bash, ```python, or a bare ``` -- has no business
    containing an H2, and that is the shape a dropped closing fence produces.
    """
    return opener_line.strip().lstrip("`").strip().lower() in MARKDOWN_INFO_STRINGS


def check(path: Path) -> list:
    problems: list = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    # (1) fence balance, and (2) headings swallowed by a fence -- checked in one walk.
    #
    # A fence whose info string says it CONTAINS markdown is exempt from the heading
    # check: ```markdown blocks legitimately hold H2s, because they are showing the
    # reader what a document should look like. juniper-canopy's AGENTS.md carries one
    # (a sample `notes/history/INDEX.md`) with four such headings, and flagging it made
    # this checker unwireable as a gate -- four permanent false findings on a clean
    # tree. Every other info string, and a BARE fence, is still checked: the fence that
    # swallowed 36 headings in juniper-ml#1746 was not a markdown example.
    in_fence = False
    opener = None
    for i, line in enumerate(lines, 1):
        if line.startswith("```"):
            if not in_fence:
                in_fence, opener = True, (i, line)
            else:
                in_fence, opener = False, None
            continue
        if in_fence and line.startswith("## ") and not _is_markdown_example(opener[1]):
            problems.append(
                f"H2 swallowed by the fence opened at line {opener[0]} "
                f"({opener[1].strip()[:20]!r}): line {i}: {line.strip()[:60]}"
            )
    if in_fence:
        problems.append(f"UNCLOSED code fence opened at line {opener[0]}: {opener[1][:60]!r}")

    # (3) table header with no separator row.
    in_fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # A four-space indent is an INDENTED CODE BLOCK -- CommonMark reads it as literally as a
        # fence, so a quoted `| ... |` row inside one is not a table. Found by writing this
        # tool's own findings to a notes document, where the quoted rows are indented precisely
        # because a fence would be closed by a residue line that contains one.
        if line[:4] == "    ":
            continue
        stripped = line.strip()
        if stripped.startswith("|") and line.count("|") >= 2:
            prev = lines[i - 1] if i else ""
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not prev.strip().startswith("|") and nxt.strip().startswith("|") and not SEPARATOR.match(nxt):
                problems.append(f"table at line {i+1} has no separator row: {stripped[:60]}")
    return problems


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    total = 0
    for arg in argv:
        p = Path(arg)
        if not p.is_file() or p.suffix.lower() != ".md":
            continue
        found = check(p)
        if found:
            total += len(found)
            print(f"=== {arg} ===")
            for f in found:
                print(f"   {f}")
    print(f"\nstructural problems: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
