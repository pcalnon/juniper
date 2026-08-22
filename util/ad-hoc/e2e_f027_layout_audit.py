#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (layout)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Is every component F-CANOPY-027 implicates actually PRESENT IN THE LAYOUT?

This is the mechanism the finding has never tested. With
``suppress_callback_exceptions=True`` Dash will happily register and RUN a
callback whose Output component is absent from the layout: the server computes a
value and returns it, but the browser has no such component to apply it to, so
the prop never changes and **no dependent callback fires**. That is exactly the
observed signature -- store "fills" on the wire, consumers never run.

Walks ``app.layout`` (and every ``children``/list nesting) collecting real
component ids, then cross-checks against the callback registry. Exact id
matching only -- substring matching conflates
``candidate-metrics-panel-training-state-store`` with
``metrics-panel-training-state-store``.

    cd juniper-canopy/src
    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        <juniper-ml>/util/ad-hoc/e2e_f027_layout_audit.py

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.getcwd())

WATCH = [
    ("BROKEN ", "candidate-metrics-panel-training-state-store"),
    ("BROKEN ", "candidate-metrics-panel-update-interval"),
    ("BROKEN ", "candidate-metrics-panel-status-badge"),
    ("BROKEN ", "candidate-metrics-panel-pool-info"),
    ("BROKEN ", "decision-boundary-boundary-data"),
    ("BROKEN ", "decision-boundary-dataset-data"),
    ("BROKEN ", "decision-boundary-plot"),
    ("BROKEN ", "dataset-plotter-dataset-store"),
    ("BROKEN ", "dataset-plotter-scatter-plot"),
    ("WORKING", "metrics-panel-training-state-store"),
    ("WORKING", "metrics-panel-stats-update-interval"),
    ("WORKING", "metrics-panel-metrics-store"),
    ("WORKING", "metrics-panel-progress-detail"),
    ("WORKING", "fast-update-interval"),
    ("WORKING", "visualization-tabs"),
    ("WORKING", "theme-state"),
]


def collect_ids(node, out, depth=0):
    """Walk a Dash layout tree collecting every component id."""
    if node is None or depth > 200:
        return
    if isinstance(node, (list, tuple)):
        for n in node:
            collect_ids(n, out, depth + 1)
        return
    cid = getattr(node, "id", None)
    if isinstance(cid, str):
        out.add(cid)
    elif isinstance(cid, dict):
        out.add(str(cid))
    children = getattr(node, "children", None)
    if children is not None:
        collect_ids(children, out, depth + 1)
    # dbc.Tabs children live on .children; some wrappers stash panes elsewhere
    for attr in ("tab_children", "content"):
        sub = getattr(node, attr, None)
        if sub is not None:
            collect_ids(sub, out, depth + 1)


def main() -> int:
    import frontend.dashboard_manager as dmmod

    dm = dmmod.DashboardManager({})
    app = dm.app

    layout = app.layout
    if callable(layout):
        layout = layout()
    ids: set[str] = set()
    collect_ids(layout, ids)
    print(f"component ids reachable from app.layout: {len(ids)}\n")

    print("=== presence of the implicated components IN THE LAYOUT ===")
    missing = []
    for tag, cid in WATCH:
        present = cid in ids
        flag = "" if present else "   <-- ABSENT FROM LAYOUT"
        print(f"  [{tag}] {cid:<48} in_layout={present}{flag}")
        if not present:
            missing.append(cid)
    print()

    # Every callback Output whose component is absent from the layout.
    def outs_of(spec):
        o = spec.get("output")
        return [str(x) for x in (o if isinstance(o, list) else [o])]

    orphan_outputs = {}
    for key, spec in app.callback_map.items():
        for o in outs_of(spec):
            comp = o.split(".")[0].strip(". ")
            if comp and comp not in ids and not comp.startswith("{"):
                orphan_outputs.setdefault(comp, set()).add(str(key)[:70])

    print("=== callback OUTPUTS whose component is absent from the layout ===")
    print(f"  {len(orphan_outputs)} such component id(s)")
    for comp in sorted(orphan_outputs):
        print(f"    {comp:<50} written by {len(orphan_outputs[comp])} callback(s)")

    orphan_inputs = {}
    for key, spec in app.callback_map.items():
        for i in spec.get("inputs", []):
            cid = i.get("id")
            if isinstance(cid, str) and cid not in ids:
                orphan_inputs.setdefault(cid, set()).add(str(key)[:70])
    print()
    print("=== callback INPUTS whose component is absent from the layout ===")
    print(f"  {len(orphan_inputs)} such component id(s)")
    for comp in sorted(orphan_inputs):
        print(f"    {comp:<50} read by {len(orphan_inputs[comp])} callback(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
