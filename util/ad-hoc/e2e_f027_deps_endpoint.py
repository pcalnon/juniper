#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (_dash-dependencies)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Does the BROWSER know about the dead dependencies?

``app.callback_map`` is the SERVER's registry. The client builds its own
dependency graph from ``/dashboard/_dash-dependencies`` (serialized from
``app._callback_list``). A callback present in ``callback_map`` but missing from
that payload would be invisible to the browser -- the store would update and the
client would simply never know to invoke the consumer. That is the one wiring
layer F-CANOPY-027 has not inspected.

Also reports, for each dead consumer, whether the client-visible entry lists the
store among its inputs.

    cd juniper-canopy/src
    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        <juniper-ml>/util/ad-hoc/e2e_f027_deps_endpoint.py

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.getcwd())

DEAD = {
    "candidate-metrics-panel-status-badge",
    "candidate-metrics-panel-pool-info",
    "candidate-metrics-panel-loss-plot",
    "decision-boundary-plot",
    "dataset-plotter-scatter-plot",
    "dataset-plotter-sample-count",
}
LIVE = {
    "metrics-panel-progress-detail",
    "metrics-panel-phase-duration",
    "metrics-panel-current-lr",
}


def main() -> int:
    import frontend.dashboard_manager as dmmod

    dm = dmmod.DashboardManager({})
    app = dm.app

    cb_list = getattr(app, "_callback_list", None)
    if cb_list is None:
        print("ERROR: app._callback_list unavailable on this Dash build", file=sys.stderr)
        return 2
    print(f"callback_map entries : {len(app.callback_map)}")
    print(f"_callback_list entries: {len(cb_list)}   <-- what the BROWSER receives")
    print()

    def outputs_of(entry):
        o = entry.get("output")
        if isinstance(o, str):
            # "..a.b...c.d.." or "a.b"
            return [p for p in o.replace("..", " ").split() if p]
        return [str(x) for x in (o if isinstance(o, list) else [o])]

    index = {}
    for entry in cb_list:
        for o in outputs_of(entry):
            index.setdefault(o.split(".")[0], []).append(entry)

    def report(title, ids):
        print(f"=== {title} ===")
        for cid in sorted(ids):
            entries = index.get(cid, [])
            if not entries:
                print(f"  {cid:<46} IN _dash-dependencies = False   <-- browser cannot see it")
                continue
            e = entries[0]
            ins = [f"{i['id']}.{i['property']}" for i in e.get("inputs", [])]
            print(f"  {cid:<46} entries={len(entries)} inputs={len(ins)}")
            print(f"      {ins}")
        print()

    report("DEAD consumers", DEAD)
    report("LIVE consumers (control)", LIVE)

    # Anything in callback_map but NOT reachable in _callback_list
    listed = set()
    for entry in cb_list:
        for o in outputs_of(entry):
            listed.add(o)
    mapped = set()
    for key, spec in app.callback_map.items():
        o = spec.get("output")
        for x in (o if isinstance(o, list) else [o]):
            mapped.add(str(x))
    only_mapped = sorted(x for x in mapped if x not in listed)
    print("=== outputs present in callback_map but ABSENT from _callback_list ===")
    print(f"  {len(only_mapped)}")
    for x in only_mapped[:40]:
        print(f"    {x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
