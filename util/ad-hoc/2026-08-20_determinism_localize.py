#!/usr/bin/env python3
"""Localise WHERE a seeded run first diverges: candidate math, or candidate selection?

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-20
Status:      ad-hoc -- one-off (juniper-cascor#532 seeded-run reproducibility)
Retire when: #532 is root-caused or accepted and the evidence note is merged; delete then.
Related:     2026-08-20_determinism_nrun.py (the RATE; this is the WHERE).

THE QUESTION THIS ANSWERS
-------------------------
The rate harness says how often two identically-seeded runs differ. It does not say what
differed, and the two live explanations demand opposite fixes:

  (a) CANDIDATE MATH -- the eight candidates themselves train to different correlations run to
      run. That is floating-point nondeterminism inside the worker, and a deterministic
      tie-break would do nothing about it.

  (b) SELECTION -- the candidates train to byte-identical correlations, but a different one is
      installed. ``_process_training_results`` sorts arrival-ordered results with a STABLE sort
      keyed only on ``(correlation is not None, |correlation|)``, so an exact tie is broken by
      whichever worker finished first. That is a scheduling race, and a secondary key on
      ``candidate_id`` fixes it outright.

Both produce the same downstream symptom -- a trajectory that separates and amplifies -- so the
end-to-end trace cannot distinguish them. The per-candidate correlations can, and they are
already logged at INFO by ``CandidateUnit.train_detailed``.

HOW
Candidate rounds are delimited by the parent's "Executing candidate training with N processes"
record; every ``Final Correlation`` record after it belongs to that round. Correlations are
compared as a SORTED multiset, because the log order is worker ARRIVAL order and therefore
timing-dependent by construction -- comparing them unsorted would report a difference on every
pair and answer nothing.

READING THE OUTPUT
  identical correlations, identical trace  -> the runs agree
  DIFFERENT correlations at round k        -> (a) candidate math; look at threading, not sorting
  identical correlations, different trace  -> (b) selection/tie-break, or a parent-side cause

PRECISION LIMIT -- READ THIS BEFORE QUOTING A VERDICT
-----------------------------------------------------
``CandidateUnit.train`` logs its correlation with ``:.6f`` (candidate_unit.py:670). "Identical
correlations" here therefore means identical TO SIX DECIMAL PLACES, and that is not the same as
identical. It matters concretely: in the cap-4 cell the top two round-0 correlations are
``0.091185`` and ``0.091184`` -- adjacent at the printed precision. If the underlying floats
differ somewhere below 1e-6 and that ordering flips, a DIFFERENT hidden unit is installed, every
later round sees a different candidate input, and the round-1 correlations then differ by tens of
percent rather than by float jitter. This tool would classify that pair as (a) CANDIDATE MATH,
because round 1 is where it first sees a difference -- even though the operative event was a
selection flip at round 0.

So (a) should be read as "the first difference OBSERVABLE AT LOGGED PRECISION is in candidate
correlations", not as "selection is exonerated". Distinguishing the two needs the installed
candidate's identity, and ``_add_best_candidate`` currently logs ``{best_candidate}`` -- the
default object repr, i.e. a memory address (cascade_correlation.py:4850) -- so the identity is
not recoverable from any existing log. Settling it requires instrumentation: log the installed
``candidate_index`` and the correlations at full precision.

What survives the precision limit either way: a deterministic SECONDARY sort key would not have
prevented any of this. A secondary key only engages on an EXACT tie; floats that differ at 1e-8
are already ordered by the primary key.

Usage: python util/ad-hoc/2026-08-20_determinism_localize.py <RUN_DIR> [<RUN_DIR> ...]
       A RUN_DIR is any directory containing logs/juniper_cascor.log (+ rotated .N segments).
Exit:  0 on a report; 2 if fewer than two runs carried a parseable candidate round.
"""

from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

RE_ROUND = re.compile(r"train_candidates: Executing candidate training with (\d+) processes")
RE_CORR = re.compile(r"CandidateUnit: train: Final Correlation: UUID: ([0-9a-f-]+), Final correlation value: ([0-9.eE+-]+)")
RE_ITER = re.compile(r"grow_network: Iteration (\d+) - Train Loss: ([0-9.eE+-]+), Train Accuracy: ([0-9.eE+-]+)")


def segments(run_dir: Path) -> "list[Path]":
    logs = run_dir / "logs"
    base = logs / "juniper_cascor.log"
    rotated = []
    if logs.is_dir():
        for p in logs.glob("juniper_cascor.log.*"):
            suffix = p.name.rsplit(".", 1)[-1]
            if suffix.isdigit():
                rotated.append((int(suffix), p))
    return [p for _n, p in sorted(rotated, reverse=True)] + ([base] if base.exists() else [])


