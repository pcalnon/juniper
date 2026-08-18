#!/usr/bin/env python3
"""Promote the per-PR sequence-safety screen to a REQUIRED status check, fleet-wide.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License

Implements §A5.4 of
``notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md``
(juniper-ml#1011).  The plan named a helper ``2026-08-09_ruleset_edit.py`` that was never
written; this is that helper, scoped to the one edit it is needed for.

Why a script and not ``gh`` by hand
-----------------------------------
The repository-ruleset update endpoint is a **full replacement**
(``PUT /repos/{owner}/{repo}/rulesets/{id}``) -- there is no additive sub-resource for a
single context.  A hand-built payload that drops a rule silently makes ``main`` unmergeable
with **nothing going red**, which is the documented failure mode for this whole class of
change.  So every write here is:

1.  ``GET`` the live ruleset and write it to a timestamped snapshot file (rollback source).
2.  Rebuild the payload with the ORIGINAL objects carried through verbatim -- only the one
    ``required_status_checks`` array is touched.
3.  Assert the invariants BEFORE writing: rule count, rule type set, bypass-actor count,
    ``strict`` policy, ref targeting, and that the new context count is exactly ``old + 1``.
4.  ``PUT``, then re-``GET`` and assert the same invariants held.

``--dry-run`` is the default and writes nothing.

Pre-flight this script does NOT do
----------------------------------
It does not verify that the context string is one the repo's CI actually publishes.  Do that
first -- a required context that never reports is never satisfied.  For this edit it was
confirmed live on 2026-08-18: all 8 non-ml repos publish exactly
``Sequence Safety (Advisory)`` (the suffix is part of the job name and MUST be kept; renaming
the job would break the required context).  juniper-ml uses the unsuffixed ``Sequence Safety``
and was promoted separately.

Usage
-----
    python3 util/ad-hoc/2026-08-18_promote_sequence_safety.py                # dry-run, all 8
    python3 util/ad-hoc/2026-08-18_promote_sequence_safety.py --repo juniper-deploy
    python3 util/ad-hoc/2026-08-18_promote_sequence_safety.py --execute

Rollback
--------
Re-``PUT`` the snapshot written under ``--snapshot-dir`` (default
``~/.local/state/juniper-ruleset-snapshots``), or simply remove the context from the ruleset
in Settings -> Rules.

Exit codes: 0 all requested repos OK (or already promoted) / 1 at least one refused or failed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

# (repo, ruleset_id) -- ruleset ids re-resolved live on 2026-08-18.  juniper-recurrence is a
# RULESET here, not classic branch protection: the plan's §A5.5 predates the 2026-08-12
# deletion of its legacy protection and is stale.
TARGETS: list[tuple[str, int]] = [
    ("juniper-cascor", 15081045),
    ("juniper-canopy", 14249530),
    ("juniper-data", 14748749),
    ("juniper-data-client", 13316681),
    ("juniper-cascor-client", 13490605),
    ("juniper-cascor-worker", 14250447),
    ("juniper-deploy", 14715370),
    ("juniper-recurrence", 20634527),
]

CONTEXT = "Sequence Safety (Advisory)"
ACTIONS_INTEGRATION_ID = 15368
OWNER = "pcalnon"


class Refused(RuntimeError):
    """A safety assertion failed; nothing was written."""


def gh_json(args: list[str], stdin: str | None = None) -> dict:
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=120,
        input=stdin,
        check=False,
    )
    if proc.returncode != 0:
        raise Refused(f"gh {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout)


def fingerprint(rs: dict) -> dict:
    """The invariants that must survive the write."""
    rsc = next(
        (r for r in rs["rules"] if r["type"] == "required_status_checks"),
        None,
    )
    return {
        "rule_count": len(rs["rules"]),
        "rule_types": sorted(r["type"] for r in rs["rules"]),
        "bypass_count": len(rs.get("bypass_actors") or []),
        "enforcement": rs.get("enforcement"),
        "include": (rs.get("conditions", {}).get("ref_name", {}) or {}).get("include"),
        "strict": (rsc or {}).get("parameters", {}).get(
            "strict_required_status_checks_policy"
        ),
        "contexts": [
            c["context"]
            for c in (rsc or {}).get("parameters", {}).get("required_status_checks", [])
        ],
    }


def build_payload(rs: dict) -> dict:
    """Carry everything through verbatim; append exactly one context."""
    rules = []
    for rule in rs["rules"]:
        if rule["type"] != "required_status_checks":
            rules.append(rule)
            continue
        params = json.loads(json.dumps(rule["parameters"]))  # deep copy
        params["required_status_checks"] = params["required_status_checks"] + [
            {"context": CONTEXT, "integration_id": ACTIONS_INTEGRATION_ID}
        ]
        rules.append({**rule, "parameters": params})
    return {
        "name": rs["name"],
        "target": rs["target"],
        "enforcement": rs["enforcement"],
        "bypass_actors": [
            {
                "actor_id": a.get("actor_id"),
                "actor_type": a["actor_type"],
                "bypass_mode": a["bypass_mode"],
            }
            for a in (rs.get("bypass_actors") or [])
        ],
        "conditions": rs["conditions"],
        "rules": rules,
    }


def promote(repo: str, ruleset_id: int, snapshot_dir: pathlib.Path, execute: bool) -> str:
    path = f"/repos/{OWNER}/{repo}/rulesets/{ruleset_id}"
    live = gh_json(["api", path])
    before = fingerprint(live)

    if CONTEXT in before["contexts"]:
        return f"SKIP  {repo}: already required ({len(before['contexts'])} contexts)"

    payload = build_payload(live)
    after_planned = fingerprint(payload)

    # --- pre-write assertions: only the context array may differ -------------------
    if after_planned["rule_count"] != before["rule_count"]:
        raise Refused(f"{repo}: rule count would change")
    if after_planned["rule_types"] != before["rule_types"]:
        raise Refused(f"{repo}: rule type set would change")
    if after_planned["bypass_count"] != before["bypass_count"]:
        raise Refused(f"{repo}: bypass actor count would change")
    if after_planned["strict"] != before["strict"]:
        raise Refused(f"{repo}: strict policy would change")
    if after_planned["include"] != before["include"]:
        raise Refused(f"{repo}: ref targeting would change")
    if after_planned["contexts"] != [*before["contexts"], CONTEXT]:
        raise Refused(f"{repo}: context array is not a pure single append")

    n_before, n_after = len(before["contexts"]), len(after_planned["contexts"])
    if not execute:
        return f"DRY   {repo}: would add {CONTEXT!r} ({n_before} -> {n_after} contexts)"

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot_dir / f"{repo}-{ruleset_id}-pre-sequence-safety.json"
    snap.write_text(json.dumps(live, indent=2), encoding="utf-8")

    gh_json(["api", "-X", "PUT", path, "--input", "-"], stdin=json.dumps(payload))

    verified = fingerprint(gh_json(["api", path]))
    if verified["contexts"] != after_planned["contexts"]:
        raise Refused(f"{repo}: POST-WRITE MISMATCH -- rollback from {snap}")
    for key in ("rule_count", "rule_types", "bypass_count", "strict", "include"):
        if verified[key] != before[key]:
            raise Refused(f"{repo}: POST-WRITE {key} changed -- rollback from {snap}")

    return f"OK    {repo}: required ({n_before} -> {n_after} contexts); snapshot {snap.name}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", help="operate on a single repo instead of all 8")
    ap.add_argument(
        "--execute", action="store_true", help="actually write (default: dry-run)"
    )
    ap.add_argument(
        "--snapshot-dir",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".local/state/juniper-ruleset-snapshots",
    )
    args = ap.parse_args()

    targets = TARGETS
    if args.repo:
        targets = [t for t in TARGETS if t[0] == args.repo]
        if not targets:
            print(f"unknown repo: {args.repo}", file=sys.stderr)
            return 1

    if not args.execute:
        print("*** DRY RUN -- nothing will be written (pass --execute) ***\n")

    failed = False
    for repo, rid in targets:
        try:
            print(promote(repo, rid, args.snapshot_dir, args.execute))
        except (Refused, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            failed = True
            print(f"FAIL  {repo}: {exc}", file=sys.stderr)

    print(
        "\nNow re-run util/ad-hoc/2026-08-10_ruleset_context_audit.py and expect "
        "BLOCKING=0 on all 9.\nHave an INDEPENDENT checker confirm -- the failure mode is "
        "silent."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
