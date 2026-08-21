#!/usr/bin/env python3
"""Merge the base-branch-guard rollout PRs via util/safe_merge.py (ml#434 part 1).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc migration tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- migration (one-off)
Retire when: the rollout is merged on all 9 repos.
Related:     ml#434; util/safe_merge.py

Sequential, not parallel, and deliberately so: `safe_merge` refuses a BEHIND PR by syncing
and re-waiting, and concurrent merges into the same repo re-BEHIND each other. Different
repos cannot collide, but keeping it serial makes each outcome individually readable, which
matters more here than wall-clock.

Merges only. It never opens, edits, closes, or force-pushes anything, and a refusal from
`safe_merge` is recorded and skipped rather than retried -- a refusal is a stated reason,
not a transient error.

Usage
-----
    python3 util/ad-hoc/base_branch_guard/merge_all.py --dry-run
    python3 util/ad-hoc/base_branch_guard/merge_all.py
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 - drives the in-repo merge gate
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SAFE_MERGE = REPO_ROOT / "util" / "safe_merge.py"

PRS = [
    ("juniper-deploy", 188),
    ("juniper-cascor", 543),
    ("juniper-canopy", 500),
    ("juniper-data", 274),
    ("juniper-data-client", 155),
    ("juniper-cascor-client", 120),
    ("juniper-cascor-worker", 156),
    ("juniper-recurrence", 119),
    ("juniper-ml", 1208),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repo", action="append", default=None)
    args = ap.parse_args()
    todo = [(r, n) for r, n in PRS if not args.repo or r in args.repo]

    results = []
    for repo, num in todo:
        cmd = [sys.executable, "-u", str(SAFE_MERGE), "--pr", str(num), "--repo", repo]
        if not args.dry_run:
            cmd.append("--execute")
        print("=" * 76)
        print(f"{repo}#{num}")
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # nosec B603
        for line in ((p.stdout or "") + (p.stderr or "")).splitlines():
            print(f"  {line}")
        results.append((repo, num, p.returncode))

    print()
    print("=" * 76)
    merged = [f"{r}#{n}" for r, n, c in results if c == 0]
    refused = [f"{r}#{n}" for r, n, c in results if c == 1]
    other = [f"{r}#{n}:{c}" for r, n, c in results if c not in (0, 1)]
    print(f"merged   : {len(merged)}  {', '.join(merged)}")
    if refused:
        print(f"REFUSED  : {len(refused)}  {', '.join(refused)}")
    if other:
        print(f"OTHER    : {len(other)}  {', '.join(other)}")
    return 0 if not refused and not other else 1


if __name__ == "__main__":
    sys.exit(main())
