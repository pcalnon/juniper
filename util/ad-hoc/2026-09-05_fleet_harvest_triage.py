#!/usr/bin/env python3
"""2026-09-05_fleet_harvest_triage.py -- what would this PR ACTUALLY add to main?

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

A fleet PR's advertised diff describes the tree its branch was cut from, not the tree
that exists now.  juniper-canopy#580 advertised ten files; **nine were already on
`main`** and only one was new, so "merge it" meant hand-resolving conflicts across five
files -- including `main.py` -- to recover a single test file.  juniper-data#351
advertised three; two were byte-identical to `main`.

When 84 of 90 open PRs read CONFLICT (juniper-ml, 2026-09-05), the merge verdict has
stopped carrying information: it says the branch is stale, which is already known.  The
question that still discriminates is **what content does this PR hold that `main` does
not**, and that is answered per FILE, against `main`, without merging anything.

WHAT IT REPORTS, PER PR

    NEW       n files absent from main entirely  -- the harvestable content
    DIVERGED  n files present but whose content differs
    SAME      n files byte-identical to main     -- nothing to carry
    EMPTY     every advertised file is already on main -> the PR is REDUNDANT

`EMPTY` is the finding that pays for this script: a PR whose whole diff is already on
`main` can be CLOSED without reading it, and a fleet that regenerates docs for work
that later landed produces a lot of them.

WHAT IT DELIBERATELY DOES NOT DO

It does not judge whether the NEW content is correct, current, or desirable -- see
`2026-09-05_fleet_provably_clean.py`'s six gates for mechanical safety, and note that
gate-clean is not the same as true (juniper-data#329 and #349 passed every gate while
documenting superseded security bounds).  A file being absent from `main` is a reason
to LOOK at it, not a reason to take it.

Usage:
    2026-09-05_fleet_harvest_triage.py --repo pcalnon/juniper-ml [--pr N ...]
                                       [--author app/cursor] [--limit N] [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 -- fixed argv gh/git invocations, no shell
import sys


def _run(cmd: list, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=180)  # nosec B603


def _gh_json(args: list):
    cp = _run(["gh", *args])
    if cp.returncode != 0:
        return None
    try:
        return json.loads(cp.stdout)
    except json.JSONDecodeError:
        return None


def _blob_sha(repo_dir: str, ref: str, path: str) -> str | None:
    """The blob SHA of ``path`` at ``ref``, or None when the path is absent there.

    Comparing SHAs rather than diffing is what makes this cheap enough for 90 PRs:
    git already computed them, and equality of content is exactly what a blob SHA is.
    """
    cp = _run(["git", "-C", repo_dir, "rev-parse", f"{ref}:{path}"])
    return cp.stdout.strip() if cp.returncode == 0 else None


def triage_pr(repo: str, repo_dir: str, pr: int, base_ref: str) -> dict:
    meta = _gh_json(["pr", "view", str(pr), "--repo", repo, "--json", "title,files,isDraft,headRefOid"])
    if meta is None:
        return {"pr": pr, "error": "gh pr view failed"}

    # The PR head must be local before its blobs can be read. A fleet branch is often
    # not fetched, and a dangling head resolves without being an ancestor of anything
    # -- so fetch by pull ref, not by branch name.
    _run(["git", "-C", repo_dir, "fetch", "origin", f"pull/{pr}/head:refs/fleet-triage/pr{pr}", "--force"])
    head = f"refs/fleet-triage/pr{pr}"

    new, diverged, same, unreadable = [], [], [], []
    for f in meta.get("files", []):
        path = f["path"]
        head_sha = _blob_sha(repo_dir, head, path)
        base_sha = _blob_sha(repo_dir, base_ref, path)
        if head_sha is None:
            # Deleted by the PR, or unreadable at its head.
            unreadable.append(path)
        elif base_sha is None:
            new.append(path)
        elif head_sha == base_sha:
            same.append(path)
        else:
            diverged.append(path)

    return {
        "pr": pr,
        "title": meta.get("title", ""),
        "draft": meta.get("isDraft"),
        "new": new,
        "diverged": diverged,
        "same": same,
        "unreadable": unreadable,
        "redundant": not new and not diverged and not unreadable,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--repo-dir", default=".", help="local checkout to read blobs from")
    ap.add_argument("--pr", type=int, action="append", help="triage only these PRs")
    ap.add_argument("--author", default=None, help="restrict the open-PR sweep to this author")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    _run(["git", "-C", args.repo_dir, "fetch", "origin", "--quiet"])

    if args.pr:
        prs = args.pr
    else:
        listing = ["pr", "list", "--repo", args.repo, "--state", "open", "--limit", str(args.limit), "--json", "number"]
        if args.author:
            listing += ["--author", args.author]
        rows = _gh_json(listing) or []
        prs = [r["number"] for r in rows]

    results = [triage_pr(args.repo, args.repo_dir, pr, args.base) for pr in prs]

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    redundant = [r for r in results if r.get("redundant")]
    harvestable = [r for r in results if r.get("new")]
    diverged_only = [r for r in results if not r.get("new") and r.get("diverged")]

    print(f"triaged {len(results)} PRs against {args.base}\n")
    print(f"  REDUNDANT (every advertised file already on {args.base}):  {len(redundant)}")
    print(f"  HARVESTABLE (>=1 file absent from {args.base}):            {len(harvestable)}")
    print(f"  DIVERGED ONLY (no new file; edits existing ones):          {len(diverged_only)}\n")

    if redundant:
        print("--- REDUNDANT: closeable without reading ---")
        for r in redundant:
            print(f"  #{r['pr']}  {len(r['same'])} files, all identical  {r['title'][:60]}")
        print()

    if harvestable:
        print("--- HARVESTABLE ---")
        for r in sorted(harvestable, key=lambda x: len(x["new"])):
            ratio = f"{len(r['new'])}/{len(r['new']) + len(r['diverged']) + len(r['same'])}"
            print(f"  #{r['pr']}  new {ratio:<7} {r['title'][:58]}")
            for p in r["new"][:4]:
                print(f"           + {p}")
        print()

    if diverged_only:
        print("--- DIVERGED ONLY (edits to files main already has) ---")
        for r in diverged_only:
            print(f"  #{r['pr']}  {len(r['diverged'])} changed  {r['title'][:58]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
