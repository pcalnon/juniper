#!/usr/bin/env python3
"""Watch the armed bot-PR sweep to completion and report each PR's terminal state.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-24
Status:      RETIRED 2026-08-25 -- purpose complete, and superseded.
Retired because: its WATCH list was hard-coded to the 17 PRs of one sweep, and
    2026-08-24_bot_pr_census.py answers the same question dynamically for any sweep.

What it produced (2026-08-24): reported 7 of the 17 armed PRs merged and 10 stuck at
    armed+BEHIND. That split is what exposed the real finding -- every repo pairs
    strict_required_status_checks_policy=true with allow_update_branch=false, so GitHub's
    auto-merge cannot clear BEHIND and an armed PR waits forever. The 7 that merged were
    simply the ones already CLEAN at arming.

    Worth keeping in mind wherever this pattern recurs: this script deliberately reported
    "still OPEN" as a distinct outcome rather than folding it into success. An armed
    auto-merge that never fires looks exactly like one that has not fired YET, and only an
    explicit terminal-state check tells them apart.

Read-only: polls state, never merges, arms, closes or pushes.

Exits when every watched PR has left OPEN, or on --deadline. Reports MERGED vs CLOSED vs
still-OPEN explicitly -- an armed auto-merge that never fires (e.g. a sibling merge turned
it BEHIND and its re-test went red) must be visible as "still open", not silently counted
as success.

Usage: python3 util/ad-hoc/2026-08-24_bot_pr_sweep_watch.py [--deadline-min 45] [--interval 60]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time

# The 17 PRs armed/merged by 2026-08-24_bot_pr_merge_sweep.py --execute.
WATCH = [
    ("juniper-ml", 1324), ("juniper-ml", 1325),
    ("juniper-cascor", 576), ("juniper-cascor", 577), ("juniper-cascor", 581),
    ("juniper-canopy", 505), ("juniper-canopy", 506), ("juniper-canopy", 510),
    ("juniper-data", 285),
    ("juniper-data-client", 163),
    ("juniper-cascor-client", 127), ("juniper-cascor-client", 128),
    ("juniper-cascor-worker", 160), ("juniper-cascor-worker", 161),
    ("juniper-deploy", 193), ("juniper-deploy", 194),
    ("juniper-recurrence", 126),
]


def state_of(repo: str, num: int) -> dict:
    p = subprocess.run(
        ["gh", "pr", "view", str(num), "--repo", f"pcalnon/{repo}",
         "--json", "state,mergeStateStatus,autoMergeRequest"],
        capture_output=True, text=True)
    if p.returncode != 0:
        return {"state": "?", "err": (p.stderr or "").strip()[:80]}
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"state": "?", "err": "unparseable"}
    return {"state": d.get("state"), "mergeState": d.get("mergeStateStatus"),
            "armed": d.get("autoMergeRequest") is not None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deadline-min", type=int, default=45)
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()

    deadline = time.monotonic() + args.deadline_min * 60
    seen: dict[tuple[str, int], str] = {}

    while True:
        pending = []
        for repo, num in WATCH:
            if seen.get((repo, num)) in ("MERGED", "CLOSED"):
                continue
            st = state_of(repo, num)
            s = st.get("state") or "?"
            if s in ("MERGED", "CLOSED"):
                seen[(repo, num)] = s
                print(f"{s:<7} {repo}#{num}", flush=True)
            else:
                pending.append((repo, num, st))
        if not pending:
            break
        if time.monotonic() > deadline:
            print(f"\nDEADLINE reached with {len(pending)} still open:", flush=True)
            for repo, num, st in pending:
                print(f"   OPEN {repo}#{num} mergeState={st.get('mergeState')} armed={st.get('armed')}", flush=True)
            return 1
        time.sleep(args.interval)

    merged = sum(1 for v in seen.values() if v == "MERGED")
    closed = sum(1 for v in seen.values() if v == "CLOSED")
    print(f"\nALL RESOLVED: merged={merged} closed={closed} of {len(WATCH)}", flush=True)
    return 0 if closed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
