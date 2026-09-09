#!/usr/bin/env python3
"""Measure the wall-clock span of a PR head's REQUIRED check contexts -- required ones only.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc measurement tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-08
Status:      ad-hoc -- measurement (re-run whenever the required-context list changes)
Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline), as for the v1 tool.
Related:     util/ad-hoc/2026-08-20_measure_required_check_span.py (v1, superseded by this);
             util/safe_merge.py REPO_TIMEOUTS; util/wait_for_checks.py (the canonical waiter).

WHY A V2
--------
v1's docstring states the right quantity:

    max(completed_at) - min(started_at)      over the REQUIRED contexts on ONE head SHA

and its code computes a different one. It fetches `check-runs?per_page=100` and filters
NOTHING, so every advisory, bot and out-of-band check-run on the SHA enters the span.

Measured on `pcalnon/juniper-cascor#626` (head 00498948):

    real CI pass          06:58:57Z -> 07:09:02Z        605 s
    `claude` check-run    12:52:24Z -> 12:52:24Z          0 s   (5.7 h later, NOT required)
    v1 reported span                                  21207 s

The 20,602 s in the middle is idle. Nothing was running, and `safe_merge` never waits for
it: it waits for the required contexts that are pending NOW. So the number that sizes every
`REPO_TIMEOUTS` entry in the fleet measures a quantity the budget is not spent on.

Three consequences, all of them observed rather than argued:

  * **The p90 is unstable by ~3x on sample size alone.** juniper-cascor: p90 720 s at n=12,
    739 s at n=13, 2121 s at n=30 -- because the estimator index steps onto or off a parked
    head. Two runs of the same command minutes apart reported 2940 s and 720 s.
  * **"3x max" is unusable.** It yields 63,621 s for cascor and 124,191 s for canopy, well
    past the ~3600 s worker lease, so the rule the v1 tool prints cannot be applied.
  * **`tests/test_safe_merge.py::test_default_timeout_is_sized_from_measurement` cannot
    fail.** Its band is `(p90, 4*p90]`; with p90 itself swinging 3x, every candidate budget
    -- including the 900 s that REFUSED ml#1754 live -- sits inside it at some sample size.

WHAT THIS TOOL DOES DIFFERENTLY
-------------------------------
  1. **Filters to the repo's actual required contexts**, read from its rulesets, so an
     advisory or bot check-run cannot enter the span.
  2. **Reads BOTH check-runs and legacy commit statuses.** A required context is either one
     or the other; `util/wait_for_checks.py:253-254` names this Trap 1, and v1 saw only
     check-runs.
  3. **Refuses a vacuous measurement.** A head whose required contexts are entirely absent
     is reported UNMEASURABLE and excluded, never counted as a small span; if no head is
     measurable the run exits 2. A correct predicate over an empty site enumeration is the
     failure this whole family of tools keeps re-introducing.
  4. **Reports coverage and `n` in the output**, because a p90 quoted without its sample
     size cannot be re-derived -- which is why the 2026-09-05 juniper-ml re-tier could not
     be reproduced.

It also prints v1's unfiltered span alongside, so the correction is auditable rather than
asserted.

Usage
-----
    python3 util/ad-hoc/2026-09-08_measure_required_check_span_v2.py --repo juniper-cascor -n 30
    python3 util/ad-hoc/2026-09-08_measure_required_check_span_v2.py --repo juniper-ml -n 30 --verbose

Exit: 0 measured; 1 no merged heads to sample; 2 nothing measurable (vacuous run refused).
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys
from datetime import datetime, timezone


def gh_json(args: list[str], allow_fail: bool = False):
    """Run `gh` and parse JSON. Raises on failure unless explicitly allowed to return None.

    A failed read is NOT a state: callers that need to tell "absent" from "could not look"
    must pass allow_fail=True and handle None. This is the hole #1824 fixed in the
    auto-merge shepherd, and it is not re-introduced here.
    """
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, timeout=180
    )
    if p.returncode != 0:
        if allow_fail:
            return None
        raise SystemExit(f"gh failed: {' '.join(args)}\n{p.stderr.strip()}")
    return json.loads(p.stdout or "null")


def pt(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def required_contexts(slug: str) -> set[str]:
    """Union of required status-check contexts across the repo's rulesets.

    Rulesets are read individually because the list endpoint does not embed `.rules`.
    A repo with no ruleset carrying a `required_status_checks` rule yields an empty set,
    and the caller REFUSES rather than measuring every check-run -- an empty required set
    would silently reproduce v1's defect.
    """
    listing = gh_json(["api", f"repos/{slug}/rulesets"], allow_fail=True)
    if not listing:
        return set()
    contexts: set[str] = set()
    for entry in listing:
        rid = entry.get("id")
        if rid is None:
            continue
        detail = gh_json(["api", f"repos/{slug}/rulesets/{rid}"], allow_fail=True)
        if not detail:
            continue
        for rule in detail.get("rules") or []:
            if rule.get("type") != "required_status_checks":
                continue
            params = rule.get("parameters") or {}
            for check in params.get("required_status_checks") or []:
                name = check.get("context")
                if name:
                    contexts.add(name)
    return contexts


def head_rows(slug: str, sha: str) -> list[tuple[str, str | None, str | None]]:
    """(name, started_at, completed_at) for every check-run AND legacy status on the SHA."""
    rows: list[tuple[str, str | None, str | None]] = []

    runs = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        [
            "gh",
            "api",
            f"repos/{slug}/commits/{sha}/check-runs?per_page=100",
            "--jq",
            ".check_runs[] | [.name, .started_at, .completed_at] | @json",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if runs.returncode == 0:
        for line in runs.stdout.splitlines():
            if line.strip():
                item = json.loads(line)
                rows.append((item[0], item[1], item[2]))

    # Legacy commit statuses. A required context may be one of these instead of a
    # check-run, and a status carries only `created_at`/`updated_at`.
    statuses = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        [
            "gh",
            "api",
            f"repos/{slug}/commits/{sha}/statuses?per_page=100",
            "--jq",
            ".[] | [.context, .created_at, .updated_at] | @json",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if statuses.returncode == 0:
        for line in statuses.stdout.splitlines():
            if line.strip():
                item = json.loads(line)
                rows.append((item[0], item[1], item[2]))

    return rows


def span_of(rows) -> float | None:
    starts = [pt(r[1]) for r in rows if r[1]]
    ends = [pt(r[2]) for r in rows if r[2]]
    if not starts or not ends:
        return None
    return (max(ends) - min(starts)).total_seconds()


def p90(sorted_values: list[float]) -> float:
    """Index-based p90, matching v1 so the two numbers are directly comparable."""
    return sorted_values[int(0.9 * (len(sorted_values) - 1))]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", default="juniper-ml")
    ap.add_argument("-n", type=int, default=30, help="how many recent merged PRs to sample")
    ap.add_argument("--verbose", action="store_true", help="print the per-head table")
    args = ap.parse_args(argv)
    slug = f"{args.owner}/{args.repo}"

    required = required_contexts(slug)
    if not required:
        print(
            f"{slug}: no required status checks found in any ruleset -- refusing to measure.\n"
            f"  Measuring every check-run instead is exactly v1's defect; a repo with no\n"
            f"  required contexts has no quantity for safe_merge to wait on.",
            file=sys.stderr,
        )
        return 2

    prs = gh_json(["pr", "list", "--repo", slug, "--state", "merged", "--limit", str(args.n), "--json", "number,headRefOid"])
    if not prs:
        print(f"{slug}: no merged PRs to sample", file=sys.stderr)
        return 1

    measured: list[tuple[int, float, float | None, int]] = []  # pr, span_required, span_all, n_required_seen
    unmeasurable: list[int] = []

    for pr in prs:
        sha = pr.get("headRefOid")
        if not sha:
            continue
        rows = head_rows(slug, sha)
        if not rows:
            unmeasurable.append(pr["number"])
            continue
        req_rows = [r for r in rows if r[0] in required]
        s_req = span_of(req_rows)
        s_all = span_of(rows)
        if s_req is None:
            # Required contexts entirely absent on this head. NOT a small span -- unknown.
            unmeasurable.append(pr["number"])
            continue
        measured.append((pr["number"], s_req, s_all, len({r[0] for r in req_rows})))

    if not measured:
        print(f"{slug}: no head had a measurable required-context span -- refusing to report", file=sys.stderr)
        return 2

    measured.sort(key=lambda r: -r[1])
    print(f"{slug}  --  {len(measured)} heads measured, {len(unmeasurable)} unmeasurable, {len(required)} required contexts")
    if args.verbose:
        print(f"{'PR':>7} {'req_ctx':>8} {'span_req':>9} {'span_all':>9}   inflation")
        print("-" * 60)
        for num, s_req, s_all, seen in measured:
            if s_all is None or not s_req:
                print(f"{num:>7} {seen:>8} {s_req:>9.0f} {'-':>9}   {'-':>7}")
                continue
            print(f"{num:>7} {seen:>8} {s_req:>9.0f} {s_all:>9.0f}   {s_all / s_req:>6.1f}x")
    if unmeasurable:
        print(f"  UNMEASURABLE heads (required contexts absent): {', '.join(str(n) for n in unmeasurable)}")

    req_spans = sorted(s for _, s, _, _ in measured)
    all_spans = sorted(s for _, _, s, _ in measured if s is not None)

    print()
    print(f"  REQUIRED-CONTEXT span   (n={len(req_spans)})")
    print(f"    min    {req_spans[0]:8.0f} s")
    print(f"    median {statistics.median(req_spans):8.0f} s")
    print(f"    p90    {p90(req_spans):8.0f} s")
    print(f"    max    {req_spans[-1]:8.0f} s")
    if all_spans:
        print()
        print(f"  v1 UNFILTERED span, for comparison  (n={len(all_spans)})")
        print(f"    p90    {p90(all_spans):8.0f} s")
        print(f"    max    {all_spans[-1]:8.0f} s")
        print(f"    -> v1 overstates max by {all_spans[-1] / req_spans[-1]:.1f}x")
    print()
    print(f"  Budget must CLEAR the observed max ({req_spans[-1]:.0f} s) and stay within 4x p90 ({4 * p90(req_spans):.0f} s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
