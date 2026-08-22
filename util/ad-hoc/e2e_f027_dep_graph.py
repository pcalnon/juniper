#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (dep graph)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Exact producer/consumer picture for the stores F-CANOPY-027 implicates.

``e2e_f027_callback_audit.py`` established that the dead consumers ARE
registered. This one answers the follow-ups precisely, without substring
guessing: for each store, EVERY callback that writes it and EVERY callback that
reads it, with the real ``callback_map`` keys.

Run from the canopy source tree:

    cd juniper-canopy/src
    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        <juniper-ml>/util/ad-hoc/e2e_f027_dep_graph.py

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.getcwd())

STORES = [
    ("BROKEN ", "candidate-metrics-panel-training-state-store"),
    ("BROKEN ", "decision-boundary-boundary-data"),
    ("BROKEN ", "dataset-plotter-dataset-store"),
    ("WORKING", "metrics-panel-training-state-store"),
    ("WORKING", "metrics-panel-metrics-store"),
    ("WORKING", "pinned-params-store"),
]


def outputs_of(spec):
    o = spec.get("output")
    if isinstance(o, list):
        return [str(x) for x in o]
    return [str(o)]


def main() -> int:
    import frontend.dashboard_manager as dmmod

    dm = dmmod.DashboardManager({})
    cbmap = dm.app.callback_map
    print(f"total registered callbacks: {len(cbmap)}\n")

    for tag, store in STORES:
        prop = f"{store}.data"
        writers, readers = [], []
        for key, spec in cbmap.items():
            outs = outputs_of(spec)
            # the callback_map key encodes outputs; check both
            if any(prop == o for o in outs) or prop in str(key):
                writers.append((key, spec))
            if any(i.get("id") == store for i in spec.get("inputs", [])):
                readers.append((key, spec))

        print(f"=== [{tag}] {store} ===")
        print(f"  writers: {len(writers)}")
        for key, spec in writers:
            ins = [f"{i['id']}.{i['property']}" for i in spec.get("inputs", [])]
            print(f"    key={str(key)[:100]}")
            print(f"      triggered by: {ins}")
        print(f"  readers: {len(readers)}")
        for key, spec in readers:
            outs = outputs_of(spec)
            ins = [f"{i['id']}.{i['property']}" for i in spec.get("inputs", [])]
            print(f"    key={str(key)[:100]}")
            print(f"      outputs: {[o[:60] for o in outs][:6]}")
            print(f"      all inputs ({len(ins)}): {ins}")
        print()

    # Any component that is READ as an Input by some callback but never WRITTEN
    # by any -- such an Input can still hold its layout default, but if Dash
    # requires every Input to resolve, a never-written one is worth knowing about.
    all_written = set()
    for key, spec in cbmap.items():
        for o in outputs_of(spec):
            all_written.add(o.split(".")[0])
        for part in str(key).replace("..", " ").split():
            all_written.add(part.split(".")[0])
    all_read = {}
    for key, spec in cbmap.items():
        for i in spec.get("inputs", []):
            all_read.setdefault(i["id"], set()).add(str(key)[:60])
    never_written = sorted(cid for cid in all_read if cid not in all_written)
    print("=== Inputs that NO registered callback ever writes ===")
    print(f"  {len(never_written)} such component id(s)")
    for cid in never_written:
        print(f"    {cid:<46} read by {len(all_read[cid])} callback(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
