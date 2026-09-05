#!/usr/bin/env python3
"""2026-09-05_fleet_docs_reinsert.py -- re-insert lines a consolidation dropped, in place.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY

`2026-09-05_fleet_docs_consolidate.py --defer-prose` keeps OURS on a two-sided prose
conflict so the batch can proceed, and its verification then reports every line that
choice dropped. Those lines are real content, so they must go back -- but they must go
back in the RIGHT PLACE, which "append to the end of the file" is not.

This script re-inserts each missing line by anchoring on the line that PRECEDED it on the
source branch. That anchor is what makes the placement correct rather than merely present:
a line-presence check (the consolidator's) cannot tell a section-body line appended to the
wrong section from one restored to its own, and a section landing under the wrong heading
is the same damage class as losing it.

Fail-closed: an anchor that is absent, or that appears more than once, is REPORTED and
skipped, never guessed at. Re-run the consolidator's `--verify` afterwards; anything this
script skipped stays in the MISSING list rather than silently disappearing from it.

Usage:
    python util/ad-hoc/2026-09-05_fleet_docs_reinsert.py \\
        --worktree /path/to/consolidation --base origin/main \\
        --pr 1711=cursor/engineering-documentation-updates-f636 [...] [--apply]
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
from pathlib import Path

NEUTRAL_LINE_RE = re.compile(
    r"^\s*(?:\*\*Version:?\*\*|\*\*Last Updated:?\*\*|\*\*Date:?\*\*|_Version:|_Last Updated:)",
    re.IGNORECASE,
)
WAIVED_LINE_RE = re.compile(
    r"^\|\s*\*\*(?:REFERENCE\.md|DEVELOPER_CHEATSHEET_JUNIPER-ML\.md)\*\*\s*\|\s*(?:Reference|Cheatsheet)\s*\|"
)


def git(wt: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(wt), *args], capture_output=True, text=True)  # nosec B603


def branch_file(wt: Path, ref: str, rel: str) -> list:
    cp = git(wt, "show", f"{ref}:{rel}")
    return cp.stdout.splitlines(keepends=True) if cp.returncode == 0 else []


def missing_for(wt: Path, base: str, branch: str) -> dict:
    """{file: [(line, preceding_anchor)]} for lines the branch added that are absent now."""
    mb = git(wt, "merge-base", base, branch).stdout.strip()
    cp = git(wt, "diff", "--unified=0", f"{mb}..{branch}", "--", "*.md")
    added: dict = {}
    current = None
    for ln in cp.stdout.splitlines():
        if ln.startswith("+++ b/"):
            current = ln[6:]
        elif ln.startswith("+") and not ln.startswith("+++") and current:
            added.setdefault(current, []).append(ln[1:])

    out: dict = {}
    for rel, lines in added.items():
        target = wt / rel
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        src = branch_file(wt, branch, rel)
        src_stripped = [s.rstrip("\n") for s in src]
        for ln in lines:
            if not ln.strip() or NEUTRAL_LINE_RE.match(ln) or WAIVED_LINE_RE.match(ln):
                continue
            if ln.strip() in text:
                continue
            anchor = None
            if ln in src_stripped:
                idx = src_stripped.index(ln)
                for j in range(idx - 1, -1, -1):
                    cand = src_stripped[j]
                    if cand.strip() and cand.strip() in text:
                        anchor = cand
                        break
            out.setdefault(rel, []).append((ln, anchor))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--pr", action="append", required=True, metavar="N=branch")
    ap.add_argument("--apply", action="store_true", help="write the insertions (default: report only)")
    args = ap.parse_args(argv)

    wt = Path(args.worktree).resolve()
    inserted = skipped = 0
    for spec in args.pr:
        num, _, br = spec.partition("=")
        branch = br if br.startswith("origin/") else f"origin/{br}"
        for rel, items in missing_for(wt, args.base, branch).items():
            target = wt / rel
            for ln, anchor in items:
                if anchor is None:
                    print(f"  SKIP #{num} {rel}: no usable anchor for: {ln.strip()[:90]}")
                    skipped += 1
                    continue
                lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                hits = [i for i, s in enumerate(lines) if s.rstrip("\n") == anchor]
                if len(hits) != 1:
                    print(f"  SKIP #{num} {rel}: anchor appears {len(hits)}x (need exactly 1): {anchor.strip()[:70]}")
                    skipped += 1
                    continue
                print(f"  {'INSERT' if args.apply else 'WOULD INSERT'} #{num} {rel} after line {hits[0]+1}: {ln.strip()[:80]}")
                if args.apply:
                    lines.insert(hits[0] + 1, ln + "\n")
                    target.write_text("".join(lines), encoding="utf-8")
                inserted += 1
    print(f"\n{'inserted' if args.apply else 'would insert'}: {inserted}; skipped (no unique anchor): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
