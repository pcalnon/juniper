#!/usr/bin/env python3
"""2026-09-05_fleet_close_superseded.py -- close fleet PRs whose content was carried elsewhere.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY

A FALSE CLOSE LOSES REAL WORK, and a bot PR closed by mistake will not be reopened by
its author. So closing is gated on evidence that the content actually landed, and the
comment left behind names the carrying PR so the trail survives the close.

This script refuses to close unless the superseding PR is MERGED -- closing against a
PR that is merely open would strand the content if that PR were later abandoned. It
re-reads each target's live state first (fleet PRs are merged concurrently by other
sessions; juniper-ml#1702 was already MERGED before this arc reached it), and skips
anything not OPEN rather than erroring.

Dry-run by default.

Usage:
    python util/ad-hoc/2026-09-05_fleet_close_superseded.py \\
        --repo juniper-ml --owner pcalnon --superseded-by 1746 \\
        --pr 1707 --pr 1709 [...] [--execute]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys

COMMENT = """Superseded by #{by}, which is **merged**.

This PR's documentation content was carried there verbatim, together with nine sibling
fleet docs PRs, because all ten edit `docs/REFERENCE.md` and this repo runs
`strict_required_status_checks_policy: true` with `allow_update_branch: false`: each
merge makes the others `BEHIND`, every resync is a fresh 17-check battery, and each
landed merge advances the `**Version:**` line that every sibling also rewrites. Merging
them one at a time degrades as it runs -- #1707 went `DIRTY` mid-train.

Nothing here was dropped. #{by} was verified in both directions: every `.md` line this
branch adds is present in the merged result, and `juniper-docs-additions-check` reports
no unwaived deletions against `main`.

Closing as superseded, not as rejected -- the work landed.
"""


def gh_json(*args: str):
    cp = subprocess.run(["gh", *args], capture_output=True, text=True)  # nosec B603
    if cp.returncode != 0:
        return {"__error__": (cp.stderr or cp.stdout).strip()[:200]}
    try:
        return json.loads(cp.stdout)
    except json.JSONDecodeError:
        return {"__error__": "non-JSON from gh"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--superseded-by", type=int, required=True)
    ap.add_argument("--pr", type=int, action="append", required=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args(argv)
    slug = f"{args.owner}/{args.repo}"

    # GATE: never close against a PR that has not landed.
    carrier = gh_json("pr", "view", str(args.superseded_by), "--repo", slug, "--json", "state,mergedAt")
    if carrier.get("state") != "MERGED":
        print(f"REFUSING: #{args.superseded_by} is {carrier.get('state')}, not MERGED. "
              "Closing now would strand this content.", file=sys.stderr)
        return 2
    print(f"carrier #{args.superseded_by} MERGED at {carrier.get('mergedAt')} -- proceeding\n")

    closed = skipped = 0
    body = COMMENT.format(by=args.superseded_by)
    for pr in args.pr:
        st = gh_json("pr", "view", str(pr), "--repo", slug, "--json", "state,title")
        if "__error__" in st:
            print(f"  #{pr}: ERROR {st['__error__']}")
            skipped += 1
            continue
        if st.get("state") != "OPEN":
            print(f"  #{pr}: SKIP (already {st.get('state')})")
            skipped += 1
            continue
        if not args.execute:
            print(f"  #{pr}: WOULD CLOSE -- {st.get('title', '')[:60]}")
            closed += 1
            continue
        cp = subprocess.run(  # nosec B603
            ["gh", "pr", "close", str(pr), "--repo", slug, "--comment", body],
            capture_output=True, text=True,
        )
        after = gh_json("pr", "view", str(pr), "--repo", slug, "--json", "state")
        if after.get("state") == "CLOSED":
            print(f"  #{pr}: CLOSED")
            closed += 1
        else:
            print(f"  #{pr}: FAILED -- state={after.get('state')} {(cp.stderr or '').strip()[:120]}")
            skipped += 1
    print(f"\n{'closed' if args.execute else 'would close'}: {closed}; skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
