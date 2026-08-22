#!/usr/bin/env python3
"""Live probe: is `expectedHeadOid` on auto-merge enable-time or continuously enforced?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc investigation tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-21
Status:      ad-hoc -- investigation (one-off)
Retire when: defect D4 in util/safe_merge.py is closed either way.
Related:     notes/JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SAFE-MERGE-KILL-FORENSICS.md (D4)

The question
------------
`safe_merge`'s LOCAL merge path pins the exact head with `--match-head-commit`. Its ARMED
auto-merge net does not, and that trade was shipped silently (defect D4). `gh pr merge`
accepts `--auto --match-head-commit` together and maps it to
`EnablePullRequestAutoMergeInput.expectedHeadOid` -- verified, because passing an abbreviated
SHA returns *"Could not coerce value ... to GitObjectID"* from that exact input type.

So the flag composes. The open question is what the OID means afterwards:

  * **enable-time check** -- an optimistic-concurrency guard against arming on a stale read.
    Harmless to add, and a real improvement.
  * **continuously enforced** -- the net dies the moment the head moves. On a `strict=true`
    repo GitHub moves the head ITSELF to satisfy the up-to-date rule, so the net would
    evaporate exactly when it is needed. Adding the flag would silently negate D1.

Docs do not settle it: `MergePullRequestInput.expectedHeadOid` says *"OID that the pull
request head ref must match to allow merge; if omitted, no check is performed"*, but the
`EnablePullRequestAutoMergeInput` field description is a bare *"The expected head OID of the
pull request."* Neither mentions ongoing validation. That is suggestive, not decisive -- and
a wrong guess here is silent and total, so it gets measured.

Method
------
Open a throwaway PR that CANNOT merge (a markdown file with no H1 fails markdownlint MD041,
so Pre-commit goes red and every required context stays unsatisfied). Arming a net on it is
therefore safe. Then arm WITH the pin, move the head, and re-read `autoMergeRequest`.

Safety: the probe PR is never mergeable while armed, and is disarmed + closed + deleted
afterwards. This script only moves the head; arming/reading/cleanup are separate steps so
each result is observed rather than inferred.

Usage
-----
    python3 util/ad-hoc/2026-08-21_d4_expected_head_oid_probe.py --pr 1225 --expected-head <sha>
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys
import tempfile

MUTATION = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid } }
}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="pcalnon/juniper-ml")
    ap.add_argument("--branch", default="test/d4-expected-head-oid-probe")
    ap.add_argument("--expected-head", required=True, help="full 40-char SHA")
    ap.add_argument("--path", default="util/ad-hoc/ZZZ_d4_probe2_DELETEME.md")
    args = ap.parse_args()

    body = (
        b"second commit: moves the head while auto-merge is armed with expectedHeadOid.\n"
        b"if the net survives this, the pin is an enable-time check only.\n"
    )
    payload = {
        "query": MUTATION,
        "variables": {
            "input": {
                "branch": {
                    "repositoryNameWithOwner": args.repo,
                    "branchName": args.branch,
                },
                "expectedHeadOid": args.expected_head,
                "message": {"headline": "test: move the head to probe expectedHeadOid"},
                "fileChanges": {
                    "additions": [
                        {
                            "path": args.path,
                            "contents": base64.b64encode(body).decode(),
                        }
                    ]
                },
            }
        },
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(payload, fh)
        tmp = fh.name
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", "api", "graphql", "--input", tmp], capture_output=True, text=True, timeout=180
    )
    print(f"rc={p.returncode}")
    print((p.stdout or p.stderr).strip()[:500])
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
