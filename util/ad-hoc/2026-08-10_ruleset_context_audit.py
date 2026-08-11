#!/usr/bin/env python3
"""Ruleset required-status-check audit across the 9 Juniper publishing repos.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

WHY THIS EXISTS
---------------
The 2026-08-10 ruleset normalization applied one fleet-union list of 30
``required_status_checks`` contexts to every repo. A required context that never
reports is never satisfied, so every repo's ``main`` became unmergeable except by
admin bypass -- the opposite of the headless-merge goal.

``required_status_checks`` is the ONE rule that cannot be normalized: it names each
repo's actual job names. This script derives, per repo:

* ``BLOCKING``   -- required but never reported (must be removed or renamed)
* ``CANDIDATE``  -- reported but not required (the "should we gate on it?" set)
* ``MATCHED``    -- required and reported (already correct)

Read-only: issues only ``gh api`` / ``gh pr list`` GETs. Writes nothing.

Usage::

    python util/ad-hoc/2026-08-10_ruleset_context_audit.py [--json] [--repo NAME]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

REPOS = [
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-recurrence",
]

# Checks that must NEVER be required, even though they report on PRs.
#
# * third-party fleet automation (Cursor / claude) -- not ours, may not run at all
# * deliberately advisory gates (soak period; promotion is issue ml#1011)
# * notification / mutation side-jobs -- they report but assert nothing
ADVISORY_PREFIXES = ("Cursor Automation:",)
ADVISORY_EXACT = {
    "claude",
    "Sequence Safety",
    "Sequence Safety (Advisory)",
    "Fleet PR Lint",
    "Build Notification",
    "Notify Downstream Repos",
    "Notify on Failure",
    "Bump AGENTS.md Last Updated",
    "Update requirements.lock",
    "CodeQL",  # umbrella; the real gate is "Analyze (python)"
}

TIMEOUT = 60


def _gh(args: list[str]) -> str:
    proc = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=TIMEOUT, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def is_advisory(name: str) -> bool:
    return name in ADVISORY_EXACT or name.startswith(ADVISORY_PREFIXES)


def required_contexts(repo: str) -> set[str]:
    out = _gh(
        [
            "api",
            f"/repos/pcalnon/{repo}/rules/branches/main",
            "--jq",
            '[.[]|select(.type=="required_status_checks")'
            "|.parameters.required_status_checks[].context]",
        ]
    )
    out = out.strip()
    return set(json.loads(out)) if out else set()


def per_pr_checks(repo: str, limit: int = 8) -> list[set[str]]:
    """Check names grouped BY PR, so path-gated jobs can be told from always-run ones.

    A context that reports on only some PRs is path-gated. Requiring it permanently
    blocks every PR that does not touch its paths -- the exact failure class this
    audit exists to fix -- so only contexts seen on EVERY sampled PR are Tier 1.
    """
    out = _gh(
        [
            "pr",
            "list",
            "--repo",
            f"pcalnon/{repo}",
            "--state",
            "all",
            "--limit",
            str(limit),
            "--json",
            "statusCheckRollup",
            "--jq",
            "[.[]|[.statusCheckRollup[].name]]",
        ]
    )
    out = out.strip()
    if not out:
        return []
    groups = [set(names) for names in json.loads(out) if names]
    if not groups:
        return []
    # Drop anomalous rollups (checks never started, or a PR merged before CI settled --
    # juniper-ml#1061 merged carrying 5 of ~37). Keeping them would make EVERY context
    # look path-gated and collapse Tier 1 to nothing. Genuine per-PR-type variation
    # (dependabot ~22 vs code ~37) is preserved -- that variation is the real signal,
    # because docs and dependabot PRs must stay mergeable too.
    counts = sorted(len(g) for g in groups)
    median = counts[len(counts) // 2]
    return [g for g in groups if len(g) >= median / 2]


def audit(repo: str) -> dict:
    required = required_contexts(repo)
    groups = per_pr_checks(repo)
    n = len(groups)
    reported = set().union(*groups) if groups else set()
    always = set.intersection(*groups) if groups else set()
    freq = {name: sum(1 for g in groups if name in g) for name in reported}

    tier1 = sorted(x for x in always if not is_advisory(x))
    return {
        "repo": repo,
        "prs_sampled": n,
        "required_count": len(required),
        "blocking": sorted(required - reported),
        "matched": sorted(required & reported),
        "tier1": tier1,
        "path_gated": sorted(
            f"{x} [{freq[x]}/{n}]" for x in reported - always if not is_advisory(x)
        ),
        "advisory_seen": sorted(x for x in reported if is_advisory(x)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--repo", help="audit a single repo instead of all 9")
    args = ap.parse_args()

    targets = [args.repo] if args.repo else REPOS
    results = []
    for repo in targets:
        try:
            results.append(audit(repo))
        except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            results.append({"repo": repo, "error": str(exc)[:300]})

    if args.json:
        print(json.dumps(results, indent=2))
        return 1 if any(r.get("blocking") or r.get("error") for r in results) else 0

    for r in results:
        print(f"\n{'=' * 78}\n{r['repo']}\n{'=' * 78}")
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        print(
            f"  required={r['required_count']}  matched={len(r['matched'])}  "
            f"BLOCKING={len(r['blocking'])}  prs_sampled={r['prs_sampled']}"
        )
        if r["blocking"]:
            print("\n  -- BLOCKING (required but never reported) --")
            for n in r["blocking"]:
                print(f"     x {n}")
        print(f"\n  -- TIER 1: safe to require (on {r['prs_sampled']}/{r['prs_sampled']} sampled PRs) --")
        for n in r["tier1"]:
            print(f"     + {n}")
        if r["path_gated"]:
            print("\n  -- PATH-GATED: do NOT require (would block unrelated PRs) --")
            for n in r["path_gated"]:
                print(f"     ~ {n}")

    total_blocking = sum(len(r.get("blocking", [])) for r in results)
    print(f"\n{'=' * 78}\nTOTAL BLOCKING CONTEXTS ACROSS FLEET: {total_blocking}")
    return 1 if total_blocking else 0


if __name__ == "__main__":
    sys.exit(main())
