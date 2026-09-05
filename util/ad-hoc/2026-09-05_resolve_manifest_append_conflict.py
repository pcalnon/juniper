#!/usr/bin/env python3
"""Resolve the stale-branch APPEND conflict in a manifest-style doc block.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc automation (Cursor-fleet flood consolidation)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- automation (consolidation of the P5 test-suite PR cohort)
Retire when: the fleet stops producing one-line-append PRs against the same
             manifest blocks, or a merge driver handles this natively.
Related:     util/ad-hoc/2026-09-05_fleet_docs_consolidate.py (docs-version churn,
             a DIFFERENT conflict class -- that resolver is header-line-scoped
             and correctly refuses this one).

THE CONFLICT CLASS

`docs/REFERENCE.md` and `AGENTS.md` carry manifest blocks -- one line per test
suite, per utility, per workflow. A fleet PR adds ONE line. While it sits open,
`main` EDITS a neighbouring line in the same block. Git then reports the whole
neighbourhood as conflicted, with:

  HEAD side : main's edited line  (newer, authoritative)
  branch    : the SAME line at its pre-edit text, PLUS the genuinely new row

Resolving "take theirs" silently reverts main's edit. Resolving "take ours"
silently drops the PR's new row -- the 2026-07-26 damage class. The correct
resolution is a UNION in which main wins any line the two sides share.

THE KEY, AND WHY IT IS THE FILENAME

Two lines are "the same row" when they describe the same artifact, even after
main rewrote the prose. The stable identity in these blocks is the leading
code-span / filename token (`test_foo.py`, `util/bar.py`). So: keep every HEAD
line; append only those branch lines whose key is absent from the HEAD side.

FAIL-CLOSED

A conflict hunk in which ANY branch-side line has no extractable key aborts the
run with the hunk printed. Guessing there is how a section gets dropped.
Run with --dry-run first; it prints every decision.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

START = re.compile(r"^<{7} ")
MID = re.compile(r"^={7}$")
END = re.compile(r"^>{7} ")

# The row's stable identity: the first `code span`, or the first bare token that
# looks like a filename. Tried in that order.
KEY_CODE = re.compile(r"`([^`]+)`")
KEY_FILE = re.compile(r"([A-Za-z0-9_./-]+\.(?:py|md|ya?ml|bash|sh|toml|json))")


def key_of(line: str) -> str | None:
    m = KEY_CODE.search(line)
    if m:
        return m.group(1).strip()
    m = KEY_FILE.search(line)
    if m:
        return m.group(1).strip()
    return None


def resolve(path: Path, dry_run: bool) -> int:
    lines = path.read_text().splitlines(keepends=True)
    out: list[str] = []
    i = 0
    hunks = 0

    while i < len(lines):
        if not START.match(lines[i]):
            out.append(lines[i])
            i += 1
            continue

        hunks += 1
        i += 1
        ours: list[str] = []
        while i < len(lines) and not MID.match(lines[i].rstrip("\n")):
            ours.append(lines[i])
            i += 1
        if i >= len(lines):
            print(f"FATAL: unterminated conflict in {path} (no ======= )", file=sys.stderr)
            return 1
        i += 1
        theirs: list[str] = []
        while i < len(lines) and not END.match(lines[i]):
            theirs.append(lines[i])
            i += 1
        if i >= len(lines):
            print(f"FATAL: unterminated conflict in {path} (no >>>>>>> )", file=sys.stderr)
            return 1
        i += 1

        ours_keys = {k for k in (key_of(x) for x in ours) if k}
        added: list[str] = []
        # A branch-side row is not always ONE line. In `.github/workflows/ci.yml` each
        # suite is a comment block followed by its `python3 -m unittest` line, and the
        # comment lines carry no key of their own. So buffer keyless lines and attach
        # them to the next KEYED line, deciding on that line's key. Keyless lines with
        # no keyed line after them are still fatal -- that is the fail-closed property,
        # narrowed to the case where it is actually earning something.
        pending: list[str] = []
        for t in theirs:
            k = key_of(t) if t.strip() else None
            if k is None:
                pending.append(t)
                continue
            if k not in ours_keys:
                added.extend(pending)
                added.append(t)
            pending = []
        if any(p.strip() for p in pending):
            print(f"FATAL: branch-side line(s) with no extractable key, and no keyed "
                  f"line following, in {path}:", file=sys.stderr)
            for p in pending:
                if p.strip():
                    print(f"  {p.rstrip()}", file=sys.stderr)
            print("  refusing to guess -- resolve this hunk by hand.", file=sys.stderr)
            return 1

        print(f"  hunk {hunks}: kept {len(ours)} HEAD line(s), "
              f"added {len(added)} new row(s) from the branch"
              f"{''.join(chr(10) + '    + ' + a.strip()[:100] for a in added)}")

        out.extend(ours)
        out.extend(added)

    if hunks == 0:
        print(f"  {path}: no conflict markers")
        return 0
    if dry_run:
        print(f"  DRY RUN — {path} not written ({hunks} hunk(s) would be resolved)")
        return 0
    path.write_text("".join(out))
    print(f"  WROTE {path} ({hunks} hunk(s) resolved)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rc = 0
    for p in args.paths:
        print(f"=== {p} ===")
        rc |= resolve(p, args.dry_run)
    return rc


if __name__ == "__main__":
    sys.exit(main())
