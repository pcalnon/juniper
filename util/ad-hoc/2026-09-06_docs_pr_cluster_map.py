#!/usr/bin/env python3
"""
Cluster a set of fleet docs PRs by the files they touch, and flag the ones that need reading.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 35 juniper-ml docs PRs left after the code harvest

A docs PR carries no test, so nothing goes red when it lands a claim `main` has since reversed.
Two measured failures shape what this reports:

* **Whole-line union fragments tables.** Ten PRs against drifted doc versions produced 49
  headerless table fragments -- damage that scales with DOC-VERSION DRIFT, not PR count. So the
  per-file `versions` count matters more than the PR count: a file touched by eight PRs whose
  bases are eight different commits is the dangerous one.
* **"Provably clean" is not "correct to merge."** Six gates passed two docs PRs documenting
  SUPERSEDED security bounds. Passing gates says the prose is well-formed, not that it is true.

So this measures, per file: how many PRs touch it, how many DISTINCT merge-bases those PRs sit
on, and how far each base is behind `origin/main`. It decides nothing -- it says which files can
be batched and which have to be read against the source.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- fixed argv git/gh invocations, no shell
import sys
from collections import defaultdict
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=300, check=False).stdout


def gh_json(repo: Path, *args: str) -> object:
    out = subprocess.run(["gh", *args], cwd=repo, capture_output=True, text=True, timeout=300, check=False)
    return json.loads(out.stdout) if out.stdout.strip() else {}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    repo = Path(args[0]).resolve()
    prs = [int(a) for a in args[1:]]

    by_file: dict[str, list[int]] = defaultdict(list)
    bases: dict[int, str] = {}
    behind: dict[int, int] = {}
    titles: dict[int, str] = {}

    for pr in prs:
        ref = f"refs/superseded/pr{pr}"
        git(repo, "fetch", "origin", f"pull/{pr}/head:{ref}", "--force")
        base = git(repo, "merge-base", "origin/main", ref).strip()
        if not base:
            print(f"#{pr}: no merge-base", file=sys.stderr)
            continue
        bases[pr] = base
        behind[pr] = len(git(repo, "rev-list", f"{base}..origin/main").split())
        meta = gh_json(repo, "pr", "view", str(pr), "--json", "title")
        titles[pr] = meta.get("title", "") if isinstance(meta, dict) else ""
        for path in git(repo, "diff", "--name-only", f"{base}..{ref}").splitlines():
            if path.endswith(".md"):
                by_file[path].append(pr)

    print(f"{'file':<78} {'PRs':>4} {'bases':>6} {'max behind':>11}")
    print("-" * 102)
    hot: list[str] = []
    for path, owners in sorted(by_file.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        distinct = len({bases[p] for p in owners})
        worst = max(behind[p] for p in owners)
        print(f"{path:<78} {len(owners):>4} {distinct:>6} {worst:>11}")
        if distinct > 1:
            hot.append(path)
            print(f"{'':<78} {'':>4} -> {sorted(owners)}")

    print()
    print(f"{len(by_file)} markdown file(s) across {len(prs)} PR(s); {len(hot)} touched from MORE THAN ONE base.")
    print("A single-base file can be batched. A multi-base file is where the 49 headerless")
    print("table fragments came from -- take those one at a time, against the current file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
