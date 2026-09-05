#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc automation (fleet PR disposition)
# File Name:     2026-09-06_superseded_method_presence.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Before closing a superseded fleet PR: is every test METHOD it adds present on main?
#
#   `2026-09-05_fleet_harvest_postmerge_verify.py` answers a LINE question -- which added lines
#   are absent from the merged tree. That is the right question for content fidelity and the
#   WRONG one for disposition, because a carrier legitimately rewrites the prose: a wiring
#   comment, a docstring, an AGENTS.md entry. Measured 2026-09-06 on juniper-ml #1629: 16 of
#   187 lines "absent", every one of them comment text, with all six test methods present.
#
#   Reading that as loss would keep six finished PRs open forever. Reading it as noise would
#   miss a genuinely dropped test. So ask the question whose unit matches the thing being
#   disposed of: the METHOD is what the PR contributes, so the method is what must be found.
#
# Usage:
#   2026-09-06_superseded_method_presence.py <repo-dir> <pr> [<pr> ...]
#   2026-09-06_superseded_method_presence.py . 1629 1633 1637
#
# Exit: 0 when every method of every PR is present; 1 when any is missing.
#####################################################################################################################################################################################################
"""Confirm a superseded PR's test methods all reached main before closing it."""

from __future__ import annotations

import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from pathlib import Path

DEF = re.compile(r"^\s*(?:async\s+)?def (test_[A-Za-z0-9_]+)", re.M)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=300, check=False)


def pr_methods(repo: Path, pr: int) -> dict[str, set[str]]:
    """`{path: {method, ...}}` for every test file the PR touches."""
    ref = f"refs/superseded/pr{pr}"
    git(repo, "fetch", "origin", f"pull/{pr}/head:{ref}", "--force")
    base = git(repo, "merge-base", "HEAD", ref).stdout.strip()
    if not base:
        return {}
    changed = [p for p in git(repo, "diff", "--name-only", f"{base}..{ref}").stdout.splitlines() if p.startswith("tests/") and p.endswith(".py")]
    out: dict[str, set[str]] = {}
    for path in changed:
        theirs = set(DEF.findall(git(repo, "show", f"{ref}:{path}").stdout))
        base_names = set(DEF.findall(git(repo, "show", f"{base}:{path}").stdout))
        added = theirs - base_names
        if added:
            out[path] = added
    return out


def on_main(repo: Path) -> set[str]:
    """Every test method name anywhere under tests/ on the current checkout."""
    names: set[str] = set()
    for path in sorted((repo / "tests").glob("test_*.py")):
        names |= set(DEF.findall(path.read_text(encoding="utf-8", errors="replace")))
    return names


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    repo = Path(args[0]).resolve()
    present = on_main(repo)
    worst = 0
    for pr in (int(a) for a in args[1:]):
        adds = pr_methods(repo, pr)
        wanted = {name for names in adds.values() for name in names}
        missing = sorted(wanted - present)
        status = "OK  " if not missing else "MISS"
        print(f"[{status}] #{pr}: {len(wanted) - len(missing)}/{len(wanted)} methods present")
        for path, names in sorted(adds.items()):
            gone = sorted(set(names) - present)
            if gone:
                print(f"    {path}: {len(gone)} absent -> {', '.join(gone)}")
        worst = max(worst, 1 if missing else 0)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
