#!/usr/bin/env python3
"""2026-09-05_fleet_provably_clean.py -- the PROVABLY-CLEAN subset of a fleet PR flood.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc analysis (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

Round 2's adversarial review established that a `predict_merge.py` verdict alone
is NOT sufficient evidence that a PR is safe to merge, because both
compositional-loss screens hard-code ``{"status": "skip"}`` on a merge conflict
(`predict_merge.py:359`). Reading the batch report naively yields the vacuous
claim "0 docs deletions across all 99" when the true statement is "0 across the
56 the screen could evaluate" -- a CORRECT predicate over an INCOMPLETE site
enumeration. All 43 CONFLICT PRs are UNSCREENED, not clean.

A second finding: a PR can be individually clean against main and still collide
with a SIBLING PR on a code file, because every PR is simulated against main
independently. Two PRs that each merge cleanly can be mutually exclusive
implementations of the same function (juniper-ml #1624 vs #1717 both rewrite
``crosscheck()`` in ``util/ad-hoc/register_status_crosscheck.py`` with different
bodies and assert on mutually exclusive error strings). Merging both is not a
line-union problem; one must be chosen.

So this script requires ALL of the following, and reports which gate each PR
fails so the exclusion is auditable:

  G1  verdict is MERGE-CLEAN or NEEDS-UPDATE-BRANCH  (i.e. the merge applied,
      so the screens actually executed rather than skipping)
  G2  ast_symbol_screen  == "pass"   (NOT "skip" -- skip is not evidence)
  G3  docs_additions_only == "pass"  (NOT "skip")
  G4  every fast gate in {black,isort,flake8,mypy,check-ast} is "pass" or a
      benign "skip" (no .py in delta / hook absent). A "fail" excludes.
  G5  no code-file collision: the PR's TRUE delta shares no .py / .bash / .yml
      file with any OTHER open PR's true delta.
  G6  required CI contexts are not failing (latest run per context name).

G4 deliberately treats "no hook with id X" as benign: `predict_merge.py`
hard-codes juniper-ml's hook names, so on a ruff repo (juniper-data) the missing
black/isort/flake8 hooks are scored `fail` and would otherwise exclude every PR
for an artifact of the instrument rather than a property of the PR.

Usage:
    python util/ad-hoc/2026-09-05_fleet_provably_clean.py \
        --predict PATH/ml_predict.json [--checks PATH/ml_checks.json] [--json]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys

FAST_GATES = ("black", "isort", "flake8", "mypy", "check-ast")
COLLIDE_SUFFIXES = (".py", ".bash", ".sh", ".yml", ".yaml")
# Missing-hook text emitted by pre-commit when the target repo does not define a hook.
MISSING_HOOK = "No hook with id"


def _status(gates: dict, key: str):
    v = (gates or {}).get(key)
    return v.get("status") if isinstance(v, dict) else v


def _detail(gates: dict, key: str) -> str:
    v = (gates or {}).get(key)
    return (v.get("detail") or "") if isinstance(v, dict) else ""


def build_collisions(prs: list) -> dict:
    """file -> [pr numbers], over TRUE merge deltas, restricted to code-ish files."""
    hits: dict = collections.defaultdict(list)
    for p in prs:
        for f in p.get("true_delta") or []:
            if f.endswith(COLLIDE_SUFFIXES):
                hits[f].append(p["pr"])
    return {f: sorted(v) for f, v in hits.items() if len(v) > 1}


def failing_contexts(checks_by_pr: dict, pr: int) -> list:
    """Latest run per context name; return names whose conclusion is a failure."""
    rollup = checks_by_pr.get(pr)
    if rollup is None:
        return []
    latest: dict = {}
    for c in rollup:
        name = c.get("name") or c.get("context") or "?"
        stamp = c.get("completedAt") or c.get("startedAt") or ""
        if name not in latest or stamp >= latest[name][0]:
            latest[name] = (stamp, (c.get("conclusion") or c.get("state") or ""))
    return sorted(n for n, (_, concl) in latest.items() if concl in ("FAILURE", "TIMED_OUT", "ERROR", "ACTION_REQUIRED"))


def evaluate(prs: list, checks_by_pr: dict) -> list:
    collisions = build_collisions(prs)
    pr_to_files: dict = collections.defaultdict(list)
    for f, nums in collisions.items():
        for n in nums:
            pr_to_files[n].append(f)

    rows = []
    for p in prs:
        g = p.get("gates") or {}
        reasons = []

        if p.get("verdict") not in ("MERGE-CLEAN", "NEEDS-UPDATE-BRANCH"):
            reasons.append(f"G1 verdict={p.get('verdict')}")

        for key, tag in (("ast_symbol_screen", "G2"), ("docs_additions_only", "G3")):
            st = _status(g, key)
            if st == "skip":
                reasons.append(f"{tag} {key}=SKIP (unscreened, not clean)")
            elif st == "fail" or (key == "ast_symbol_screen" and (g.get(key) or {}).get("lost")):
                reasons.append(f"{tag} {key}=FAIL")
            elif (key == "docs_additions_only") and (g.get(key) or {}).get("deletions"):
                reasons.append(f"{tag} docs deletions present")

        for hook in FAST_GATES:
            if _status(g, hook) == "fail":
                if MISSING_HOOK in _detail(g, hook):
                    continue  # instrument artifact, not a PR property
                reasons.append(f"G4 {hook}=fail")

        if pr_to_files.get(p["pr"]):
            shown = ", ".join(sorted(pr_to_files[p["pr"]])[:3])
            reasons.append(f"G5 code-file collision ({shown})")

        fc = failing_contexts(checks_by_pr, p["pr"])
        if fc:
            reasons.append("G6 CI failing: " + ", ".join(fc[:4]))

        rows.append({"pr": p["pr"], "title": p.get("title", ""), "verdict": p.get("verdict"), "clean": not reasons, "reasons": reasons})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--predict", required=True)
    ap.add_argument("--checks", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    with open(args.predict) as fh:
        prs = json.load(fh)["prs"]

    checks_by_pr: dict = {}
    if args.checks:
        with open(args.checks) as fh:
            for entry in json.load(fh):
                checks_by_pr[entry["number"]] = entry.get("statusCheckRollup") or []

    rows = evaluate(prs, checks_by_pr)
    clean = [r for r in rows if r["clean"]]

    if args.json:
        print(json.dumps({"n_total": len(rows), "n_clean": len(clean), "rows": rows}, indent=2))
        return 0

    print(f"PROVABLY CLEAN: {len(clean)} of {len(rows)}\n")
    for r in clean:
        print(f"  #{r['pr']}  {r['verdict']:<20} {r['title'][:72]}")
    print("\n--- exclusion reasons, by gate ---")
    tally: collections.Counter = collections.Counter()
    for r in rows:
        for reason in r["reasons"]:
            tally[reason.split(" ", 1)[0]] += 1
    for gate, n in sorted(tally.items()):
        print(f"  {gate}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
