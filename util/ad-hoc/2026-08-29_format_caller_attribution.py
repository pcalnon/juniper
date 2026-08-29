#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Attribute ``Tensor.__format__`` (and any target function) to its CALLERS across a cProfile corpus.

WHY
---
The logging redesign (notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md, F-1)
claims the level filter cannot prevent message cost because f-strings are evaluated at the call
site. The call-site-migration analysis (same date) states as guardrail G-1 that the honest
instrument is caller attribution from the profile corpus, NOT a name-based grep.

This is that instrument. cProfile records caller -> callee edges in ``Stats.stats``:

    stats[(file, line, func)] = (cc, nc, tt, ct, callers)
    callers[(caller_file, caller_line, caller_func)] = (cc, nc, tt, ct)

so the per-caller ``ct`` for a given callee is exactly "cumulative time this caller spent inside
that callee". Summing those over the corpus ranks the real cost centres.

WHAT IT DOES NOT DO
-------------------
It attributes to the enclosing FUNCTION, which is the granularity cProfile records -- not to the
individual log statement. A function containing three ``logger.trace(f"...")`` calls appears once.
Mapping a hot caller to a specific level still requires reading that function, and the script
prints the file:line of the caller so that read is one grep away.

Usage
-----
    2026-08-29_format_caller_attribution.py <PROF_DIR> [--target SUBSTR] [--top N]

``--target`` matches against "file:line(func)" of the callee; default catches ``__format__``.
Exit: 0 on success, 2 on usage/no-profiles.
"""

from __future__ import annotations

import argparse
import pstats
import sys
from collections import defaultdict
from pathlib import Path


def fmt_key(key) -> str:
    """cProfile keys are (file, line, func); builtins use ('~', 0, name)."""
    fn, ln, fun = key
    if fn == "~":
        return f"{fun}"
    return f"{Path(fn).name}:{ln}({fun})"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prof_dir")
    ap.add_argument("--target", default="__format__", help="substring matched against the callee key")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args(argv)

    prof_dir = Path(args.prof_dir)
    files = sorted(prof_dir.glob("*.prof"))
    if not files:
        print(f"no .prof files under {prof_dir}", file=sys.stderr)
        return 2

    # caller-key -> [cumulative seconds inside target, call count]
    attrib: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])
    target_total_ct = 0.0
    target_total_nc = 0
    matched_callees: set[str] = set()
    unattributed_ct = 0.0

    for f in files:
        st = pstats.Stats(str(f))
        for callee_key, entry in st.stats.items():
            callee = fmt_key(callee_key)
            if args.target not in callee:
                continue
            matched_callees.add(callee)
            _cc, nc, _tt, ct, callers = entry
            target_total_ct += ct
            target_total_nc += nc
            if not callers:
                # A callee with no recorded caller cannot be attributed; count it so the
                # totals stay honest instead of silently under-reporting.
                unattributed_ct += ct
                continue
            for caller_key, cvals in callers.items():
                # (cc, nc, tt, ct) per caller edge
                c_nc, c_ct = cvals[1], cvals[3]
                slot = attrib[fmt_key(caller_key)]
                slot[0] += c_ct
                slot[1] += c_nc

    print(f"# corpus: {len(files)} profiles under {prof_dir}")
    print(f"# target: callee key containing {args.target!r}")
    print(f"# matched callees: {sorted(matched_callees)}")
    print(f"# target cumulative time: {target_total_ct:8.2f} s over {target_total_nc:,} calls")
    if unattributed_ct:
        print(f"# WARNING unattributed (callee had no recorded caller): {unattributed_ct:.2f} s")
    print()

    rows = sorted(attrib.items(), key=lambda kv: kv[1][0], reverse=True)
    attributed = sum(v[0] for v in attrib.values())
    print(f"{'cum_s':>9}  {'share':>7}  {'calls':>12}  caller")
    for name, (ct, nc) in rows[: args.top]:
        share = (ct / target_total_ct * 100.0) if target_total_ct else 0.0
        print(f"{ct:9.2f}  {share:6.2f}%  {nc:12,}  {name}")
    shown = sum(v[0] for _, v in rows[: args.top])
    print()
    print(f"# attributed to callers: {attributed:.2f} s ({attributed / target_total_ct * 100:.1f}% of target)" if target_total_ct else "")
    print(f"# shown in top {args.top}: {shown:.2f} s ({shown / target_total_ct * 100:.1f}% of target)" if target_total_ct else "")
    print(f"# NOT shown (tail of {max(0, len(rows) - args.top)} callers): {attributed - shown:.2f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
