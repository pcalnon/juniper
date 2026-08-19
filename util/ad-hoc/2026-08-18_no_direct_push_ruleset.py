#!/usr/bin/env python3
"""Create the no-bypass "require a pull request" ruleset on every Juniper repo.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License

Implements recommendation **R5** of
``notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md``.

Why a SECOND ruleset
--------------------
Direct pushes to ``main`` were never permitted: the existing ruleset already carries a
``pull_request`` rule, and rule suites show it firing --
``pull_request: fail "Changes must be made through a pull request"`` -- while the push lands
anyway, because the suite result is ``bypass``. **Bypass actors are per-ruleset**, and the
main ruleset grants ``RepositoryRole 5`` (owner) an ``always`` bypass.

That entitlement is load-bearing for three separate reasons (squash-SHA races, unresolved
review threads, and emergency access), so it is NOT being removed. Instead a **second**
ruleset carries the same ``pull_request`` rule with an **empty** ``bypass_actors`` list. Both
rulesets are evaluated, so the no-bypass copy binds everyone -- including the owner -- while
the original keeps its bypass for the other seven rules.

This is what R5 needs: 5 of juniper-ml's 9 post-adoption ``main`` breakages came from direct
pushes with no PR at all, and **both** true content-destruction events of the strict era were
direct pushes (cascor ``4d07a88c`` lost 136 symbols across five ``src/snapshots/*.py``
modules). No per-PR control -- ``strict`` or sequence-safety -- has jurisdiction over that
path, because there is no PR to gate.

Verified behaviour (live, juniper-ml, 2026-08-18)
------------------------------------------------
* A ref **update** is rejected: ``GH013: Repository rule violations found`` /
  *"Changes must be made through a pull request."* -- **even for the owner**.
* A branch **creation** is NOT rejected by this rule. Irrelevant for ``main``, which exists,
  but do not assume this rule blocks new branches.
* ``git push --dry-run`` does **NOT** evaluate rulesets -- it happily reports a push that the
  server then rejects. Never use it to verify a rule; it is a false-negative trap.

Pre-flight performed before the fleet rollout: no workflow in any of the 9 repos pushes to
``main``. The three ``lockfile-update.yml`` ``git push`` call sites run on ``dependabot/pip/**``
branches and push there, not to the default branch.

Cost, stated plainly
--------------------
Emergency direct fixes to ``main`` become impossible; a broken ``main`` must be repaired
through a PR that passes the required checks. ``util/safe_merge.py`` makes that path cheap.
Rollback is one call: delete (or disable) the ruleset this script creates.

Usage
-----
    python3 util/ad-hoc/2026-08-18_no_direct_push_ruleset.py                 # dry-run
    python3 util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --repo juniper-data
    python3 util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --execute
    python3 util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --status
    python3 util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --remove --execute   # rollback

Exit codes: 0 all requested repos OK (or already present) / 1 at least one failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

OWNER = "pcalnon"
RULESET_NAME = "juniper-no-direct-push"
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

# Least-restrictive pull_request parameters. Both rulesets' pull_request rules are evaluated,
# so anything stricter here would silently tighten the merge policy as a side effect of a
# change that is only meant to close the direct-push path.
PAYLOAD = {
    "name": RULESET_NAME,
    "target": "branch",
    "enforcement": "active",
    "bypass_actors": [],
    "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
    "rules": [
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": 0,
                "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_review_thread_resolution": False,
                "allowed_merge_methods": ["merge", "squash", "rebase"],
            },
        }
    ],
}


class Failed(RuntimeError):
    pass


def gh(args: list[str], stdin: str | None = None) -> str:
    proc = subprocess.run(  # nosec B603 B607
        ["gh", *args], capture_output=True, text=True, timeout=120, input=stdin, check=False
    )
    if proc.returncode != 0:
        raise Failed(f"gh {' '.join(args[:3])}… failed: {proc.stderr.strip()[:250]}")
    return proc.stdout


def find(repo: str) -> dict | None:
    data = json.loads(gh(["api", f"/repos/{OWNER}/{repo}/rulesets"]) or "[]")
    for rs in data:
        if rs.get("name") == RULESET_NAME:
            return rs
    return None


def status(repo: str) -> str:
    rs = find(repo)
    if not rs:
        return f"ABSENT   {repo}"
    full = json.loads(gh(["api", f"/repos/{OWNER}/{repo}/rulesets/{rs['id']}"]))
    return (
        f"PRESENT  {repo}: id={full['id']} enforcement={full['enforcement']} "
        f"bypass={len(full.get('bypass_actors') or [])} "
        f"rules={','.join(r['type'] for r in full['rules'])}"
    )


def create(repo: str, execute: bool) -> str:
    if find(repo):
        return f"SKIP     {repo}: already present"
    if not execute:
        return f"DRY      {repo}: would create '{RULESET_NAME}' (active, 0 bypass actors)"
    out = gh(
        ["api", "-X", "POST", f"/repos/{OWNER}/{repo}/rulesets", "--input", "-"],
        stdin=json.dumps(PAYLOAD),
    )
    made = json.loads(out)
    if made.get("bypass_actors"):
        raise Failed(f"{repo}: created ruleset has bypass actors — it would not bind")
    return f"OK       {repo}: created id={made['id']} enforcement={made['enforcement']}"


def remove(repo: str, execute: bool) -> str:
    rs = find(repo)
    if not rs:
        return f"SKIP     {repo}: not present"
    if not execute:
        return f"DRY      {repo}: would DELETE ruleset id={rs['id']}"
    gh(["api", "-X", "DELETE", f"/repos/{OWNER}/{repo}/rulesets/{rs['id']}"])
    return f"REMOVED  {repo}: id={rs['id']}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", help="operate on one repo instead of all 9")
    ap.add_argument("--execute", action="store_true", help="actually write (default: dry-run)")
    ap.add_argument("--status", action="store_true", help="report current state and exit")
    ap.add_argument("--remove", action="store_true", help="ROLLBACK: delete the ruleset")
    args = ap.parse_args()

    targets = [args.repo] if args.repo else REPOS
    if args.repo and args.repo not in REPOS:
        print(f"unknown repo: {args.repo}", file=sys.stderr)
        return 1

    if not (args.status or args.execute):
        print("*** DRY RUN — nothing will be written (pass --execute) ***\n")

    failed = False
    for repo in targets:
        try:
            if args.status:
                print(status(repo))
            elif args.remove:
                print(remove(repo, args.execute))
            else:
                print(create(repo, args.execute))
        except (Failed, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            failed = True
            print(f"FAIL     {repo}: {exc}", file=sys.stderr)

    if not args.status:
        print(
            "\nVerify: python util/ad-hoc/2026-08-10_ruleset_context_audit.py "
            "(expect BLOCKING=0 on all 9) and confirm open PRs still reach CLEAN."
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
