#!/usr/bin/env python3
"""Rep-paired ratios across thread-budget conditions.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-22
Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
Retire when: the residual wall-gap evidence note is merged; delete then.
Related:     2026-08-21_h2h_thread_sweep.bash (produces what this reads).

WHY REP-PAIRED AND NOT PER-ARM MEANS
The sweep rotates its conditions INSIDE each replicate, so the legs of one rep ran within minutes
of each other and saw the same host. That makes a rep a valid pairing unit, exactly as a pair is in
the CLI-vs-service campaign, and forming the ratio inside a rep cancels the load drift that
otherwise dominates.

It matters here: the per-arm rate means carry a ~12% cv purely from host drift across the sweep,
while the paired CLI-vs-service rate held a 3.7% cv. Comparing per-arm means would hide a real
30% effect inside the noise, or manufacture one.

Reads the per-candidate-epoch RATE by default, because the direct CLI's candidate WORK varies run
to run (juniper-cascor#532, divergence rate 0.768) and the rate is the channel that stays stable
across a 2x work swing.

Usage: python util/ad-hoc/2026-08-22_h2h_sweep_ratios.py <SWEEP_DIR> <BASELINE_COND> <COND> [COND...]
       Conditions are the suffixes used by the sweep driver (e.g. default 16 2).
Exit:  0 on a report; 2 if a condition had no parseable leg.
"""

from __future__ import annotations

import importlib.util
import statistics
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_det", _HERE / "2026-08-20_determinism_nrun.py")
_det = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_det)


def legs(sweep: Path, cond: str) -> "list[dict]":
    dirs = sorted(p for p in sweep.glob(f"t{cond}-r*") if (p / "logs").is_dir())
    return [_det.parse_run(p) for p in dirs]


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    sweep, base = Path(sys.argv[1]), sys.argv[2]
    others = sys.argv[3:]

    data = {c: legs(sweep, c) for c in [base] + others}
    for c, rows in data.items():
        if not rows:
            print(f"sweep-ratios: no parseable leg for condition {c!r}", file=sys.stderr)
            return 2

    n = min(len(v) for v in data.values())
    print(f"{'rep':>3}  " + "  ".join(f"{c+' s/ep':>13}" for c in [base] + others))
    print("-" * (5 + 15 * (1 + len(others))))
    for i in range(n):
        cells = [f"{data[c][i]['s_per_cand_epoch']:>13.5f}" for c in [base] + others]
        print(f"{i + 1:>3}  " + "  ".join(cells))

    print(f"\n=== rep-paired rate ratios vs {base} ===")
    for c in others:
        ratios = [data[c][i]["s_per_cand_epoch"] / data[base][i]["s_per_cand_epoch"]
                  for i in range(n)
                  if data[c][i]["s_per_cand_epoch"] and data[base][i]["s_per_cand_epoch"]]
        if not ratios:
            print(f"  {c:<14}: n/a")
            continue
        m = statistics.mean(ratios)
        sd = statistics.stdev(ratios) if len(ratios) > 1 else None
        if sd is None:
            print(f"  {c:<14}: {m:.3f}  [n=1]")
            continue
        half = 1.96 * sd / len(ratios) ** 0.5
        print(f"  {c:<14}: {m:.3f} ± {sd:.3f}   95% CI [{m - half:.3f}, {m + half:.3f}]  [n={len(ratios)}]"
              + ("   <-- interval EXCLUDES 1.0" if m - half > 1.0 or m + half < 1.0 else "   (interval includes 1.0: no effect demonstrated)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
