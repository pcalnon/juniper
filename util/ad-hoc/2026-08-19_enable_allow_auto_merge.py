#!/usr/bin/env python3
"""Enable `allow_auto_merge` on the Juniper repos that lack it.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License

Why this is a SAFETY fix, not a convenience one
-----------------------------------------------
With `allow_auto_merge: false`, `gh pr merge --auto` does **not** arm auto-merge -- it
silently falls back to an **immediate merge**. On these repos the owner also holds an
`always` ruleset bypass, so that fallback can merge a PR whose required checks never
finished. That is precisely the failure `util/safe_merge.py` exists to prevent
(ml#932 merged 66 s after its sync on a head with zero CI check-runs; ml#924 merged 25 s
after its update-branch head).

Measured 2026-08-19: `allow_auto_merge` was `true` on **juniper-ml only** and `false` on the
other eight. So the fleet-wide behaviour of `--auto` was the dangerous one everywhere except
the repo where it had been exercised.

Enabling it makes `--auto` *arm and wait* -- server-side, and therefore unaffected by a
session ending or a script being killed. That is what unblocks the outstanding
kill-resilience gap in `safe_merge` (RC-4 of ml#1176): a merge can be handed to GitHub
instead of depending on a local process surviving.

What it does NOT do
-------------------
It does not arm auto-merge on any PR, change any ruleset, weaken any required check, or
merge anything. It only makes the repository *capable* of queuing an auto-merge, which is a
prerequisite for `--auto` behaving as its name implies.

Usage
-----
    python3 util/ad-hoc/2026-08-19_enable_allow_auto_merge.py             # dry-run
    python3 util/ad-hoc/2026-08-19_enable_allow_auto_merge.py --execute
    python3 util/ad-hoc/2026-08-19_enable_allow_auto_merge.py --status
    python3 util/ad-hoc/2026-08-19_enable_allow_auto_merge.py --disable --execute  # revert

Exit codes: 0 all requested repos OK / 1 at least one failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

OWNER = "pcalnon"
REPOS = [
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
]


class Failed(RuntimeError):
    pass


def gh(args: list[str]) -> str:
    proc = subprocess.run(  # nosec B603 B607
        ["gh", *args], capture_output=True, text=True, timeout=120, check=False
    )
    if proc.returncode != 0:
        raise Failed(f"gh {' '.join(args[:3])}… failed: {proc.stderr.strip()[:250]}")
    return proc.stdout


def current(repo: str) -> bool:
    return json.loads(gh(["api", f"/repos/{OWNER}/{repo}", "--jq", ".allow_auto_merge"]))


def apply(repo: str, want: bool, execute: bool) -> str:
    now = current(repo)
    if now == want:
        return f"SKIP     {repo}: already {want}"
    if not execute:
        return f"DRY      {repo}: would set allow_auto_merge {now} -> {want}"
    gh(["api", "-X", "PATCH", f"/repos/{OWNER}/{repo}", "-F", f"allow_auto_merge={str(want).lower()}"])
    got = current(repo)
    if got != want:
        raise Failed(f"{repo}: set to {want} but reads back {got}")
    return f"OK       {repo}: allow_auto_merge {now} -> {got}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", help="operate on one repo instead of all 9")
    ap.add_argument("--execute", action="store_true", help="actually write (default: dry-run)")
    ap.add_argument("--status", action="store_true", help="report current state and exit")
    ap.add_argument("--disable", action="store_true", help="REVERT: set allow_auto_merge false")
    args = ap.parse_args()

    targets = [args.repo] if args.repo else REPOS
    if args.repo and args.repo not in REPOS:
        print(f"unknown repo: {args.repo}", file=sys.stderr)
        return 1
    if not (args.status or args.execute):
        print("*** DRY RUN — nothing will be written (pass --execute) ***\n")

    failed = False
    for repo in targets:
        try:
            if args.status:
                print(f"{repo:<24} allow_auto_merge={current(repo)}")
            else:
                print(apply(repo, not args.disable, args.execute))
        except (Failed, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            failed = True
            print(f"FAIL     {repo}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
