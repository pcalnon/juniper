#!/usr/bin/env python3
"""Full 9-repo census of who has actually EXERCISED a ruleset bypass.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- audit (re-run before any bypass-roster change)
Retire when: the bypass roster is settled and the decision recorded.
Related:     HANDOFF_2026-08-19 section 2.5; ml#1012.

Why this exists
---------------
The standing argument for removing the `29110` (dependabot) and `1143301` (Copilot SWE
Agent) bypass rows is that they "work solely via PRs on their own branches, and the rulesets
target ~DEFAULT_BRANCH only" -- so the entitlement is never used.

**That is an INFERENCE, not a finding.** The prior evidence was a 300-suite sample across
three repos (ml / cascor / data) showing only `pcalnon`. Three repos is not nine, and a
sample is not a census. This walks the FULL rule-suite history on all nine repos and reports
every distinct actor, with per-result counts.

Reading the output
------------------
`result` is the ruleset evaluation outcome for that push:

    pass    -- the push satisfied the rules
    fail    -- the push was rejected
    bypass  -- the actor's entitlement let a push through that would otherwise have FAILED

Only `bypass` is evidence of an entitlement being exercised. An actor appearing only with
`pass` has never needed its bypass, which is what the removal argument asserts.

CAVEAT: absence in this history is not proof of absence forever -- GitHub retains rule-suite
history for a bounded window. Report the window actually covered (this tool prints it) and do
not upgrade "not seen in the retained window" into "never".

Usage
-----
    python3 util/ad-hoc/2026-08-20_bypass_actor_census.py
    python3 util/ad-hoc/2026-08-20_bypass_actor_census.py --max-pages 20
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
from collections import defaultdict

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--max-pages", type=int, default=10, help="100 suites per page")
    # The API's `time_period` DEFAULTS TO `day`. Omitting it silently produces a 24-hour
    # census that looks like a full one -- the first run of this tool reported "no bypasses
    # on any of 9 repos" off 35 suites, all from a single day. `month` is the widest value
    # the endpoint accepts.
    ap.add_argument(
        "--time-period", default="month", choices=("hour", "day", "week", "month")
    )
    args = ap.parse_args()

    grand = defaultdict(lambda: defaultdict(int))
    any_bypass = []
    print(f"census window: time_period={args.time_period}  (API default is 'day' -- widen it)")
    print()
    print(f"{'repo':<24} {'suites':>7} {'oldest':<12} {'actors (result:count)'}")
    print("-" * 108)

    for repo in REPOS:
        suites = []
        for page in range(1, args.max_pages + 1):
            batch = gh_json(
                f"repos/{args.owner}/{repo}/rulesets/rule-suites"
                f"?per_page=100&page={page}"
                f"&time_period={args.time_period}&rule_suite_result=all"
            )
            if not batch:
                break
            suites.extend(batch)
            if len(batch) < 100:
                break

        per = defaultdict(lambda: defaultdict(int))
        for s in suites:
            actor = s.get("actor_name") or f"id:{s.get('actor_id')}"
            res = s.get("result") or "?"
            per[actor][res] += 1
            grand[actor][res] += 1
            if res == "bypass":
                any_bypass.append((repo, actor, s.get("pushed_at"), s.get("ref")))

        oldest = min((s.get("pushed_at") or "" for s in suites), default="")
        summary = "  ".join(
            f"{a}({','.join(f'{r}:{n}' for r, n in sorted(d.items()))})"
            for a, d in sorted(per.items())
        )
        print(f"{repo:<24} {len(suites):>7} {oldest[:10]:<12} {summary or '(none)'}")

    print()
    print("=" * 108)
    print("FLEET TOTALS BY ACTOR")
    print("=" * 108)
    for actor, d in sorted(grand.items()):
        tot = sum(d.values())
        detail = ", ".join(f"{r}={n}" for r, n in sorted(d.items()))
        print(f"  {actor:<28} {tot:>6} suites   ({detail})")

    print()
    print("=" * 108)
    print("BYPASSES ACTUALLY EXERCISED")
    print("=" * 108)
    if not any_bypass:
        print("  NONE in the retained history window on any of the 9 repos.")
        print()
        print("  This is the census the removal argument needed. It still does not prove")
        print("  'never' -- GitHub retains rule-suite history for a bounded window, and the")
        print("  per-repo 'oldest' column above is how far back this actually looked.")
    else:
        for repo, actor, when, ref in any_bypass:
            print(f"  {repo:<24} {actor:<28} {when} {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
