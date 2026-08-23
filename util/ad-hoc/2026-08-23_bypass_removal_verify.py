#!/usr/bin/env python3
"""Verify rows 29110 (dependabot) / 1143301 (Copilot) are gone, and the scope still holds.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License

Post-removal check for the 2026-08-22 determination
(`notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md`).

Checks TWO things, because the removal is only safe while the second holds:

1. Neither candidate row is present on any ruleset.
2. **No ruleset is scoped `~ALL`.** This is the load-bearing half. Under `~ALL` the
   `creation` rule is evaluated on every branch, which is exactly when the removed rows
   were needed -- re-scoping any ruleset back to `~ALL` would stop dependency PRs
   fleet-wide with no bypass left to catch it.

READ-ONLY. Exits 1 on a surviving row, 2 on a `~ALL` scope or a failed probe.

Usage: python3 util/ad-hoc/2026-08-23_bypass_removal_verify.py
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys

OWNER = "pcalnon"
REPOS = [
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
]
REMOVED = {"29110": "dependabot[bot]", "1143301": "Copilot SWE Agent"}


def gh_json(args: list[str]):
    """Failed probes return "ERROR", never [] -- a broken probe must not read as clean."""
    proc = subprocess.run(  # nosec B603 B607
        ["gh", *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        return "ERROR"
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return "ERROR"


def main() -> int:
    survivors, wide_scope, errors = [], [], []

    for repo in REPOS:
        rulesets = gh_json(["api", f"repos/{OWNER}/{repo}/rulesets"])
        if rulesets == "ERROR":
            errors.append(f"{repo}: could not list rulesets")
            continue
        for rs in rulesets:
            cur = gh_json(["api", f"repos/{OWNER}/{repo}/rulesets/{rs['id']}"])
            if cur == "ERROR":
                errors.append(f"{repo}/{rs['id']}: read failed")
                continue
            ids = {str(b.get("actor_id")) for b in cur.get("bypass_actors") or []}
            scope = (cur.get("conditions") or {}).get("ref_name", {}).get("include", [])
            left = sorted(ids & set(REMOVED))
            mark = "  <-- ROW STILL PRESENT" if left else ""
            wide = "  <-- ~ALL SCOPE" if "~ALL" in scope else ""
            print(
                f"{repo:24s} [{rs['id']}] {cur.get('name'):30s} "
                f"scope={','.join(scope) or '(none)'}{wide}{mark}"
            )
            if left:
                survivors.append((repo, rs["id"], left))
            if "~ALL" in scope:
                wide_scope.append((repo, rs["id"]))

    print("\n" + "=" * 80)
    print(f"rows still present : {len(survivors)}")
    print(f"~ALL-scoped rulesets: {len(wide_scope)}")
    print(f"probe failures      : {len(errors)}")
    for e in errors:
        print(f"  ERROR {e}")
    print("=" * 80)

    if errors:
        print("\nWARNING: a failed probe is NOT a clean result.")
        return 2
    if wide_scope:
        print("\nFAIL: a `~ALL`-scoped ruleset re-arms the need for the removed rows.")
        return 2
    if survivors:
        print(f"\nFAIL: {len(survivors)} row(s) not removed.")
        return 1
    print("\nOK: both rows absent fleet-wide, and no ruleset is `~ALL`-scoped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
