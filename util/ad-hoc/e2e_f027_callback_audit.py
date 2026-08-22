#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Audit canopy's Dash callback registry IN-PROCESS, to answer the one mechanism
F-CANOPY-027 has never tested: **are the dead consumer callbacks registered at
all, and if so how does their registration differ from the working ones?**

Everything refuted so far was measured through the browser. This looks at
``app.callback_map`` directly, so it needs no stack and cannot be fooled by
render timing, response slicing, or DOM raciness.

Run from the canopy source tree:

    cd juniper-canopy/src
    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        <juniper-ml>/util/ad-hoc/e2e_f027_callback_audit.py

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import os
import sys

# sys.path[0] is THIS script's directory, not the cwd, so canopy's src/ modules
# (canopy_constants, frontend.*, backend.*) are not importable without this.
sys.path.insert(0, os.getcwd())

# The three panels F-CANOPY-027 covers, plus a KNOWN-WORKING control from the
# metrics panel. If the broken ones differ structurally from the control, that
# difference is the lead.
BROKEN_OUTPUTS = [
    "candidate-metrics-panel-status-badge.children",
    "candidate-metrics-panel-phase.children",
    "candidate-metrics-panel-pool-size.children",
    "candidate-metrics-panel-pool-info.children",
    "decision-boundary-plot.figure",
    "decision-boundary-status.children",
    "dataset-plotter-scatter-plot.figure",
    "dataset-plotter-sample-count.children",
]
WORKING_OUTPUTS = [
    "metrics-panel-progress-detail.children",
    "metrics-panel-phase-duration.children",
    "metrics-panel-current-lr.children",
    "sidebar-pinned-card.style",
]
STORES = [
    "candidate-metrics-panel-training-state-store.data",
    "decision-boundary-boundary-data.data",
    "dataset-plotter-dataset-store.data",
    "metrics-panel-metrics-store.data",
    "metrics-panel-training-state-store.data",
]


def describe(cbmap, key):
    """Return a compact description of the callback that OWNS this output."""
    for cb_key, spec in cbmap.items():
        outs = [str(o) for o in (spec.get("output") if isinstance(spec.get("output"), list) else [spec.get("output")])]
        # Dash stores the output key as "a.b" or "..a.b...c.d.." for multi-output
        if key in cb_key or any(key == o for o in outs):
            inputs = [f"{i['id']}.{i['property']}" for i in spec.get("inputs", [])]
            states = [f"{s['id']}.{s['property']}" for s in spec.get("state", [])]
            return {
                "registered": True,
                "callback_key": cb_key[:120],
                "n_inputs": len(inputs),
                "inputs": inputs,
                "n_state": len(states),
                "clientside": bool(spec.get("clientside_function")),
                "prevent_initial_call": spec.get("prevent_initial_call"),
            }
    return {"registered": False}


def main() -> int:
    try:
        import frontend.dashboard_manager as dmmod
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR importing dashboard_manager: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Run this from the canopy src/ directory with LD_LIBRARY_PATH cleared.", file=sys.stderr)
        return 2

    dm = dmmod.DashboardManager({})
    app = dm.app
    cbmap = app.callback_map
    print(f"total registered callbacks: {len(cbmap)}")
    print()

    def report(title, keys):
        print(f"=== {title} ===")
        for k in keys:
            d = describe(cbmap, k)
            if not d["registered"]:
                print(f"  {k:<52} REGISTERED=False   <-- not in callback_map")
            else:
                print(
                    f"  {k:<52} inputs={d['n_inputs']:<2} state={d['n_state']:<2} "
                    f"clientside={d['clientside']} prevent_initial={d['prevent_initial_call']}"
                )
                print(f"      inputs: {d['inputs']}")
        print()

    report("BROKEN consumers (F-CANOPY-027)", BROKEN_OUTPUTS)
    report("WORKING consumers (control)", WORKING_OUTPUTS)
    report("STORE writers", STORES)

    # Which components appear as an Input somewhere but are never an Output of
    # anything -- i.e. nothing ever writes them. A consumer whose Input is never
    # written can never fire.
    written = set()
    for cb_key, spec in cbmap.items():
        outs = spec.get("output")
        outs = outs if isinstance(outs, list) else [outs]
        for o in outs:
            written.add(str(o))
    for k in cbmap:
        for part in str(k).replace("..", " ").split():
            written.add(part)

    print("=== Are the store Inputs ever WRITTEN by any registered callback? ===")
    for s in STORES:
        hit = any(s in w for w in written)
        print(f"  {s:<52} written_by_some_callback={hit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
