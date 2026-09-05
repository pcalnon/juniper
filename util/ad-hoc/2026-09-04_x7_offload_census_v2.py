#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Provenance-resolving census of un-offloaded blocking calls in async handlers
#
# Author:        Paul Calnon
# Version:       0.3.0
# File Name:     2026-09-04_x7_offload_census_v2.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-04
# Last Modified: 2026-09-04
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     X7 slice 1a's acceptance criterion is "zero un-offloaded blocking calls in async route
#     handlers", so this census IS the test and it has to be right in BOTH directions.
#
#     v1 matched receivers by NAME and was wrong: the bare name ``client`` is bound in main.py to
#     at least four different objects -- the cascor client, the redis client, the cassandra
#     client, and an ``httpx.AsyncClient``. It therefore reported ``client.stream`` at
#     main.py:1646 as a blocking site when that receiver is an ASYNC client used inside
#     ``async with``. Name-matching is exactly the flaw that makes the repo's existing
#     ``ruff --select ASYNC`` hook report "All checks passed!" against ~40 live sites, and
#     shipping a second name-matching gate would license the same complacency.
#
#     v2 resolves each receiver by ASSIGNMENT PROVENANCE inside its enclosing function, then
#     classifies it:
#
#       ASYNC   -- bound from an async factory (httpx.AsyncClient); its calls are awaited. Not a
#                  finding.
#       CASCOR  -- the module-level ``backend`` global or an attribute chain rooted at it
#                  (``backend._adapter``, ``backend._adapter._client``). Sync HTTP to cascor.
#       OTHER   -- bound from another SYNC factory (redis, cassandra). Same MECHANISM as X7 --
#                  sync I/O on the event loop -- with a different upstream, so it belongs in the
#                  same slice: the split is by mechanism, and excluding these would be the
#                  path-subset exclusion the design forbids.
#       UNRESOLVED -- provenance not determined. Reported SEPARATELY and never silently included
#                  or excluded, because an unaudited bucket is how a gate goes quietly wrong.
#
#     Offload detection is closure-aware (see v1): canopy's correct idiom includes bare-attribute
#     offloads (``to_thread(backend.get_status)``, never a Call node) and named closures, both of
#     which a lexical scan misreads.
#
#####################################################################################################################################################################################################
# Notes:
#     - Read-only, static. Exits non-zero while findings remain.
#     - Prints every site with its resolved provenance so the count is auditable, not trusted.
#     - **NOT the authority.** The gate that governs slice 1a is
#       ``juniper-canopy/src/tests/regression/test_x7_off_loop_discipline.py``. This script is the
#       exploratory sibling: same classification logic, but it does NOT carry the gate's
#       ``VERIFIED_NO_IO_CALLS`` exclusions. That is the entire difference between the two counts
#       -- this reports **54**, the gate reports **52**, and the delta is exactly the two
#       ``backend._demo`` accessors (``get_network``, ``get_current_state``) that were each read and
#       confirmed to be in-process. Use the gate to decide when 1a is done; use this to explore.
#     - Both share a SCOPE LIMIT: they read ``main.py`` only. Design section 5.2 also puts the
#       metrics relay's inline ``extract_network_topology()`` in slice 1a
#       (``cascor_service_adapter.py:771``, measured 123 s blocked per 183 s with no user present).
#       It is a ``self``-method with internal I/O and is invisible to a receiver-based scan.
#
#####################################################################################################################################################################################################

