#!/usr/bin/env python3
"""Append verdict rows to a Phase-1 run's ``statuses.tsv``.

Project:     Juniper
Sub-Project: juniper-ml
Application: Canopy E2E validation arc -- Phase 1 evidence tooling
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Why this exists
---------------
Verdicts accumulate in the per-run TSV as each lane is driven. Appending them
by shell redirect is both awkward (embedded tabs, quoting) and unavailable in a
worktree-isolated session. This helper takes a JSON array of rows and appends
them, refusing to write a duplicate ``row_id`` so a re-run cannot silently
double-count a lane.

Usage
-----
    python util/ad-hoc/e2e_append_statuses.py <statuses.tsv> <rows.json> [--replace]

``rows.json`` is a list of objects with keys ``row_id``, ``status``, ``notes``
and (optionally) ``screenshots`` -- defaulting to an em dash when absent.
Tabs and newlines inside any field are collapsed to spaces so one row stays one
TSV line.

Without ``--replace`` an existing ``row_id`` is skipped (the default, so a
re-run cannot double-count a lane). With ``--replace`` an existing row is
rewritten IN PLACE, keeping its original position in the file -- for when
later evidence revises an earlier verdict.
"""

from __future__ import annotations

import json
import os
import sys

COLUMNS = ("row_id", "status", "notes", "screenshots")


def clean(value: str) -> str:
    """Collapse anything that would break the one-row-per-line contract."""
    return " ".join(str(value).replace("\t", " ").split())


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if a != "--replace"]
    replace = "--replace" in argv
    if len(args) != 2:
        print(__doc__)
        return 2
    tsv_path, rows_path = args[0], args[1]

    if not os.path.isfile(tsv_path):
        print(f"no such TSV: {tsv_path}", file=sys.stderr)
        return 2

    with open(rows_path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        print("rows.json must contain a JSON array", file=sys.stderr)
        return 2

    with open(tsv_path, "r", encoding="utf-8") as handle:
        existing_lines = handle.read().splitlines()
    existing_ids = {line.split("\t", 1)[0] for line in existing_lines if line.strip()}

    appended, skipped, replaced = [], [], []
    out_lines = [line for line in existing_lines if line.strip()]
    for row in rows:
        row_id = clean(row["row_id"])
        rendered = "\t".join(
            [
                row_id,
                clean(row.get("status", "")),
                clean(row.get("notes", "")),
                clean(row.get("screenshots", "—")) or "—",
            ]
        )
        if row_id in existing_ids:
            if not replace:
                skipped.append(row_id)
                continue
            for i, line in enumerate(out_lines):
                if line.split("\t", 1)[0] == row_id:
                    out_lines[i] = rendered  # rewrite in place, keeping file order
                    break
            replaced.append(row_id)
            continue
        out_lines.append(rendered)
        existing_ids.add(row_id)
        appended.append(row_id)

    with open(tsv_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out_lines) + "\n")

    print(f"appended {len(appended)}: {', '.join(appended) if appended else '(none)'}")
    if replaced:
        print(f"replaced {len(replaced)}: {', '.join(replaced)}")
    if skipped:
        print(f"skipped {len(skipped)} already-present: {', '.join(skipped)}")
    print(f"total rows now: {len(out_lines) - 1} (excluding header)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
