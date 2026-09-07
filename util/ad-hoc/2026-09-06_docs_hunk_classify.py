#!/usr/bin/env python3
"""
Classify every markdown hunk a fleet docs PR adds, so the batchable ones can be told apart.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 35 juniper-ml docs PRs; `2026-09-06_docs_pr_cluster_map.py`

Thirty-five PRs all edit the same four documents from seventeen different bases. A whole-line
union over that configuration is what produced 49 headerless table fragments: two halves of one
row arriving as two broken rows, because the union's unit (a line) is finer than the thing's
identity (a row).

The way out is to stop unioning and start classifying. Almost every hunk in this fleet is one of
three shapes, and only the third needs a human read:

  SECTION   the hunk is a self-contained new `##`/`###` block -- appendable anywhere its
            heading level allows, because nothing around it moved
  ROW       one or more `|`-delimited rows added to a table that already exists -- insertable
            IF the current file still has a table with the same header
  PROSE     an edit inside existing running text, or a hunk that mixes shapes -- the only kind
            whose correctness depends on what the surrounding text says NOW

The counts this prints decide the plan. They are not a disposition.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from collections import Counter
from pathlib import Path

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
HEADING = re.compile(r"^#{1,6} \S")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=300, check=False).stdout


def classify(added: list[str], removed: list[str]) -> str:
    """SECTION / ROW / PROSE for one hunk's added lines."""
    if removed:
        return "PROSE"  # a replacement is never a pure addition, whatever it looks like
    body = [ln for ln in added if ln.strip()]
    if not body:
        return "BLANK"
    if HEADING.match(body[0]):
        return "SECTION"
    if all(TABLE_ROW.match(ln) for ln in body):
        return "ROW"
    return "PROSE"


def hunks(diff: str):
    """Yield `(path, added_lines, removed_lines)` per hunk."""
    path = ""
    added: list[str] = []
    removed: list[str] = []
    started = False
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if HUNK.match(line):
            if started:
                yield path, added, removed
            added, removed, started = [], [], True
            continue
        if not started:
            continue
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            removed.append(line[1:])
    if started:
        yield path, added, removed


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    repo = Path(args[0]).resolve()
    prs = [int(a) for a in args[1:]]

    grand: Counter[str] = Counter()
    prose_sites: list[str] = []
    for pr in prs:
        ref = f"refs/superseded/pr{pr}"
        git(repo, "fetch", "origin", f"pull/{pr}/head:{ref}", "--force")
        base = git(repo, "merge-base", "origin/main", ref).strip()
        if not base:
            continue
        diff = git(repo, "diff", "-U0", f"{base}..{ref}", "--", "*.md")
        counts: Counter[str] = Counter()
        for path, added, removed in hunks(diff):
            kind = classify(added, removed)
            counts[kind] += 1
            grand[kind] += 1
            if kind == "PROSE":
                prose_sites.append(f"#{pr} {path}: +{len(added)}/-{len(removed)}")
        print(f"#{pr}: " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    print()
    print("TOTAL: " + "  ".join(f"{k}={v}" for k, v in sorted(grand.items())))
    print()
    print(f"{len(prose_sites)} hunk(s) need reading against the CURRENT text:")
    for site in prose_sites:
        print(f"    {site}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