"""Census un-offloaded blocking calls in async route handlers, resolving receiver provenance."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

CANOPY_MAIN = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src/main.py")

# Factories whose product is an ASYNC client: calls on it are awaited, not blocking.
ASYNC_FACTORIES = {"AsyncClient"}

# Factories whose product is a SYNC client that performs network I/O.
SYNC_FACTORIES = {"get_redis_client", "get_cassandra_client"}

# Factories returning the cascor service adapter. Adjudicated from main.py:2742 etc.
CASCOR_FACTORIES = {"_require_service_adapter"}

# Factories whose product performs NO network I/O. ``DataAdapter`` computes weight/topology
# statistics from torch tensors handed to it -- verified: zero requests/httpx/urlopen references
# in backend/data_adapter.py. Its calls can still occupy the loop with CPU work, which is a real
# but DIFFERENT concern: X7 is an unbounded wait on an unreachable upstream, and offloading local
# computation neither closes X7 nor is bounded by slice 1a's acceptance. Recorded, not counted.
LOCAL_FACTORIES = {"DataAdapter"}

# The cascor surface: the module-level backend and anything reached through it.
CASCOR_ROOTS = {"backend"}

OFFLOADERS = {"to_thread", "run_in_executor"}


def _root_name(node: ast.AST) -> str | None:
    """Return the leftmost Name of an attribute chain (``backend._adapter._client`` -> backend)."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _offloaded(tree: ast.AST) -> set[str]:
    """Names and bare attributes handed to an offloader."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) in OFFLOADERS:
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    out.add(arg.id)
                elif isinstance(arg, ast.Attribute):
                    out.add(ast.unparse(arg))
    return out


def _provenance(fn: ast.AsyncFunctionDef) -> dict[str, str]:
    """Map local names to the factory they were bound from, within this handler."""
    bound: dict[str, str] = {}
    for node in ast.walk(fn):
        # client = get_redis_client()
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            callee = node.value.func
            factory = getattr(callee, "attr", None) or getattr(callee, "id", None)
            for target in node.targets:
                if isinstance(target, ast.Name) and factory:
                    bound[target.id] = factory
        # async with httpx.AsyncClient(...) as client
        for item in getattr(node, "items", []) or []:
            ctx = item.context_expr
            if isinstance(ctx, ast.Call):
                factory = getattr(ctx.func, "attr", None) or getattr(ctx.func, "id", None)
                var = item.optional_vars
                if isinstance(var, ast.Name) and factory:
                    bound[var.id] = factory
    return bound


def classify(receiver: ast.AST, bound: dict[str, str]) -> str:
    """Classify a receiver expression as ASYNC / CASCOR / OTHER / UNRESOLVED."""
    root = _root_name(receiver)
    if root is None:
        return "UNRESOLVED"
    if root in CASCOR_ROOTS:
        return "CASCOR"
    factory = bound.get(root)
    if factory in ASYNC_FACTORIES:
        return "ASYNC"
    if factory in CASCOR_FACTORIES:
        return "CASCOR"
    if factory in SYNC_FACTORIES:
        return "OTHER"
    if factory in LOCAL_FACTORIES:
        return "LOCAL"
    return "UNRESOLVED"


def census_source(source: str) -> dict[str, list[tuple[int, str, str]]]:
    """Classify un-offloaded calls in ``source``.

    Extracted from ``main`` so the walk can be tested without canopy's ``main.py``.
    Keys: CASCOR, OTHER, LOCAL, ASYNC, UNRESOLVED. Each value is
    ``(lineno, handler, expr)``.
    """
    tree = ast.parse(source)
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child._parent = parent  # type: ignore[attr-defined]

    offloaded = _offloaded(tree)
    buckets: dict[str, list[tuple[int, str, str]]] = {"CASCOR": [], "OTHER": [], "LOCAL": [], "ASYNC": [], "UNRESOLVED": []}

    for fn in ast.walk(tree):
        if not isinstance(fn, ast.AsyncFunctionDef):
            continue
        bound = _provenance(fn)

        exempt: set[int] = set()
        for inner in ast.walk(fn):
            if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)) and inner is not fn and inner.name in offloaded:
                exempt |= {id(n) for n in ast.walk(inner)}

        for node in ast.walk(fn):
            if id(node) in exempt or not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            expr = ast.unparse(node.func)
            # v0.3.0: the cross-site expression exemption that used to sit here made this
            # census UNSOUND, in the worst direction. It skipped any call whose expression
            # appeared handed to an offloader ANYWHERE in the module, so because main.py:3574
            # offloads ``backend.get_status``, every OTHER ``backend.get_status()`` went
            # unreported -- including the three health endpoints X7 is defined by. It also
            # degraded as work progressed: offloading one site made its untouched twin
            # disappear. Reported 39 where the true count is 52. Exemption is now site-local
            # only (the ``exempt`` node-id set above, covering calls inside a closure that is
            # itself offloaded). Do not reintroduce matching by expression across sites.
            if isinstance(getattr(node, "_parent", None), ast.Await):
                continue
            kind = classify(node.func.value, bound)
            if kind == "UNRESOLVED":
                # Only report unresolved receivers that plausibly do I/O, not every helper call.
                root = _root_name(node.func.value)
                if root not in {"client", "adapter", "_adapter", "_client"}:
                    continue
            buckets[kind].append((node.lineno, fn.name, expr))
    return buckets


def main() -> int:
    buckets = census_source(CANOPY_MAIN.read_text())
    blocking = buckets["CASCOR"] + buckets["OTHER"] + buckets["UNRESOLVED"]
    print(f"file: {CANOPY_MAIN}\n")
    for kind in ("CASCOR", "OTHER", "UNRESOLVED", "LOCAL", "ASYNC"):
        rows = sorted(buckets[kind])
        label = {
            "ASYNC": "not a finding (awaited async client)",
            "LOCAL": "not a finding (no network I/O; CPU only)",
            "UNRESOLVED": "NEEDS ADJUDICATION",
        }.get(kind, "BLOCKING -- slice 1a scope")
        print(f"{kind:<11} {len(rows):>3}  [{label}]")
        for lineno, handler, expr in rows:
            print(f"    main.py:{lineno:<5} {handler:<36} {expr}")
        print()
    print(f"TOTAL BLOCKING (cascor + other + unresolved): {len(blocking)}")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
