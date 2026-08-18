#!/usr/bin/env python3
"""Compare repeated runs of an identical config: deterministic, or not?

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-18
Status:      ad-hoc -- one-off (CLI reproducibility investigation)
Retire when: the reproducibility defect is root-caused and written up; delete then.
Related:     2026-08-18_h2h_determinism_sweep.bash (produces the pairs this reads).

The direct CLI finished two runs of one identical cell 10 pp apart in validation accuracy while the
service reproduced the same cell bit-identically. A pair of final numbers says "these differ" but
not *where* they started differing, and the where is the useful part: the two CLI runs were
identical through iteration 1 and diverged at iteration 2 -- which rules out the dataset, the
network initialisation and the first candidate round, and points at something that only comes into
play once training is under way.

So this reports the FIRST DIVERGENT ITERATION rather than a bare pass/fail, using the per-iteration
``grow_network`` trace as the fingerprint.

Usage: python util/ad-hoc/2026-08-18_h2h_pair_compare.py <RUN_DIR> [<RUN_DIR> ...]
       A RUN_DIR is any directory containing logs/juniper_cascor.log (+ rotated segments).
       Directories are grouped into pairs by name; a trailing -a / -b suffix is stripped.
Exit:  0 always -- this is a report, not a gate.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

RE_ITER = re.compile(r"grow_network:\d+\].*Iteration (\d+) - Train Loss: ([0-9.]+), Train Accuracy: ([0-9.]+)")
RE_ACC = re.compile(r"calculate_accuracy:\d+\].*Calculated accuracy: ([0-9.]+)")
# A run is only comparable once training has actually finished. Without this the tool will happily
# diff an IN-FLIGHT log against a finished one and report a confident divergence that is really
# just "one of these is still running" -- which it did, to me, on first use.
RE_DONE = re.compile(r"fit:\d+\].*Training completed\.")


def _segments(d: Path) -> "list[Path]":
    """The run's parent log plus any rotated siblings, oldest first."""
    logs = d / "logs"
    base = logs / "juniper_cascor.log"
    rot = []
    if logs.is_dir():
        for p in logs.glob("juniper_cascor.log.*"):
            suffix = p.name.rsplit(".", 1)[-1]
            if suffix.isdigit():
                rot.append((int(suffix), p))
    return [p for _n, p in sorted(rot, reverse=True)] + ([base] if base.exists() else [])


def trace(run_dir: Path) -> dict:
    iters: "list[tuple[int, str, str]]" = []
    accs: "list[str]" = []
    complete = False
    for seg in _segments(run_dir):
        with seg.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if (m := RE_ITER.search(line)):
                    iters.append((int(m.group(1)), m.group(2), m.group(3)))
                elif (m := RE_ACC.search(line)):
                    accs.append(m.group(1))
                elif RE_DONE.search(line):
                    complete = True
    # SpiralProblem.evaluate calls calculate_accuracy on (train) then (test) last.
    return {"dir": run_dir, "iters": iters, "complete": complete, "train": accs[-2] if len(accs) >= 2 else None, "val": accs[-1] if len(accs) >= 2 else None}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 0

    groups: "dict[str, list[dict]]" = defaultdict(list)
    for arg in sys.argv[1:]:
        d = Path(arg)
        t = trace(d)
        if not t["iters"]:
            print(f"  (no iteration trace in {d}) -- skipped", file=sys.stderr)
            continue
        groups[re.sub(r"-[ab]$", "", d.name)].append(t)

    for label, runs in sorted(groups.items()):
        print(f"\n=== {label} ({len(runs)} run(s)) ===")
        for r in runs:
            state = "" if r["complete"] else "  <-- IN FLIGHT (no 'Training completed.')"
            print(f"  {r['dir'].name:<18} iterations={len(r['iters']):<4} train={r['train']} val={r['val']}{state}")
        if len(runs) < 2:
            print("  (need two runs to judge determinism)")
            continue
        unfinished = [r for r in runs if not r["complete"]]
        if unfinished:
            # Refuse rather than guess. A partial trace diffs as a divergence, and a false
            # NONDETERMINISTIC verdict is worse than no verdict on a question this tool exists
            # to answer carefully.
            print(f"  VERDICT: UNCOMPARABLE -- {len(unfinished)} run(s) still in flight; re-run once training has completed")
            continue
        a, b = runs[0], runs[1]
        first = None
        for ia, ib in zip(a["iters"], b["iters"]):
            if ia != ib:
                first = (ia, ib)
                break
        if first is None and len(a["iters"]) == len(b["iters"]):
            print(f"  VERDICT: DETERMINISTIC -- {len(a['iters'])} iterations identical, val {a['val']} in both")
        elif first is None:
            print(f"  VERDICT: DIVERGENT -- traces agree where they overlap but differ in length ({len(a['iters'])} vs {len(b['iters'])})")
        else:
            ia, ib = first
            print(f"  VERDICT: NONDETERMINISTIC -- first divergence at iteration {ia[0]}")
            print(f"           a: loss={ia[1]} acc={ia[2]}")
            print(f"           b: loss={ib[1]} acc={ib[2]}")
            print(f"           final val: {a['val']} vs {b['val']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
