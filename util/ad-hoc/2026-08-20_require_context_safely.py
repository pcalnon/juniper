#!/usr/bin/env python3
"""Add ONE required status-check context to a repo ruleset, safely and reversibly.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc ruleset tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- migration (base-branch-guard rollout, ml#434 part 2)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: a general ruleset editor exists in util/ proper, or the rollout is done.
Related:     ml#434; util/ad-hoc/2026-08-18_promote_sequence_safety.py;
             util/ad-hoc/2026-08-19_sequence_safety_context_rename.py;
             util/ad-hoc/2026-08-20_add_required_context.py;
             notes/JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-CONTEXT-RENAME.md

Why another one
---------------
Three ruleset writers already exist and no single one has all the needed properties:

  promote_sequence_safety.py  -- snapshot + 5-invariant asserts + explicit integration_id,
                                 but hardcoded targets and context.
  ..._context_rename.py       -- preserves each context's OWN integration_id and asserts no
                                 drift, but is rename-shaped (three phases).
  add_required_context.py     -- parameterized and carries `rules` verbatim, but writes NO
                                 disk snapshot, OMITS integration_id on the new context, and
                                 verifies contexts only.

This combines the strongest property of each, and adds the pre-flight all three are missing.

The pre-flight none of them had
-------------------------------
`promote_sequence_safety.py` says so in its own docstring: it does NOT verify that the
context string is one the repo's CI actually publishes. That is the single most dangerous
gap, because the failure is SILENT and TOTAL -- a required context that never reports is
never satisfied, and the PR sits BLOCKED with nothing red. That is exactly how `main` went
unmergeable on five repos (a hardcoded integration_id retargeted `Bandit` at an app that
never reports it): "Five PRs sat BLOCKED with zero pending checks, zero unresolved review
threads, no failing checks, and every required context reporting SUCCESS."

So the pre-flight is observed-only BY DEFAULT -- there is no `--require-observed` flag (two
handoffs cited one after reading an earlier wording of this paragraph): it refuses unless the
exact context string appears as a check-run NAME on one of the eight most recently updated PR
heads in THAT repo, whatever the conclusion (a `pull_request`-only job reads `skipped` on every
`main` commit, and that is fine). Use `--allow-unobserved` only with a reason.

Invariants enforced
-------------------
1. `rules` is carried through VERBATIM -- never rebuilt from a schema-derived allowlist.
   `code_quality` is emitted by REST but absent from the documented REST enum AND from
   GraphQL's RepositoryRuleType; an allowlist rebuild silently drops it (and
   `copilot_code_review`, `license_compliance_scanning`). That is a silent policy change.
2. Each EXISTING context keeps its OWN `integration_id`. Never rewrite them from a
   constant: `Bandit` is 57789 on five repos, not Actions' 15368.
3. `bypass_actors` carried verbatim -- it is full-replacement too, and carries a row with a
   `null` actor_id (DeployKey) that is easy to mistranscribe.
4. Snapshot to disk BEFORE the PUT, outside the repo, so rollback does not depend on the
   history API.
5. Re-read the live ruleset IMMEDIATELY before the PUT -- multiple sessions edit these.
6. Post-write re-read asserting: rule count, rule-type set, bypass count, enforcement,
   ref include, `strict`, every prior context still present, and NO integration_id drift.

Usage
-----
    python3 util/ad-hoc/2026-08-20_require_context_safely.py --status
    python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-cascor
    python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-cascor --apply
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CONTEXT = "Guard PR base branch"
ACTIONS_INTEGRATION_ID = 15368  # the GitHub Actions app
SNAP_DIR = Path.home() / ".local" / "state" / "juniper-ruleset-snapshots"

# The default READ and WRITE roster. It must name every governed repo: a repo missing here
# is silently absent from `--status`, which reads as a complete census (ml#1403's class).
# `juniper-recurrence` was omitted until 2026-08-29 -- it joined the fleet with the P5 port
# and has carried `Memory Budget` as required since the 2026-08-27 promotion, so `--status`
# reported 8 of 9 and looked whole. Kept in step with the census ROSTER in
# `util/ad-hoc/2026-08-26_p5_fleet_state.py` by tests/test_require_context_safely.py.
TARGETS = [
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


def gh(args: list[str], check: bool = False):
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, timeout=180
    )
    if check and p.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])} failed: {p.stderr.strip()[:200]}")
    return p


def gh_json(path: str, method: str | None = None, body: dict | None = None):
    args = ["api", path]
    if method:
        args += ["-X", method]
    inp = None
    if body is not None:
        args += ["--input", "-"]
        inp = json.dumps(body)
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, input=inp, timeout=180
    )
    if p.returncode != 0:
        return None, p.stderr.strip()[:300]
    try:
        return json.loads(p.stdout or "null"), None
    except json.JSONDecodeError:
        return None, "unparseable response"


def find_ruleset(owner: str, repo: str):
    """Resolve the ruleset carrying required_status_checks, BY CONTENT not by name.

    Deliberately not "the first branch ruleset whose name != juniper-no-direct-push" --
    that heuristic holds only while every repo has exactly two rulesets and fails silently
    the day a third appears. Selecting on the rule we are about to edit cannot mis-target.
    """
    sets, err = gh_json(f"repos/{owner}/{repo}/rulesets")
    if sets is None:
        return None, f"cannot list rulesets: {err}"
    hits = []
    for rs in sets:
        full, err = gh_json(f"repos/{owner}/{repo}/rulesets/{rs['id']}")
        if full is None:
            # A failed per-ruleset GET used to be `continue`d, which turned a rate limit or a
            # network blip into "no ruleset carries required_status_checks" -- the same
            # fail-into-plausible shape as the census columns fixed in ml#1403. Seen twice
            # during the 2026-08-27 promotion (cascor-client on the dry-run, data on the
            # post-apply --status) with both rulesets intact. A read failure is an error,
            # never an absence.
            return None, f"cannot read ruleset {rs.get('id')} ({rs.get('name')}): {err}"
        if any(r.get("type") == "required_status_checks" for r in full.get("rules", [])):
            hits.append(full)
    if not hits:
        return None, "no ruleset carries required_status_checks"
    if len(hits) > 1:
        names = ", ".join(f"{h['name']}({h['id']})" for h in hits)
        return None, f"AMBIGUOUS -- {len(hits)} rulesets carry required_status_checks: {names}"
    return hits[0], None


def checks_rule(rs: dict):
    for r in rs.get("rules", []):
        if r.get("type") == "required_status_checks":
            return r
    return None


def contexts_of(rs: dict):
    rule = checks_rule(rs)
    if not rule:
        return []
    return (rule.get("parameters") or {}).get("required_status_checks", [])


def fingerprint(rs: dict):
    """The invariants a correct edit must not disturb."""
    rule = checks_rule(rs) or {}
    params = rule.get("parameters") or {}
    return {
        "rule_count": len(rs.get("rules", [])),
        "rule_types": sorted(r.get("type", "") for r in rs.get("rules", [])),
        "bypass_count": len(rs.get("bypass_actors") or []),
        "enforcement": rs.get("enforcement"),
        "ref_include": sorted(
            ((rs.get("conditions") or {}).get("ref_name") or {}).get("include", [])
        ),
        "strict": params.get("strict_required_status_checks_policy"),
        "pairs": sorted(
            (c.get("context", ""), c.get("integration_id")) for c in contexts_of(rs)
        ),
    }


def observed_contexts(owner: str, repo: str, limit: int = 8):
    """Context strings this repo's CI has ACTUALLY published recently.

    Looked up from recent PR heads rather than from the ruleset, because the question is
    'does anything publish this name here', which the ruleset cannot answer.
    """
    prs, _ = gh_json(
        f"repos/{owner}/{repo}/pulls?state=all&sort=updated&direction=desc&per_page={limit}"
    )
    seen = set()
    for pr in prs or []:
        sha = ((pr.get("head") or {}).get("sha")) or ""
        if not sha:
            continue
        runs, _ = gh_json(f"repos/{owner}/{repo}/commits/{sha}/check-runs?per_page=100")
        for cr in (runs or {}).get("check_runs", []):
            if cr.get("name"):
                seen.add(cr["name"])
    return seen


def observed_context_apps(owner: str, repo: str, context: str, limit: int = 8):
    """App ids that have ACTUALLY published a check-run named ``context`` in this repo.

    The name-only :func:`observed_contexts` answers "does anything publish this name here",
    which is the right pre-flight for ADDING a context. Amending an ``integration_id`` asks a
    strictly harder question -- "is THIS app the one that publishes it" -- and getting that
    wrong reproduces the outage this whole tool exists to prevent: an id pointing at an app
    that never reports leaves the context permanently unsatisfied, so the PR sits BLOCKED with
    nothing red.

    Returns ``{app_id: app_slug}`` so a refusal can name what actually publishes instead of
    just saying no.
    """
    prs, _ = gh_json(
        f"repos/{owner}/{repo}/pulls?state=all&sort=updated&direction=desc&per_page={limit}"
    )
    found: dict = {}
    for pr in prs or []:
        sha = ((pr.get("head") or {}).get("sha")) or ""
        if not sha:
            continue
        runs, _ = gh_json(f"repos/{owner}/{repo}/commits/{sha}/check-runs?per_page=100")
        for cr in (runs or {}).get("check_runs", []):
            if cr.get("name") != context:
                continue
            app = cr.get("app") or {}
            if app.get("id") is not None:
                found[app["id"]] = app.get("slug") or "?"
    # A PR-gated job reports on PR heads; one that only runs on main may not appear above, so
    # fall back to main's own check-runs rather than refusing a legitimate amend.
    if not found:
        runs, _ = gh_json(f"repos/{owner}/{repo}/commits/main/check-runs?per_page=100")
        for cr in (runs or {}).get("check_runs", []):
            if cr.get("name") != context:
                continue
            app = cr.get("app") or {}
            if app.get("id") is not None:
                found[app["id"]] = app.get("slug") or "?"
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", action="append", default=None, help="repeatable; default: all 9")
    ap.add_argument("--context", default=DEFAULT_CONTEXT)
    ap.add_argument("--integration-id", type=int, default=ACTIONS_INTEGRATION_ID)
    ap.add_argument(
        "--amend-integration-id",
        action="store_true",
        help="change the integration_id of a context that is ALREADY required (default is a "
        "no-op on such a context). Refuses unless the id is an app observed publishing that "
        "exact context name in that repo.",
    )
    ap.add_argument("--apply", action="store_true", help="write (default is dry-run)")
    ap.add_argument("--status", action="store_true", help="report only, never write")
    ap.add_argument(
        "--allow-unobserved",
        action="store_true",
        help="require the context even though nothing has been seen publishing it "
        "(DANGEROUS: a never-reporting required context blocks every PR, silently)",
    )
    args = ap.parse_args()
    repos = args.repo or TARGETS
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    rc = 0
    for repo in repos:
        print("=" * 78)
        print(f"{args.owner}/{repo}")
        rs, err = find_ruleset(args.owner, repo)
        if rs is None:
            print(f"  ERROR: {err}")
            rc = 1
            continue

        before = fingerprint(rs)
        names = [c.get("context") for c in contexts_of(rs)]
        print(f"  ruleset      : {rs['name']} (id={rs['id']})")
        print(f"  required now : {len(names)} contexts")

        amending = False
        if args.context in names:
            cur = next(c for c in contexts_of(rs) if c.get("context") == args.context)
            cur_iid = cur.get("integration_id")
            if not args.amend_integration_id:
                print(f"  ALREADY REQUIRED (integration_id={cur_iid}) — no-op")
                continue
            # ---- amend path: change the integration_id of an EXISTING context ----
            # No "is the id explicit?" guard here: --integration-id defaults to
            # ACTIONS_INTEGRATION_ID, so it is never None and such a check would be dead code.
            # The real gate is the observed-publisher refusal below, which is what stops a
            # wrong id regardless of whether it was typed or defaulted.
            if cur_iid == args.integration_id:
                print(f"  ALREADY PINNED (integration_id={cur_iid}) — no-op")
                continue
            publishers = observed_context_apps(args.owner, repo, args.context)
            print(f"  amend        : integration_id {cur_iid} -> {args.integration_id}")
            print(f"  observed publishers of {args.context!r}: "
                  f"{publishers if publishers else 'NONE'}")
            if args.integration_id not in publishers and not args.allow_unobserved:
                print(
                    f"  REFUSING: app {args.integration_id} has not been observed publishing\n"
                    f"  {args.context!r} in {repo}. Pinning a context to an app that does not\n"
                    "  report it leaves the context permanently unsatisfied: the PR sits\n"
                    "  BLOCKED with zero failing checks and zero pending checks. That is the\n"
                    "  five-repo outage this tool was written after. Pass --allow-unobserved\n"
                    "  only with a reason."
                )
                rc = 1
                continue
            amending = True

        obs = observed_contexts(args.owner, repo) if not amending else set()
        published = amending or args.context in obs
        if not amending:
            print(f"  context observed publishing here: {'YES' if published else 'NO'}")
        if not published and not args.allow_unobserved:
            print(
                f"  REFUSING: nothing in {repo}'s recent check-runs publishes "
                f"{args.context!r}.\n"
                "  A required context that never reports is never satisfied: the PR sits\n"
                "  BLOCKED with zero failing checks and zero pending checks. Land the\n"
                "  workflow and let it report at least once first, or pass\n"
                "  --allow-unobserved with a reason."
            )
            rc = 1
            continue

        verb = "amend" if amending else "add"
        if args.status:
            print(f"  [--status] would {verb}; not writing")
            continue
        if not args.apply:
            if amending:
                print(f"  [dry-run] would amend {args.context!r} integration_id "
                      f"{cur_iid} -> {args.integration_id} ({len(names)} contexts, unchanged)")
            else:
                print(f"  [dry-run] would add {args.context!r} "
                      f"(integration_id={args.integration_id}) -> {len(names) + 1} contexts")
            continue

        # ---- snapshot BEFORE the write, outside the repo -------------------
        SNAP_DIR.mkdir(parents=True, exist_ok=True)
        snap = SNAP_DIR / f"{repo}-{rs['name']}-{stamp}-pre-require-guard.json"
        snap.write_text(json.dumps(rs, indent=2))
        print(f"  snapshot     : {snap}")

        # ---- re-read live immediately before the PUT -----------------------
        fresh, err = find_ruleset(args.owner, repo)
        if fresh is None:
            print(f"  ERROR on re-read: {err}")
            rc = 1
            continue
        if fingerprint(fresh) != before:
            print("  ABORT: ruleset CHANGED between read and write (concurrent session).")
            print("  Re-run; do not force.")
            rc = 1
            continue

        rule = checks_rule(fresh)
        if amending:
            # Mutate the ONE entry in place. Every other context object is left untouched,
            # which is invariant 2 (each existing context keeps its OWN integration_id) --
            # the invariant whose violation retargeted `Bandit` and cost five repos.
            target = next(
                c for c in rule["parameters"]["required_status_checks"]
                if c.get("context") == args.context
            )
            target["integration_id"] = args.integration_id
        else:
            rule["parameters"]["required_status_checks"].append(
                {"context": args.context, "integration_id": args.integration_id}
            )
        payload = {
            "name": fresh["name"],
            "target": fresh["target"],
            "enforcement": fresh["enforcement"],
            "conditions": fresh["conditions"],
            "rules": fresh["rules"],  # VERBATIM -- never rebuilt from an allowlist
        }
        if fresh.get("bypass_actors"):
            payload["bypass_actors"] = fresh["bypass_actors"]

        _, err = gh_json(
            f"repos/{args.owner}/{repo}/rulesets/{fresh['id']}", method="PUT", body=payload
        )
        if err:
            print(f"  PUT FAILED: {err}")
            rc = 1
            continue

        # ---- post-write verification --------------------------------------
        after_rs, err = find_ruleset(args.owner, repo)
        if after_rs is None:
            print(f"  ERROR on verify: {err}")
            rc = 1
            continue
        after = fingerprint(after_rs)
        problems = []
        if after["rule_count"] != before["rule_count"]:
            problems.append(f"rule_count {before['rule_count']} -> {after['rule_count']}")
        if after["rule_types"] != before["rule_types"]:
            lost = set(before["rule_types"]) - set(after["rule_types"])
            problems.append(f"rule types LOST: {sorted(lost)}")
        if after["bypass_count"] != before["bypass_count"]:
            problems.append(f"bypass {before['bypass_count']} -> {after['bypass_count']}")
        for k in ("enforcement", "ref_include", "strict"):
            if after[k] != before[k]:
                problems.append(f"{k} {before[k]!r} -> {after[k]!r}")
        before_pairs = dict((c, i) for c, i in before["pairs"])
        after_pairs = dict((c, i) for c, i in after["pairs"])
        for ctx, iid in before_pairs.items():
            if ctx not in after_pairs:
                problems.append(f"context DROPPED: {ctx}")
            elif after_pairs[ctx] != iid:
                # An amend changes exactly ONE context's id BY DESIGN. Whitelisting that one
                # pair -- rather than relaxing or skipping the drift check -- keeps the
                # assertion live for all 16 others; a check that is switched off during the
                # one operation that rewrites ids would be worse than no check.
                if amending and ctx == args.context and after_pairs[ctx] == args.integration_id:
                    print(f"  amended      : {ctx}: {iid} -> {after_pairs[ctx]} (intended)")
                else:
                    problems.append(f"integration_id DRIFT on {ctx}: {iid} -> {after_pairs[ctx]}")
        if args.context not in after_pairs:
            problems.append(f"context {args.context!r} NOT present after write")
        if amending and after_pairs.get(args.context) != args.integration_id:
            problems.append(
                f"amend DID NOT TAKE: {args.context!r} is "
                f"{after_pairs.get(args.context)}, expected {args.integration_id}"
            )
        if amending and len(after_pairs) != len(before_pairs):
            problems.append(
                f"context COUNT changed during an amend: "
                f"{len(before_pairs)} -> {len(after_pairs)}"
            )

        if problems:
            print("  !! POST-WRITE VERIFICATION FAILED:")
            for p in problems:
                print(f"       {p}")
            print(f"  ROLLBACK: gh api repos/{args.owner}/{repo}/rulesets/{fresh['id']} "
                  f"-X PUT --input {snap}")
            rc = 1
        else:
            print(f"  OK: {len(before['pairs'])} -> {len(after['pairs'])} contexts, "
                  "all invariants held")

    return rc


if __name__ == "__main__":
    sys.exit(main())
