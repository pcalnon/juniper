#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E arc -- can the driver actually READ a dcc.Store? (ad-hoc)
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

ANSWERS ONE QUESTION: does ``e2e_seg17_topology_driver._store()`` return a live
value, or does it return ``None`` for stores that demonstrably hold data?

WHY IT EXISTS. M-TOPOLOGY-18's scorer read ``-raw-topology-store`` as empty while
the Weight Matrix heatmap was rendering at ``plot_area=0.70`` -- which requires
that exact store to be populated. Both cannot be true. A reader that returns
``None`` for a populated store does not report "I could not read it"; it reports
"the store is empty", and the row then files a product defect against a working
gate. That is the same shape as the earlier version of the same row, which counted
BROWSER requests for an endpoint canopy fetches SERVER-SIDE and confidently read 0.

Two failure modes are distinguished here, because they have different fixes:
  * the store id does not exist in the layout at all (wrong id -> fix the caller);
  * the id exists but every access path returns nothing (the READER is broken ->
    fix ``_store``).

A store that renders no DOM cannot be read from the DOM, so the probe reports what
each access path yields rather than just the final answer.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/2026-09-03_store_read_probe.py

See util/ad-hoc/README.md for the ad-hoc-script convention.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_drv = _load("_seg17drv", "e2e_seg17_topology_driver.py")

log = _drv.log
open_dashboard = _drv.open_dashboard
open_tab = _drv.open_tab
wake_topology = _drv.wake_topology
set_radio = _drv.set_radio
settle_figure = _drv.settle_figure
wait_for = _drv.wait_for
_graph = _drv._graph
_store = _drv._store
NV = _drv.NV
RUN_DIR = _drv.RUN_DIR

OUT = os.path.join(RUN_DIR, "store_read_probe.json")

# Report every access path separately, so "unreadable" is never mistaken for "empty".
_JS_PATHS = """(id) => {
  const out = {id: id, el_present: false, dashprivate: '<absent>', redux: '<absent>',
               redux_has_layout: false, ctx_api: !!window.dash_component_api};
  const el = document.getElementById(id);
  out.el_present = !!el;
  try {
    if (el && el._dashprivate_layout) {
      const d = el._dashprivate_layout.props.data;
      out.dashprivate = d === undefined ? '<undefined>' : (d === null ? '<null>' : typeof d);
    }
  } catch (e) { out.dashprivate = '<err ' + e.message + '>'; }
  try {
    const st = window.store && window.store.getState ? window.store.getState() : null;
    out.redux_has_layout = !!(st && st.layout);
    if (st && st.layout) {
      const walk = (n) => { if (!n || typeof n !== 'object') return undefined;
        if (n.props && n.props.id === id) return n.props.data;
        const ch = n.props && n.props.children;
        const arr = Array.isArray(ch) ? ch : (ch ? [ch] : []);
        for (const c of arr) { const r = walk(c); if (r !== undefined) return r; }
        return undefined; };
      const v = walk(st.layout);
      out.redux = v === undefined ? '<not-found-in-layout>' : (v === null ? '<null>' : typeof v);
    }
  } catch (e) { out.redux = '<err ' + e.message + '>'; }
  return out;
}"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    out: dict = {}
    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            open_tab(page, "Network Topology")
            wake = wake_topology(page)
            log(f"wake_topology: {wake}")
            if not wake.get("woke"):
                out["error"] = "graph never painted"
                return 1

            # Put the app in the state where -raw-topology-store MUST hold data:
            # Weight Matrix rendering a real heatmap.
            set_radio(page, f"{NV}-display-mode", "weight_matrix")
            ok_heat, heat_s, _ = wait_for(
                lambda: any(t.get("type") == "heatmap" for t in (_graph(page).get("traces") or [])),
                budget_s=60, every_s=2.0, label="weight-matrix heatmap",
            )
            g = _graph(page)
            out["heatmap_rendered"] = ok_heat
            out["plot_area"] = g.get("plot_area")
            log(f"heatmap rendered={ok_heat} in {heat_s}s  plot_area={g.get('plot_area')} n_yaxes={g.get('n_yaxes')}")
            log("  (a rendered heatmap PROVES -raw-topology-store holds data; anything reading it as empty is broken)")

            ids = [
                f"{NV}-raw-topology-store",
                f"{NV}-topology-store",
                f"{NV}-view-state",
                f"{NV}-selected-nodes",
                "metrics-panel-metrics-store",
            ]
            rows = []
            for sid in ids:
                paths = page.evaluate(_JS_PATHS, sid)
                val = _store(page, sid)
                summary = {
                    "id": sid,
                    "el_present": paths["el_present"],
                    "dashprivate": paths["dashprivate"],
                    "redux": paths["redux"],
                    "redux_has_layout": paths["redux_has_layout"],
                    "_store_returned": type(val).__name__ if val is not None else "None",
                    "_store_truthy": bool(val),
                }
                rows.append(summary)
                log(f"  {sid:42s} el={paths['el_present']!s:5s} dashprivate={paths['dashprivate']:22s} redux={paths['redux']:24s} _store->{summary['_store_returned']} truthy={summary['_store_truthy']}")
            out["stores"] = rows
            out["redux_available"] = rows[0]["redux_has_layout"] if rows else None

            broken = [r for r in rows if r["el_present"] and not r["_store_truthy"]]
            log("")
            log(f"  VERDICT: _store() returned falsy for {len(broken)} of {len(rows)} present stores")
            if out.get("heatmap_rendered") and not rows[0]["_store_truthy"]:
                log("  !! -raw-topology-store reads EMPTY while its heatmap is RENDERED -- the READER is broken,")
                log("     not the product. Do not score M-TOPOLOGY-18 off this reader.")
        finally:
            os.makedirs(RUN_DIR, exist_ok=True)
            with open(OUT, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=2, default=str)
            log(f"probe -> {OUT}")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
