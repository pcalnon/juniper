#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E arc -- matrix status-cell updater (ad-hoc)
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

Sets the ``status`` cell of named matrix rows, and REFUSES to overwrite a cell
that does not currently hold the value the caller says it expects.

Hand-editing the matrix is how a row silently acquires a verdict nobody measured:
the table is 298 rows of pipe-delimited text, the status column is the last cell,
and a mis-aimed edit lands on a neighbouring row that looks identical at a glance.
The ``--from`` guard makes that a loud failure instead of a quiet one, which is the
same posture ``e2e_unfilled_rows.py`` takes toward unscored rows.

Usage:
    python3 util/ad-hoc/2026-09-02_matrix_set_verdicts.py \
        --matrix notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md \
        --from BLOCKED --set M-TOPOLOGY-09=PASS --set M-TOPOLOGY-12=FAIL

Exit: 0 all requested rows updated; 1 any row missing or not in the expected state.

See util/ad-hoc/README.md for the ad-hoc-script convention.
"""

import argparse
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--from", dest="from_status", required=True, help="the status every named row must currently hold")
    ap.add_argument("--set", dest="sets", action="append", required=True, metavar="ROW=VERDICT")
    args = ap.parse_args()

    want = {}
    for s in args.sets:
        rid, _, verdict = s.partition("=")
        if not rid or not verdict:
            print(f"bad --set {s!r}; expected ROW=VERDICT", file=sys.stderr)
            return 2
        want[rid.strip()] = verdict.strip()

    with open(args.matrix, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    seen, changed, refused = set(), [], []
    for i, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        cells = line.split("|")
        if len(cells) < 3:
            continue
        rid = cells[1].strip()
        if rid not in want:
            continue
        seen.add(rid)
        current = cells[-2].strip()
        if current != args.from_status:
            refused.append((rid, current))
            continue
        cells[-2] = f" {want[rid]} "
        lines[i] = "|".join(cells)
        changed.append((rid, want[rid]))

    missing = sorted(set(want) - seen)
    if missing or refused:
        for rid in missing:
            print(f"MISSING: {rid} is not a row in {args.matrix}", file=sys.stderr)
        for rid, cur in refused:
            print(f"REFUSED: {rid} holds {cur!r}, not {args.from_status!r} — not overwriting", file=sys.stderr)
        return 1

    with open(args.matrix, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    for rid, verdict in changed:
        print(f"  {rid}: {args.from_status} -> {verdict}")
    print(f"updated {len(changed)} row(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
