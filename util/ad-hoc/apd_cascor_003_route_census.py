#!/usr/bin/env python3
"""AST census of juniper-cascor's route decorators, for the APD-CASCOR-003 pass.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation (grounding for the APD-CASCOR-003 / operation_id pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-CASCOR-003 and its §4.3 note)

``APD-CASCOR-003`` says 46 of 47 routes declare no ``response_model``; the register's §4.3 note
records that the SAME 47 decorators also declare no ``operation_id`` (the ``APD-DATA-023`` gap,
never filed as its own row). Both are one mechanical pass over one set of decorators.

Before rewriting anything, this reports what is actually there: per-file decorator counts, the
keyword sets already in use, which handlers return the ``{"status","data","meta"}`` envelope via
``success_response()``, and which do something else. The last group is the one that matters --
the register's measurement says declaring ``response_model=ResponseEnvelope`` is wire-safe
*because* every enveloped body already round-trips through that model, so any handler that does
NOT go through ``success_response()`` is where that guarantee stops.

Read-only. Prints a report; changes nothing.

    python3 util/ad-hoc/apd_cascor_003_route_census.py <cascor-worktree>
"""

from __future__ import annotations

import ast
import collections
import sys
from pathlib import Path

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}


def _returns_envelope(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Classify how a handler builds its response body."""
    calls = {node.func.id for node in ast.walk(fn) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    if "success_response" in calls:
        return "success_response"
    if "error_response" in calls:
        return "error_response"
    returns = [node for node in ast.walk(fn) if isinstance(node, ast.Return) and node.value is not None]
    if any(isinstance(r.value, ast.Dict) for r in returns):
        return "bare dict"
    if not returns:
        return "no return"
    return "other"


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    root = Path(argv[0]).resolve() / "src" / "api" / "routes"
    if not root.is_dir():
        raise SystemExit(f"no routes directory at {root}")

    rows = []
    for path in sorted(root.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                fn = dec.func
                if not (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "router" and fn.attr in HTTP_METHODS):
                    continue
                rows.append(
                    {
                        "file": path.name,
                        "handler": node.name,
                        "method": fn.attr,
                        "line": dec.lineno,
                        "kwargs": tuple(sorted(k.arg for k in dec.keywords if k.arg)),
                        "body": _returns_envelope(node),
                    }
                )

    per_file = collections.Counter(r["file"] for r in rows)
    print("=== decorators per file ===")
    for name, count in sorted(per_file.items()):
        print(f"  {name:26s} {count:2d}")
    print(f"  {'TOTAL':26s} {len(rows):2d}")

    print("\n=== keyword sets already declared ===")
    for kw, count in collections.Counter(r["kwargs"] for r in rows).most_common():
        print(f"  {count:3d}  {list(kw) or '(none)'}")

    print("\n=== how the handler builds its body ===")
    for body, count in collections.Counter(r["body"] for r in rows).most_common():
        print(f"  {count:3d}  {body}")

    outliers = [r for r in rows if r["body"] != "success_response"]
    print(f"\n=== {len(outliers)} handler(s) NOT going through success_response() ===")
    for r in outliers:
        print(f"  {r['file']}:{r['line']:4d}  {r['method']:6s} {r['handler']:38s} body={r['body']:16s} kwargs={list(r['kwargs'])}")

    already = [r for r in rows if "response_model" in r["kwargs"]]
    print(f"\n=== {len(already)} already declaring response_model ===")
    for r in already:
        print(f"  {r['file']}:{r['line']}  {r['handler']}")

    ids = [r for r in rows if "operation_id" in r["kwargs"]]
    print(f"\n=== {len(ids)} already declaring operation_id ===")

    dupes = [name for name, count in collections.Counter(r["handler"] for r in rows).items() if count > 1]
    print(f"\n=== handler-name collisions (would break operation_id uniqueness): {dupes or 'none'} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
