#!/usr/bin/env python3
"""Keep armed auto-merge PRs synced until they land, one at a time.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc automation (merge-train shepherding)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- automation
Retire when: merge queues become available (they require org/enterprise ownership
             and are settled policy as UNAVAILABLE), or `allow_update_branch`
             gains a server-side auto-sync.
Related:     util/safe_merge.py (single-PR local wait + merge).

THE PARKED STATE THIS EXISTS FOR

GitHub's native auto-merge fires the instant required checks go green -- it wins
races a client poll loop cannot. But it does **not** move a BEHIND branch. Under
`strict_required_status_checks_policy: true` that produces a state which looks
exactly like progress and is actually terminal:

    checks: 20 SUCCESS, 0 pending, 0 failing
    mergeStateStatus: BEHIND
    autoMergeRequest: armed

Nothing fails. Nothing warns. The PR simply never lands. Measured 2026-09-05 on
juniper-ml: three PRs sat in this state for a full hour while `main` took eleven
merges around them.

WHY ONE AT A TIME

Syncing every PR at once is worse than syncing none: each sync starts a fresh
~7.5 min battery, and the first one to land puts all the others BEHIND again, so
N PRs re-invalidate each other indefinitely. This shepherds a SINGLE PR to
completion, then moves to the next. `main`'s observed merge gaps that day were
10-28 minutes against a 7.5 minute battery, so one PR at a time fits; N do not.

FAIL-SAFE

- Never merges. It only calls `update-branch`, which is server-side and
  GitHub-signed (`required_signatures` accepts it); the armed net does the merge.
- `expected_head_sha` is pinned on every call, so a concurrent push fails loudly
  rather than being clobbered.
- Refuses to sync a PR with a failing check -- a red PR should be fixed, not
  spun.
- Bounded by `--max-syncs` per PR, so a genuinely-too-busy `main` reports rather
  than thrashing forever.

Usage
-----
    python3 util/ad-hoc/2026-09-05_auto_merge_shepherd.py --pr 1756 --pr 1760 --pr 1763
    python3 util/ad-hoc/2026-09-05_auto_merge_shepherd.py --pr 1756 --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
import time

TERMINAL = {"MERGED", "CLOSED"}


def gh_json(*args: str) -> dict | list | None:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def pr_state(repo: str, pr: int) -> dict:
    """GraphQL view for state + checks, plus a REST read to FORCE mergeability.

    The REST call is not redundant: `mergeStateStatus` sits at UNKNOWN until
    something asks for it, and GraphQL alone never triggers the computation.
    """
    view = gh_json(
        "pr", "view", str(pr), "--repo", repo,
        "--json", "state,mergeStateStatus,autoMergeRequest,headRefOid,statusCheckRollup",
    ) or {}
    rest = gh_json("api", f"repos/{repo}/pulls/{pr}") or {}
    rollup = view.get("statusCheckRollup") or []
    concl = [c.get("conclusion") for c in rollup]

    # STATE COMES FROM REST, NOT GRAPHQL. Observed 2026-09-05 on ml#1756: the armed net
    # fired and merged the PR, and for a short window the GraphQL view still reported
    # `state: OPEN` while `autoMergeRequest` had ALREADY been cleared by the merge it
    # performed. Reading both from that view yields OPEN + not-armed, and this tool
    # reported NOT-ARMED for a PR that had just landed -- a false negative whose obvious
    # human response (re-arm it) acts on a PR that no longer exists in that state.
    # REST is authoritative and is already being called here to force mergeability.
    state = "MERGED" if rest.get("merged") else (rest.get("state") or view.get("state") or "").upper()
    return {
        "state": state,
        "merge_state": (rest.get("mergeable_state") or view.get("mergeStateStatus") or "").upper(),
        "armed": view.get("autoMergeRequest") is not None,
        "head": view.get("headRefOid") or "",
        "failing": sum(1 for c in concl if c in {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"}),
        "pending": sum(1 for c in concl if not c),
        "success": sum(1 for c in concl if c == "SUCCESS"),
    }


def sync(repo: str, pr: int, head: str, dry_run: bool) -> bool:
    if dry_run:
        print(f"    DRY RUN — would update-branch #{pr} pinned to {head[:8]}")
        return True
    proc = subprocess.run(
        ["gh", "api", "-X", "PUT", f"repos/{repo}/pulls/{pr}/update-branch",
         "-f", f"expected_head_sha={head}"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        print(f"    update-branch REFUSED: {proc.stderr.strip()[:200]}")
        return False
    print(f"    update-branch accepted (202) for #{pr} @ {head[:8]}")
    return True


def shepherd(repo: str, pr: int, max_syncs: int, poll: int, dry_run: bool) -> str:
    syncs = 0
    while True:
        s = pr_state(repo, pr)
        if s["state"] in TERMINAL:
            return s["state"]
        if not s["armed"]:
            return "NOT-ARMED"
        if s["failing"]:
            return f"FAILING({s['failing']})"

        print(f"  #{pr}: {s['merge_state']}  green={s['success']} pending={s['pending']} "
              f"syncs={syncs}/{max_syncs}")

        if s["merge_state"] == "BEHIND":
            if syncs >= max_syncs:
                return "SYNC-CAP-REACHED"
            if not sync(repo, pr, s["head"], dry_run):
                return "SYNC-REFUSED"
            syncs += 1
            if dry_run:
                return "DRY-RUN"
        time.sleep(poll)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="pcalnon/juniper-ml")
    ap.add_argument("--pr", type=int, action="append", required=True)
    ap.add_argument("--max-syncs", type=int, default=8, help="per PR, before giving up")
    ap.add_argument("--poll", type=int, default=60)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    results: dict[int, str] = {}
    for pr in args.pr:
        print(f"=== shepherding #{pr} ===")
        outcome = shepherd(args.repo, pr, args.max_syncs, args.poll, args.dry_run)
        results[pr] = outcome
        print(f"  #{pr} -> {outcome}\n")

    print("=== summary ===")
    for pr, outcome in results.items():
        print(f"  #{pr}: {outcome}")
    return 0 if all(v == "MERGED" for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
