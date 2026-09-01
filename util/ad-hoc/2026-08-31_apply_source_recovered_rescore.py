#!/usr/bin/env python3
"""Apply the owner's 2026-08-31 re-score to the source-recovered backlog.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc soak tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-31
Status:      ad-hoc -- one-shot migration of the 2026-08-22 backlog, which was
             scored before `source-recovered` existed as an outcome.
Retire when: the backlog is migrated. Future runs record the outcome directly
             (`probe-run --outcome source-recovered`); this verb is for history.

What it does
------------
For every seeded, in-scope, non-invalidated architectural MISS whose scorer note
says the fact was SOURCE-RECOVERED, append a `rescore` row moving it to
`source-recovered`. Each append carries the scorer's own words as its reason, so
the re-score is justified by the evidence recorded at scoring time rather than by
a decision taken afterwards.

What it deliberately does NOT do
--------------------------------
It will not touch a miss whose note lacks the SOURCE-RECOVERED marker. Two of the
eleven are real misses (both P15: the agent proposed removal rather than
convergence, one of them *after* retrieving the fact) and they must stay misses --
they are the only evidence in the ledger that the discriminator can still fail
something.

Dry run by default. `soak_ledger.py rescore` refuses a double re-score, so a
second run is a no-op rather than a corruption.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"
TOOL = ROOT / "util" / "soak_ledger.py"
SRC = re.compile(r"source[- ]recovered", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write (default: dry run)")
    args = ap.parse_args()

    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    inval = {r.get("invalidates") for r in rows if r.get("kind") == "invalidate"}
    already = {r.get("rescores") for r in rows if r.get("kind") == "rescore"}

    targets = [
        r for r in rows
        if r.get("kind") not in ("resolve", "invalidate", "rescore")
        and r.get("obs_id") not in inval
        and r.get("in_scope") is True
        and r.get("arm") == "seeded"
        and r.get("outcome") == "miss"
        and r.get("miss_class") != "pointer-defect"
        and SRC.search(r.get("note") or "")
        and r.get("obs_id") not in already
    ]
    skipped = [
        r for r in rows
        if r.get("kind") not in ("resolve", "invalidate", "rescore")
        and r.get("obs_id") not in inval
        and r.get("in_scope") is True
        and r.get("arm") == "seeded"
        and r.get("outcome") == "miss"
        and r.get("miss_class") != "pointer-defect"
        and not SRC.search(r.get("note") or "")
    ]

    print(f"to re-score : {len(targets)}")
    print(f"left as MISS: {len(skipped)}  (no SOURCE-RECOVERED marker in the scorer's note)")
    for r in skipped:
        print(f"    KEEP {r.get('probe_id')}  {(r.get('note') or '')[:110]}")
    print()

    rc_all = 0
    for r in targets:
        note = (r.get("note") or "").strip()
        reason = (
            "owner decision 2026-08-31: correct answer reached from source, not via the "
            "relocated pointer. Scorer's contemporaneous note: " + note[:400]
        )
        print(f"  {'APPLY' if args.apply else 'DRY  '} {r.get('probe_id'):34s} {r.get('obs_id')}")
        if not args.apply:
            continue
        cmd = [
            sys.executable, str(TOOL), "rescore",
            "--obs-id", r["obs_id"],
            "--to", "source-recovered",
            "--reason", reason,
        ]
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)  # nosec B603
        if p.returncode != 0:
            rc_all = 1
            print(f"      FAILED rc={p.returncode}: {p.stderr.strip()[:200]}")

    if not args.apply:
        print("\nDRY RUN -- nothing written. Pass --apply.")
    return rc_all


if __name__ == "__main__":
    raise SystemExit(main())
