#!/usr/bin/env python3
"""Append a GitHub-signed commit to an EXISTING branch, without opening a PR.

Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
License     : MIT License
Created     : 2026-09-08

Why this exists
---------------
`util/open_signed_pr.py` does branch + signed commit + PR in one shot, and its
DUP-GUARD returns 1 the moment an open PR already exists for the branch. That
guard is correct -- it stops a second PR being opened for the same branch -- but
it fires BEFORE the commit, so there is no supported way to add a follow-up
commit to a PR that tool opened. Signing locally is not an option in a headless
session, and an unsigned commit anywhere in a branch's history blocks the merge
under `required_signatures` (squash does not rescue it).

This reuses `open_signed_pr`'s own `create_signed_commit` against the branch's
current head, so the follow-up commit is signed by GitHub exactly like the first.

The `expected_head_oid` is read live rather than passed in: that is the
optimistic-concurrency token, so a concurrent push to the same branch makes this
fail loudly instead of clobbering. Note the addition is a WHOLE-FILE upload --
read the branch's current copy before editing, or you silently revert whatever
landed on it since.

Usage
-----
    python3 util/ad-hoc/append_signed_commit.py \
        --repo juniper-ml --branch docs/some-branch \
        --add notes/FOO.md:notes/FOO.md \
        --message "docs: follow-up" --commit-body-file /tmp/body.md
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess  # nosec B404 - shells out to the authenticated `gh` CLI only
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from open_signed_pr import create_signed_commit, parse_add  # noqa: E402


def branch_head_oid(owner: str, repo: str, branch: str) -> str:
    """Live head OID of ``branch`` -- the optimistic-concurrency token."""
    out = subprocess.run(  # nosec B603,B607 - fixed argv, authenticated gh CLI
        ["gh", "api", f"repos/{owner}/{repo}/git/ref/heads/{branch}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["object"]["sha"]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--add", action="append", required=True, metavar="LOCAL:REPOPATH")
    ap.add_argument("--message", required=True)
    ap.add_argument("--commit-body-file")
    args = ap.parse_args(argv)

    additions = []
    for spec in args.add:
        local, repopath = parse_add(spec)
        additions.append({"path": repopath, "contents": base64.b64encode(Path(local).read_bytes()).decode("ascii")})

    body = Path(args.commit_body_file).read_text(encoding="utf-8") if args.commit_body_file else None
    head = branch_head_oid(args.owner, args.repo, args.branch)
    print(f"branch head is {head[:12]}; appending {len(additions)} file(s)")

    sha = create_signed_commit(args.owner, args.repo, args.branch, args.message, additions, head, commit_body=body)
    print(f"signed commit {sha[:12]} on {args.owner}/{args.repo}:{args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
