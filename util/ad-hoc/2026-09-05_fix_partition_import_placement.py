#!/usr/bin/env python3
"""Repair the ``partitions`` import inserted inside a multi-line import statement.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data#369

The migration script placed the new import after the last line STARTING WITH
``from juniper_data``. In three files that line opens a parenthesised multi-line
import, so the new statement landed between ``from x import (`` and its first name --
a SyntaxError.

The fix uses the AST instead of line prefixes: parse the file with the bad line
removed, ask for the last top-level ``Import`` / ``ImportFrom`` node's ``end_lineno``,
and insert after it. A line prefix cannot see where a statement ENDS; the parser can.
"""

from __future__ import annotations

import ast
import pathlib
import sys

WT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--drop-full-family--20260905-1330--cc15640c")
TESTS = WT / "juniper_data/tests"
IMPORT_LINE = "from juniper_data.tests.partitions import whole\n"


def _repair(path: pathlib.Path) -> bool:
    lines = path.read_text().splitlines(keepends=True)
    if IMPORT_LINE not in lines:
        return False
    without = [ln for ln in lines if ln != IMPORT_LINE]
    source = "".join(without)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"{path.name}: still unparseable without the import ({exc})", file=sys.stderr)
        return False

    end = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = max(end, node.end_lineno or node.lineno)
    if end == 0:
        print(f"{path.name}: no top-level imports found", file=sys.stderr)
        return False

    without.insert(end, IMPORT_LINE)
    repaired = "".join(without)
    try:
        ast.parse(repaired)
    except SyntaxError as exc:
        print(f"{path.name}: repair still does not parse ({exc})", file=sys.stderr)
        return False
    path.write_text(repaired)
    return True


def main() -> int:
    fixed = 0
    for path in sorted(TESTS.rglob("test_*.py")):
        try:
            ast.parse(path.read_text())
        except SyntaxError:
            # A file that does not parse is exactly the population this script exists
            # to repair, so the failure is the SELECTOR, not an error. Falling through
            # to `_repair` below is the intended path; `_repair` re-parses and refuses
            # to write anything it cannot make parse.
            pass
        else:
            continue  # already parses -- nothing to do
        if _repair(path):
            print(f"{path.relative_to(WT)}: import re-placed")
            fixed += 1
    print(f"{fixed} file(s) repaired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
