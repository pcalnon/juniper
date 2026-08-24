#!/usr/bin/env python3
"""Scratch probe: compute canopy's worst-case concurrent poller count from the BUILT app.

More accurate than the AST census in ``canopy_poller_inventory.py`` (which resolves 151 of
182 callbacks) because it reads ``app._callback_list`` directly. Used to pick the budget the
Stage 3 guard pins. See notes/JUNIPER_2026-08-23_JUNIPER-CANOPY_CALLBACK-STARVATION-REMEDIATION-DESIGN.md
"""

import collections
import sys

sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-canopy/src")

from frontend.dashboard_manager import _GATED_POLL_INTERVALS, DashboardManager  # noqa: E402


def walk(component):
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if hasattr(child, "children") or hasattr(child, "id"):
            yield from walk(child)


def deps(entry, key):
    out = set()
    for dep in entry.get(key) or []:
        if isinstance(dep, dict) and isinstance(dep.get("id"), str):
            out.add(f"{dep['id']}.{dep['property']}")
    return out


def main() -> int:
    dash_mgr = DashboardManager({})
    comps = {getattr(c, "id", None): c for c in walk(dash_mgr.app.layout) if isinstance(getattr(c, "id", None), str)}
    gate = dict(_GATED_POLL_INTERVALS)

    rows = []
    for entry in dash_mgr.app._callback_list:
        if entry.get("clientside_function"):
            continue  # clientside costs no renderer slot
        for dep in deps(entry, "inputs"):
            if not dep.endswith(".n_intervals"):
                continue
            interval_id = dep.split(".")[0]
            comp = comps.get(interval_id)
            one_shot = getattr(comp, "max_intervals", None) not in (None, -1)
            rows.append((interval_id, gate.get(interval_id, "UNGATED"), one_shot, str(entry["output"])[:70]))

    perpetual = [r for r in rows if not r[2]]
    print(f"server-side interval-driven callbacks : {len(rows)}")
    print(f"perpetual (not one-shot)              : {len(perpetual)}")

    by_gate = collections.Counter(r[1] for r in perpetual)
    print("\nperpetual pollers by gate:")
    for key, n in by_gate.most_common():
        print(f"  {n:>3}  {key}")

    global_n = sum(n for k, n in by_gate.items() if k in (None, "UNGATED"))
    per_tab = {k: n for k, n in by_gate.items() if k not in (None, "UNGATED")}
    worst_tab, worst_n = max(per_tab.items(), key=lambda kv: kv[1], default=("-", 0))
    print(f"\nglobal (never gated)      : {global_n}")
    print(f"worst single tab ({worst_tab}) adds : {worst_n}")
    print(f"WORST-CASE CONCURRENT     : {global_n + worst_n}   (renderer cap 12)")

    print("\nungated perpetual pollers (the Stage 2 target):")
    for interval_id, gate_tab, _one_shot, out in perpetual:
        if gate_tab in (None, "UNGATED"):
            print(f"  {interval_id:<42} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
