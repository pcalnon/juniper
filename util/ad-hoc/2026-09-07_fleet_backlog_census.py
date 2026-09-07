#!/usr/bin/env python3
"""
Count open `app/cursor` PRs across every Juniper repo, so "the backlog is zero" is measured.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-07
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-06_close_superseded_fleet.py`, which did the closing

A backlog claim is a universal quantifier over a set the claimant chose. "Zero across all four
repos" is only as good as the list of repos, and the original request named four while the
ecosystem has eight -- so this walks the full roster and reports each, including the ones nobody
expected to have any. A repo that errors is reported as ERROR, never as zero: an unreachable
repo and an empty one are the same number and not the same fact.

The roster is ENUMERATED from the org, not hard-coded. A census over a list the author chose is
a universal quantifier over that list and nothing more -- and the hard-coded set this started
with omitted `juniper-recurrence`, a live ecosystem repo missing from the parent CLAUDE.md's
"Active Repositories" table. The fallback list remains for when the org listing fails, and that
fallback is announced, because a narrower census that prints the same zero is the failure here.

Usage:
    2026-09-07_fleet_backlog_census.py [--author app/cursor] [--owner pcalnon]

Exit: 0 when every repo answered and the total is zero; 1 when any PR is open; 2 when a repo
      could not be read.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell

# Fallback ONLY. The real roster is enumerated from the org, because a census over a list the
# author chose is a universal quantifier over that list and nothing more. Measured 2026-09-07:
# this hard-coded set omits `juniper-recurrence`, a live ecosystem repo absent from the parent
# CLAUDE.md's "Active Repositories" table -- so a zero here could have coexisted with open PRs
# one repo away. It happened not to, which is luck rather than method.
FALLBACK_REPOS = (
    "juniper-ml",
    "juniper-data",
    "juniper-canopy",
    "juniper-data-client",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
)


def roster(owner: str) -> tuple[list[str], bool]:
    """`(names, from_org)` -- every non-archived repo in the org, else the fallback list."""
    res = subprocess.run(
        ["gh", "repo", "list", owner, "--limit", "500", "--json", "name,isArchived"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if res.returncode != 0 or not res.stdout.strip():
        return list(FALLBACK_REPOS), False
    names = [r["name"] for r in json.loads(res.stdout) if not r.get("isArchived")]
    return (sorted(names), True) if names else (list(FALLBACK_REPOS), False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", default="app/cursor")
    parser.add_argument("--owner", default="pcalnon")
    args = parser.parse_args()

    repos, from_org = roster(args.owner)
    if not from_org:
        print(f"WARNING: could not enumerate {args.owner}'s repos; falling back to a {len(repos)}-repo hard-coded list.")
        print("         A zero from this run covers that list ONLY.")
    total = 0
    unreadable = 0
    for repo in repos:
        res = subprocess.run(
            ["gh", "pr", "list", "--repo", f"{args.owner}/{repo}", "--state", "open", "--json", "number,author,title", "--limit", "300"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if res.returncode != 0:
            print(f"{repo:<24} ERROR  {res.stderr.strip()[:70]}")
            unreadable += 1
            continue
        rows = [p for p in json.loads(res.stdout or "[]") if p["author"]["login"] == args.author]
        print(f"{repo:<24} {len(rows):>3}" + ("" if not rows else "  " + ", ".join(f"#{p['number']}" for p in rows[:8])))
        total += len(rows)

    print()
    source = f"{args.owner} org listing" if from_org else "hard-coded fallback"
    print(f"total open {args.author} PRs across {len(repos)} repo(s) [{source}]: {total}" + (f"  ({unreadable} UNREADABLE)" if unreadable else ""))
    return 2 if unreadable else (1 if total else 0)


if __name__ == "__main__":
    raise SystemExit(main())
