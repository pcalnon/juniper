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

PREFER `util/wait_for_checks.py`. It is the canonical waiter and the reference
implementation for check classification; this module exists only for the
green-but-BEHIND park, which that waiter does not clear. Under strict rules the
settled 2026-09-03 policy is to try `util/safe_merge.py --execute` FIRST. And do
not run `safe_merge --execute` against a PR this tool is shepherding: a refusal
disarms the net, and this tool cannot re-arm one.

FAIL-SAFE

- Never merges. It only calls `update-branch`, which is server-side and
  GitHub-signed (`required_signatures` accepts it); the armed net does the merge.
- `expected_head_sha` is pinned on every call, so a concurrent push fails loudly
  rather than being clobbered.
- Refuses to sync a PR with a failing check -- a red PR should be fixed, not
  spun. "Failing" includes `ERROR`, and reads a legacy commit status's `state`
  as well as a check-run's `conclusion`; reading only `conclusion` made every
  failing legacy context read as *pending*.
- Bounded BOTH ways: `--max-syncs` per PR, and `--per-pr-timeout` wall-clock.
  Only the BEHIND arm used to have an exit, so a PR parked at BLOCKED or UNKNOWN
  -- the livelock this tool exists to survive -- looped forever.
- A failed read is reported as `READ-FAILED`, never as a state, and the run exits
  **2** (inconclusive) rather than 1. See `ReadFailed`.

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


class ReadFailed(Exception):
    """A `gh` read did not succeed. NOT the same as a read that returned nothing.

    The first version of this module returned None for both, and every caller
    treated None as an empty dict. Measured consequence, 2026-09-07: with five
    review agents and a merge train sharing the API, `gh pr view` was throttled
    and the shepherd reported **NOT-ARMED for 4 of 4 PRs that were armed** —
    100% false negatives. The obvious operator response to NOT-ARMED is to
    re-arm, which acts on a PR that never needed it, and the run exits 1 as if
    it had adjudicated something.

    A state verdict must never be derived from a read that did not happen.
    """


def gh_json(*args: str, attempts: int = 3, backoff: float = 2.0):
    """Run `gh ... --json`, retrying transient failures. Raises ReadFailed."""
    last = ""
    for i in range(attempts):
        proc = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                last = f"undecodable JSON: {exc}"
        else:
            last = proc.stderr.strip()[:200]
        if i < attempts - 1:
            time.sleep(backoff * (i + 1))
    raise ReadFailed(f"gh {' '.join(args[:3])}…: {last}")


def pr_state(repo: str, pr: int) -> dict:
    """GraphQL view for state + checks, plus a REST read to FORCE mergeability.

    The REST call is not redundant: `mergeStateStatus` sits at UNKNOWN until
    something asks for it, and GraphQL alone never triggers the computation.
    """
    view = gh_json(
        "pr", "view", str(pr), "--repo", repo,
        "--json", "state,mergeStateStatus,autoMergeRequest,headRefOid,statusCheckRollup",
    )
    rest = gh_json("api", f"repos/{repo}/pulls/{pr}")
    rollup = view.get("statusCheckRollup") or []

    # A check row is EITHER a check-run (`conclusion`) or a legacy commit status
    # (`state`); reading only `conclusion` made every failing legacy context read as
    # pending. `ERROR` was also missing from the failing set. Both are fixed against
    # the canonical list in util/wait_for_checks.py, which is the reference
    # implementation -- prefer that waiter over this one wherever it fits.
    concl = [((c.get("conclusion") or c.get("state") or "") or None) for c in rollup]
    failing_states = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "ERROR"}

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
        "failing": sum(1 for c in concl if (c or "").upper() in failing_states),
        "pending": sum(1 for c in concl if not c),
        "success": sum(1 for c in concl if (c or "").upper() == "SUCCESS"),
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


def shepherd(repo: str, pr: int, max_syncs: int, poll: int, dry_run: bool,
             deadline: float) -> str:
    """Drive one PR out of the green-but-BEHIND park. Never merges.

    THE WALL-CLOCK BOUND IS NOT DECORATION. Only the BEHIND arm previously had an
    exit; a PR sitting at BLOCKED or UNKNOWN — the green-but-BLOCKED livelock this
    tool exists to survive — looped forever with no report.
    """
    syncs = 0
    while True:
        if time.time() > deadline:
            return "DEADLINE-REACHED"
        try:
            s = pr_state(repo, pr)
        except ReadFailed as exc:
            # A failed read is NOT a state. Report it as itself and move on rather
            # than emitting NOT-ARMED, which reads as an adjudication.
            return f"READ-FAILED ({exc})"

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
    ap.add_argument("--per-pr-timeout", type=int, default=2700,
                    help="wall-clock bound per PR, seconds (default 45 min)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    results: dict[int, str] = {}
    for pr in args.pr:
        print(f"=== shepherding #{pr} ===")
        outcome = shepherd(args.repo, pr, args.max_syncs, args.poll, args.dry_run,
                           deadline=time.time() + args.per_pr_timeout)
        results[pr] = outcome
        print(f"  #{pr} -> {outcome}\n")

    print("=== summary ===")
    for pr, outcome in results.items():
        print(f"  #{pr}: {outcome}")

    # A READ-FAILED run adjudicated nothing. Exit 2 so a caller can tell "this PR did
    # not merge" from "this tool could not see".
    if any(v.startswith("READ-FAILED") for v in results.values()):
        print("\nINCONCLUSIVE: at least one PR could not be read; no verdict for it.")
        return 2
    return 0 if all(v == "MERGED" for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
