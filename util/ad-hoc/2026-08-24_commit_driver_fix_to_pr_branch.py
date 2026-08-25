#!/usr/bin/env python3
"""
Project: Juniper
Sub-Project: juniper-ml
Application: one-shot signed-commit push of the CodeQL py/empty-except fix to PR #1311's branch
Author: Paul Calnon
Version: 0.1.0
License: MIT License

Single-use (2026-08-24): `open_signed_pr.py` refuses a second PR on a branch that
already has one open, but a CORRECTION to an open PR only needs a second signed
COMMIT on the same branch. This pushes the amended
``util/ad-hoc/e2e_f027_redrive.py`` to ``docs/canopy-e2e-f027-redrive`` via the
GraphQL ``createCommitOnBranch`` mutation (GitHub signs API-authored commits),
with ``expectedHeadOid`` freshly resolved so a concurrent push conflicts instead
of being clobbered.
"""

import base64
import json
import subprocess
import sys

REPO = "pcalnon/juniper-ml"
BRANCH = "docs/canopy-e2e-f027-redrive"
PATH = "util/ad-hoc/e2e_f027_redrive.py"


def main() -> int:
    head = subprocess.run(
        ["gh", "api", f"repos/{REPO}/git/ref/heads/{BRANCH}", "-q", ".object.sha"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    print(f"expectedHeadOid: {head}")
    with open(PATH, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    query = "mutation($input: CreateCommitOnBranchInput!) { createCommitOnBranch(input: $input) { commit { oid } } }"
    variables = {
        "input": {
            "branch": {"repositoryNameWithOwner": REPO, "branchName": BRANCH},
            "message": {"headline": "fix(util): explain the deliberately-empty except in the re-drive sampler (CodeQL py/empty-except)"},
            "expectedHeadOid": head,
            "fileChanges": {"additions": [{"path": PATH, "contents": b64}]},
        }
    }
    r = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=json.dumps({"query": query, "variables": variables}),
        capture_output=True,
        text=True,
    )
    print(r.stdout[:500])
    if r.returncode:
        print(r.stderr[:500], file=sys.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
