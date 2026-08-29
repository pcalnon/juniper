#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Add a GitHub-signed follow-up commit to an EXISTING PR branch on any Juniper repo.

``util/open_signed_pr.py`` refuses a branch that already exists (its dup-guard is
right for opening PRs), so a correction to an open PR needs this: the same
``createCommitOnBranch`` mutation (GitHub signs API-authored commits -- the only
way past ``required_signatures`` from a session without a signing key), pinned
to the branch's current head so a concurrent push fails loudly instead of
clobbering. Generalises the one-file helper archived as
``2026-08-24_commit_driver_fix_to_pr_branch.py``.

Usage
-----
    python3 util/ad-hoc/2026-08-26_commit_files_to_pr_branch.py \\
        --repo juniper-canopy --branch fix/phase4-docs-truth-up-d2-d5-version \\
        --message "fix(truth-up): seed nn_init_output_weights on mount" \\
        --add /local/path/dashboard_manager.py:src/frontend/dashboard_manager.py \\
        [--add LOCAL:REPOPATH ...] [--body-file path] [--owner pcalnon]

Every ``--add`` uploads the WHOLE local file to REPOPATH (same contract as
open_signed_pr.py): base the local copies on the branch's current content.
Exit 0 = commit created (prints the oid); 2 = GitHub refused (message printed).
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True, help="existing PR head branch")
    ap.add_argument("--message", required=True, help="commit headline")
    ap.add_argument("--body-file", default=None, help="optional commit body (file)")
    ap.add_argument("--add", action="append", required=True, metavar="LOCAL:REPOPATH", help="whole-file upload (repeatable)")
    args = ap.parse_args()

    full = f"{args.owner}/{args.repo}"
    head = subprocess.run(["gh", "api", f"repos/{full}/git/ref/heads/{args.branch}", "-q", ".object.sha"], capture_output=True, text=True, check=True).stdout.strip()
    print(f"expectedHeadOid: {head}")

    additions = []
    for spec in args.add:
        local, _, repo_path = spec.partition(":")
        if not local or not repo_path:
            print(f"bad --add spec: {spec!r}", file=sys.stderr)
            return 2
        additions.append({"path": repo_path, "contents": base64.b64encode(Path(local).read_bytes()).decode()})

    message = {"headline": args.message}
    if args.body_file:
        message["body"] = Path(args.body_file).read_text(encoding="utf-8")

    query = "mutation($input: CreateCommitOnBranchInput!) { createCommitOnBranch(input: $input) { commit { oid } } }"
    variables = {
        "input": {
            "branch": {"repositoryNameWithOwner": full, "branchName": args.branch},
            "message": message,
            "expectedHeadOid": head,
            "fileChanges": {"additions": additions},
        }
    }
    result = subprocess.run(["gh", "api", "graphql", "--input", "-"], input=json.dumps({"query": query, "variables": variables}), capture_output=True, text=True)
    if result.returncode:
        print(result.stdout[:800])
        print(result.stderr[:800], file=sys.stderr)
        return 2
    try:
        oid = json.loads(result.stdout)["data"]["createCommitOnBranch"]["commit"]["oid"]
    except (KeyError, TypeError, ValueError):
        print(result.stdout[:800])
        return 2
    print(f"signed commit {oid[:12]} on {full}:{args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
