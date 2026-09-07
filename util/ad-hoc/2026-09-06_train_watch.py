#!/usr/bin/env python3
"""
Emit one line per state change on a set of PRs, and exit when none is OPEN.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- one-off (cursor-fleet merge train)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-05_auto_merge_shepherd.py`, which does the syncing this only watches

A merge train under `strict_required_status_checks_policy` has a state that looks like progress
and is terminal: every check SUCCESS, auto-merge armed, `mergeStateStatus: BEHIND`, nothing
failing and nothing landing. So the watch reports the STATUS TRANSITIONS, not a heartbeat --
a PR that stops moving stops producing lines, and that silence is itself the signal.

Emits on every terminal state, not just MERGED: a CLOSED or a check failure has to break the
silence too, or a crashed train reads exactly like a slow one.

Usage:
    2026-09-06_train_watch.py <pr> [<pr> ...]

Exit: 0 when none of the PRs is OPEN; 1 if the poll budget runs out first.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
import time

REPO = "pcalnon/juniper-ml"
POLL_SECONDS = 45
MAX_POLLS = 80


def snapshot(prs: list[int]) -> dict[int, str]:
    out: dict[int, str] = {}
    for pr in prs:
        res = subprocess.run(
            ["gh", "pr", "view", str(pr), "--repo", REPO, "--json", "state,mergeStateStatus,statusCheckRollup"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if res.returncode != 0 or not res.stdout.strip():
            out[pr] = "UNREACHABLE"
            continue
        data = json.loads(res.stdout)
        failing = [c.get("name", "?") for c in (data.get("statusCheckRollup") or []) if c.get("conclusion") in ("FAILURE", "TIMED_OUT", "CANCELLED")]
        state = data.get("state", "?")
        label = f"{state}/{data.get('mergeStateStatus', '?')}"
        if failing:
            label += f" FAILING[{','.join(sorted(set(failing))[:3])}]"
        out[pr] = label
    return out


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    prs = [int(a) for a in args]
    previous: dict[int, str] = {}
    for _ in range(MAX_POLLS):
        current = snapshot(prs)
        for pr in prs:
            if current[pr] != previous.get(pr):
                print(f"#{pr}: {current[pr]}", flush=True)
        previous = current
        if not any(v.startswith("OPEN") for v in current.values()):
            print("train resolved: none OPEN", flush=True)
            return 0
        time.sleep(POLL_SECONDS)
    print("poll budget exhausted; still OPEN: " + ", ".join(f"#{p}" for p, v in previous.items() if v.startswith("OPEN")), flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
