#!/usr/bin/env python3
"""Append ONE GitHub-signed commit to an EXISTING branch on any Juniper repo.

Project:     Juniper
Sub-Project: juniper-ml
Application: cross-repo tooling (ad-hoc)
Author:      Paul Calnon
Created:     2026-09-08
Status:      ad-hoc (decision-11 release train); candidate for util/ promotion
Related:     util/open_signed_pr.py (opens a NEW branch + PR; refuses an existing
             branch), util/release_train/propose.py (opens release-proposal PRs
             whose branches this script then completes)

Why this exists
---------------
``required_signatures`` is on in every Juniper repo and local ``git commit`` hangs
in a headless session (the YubiKey signing key needs a touch). ``open_signed_pr.py``
covers the "new branch + PR" case but deliberately refuses a branch that already
exists. The release train's ``propose.py`` opens a branch that is *almost* complete:
it bumps ``pyproject.toml`` / ``_version.py`` / ``CHANGELOG.md`` / ``AGENTS.md`` but
not the carriers a repo's own tests pin -- juniper-data-client's ``__init__.py``
``__version__`` plus its nine ``Version:`` file headers, juniper-data's and
juniper-canopy's ``__init__.py`` fallback strings. This script lands those as a
follow-up signed commit on the proposal branch, pinning ``expectedHeadOid`` to the
branch's CURRENT head so a concurrent push fails loudly instead of being clobbered.

Usage
-----
    python3 util/ad-hoc/2026-09-08_push_signed_commit.py \
        --repo juniper-data-client --branch release/juniper-data-client-v0.5.0 \
        --add /local/edited/__init__.py:juniper_data_client/__init__.py \
        --message "chore(release): bump the carriers the train does not know about" \
        [--commit-body-file body.txt] [--delete repo/path] [--owner pcalnon] [--dry-run]

Exit 0 = commit landed (or --dry-run), 1 = refused (branch missing / no changes),
2 = hard error. Reads local file contents in binary and base64-encodes them, so any
file type is fine.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # util/ -- for open_signed_pr

import open_signed_pr as osp  # noqa: E402


def branch_head(owner: str, repo: str, branch: str) -> str | None:
    """The branch's current head sha, or None when the ref does not exist."""
    try:
        out = osp.gh(["api", f"repos/{owner}/{repo}/git/ref/heads/{branch}", "--jq", ".object.sha"])
    except osp.GhError:
        return None
    return out.strip() or None


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--owner", default=os.environ.get("JUNIPER_RELEASE_TRAIN_OWNER", "pcalnon"))
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--add", action="append", default=[], metavar="LOCAL:REPOPATH")
    ap.add_argument("--delete", action="append", default=[], metavar="REPOPATH")
    ap.add_argument("--message", required=True, help="commit headline")
    ap.add_argument("--commit-body", default=None)
    ap.add_argument("--commit-body-file", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not args.add and not args.delete:
        print("refused: nothing to add or delete", file=sys.stderr)
        return 1
    if args.commit_body and args.commit_body_file:
        print("refused: --commit-body and --commit-body-file are mutually exclusive", file=sys.stderr)
        return 2
    body = args.commit_body
    if args.commit_body_file:
        body = Path(args.commit_body_file).read_text(encoding="utf-8")

    additions = []
    for spec in args.add:
        local, repo_path = osp.parse_add(spec)
        raw = Path(local).read_bytes()
        additions.append((repo_path, base64.b64encode(raw).decode("ascii")))

    head = branch_head(args.owner, args.repo, args.branch)
    if head is None:
        print(f"refused: branch {args.branch} does not exist on {args.owner}/{args.repo}", file=sys.stderr)
        return 1

    print(f"repo={args.owner}/{args.repo} branch={args.branch} head={head}")
    for repo_path, _ in additions:
        print(f"  add    {repo_path}")
    for repo_path in args.delete:
        print(f"  delete {repo_path}")
    if args.dry_run:
        print("dry-run: no commit created")
        return 0

    try:
        oid = osp.create_signed_commit(args.owner, args.repo, args.branch, args.message, additions, head, deletions=args.delete or None, commit_body=body)
    except osp.GhError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"commit {oid} landed on {args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
