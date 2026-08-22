#!/usr/bin/env python3
"""Add one more GitHub-signed commit to a PR branch that is already in flight.

Project: juniper-ml
Sub-Project: cross-repo tooling
Author: Paul Calnon
Created: 2026-08-22
Status: ad-hoc — fills a gap in util/open_signed_pr.py
Retire when: open_signed_pr.py grows an --amend mode, or this graduates to util/ proper.
Related: util/open_signed_pr.py (whose create_signed_commit this reuses), juniper-ml#1254

WHY THIS EXISTS
    `required_signatures` is live on all 9 repos, so a headless local `git commit` can
    never land -- every commit has to go through GitHub's `createCommitOnBranch`, which
    signs server-side. `util/open_signed_pr.py` does that, but only for the FIRST commit:
    it resolves the base sha, creates the branch, and refuses if the branch already
    exists (by design -- that refusal is its duplicate-PR guard).

    So there was no supported way to add a second commit to a PR already open, and the
    documented workaround was to close and re-cut it. This closes that gap by reusing
    the same helper against the branch's CURRENT head.

WHY expectedHeadOid IS PINNED TO THE BRANCH, NOT THE BASE
    `expectedHeadOid` is optimistic concurrency: the mutation fails rather than
    overwriting if the branch moved since it was read. Pinning it to the branch head
    (not the base) is what makes this an append rather than a rewrite.

⚠ WHOLE-FILE SEMANTICS, SAME AS open_signed_pr.py
    Every --add sends the file's ENTIRE current local content. Any change made to those
    paths on the branch by anyone else since you last synced is silently reverted. Check
    immediately before running, not at sync time:

        git log --oneline HEAD..origin/main -- <paths>     # want empty

USAGE
    python util/ad-hoc/2026-08-22_amend_signed_pr.py \\
        --repo juniper-ml --branch feat/my-branch \\
        --add .github/workflows/ci.yml:.github/workflows/ci.yml \\
        --message "ci(tests): wire the snapshot suites"
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from open_signed_pr import create_signed_commit  # noqa: E402 - path bootstrap must precede the import


def branch_head(owner: str, repo: str, branch: str) -> str:
    """Resolve the branch's current head sha, which is what we pin against."""
    out = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/git/ref/heads/{branch}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["object"]["sha"]


def parse_add(value: str) -> "tuple[str, str]":
    local, _, repo_path = value.partition(":")
    if not local or not repo_path:
        raise argparse.ArgumentTypeError(f"--add expects LOCAL:REPOPATH, got {value!r}")
    return local, repo_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--owner", default="pcalnon")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--add", action="append", default=[], type=parse_add, metavar="LOCAL:REPOPATH", required=True)
    parser.add_argument("--message", required=True, help="commit headline")
    parser.add_argument("--commit-body", default=None, help="commit message body (waiver trailers go here)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    additions = []
    for local, repo_path in args.add:
        path = Path(local)
        if not path.is_file():
            print(f"ERROR: not a file: {local}", file=sys.stderr)
            return 2
        additions.append((repo_path, base64.b64encode(path.read_bytes()).decode("ascii")))

    head = branch_head(args.owner, args.repo, args.branch)
    if args.dry_run:
        print(f"DRY-RUN {args.owner}/{args.repo}:{args.branch} @ {head}")
        for repo_path, contents in additions:
            print(f"  add    {repo_path} ({len(base64.b64decode(contents))} bytes)")
        print(f"  commit {args.message}")
        return 0

    oid = create_signed_commit(
        args.owner,
        args.repo,
        args.branch,
        args.message,
        additions,
        head,
        commit_body=args.commit_body,
    )
    print(f"signed commit {oid[:12]} appended to {args.owner}/{args.repo}:{args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
