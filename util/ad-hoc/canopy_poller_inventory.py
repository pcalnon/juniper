#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 remediation design
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Inventory every interval-driven Dash callback in juniper-canopy's frontend and
classify it by trigger interval and tab gate.

WHY. F-CANOPY-027 is callback starvation under dash-renderer's hard-coded 12-slot
concurrency pool (``dash_renderer.dev.js:2846``). The remediation lever is the
number of callbacks pending CONCURRENTLY, so the design needs an exact census of
what polls, how often, and whether it is gated to a tab -- not an estimate.

The distinction that matters: a callback which returns ``dash.no_update`` because
its tab is inactive has ALREADY spent a server round-trip and a renderer slot to
decide that. Server-side gating does not reduce load; only client-side gating
(``dcc.Interval.disabled``) does.

Static AST analysis -- no running stack required. Resolves ``f"{self.component_id}-..."``
against each class's ``component_id`` default.

    python3 util/ad-hoc/canopy_poller_inventory.py
    python3 util/ad-hoc/canopy_poller_inventory.py --root /path/to/juniper-canopy/src/frontend
    python3 util/ad-hoc/canopy_poller_inventory.py --markdown

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import ast
import collections
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_ROOT = "/home/pcalnon/Development/python/Juniper/juniper-canopy/src/frontend"
DEP_KINDS = ("Output", "Input", "State")
TAB_COMPONENT = "visualization-tabs"


def _class_component_ids(tree: ast.AST) -> Dict[str, str]:
    """Map ClassName -> the default value of its ``component_id`` __init__ arg."""
    out: Dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, ast.FunctionDef) or item.name != "__init__":
                continue
            args = item.args
            names = [a.arg for a in args.args]
            defaults = args.defaults
            # defaults align to the TAIL of args.args
            offset = len(names) - len(defaults)
            for i, d in enumerate(defaults):
                if names[offset + i] == "component_id" and isinstance(d, ast.Constant) and isinstance(d.value, str):
                    out[node.name] = d.value
    return out


def _resolve_str(node: ast.AST, component_id: Optional[str]) -> Optional[str]:
    """Resolve a plain string or an f-string built from ``self.component_id``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: List[str] = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            elif isinstance(v, ast.FormattedValue):
                inner = v.value
                if (
                    isinstance(inner, ast.Attribute)
                    and inner.attr == "component_id"
                    and isinstance(inner.value, ast.Name)
                    and inner.value.id == "self"
                ):
                    if component_id is None:
                        return None
                    parts.append(component_id)
                else:
                    return None  # unresolvable (pattern-matching id, variable, ...)
            else:
                return None
        return "".join(parts)
    return None


def _deps_from_decorator(dec: ast.Call, component_id: Optional[str]) -> Dict[str, List[Tuple[str, str]]]:
    """Pull every Output/Input/State (id, property) out of one callback decorator."""
    found: Dict[str, List[Tuple[str, str]]] = {k: [] for k in DEP_KINDS}
    for sub in ast.walk(dec):
        if not isinstance(sub, ast.Call):
            continue
        fn = sub.func
        name = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else None)
        if name not in DEP_KINDS or len(sub.args) < 2:
            continue
        cid = _resolve_str(sub.args[0], component_id)
        prop = _resolve_str(sub.args[1], component_id)
        if cid is None or prop is None:
            continue
        found[name].append((cid, prop))
    return found


def _enclosing_class(tree: ast.AST, target: ast.AST) -> Optional[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for sub in ast.walk(node):
                if sub is target:
                    return node.name
    return None


def analyse_file(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    class_ids = _class_component_ids(tree)

    rows: List[Dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            fn = dec.func
            if not (isinstance(fn, ast.Attribute) and fn.attr == "callback"):
                continue
            cls = _enclosing_class(tree, node)
            deps = _deps_from_decorator(dec, class_ids.get(cls or "", None))

            intervals = [cid for cid, prop in deps["Input"] if prop == "n_intervals"]
            tab_input = any(cid == TAB_COMPONENT and prop == "active_tab" for cid, prop in deps["Input"])
            tab_state = any(cid == TAB_COMPONENT and prop == "active_tab" for cid, prop in deps["State"])
            rows.append(
                {
                    "file": os.path.basename(path),
                    "func": node.name,
                    "line": node.lineno,
                    "intervals": intervals,
                    "outputs": deps["Output"],
                    "tab_input": tab_input,
                    "tab_state": tab_state,
                }
            )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="canopy interval-driven callback inventory")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--markdown", action="store_true", help="emit a markdown table")
    args = ap.parse_args()

    rows: List[Dict[str, Any]] = []
    for dirpath, _dirs, files in os.walk(args.root):
        for f in sorted(files):
            if f.endswith(".py"):
                rows.extend(analyse_file(os.path.join(dirpath, f)))

    pollers = [r for r in rows if r["intervals"]]
    by_interval = collections.Counter(i for r in pollers for i in r["intervals"])

    print(f"callbacks found            : {len(rows)}")
    print(f"interval-driven (pollers)  : {len(pollers)}")
    print("renderer concurrency cap   : 12   (dash_renderer.dev.js:2846)")
    print()
    print("pollers per interval component:")
    for name, n in by_interval.most_common():
        print(f"  {n:>3}  {name}")
    print()

    gated = [r for r in pollers if r["tab_input"] or r["tab_state"]]
    ungated = [r for r in pollers if not (r["tab_input"] or r["tab_state"])]
    print(f"tab-gated pollers   : {len(gated)}   <- these can be silenced CLIENT-side (Interval.disabled)")
    print(f"un-gated pollers    : {len(ungated)}   <- always-on; must stay, or need another lever")
    print()

    if args.markdown:
        print("| callback | file:line | interval | tab-gated | first output |")
        print("|---|---|---|---|---|")
        for r in sorted(pollers, key=lambda r: (r["file"], r["line"])):
            iv = ", ".join(r["intervals"])
            gate = "Input" if r["tab_input"] else ("State" if r["tab_state"] else "—")
            out = f"`{r['outputs'][0][0]}.{r['outputs'][0][1]}`" if r["outputs"] else "—"
            print(f"| `{r['func']}` | `{r['file']}:{r['line']}` | `{iv}` | {gate} | {out} |")
        return 0

    print("=== TAB-GATED (candidates for client-side gating) ===")
    for r in sorted(gated, key=lambda r: (r["file"], r["line"])):
        gate = "Input" if r["tab_input"] else "State"
        out = f"{r['outputs'][0][0]}.{r['outputs'][0][1]}" if r["outputs"] else "-"
        print(f"  {r['file']}:{r['line']:<5} {r['func']:<38} {','.join(r['intervals']):<32} gate={gate:<6} -> {out}")
    print()
    print("=== UN-GATED (always polling, every tab) ===")
    for r in sorted(ungated, key=lambda r: (r["file"], r["line"])):
        out = f"{r['outputs'][0][0]}.{r['outputs'][0][1]}" if r["outputs"] else "-"
        print(f"  {r['file']}:{r['line']:<5} {r['func']:<38} {','.join(r['intervals']):<32} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
