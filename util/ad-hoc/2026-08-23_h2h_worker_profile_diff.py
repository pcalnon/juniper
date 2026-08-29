#!/usr/bin/env python3
"""Diff aggregated forked-worker cProfile dumps between the two entry points.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-23
Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the residual wall-gap evidence note is merged; delete then.
Related:     util/experiments/suites/p4/e-n-profile-cap4.yaml (the service leg);
             the JUNIPER_CASCOR_WORKER_PROFILE dispatcher in train_candidate_worker.

WHY PER-CALL AND NOT TOTAL
The two arms do not necessarily run the same number of candidate epochs -- the direct CLI is
nondeterministic (juniper-cascor#532) and its candidate work has been measured 0.913x to 1.680x the
service's on identical configuration. Comparing TOTAL time per function would therefore mostly
measure how much work each arm happened to do, which is already known and is not what a profile is
for.

So the headline column is **tottime per call**: the cost of one invocation of that function,
excluding its callees. If the CLI path is genuinely slower per unit of work, that shows up as the
same functions costing more per call. If instead the arms differ only in how OFTEN things are
called, per-call costs match and the ncalls ratio carries the difference -- a completely different
finding, and one that would point back at the work term rather than at the runtime.

cProfile's overhead inflates both arms, so absolute times here are not the real cost. Ratios
between the arms are the usable output, and only for functions with enough calls to be stable.

Usage: python util/ad-hoc/2026-08-23_h2h_worker_profile_diff.py <BASE_LABEL> <BASE_DIR> <OTHER_LABEL> <OTHER_DIR> [--top N] [--min-calls M]
Exit:  0 on a report; 2 if either directory held no readable profile.
"""

from __future__ import annotations

import argparse
import pstats
import sys
from pathlib import Path


def load(d: Path) -> "tuple[pstats.Stats | None, int]":
    files = sorted(d.glob("*.prof"))
    st = None
    used = 0
    for f in files:
        try:
            st = pstats.Stats(str(f)) if st is None else st.add(str(f))
            used += 1
        except Exception:  # a worker killed mid-dump leaves a truncated file; skip it loudly below
            continue
    return st, used


def rows(st: pstats.Stats) -> "dict[str, tuple[int, float, float]]":
    """func key -> (ncalls, tottime, cumtime)."""
    out = {}
    for func, (_cc, nc, tt, ct, _callers) in st.stats.items():  # type: ignore[attr-defined]
        fname, line, name = func
        # Trim to the last two path components: full paths differ between the two checkouts and
        # would make otherwise-identical functions look like different rows.
        short = "/".join(Path(fname).parts[-2:]) if fname not in ("~", "") else fname
        out[f"{short}:{line}({name})"] = (nc, tt, ct)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base_label")
    ap.add_argument("base_dir", type=Path)
    ap.add_argument("other_label")
    ap.add_argument("other_dir", type=Path)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--min-calls", type=int, default=50)
    args = ap.parse_args()

    a_st, a_n = load(args.base_dir)
    b_st, b_n = load(args.other_dir)
    if a_st is None or b_st is None:
        print(f"profile-diff: no readable .prof in {args.base_dir if a_st is None else args.other_dir}", file=sys.stderr)
        return 2
    print(f"{args.base_label}: {a_n} profiles   |   {args.other_label}: {b_n} profiles")

    a, b = rows(a_st), rows(b_st)
    shared = [k for k in a if k in b and a[k][0] >= args.min_calls and b[k][0] >= args.min_calls]
    if not shared:
        print("profile-diff: no shared function met --min-calls", file=sys.stderr)
        return 2

    # Rank by how much TIME the slower arm spends there: a large per-call ratio on a function that
    # accounts for microseconds is a curiosity, not an explanation.
    shared.sort(key=lambda k: -max(a[k][1], b[k][1]))

    print(f"\n{'function':<58} {'calls a/b':>17} {'µs/call a':>10} {'µs/call b':>10} {'per-call':>9} {'tot b/a':>8}")
    print("-" * 118)
    for k in shared[: args.top]:
        anc, att, _ = a[k]
        bnc, btt, _ = b[k]
        a_per = att / anc * 1e6
        b_per = btt / bnc * 1e6
        print(f"{k[-58:]:<58} {anc:>8}/{bnc:<8} {a_per:>10.2f} {b_per:>10.2f} "
              f"{(b_per / a_per if a_per else 0):>9.3f} {(btt / att if att else 0):>8.3f}")

    a_tot = sum(v[1] for v in a.values())
    b_tot = sum(v[1] for v in b.values())
    a_calls = sum(v[0] for v in a.values())
    b_calls = sum(v[0] for v in b.values())
    print("\n=== aggregate over ALL functions ===")
    print(f"  total tottime   : {args.base_label} {a_tot:.1f}s   {args.other_label} {b_tot:.1f}s   ratio {b_tot / a_tot:.3f}")
    print(f"  total calls     : {args.base_label} {a_calls}   {args.other_label} {b_calls}   ratio {b_calls / a_calls:.3f}")
    print(f"  time per call   : {a_tot / a_calls * 1e6:.3f} µs   {b_tot / b_calls * 1e6:.3f} µs   "
          f"ratio {(b_tot / b_calls) / (a_tot / a_calls):.3f}")
    print("\n  If 'time per call' ~= 1.0 while 'total calls' carries the ratio, the arms run the SAME\n"
          "  code at the SAME speed and simply do different amounts of work -- which points back at\n"
          "  the work term, not the runtime. If per-call is elevated, the runtime really is slower.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
