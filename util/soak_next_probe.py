#!/usr/bin/env python3
"""Emit the next soak probe's task, UNPRIMED, for pasting into a fresh session.

Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

The re-soak protocol (soak ledger sections 7, 15.4 and 17) has two requirements
that are easy to state and easy to violate:

1. the session must be FRESH -- started after the rung-1 index rows landed on
   2026-08-31, or its memory snapshot predates the intervention being measured;
2. the session must be UNPRIMED -- it must never see the word "soak", the fact,
   the pointer, or the prediction. Priming is what invalidated option A
   (ledger section 11 D2), and a primed run cannot be un-primed afterwards.

Requirement 2 is why this exists. Selecting a probe by hand means reading its
fact and pointer, and a human who has just read them writes a different prompt
than one who has not. This prints the probe's `task` and NOTHING else, so the
text can be moved to a fresh session without the operator having read the answer
they are about to test for.

Everything else -- the fact, the pointer, the discriminator, the prediction --
stays hidden behind `--reveal`, which is for SCORING, after the run.

Usage:
    python3 util/soak_next_probe.py                 # the task to paste, alone
    python3 util/soak_next_probe.py --probe-id P19-port-check-fail-opens
    python3 util/soak_next_probe.py --status        # coverage, no task text
    python3 util/soak_next_probe.py --reveal --probe-id <id>   # SCORING ONLY
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBES = ROOT / "conf" / "soak_probes.json"
LEDGER = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"

# The rung-1 index rows landed on this date. A run recorded before it measures
# the pre-intervention index and must not be pooled with post-intervention runs
# (ledger section 15.4).
INTERVENTION = "2026-08-31"


def load_rows() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]


def post_intervention(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if r.get("kind") not in (None, "observation") or r.get("arm") != "seeded":
            continue
        ts = str(r.get("ts") or "")
        if ts >= INTERVENTION:
            out.append(r)
    return out


def pick_next(probes: list[dict], runs: Counter) -> dict:
    """Least post-intervention coverage first, then registry order.

    Pre-intervention rows must not enter ``runs``. Pooling them here is how a
    probe that rung 1 never touched looks already-sampled and billed sessions
    keep landing on the already-covered ones (ledger §15.4; consensus §4.6).
    """
    return min(probes, key=lambda p: (runs.get(p["probe_id"], 0), probes.index(p)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-id", default=None)
    ap.add_argument("--status", action="store_true", help="coverage only; prints no task")
    ap.add_argument(
        "--reveal",
        action="store_true",
        help="show fact/pointer/discriminator. SCORING ONLY -- never before a run",
    )
    args = ap.parse_args()

    probes = json.loads(PROBES.read_text(encoding="utf-8"))["probes"]
    by_id = {p["probe_id"]: p for p in probes}
    runs = Counter(r.get("probe_id") for r in post_intervention(load_rows()))

    if args.status:
        print(f"post-intervention runs (ts >= {INTERVENTION}), by probe:")
        for p in probes:
            n = runs.get(p["probe_id"], 0)
            print(f"  {n:2d}  {p['probe_id']}")
        print(f"\ntotal post-intervention seeded runs: {sum(runs.values())}")
        print("Facts and pointers are deliberately not shown. Use --reveal when SCORING.")
        return 0

    if args.probe_id:
        probe = by_id.get(args.probe_id)
        if probe is None:
            print(f"no such probe: {args.probe_id}", file=sys.stderr)
            return 2
    else:
        probe = pick_next(probes, runs)

    if args.reveal:
        print(f"probe_id      : {probe['probe_id']}")
        print(f"severity      : {probe.get('severity')}    area: {probe.get('area')}")
        print(f"fact          : {probe.get('fact')}")
        print(f"pointer       : {probe.get('pointer')}")
        print(f"evidence      : {probe.get('evidence')}")
        print(f"discriminator : {probe.get('discriminator')}")
        print(f"post-interv.  : {runs.get(probe['probe_id'], 0)} run(s)")
        print()
        print("Record with:")
        print(f"  python3 util/soak_ledger.py probe-run --probe-id {probe['probe_id']} \\")
        print("      --outcome follow|source-recovered|miss --session <id> --scored-by <who>")
        return 0

    # The unprimed payload. Nothing above this line is printed in this mode.
    sys.stderr.write(
        f"# probe {probe['probe_id']} | {runs.get(probe['probe_id'], 0)} post-intervention run(s)\n"
        f"# Paste ONLY the stdout below into a session started after {INTERVENTION}.\n"
        f"# Do not mention the soak. Do not run --reveal until you are scoring.\n"
        f"# generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
    )
    print(probe["task"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
