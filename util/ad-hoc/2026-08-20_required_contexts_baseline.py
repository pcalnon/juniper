#!/usr/bin/env python3
"""Snapshot every repo's required-status-check contexts, with integration_ids.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- audit / pre-change baseline
Retire when: the base-branch-guard rollout (ml#434 part 2) is complete and verified.
Related:     ml#434; util/ad-hoc/2026-08-20_base_branch_guard_scan.py.

Why a baseline exists at all
----------------------------
A ruleset PUT is a **full replacement**. Adding one required context means re-sending every
other one, and a required status check is a **(context, integration_id) pair**, not a bare
string -- hardcoding one app's integration id once made `main` unmergeable on five repos
because their `Bandit` check is emitted by a different app id.

So before any write: snapshot what is there, to disk, with ids. This tool only reads. It
writes its snapshot outside the repo (default ~/.local/state/juniper-ruleset-snapshots/)
so a rollback source survives independently of the working tree.

Usage
-----
    python3 util/ad-hoc/2026-08-20_required_contexts_baseline.py
    python3 util/ad-hoc/2026-08-20_required_contexts_baseline.py --save
    python3 util/ad-hoc/2026-08-20_required_contexts_baseline.py --grep "Guard PR base"
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
from datetime import datetime, timezone
from pathlib import Path

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
SNAP_DIR = Path.home() / ".local" / "state" / "juniper-ruleset-snapshots"


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
    ap.add_argument("--save", action="store_true", help="write full ruleset JSON snapshots")
    ap.add_argument("--grep", default="", help="only show contexts containing this substring")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    if args.save:
        SNAP_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    print(f"{'repo':<24} {'ruleset':<30} {'#req':>5}  integration_ids seen")
    print("-" * 96)
    for repo in REPOS:
        for rs in gh_json(f"repos/{args.owner}/{repo}/rulesets") or []:
            full = gh_json(f"repos/{args.owner}/{repo}/rulesets/{rs['id']}")
            if not full:
                continue
            if args.save:
                out = SNAP_DIR / f"{repo}-{full['name']}-{stamp}-pre-base-guard.json"
                out.write_text(json.dumps(full, indent=2))
            ctxs = []
            for rule in full.get("rules", []):
                if rule.get("type") == "required_status_checks":
                    ctxs = (rule.get("parameters") or {}).get("required_status_checks", [])
            if not ctxs:
                continue
            total += len(ctxs)
            ids = sorted({str(c.get("integration_id")) for c in ctxs})
            print(f"{repo:<24} {full['name'][:29]:<30} {len(ctxs):>5}  {', '.join(ids)}")
            shown = [
                c
                for c in ctxs
                if not args.grep or args.grep.lower() in (c.get("context") or "").lower()
            ]
            if args.grep:
                for c in shown:
                    print(f"{'':<24}   HIT: {c.get('context')} (integration_id={c.get('integration_id')})")

    print()
    print(f"total required contexts across fleet: {total}")
    if args.save:
        print(f"snapshots written to: {SNAP_DIR}  (pattern *-{stamp}-pre-base-guard.json)")
    print()
    print("A required status check is a (context, integration_id) PAIR. Preserve BOTH on any")
    print("PUT -- a ruleset PUT is a full replacement, and a wrong id blocks every merge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
