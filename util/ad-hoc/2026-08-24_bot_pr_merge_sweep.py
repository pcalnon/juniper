#!/usr/bin/env python3
"""Arm GitHub-native auto-merge on green bot PRs across the 9 Juniper repos.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-24
Status:      ad-hoc -- recurring (every dependabot sweep)
Retire when: superseded by a fleet merge tool that carries BOTH guards below; delete then.

WHAT IT PRODUCED (2026-08-24)
-----------------------------
Armed or merged 17 bot PRs across 9 repos; 24 landed in total once the stragglers and two
owner decisions were folded in. The two guards here are the whole value, and each was
earned by a defect found during that sweep:

* ``classify`` anchors on REQUIRED contexts, not the rollup -- see its docstring for
  ml#1304, which read green with 0/17 required contexts ever run.
* The ``allow_auto_merge`` gate refuses rather than arming, because where that setting is
  false ``--auto`` silently degrades to an IMMEDIATE merge.

Its probe window was ALSO wrong in the opposite direction and had to be widened twice:
juniper-data-client#170 was reported "NEVER REPORTED (orphaned)" while its contexts were
merely ``pending``, and later verified 19/19 GREEN. Both errors are one mistake -- treating
a short observation window as a terminal answer. If a verdict here surprises you, re-probe
with ``util/wait_for_checks.py`` at a real timeout before believing it.

WHY NATIVE AUTO-MERGE RATHER THAN util/safe_merge.py
----------------------------------------------------
Several repos hold 2-3 bot PRs each, and every repo runs
``strict_required_status_checks_policy: true``. Merging one PR makes its siblings BEHIND,
so a sequential client-side "sync, wait, merge" loop re-tests every sibling on every
merge and loses the race against a moving main -- exactly the refusal safe_merge produced
on ml#1316 today (BEHIND 3x, then gave up). GitHub's own auto-merge moves the head
server-side and merges each PR when ITS checks pass, so the sequencing is handled where
the race actually lives.

SAFETY
------
* ``--dry-run`` (default) changes nothing; ``--execute`` is required to arm.
* Refuses any repo whose ``allow_auto_merge`` is false -- there ``--auto`` silently
  degrades to an IMMEDIATE merge, which with the owner's ruleset bypass can land a PR
  whose checks never finished. That gate is the whole reason this is not a one-liner.
* Refuses any PR that is draft, non-MERGEABLE, or whose rollup is not green.
* Never force-pushes, never closes, never approves, never edits a PR body.
* After arming, verifies state is OPEN+armed OR already MERGED -- and reports anything
  else loudly rather than assuming success. Exit code is NOT the success signal.

Usage:
  python3 util/ad-hoc/2026-08-24_bot_pr_merge_sweep.py            # dry run
  python3 util/ad-hoc/2026-08-24_bot_pr_merge_sweep.py --execute
  python3 util/ad-hoc/2026-08-24_bot_pr_merge_sweep.py --execute --only juniper-deploy
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

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

# Rollup states that are neither success nor "still running".
BAD = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}
PENDING = {"PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED", "WAITING", "REQUESTED"}


def run(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def gh_json(args: list[str], retries: int = 2):
    """gh + JSON with a retry: a transient graphql i/o timeout must not read as 'no PRs'."""
    last = ""
    for _ in range(retries + 1):
        rc, out, err = run(args)
        if rc == 0:
            try:
                return json.loads(out or "[]")
            except json.JSONDecodeError as exc:
                last = f"unparseable: {exc}"
                continue
        last = err[:200]
    raise RuntimeError(last or "gh failed")


def classify(repo: str, pr: dict) -> tuple[str, str]:
    """Return (verdict, reason). Only 'GREEN' is eligible to arm.

    Anchored on the ruleset's REQUIRED contexts via ``util/wait_for_checks.py``, not on
    "the rollup shows nothing bad". That distinction is load-bearing: ml#1304 reported
    five checks, all of them ``Cursor Automation: ... skipping``, and a naive
    no-failures-no-pending rule called it GREEN -- while **0 of its 17 required contexts
    had ever run**. Its workflows sat in ``action_required`` because it was authored by
    ``app/github-actions`` (GITHUB_TOKEN), which GitHub deliberately does not let trigger
    workflows. A vacuous green on a *write* path is how untested code merges.
    """
    if pr.get("isDraft"):
        return "SKIP", "draft"
    if pr.get("mergeable") == "CONFLICTING":
        return "SKIP", "CONFLICTING"

    # 30s was too short and produced a FALSE NEGATIVE: juniper-data-client#170's contexts
    # were `pending` (registering) and got reported as "NEVER REPORTED (orphaned)". That is
    # the mirror of the vacuous green in this function's docstring -- both treat a short
    # observation window as a terminal answer. 150s is long enough for a run to register,
    # and "absent" below is only trusted after it.
    rc, out, err = run([sys.executable, "util/wait_for_checks.py",
                        "--pr", str(pr["number"]), "--repo", repo,
                        "--anchor", "required", "--timeout", "150", "--json"])
    try:
        rep = json.loads(out)
    except json.JSONDecodeError:
        return "SKIP", f"required-context probe unreadable (rc={rc}) {err[:80]}"

    status = rep.get("status", "?")
    if status == "green":
        return "GREEN", f"{len(rep.get('done') or [])} required contexts green"
    if rep.get("failed"):
        names = ", ".join(str(f[0] if isinstance(f, list) else f) for f in rep["failed"][:4])
        return "FAIL", f"required failed: {names}"
    absent = rep.get("absent") or rep.get("never_reported") or []
    if absent:
        return "SKIP", f"{len(absent)} required contexts NEVER REPORTED (orphaned/unapproved)"
    if rep.get("running"):
        return "PENDING", f"{len(rep['running'])} required still running"
    return "SKIP", f"required-context status={status}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="actually arm auto-merge")
    ap.add_argument("--only", action="append", help="restrict to these repos (repeatable)")
    args = ap.parse_args()

    repos = [r for r in REPOS if not args.only or r in args.only]
    fields = "number,title,author,isDraft,mergeable,mergeStateStatus,statusCheckRollup"

    # allow_auto_merge gate, per repo, BEFORE touching anything.
    gate: dict[str, bool] = {}
    for repo in repos:
        try:
            gate[repo] = bool(gh_json(["gh", "api", f"repos/pcalnon/{repo}",
                                       "--jq", ".allow_auto_merge"]))
        except RuntimeError as exc:
            print(f"!! {repo}: cannot read allow_auto_merge ({exc}) -- SKIPPING REPO")
            gate[repo] = False

    armed, skipped, failed = [], [], []
    for repo in repos:
        try:
            prs = gh_json(["gh", "pr", "list", "--repo", f"pcalnon/{repo}", "--state", "open",
                           "--limit", "100", "--json", fields])
        except RuntimeError as exc:
            print(f"!! {repo}: PR list failed after retries ({exc}) -- REPO NOT COVERED")
            failed.append((repo, "-", f"list failed: {exc}"))
            continue

        for pr in prs:
            if (pr.get("author") or {}).get("login", "") not in BOT_LOGINS:
                continue
            num, title = pr["number"], pr["title"][:56]
            verdict, reason = classify(repo, pr)
            tag = f"{repo}#{num}"

            if verdict != "GREEN":
                print(f"  SKIP  {tag:<28} {verdict:<8} {reason}  | {title}")
                skipped.append((tag, verdict, reason))
                continue
            if not gate[repo]:
                print(f"  SKIP  {tag:<28} allow_auto_merge=false -- would merge IMMEDIATELY  | {title}")
                skipped.append((tag, "GATE", "allow_auto_merge false"))
                continue
            if not args.execute:
                print(f"  ARM?  {tag:<28} green ({reason})  | {title}")
                armed.append((tag, "dry-run"))
                continue

            rc, out, err = run(["gh", "pr", "merge", str(num), "--repo", f"pcalnon/{repo}",
                                "--squash", "--auto"])
            # Verify rather than trust rc.
            try:
                st = gh_json(["gh", "pr", "view", str(num), "--repo", f"pcalnon/{repo}",
                              "--json", "state,autoMergeRequest",
                              "--jq", "{state:.state,armed:(.autoMergeRequest!=null)}"])
            except RuntimeError as exc:
                print(f"  ????  {tag:<28} armed but state unreadable ({exc}) -- CHECK BY HAND")
                failed.append((tag, "?", f"verify failed: {exc}"))
                continue
            if st.get("state") == "MERGED":
                print(f"  MERGED {tag:<27} merged on arming (was already green)  | {title}")
                armed.append((tag, "merged"))
            elif st.get("state") == "OPEN" and st.get("armed"):
                print(f"  ARMED {tag:<28} auto-merge pending checks  | {title}")
                armed.append((tag, "armed"))
            else:
                print(f"  ????  {tag:<28} rc={rc} state={st} err={err[:80]} -- CHECK BY HAND")
                failed.append((tag, "?", f"rc={rc} state={st}"))

    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"\n[{mode}] armed/merged={len(armed)}  skipped={len(skipped)}  needs-attention={len(failed)}")
    for t, v, r in skipped:
        print(f"   skipped {t}: {v} {r}")
    for t, _v, r in failed:
        print(f"   !! {t}: {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
