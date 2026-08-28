#!/usr/bin/env python3
"""
Push a GitHub-signed fixup commit onto an EXISTING PR branch.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- tooling gap filler
Retire when: superseded by an `--update` mode on util/open_signed_pr.py, or RETAINED as
             provenance per the owner policy (2026-08-25)
Related: util/open_signed_pr.py (whose create_signed_commit this reuses verbatim)

Why this exists
---------------
``required_signatures`` means a local ``git push`` cannot land a mergeable commit, so
``util/open_signed_pr.py`` is the only way to write to a branch. But it deliberately REFUSES
when the branch or an open PR already exists -- a dup-guard against concurrent sessions. That
is the right default for opening a PR and the wrong one for fixing the PR you just opened: a
CI failure on your own branch (a black reformat, a lint nit) leaves no supported path forward
except closing the PR and re-cutting it under a new name, which discards the review thread.

This fills that gap without weakening the dup-guard: it targets a branch that must ALREADY
exist, pins ``expectedHeadOid`` to that branch's current head so a concurrent write fails
loudly rather than being clobbered, and reuses ``open_signed_pr.create_signed_commit``
unmodified rather than re-implementing the mutation.

Usage
-----
    python3 util/ad-hoc/2026-08-26_push_signed_fixup.py \\
        --repo juniper-ml --branch fix/some-branch \\
        --add tests/test_x.py:tests/test_x.py \\
        --message "style: black"

Exit 0 = commit pushed, 1 = refused (branch missing), 2 = hard error.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_spec = importlib.util.spec_from_file_location("open_signed_pr", REPO_ROOT / "util" / "open_signed_pr.py")
osp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(osp)


def branch_head(owner: str, repo: str, branch: str) -> "str | None":
    """The branch's current head sha, or None when the branch does not exist."""
    try:
        out = osp.gh(["api", f"repos/{owner}/{repo}/git/ref/heads/{branch}"])
    except osp.GhError:
        return None
    try:
        return (json.loads(out).get("object") or {}).get("sha")
    except ValueError:
        return None


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--owner", default="pcalnon")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--add", action="append", default=[], metavar="LOCAL:REPOPATH", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--commit-body", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    head = branch_head(args.owner, args.repo, args.branch)
    if head is None:
        print(f"REFUSED: {args.owner}/{args.repo}:{args.branch} does not exist — use open_signed_pr.py to create it", file=sys.stderr)
        return 1

    additions = []
    for spec in args.add:
        local, _, repo_path = spec.partition(":")
        if not repo_path:
            print(f"ERROR: --add needs LOCAL:REPOPATH, got {spec!r}", file=sys.stderr)
            return 2
        path = Path(local).expanduser()
        if not path.is_file():
            print(f"ERROR: {path} is not a file", file=sys.stderr)
            return 2
        additions.append((repo_path, base64.b64encode(path.read_bytes()).decode("ascii")))

    if args.dry_run:
        print(f"DRY-RUN {args.owner}/{args.repo}:{args.branch} @ {head[:12]}")
        for repo_path, contents in additions:
            print(f"  add {repo_path} ({len(base64.b64decode(contents))} bytes)")
        print(f"  commit {args.message}")
        return 0

    oid = osp.create_signed_commit(args.owner, args.repo, args.branch, args.message, additions, head, commit_body=args.commit_body)
    print(f"signed fixup {oid[:12]} on {args.owner}/{args.repo}:{args.branch} (was {head[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
