#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Re-score a NAMED set of E2E matrix rows after a defect is fixed.

WHY NOT ``e2e_matrix_fill.py --overwrite``
------------------------------------------
``--overwrite`` rewrites **every** cell any verdict source covers. The matrix
carries hand-authored cells from earlier segments that no TSV reproduces
(``INCONCLUSIVE``, ``DIVERGENCE D-1 CONFIRMED ...``), so a blanket overwrite
silently clobbers them. Phase 2 needs the opposite: touch exactly the rows a fix
re-opened, and nothing else.

Safety
------
Reuses ``e2e_matrix_fill``'s own pipe splitting (``\\|`` stays inside its cell)
and refuses to write any line whose **cell count** changes -- the failure mode
that once wrote a PASS into C2.2-04's FA column.

Usage
-----
    # show what would change
    python3 util/ad-hoc/e2e_matrix_rescore.py --row M-DATASET-01 --row M-DATASET-02 --status PASS

    # apply
    python3 util/ad-hoc/e2e_matrix_rescore.py --row M-DATASET-01 --status PASS --write
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_filler():
    spec = importlib.util.spec_from_file_location("e2e_matrix_fill", HERE / "e2e_matrix_fill.py")
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError("cannot load e2e_matrix_fill.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fill = _load_filler()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", action="append", required=True, help="row id (repeatable)")
    ap.add_argument("--status", required=True, help="terminal verdict to write (plan §9 vocabulary)")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--matrix", default=None)
    ap.add_argument("--write", action="store_true", help="apply (default is a dry run)")
    args = ap.parse_args()

    if args.status.strip().lower().startswith("pending"):
        print("ERROR: 'pending ...' is not a verdict; refusing.", file=sys.stderr)
        return 2

    root = Path(args.repo_root).resolve()
    matrix = Path(args.matrix) if args.matrix else root / fill.DEFAULT_MATRIX
    targets = {r.strip() for r in args.row}

    lines = matrix.read_text(encoding="utf-8").splitlines(keepends=True)
    status_idx: int | None = None
    header: list[str] = []
    changed, seen = [], set()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            status_idx = None
            continue
        if fill.is_separator(line):
            low = [c.strip().lower() for c in header]
            status_idx = low.index("status") if "status" in low else None
            continue
        cells = fill.split_row(line.rstrip("\n"))
        header = cells
        if status_idx is None or status_idx >= len(cells):
            continue
        rid = cells[1].strip()
        if rid not in targets:
            continue
        seen.add(rid)
        before = cells[status_idx].strip()
        newline = line.rstrip("\n")
        # width-preserving replacement of just the status cell
        pre = cells[:status_idx]
        post = cells[status_idx + 1 :]
        rebuilt = "|".join(pre + [f" {args.status} "] + post)
        if len(fill.split_row(rebuilt)) != len(fill.split_row(newline)):
            print(f"ERROR: cell-count would change for {rid}; refusing.", file=sys.stderr)
            return 3
        changed.append((rid, before, args.status))
        lines[i] = rebuilt + "\n"

    missing = targets - seen
    for rid, before, after in changed:
        print(f"  {rid:<16} {before!r}  ->  {after!r}")
    if missing:
        print(f"WARNING: row id(s) not found in matrix: {sorted(missing)}", file=sys.stderr)
    print(f"\n{len(changed)} row(s) would change" if not args.write else f"\n{len(changed)} row(s) changed")

    if args.write:
        matrix.write_text("".join(lines), encoding="utf-8")
        print(f"WROTE {matrix}")
    else:
        print("DRY RUN -- nothing written (pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
