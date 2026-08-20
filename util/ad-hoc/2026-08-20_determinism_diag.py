#!/usr/bin/env python3
"""Read the instrumented build's DIAG records: is it a near-tie flip, or arithmetic jitter?

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-20
Status:      ad-hoc -- one-off (juniper-cascor#532 root cause)
Retire when: #532 is root-caused or accepted and the evidence note is merged; delete then.
Related:     2026-08-20_determinism_localize.py (which this exists to disambiguate).

WHY THIS NEEDS AN INSTRUMENTED BUILD
The shipped logs cannot answer the question. Correlations are printed at ``:.6f``, and in this
cell the top two round-0 values are 0.091185 and 0.091184 -- adjacent at that precision. So
"identical correlations" from any shipped log is compatible with two very different stories:

  NEAR-TIE FLIP   the candidates trained bit-identically, but two of them are within 1e-6 and a
                  sub-precision difference reversed their order, installing a different unit.
                  Every later round then sees a different input and diverges by a lot.
  JITTER          the same candidate index genuinely trains to a different correlation.

They demand different fixes, and the installed unit's identity -- the one fact that separates them
-- is not in any shipped log: ``_add_best_candidate`` interpolates a ``CandidateUnit`` that has no
``__repr__``, so what lands in the log is a memory address.

The diagnostic build adds two INFO records: per candidate, ``candidate_index`` with the full-repr
correlation and its epoch count; per installed unit, the iteration and ``installed_index``. This
reads them and reports, per round, whether the index->correlation MAP agrees between runs.

READING THE OUTPUT
  map identical, installed index identical     -> that round is bit-reproducible
  map identical, installed index DIFFERENT     -> NEAR-TIE FLIP (fix: ordering / precision)
  map DIFFERENT for a shared index             -> JITTER (fix: whatever makes that arithmetic vary)

Usage: python util/ad-hoc/2026-08-20_determinism_diag.py <RUN_DIR> [<RUN_DIR> ...]
Exit:  0 on a report; 2 if fewer than two runs carried DIAG records (wrong build?).
"""

from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

RE_ROUND = re.compile(r"train_candidates: Executing candidate training with \d+ processes")
RE_CAND = re.compile(r"CandidateUnit: train: DIAG: candidate_index=(\d+) correlation_exact=([0-9.eE+-]+) epochs_completed=(\d+)")
RE_INSTALL = re.compile(r"_add_best_candidate: DIAG: iteration=(\d+) installed_index=(\S+) correlation_exact=(\S+)")


def segments(run_dir: Path) -> "list[Path]":
    logs = run_dir / "logs"
    base = logs / "juniper_cascor.log"
    rotated = []
    if logs.is_dir():
        for p in logs.glob("juniper_cascor.log.*"):
            if p.name.rsplit(".", 1)[-1].isdigit():
                rotated.append((int(p.name.rsplit(".", 1)[-1]), p))
    return [p for _n, p in sorted(rotated, reverse=True)] + ([base] if base.exists() else [])


def parse(run_dir: Path) -> dict:
    rounds: "list[dict[str, tuple[str, str]]]" = []
    installed: "list[tuple[str, str]]" = []
    for seg in segments(run_dir):
        try:
            fh = seg.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if RE_ROUND.search(line):
                    rounds.append({})
                elif (m := RE_CAND.search(line)):
                    if rounds:
                        rounds[-1][m.group(1)] = (m.group(2), m.group(3))
                elif (m := RE_INSTALL.search(line)):
                    installed.append((m.group(2), m.group(3)))
    return {"name": run_dir.name, "rounds": rounds, "installed": installed}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    runs = [parse(Path(a)) for a in sys.argv[1:]]
    usable = [r for r in runs if r["rounds"] and any(r["rounds"])]
    for r in runs:
        if r not in usable:
            print(f"  (no DIAG records in {r['name']} -- instrumented build not used?) -- skipped", file=sys.stderr)
    if len(usable) < 2:
        print("diag: need at least two runs carrying DIAG records", file=sys.stderr)
        return 2

    print(f"{'run':<14} {'rounds':>6} {'installed indices':<24} {'installed correlations'}")
    print("-" * 110)
    for r in usable:
        idx = ",".join(i for i, _c in r["installed"])
        corr = ",".join(c[:10] for _i, c in r["installed"])
        print(f"{r['name']:<14} {len(r['rounds']):>6} {idx:<24} {corr}")

    verdict = {"identical": 0, "flip": 0, "jitter": 0}
    print("\n=== pairwise, per round ===")
    for a, b in itertools.combinations(usable, 2):
        n = min(len(a["rounds"]), len(b["rounds"]))
        for k in range(n):
            ra, rb = a["rounds"][k], b["rounds"][k]
            shared = sorted(set(ra) & set(rb), key=int)
            # Compare the index -> correlation MAP, which is what removes arrival order from the
            # comparison entirely: a permuted pool has the same map.
            differing = [i for i in shared if ra[i][0] != rb[i][0]]
            ia = a["installed"][k][0] if k < len(a["installed"]) else None
            ib = b["installed"][k][0] if k < len(b["installed"]) else None
            if not differing and ia == ib:
                verdict["identical"] += 1
                continue
            if not differing and ia != ib:
                verdict["flip"] += 1
                print(f"  {a['name']} vs {b['name']}  round {k}: NEAR-TIE FLIP -- "
                      f"identical correlations for all {len(shared)} candidates, but installed "
                      f"index {ia} vs {ib}")
                break
            verdict["jitter"] += 1
            i0 = differing[0]
            print(f"  {a['name']} vs {b['name']}  round {k}: JITTER -- candidate_index={i0} "
                  f"trained to {ra[i0][0]} vs {rb[i0][0]} "
                  f"(epochs {ra[i0][1]} vs {rb[i0][1]}); {len(differing)}/{len(shared)} candidates differ; "
                  f"installed {ia} vs {ib}")
            break

    print(f"\n=== summary over {sum(verdict.values())} pair-rounds up to first difference ===")
    print(f"  rounds identical (map + installed) : {verdict['identical']}")
    print(f"  NEAR-TIE FLIP  (same corrs, diff install) : {verdict['flip']}")
    print(f"  JITTER         (same index, diff corr)    : {verdict['jitter']}")
    if verdict["jitter"] and not verdict["flip"]:
        print("\n  -> The SAME candidate trains to a DIFFERENT correlation. This is not an ordering\n"
              "     problem, so no sort-key or tie-break change addresses it. The arithmetic\n"
              "     inside candidate training is what varies.")
    elif verdict["flip"] and not verdict["jitter"]:
        print("\n  -> Candidates train bit-identically; a near-tie is resolved differently. The fix\n"
              "     is in ordering/precision at selection, not in the training arithmetic.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