def parse(run_dir: Path) -> dict:
    rounds: "list[list[str]]" = []
    arrival: "list[list[str]]" = []
    iters: "list[tuple[str, str, str]]" = []
    for seg in segments(run_dir):
        try:
            fh = seg.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if RE_ROUND.search(line):
                    rounds.append([])
                    arrival.append([])
                elif (m := RE_CORR.search(line)):
                    if rounds:
                        rounds[-1].append(m.group(2))
                        # Arrival order is tracked as the sequence of correlation VALUES, not the
                        # candidate UUIDs. ``CandidateUnit`` mints a fresh ``uuid.uuid4()`` per
                        # instantiation (candidate_unit.py:1154), so a UUID sequence differs
                        # between two runs unconditionally -- comparing those would "detect"
                        # reordering in 100% of pairs including bit-identical ones, which is a
                        # check that cannot fail and therefore measures nothing.
                        arrival[-1].append(m.group(2))
                elif (m := RE_ITER.search(line)):
                    iters.append((m.group(1), m.group(2), m.group(3)))
    return {
        "name": run_dir.name,
        # Sorted: log order is worker arrival order, which is timing-dependent by construction.
        "rounds": [sorted(r) for r in rounds],
        "arrival": arrival,
        "iters": iters,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    runs = [parse(Path(a)) for a in sys.argv[1:]]
    usable = [r for r in runs if r["rounds"]]
    for r in runs:
        if not r["rounds"]:
            print(f"  (no candidate rounds parsed in {r['name']}) -- skipped", file=sys.stderr)
    if len(usable) < 2:
        print("localize: need at least two runs with a parseable candidate round", file=sys.stderr)
        return 2

    print(f"{'run':<34} {'rounds':>6} {'cands/round':>12} {'iters':>6}")
    print("-" * 62)
    for r in usable:
        sizes = sorted({len(x) for x in r["rounds"]})
        print(f"{r['name'][:34]:<34} {len(r['rounds']):>6} {str(sizes):>12} {len(r['iters']):>6}")

    print("\n=== pairwise localisation ===")
    verdicts = {"agree": 0, "math": 0, "selection": 0}
    reorder_pairs = 0
    for a, b in itertools.combinations(usable, 2):
        n = min(len(a["rounds"]), len(b["rounds"]))
        corr_div = next((k for k in range(n) if a["rounds"][k] != b["rounds"][k]), None)
        trace_div = next((k for k, (x, y) in enumerate(zip(a["iters"], b["iters"])) if x != y), None)
        # Whether the pool genuinely completed in a different order. Only meaningful for a round
        # whose SORTED correlations agree: same multiset, different sequence == pure reordering,
        # which is precisely the condition under which a stable sort keyed on correlation alone
        # could install a different candidate. If reordering happens in rounds that nonetheless
        # produce identical downstream traces, the tie-break is being exercised and is NOT the
        # cause of the divergences seen elsewhere.
        reordered = next(
            (k for k in range(n)
             if a["rounds"][k] == b["rounds"][k] and a["arrival"][k] != b["arrival"][k]),
            None,
        )

        if corr_div is None and trace_div is None:
            verdicts["agree"] += 1
            label = "AGREE"
            detail = f"all {n} rounds identical"
        elif corr_div is not None:
            verdicts["math"] += 1
            label = "CANDIDATE MATH"
            sa, sb = a["rounds"][corr_div], b["rounds"][corr_div]
            first = next((i for i, (x, y) in enumerate(zip(sa, sb)) if x != y), None)
            detail = f"correlations first differ in round {corr_div}"
            if first is not None:
                detail += f" ({sa[first]} vs {sb[first]})"
            if trace_div is not None:
                detail += f"; trace diverges at iteration {a['iters'][trace_div][0]}"
        else:
            verdicts["selection"] += 1
            label = "SELECTION"
            detail = (f"correlations identical in all {n} rounds, but trace diverges at "
                      f"iteration {a['iters'][trace_div][0]} "
                      f"({a['iters'][trace_div][1]} vs {b['iters'][trace_div][1]})")
        if reordered is not None:
            reorder_pairs += 1
        arr = "" if reordered is None else f"  [pool REORDERED in round {reordered}, same correlations]"
        print(f"  {a['name'][:22]:<22} vs {b['name'][:22]:<22} {label:<15} {detail}{arr}")

    total = sum(verdicts.values())
    print(f"\n=== summary over {total} pairs ===")
    print(f"  agree                       : {verdicts['agree']}")
    print(f"  diverge in CANDIDATE MATH   : {verdicts['math']}")
    print(f"  diverge in SELECTION only   : {verdicts['selection']}")
    print(f"  pool reordered, same corrs  : {reorder_pairs}  "
          "(the stable-sort tie-break was exercised in these)")
    if verdicts["math"] and not verdicts["selection"]:
        print("\n  -> The first difference observable at logged precision (6 dp) is in candidate\n"
              "     CORRELATIONS, not in which candidate was installed given equal ones. A\n"
              "     deterministic secondary sort key would not have prevented any of these: a\n"
              "     secondary key engages only on an EXACT tie.\n"
              "     NOT established: whether a sub-1e-6 difference flipped a NEAR-tie at an\n"
              "     earlier round, installing a different unit. See PRECISION LIMIT in --help;\n"
              "     the installed candidate's identity is not currently logged.")
    elif verdicts["selection"] and not verdicts["math"]:
        print("\n  -> Candidates train identically to 6 dp; a different one is installed. Consistent\n"
              "     with the stable-sort tie-break on arrival order -- but confirm the correlations\n"
              "     are equal below print precision before calling a secondary key the fix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
