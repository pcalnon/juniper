#!/usr/bin/env python3
"""Re-derive the P5 arc's net AGENTS.md delta from git, per repo.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (plan §P5 step e — record-of-truth verification)
Author:      Paul Calnon
License:     MIT

Why this exists.

The §P5 banner and the ml#1326 tracker title are the arc's two records of truth, and §4a
forbids leaving either stale. Both were rewritten on 2026-08-31 from a handoff table. A
handoff table is prose ABOUT the repos; this re-derives the same figures FROM them, so the
banner cites a number someone can reproduce.

Method. For each governed repo, measure ``AGENTS.md`` in CHARACTERS (the unit the ceiling
uses) at two refs:

  * ARC START -- the repo's memory-budget PORT squash commit. The port added
    ``conf/memory_budget.json`` and the workflow job; it did not touch ``AGENTS.md``, so the
    file's size at that commit is its size on the day the arc reached the repo. This is
    deliberately NOT the ``ceiling_chars`` seed recorded in ``conf/memory_budget.json``:
    that seed was computed before the port merged and is 176 chars stale for canopy.

  * NOW -- ``origin/main``, after a ``git fetch``.

The difference spans the WHOLE arc, not just the cut: it nets the cut against the Hazards
block each repo gained afterwards. Six of the seven cut repos gained their Hazards block
AFTER the cut, so a cut-only figure overstates the reduction.

Read-only. Runs ``git -C`` against each primary checkout; touches no working tree, and
fetches only if ``--fetch`` is passed.

Usage:
    python3 util/ad-hoc/2026-08-31_p5_arc_net_delta.py
    python3 util/ad-hoc/2026-08-31_p5_arc_net_delta.py --fetch --root /path/to/Juniper
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# repo -> (port PR number, port squash SHA).  SHAs transcribed from the §P5 banner and
# re-verified here: the script fails loudly if a SHA does not resolve in its repo.
PORTS: dict[str, tuple[str, str]] = {
    "juniper-canopy": ("#516", "611141c1"),
    # NOT c83c3407 -- that is the PR HEAD (a test fix, "drop the Version: header"), which the
    # §P5 banner recorded as the squash. It is the precise trap the banner's own next sentence
    # warns about; corrected here 2026-08-31 against `gh pr view 585 --json mergeCommit`.
    "juniper-cascor": ("#585", "fa649d0b"),
    "juniper-cascor-client": ("#139", "b1c1acd7"),
    "juniper-cascor-worker": ("#162", "177c2a15"),
    "juniper-data": ("#291", "19b84a8a"),
    "juniper-data-client": ("#173", "918f1dee"),
    "juniper-deploy": ("#195", "7e046491"),
    "juniper-recurrence": ("#131", "369d8f59"),
}


# repo -> list of (label, claimed squash SHA) for every commit the §P5 banner cites as a
# merged arc squash.  Verified by --check-shas: each must resolve AND be an ancestor of
# origin/main.  A SHA that resolves but is NOT an ancestor is the failure this catches --
# that is what a PR *head* looks like once its branch is deleted, and the banner recorded
# one (cascor #585) for five days.
CUTS: dict[str, list[tuple[str, str]]] = {
    "juniper-canopy": [("cut PR1 #540", "1a29ca4e"), ("cut PR2 #541", "f7e0213e")],
    "juniper-cascor": [("cut #600", "9820ebd6"), ("hazards #601", "9c813ba5")],
    "juniper-cascor-client": [("cut #142", "e19d7926")],
    "juniper-cascor-worker": [("cut #164", "9abbe3cc")],
    "juniper-data": [("cut #296", "9f9c0b8c")],
    "juniper-data-client": [("cut #176", "e3a8ddb9")],
    "juniper-deploy": [("cut #197", "4d2a66fa")],
    "juniper-recurrence": [("ceiling raise #135", "315d014b")],
}


def git(repo: Path, *args: str) -> str:
    """Run a read-only git command in ``repo`` and return stdout, or raise."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {repo.name}: {proc.stderr.strip()}")
    return proc.stdout


def agents_chars(repo: Path, ref: str) -> int:
    """Character count of AGENTS.md at ``ref``.

    Characters, not bytes -- the shipped Claude Code check compares ``content.length``,
    and AGENTS.md carries non-ASCII (em dashes, arrows) in every repo.
    """
    return len(git(repo, "show", f"{ref}:AGENTS.md"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        default="/home/pcalnon/Development/python/Juniper",
        help="parent directory holding the primary checkouts",
    )
    ap.add_argument("--fetch", action="store_true", help="git fetch each repo first")
    ap.add_argument(
        "--check-shas",
        action="store_true",
        help="verify every banner-cited squash SHA is an ANCESTOR of origin/main",
    )
    args = ap.parse_args()

    root = Path(args.root)

    if args.check_shas:
        bad = 0
        for name, claims in sorted(CUTS.items()):
            repo = root / name
            for label, sha in claims:
                try:
                    git(repo, "rev-parse", "--verify", f"{sha}^{{commit}}")
                except RuntimeError:
                    print(f"MISSING  {name:<22} {label:<20} {sha}  does not resolve")
                    bad += 1
                    continue
                merged = subprocess.run(
                    ["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, "origin/main"],
                    capture_output=True,
                    check=False,
                )
                if merged.returncode == 0:
                    print(f"ok       {name:<22} {label:<20} {sha}")
                else:
                    print(f"NOT-ON-MAIN {name:<19} {label:<20} {sha}  (a PR head, not a squash?)")
                    bad += 1
        print(f"\n{'FAIL' if bad else 'PASS'}: {bad} bad SHA(s)")
        return 1 if bad else 0

    rows: list[tuple[str, int, int, int]] = []
    failures: list[str] = []

    for name, (pr, port_sha) in sorted(PORTS.items()):
        repo = root / name
        if not (repo / ".git").exists():
            failures.append(f"{name}: no checkout at {repo}")
            continue
        try:
            if args.fetch:
                git(repo, "fetch", "origin", "--quiet")
            # Fail loudly rather than silently measuring the wrong commit.
            git(repo, "rev-parse", "--verify", f"{port_sha}^{{commit}}")
            start = agents_chars(repo, port_sha)
            now = agents_chars(repo, "origin/main")
        except RuntimeError as exc:
            failures.append(str(exc))
            continue
        rows.append((name, start, now, now - start))
        print(f"{name:<24} port {pr:<6} {port_sha}  {start:>7,} -> {now:>7,}  {now - start:+8,}")

    if rows:
        total = sum(delta for _, _, _, delta in rows)
        grew = [name for name, _, _, delta in rows if delta > 0]
        print("-" * 78)
        print(f"{'NET across ' + str(len(rows)) + ' repos':<24} {'':<20} {total:+8,} chars")
        if grew:
            print(f"grew: {', '.join(grew)}")

    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
