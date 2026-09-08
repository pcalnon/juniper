#!/usr/bin/env python3
"""Measure the real wall-clock span of a PR head's REQUIRED check contexts.

*** SUPERSEDED 2026-09-08 by util/ad-hoc/2026-09-08_measure_required_check_span_v2.py. ***

This tool does not do what the sentence above says. It fetches
`repos/{slug}/commits/{sha}/check-runs?per_page=100` and filters NOTHING, so advisory and bot
check-runs enter the span alongside the required ones. On `pcalnon/juniper-cascor#626` a
`claude` check-run attached to the head SHA 5.7 hours after CI finished, and this tool
reported a 21,207 s span for a 605 s CI pass.

Measured overstatement of the observed max, n=30 per repo: cascor 11x, canopy 20x,
cascor-client 19x, data-client 27x, cascor-worker 70x, deploy 110x. It also makes the p90
unstable by ~3x on sample size alone (cascor: 720 s at n=12, 2121 s at n=30), which is why
the 2026-09-05 juniper-ml re-tier could not be reproduced.

Use v2. It is kept only so the historical numbers in `util/safe_merge.py` can be re-derived
and the correction audited; v2 prints this tool's unfiltered span alongside its own for
exactly that purpose.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc measurement tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      SUPERSEDED by the v2 tool -- retained for audit, do not size budgets from it
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: `DEFAULT_TIMEOUT` is derived automatically, or the fleet's CI shape settles.
Related:     HANDOFF_2026-08-19 section 2.3; util/safe_merge.py DEFAULT_TIMEOUT.

Why not just time `ci.yml`
--------------------------
`safe_merge` waits for **every required context**, which spans several workflows that start
at different moments and finish at different moments. The quantity that must fit inside
`DEFAULT_TIMEOUT` is therefore

    max(completed_at) - min(started_at)      over the required contexts on ONE head SHA

not any single workflow's duration. Measuring one workflow undercounts, which is how the
current 900 s came to be sized against a 251 s median.

The 251 s figure is also stale by construction: it predates `Sequence Safety` becoming
required (2026-08-18) and `Memory Budget` (2026-08-20, ml 15 -> 16 contexts).

Usage
-----
    python3 util/ad-hoc/2026-08-20_measure_required_check_span.py
    python3 util/ad-hoc/2026-08-20_measure_required_check_span.py --repo juniper-cascor -n 25
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys
from datetime import datetime, timezone


def gh_json(args: list[str]):
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, timeout=120
    )
    if p.returncode != 0:
        raise SystemExit(f"gh failed: {' '.join(args)}\n{p.stderr.strip()}")
    return json.loads(p.stdout or "null")


def pt(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", default="juniper-ml")
    ap.add_argument("-n", type=int, default=20, help="how many recent merged PRs to sample")
    args = ap.parse_args()
    slug = f"{args.owner}/{args.repo}"

    prs = gh_json(
        [
            "pr",
            "list",
            "--repo",
            slug,
            "--state",
            "merged",
            "--limit",
            str(args.n),
            "--json",
            "number,mergeCommit,headRefOid",
        ]
    )

    spans, rows = [], []
    for pr in prs:
        sha = pr.get("headRefOid")
        if not sha:
            continue
        # `--jq` over a stream emits one JSON doc PER LINE, so this cannot go through
        # gh_json()'s single json.loads -- it is parsed line by line below.
        p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
            [
                "gh",
                "api",
                f"repos/{slug}/commits/{sha}/check-runs?per_page=100",
                "--jq",
                ".check_runs[] | [.name, .started_at, .completed_at, .conclusion] | @json",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if p.returncode != 0:
            continue
        items = [json.loads(ln) for ln in p.stdout.splitlines() if ln.strip()]
        starts = [pt(i[1]) for i in items if i[1]]
        ends = [pt(i[2]) for i in items if i[2]]
        if not starts or not ends:
            continue
        span = (max(ends) - min(starts)).total_seconds()
        slowest = max(
            ((pt(i[2]) - pt(i[1])).total_seconds(), i[0]) for i in items if i[1] and i[2]
        )
        spans.append(span)
        rows.append((pr["number"], len(items), span, slowest[1][:44], slowest[0]))

    if not spans:
        print(f"{slug}: no measurable heads", file=sys.stderr)
        return 1

    rows.sort(key=lambda r: -r[2])
    print(f"{slug}  —  {len(spans)} heads sampled")
    print(f"{'PR':>7} {'checks':>7} {'span_s':>9}   slowest single context")
    print("-" * 88)
    for num, n, span, name, dur in rows:
        print(f"{num:>7} {n:>7} {span:>9.0f}   {name} ({dur:.0f}s)")

    spans.sort()
    print()
    print(f"  min    {spans[0]:8.0f} s")
    print(f"  median {statistics.median(spans):8.0f} s")
    print(f"  p90    {spans[int(0.9 * (len(spans) - 1))]:8.0f} s")
    print(f"  max    {spans[-1]:8.0f} s")
    print()
    print(f"  3x max   -> {3 * spans[-1]:.0f} s      (the sizing rule DEFAULT_TIMEOUT claims)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
