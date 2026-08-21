"""
Open a PR on any Juniper repo whose commit is GitHub-signed (createCommitOnBranch).

Project: juniper-ml
Sub-Project: cross-repo tooling
Author: Paul Calnon
Created: 2026-08-14
Status: permanent utility (promoted from util/ad-hoc/ after the ml#1099 fan-out)
Related: juniper-ml#1099 (the fan-out this was built for), juniper-ml#1096
         (util/release_train/propose.py's create_signed_commit -- the reference
         implementation this mirrors)

Why this exists
---------------
The 2026-08-12 branch-protection normalization added ``required_signatures`` to
all 9 Juniper repos. GPG/YubiKey signing is not available to a hosted runner, and
an unsigned commit ANYWHERE in a branch's history blocks the merge -- squash does
not rescue it. The portable way to produce a signed commit without a key is the
GraphQL ``createCommitOnBranch`` mutation: GitHub signs commits authored through
its API.

That makes this useful well beyond the original fan-out. Any time you need to land
a change on a sibling repo -- a workflow fix, a pin bump, a config correction --
without cloning it, this opens the branch, the signed commit, and the PR in three
API calls. It needs no working tree, so it is also the sandbox-friendly path when
a session is confined to one worktree and cannot commit in sibling checkouts.

Usage
-----
    python util/open_signed_pr.py \\
        --repo juniper-cascor \\
        --branch ci/lockfile-lane-signed-commit \\
        --add /local/path/lockfile-update.yml:.github/workflows/lockfile-update.yml \\
        --message "ci(lockfile): sign the regen commit" \\
        --title "ci(lockfile): sign the regen commit" \\
        --body-file /local/path/body.md \\
        [--delete path/to/remove] [--base main] [--owner pcalnon] [--dry-run]

``--add`` is repeatable (LOCAL_PATH:REPO_PATH) and ``--delete`` is repeatable
(REPO_PATH); together they express a file move. At least one of the two is
required. Exit 0 = PR opened (or --dry-run), 1 = refused (dup PR / branch exists),
2 = hard error.

Safety contract
---------------
* Refuses when an open PR already exists for the branch (concurrent sessions are
  a real hazard in this fleet) and when the branch already exists -- it never
  force-updates someone else's ref.
* ``expectedHeadOid`` is pinned to the resolved base sha, so a concurrent push
  makes the mutation fail loudly rather than clobber.
* ``--dry-run`` performs the read-only resolution and prints the plan; it creates
  no branch, no commit and no PR.

Tests: ``tests/test_open_signed_pr.py`` (hermetic; ``gh`` is a PATH stub).
``util/`` is not covered by the pre-commit Python hooks, so that suite is the gate.
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


def create_signed_commit(owner: str, repo: str, branch: str, message: str, additions: list, expected_head_oid: str, deletions: "list | None" = None, commit_body: "str | None" = None) -> str:
    """Land ``additions`` (and any ``deletions``) as ONE GitHub-signed commit on ``branch``.

    Mirrors util/release_train/propose.py::create_signed_commit -- the whole
    CreateCommitOnBranchInput goes through as a single ``$input`` object via a
    JSON request body, because ``gh api graphql -f k=v`` can only pass scalars
    and ``fileChanges.additions`` is a list.

    ``deletions`` is omitted from the payload entirely when empty rather than sent
    as ``[]``, keeping the request byte-identical to the additions-only form.

    ``commit_body`` fills the message BODY. Without it this helper could only set a
    headline, which meant it could not carry a **commit trailer** -- and trailers are
    the only way to waive a sequence-safety finding
    (``Allow-Symbol-Loss:`` / ``Allow-Docs-Rewrite:``). Since ``required_signatures``
    makes this script the only way to land a commit at all, "no body" meant "no waiver",
    which meant closing and re-cutting the PR by hand. The trailer must live in a commit
    message rather than PR prose because it has to survive the squash-merge, and it must
    be in the FIRST commit because squash keeps only that message.
    """
    file_changes: dict = {"additions": [{"path": path, "contents": contents} for path, contents in additions]}
    if deletions:
        file_changes["deletions"] = [{"path": path} for path in deletions]
    body = {
        "query": CREATE_COMMIT_MUTATION,
        "variables": {
            "input": {
                "branch": {"repositoryNameWithOwner": f"{owner}/{repo}", "branchName": branch},
                "message": ({"headline": message, "body": commit_body} if commit_body else {"headline": message}),
                "expectedHeadOid": expected_head_oid,
                "fileChanges": file_changes,
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
    ap.add_argument("--add", action="append", default=[], type=parse_add, metavar="LOCAL:REPOPATH")
    ap.add_argument("--delete", action="append", default=[], metavar="REPOPATH", help="repo path to delete in the same commit (repeatable)")
    ap.add_argument("--message", required=True, help="commit headline")
    ap.add_argument(
        "--commit-body",
        default=None,
        help="commit message BODY -- put sequence-safety waiver trailers here "
        "(Allow-Symbol-Loss: method:Class.name), not in the PR description; "
        "the trailer must survive squash-merge",
    )
    ap.add_argument(
        "--commit-body-file",
        default=None,
        help="read the commit message body from a file (mutually exclusive with --commit-body)",
    )
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not args.add and not args.delete:
        print("ERROR: nothing to commit -- pass at least one --add or --delete.", file=sys.stderr)
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

    if args.commit_body and args.commit_body_file:
        print("ERROR: --commit-body and --commit-body-file are mutually exclusive", file=sys.stderr)
        return 2
    commit_body = args.commit_body
    if args.commit_body_file:
        try:
            with open(args.commit_body_file, encoding="utf-8") as fh:
                commit_body = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read --commit-body-file {args.commit_body_file}: {exc}", file=sys.stderr)
            return 2

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
            for repo_path in args.delete:
                print(f"  delete {repo_path}")
            print(f"  commit {args.message}")
            if commit_body:
                print("  commit body:")
                for line in commit_body.splitlines():
                    print(f"    {line}")
            print(f"  title  {args.title}")
            print("  (nothing written)")
            return 0

        if branch_exists(args.owner, args.repo, args.branch):
            print(f"REFUSED: branch {args.branch} already exists on {slug}; delete it or pick another name.")
            return 1
        create_branch(args.owner, args.repo, args.branch, base_sha)

        oid = create_signed_commit(
            args.owner, args.repo, args.branch, args.message, additions, base_sha, args.delete, commit_body
        )
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
            except OSError as exc:
                print(f"WARNING: failed to remove temporary body file {body_path}: {exc}", file=sys.stderr)
        print(f"PR: {url}")
        return 0
    except GhError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
