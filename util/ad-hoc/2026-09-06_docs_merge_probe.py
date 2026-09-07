#!/usr/bin/env python3
"""
Probe how a sequential 3-WAY MERGE of the docs fleet behaves, without keeping the result.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 35 juniper-ml docs PRs; `2026-09-06_docs_pr_cluster_map.py`

The previous consolidation fragmented 49 table rows, and the diagnosis stuck to the union: a
whole-line union's unit is the LINE, while a table row's identity is the ROW, so two halves of
one row arrive as two broken rows.

A 3-way merge does not share that defect -- it has the base, so it can tell an added row from a
changed one. The question is therefore not "union or not" but "how much does git resolve on its
own, and what is left". This answers that and throws the tree away: it merges each PR onto an
accumulating scratch branch in the given order, records conflicted paths per step, and aborts
each conflict rather than resolving it, so the count is the count of REAL decisions.

Aborting means later steps merge onto a tree missing the aborted PR's content -- so the numbers
are a LOWER bound on what a real run resolves, and an upper bound on how independent the PRs are.
Run it before committing to an order, not instead of doing the merges.
"""

from __future__ import annotations

import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from collections import Counter
from pathlib import Path


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=600, check=False)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    repo = Path(args[0]).resolve()
    prs = [int(a) for a in args[1:]]

    scratch = "refs/heads/probe/docs-merge-order"
    git(repo, "branch", "-f", "probe/docs-merge-order", "origin/main")
    start = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    git(repo, "checkout", "probe/docs-merge-order")

    clean, conflicted = 0, 0
    paths: Counter[str] = Counter()
    try:
        for pr in prs:
            ref = f"refs/superseded/pr{pr}"
            git(repo, "fetch", "origin", f"pull/{pr}/head:{ref}", "--force")
            res = git(repo, "merge", "--no-edit", "--no-ff", ref)
            if res.returncode == 0:
                clean += 1
                print(f"[CLEAN] #{pr}")
                continue
            conflicted += 1
            files = [ln for ln in git(repo, "diff", "--name-only", "--diff-filter=U").stdout.splitlines() if ln]
            for f in files:
                paths[f] += 1
            print(f"[CONFL] #{pr}: {', '.join(files) or '(no unmerged paths -- other failure)'}")
            git(repo, "merge", "--abort")
    finally:
        git(repo, "checkout", start)
        git(repo, "branch", "-D", "probe/docs-merge-order")
        git(repo, "update-ref", "-d", scratch)

    print()
    print(f"{clean} merged clean, {conflicted} conflicted (lower bound -- aborted PRs' content is absent from later merges)")
    print()
    for path, n in paths.most_common():
        print(f"    {n:>3}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
