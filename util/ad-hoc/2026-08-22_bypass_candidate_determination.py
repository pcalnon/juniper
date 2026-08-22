#!/usr/bin/env python3
"""Determine the two UNDETERMINED bypass rows: 29110 (dependabot), 1143301 (Copilot).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License

The 2026-08-20 census left both rows UNDETERMINED because the only evidence was
ABSENCE FROM HISTORY -- the standard the census itself called insufficient (§3c).

This tool replaces that with a MECHANISM. A bypass row is load-bearing only if the
rule it bypasses is actually EVALUATED for the actor's operations. GitHub keeps a
per-ruleset version history, so the scope in force at any past moment is readable:

    GET /repos/{owner}/{repo}/rulesets/{id}/history
    GET /repos/{owner}/{repo}/rulesets/{id}/history/{version_id}   -> {.state}

`~ALL` scoping evaluates `creation` on EVERY branch, so an actor that creates
branches needs the bypass. `~DEFAULT_BRANCH` scoping evaluates it only on the
default branch, which neither actor ever creates -- so the row is INERT for
creation, and the observed absence of rule suites is PREDICTED rather than merely
consistent.

READ-ONLY. Queries the API; never writes a ruleset, bypass row, or setting.

Usage:
    python3 util/ad-hoc/2026-08-22_bypass_candidate_determination.py
    python3 util/ad-hoc/2026-08-22_bypass_candidate_determination.py --json
"""

from __future__ import annotations

import argparse
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

CANDIDATES = {"29110": "dependabot[bot]", "1143301": "Copilot SWE Agent"}

# Every rule that a `~ALL`-scoped ruleset would evaluate on a NON-default branch.
# Narrowing to `~DEFAULT_BRANCH` stops evaluating all of them off `main`.
BRANCH_SCOPED_RULES = {"creation", "deletion", "non_fast_forward", "required_signatures"}


def gh_json(args: list[str]):
    """Return parsed JSON, or a sentinel that CANNOT be mistaken for an empty answer.

    The census's own §3 near-miss was `gh_json(...) or []` -- a failed probe reported as
    zero findings. Failures return the string "ERROR" so callers must handle them.
    """
    proc = subprocess.run(  # nosec B603 B607
        ["gh", *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        return "ERROR"
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return "ERROR"


def scope_of(state: dict) -> list[str]:
    return ((state or {}).get("conditions") or {}).get("ref_name", {}).get("include", [])


def bypass_ids(state: dict) -> set[str]:
    return {str(b.get("actor_id")) for b in (state or {}).get("bypass_actors") or []}


def rules_of(state: dict) -> set[str]:
    return {r.get("type") for r in (state or {}).get("rules") or []}


def audit_repo(repo: str) -> dict:
    out: dict = {"repo": repo, "rulesets": [], "error": None}
    rulesets = gh_json(["api", f"repos/{OWNER}/{repo}/rulesets"])
    if rulesets == "ERROR":
        out["error"] = "could not list rulesets"
        return out

    for rs in rulesets:
        rid = rs["id"]
        cur = gh_json(["api", f"repos/{OWNER}/{repo}/rulesets/{rid}"])
        if cur == "ERROR":
            out["rulesets"].append({"id": rid, "name": rs.get("name"), "error": "read failed"})
            continue

        entry = {
            "id": rid,
            "name": cur.get("name"),
            "scope": scope_of(cur),
            "rules": sorted(rules_of(cur)),
            "bypass": sorted(bypass_ids(cur)),
            "candidates_present": sorted(bypass_ids(cur) & set(CANDIDATES)),
            "narrowing": None,
        }

        # Walk the version history newest -> oldest and find the transition OFF `~ALL`.
        hist = gh_json(["api", f"repos/{OWNER}/{repo}/rulesets/{rid}/history"])
        if hist == "ERROR":
            entry["narrowing"] = {"error": "history unavailable"}
        else:
            prev_scope, prev_when = None, None
            for ver in hist:  # newest first
                st = gh_json(
                    ["api", f"repos/{OWNER}/{repo}/rulesets/{rid}/history/{ver['version_id']}"]
                )
                if st == "ERROR":
                    continue
                sc = scope_of(st.get("state") or {})
                if prev_scope is not None and sc != prev_scope:
                    entry["narrowing"] = {
                        "changed_at": prev_when,
                        "from": sc,
                        "to": prev_scope,
                        "candidates_before": sorted(
                            bypass_ids(st.get("state") or {}) & set(CANDIDATES)
                        ),
                    }
                    break
                prev_scope, prev_when = sc, ver.get("updated_at")

        out["rulesets"].append(entry)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    results = [audit_repo(r) for r in REPOS]

    if args.as_json:
        print(json.dumps(results, indent=2))
        return 0

    print("=" * 96)
    print("BYPASS CANDIDATE DETERMINATION -- scope in force, not absence from history")
    print("=" * 96)

    inert, loadbearing, unknown = [], [], []

    for res in results:
        if res["error"]:
            print(f"\n{res['repo']}: ERROR -- {res['error']}")
            unknown.append(res["repo"])
            continue
        print(f"\n{res['repo']}")
        for e in res["rulesets"]:
            if e.get("error"):
                print(f"  ruleset {e['id']}: ERROR -- {e['error']}")
                unknown.append(res["repo"])
                continue
            scope = ",".join(e["scope"]) or "(none)"
            cands = ",".join(e["candidates_present"]) or "-"
            print(f"  [{e['id']}] {e['name']}")
            print(f"        scope={scope}   candidates={cands}")
            evaluated_off_main = "~ALL" in e["scope"]
            if e["candidates_present"]:
                if evaluated_off_main:
                    print("        VERDICT: LOAD-BEARING off-main (scope is ~ALL)")
                    loadbearing.append((res["repo"], e["id"]))
                else:
                    off = sorted(BRANCH_SCOPED_RULES & set(e["rules"]))
                    print(
                        f"        VERDICT: INERT off-main -- {','.join(off)} "
                        "no longer evaluated on non-default branches"
                    )
                    inert.append((res["repo"], e["id"]))
            n = e["narrowing"]
            if n and not n.get("error"):
                print(
                    f"        narrowed {','.join(n['from'])} -> {','.join(n['to'])} "
                    f"at {n['changed_at']}"
                )
            elif n:
                print(f"        narrowing: {n['error']}")

    print("\n" + "=" * 96)
    print(f"INERT (candidate rows removable): {len(inert)}")
    print(f"LOAD-BEARING (do NOT remove):     {len(loadbearing)}")
    print(f"UNDETERMINED (probe failed):      {len(unknown)}")
    print("=" * 96)
    if unknown:
        print("\nWARNING: at least one probe FAILED. A failed probe is not a clean result.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
