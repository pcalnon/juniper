#!/usr/bin/env python3
"""Add ONE GitHub-signed commit to an EXISTING branch of any Juniper repo (createCommitOnBranch).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — wip (candidate for promotion next to util/open_signed_pr.py, with a hermetic test like tests/test_open_signed_pr.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py (whose ``create_signed_commit`` this reuses verbatim); canopy#601 (the first PR it added a fix-up to)

Why this exists
---------------
``util/open_signed_pr.py`` opens a branch + signed commit + PR in one go and, by its safety
contract, REFUSES a branch that already exists. That leaves no way to land a follow-up commit on
a PR it opened -- a CI fix-up, a review change -- when the session cannot sign locally (the
signing subkey lives on a YubiKey that needs a touch; ``gpg: signing failed: Timeout``). This
script fills exactly that gap: it sends whole-file additions to an existing branch as one
GitHub-signed commit, pinned to ``--expected-head`` so a concurrent push fails loudly rather
than clobbering.

Like the helper it reuses, it sends WHOLE FILE contents: anything merged to those paths on the
branch since your worktree was synced is silently reverted. Sync and re-check the branch head
immediately before running, not when you start editing.

Usage
-----
    python util/ad-hoc/push_signed_commit.py \
        --repo juniper-canopy --branch fix/some-branch \
        --expected-head <full sha of the branch head you built on> \
        --add /local/path/file.py:src/path/file.py [--add ...] [--delete repo/path] \
        --message "headline" [--commit-body-file body.txt] [--dry-run]

Exit 0 = commit landed (or --dry-run), 1 = refused (head moved / branch missing), 2 = hard error.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys

_UTIL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _UTIL_DIR)

import open_signed_pr as osp  # noqa: E402  (util/ is not a package; sibling import by path)


def _branch_head(owner: str, repo: str, branch: str) -> str:
    out = osp.gh(["api", f"/repos/{owner}/{repo}/git/ref/heads/{branch}", "--jq", ".object.sha"], check=False)
    return (out or "").strip()


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--owner", default="pcalnon")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--expected-head", required=True, help="full sha the branch MUST still be at (the head you built on)")
    parser.add_argument("--add", action="append", default=[], type=osp.parse_add, metavar="LOCAL:REPOPATH")
    parser.add_argument("--delete", action="append", default=[], metavar="REPOPATH")
    parser.add_argument("--message", required=True, help="commit headline")
    parser.add_argument("--commit-body-file", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.add and not args.delete:
        print("ERROR: nothing to commit -- give at least one --add or --delete", file=sys.stderr)
        return 2

    additions = []
    for local, repo_path in args.add:
        try:
            with open(local, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read {local}: {exc}", file=sys.stderr)
            return 2
        additions.append((repo_path, base64.b64encode(raw).decode("ascii")))

    commit_body = None
    if args.commit_body_file:
        try:
            with open(args.commit_body_file, encoding="utf-8") as fh:
                commit_body = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read --commit-body-file {args.commit_body_file}: {exc}", file=sys.stderr)
            return 2

    head = _branch_head(args.owner, args.repo, args.branch)
    if not head:
        print(f"REFUSED: branch {args.branch} does not exist on {args.owner}/{args.repo}", file=sys.stderr)
        return 1
    if head != args.expected_head:
        print(f"REFUSED: {args.branch} is at {head}, not the expected {args.expected_head} -- sync, re-apply, re-check", file=sys.stderr)
        return 1

    print(f"branch {args.owner}/{args.repo}:{args.branch} @ {head}")
    for repo_path, _contents in additions:
        print(f"  add     {repo_path}")
    for repo_path in args.delete:
        print(f"  delete  {repo_path}")
    print(f"  message {args.message}")
    if args.dry_run:
        print("  (dry run: nothing written)")
        return 0

    try:
        oid = osp.create_signed_commit(args.owner, args.repo, args.branch, args.message, additions, head, args.delete or None, commit_body)
    except osp.GhError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"signed commit {oid} on {args.owner}/{args.repo}:{args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
