#!/usr/bin/env python3
"""Which repos restrict ref CREATION -- the rule that makes dependabot need its bypass.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- audit
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the bypass roster decision (HANDOFF_2026-08-19 section 2.5) is recorded.
Related:     util/ad-hoc/2026-08-20_bypass_actor_census.py; ml#1012.

The finding this exists to make checkable
-----------------------------------------
The standing argument for dropping the `29110` (dependabot) bypass row was:

    "Both work solely via PRs on their own branches, and the rulesets target
     ~DEFAULT_BRANCH only."

The census (sibling script) shows dependabot exercising a bypass **24 times** on
juniper-cascor-client, every one of its suites, none passing without it. Suite 3625611564
shows why:

    before_sha : 0000000000000000000000000000000000000000   <- a branch CREATION
    creation   : fail -- "Cannot create ref due to creations being restricted."
    result     : bypass

So the premise is TRUE and INSUFFICIENT. The ruleset really does scope to `~DEFAULT_BRANCH`,
and a `creation` rule inside it still evaluates against dependabot's own branch creation.
`~DEFAULT_BRANCH` scoping does not imply "never touches other branches" when the ruleset
carries a `creation` rule.

This scan reports, per repo, whether any active ruleset carries `creation` -- i.e. where
removing dependabot's bypass would stop it opening update PRs at all.

Usage
-----
    python3 util/ad-hoc/2026-08-20_creation_rule_scan.py
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design

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


def gh_json(path: str):
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", "api", path], capture_output=True, text=True, timeout=120
    )
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout or "null")
    except json.JSONDecodeError:
        return None


def main() -> int:
    print(f"{'repo':<24} {'ruleset':<30} {'include':<22} {'creation?':<10} rules")
    print("-" * 118)
    at_risk = []
    for repo in REPOS:
        sets = gh_json(f"repos/pcalnon/{repo}/rulesets") or []
        for s in sets:
            full = gh_json(f"repos/pcalnon/{repo}/rulesets/{s['id']}")
            if not full:
                continue
            rules = [r["type"] for r in full.get("rules", [])]
            inc = ",".join(
                ((full.get("conditions") or {}).get("ref_name") or {}).get("include", [])
            )
            has = "creation" in rules
            if has:
                at_risk.append((repo, full.get("name")))
            print(
                f"{repo:<24} {str(full.get('name'))[:29]:<30} {inc[:21]:<22} "
                f"{'YES' if has else 'no':<10} {'+'.join(rules)[:40]}"
            )

    print()
    print("=" * 118)
    print("REPOS WHERE REMOVING dependabot's BYPASS WOULD BLOCK BRANCH CREATION")
    print("=" * 118)
    if at_risk:
        for repo, name in at_risk:
            print(f"  {repo:<24} via ruleset {name!r}")
        print()
        print("  On these, dependabot cannot create its own update branch without the")
        print("  bypass -- so removing row 29110 stops dependency PRs entirely.")
    else:
        print("  none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
