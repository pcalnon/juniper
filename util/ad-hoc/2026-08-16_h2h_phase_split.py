#!/usr/bin/env python3
"""WIDE-BUDGET HEAD-TO-HEAD -- split a run's training span into candidate vs output phases.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-16
Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
Retire when: the wide-budget head-to-head evidence note is merged; delete then.
Related:     2026-08-16_h2h_collect.py (the arm-level table this explains).

WHY
The cap-64 replicate r0 finished with the two arms having done provably IDENTICAL work -- 512
candidate trainings (64 iterations x pool 8) and 13000 output-epoch progress records (130,000
epochs) each -- yet the direct CLI's training span was 7412 s against the service's 3570 s. Equal
work at 2.08x the wall is a THROUGHPUT difference, and a throughput difference has to live in one
of the two phases. Reporting "the CLI is 2x slower" without saying which phase, and why, would be
exactly the unexamined ratio the smoke note refused to print.

HOW
A cascade iteration in the parent log looks like:

    train_candidates:2166        <- candidate phase begins
    train_candidate_worker:...   <- pool members (8 per iteration)
    train_output_layer:2100      <- output pass progress, one record per 10 epochs
    train_output_layer:2120      <- "Final output layer training loss" = iteration boundary
    grow_network:4650            <- iteration summary

So within an iteration the candidate phase runs from its start to the FIRST output-progress
record, and the output pass runs from there to the boundary. Timestamps are second-resolution,
which is noise at these durations but is why per-iteration figures are reported as totals and
medians rather than to the millisecond.

Usage: python util/ad-hoc/2026-08-16_h2h_phase_split.py <LOG_DIR> [<LOG_DIR> ...]
       Each LOG_DIR is a directory holding juniper_cascor.log (+ rotated .N segments).
Exit:  0 analysed; 2 nothing parseable.
"""

from __future__ import annotations

import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

TS = re.compile(r"\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)")
MARK = re.compile(r"(train_candidates:2166|train_output_layer:2100|train_output_layer:2120|fit:1918|fit:1936)")


def segments(d: Path) -> "list[Path]":
    base = d / "juniper_cascor.log"
    rot = []
    for p in d.glob("juniper_cascor.log.*"):
        if p.name.rsplit(".", 1)[-1].isdigit():
            rot.append((int(p.name.rsplit(".", 1)[-1]), p))
    return [p for _n, p in sorted(rot, reverse=True)] + ([base] if base.exists() else [])


def events(d: Path):
    for seg in segments(d):
        with seg.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = MARK.search(line)
                if not m:
                    continue
                t = TS.search(line)
                if t:
                    yield m.group(1), datetime.strptime(t.group(1), "%Y-%m-%d %H:%M:%S")


def analyse(d: Path) -> dict | None:
    cand_start = None
    out_start = None
    cand_secs: list[float] = []
    out_secs: list[float] = []
    fit0 = fit1 = None
    for kind, ts in events(d):
        if kind == "fit:1918":
            fit0 = ts
        elif kind == "fit:1936":
            fit1 = ts
        elif kind == "train_candidates:2166":
            cand_start, out_start = ts, None
        elif kind == "train_output_layer:2100":
            # First output-progress record after a candidate phase closes that phase.
            if cand_start is not None and out_start is None:
                cand_secs.append((ts - cand_start).total_seconds())
                out_start = ts
        elif kind == "train_output_layer:2120":
            if out_start is not None:
                out_secs.append((ts - out_start).total_seconds())
            cand_start = out_start = None
    if not cand_secs and not out_secs:
        return None
    return {
        "dir": d,
        "span": (fit1 - fit0).total_seconds() if fit0 and fit1 else None,
        "iterations": len(cand_secs),
        "cand_total": sum(cand_secs),
        "cand_median": statistics.median(cand_secs) if cand_secs else None,
        "out_total": sum(out_secs),
        "out_median": statistics.median(out_secs) if out_secs else None,
        "out_passes": len(out_secs),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    rows = [r for r in (analyse(Path(a)) for a in sys.argv[1:]) if r]
    if not rows:
        print("phase split: nothing parseable", file=sys.stderr)
        return 2
    print(f"{'log dir':<52} {'span_s':>7} {'iters':>6} {'cand_total':>11} {'cand_med':>9} {'out_total':>10} {'out_med':>8} {'accounted':>10}")
    print("-" * 122)
    for r in rows:
        acct = r["cand_total"] + r["out_total"]
        pct = f"{100 * acct / r['span']:.0f}%" if r["span"] else "-"
        print(f"{str(r['dir'])[-52:]:<52} {r['span'] or 0:>7.0f} {r['iterations']:>6} {r['cand_total']:>11.0f} {r['cand_median'] or 0:>9.1f} {r['out_total']:>10.0f} {r['out_median'] or 0:>8.1f} {pct:>10}")
    if len(rows) == 2:
        a, b = rows
        print()
        print(f"candidate phase : {b['cand_total'] / a['cand_total']:.2f}x   ({a['cand_total']:.0f} s -> {b['cand_total']:.0f} s)")
        print(f"output   phase : {b['out_total'] / a['out_total']:.2f}x   ({a['out_total']:.0f} s -> {b['out_total']:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
