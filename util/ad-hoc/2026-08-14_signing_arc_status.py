"""
Status board for the ml#1099 runner-commit signing fan-out (11 PRs across 8 repos).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-14
Status: ad-hoc -- investigation (all 11 PRs MERGED 2026-08-14; ml#1099 closed)
Retire when: juniper-cascor 0.9.0 is published to PyPI (the last open thread this
             board was watching) and the arc is fully closed. Delete or move to
             util/ad-hoc/retired/ then.
Related: juniper-ml#1099, juniper-ml#1105, juniper-cascor#518

Reports per PR: check rollup, ran/pending/failed context counts, mergeStateStatus,
whether EVERY commit is signed, and any unresolved review thread. The signature
column is the point of the arc -- a PR here that is itself unsigned would be
self-refuting.

The MERGE-OK column is the reusable part. Merging a fleet of PRs needs more than a
green rollup, and each of these guards exists because the arc hit the failure:

  * ran > 0            -- a PR whose contexts NEVER reported also shows no
                          failures. That is exactly the `[skip ci]` orphan class
                          (cascor#515), where every required check sat at
                          "expected" and the rollup looked clean.
  * threads == 0       -- ml#1096 sat BLOCKED with all 18 checks passing on one
                          unresolved github-advanced-security review thread,
                          which `gh pr checks` does not surface at all.
  * every commit signed-- the whole point of ml#1099; an unsigned commit anywhere
                          in the branch history blocks the merge.
  * mergeStateStatus   -- BEHIND / BLOCKED are both non-mergeable and are NOT
    == CLEAN              visible in the check rollup either.

Re-point PRS at a new batch to reuse it. Note `gh pr checks` has no --json in the
installed gh, which is why the counts come from the GraphQL rollup instead.

Usage:
    python util/ad-hoc/2026-08-14_signing_arc_status.py [--owner pcalnon]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

# (repo, pr_number, short label)
PRS = [
    ("juniper-ml", 1105, "ml: touch-up verify + lockfile sign"),
    ("juniper-cascor", 519, "lockfile: signed + skip release/**"),
    ("juniper-canopy", 490, "lockfile: signed + skip release/**"),
    ("juniper-data", 264, "lockfile: signed + skip release/**"),
    ("juniper-cascor", 520, "agents-md: verify"),
    ("juniper-canopy", 491, "agents-md: verify"),
    ("juniper-data", 265, "agents-md: verify"),
    ("juniper-data-client", 149, "agents-md: verify"),
    ("juniper-cascor-client", 116, "agents-md: verify"),
    ("juniper-cascor-worker", 152, "agents-md: verify"),
    ("juniper-deploy", 178, "agents-md: verify"),
    ("juniper-cascor", 518, "RELEASE juniper-cascor v0.9.0"),
]

QUERY = """
query($owner:String!, $repo:String!, $num:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$num) {
      state
      mergeable
      mergeStateStatus
      reviewThreads(first:50) { nodes { isResolved } }
      commits(first:100) { nodes { commit { oid signature { isValid } } } }
      statusCheckRollup: commits(last:1) {
        nodes { commit { statusCheckRollup {
          state
          contexts(first:100) {
            totalCount
            nodes {
              __typename
              ... on CheckRun { name conclusion status }
              ... on StatusContext { context state }
            }
          }
        } } }
      }
    }
  }
}
"""


def summarize_contexts(rollup: dict) -> tuple:
    """-> (ran, pending, failed) counts.

    'Green rollup' is not enough: a PR whose contexts never reported at all also
    shows no failures. Counting what actually RAN is the guardrail (the [skip ci]
    orphan class, where every required check sat at 'expected').
    """
    contexts = ((rollup or {}).get("contexts") or {}).get("nodes") or []
    ran = pending = failed = 0
    for c in contexts:
        if c.get("__typename") == "CheckRun":
            status = (c.get("status") or "").upper()
            concl = (c.get("conclusion") or "").upper()
            if status != "COMPLETED":
                pending += 1
            elif concl in ("SUCCESS", "NEUTRAL", "SKIPPED"):
                ran += 1
            else:
                failed += 1
        else:
            state = (c.get("state") or "").upper()
            if state == "PENDING":
                pending += 1
            elif state == "SUCCESS":
                ran += 1
            else:
                failed += 1
    return ran, pending, failed


def query_pr(owner: str, repo: str, num: int):
    proc = subprocess.run(
        [
            "gh", "api", "graphql",
            "-f", f"query={QUERY}",
            "-F", f"owner={owner}",
            "-F", f"repo={repo}",
            "-F", f"num={num}",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return None
    return ((data.get("data") or {}).get("repository") or {}).get("pullRequest")


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    args = ap.parse_args(argv)

    print(f"{'repo#pr':<24} {'state':<7} {'rollup':<9} {'ran/pend/fail':<14} {'merge':<10} {'signed':<8} {'thr':<4} {'MERGE-OK'}")
    print("-" * 104)
    blocked = 0
    for repo, num, label in PRS:
        pr = query_pr(args.owner, repo, num)
        ident = f"{repo.replace('juniper-', '')}#{num}"
        if pr is None:
            print(f"{ident:<28} {'ERROR':<7} {'?':<9} {'?':<10} {'?':<9} ?")
            blocked += 1
            continue

        commits = [n["commit"] for n in (pr.get("commits") or {}).get("nodes") or []]
        sig = sum(1 for c in commits if (c.get("signature") or {}).get("isValid"))
        signed = f"{sig}/{len(commits)}"
        unsigned = sig != len(commits)

        rollup_nodes = (pr.get("statusCheckRollup") or {}).get("nodes") or []
        rollup = "-"
        rc = None
        if rollup_nodes:
            rc = (rollup_nodes[0].get("commit") or {}).get("statusCheckRollup")
            rollup = (rc or {}).get("state") or "NONE"
        ran, pending, failed = summarize_contexts(rc)

        threads = [t for t in ((pr.get("reviewThreads") or {}).get("nodes") or []) if not t.get("isResolved")]
        thr = str(len(threads)) if threads else "-"

        state = pr.get("state", "?")
        merge_state = pr.get("mergeStateStatus", "?")

        # Every guardrail must hold before this PR may be merged.
        ok = (
            state == "OPEN"
            and not unsigned
            and not threads
            and merge_state == "CLEAN"
            and failed == 0
            and pending == 0
            and ran > 0  # checks actually REPORTED -- not merely "nothing failed"
        )
        verdict = "YES" if ok else ("merged" if state == "MERGED" else "no")

        mark = "  <-- UNSIGNED" if unsigned else ""
        print(f"{ident:<24} {state:<7} {rollup:<9} {f'{ran}/{pending}/{failed}':<14} {merge_state:<10} {signed:<8} {thr:<4} {verdict}{mark}")
        print(f"{'':<24} {label}")
        if unsigned and state == "OPEN":
            blocked += 1
    if blocked:
        print(f"\n{blocked} OPEN row(s) need attention (unsigned commit or query error).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
