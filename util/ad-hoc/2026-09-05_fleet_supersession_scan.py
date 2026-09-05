#!/usr/bin/env python3
"""Is a stale fleet PR still ADDING anything, or has main already said it?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (Cursor-fleet flood disposition)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- analysis
Retire when: the fleet stops re-applying work against a moved base.

WHY

`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`
§6 chose "harvested, not merged" for part of the flood, on the grounds that the
bot branches are stale re-applications "whose risk is in what they TAKE AWAY".
That is a claim about a specific PR set, and it needs measuring per PR rather
than assuming -- some stale branches still carry genuinely new content.

Measured on ml#1630: every substantive line it adds is already on `main`, and
main's version is STRICTLY BETTER -- it additionally records that the
`allow-symbol-loss` label is WARN-only and that only a commit trailer waives a
finding. Merging #1630 would have deleted that sentence. Consolidating it would
have carried the deletion in.

WHAT IS MEASURED

For each PR, of the substantive lines it ADDS (header churn excluded):

  present   -- already on main verbatim
  novel     -- not on main

  coverage  = present / (present + novel)

A PR at coverage ~1.0 adds nothing main lacks -> SUPERSEDED, close it.
A PR at low coverage carries real content -> consolidate or harvest it.

DELETIONS ARE REPORTED SEPARATELY AND MATTER MORE. A stale branch that removes
base lines is dangerous regardless of its coverage, because a consolidation
carries the removal in silently. `removes` counts base lines the PR deletes.

This does NOT decide anything on its own -- a high-coverage PR may still carry
one line worth keeping, which is what `novel_sample` is for.

Usage
-----
    python3 util/ad-hoc/2026-09-05_fleet_supersession_scan.py --pr 1615 --pr 1619 ...
    python3 util/ad-hoc/2026-09-05_fleet_supersession_scan.py --dump ml_files.json --cohort docs
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from pathlib import Path

NEUTRAL = re.compile(
    r"^\s*\*\*(Version|Status|Last Updated|Author|License|Project|Sub-Project|Maintainer)[:*]",
    re.IGNORECASE,
)
TRIVIAL = re.compile(r"^[\s`|<>*_#=+-]*$")


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout


def norm(s: str) -> str:
    return " ".join(s.split())


def base_corpus(base: str, paths: set[str]) -> set[str]:
    corpus = set()
    for p in sorted(paths):
        text = git("show", f"{base}:{p}")
        for ln in text.splitlines():
            if ln.strip() and not TRIVIAL.match(ln):
                corpus.add(norm(ln))
    return corpus


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--pr", type=int, action="append")
    ap.add_argument("--dump", type=Path, help="gh pr list --json output, to resolve branches")
    ap.add_argument("--novel-sample", type=int, default=2)
    args = ap.parse_args()

    if not args.pr:
        print("pass at least one --pr", file=sys.stderr)
        return 2

    print(f"{'PR':>6} {'adds':>5} {'present':>8} {'novel':>6} {'cover':>6} {'removes':>8}  disposition")
    rows = []
    for pr in args.pr:
        ref = f"refs/tmp/sup/{pr}"
        subprocess.run(["git", "fetch", "-q", "origin", f"pull/{pr}/head:{ref}", "--force"],
                       capture_output=True, check=False)
        diff = git("diff", f"{args.base}...{ref}")
        if not diff:
            print(f"{pr:>6}  (no diff / unfetchable)")
            continue

        touched = set()
        adds, removes = [], 0
        for ln in diff.splitlines():
            if ln.startswith("+++ b/"):
                touched.add(ln[6:])
            elif ln.startswith("+") and not ln.startswith("+++"):
                body = ln[1:]
                if body.strip() and not NEUTRAL.match(body) and not TRIVIAL.match(body):
                    adds.append(body)
            elif ln.startswith("-") and not ln.startswith("---"):
                body = ln[1:]
                if body.strip() and not NEUTRAL.match(body) and not TRIVIAL.match(body):
                    removes += 1

        corpus = base_corpus(args.base, touched)
        present = [a for a in adds if norm(a) in corpus]
        novel = [a for a in adds if norm(a) not in corpus]
        cover = len(present) / len(adds) if adds else 1.0

        if cover >= 0.95 and removes == 0:
            disp = "SUPERSEDED — close"
        elif cover >= 0.95:
            disp = f"SUPERSEDED but REMOVES {removes} — close, do not merge"
        elif removes > 0:
            disp = f"HARVEST — {len(novel)} novel, but REMOVES {removes}"
        else:
            disp = f"CONSOLIDATE — {len(novel)} novel, no removals"

        print(f"{pr:>6} {len(adds):>5} {len(present):>8} {len(novel):>6} {cover:>6.2f} {removes:>8}  {disp}")
        for n in novel[: args.novel_sample]:
            print(f"        novel: {n.strip()[:118]}")
        rows.append((pr, cover, removes, len(novel)))

    print()
    sup = sum(1 for _, c, r, _ in rows if c >= 0.95)
    rem = sum(1 for _, _, r, _ in rows if r > 0)
    print(f"summary: {len(rows)} scanned; {sup} superseded (>=0.95 coverage); "
          f"{rem} remove base lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
