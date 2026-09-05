#!/usr/bin/env python3
"""
Find `.get(...)` chains over JSON written by ANOTHER process, where the value's type is assumed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1781, which fixed four of these in `util/experiments/read_run_metrics.py`

`x = blob.get("k") or {}` is a FALSY guard, not a TYPE guard. It fixes `None` and `{}` and does
nothing about a value that is truthy and not a dict -- a list, a string, a number -- which then
raises `AttributeError` on the next `.get`. ml#1781 fixed four such sites; the sweep that found
them stopped at the file it was in.

Not every `.get` chain is a risk. The distinguishing question is WHO WROTE THE JSON:

  * a GitHub API response has a schema the server enforces -- a missing key is possible, a
    wrongly-typed one is not;
  * a `manifest.json`, `experiment.yaml`, `registry.jsonl` or snapshot meta is written by a
    driver, an operator, or an older version of this code, and all three produce shapes the
    reader never anticipated. That is where the guard has to be a type guard.

So this reports `.get(...)` chains in files that read one of those artifacts, and says for each
whether an `isinstance` appears anywhere in the enclosing function. It ranks; it does not fix.

Usage:
    2026-09-06_untyped_json_read_census.py <dir> [<dir> ...]

Exit: 0 always -- this is a census, and a count is not a verdict.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Artifacts written by a driver, an operator, or an older version of this code.
UNTRUSTED = ("manifest.json", "experiment.yaml", "registry.jsonl", "meta.json", "index.jsonl", "baseline.json", "HOST.json", "stats.json", "aggregate.csv", "summary.md")


def reads_untrusted(src: str) -> list[str]:
    return sorted({name for name in UNTRUSTED if name in src})


def chains(tree: ast.Module) -> list[tuple[int, str]]:
    """`(lineno, rendering)` for every `X.get(...).get(...)` or `(X.get(...) or {}).get(...)`."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "get":
            continue
        inner = node.func.value
        # Unwrap `(... or {})`, which is the falsy guard this census is about.
        if isinstance(inner, ast.BoolOp) and isinstance(inner.op, ast.Or):
            inner = inner.values[0]
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) and inner.func.attr == "get":
            found.append((node.lineno, ast.unparse(node)[:110]))
    return found


def guarded_functions(tree: ast.Module) -> set[int]:
    """Line numbers spanned by any function whose body mentions `isinstance`."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(n, ast.Name) and n.id == "isinstance" for n in ast.walk(node)):
                lines |= set(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return lines


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2

    rows: list[tuple[int, str, str]] = []
    for root in args:
        for path in sorted(Path(root).rglob("*.py")):
            src = path.read_text(encoding="utf-8", errors="replace")
            artifacts = reads_untrusted(src)
            if not artifacts:
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            guarded = guarded_functions(tree)
            hits = chains(tree)
            if not hits:
                continue
            unguarded = [(ln, text) for ln, text in hits if ln not in guarded]
            rows.append((len(unguarded), str(path), f"{len(hits)} chain(s), {len(unguarded)} in functions with NO isinstance -- reads {', '.join(artifacts)}"))
            for ln, text in unguarded:
                rows.append((0, f"    {path}:{ln}", text))

    for _, where, what in sorted(rows, key=lambda r: (-r[0], r[1])):
        print(f"{where}  {what}" if what else where)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
