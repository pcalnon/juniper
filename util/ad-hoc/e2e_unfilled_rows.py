#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : E2E validation arc tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

List the E2E matrix rows whose ``status`` cell is still a placeholder --
straight from the ledger, grouped by the ``###`` section that contains them.

WHY THIS EXISTS
---------------
``e2e_row_coverage.py`` is an *estimator*: it reads verdict records and
guesses which rows they cover, so it mis-reads compressed enumerations and
over-credits rows whose only record is a non-terminal ``pending ...``. The
matrix is the ledger. Segment 15's first handoff draft planned from the
estimator's list published under the ledger's headline -- it would have sent
the segment to re-drive two already-``PASS`` rows while silently dropping
three unfilled ones.

This reads the matrix and nothing else, reusing ``e2e_matrix_fill``'s own
pipe-splitting (``\\|`` stays inside its cell) and placeholder set so the
answer cannot drift from what the filler will actually write.

Usage
-----
    python3 util/ad-hoc/e2e_unfilled_rows.py
    python3 util/ad-hoc/e2e_unfilled_rows.py --repo-root /path/to/juniper-ml
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_filler():
    """Import ``e2e_matrix_fill`` from this same ad-hoc directory."""
    spec = importlib.util.spec_from_file_location(
        "e2e_matrix_fill", HERE / "e2e_matrix_fill.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError("cannot load e2e_matrix_fill.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    fill = _load_filler()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--matrix", default=None)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    matrix = Path(args.matrix) if args.matrix else root / fill.DEFAULT_MATRIX
    lines = matrix.read_text(encoding="utf-8").splitlines()

    section = "(before any ### header)"
    section_line = 0
    status_idx: int | None = None
    header_cells: list[str] = []
    order: list[tuple[str, int]] = []
    unfilled: dict[tuple[str, int], list[str]] = {}
    total_rows = 0
    total_filled = 0

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("###"):
            section = stripped.lstrip("#").strip()
            section_line = lineno
            status_idx = None
            continue
        if not stripped.startswith("|"):
            status_idx = None
            continue
        if fill.is_separator(line):
            lowered = [c.strip().lower() for c in header_cells]
            status_idx = lowered.index("status") if "status" in lowered else None
            continue

        cells = fill.split_row(line)
        header_cells = cells
        if status_idx is None or status_idx >= len(cells):
            continue
        row_id = cells[1].strip() if len(cells) > 1 else ""
        if not row_id.startswith(fill.MATRIX_NAMESPACES):
            continue

        total_rows += 1
        key = (section, section_line)
        if key not in unfilled:
            unfilled[key] = []
            order.append(key)
        if cells[status_idx].strip() in fill.PLACEHOLDERS:
            unfilled[key].append(row_id)
        else:
            total_filled += 1

    print(f"matrix        : {matrix}")
    print(f"matrix rows   : {total_rows}")
    print(f"verdicted     : {total_filled}")
    print(f"UNFILLED      : {total_rows - total_filled}")
    print()
    print("| section (line) | unfilled | row ids |")
    print("|----------------|---------:|---------|")
    running = 0
    for key in order:
        ids = unfilled[key]
        if not ids:
            continue
        running += len(ids)
        name, ln = key
        print(f"| {name} (`:{ln}`) | {len(ids)} | {', '.join(ids)} |")
    print()
    print(f"sum of per-section unfilled counts: {running}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
