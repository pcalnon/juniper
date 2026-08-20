#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
License:     MIT License

Add ONE required status check to a branch ruleset, without disturbing anything else.

Why a script rather than a hand-built `gh api -X PUT`
-----------------------------------------------------
Updating a ruleset is a create-or-update PUT: a hand-written payload that omits a
field CLEARS it. This repo already has that scar -- the publish-path work records a
PUT that would have silently dropped the `pypi` environment's required reviewers
while successfully setting a ref policy, leaving the environment looking *more*
configured while being weaker.

So this reads the CURRENT ruleset, mutates exactly one array element, and writes the
whole object back. It never composes a payload from scratch.

Refusals (all before any write):
  * ruleset has no `required_status_checks` rule  -> the shape is not what we think
  * the context is already present                -> idempotent no-op
  * the rebuilt rule set loses any existing context -> would be a silent downgrade

Usage:
    python3 util/ad-hoc/2026-08-20_add_required_context.py \\
        --ruleset-id 13805432 --context 'Memory Budget' [--apply]

Default is a dry run. Exit 0 ok / 1 refused / 2 hard error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def gh_json(*args: str) -> dict:
    res = subprocess.run(["gh", *args], capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"::error::gh {' '.join(args)} failed: {res.stderr.strip()}")
    return json.loads(res.stdout)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="pcalnon/juniper-ml")
    ap.add_argument("--ruleset-id", required=True)
    ap.add_argument("--context", required=True)
    ap.add_argument("--apply", action="store_true", help="write (default: dry run)")
    args = ap.parse_args()

    path = f"repos/{args.repo}/rulesets/{args.ruleset_id}"
    rs = gh_json("api", path)

    checks_rule = next(
        (r for r in rs.get("rules", []) if r.get("type") == "required_status_checks"), None
    )
    if checks_rule is None:
        print("::error::ruleset has no required_status_checks rule", file=sys.stderr)
        return 1

    existing = [c["context"] for c in checks_rule["parameters"]["required_status_checks"]]
    print(f"ruleset {args.ruleset_id} ({rs.get('name')}) currently requires {len(existing)}:")
    for c in existing:
        print(f"    {c}")

    if args.context in existing:
        print(f"\n'{args.context}' is already required — nothing to do.")
        return 0

    checks_rule["parameters"]["required_status_checks"].append({"context": args.context})
    rebuilt = [c["context"] for c in checks_rule["parameters"]["required_status_checks"]]

    # Downgrade guard: every previously-required context must survive.
    lost = set(existing) - set(rebuilt)
    if lost:
        print(f"::error::rebuild would DROP {sorted(lost)} — refusing", file=sys.stderr)
        return 1

    print(f"\nwould add: {args.context}")
    print(f"result: {len(existing)} -> {len(rebuilt)} required contexts")

    if not args.apply:
        print("\nDRY RUN — nothing written. Pass --apply.")
        return 0

    payload = {
        "name": rs["name"],
        "target": rs["target"],
        "enforcement": rs["enforcement"],
        "conditions": rs["conditions"],
        "rules": rs["rules"],
    }
    if rs.get("bypass_actors"):
        payload["bypass_actors"] = rs["bypass_actors"]

    res = subprocess.run(
        ["gh", "api", "-X", "PUT", path, "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"::error::PUT failed: {res.stderr.strip()}", file=sys.stderr)
        return 2

    after = gh_json("api", path)
    after_rule = next(
        r for r in after["rules"] if r.get("type") == "required_status_checks"
    )
    after_ctx = [c["context"] for c in after_rule["parameters"]["required_status_checks"]]
    print(f"\nAPPLIED. now requires {len(after_ctx)}:")
    for c in after_ctx:
        print(f"    {c}")
    if args.context not in after_ctx:
        print("::error::context absent after write — verify manually", file=sys.stderr)
        return 2
    still_lost = set(existing) - set(after_ctx)
    if still_lost:
        print(f"::error::write DROPPED {sorted(still_lost)} — restore from backup",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
