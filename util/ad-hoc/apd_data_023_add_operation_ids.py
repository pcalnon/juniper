#!/usr/bin/env python3
"""Add an explicit ``operation_id`` to every juniper-data route decorator (APD-DATA-023).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- one-shot rewrite (the APD-DATA-023 close)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-DATA-023), the juniper-data fix PR named in its §5.1 row

For every ``@router.<verb>(<path>, ...)`` decorator under ``juniper_data/api/routes/`` that
carries no ``operation_id=`` keyword, inserts ``operation_id="<handler name>"`` immediately
after the path argument. The insertion point is the AST end position of that argument, so
the rewrite is exact, and it is idempotent -- a second run finds nothing to do. One line is
printed per edit so the census can be checked against the register row (21 routes:
datasets 16, generators 2, health 3).

    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/apd_data_023_add_operation_ids.py <juniper-data-worktree>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

HTTP_VERBS = frozenset({"get", "post", "put", "patch", "delete", "head", "options", "trace"})


def _edits(source: str) -> list[tuple[int, int, str]]:
    """Return ``(lineno, byte column, handler name)`` for every route decorator lacking an id."""
    edits: list[tuple[int, int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            is_route = isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr in HTTP_VERBS and isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "router"
            if not is_route or any(keyword.arg == "operation_id" for keyword in decorator.keywords):
                continue
            if not decorator.args:
                raise SystemExit(f"route decorator without a path argument at line {decorator.lineno}")
            path_arg = decorator.args[0]
            edits.append((path_arg.end_lineno or path_arg.lineno, path_arg.end_col_offset, node.name))
    return edits


def rewrite(path: Path) -> int:
    """Insert the missing ids bottom-up so earlier offsets stay valid; return the edit count."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    edits = sorted(_edits(source), reverse=True)
    for lineno, column, handler in edits:
        line = lines[lineno - 1]
        if not line.isascii():  # end_col_offset is a UTF-8 byte offset; the decorator lines are ASCII
            raise SystemExit(f"{path}:{lineno}: non-ASCII decorator line -- refusing a byte-offset splice")
        lines[lineno - 1] = f'{line[:column]}, operation_id="{handler}"{line[column:]}'
        print(f"{path.name}:{lineno}: operation_id={handler!r}")
    if edits:
        path.write_text("".join(lines), encoding="utf-8")
    return len(edits)


def main() -> int:
    worktree = Path(sys.argv[1]).resolve()
    routes_dir = worktree / "juniper_data" / "api" / "routes"
    total = 0
    for path in sorted(routes_dir.glob("*.py")):
        if path.name != "__init__.py":
            total += rewrite(path)
    print(f"{total} decorator(s) rewritten under {routes_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
