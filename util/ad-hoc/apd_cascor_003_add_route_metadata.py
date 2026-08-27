#!/usr/bin/env python3
"""Add ``operation_id`` (all routes) and ``response_model`` (envelope routes) to juniper-cascor.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- migration (the APD-CASCOR-003 + unfiled operation_id pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-CASCOR-003 and its §4.3 note), the juniper-cascor fix PR named in its §5.1 row

Two gaps over ONE set of decorators, done in one pass because splitting them rewrites all 47
twice (the register's §4.3 note says so):

* ``operation_id`` -- absent on all 47. FastAPI's default is ``<handler>_<path>_<method>``, which
  couples the generated SDK method name to the handler name, the router prefix AND the version
  prefix. Applied to **every** route; the census confirms no handler-name collisions, so the ids
  are unique.
* ``response_model`` -- absent on 46 of 47. Applied ONLY to the 44 routes whose body comes from
  ``success_response()``, which is wire-safe because that helper already returns
  ``ResponseEnvelope(...).model_dump()`` -- the second pass is idempotent by construction.

**The three health routes are deliberately excluded from the response_model half.** They do not
use the envelope. ``readiness_probe`` already declares ``ReadinessResponse``; ``health_check`` and
``liveness_probe`` return bare dicts on a documented cross-service contract (the API-02
``{status, version, service}`` base shared with juniper-data and juniper-canopy). Declaring a
model on them is NOT wire-neutral -- measured: a ``str | None`` field absent from the 200 body
comes back as an explicit ``"error": null`` once a model is declared, because
``response_model_exclude_none`` defaults to False. Giving those two their own models is a
cross-repo wire decision, not this defect.

The edit is idempotent and anchored on AST positions, applied bottom-up so earlier offsets stay
valid. It refuses rather than guesses if a decorator's source does not end in ``)``.

    python3 util/ad-hoc/apd_cascor_003_add_route_metadata.py <cascor-worktree>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}
OLD_IMPORT = "from api.models.common import success_response\n"
NEW_IMPORT = "from api.models.common import ResponseEnvelope, success_response\n"


def _uses_envelope(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True when the handler builds its body with ``success_response()``."""
    return any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "success_response" for node in ast.walk(fn))


def _decorators(tree: ast.Module) -> list[tuple[ast.Call, str, bool]]:
    """Every ``@router.<method>(...)`` decorator, with its handler name and envelope flag."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        envelope = _uses_envelope(node)
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            fn = dec.func
            if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "router" and fn.attr in HTTP_METHODS:
                found.append((dec, node.name, envelope))
    return found


def _offset(lines: list[str], lineno: int, col: int) -> int:
    """Absolute character offset of a (1-based lineno, 0-based col) position."""
    return sum(len(line) for line in lines[: lineno - 1]) + col


def patch_file(path: Path) -> tuple[int, int]:
    """Return (operation_ids added, response_models added)."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    decorators = _decorators(tree)
    if not decorators:
        return (0, 0)

    lines = source.splitlines(keepends=True)
    edits = []
    ids_added = models_added = 0

    for dec, handler, envelope in decorators:
        existing = {kw.arg for kw in dec.keywords if kw.arg}
        additions = []
        if "operation_id" not in existing:
            additions.append(f'operation_id="{handler}"')
            ids_added += 1
        if envelope and "response_model" not in existing:
            additions.append("response_model=ResponseEnvelope")
            models_added += 1
        if not additions:
            continue

        end = _offset(lines, dec.end_lineno, dec.end_col_offset)
        if source[end - 1] != ")":
            raise SystemExit(f"{path}:{dec.lineno}: decorator does not end in ')' -- refusing to guess")
        before = source[:end - 1].rstrip()
        sep = "" if before.endswith((",", "(")) else ", "
        edits.append((end - 1, sep + ", ".join(additions)))

    for pos, text in sorted(edits, reverse=True):
        source = source[:pos] + text + source[pos:]

    if models_added and OLD_IMPORT in source:
        source = source.replace(OLD_IMPORT, NEW_IMPORT, 1)

    path.write_text(source, encoding="utf-8")
    return (ids_added, models_added)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    root = Path(argv[0]).resolve() / "src" / "api" / "routes"
    if not root.is_dir():
        raise SystemExit(f"no routes directory at {root}")

    total_ids = total_models = 0
    for path in sorted(root.glob("*.py")):
        if path.name == "__init__.py":
            continue
        ids, models = patch_file(path)
        total_ids += ids
        total_models += models
        state = f"operation_id+{ids} response_model+{models}" if (ids or models) else "already patched"
        print(f"  {path.name:26s} {state}")
    print(f"\nTOTAL operation_id +{total_ids}, response_model +{total_models}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
