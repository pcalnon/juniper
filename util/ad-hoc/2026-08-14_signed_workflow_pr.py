"""
Open a PR on any Juniper repo whose commit is GitHub-signed (createCommitOnBranch).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-14
Status: ad-hoc -- migration
Retire when: the ml#1099 runner-commit signing fan-out has landed in all 9 repos
             (lockfile lanes + agents-md-touch-up lanes) and no further
             cross-repo workflow PRs are needed for this arc.
Related: juniper-ml#1099, juniper-cascor#518 (live repro), juniper-ml#1096
         (propose.py's create_signed_commit -- the reference implementation)

Why this exists
---------------
The 2026-08-12 branch-protection normalization added ``required_signatures`` to
all 9 Juniper repos. A local ``git commit`` on a runner is unsigned, so every
automation that pushes one now produces an UNMERGEABLE branch -- and an unsigned
commit anywhere in the branch history blocks the merge (squash does not rescue
it). ml#1096 fixed that for ``propose.py``; this script is the vehicle for
fixing the remaining lanes, and it deliberately uses the same mechanism it is
shipping: every commit it makes is created through the GitHub API, which GitHub
signs, so these fix-PRs are themselves mergeable under the new rule.

Usage
-----
    python util/ad-hoc/2026-08-14_signed_workflow_pr.py \
        --repo juniper-cascor \
        --branch fix/lockfile-lane-signed-commit \
        --add /path/to/new-lockfile-update.yml:.github/workflows/lockfile-update.yml \
        --message "ci(lockfile): sign the regen commit and skip release/** heads" \
        --title "ci(lockfile): sign the regen commit and skip release/** heads" \
        --body-file /path/to/body.md \
        [--base main] [--owner pcalnon] [--dry-run]

``--add`` is repeatable (LOCAL_PATH:REPO_PATH). Exit 0 = PR open (or already
open), 1 = refused/dup, 2 = hard error.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile

CREATE_COMMIT_MUTATION = "mutation($input: CreateCommitOnBranchInput!) { createCommitOnBranch(input: $input) { commit { oid url } } }"


class GhError(RuntimeError):
    """A ``gh`` invocation failed or returned something unusable."""


def gh(args: list, check: bool = True) -> str:
    """Run ``gh`` and return stdout. Raises GhError on nonzero exit."""
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise GhError(f"gh {' '.join(args)} -> exit {proc.returncode}\n{proc.stderr.strip()}")
    return proc.stdout


def resolve_base_sha(owner: str, repo: str, base: str) -> str:
    out = gh(["api", f"repos/{owner}/{repo}/git/ref/heads/{base}", "--jq", ".object.sha"])
    sha = out.strip()
    if not sha:
        raise GhError(f"could not resolve {owner}/{repo}@{base}")
    return sha


def branch_exists(owner: str, repo: str, branch: str) -> bool:
    proc = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/git/ref/heads/{branch}"],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def create_branch(owner: str, repo: str, branch: str, sha: str) -> None:
    # Explicit ref= is mandatory (the ml#770 R7 lesson: an omitted/empty ref
    # must never be deferred to the live API).
    gh(
        [
            "api",
            f"repos/{owner}/{repo}/git/refs",
            "-X",
            "POST",
            "-f",
            f"ref=refs/heads/{branch}",
            "-f",
            f"sha={sha}",
        ]
    )


def create_signed_commit(owner: str, repo: str, branch: str, message: str, additions: list, expected_head_oid: str) -> str:
    """Land ``additions`` as ONE GitHub-signed commit on ``branch``.

    Mirrors util/release_train/propose.py::create_signed_commit -- the whole
    CreateCommitOnBranchInput goes through as a single ``$input`` object via a
    JSON request body, because ``gh api graphql -f k=v`` can only pass scalars
    and ``fileChanges.additions`` is a list.
    """
    body = {
        "query": CREATE_COMMIT_MUTATION,
        "variables": {
            "input": {
                "branch": {"repositoryNameWithOwner": f"{owner}/{repo}", "branchName": branch},
                "message": {"headline": message},
                "expectedHeadOid": expected_head_oid,
                "fileChanges": {"additions": [{"path": path, "contents": contents} for path, contents in additions]},
            }
        },
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
        json.dump(body, fh)
        body_path = fh.name
    try:
        out = gh(["api", "graphql", "--input", body_path])
    finally:
        try:
            os.unlink(body_path)
        except OSError:
            # Best-effort cleanup of our own tempfile; the commit either landed
            # or failed already and a stray temp file must not mask that.
            pass
    try:
        data = json.loads(out) if out else {}
    except ValueError as exc:
        raise GhError(f"createCommitOnBranch returned non-JSON for {repo}") from exc
    if data.get("errors"):
        raise GhError(f"createCommitOnBranch failed for {repo}: {data['errors']}")
    commit = (((data.get("data") or {}).get("createCommitOnBranch") or {}).get("commit") or {})
    if not commit.get("oid"):
        raise GhError(f"createCommitOnBranch returned no commit oid for {repo}")
    return commit["oid"]


def find_open_pr(owner: str, repo: str, branch: str) -> str:
    out = gh(
        ["pr", "list", "--repo", f"{owner}/{repo}", "--head", branch, "--state", "open", "--json", "url", "--jq", ".[0].url"],
        check=False,
    )
    return out.strip()


def parse_add(spec: str) -> tuple:
    local, sep, repo_path = spec.partition(":")
    if not sep or not local or not repo_path:
        raise argparse.ArgumentTypeError(f"--add expects LOCAL_PATH:REPO_PATH, got {spec!r}")
    return (local, repo_path)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--add", action="append", required=True, type=parse_add, metavar="LOCAL:REPOPATH")
    ap.add_argument("--message", required=True, help="commit headline")
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    additions = []
    for local, repo_path in args.add:
        try:
            with open(local, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read {local}: {exc}", file=sys.stderr)
            return 2
        additions.append((repo_path, base64.b64encode(raw).decode("ascii")))

    try:
        with open(args.body_file, encoding="utf-8") as fh:
            body = fh.read()
    except OSError as exc:
        print(f"ERROR: cannot read --body-file {args.body_file}: {exc}", file=sys.stderr)
        return 2

    slug = f"{args.owner}/{args.repo}"
    try:
        existing = find_open_pr(args.owner, args.repo, args.branch)
        if existing:
            print(f"DUP-GUARD: an open PR already exists for {slug}:{args.branch} -> {existing}")
            return 1

        base_sha = resolve_base_sha(args.owner, args.repo, args.base)

        if args.dry_run:
            print(f"DRY-RUN {slug}")
            print(f"  base   {args.base} @ {base_sha}")
            print(f"  branch {args.branch}")
            for repo_path, contents in additions:
                print(f"  add    {repo_path} ({len(base64.b64decode(contents))} bytes)")
            print(f"  commit {args.message}")
            print(f"  title  {args.title}")
            print("  (nothing written)")
            return 0

        if branch_exists(args.owner, args.repo, args.branch):
            print(f"REFUSED: branch {args.branch} already exists on {slug}; delete it or pick another name.")
            return 1
        create_branch(args.owner, args.repo, args.branch, base_sha)

        oid = create_signed_commit(args.owner, args.repo, args.branch, args.message, additions, base_sha)
        print(f"signed commit {oid[:12]} on {slug}:{args.branch}")

        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as fh:
            fh.write(body)
            body_path = fh.name
        try:
            url = gh(
                [
                    "pr", "create",
                    "--repo", slug,
                    "--base", args.base,
                    "--head", args.branch,
                    "--title", args.title,
                    "--body-file", body_path,
                ]
            ).strip()
        finally:
            try:
                os.unlink(body_path)
            except OSError:
                pass
        print(f"PR: {url}")
        return 0
    except GhError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
