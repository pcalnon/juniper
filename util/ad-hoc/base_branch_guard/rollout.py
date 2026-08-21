#!/usr/bin/env python3
"""Fan the PR base-branch guard out to the Juniper repos (ml#434 part 1).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc migration tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- migration (one-off fan-out)
Retire when: the guard is present on all 9 repos and ml#434 is closed.
Related:     ml#434; util/open_signed_pr.py;
             notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_PR-BASE-BRANCH-GUARD-AUDIT.md

Drives `util/open_signed_pr.py` once per repo, because a runner-side / local commit is
UNSIGNED and `required_signatures` rejects it fleet-wide -- an unsigned commit anywhere in a
branch's history blocks the merge and squash does not rescue it. The GraphQL
`createCommitOnBranch` path that open_signed_pr.py uses produces a GitHub-signed commit and
needs no checkout, which also makes it the only option from inside a single-worktree session.

Sequencing note (this is part 1 of 2, and the order is load-bearing)
--------------------------------------------------------------------
This lands the WORKFLOW only. Making `Guard PR base branch` a required status check is a
separate, owner-gated ruleset write that must come AFTER these merge and the context is
observed reporting. Requiring a context nothing publishes yet leaves every open PR stuck at
"expected" with nothing red -- the cascor#515 shape. `2026-08-20_require_context_safely.py`
enforces that ordering by refusing to require an unobserved context.

Usage
-----
    python3 util/ad-hoc/base_branch_guard/rollout.py --dry-run
    python3 util/ad-hoc/base_branch_guard/rollout.py
    python3 util/ad-hoc/base_branch_guard/rollout.py --repo juniper-cascor
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 - drives the in-repo signed-PR helper
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
OPENER = REPO_ROOT / "util" / "open_signed_pr.py"
WORKFLOW = HERE / "pr-base-branch-guard.yml"
BODY = HERE / "PR_BODY.md"

BRANCH = "ci/pr-base-branch-guard"
DEST = ".github/workflows/pr-base-branch-guard.yml"
MESSAGE = "ci: add the PR base-branch guard (ml#434 part 1)"
TITLE = "ci: add the PR base-branch guard"

# juniper-recurrence already has it (it is the source). juniper-deploy was the canary and
# is done; it stays in the list because the opener is dup-guarded and will simply refuse.
TARGETS = [
    "juniper-deploy",
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", action="append", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    repos = args.repo or TARGETS

    for p in (OPENER, WORKFLOW, BODY):
        if not p.exists():
            print(f"FATAL: missing {p}", file=sys.stderr)
            return 2

    results = []
    for repo in repos:
        cmd = [
            sys.executable,
            str(OPENER),
            "--repo",
            repo,
            "--branch",
            BRANCH,
            "--add",
            f"{WORKFLOW}:{DEST}",
            "--message",
            MESSAGE,
            "--title",
            TITLE,
            "--body-file",
            str(BODY),
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        print("=" * 76)
        print(f"{repo}")
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # nosec B603
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        if out:
            print("  " + "\n  ".join(out.splitlines()))
        if err:
            print("  " + "\n  ".join(err.splitlines()))
        # exit 1 from the opener is a REFUSAL (dup PR / branch exists), not a crash --
        # re-running the fan-out must be safe, so refusals are recorded, not fatal.
        results.append((repo, p.returncode))

    print()
    print("=" * 76)
    ok = [r for r, c in results if c == 0]
    refused = [r for r, c in results if c == 1]
    hard = [r for r, c in results if c not in (0, 1)]
    print(f"opened/dry-run OK : {len(ok)}  {', '.join(ok)}")
    if refused:
        print(f"refused (dup)     : {len(refused)}  {', '.join(refused)}")
    if hard:
        print(f"HARD ERROR        : {len(hard)}  {', '.join(hard)}")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
