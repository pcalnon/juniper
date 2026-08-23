#!/usr/bin/env python3
"""Is the per-epoch penalty real arithmetic, or just pool load imbalance?

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-21
Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
Retire when: the residual wall-gap evidence note is merged; delete then.
Related:     2026-08-21_h2h_paired_ratio.py (whose `rate` column this validates or refutes);
             2026-08-21_cascor_seeds_and_balance_diag.patch (the build that logs what this reads).

THE PROBLEM WITH THE RATE COLUMN
The paired analyser reports `s / candidate epoch` = candidate-phase WALL divided by TOTAL epochs
summed over all candidates. That is not a per-epoch cost, and treating it as one is a mistake worth
catching before a fix gets aimed at the wrong thing.

A candidate round runs `candidate_pool_size` candidates over `num_processes` workers -- 8 over 7
here -- so at least one worker runs two candidates sequentially. The round's WALL is therefore set
by the busiest worker's CRITICAL PATH, not by the total:

    wall  ~=  per_epoch_cost  x  max_over_workers(sum of that worker's candidates' epochs)

Divide that wall by the TOTAL instead, and the answer moves whenever the epoch distribution across
the pool changes shape -- even at identical arithmetic cost. A path whose candidates finish
unevenly looks slower per epoch than one whose candidates finish together, purely from how the work
packed.

WHAT THIS COMPUTES
Per round, from the diagnostic build's `epochs_completed` records:

  total       sum over candidates (what the rate column divides by)
  max         the single longest candidate
  critical    LPT estimate of the busiest worker's load: sort candidates descending and greedily
              assign each to the currently-least-loaded worker. The pool dispatches dynamically,
              which is what LPT models, so this is a close estimate of the real critical path --
              and it is the denominator a per-epoch cost should actually use.
  imbalance   critical / (total / n_workers), i.e. how much worse the packing is than a perfect
              split. 1.00 is perfect; higher means the round is waiting on a straggler.

If the two arms have similar imbalance, the rate column is measuring arithmetic and a fix should
look at the worker environment. If the CLI's imbalance is systematically higher, part or all of the
"rate penalty" is scheduling, and the fix is a different one entirely.

Usage: python util/ad-hoc/2026-08-21_h2h_pool_balance.py <ARM_LABEL> <RUN_DIR> [<ARM_LABEL> <RUN_DIR> ...]
Exit:  0 on a report; 2 if no run carried DIAG epoch records (wrong build?).
"""

from __future__ import annotations

import re
import statistics
import sys
from pathlib import Path

RE_ROUND = re.compile(r"train_candidates: Executing candidate training with (\d+) processes")
RE_EPOCHS = re.compile(r"CandidateUnit: train: DIAG: candidate_index=(\d+) correlation_exact=\S+ epochs_completed=(\d+)")


def segments(run_dir: Path) -> "list[Path]":
    logs = run_dir / "logs"
    base = logs / "juniper_cascor.log"
    rot = []
    if logs.is_dir():
        for p in logs.glob("juniper_cascor.log.*"):
            if p.name.rsplit(".", 1)[-1].isdigit():
                rot.append((int(p.name.rsplit(".", 1)[-1]), p))
    return [p for _n, p in sorted(rot, reverse=True)] + ([base] if base.exists() else [])


def lpt_critical(epochs: "list[int]", workers: int) -> int:
    """Longest-processing-time estimate of the busiest worker's total."""
    loads = [0] * max(1, workers)
    for e in sorted(epochs, reverse=True):
        i = loads.index(min(loads))
        loads[i] += e
    return max(loads)


def parse(run_dir: Path) -> "tuple[list[list[int]], int]":
    rounds: "list[list[int]]" = []
    workers = 0
    for seg in segments(run_dir):
        try:
            fh = seg.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if (m := RE_ROUND.search(line)):
                    rounds.append([])
                    workers = int(m.group(1))
                elif (m := RE_EPOCHS.search(line)):
                    if rounds:
                        rounds[-1].append(int(m.group(2)))
    return [r for r in rounds if r], workers


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2:
        print(__doc__, file=sys.stderr)
        return 2

    results = []
    for i in range(0, len(args), 2):
        label, run_dir = args[i], Path(args[i + 1])
        rounds, workers = parse(run_dir)
        if not rounds:
            print(f"  (no DIAG epoch records in {run_dir} -- instrumented build not used?)", file=sys.stderr)
            continue
        totals = [sum(r) for r in rounds]
        crits = [lpt_critical(r, workers) for r in rounds]
        imbal = [c / (t / workers) for c, t in zip(crits, totals) if t]
        results.append({
            "label": label, "rounds": len(rounds), "workers": workers,
            "total": sum(totals), "critical": sum(crits),
            "imbalance_mean": statistics.mean(imbal), "imbalance_sd": statistics.stdev(imbal) if len(imbal) > 1 else None,
            "cands": statistics.mean(len(r) for r in rounds),
        })
    if not results:
        print("pool-balance: no usable run", file=sys.stderr)
        return 2

    print(f"{'arm':<16} {'rounds':>6} {'workers':>7} {'cands/rnd':>9} {'total_ep':>10} "
          f"{'critical_ep':>12} {'imbalance':>10}")
    print("-" * 78)
    for r in results:
        sd = f" ± {r['imbalance_sd']:.3f}" if r["imbalance_sd"] is not None else ""
        print(f"{r['label']:<16} {r['rounds']:>6} {r['workers']:>7} {r['cands']:>9.1f} "
              f"{r['total']:>10} {r['critical']:>12} {r['imbalance_mean']:>7.3f}{sd}")

    if len(results) == 2:
        a, b = results
        print(f"\n=== {b['label']} / {a['label']} ===")
        print(f"  total epochs      : {b['total'] / a['total']:.3f}x   <- what the rate column divides by")
        print(f"  CRITICAL epochs   : {b['critical'] / a['critical']:.3f}x   <- what actually sets the wall")
        print(f"  imbalance         : {b['imbalance_mean'] / a['imbalance_mean']:.3f}x")
        drift = abs(b["critical"] / a["critical"] - b["total"] / a["total"])
        if drift < 0.03:
            print("\n  -> The two denominators agree, so pool packing is NOT distorting the rate\n"
                  "     column: a per-epoch penalty measured against totals is measuring arithmetic.")
        else:
            print(f"\n  -> They DISAGREE by {drift:.3f}. The rate column is partly a packing artefact;\n"
                  "     recompute the per-epoch cost against CRITICAL epochs before attributing it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
