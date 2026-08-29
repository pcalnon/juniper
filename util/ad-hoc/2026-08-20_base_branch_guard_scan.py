#!/usr/bin/env python3
"""Is the stacked-PR footgun structurally prevented, or only swept for? (ml#434)

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- audit
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: ml#434 is closed.
Related:     ml#434; util/ad-hoc/2026-08-20_stacked_pr_sweep.py.

A periodic sweep finds instances after the fact. `pr-base-branch-guard.yml` prevents them:
it fails a PR whose base is not a trunk branch, so the footgun cannot fire unnoticed. This
reports which repos have the workflow, and -- separately -- whether its check is actually
REQUIRED by the ruleset, because a present-but-advisory guard stops nothing on a repo whose
owner holds an `always` bypass.
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
GUARD = "pr-base-branch-guard.yml"


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
    print(f"{'repo':<24} {'workflow':<12} {'required context?':<40}")
    print("-" * 80)
    missing, advisory = [], []
    for repo in REPOS:
        files = gh_json(f"repos/pcalnon/{repo}/contents/.github/workflows") or []
        names = {f["name"] for f in files if isinstance(f, dict)}
        has = GUARD in names

        req = set()
        for rs in gh_json(f"repos/pcalnon/{repo}/rulesets") or []:
            full = gh_json(f"repos/pcalnon/{repo}/rulesets/{rs['id']}")
            for rule in (full or {}).get("rules", []):
                if rule.get("type") == "required_status_checks":
                    for c in (rule.get("parameters") or {}).get(
                        "required_status_checks", []
                    ):
                        req.add(c.get("context", ""))
        hit = sorted(c for c in req if "base branch" in c.lower() or "base-branch" in c.lower())

        if not has:
            missing.append(repo)
        elif not hit:
            advisory.append(repo)
        print(
            f"{repo:<24} {'YES' if has else 'no':<12} {(', '.join(hit) or '-- not required --'):<40}"
        )

    print()
    if missing:
        print(f"NO GUARD WORKFLOW ({len(missing)}): {', '.join(missing)}")
        print("  A stacked PR on these merges with nothing objecting.")
    if advisory:
        print(f"GUARD PRESENT BUT NOT REQUIRED ({len(advisory)}): {', '.join(advisory)}")
        print("  Advisory only -- and the owner holds an `always` bypass, so an advisory")
        print("  check constrains nothing. Present is not the same as enforced.")
    if not missing and not advisory:
        print("All 9 repos carry the guard AND require its context. Class is structurally")
        print("prevented, not merely swept for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
