#!/usr/bin/env python3
"""Sweep merged PRs for the squash-into-stacked-branch footgun (ml#434).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- audit (re-runnable; widen --since to re-sweep)
Retire when: ml#434 is closed and the "verify the diff reached main" step is part of the
             merge procedure rather than a periodic sweep.
Related:     ml#434; canopy#365/#366; juniper-recurrence#7/#8.

The failure class
-----------------
A PR whose `baseRefName` is another feature branch (a "stacked" PR) can show **MERGED**
while its diff never reaches `main` -- the squash lands on the intermediate branch, and if
that branch is never itself merged, the work is stranded with a green checkmark on it.

Known instances: canopy#365 (recovered by #366), juniper-recurrence#7 + #8 (stranded --
routes + publish workflow never landed, leaving the app unpublishable).

Two traps this tool is built around
-----------------------------------
1. **`--limit` truncates SILENTLY.** `gh pr list --state merged --limit 100` on a repo with
   117 merged PRs returns the newest 100 and says nothing. The first run of this sweep
   reported "0 stacked PRs" on juniper-recurrence -- the repo with the two *known* stranded
   PRs -- purely because #7/#8 fell off the end. So this tool asserts COVERAGE: the oldest
   PR it retrieved must predate the window start, otherwise it reports INCOMPLETE loudly and
   exits non-zero. A sweep that cannot prove it saw the whole window is not a sweep.

2. **Ancestry is the WRONG test for a squash merge.** ml#434 proposes
   `git merge-base --is-ancestor <pr-head-sha> origin/main`. That is always FALSE for a
   squash-merged PR, because squashing creates a NEW commit and discards the original SHAs --
   observed directly on ml#1202, which merged cleanly to main and whose head SHA is still not
   an ancestor. Applied as written, that check would flag every squash-merged PR in the fleet
   as stranded. This tool tests the **merge commit** for reachability from `main` instead, and
   for anything it cannot resolve that way it reports NEEDS-REVIEW rather than guessing.

Usage
-----
    python3 util/ad-hoc/2026-08-20_stacked_pr_sweep.py
    python3 util/ad-hoc/2026-08-20_stacked_pr_sweep.py --since 2026-01-01
    python3 util/ad-hoc/2026-08-20_stacked_pr_sweep.py --repo juniper-recurrence
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys

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

TRUNK = {"main", "master", "develop"}


def gh(args: list[str]):
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, timeout=180
    )
    if p.returncode != 0:
        return None
    return p.stdout


def gh_json(args: list[str]):
    out = gh(args)
    if out is None:
        return None
    try:
        return json.loads(out or "null")
    except json.JSONDecodeError:
        return None


def merged_prs(owner: str, repo: str, limit: int):
    return gh_json(
        [
            "pr",
            "list",
            "--repo",
            f"{owner}/{repo}",
            "--state",
            "merged",
            "--limit",
            str(limit),
            "--json",
            "number,title,baseRefName,headRefName,mergedAt,mergeCommit,url",
        ]
    )


def reachable_from_main(owner: str, repo: str, sha: str):
    """Is `sha` reachable from main? Returns True / False / None (undetermined).

    Uses the compare API rather than local git so no sibling checkout is required and no
    clone can be stale. `compare/main...<sha>` reports <sha> relative to main:
    `behind` / `identical` mean it is an ancestor.
    """
    data = gh_json(["api", f"repos/{owner}/{repo}/compare/main...{sha}"])
    if not data or "status" not in data:
        return None
    return data["status"] in ("behind", "identical")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", action="append", default=None)
    ap.add_argument("--since", default="2026-06-01", help="window start, YYYY-MM-DD")
    ap.add_argument("--limit", type=int, default=1000)
    args = ap.parse_args()
    repos = args.repo or REPOS

    print(f"window: mergedAt >= {args.since}   repos: {len(repos)}")
    print()
    print(f"{'repo':<24} {'merged':>7} {'oldest seen':<12} {'coverage':<12} {'stacked':>8}")
    print("-" * 74)

    incomplete, flagged = [], []
    for repo in repos:
        prs = merged_prs(args.owner, repo, args.limit) or []
        oldest = min((p["mergedAt"] or "" for p in prs), default="")
        # COVERAGE ASSERTION -- the guard against a silent --limit truncation.
        #
        # Complete when EITHER we exhausted the repo's merged-PR list (fewer rows came back
        # than we asked for, so there is nothing older to miss) OR the oldest row predates
        # the window. The first arm matters: juniper-recurrence's whole history starts
        # 2026-06-15, so requiring "oldest < since" alone reported INCOMPLETE on a repo that
        # was in fact fully covered -- a false alarm is as corrosive to a sweep as a false
        # clear, because the next reader learns to ignore the banner.
        exhausted = len(prs) < args.limit
        covered = bool(prs) and (exhausted or oldest[:10] < args.since)
        if not prs:
            covered, note = False, "NO DATA"
        elif not covered:
            note = "INCOMPLETE"
            incomplete.append((repo, len(prs), oldest))
        else:
            note = "ok (all)" if exhausted else "ok"
        stacked = [
            p
            for p in prs
            if (p["mergedAt"] or "")[:10] >= args.since and p["baseRefName"] not in TRUNK
        ]
        flagged.extend((repo, p) for p in stacked)
        print(
            f"{repo:<24} {len(prs):>7} {oldest[:10]:<12} {note:<12} {len(stacked):>8}"
        )

    if incomplete:
        print()
        print("!! COVERAGE INCOMPLETE -- the oldest PR retrieved is NEWER than the window")
        print("!! start, so older PRs were never examined. Raise --limit and re-run.")
        for repo, n, oldest in incomplete:
            print(f"     {repo}: retrieved {n}, oldest {oldest[:10]}, window starts {args.since}")

    print()
    print("=" * 100)
    print("STACKED PRs (baseRefName is not a trunk branch)")
    print("=" * 100)
    if not flagged:
        print("  none in window")
    else:
        print(f"{'repo':<22} {'PR':>5} {'base':<34} {'landed?':<12} merged")
        print("-" * 100)
        for repo, p in sorted(flagged, key=lambda r: (r[0], r[1]["number"])):
            sha = (p.get("mergeCommit") or {}).get("oid")
            ok = reachable_from_main(args.owner, repo, sha) if sha else None
            # "NOT-ON-MAIN", not "STRANDED". The test answers a narrow question -- is THIS
            # PR's merge commit an ancestor of main -- and a False can still mean the work
            # reached main by another route (canopy#365's content was re-landed by #366, so
            # it reports False and is nonetheless remediated). Calling that "STRANDED" would
            # overstate a mechanical check into a conclusion about the work, and send the
            # next reader chasing already-fixed items.
            verdict = {True: "LANDED", False: "** NOT-ON-MAIN **", None: "NEEDS-REVIEW"}[ok]
            print(
                f"{repo:<22} {p['number']:>5} {p['baseRefName'][:33]:<34} "
                f"{verdict:<12} {(p['mergedAt'] or '')[:10]}"
            )
            if ok is False:
                print(f"{'':<22}       -> {p['url']}  head={p['headRefName']}")

    print()
    print("NOT-ON-MAIN means: this PR's own merge commit is not an ancestor of main. It is a")
    print("  starting point for review, NOT a conclusion -- the work may have been re-landed")
    print("  by a later PR (canopy#365 reports NOT-ON-MAIN and was remediated by #366).")
    print("  Adjudicate each one before acting.")
    print()
    print("NOTE on method: reachability is tested on the MERGE COMMIT, not the PR head.")
    print("  ml#434 proposes `git merge-base --is-ancestor <pr-head-sha> origin/main`, which")
    print("  is always FALSE under squash-merge (squash discards the original SHAs) and would")
    print("  flag every squash-merged PR in the fleet. Verified on ml#1202: merged to main,")
    print("  head SHA still not an ancestor.")
    return 1 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
