#!/usr/bin/env python3
"""Diff py-spy --native collapsed stacks between the two entry points, per unit of work.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-23
Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the residual wall-gap evidence note is merged; delete then.
Related:     2026-08-23_pyspy_conda_shim.bash (service leg), 2026-08-23_pyspy_cli_leg.bash (CLI leg).

WHY SAMPLES PER CANDIDATE EPOCH, AND NOT PERCENTAGE OF SAMPLES
The obvious normalisation -- each frame's share of total samples -- cannot answer this question. If
the CLI spends the same *proportion* of its time everywhere but takes longer per epoch, every share
matches and the diff reports nothing while the penalty is plainly real.

So each frame's sample count is divided by that arm's candidate EPOCHS. py-spy samples at a fixed
rate, so samples are proportional to CPU-time; dividing by epochs gives CPU-time per unit of work,
which is exactly the quantity measured at 1.33x-1.55x and exactly what a fix would have to move.

SELF vs INCLUSIVE
`self` is samples where the frame was the LEAF -- time actually executing there. `inclusive` counts
every stack containing it. Self is what localises a cost; inclusive is what attributes it to a
caller. Both are reported, and they answer different questions: a big inclusive difference with no
self difference means the extra time is in something that frame CALLS.

WHAT A NEGATIVE RESULT LOOKS LIKE
If no frame shows a meaningful self-per-epoch difference, the penalty is not CPU time in either
arm's code at all -- it is time not being spent (blocking, waiting, scheduling), which a CPU
sampler under-represents by construction. That would be a real finding and should be reported as
one rather than mined for the largest ratio in the noise.

Usage:
    python util/ad-hoc/2026-08-23_h2h_native_profile_diff.py \
        <A_LABEL> <A_RAW> <A_EPOCHS> <B_LABEL> <B_RAW> <B_EPOCHS> [--top N] [--min-samples M]
Exit: 0 on a report; 2 if either input had no parseable sample.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path


def parse(raw: Path) -> "tuple[dict[str, int], dict[str, int], int]":
    """-> (self_samples_by_frame, inclusive_samples_by_frame, total_samples)."""
    self_s: "dict[str, int]" = defaultdict(int)
    incl_s: "dict[str, int]" = defaultdict(int)
    total = 0
    with raw.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            stack, _, count_s = line.rpartition(" ")
            try:
                count = int(count_s)
            except ValueError:
                continue
            frames = [f for f in stack.split(";") if f]
            if not frames:
                continue
            total += count
            self_s[frames[-1]] += count
            # A recursive frame must not be counted twice for one sample.
            for f in set(frames):
                incl_s[f] += count
    return self_s, incl_s, total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a_label")
    ap.add_argument("a_raw", type=Path)
    ap.add_argument("a_epochs", type=int)
    ap.add_argument("b_label")
    ap.add_argument("b_raw", type=Path)
    ap.add_argument("b_epochs", type=int)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-samples", type=int, default=200)
    args = ap.parse_args()

    a_self, a_incl, a_tot = parse(args.a_raw)
    b_self, b_incl, b_tot = parse(args.b_raw)
    if not a_tot or not b_tot:
        print("native-diff: no samples parsed", file=sys.stderr)
        return 2

    print(f"{args.a_label}: {a_tot} samples over {args.a_epochs} candidate epochs "
          f"({a_tot / args.a_epochs:.3f} samples/epoch)")
    print(f"{args.b_label}: {b_tot} samples over {args.b_epochs} candidate epochs "
          f"({b_tot / args.b_epochs:.3f} samples/epoch)")
    print(f"\nOVERALL samples/epoch ratio ({args.b_label}/{args.a_label}): "
          f"{(b_tot / args.b_epochs) / (a_tot / args.a_epochs):.3f}")

    keys = [k for k in set(a_self) | set(b_self)
            if a_self.get(k, 0) + b_self.get(k, 0) >= args.min_samples]
    # Rank by the ABSOLUTE per-epoch difference: a 10x ratio on a frame worth
    # 0.001 samples/epoch explains nothing, and sorting by ratio surfaces exactly those.

    def delta(k: str) -> float:
        return (b_self.get(k, 0) / args.b_epochs) - (a_self.get(k, 0) / args.a_epochs)

    keys.sort(key=lambda k: -abs(delta(k)))

    print("\n=== SELF time per candidate epoch, largest absolute differences ===")
    print(f"{'frame':<64} {'a s/ep':>9} {'b s/ep':>9} {'delta':>9} {'ratio':>7}")
    print("-" * 102)
    for k in keys[: args.top]:
        a_pe = a_self.get(k, 0) / args.a_epochs
        b_pe = b_self.get(k, 0) / args.b_epochs
        ratio = (b_pe / a_pe) if a_pe else float("inf")
        print(f"{k[-64:]:<64} {a_pe:>9.4f} {b_pe:>9.4f} {delta(k):>+9.4f} {ratio:>7.2f}")

    tot_delta = sum(delta(k) for k in keys)
    print(f"\n  sum of listed deltas: {tot_delta:+.4f} samples/epoch "
          f"(overall gap {(b_tot / args.b_epochs) - (a_tot / args.a_epochs):+.4f})")
    print("\n  A per-epoch ratio near 1.0 with no frame carrying a meaningful delta means the\n"
          "  penalty is NOT CPU time in either arm's code -- it is time not being spent, which a\n"
          "  CPU sampler under-represents by construction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
