#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Closure-aware census of un-offloaded blocking backend calls in async handlers
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-04_x7_offload_census.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-04
# Last Modified: 2026-09-04
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     X7 slice 1a's acceptance criterion is "zero un-offloaded blocking backend calls in async
#     route handlers", so the census IS the test and it must be right. A naive lexical scan is
#     not: measured on this codebase it reports 50 unguarded / 0 guarded, because canopy's
#     CORRECT idiom takes two shapes a lexical rule cannot see --
#
#       1. bare-attribute offload:  await asyncio.to_thread(backend.get_status)
#          The backend call is an ast.Attribute, never an ast.Call, so "find Call nodes" misses
#          all 13 of them and then reports the surrounding handler as unguarded.
#       2. named closure:           def _fetch(): return backend.get_status()
#                                   await asyncio.to_thread(_fetch)
#          The call sits in a nested FunctionDef that IS offloaded; a scope-blind walk counts it
#          as a direct call in the handler.
#
#     So a naive checker emits false positives on the exemplar code while missing the correct
#     offloads -- worse than no checker, because it licenses complacency. This pass is
#     closure-aware: it resolves nested functions and treats a function as offloaded when it is
#     handed to asyncio.to_thread / run_in_executor by name or as a bare attribute.
#
#####################################################################################################################################################################################################
# Notes:
#     - Read-only. Prints a per-site inventory so the count can be audited, not just trusted.
#     - The blocking surface is the backend/adapter/client boundary, which is what reaches
#       cascor over HTTP; see the design's section 5.2.
#
#####################################################################################################################################################################################################

"""Census un-offloaded blocking backend calls inside async route handlers."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")

# Receivers whose methods reach cascor over HTTP synchronously.
BLOCKING_RECEIVERS = {"backend", "_adapter", "adapter", "_client", "client"}

OFFLOADERS = {"to_thread", "run_in_executor"}


def _offloaded_names(tree: ast.AST) -> set[str]:
    """Names handed to an offloader, by reference or as a bare attribute.

    Covers ``to_thread(_fetch)`` (Name) and ``to_thread(backend.get_status)`` (Attribute).
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        attr = getattr(func, "attr", None)
        if attr not in OFFLOADERS:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Name):
                names.add(arg.id)
            elif isinstance(arg, ast.Attribute):
                # bare-attribute offload: the call itself never happens inline
                names.add(f"{getattr(arg.value, 'id', '?')}.{arg.attr}")
    return names


def _is_blocking_call(node: ast.AST) -> str | None:
    """Return ``receiver.method`` when the node is a blocking backend call."""
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    recv = func.value
    recv_name = getattr(recv, "id", None) or getattr(recv, "attr", None)
    if recv_name in BLOCKING_RECEIVERS:
        return f"{recv_name}.{func.attr}"
    return None


def census(path: Path) -> list[tuple[int, str, str]]:
    """Return (lineno, handler, call) for each un-offloaded blocking call."""
    tree = ast.parse(path.read_text())
    offloaded = _offloaded_names(tree)
    findings: list[tuple[int, str, str]] = []

    for fn in ast.walk(tree):
        if not isinstance(fn, ast.AsyncFunctionDef):
            continue
        # Nested defs that are handed to an offloader run OFF the loop; their bodies are exempt.
        exempt_bodies: list[ast.AST] = []
        for inner in ast.walk(fn):
            if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)) and inner is not fn and inner.name in offloaded:
                exempt_bodies.append(inner)

        exempt_nodes = {id(n) for body in exempt_bodies for n in ast.walk(body)}

        for node in ast.walk(fn):
            if id(node) in exempt_nodes:
                continue
            call = _is_blocking_call(node)
            if call is None:
                continue
            if call in offloaded:  # bare-attribute offload of this exact call
                continue
            # An awaited call is not a sync blocking call.
            parent_awaited = isinstance(getattr(node, "_x7_parent", None), ast.Await)
            if parent_awaited:
                continue
            findings.append((node.lineno, fn.name, call))
    return findings


def _annotate_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child._x7_parent = parent  # type: ignore[attr-defined]


def main() -> int:
    target = CANOPY_SRC / "main.py"
    tree = ast.parse(target.read_text())
    _annotate_parents(tree)

    # Re-run census against the annotated tree.
    offloaded = _offloaded_names(tree)
    findings: list[tuple[int, str, str]] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.AsyncFunctionDef):
            continue
        exempt_nodes: set[int] = set()
        for inner in ast.walk(fn):
            if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)) and inner is not fn and inner.name in offloaded:
                exempt_nodes |= {id(n) for n in ast.walk(inner)}
        for node in ast.walk(fn):
            if id(node) in exempt_nodes:
                continue
            call = _is_blocking_call(node)
            if call is None or call in offloaded:
                continue
            if isinstance(getattr(node, "_x7_parent", None), ast.Await):
                continue
            findings.append((node.lineno, fn.name, call))

    print(f"file            : {target}")
    print(f"offloaded names : {len(offloaded)} -> {sorted(offloaded)[:8]}{' ...' if len(offloaded) > 8 else ''}")
    print(f"UN-OFFLOADED blocking calls in async handlers: {len(findings)}")
    for lineno, handler, call in sorted(findings):
        print(f"  main.py:{lineno:<5} {handler:<38} {call}")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
