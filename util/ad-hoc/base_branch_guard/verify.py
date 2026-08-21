#!/usr/bin/env python3
"""Verify the base-branch guard actually reports on each rollout PR (ml#434 part 1).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc migration tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- migration
Retire when: the rollout is merged and verified on all 9 repos.
Related:     ml#434; util/ad-hoc/base_branch_guard/rollout.py

Why this does not read the rollup
---------------------------------
A `neutral` check run counts as SUCCESS in the aggregate rollup. juniper-cascor#515 sat
permanently unmergeable with a GREEN rollup because the only check runs on its head were five
`Cursor Automation: *` runs at `neutral` and ZERO GitHub Actions runs -- every required
context stuck at "expected", nothing red. The same five neutral Cursor runs are present on
these rollout PRs.

So this counts the SPECIFIC named check run and reports its own conclusion, and separately
reports how many required contexts have actually reported. A rollup is not evidence.

Usage
-----
    python3 util/ad-hoc/base_branch_guard/verify.py
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys

CONTEXT = "Guard PR base branch"

PRS = {
    "juniper-deploy": 188,
    "juniper-ml": 1208,
    "juniper-cascor": 543,
    "juniper-canopy": 500,
    "juniper-data": 274,
    "juniper-data-client": 155,
    "juniper-cascor-client": 120,
    "juniper-cascor-worker": 156,
    # recurrence is the guard's ORIGIN, not a new install -- this PR carries the
    # label-hatch / fail-open / message fixes back to it. It is the repo where the
    # defect mattered most, because the context is already REQUIRED there.
    "juniper-recurrence": 119,
}


def gh_json(path: str):
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", "api", path], capture_output=True, text=True, timeout=120
    )
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout or "null")
    except json.JSONDecodeError:
        return None


def main() -> int:
    print(f"{'repo':<24} {'PR':>5} {'guard':<12} {'base':<8} {'other checks':<14} state")
    print("-" * 86)
    bad = []
    for repo, num in PRS.items():
        pr = gh_json(f"repos/pcalnon/{repo}/pulls/{num}")
        if not pr:
            print(f"{repo:<24} {num:>5}  (could not read PR)")
            bad.append(repo)
            continue
        sha = (pr.get("head") or {}).get("sha", "")
        base = (pr.get("base") or {}).get("ref", "?")
        runs = gh_json(f"repos/pcalnon/{repo}/commits/{sha}/check-runs?per_page=100") or {}
        crs = runs.get("check_runs", [])
        mine = [c for c in crs if c.get("name") == CONTEXT]
        if not mine:
            verdict = "ABSENT"
            bad.append(repo)
        else:
            # Duplicates are EXPECTED and usually benign: every trigger type produces its
            # own run, and all of them stay attached to the head. Opening a PR and then
            # editing its body yields two (`opened` + `edited`). Measured 2026-08-20 on
            # juniper-recurrence#120: GitHub counts the LATEST run -- a stale `failure`
            # alongside a newer `success` is reported by `gh pr checks` as **pass**.
            # So judge the newest, and only report the count as context.
            latest = sorted(mine, key=lambda c: c.get("started_at") or "")[-1]
            verdict = latest.get("conclusion") or latest.get("status") or "?"
            if len(mine) > 1:
                verdict = f"{verdict} (x{len(mine)})"
            if (latest.get("conclusion") or latest.get("status")) not in (
                "success",
                "queued",
                "in_progress",
            ):
                bad.append(repo)
        # count non-neutral, actually-reporting runs so a wall of `neutral` cannot
        # masquerade as coverage
        real = [c for c in crs if c.get("conclusion") not in (None, "neutral")]
        print(
            f"{repo:<24} {num:>5} {verdict:<12} {base:<8} "
            f"{f'{len(real)}/{len(crs)} real':<14} {pr.get('mergeable_state', '?')}"
        )

    print()
    if bad:
        print(f"NEEDS ATTENTION ({len(bad)}): {', '.join(sorted(set(bad)))}")
        print("  ABSENT = the guard produced no check run at all -- requiring the context")
        print("           on this repo would block every PR. Do NOT proceed to part 2.")
        print("  (xN)   = N runs of that name exist; only the NEWEST is judged, which is")
        print("           what GitHub counts. Not a problem on its own.")
        return 1
    print("Every rollout PR publishes 'Guard PR base branch', newest run passing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
