#!/usr/bin/env python3
"""Drive armed-but-BEHIND bot PRs to merge, one at a time per repo.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-24
Status:      ad-hoc -- recurring (every dependabot sweep, until allow_update_branch flips)
Retire when: ``allow_update_branch: true`` is set on the 9 repos -- then arming auto-merge
             is sufficient on its own and this script has no job. Delete it in that PR.

THE PROBLEM THIS SOLVES
-----------------------
Every Juniper repo runs ``strict_required_status_checks_policy: true`` but has
``allow_update_branch: false``. Consequence, measured 2026-08-24: GitHub's native
auto-merge **cannot** clear a BEHIND branch, so an armed PR that goes BEHIND -- which every
sibling merge causes -- stays armed forever instead of merging. 7 of 17 swept PRs merged
(they were CLEAN at arming); the other 10 sat armed+BEHIND indefinitely.

The systemic fix is ``allow_update_branch: true``, which is a repo-settings change and
therefore the owner's call. This script is the no-settings-change alternative: it issues
the ``update-branch`` GitHub will not, then lets the ALREADY-ARMED auto-merge fire once the
re-test is green.

WHAT IT PRODUCED (2026-08-24 sweep)
-----------------------------------
Drove the 10 armed+BEHIND survivors of the 17-PR sweep to merge across juniper-ml,
-cascor, -canopy, -data-client and -recurrence. Two costs worth knowing before the next run:

* It is killed by the ~3600s background-worker lease. Six runs died mid-sweep. That costs
  the LOG, never the work -- every pass re-reads live GitHub state and resumes -- so re-run
  it rather than trying to keep one invocation alive. Short ``--deadline-min`` windows
  (~20) fit inside a lease.
* On juniper-ml specifically, main took a commit every ~13 min against a ~10 min pipeline,
  so a PR can lose the race repeatedly through no fault of its own. ml#1304 lost it twice.

WHY ONE PR AT A TIME PER REPO
-----------------------------
Under the strict rule only one PR per repo can be up-to-date at once: merging any PR makes
every sibling BEHIND again. Updating all of a repo's PRs together therefore burns a full CI
run per sibling and immediately invalidates all but one. Repos run in parallel; PRs within a
repo run strictly in sequence.

SAFETY
------
* Never merges. Only calls ``update-branch`` on PRs that are ALREADY armed by their owner's
  earlier explicit decision -- the merge itself is still GitHub's checks-gated auto-merge.
* Refuses to touch a PR that is not both OPEN and armed.
* ``--dry-run`` default.

Usage:
  python3 util/ad-hoc/2026-08-24_bot_pr_converge.py
  python3 util/ad-hoc/2026-08-24_bot_pr_converge.py --execute --deadline-min 90
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

REPOS = (
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
)

BOT_LOGINS = {"dependabot", "app/dependabot", "github-actions", "app/github-actions"}


def discover() -> dict[str, list[int]]:
    """Every OPEN, ARMED bot PR, grouped by repo, oldest first.

    Discovered rather than hard-coded: the first version of this script carried a frozen
    PR list, which went stale the moment anything merged and had to be hand-edited three
    times during one sweep. Ordering is by PR number so a repo's queue is stable across
    runs -- under the strict rule only one PR per repo can be up to date at a time, so the
    queue order decides which one gets the CI budget.
    """
    targets: dict[str, list[int]] = {}
    for repo in REPOS:
        rc, out, err = gh(["gh", "pr", "list", "--repo", f"pcalnon/{repo}", "--state", "open",
                           "--limit", "100", "--json", "number,author,autoMergeRequest"])
        if rc != 0:
            print(f"!! {repo}: PR list failed ({err[:80]}) -- REPO NOT COVERED THIS PASS")
            continue
        try:
            prs = json.loads(out or "[]")
        except json.JSONDecodeError:
            print(f"!! {repo}: PR list unparseable -- REPO NOT COVERED THIS PASS")
            continue
        nums = sorted(p["number"] for p in prs
                      if (p.get("author") or {}).get("login", "") in BOT_LOGINS
                      and p.get("autoMergeRequest") is not None)
        if nums:
            targets[repo] = nums
    return targets


def gh(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def view(repo: str, num: int, retries: int = 3) -> dict:
    """PR state, retried.

    A transient ``dial tcp ... i/o timeout`` from the graphql endpoint is NOT a terminal
    outcome, and the first version of this driver treated it as one: it returned
    ``state="?"``, the caller took that as SKIP, and cascor#576 and data-client#163 were
    abandoned mid-sweep on a blip. Same lesson the census script already carries -- a
    network failure must retry, never be recorded as an answer.
    """
    last = ""
    for attempt in range(retries + 1):
        rc, out, err = gh(["gh", "pr", "view", str(num), "--repo", f"pcalnon/{repo}",
                           "--json", "state,mergeStateStatus,autoMergeRequest"])
        if rc == 0:
            try:
                d = json.loads(out)
            except json.JSONDecodeError:
                last = "unparseable"
            else:
                return {"state": d.get("state"), "mergeState": d.get("mergeStateStatus"),
                        "armed": d.get("autoMergeRequest") is not None}
        else:
            last = err[:100]
        if attempt < retries:
            time.sleep(5 * (attempt + 1))
    return {"state": "TRANSIENT", "err": last}


def update_branch(repo: str, num: int) -> tuple[bool, str]:
    rc, out, err = gh(["gh", "api", "-X", "PUT",
                       f"repos/pcalnon/{repo}/pulls/{num}/update-branch",
                       "-H", "Accept: application/vnd.github+json"])
    return rc == 0, (err or out)[:120]


def drive_repo(repo: str, nums: list[int], execute: bool, deadline: float, interval: int) -> list[str]:
    log: list[str] = []
    for num in nums:
        tag = f"{repo}#{num}"
        while True:
            if time.monotonic() > deadline:
                log.append(f"DEADLINE {tag} not resolved")
                return log
            st = view(repo, num)
            state = st.get("state")
            if state == "MERGED":
                log.append(f"MERGED  {tag}")
                break
            if state == "TRANSIENT":
                # Retries already exhausted inside view(); wait and keep this PR in the
                # queue rather than abandoning it -- the network, not the PR, is at fault.
                log.append(f"retry   {tag} after transient: {st.get('err', '')}")
                time.sleep(interval)
                continue
            if state in ("CLOSED", "?"):
                log.append(f"SKIP    {tag} state={state} {st.get('err', '')}")
                break
            if not st.get("armed"):
                log.append(f"SKIP    {tag} NOT ARMED -- refusing to touch")
                break
            ms = st.get("mergeState")
            if ms == "BEHIND":
                if not execute:
                    log.append(f"WOULD-UPDATE {tag} (BEHIND, armed)")
                    break
                ok, msg = update_branch(repo, num)
                log.append(f"update  {tag} -> {'ok' if ok else 'FAILED ' + msg}")
                if not ok:
                    break
            elif not execute:
                log.append(f"WAIT    {tag} mergeState={ms} (armed; auto-merge should fire)")
                break
            time.sleep(interval)
    return log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--deadline-min", type=int, default=90)
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()

    deadline = time.monotonic() + args.deadline_min * 60
    targets = discover()
    if not targets:
        print("no OPEN armed bot PRs found -- nothing to converge")
        return 0
    total = sum(len(v) for v in targets.values())
    print(f"discovered {total} armed bot PR(s) across {len(targets)} repo(s)", flush=True)
    with ThreadPoolExecutor(max_workers=len(targets)) as ex:
        futs = {r: ex.submit(drive_repo, r, n, args.execute, deadline, args.interval)
                for r, n in targets.items()}
        for _repo, fut in futs.items():
            for line in fut.result():
                print(line, flush=True)

    print(f"\n[{'EXECUTE' if args.execute else 'DRY RUN'}] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
