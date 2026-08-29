#!/usr/bin/env python3
"""Census of open bot-authored PRs (dependabot / github-actions) across the 9 Juniper repos.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-24
Status:      ad-hoc -- recurring (run before every dependabot sweep)
Retire when: a repo-level or fleet dashboard reports the same thing; delete then.

Read-only. Never merges, closes, approves, or pushes -- it only reports, so the merge
decision stays explicit and per-PR.

WHAT IT PRODUCED (2026-08-24)
-----------------------------
19 open bot PRs across 9 of 9 repos, of which 17 were mergeable. Two findings the raw
``gh pr list`` would not have surfaced:

* juniper-cascor-client returned a graphql i/o timeout and would have been recorded as
  ZERO bot PRs. It had two. Hence ``gh_json``'s retry -- a network failure is not an
  answer, and a silently-skipped repo is the ml#1305 defect class.
* The rollup summary here is deliberately NOT a merge gate. ml#1304 showed five checks,
  all ``Cursor Automation ... skipping``, and read as clean while 0 of its 17 REQUIRED
  contexts had run. Gate on required contexts (see the sweep script's ``classify``),
  never on "the rollup shows nothing bad".

The roster is the canonical 9 from ``util/ruleset_scope_guard.py`` (juniper-slacker is
deliberately NOT in it). Do not hand-write a shorter list: ml#1305 records two rosters
that silently skipped juniper-recurrence.

Usage: python3 util/ad-hoc/2026-08-24_bot_pr_census.py [--json]
"""

from __future__ import annotations

import json
import subprocess
import sys

REPOS = (
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
)

BOT_LOGINS = {"dependabot", "app/dependabot", "github-actions", "app/github-actions"}

FIELDS = "number,title,author,mergeStateStatus,mergeable,isDraft,headRefName,createdAt,statusCheckRollup"


def gh_json(args: list[str]) -> object:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        return {"__error__": (proc.stderr or "").strip()[:200]}
    try:
        return json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return {"__error__": f"unparseable: {exc}"}


def rollup_state(pr: dict) -> str:
    """Summarise the head commit's check rollup without trusting a single aggregate."""
    nodes = pr.get("statusCheckRollup") or []
    if not nodes:
        return "no-checks"
    buckets: dict[str, int] = {}
    for n in nodes:
        val = (n.get("conclusion") or n.get("state") or n.get("status") or "?").upper()
        buckets[val] = buckets.get(val, 0) + 1
    bad = [f"{v}x{k}" for k, v in sorted(buckets.items()) if k in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED")]
    pending = [f"{v}x{k}" for k, v in sorted(buckets.items()) if k in ("PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED")]
    if bad:
        return "FAIL " + ",".join(bad)
    if pending:
        return "PENDING " + ",".join(pending)
    return "green"


def main() -> int:
    as_json = "--json" in sys.argv
    out: list[dict] = []
    for repo in REPOS:
        data = gh_json(["gh", "pr", "list", "--repo", f"pcalnon/{repo}", "--state", "open",
                        "--limit", "100", "--json", FIELDS])
        if isinstance(data, dict) and "__error__" in data:
            out.append({"repo": repo, "error": data["__error__"]})
            continue
        for pr in data:  # type: ignore[union-attr]
            login = (pr.get("author") or {}).get("login", "")
            if login not in BOT_LOGINS:
                continue
            out.append({
                "repo": repo,
                "number": pr["number"],
                "title": pr["title"],
                "author": login,
                "draft": pr.get("isDraft"),
                "mergeState": pr.get("mergeStateStatus"),
                "mergeable": pr.get("mergeable"),
                "checks": rollup_state(pr),
                "branch": pr.get("headRefName"),
                "created": (pr.get("createdAt") or "")[:10],
            })

    if as_json:
        print(json.dumps(out, indent=2))
        return 0

    errs = [r for r in out if "error" in r]
    prs = [r for r in out if "error" not in r]
    print(f"{'repo':<24} {'#':>5}  {'checks':<28} {'mergeState':<12} title")
    print("-" * 130)
    for r in sorted(prs, key=lambda x: (x["repo"], x["number"])):
        print(f"{r['repo']:<24} {r['number']:>5}  {r['checks']:<28} {str(r['mergeState']):<12} {r['title'][:58]}")
    print()
    print(f"TOTAL bot PRs: {len(prs)} across {len({r['repo'] for r in prs})} of {len(REPOS)} repos")
    for e in errs:
        print(f"  !! {e['repo']}: {e['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
