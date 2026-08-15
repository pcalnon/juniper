#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-1 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Bulk-fill the ``status`` column of the canopy E2E click-by-click test
#          matrix from a run's ``statuses.tsv``. Written during the 2026-08-14
#          Phase-1 segment-10 session; the bulk-fill had been deferred every
#          segment since segment 4 and was never scripted.
#
# Why a script and not sed
# ------------------------
# The matrix is NOT one uniform table. Different sections carry different column
# sets -- the C2.4 WS-badge table is ``| row id | # | Badge text | Trigger |
# Colour | mode | status |`` while the M-* tables are ``| row id | control |
# interaction | expected | backend | verify | auto | mode | FA | status |``. So
# the status column has to be located **by header name per table**, never by a
# fixed index. Guessing an index silently writes verdicts into the wrong column.
#
# Scope note: only the ``C2.*`` / ``M-*`` namespaces are table rows with a status
# column. The W-lane verdicts (W3-*, W5-*, W6-*, W11-*) are numbered PROSE steps
# in the matrix and have no status cell to fill; they are reported as
# ``no-matrix-row`` rather than treated as an error.
#
# Usage:
#   python3 util/ad-hoc/e2e_matrix_fill.py --verdicts reports/e2e/<RUN>/statuses.tsv
#   python3 util/ad-hoc/e2e_matrix_fill.py --verdicts <tsv> --write
#   python3 util/ad-hoc/e2e_matrix_fill.py --verdicts <tsv> --write --overwrite
#
# Default is a DRY RUN (writes nothing). Without --overwrite an already-filled
# status cell is left alone, so a re-run cannot clobber a hand-edited verdict.
#
# Exit codes: 0 ok, 1 nothing matched, 2 misuse / unreadable input.

import argparse
import csv
import re
import sys
from pathlib import Path

DEFAULT_MATRIX = "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
PLACEHOLDERS = {"", "—", "-", "--", "TBD", "n/a"}
MATRIX_NAMESPACES = ("C2.", "M-")


def split_row(line: str) -> list[str]:
    """Split a markdown table line into its cells (keeping the outer empties)."""
    return line.split("|")


def is_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    body = stripped.strip("|")
    return bool(body) and all(set(c.strip()) <= {"-", ":"} and c.strip() for c in body.split("|"))


def _balanced(text: str) -> str:
    """Trim back to the last point where parentheses are balanced.

    A blind character truncation cuts mid-parenthetical and silently drops the
    trailing finding id -- e.g. 'PASS(request path) / FAIL(status message --
    F-CANOPY-013)' loses the one token a matrix reader most needs. Cutting at the
    last balanced point keeps the cell honest about what it is not showing.
    """
    depth = 0
    last_balanced = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
            if depth == 0:
                last_balanced = i + 1
    if depth == 0:
        return text
    return text[:last_balanced].rstrip(" /-–—") if last_balanced else text


def shorten(status: str, max_len: int) -> str:
    """Keep the matrix cell readable: drop a trailing parenthetical/em-dash rider.

    Never emit a cell whose parentheses are unbalanced -- that is how a finding
    id gets silently amputated.
    """
    status = " ".join(status.split())
    if len(status) <= max_len:
        return status
    # prefer dropping a whole trailing rider over any character truncation
    for sep in (" — ", " -- ", " ("):
        head = status.split(sep, 1)[0].strip()
        if head and len(head) <= max_len and _balanced(head) == head:
            return head
    cut = _balanced(status[:max_len])
    if cut and len(cut) <= max_len:
        return cut + ("…" if len(cut) < len(status) else "")
    return status[: max_len - 1].rstrip() + "…"


def load_verdicts(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if not reader.fieldnames or "row_id" not in reader.fieldnames:
            raise ValueError(f"{path} has no row_id column")
        return {r["row_id"].strip(): (r.get("status") or "").strip() for r in reader if r.get("row_id")}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fill the E2E matrix status column from a run's statuses.tsv.")
    ap.add_argument("--verdicts", required=True, type=Path)
    ap.add_argument("--matrix", type=Path, default=None)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--max-len", type=int, default=44, help="cap on the rendered status cell")
    ap.add_argument("--write", action="store_true", help="apply changes (default is a dry run)")
    ap.add_argument("--overwrite", action="store_true", help="replace an already-filled status cell too")
    args = ap.parse_args()

    matrix = args.matrix or (args.repo_root / DEFAULT_MATRIX)
    try:
        verdicts = load_verdicts(args.verdicts)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    try:
        lines = matrix.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    status_idx: int | None = None
    header_cells: list[str] = []
    filled, skipped_filled, unmatched_rows = [], [], []
    seen_ids: set[str] = set()

    for lineno, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            status_idx = None
            continue
        if is_separator(line):
            # the previous non-separator table line was the header
            for cand in (header_cells,):
                lowered = [c.strip().lower() for c in cand]
                status_idx = lowered.index("status") if "status" in lowered else None
            continue

        cells = split_row(line.rstrip("\n"))
        header_cells = cells
        if status_idx is None or status_idx >= len(cells):
            continue

        row_id = cells[1].strip() if len(cells) > 1 else ""
        if not row_id.startswith(MATRIX_NAMESPACES):
            continue
        seen_ids.add(row_id)
        verdict = verdicts.get(row_id)
        if not verdict:
            unmatched_rows.append(row_id)
            continue

        current = cells[status_idx].strip()
        if current not in PLACEHOLDERS and not args.overwrite:
            skipped_filled.append((row_id, current))
            continue

        new_text = shorten(verdict, args.max_len)
        cells[status_idx] = f" {new_text} "
        lines[lineno] = "|".join(cells) + "\n"
        filled.append((row_id, new_text))

    print(f"matrix          : {matrix}")
    print(f"verdict rows    : {len(verdicts)}")
    print(f"matrix table ids: {len(seen_ids)}")
    print(f"filled          : {len(filled)}")
    print(f"already filled  : {len(skipped_filled)} (left alone; use --overwrite to replace)")
    print(f"no verdict yet  : {len(unmatched_rows)}")

    no_matrix_row = sorted(
        rid for rid in verdicts if rid.startswith(MATRIX_NAMESPACES) and rid not in seen_ids
    )
    if no_matrix_row:
        print(f"verdicts with NO matrix row ({len(no_matrix_row)}): {', '.join(no_matrix_row)}")
    w_lane = sorted(rid for rid in verdicts if not rid.startswith(MATRIX_NAMESPACES))
    if w_lane:
        print(f"W-lane / finding verdicts (prose steps, no status cell): {len(w_lane)}")

    if filled:
        print("\nfilled rows:")
        for rid, text in filled:
            print(f"  {rid:24s} -> {text}")

    if not filled:
        print("\nnothing to fill")
        return 1

    if args.write:
        matrix.write_text("".join(lines), encoding="utf-8")
        print(f"\nWROTE {matrix}")
    else:
        print("\nDRY RUN — nothing written (pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
