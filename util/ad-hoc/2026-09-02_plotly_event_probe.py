#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E Phase 2 -- plotly-event idiom probe for M-TOPOLOGY-10..15 (ad-hoc)
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

PINS THE IDIOM BEFORE ANY ROW IS SCORED, which is the same discipline
``e2e_seg17_topology_driver.py --step probe`` applies to the four topology
controls. M-TOPOLOGY-10..15 drive ``network-visualizer-graph`` itself -- click a
node, box-select, click empty space, zoom/pan, camera export, hover -- and the
driver has NO plotly-event idiom at all (only ``set_radio`` / ``set_checklist`` /
``set_dropdown`` / ``set_slider``). Guessing one and writing five scorers on top
of the guess is how this arc produced twenty refuted mechanisms.

WHY A REAL MOUSE CLICK AND NOT ``gd.emit('plotly_click', ...)``. A synthetic emit
fabricates the event payload, so it proves the CALLBACK works when handed a
payload the driver invented -- it cannot fail the way a user's click fails, and
it would have been blind to F-CANOPY-040's whole class ("unit coverage of a
correct function cannot see a caller that never supplies the value"). A real
click at the point's own pixel position makes Plotly do its own hit-testing and
build its own event, so a wrong idiom shows up as "nothing happened" instead of
a false PASS.

This probe answers, against the live app:

  1. which traces carry the NODES (as opposed to the ~944 edge traces), and what
     hit-testable points they expose;
  2. whether data -> viewport pixel conversion via ``xaxis.l2p`` + ``_fullLayout._size``
     lands on a node Plotly will actually hit-test;
  3. whether a real click on that pixel makes ``-selection-info`` appear (M-10);
  4. what the modebar exposes for box-select (M-11) and camera export (M-14);
  5. whether ``-view-state`` is written by a zoom/pan relayout (M-13).

It SCORES NOTHING. Its output is the input to the row scorers.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/2026-09-02_plotly_event_probe.py

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
vis = _drv.vis
text_of = _drv.text_of
NV = _drv.NV
RUN_DIR = _drv.RUN_DIR

OUT = os.path.join(RUN_DIR, "plotly_event_probe.json")

# --------------------------------------------------------------------------
# The idiom under test
# --------------------------------------------------------------------------

# Enumerate marker traces and their points, with the data coords Plotly will
# hit-test. Edge traces are mode:"lines"; node traces carry markers.
_JS_POINTS = """(id) => {
  const root = document.getElementById(id);
  if (!root) return {present:false};
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd || !gd.data) return {present:true, plotly:false};
  const marker_traces = [];
  gd.data.forEach((t, ci) => {
    const mode = t.mode || '';
    const is3d = String(t.type || '').indexOf('3d') >= 0;
    if (mode.indexOf('markers') < 0) return;
    const n = (t.x && t.x.length) || 0;
    const pts = [];
    for (let i = 0; i < Math.min(n, 6); i++) {
      pts.push({i: i, x: t.x[i], y: t.y ? t.y[i] : null,
                text: Array.isArray(t.text) ? t.text[i] : (t.text || null),
                hovertext: Array.isArray(t.hovertext) ? t.hovertext[i] : (t.hovertext || null)});
    }
    marker_traces.push({curve: ci, name: t.name || '', mode: mode, type: t.type || 'scatter',
                        n: n, is3d: is3d, sample: pts});
  });
  return {present:true, plotly:true, n_traces: gd.data.length, marker_traces: marker_traces};
}"""

# data coords -> VIEWPORT pixels. ``l2p`` maps a data value to a pixel offset
# inside the plot area; ``_fullLayout._size.l/.t`` is that area's offset inside
# the graph div; the bounding rect puts it in the viewport.
_JS_XY = """([id, curve, index]) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd || !gd._fullLayout) return {ok:false, why:'no _fullLayout'};
  const fl = gd._fullLayout;
  const xa = fl.xaxis, ya = fl.yaxis;
  if (!xa || !ya || !xa.l2p || !ya.l2p) return {ok:false, why:'no 2-D cartesian axes (3-D scene?)'};
  const t = gd.data[curve];
  if (!t) return {ok:false, why:'no such curve'};
  const dx = t.x[index], dy = t.y[index];
  if (dx === undefined || dy === undefined) return {ok:false, why:'no such point'};
  const r = gd.getBoundingClientRect();
  return {ok:true, dataX: dx, dataY: dy,
          x: r.left + fl._size.l + xa.l2p(dx),
          y: r.top  + fl._size.t + ya.l2p(dy),
          rect: {left: Math.round(r.left), top: Math.round(r.top),
                 w: Math.round(r.width), h: Math.round(r.height)},
          size: {l: fl._size.l, t: fl._size.t, w: fl._size.w, h: fl._size.h}};
}"""

_JS_MODEBAR = """(id) => {
  const root = document.getElementById(id);
  const bar = root ? root.querySelector('.modebar') : null;
  if (!bar) return {present:false};
  return {present:true, buttons: [...bar.querySelectorAll('a.modebar-btn')]
            .map(b => b.getAttribute('data-title') || b.getAttribute('data-attr') || '')};
}"""

_JS_DRAGMODE = """(id) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  return gd && gd._fullLayout ? (gd._fullLayout.dragmode || null) : null;
}"""


def selection_state(page) -> dict:
    """-selection-info's text and whether it is displayed (M-10 / -11 / -12's oracle)."""
    return {
        "text": text_of(page, f"{NV}-selection-info"),
        "display": (vis(page, f"{NV}-selection-info") or {}).get("display"),
    }


def store_state(page, store_id: str):
    """Read a dcc.Store's value out of the Dash layout registry."""
    return page.evaluate(
        """(sid) => { const el = document.getElementById(sid);
             if (!el) return {present:false};
             return {present:true, text:(el.textContent||'').slice(0,300)}; }""",
        store_id,
    )


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
            out["wake"] = wake
            if not wake.get("woke"):
                log("!! graph never painted -- probe cannot pin the idiom")
                out["error"] = "graph never painted"
                return 1

            gid = f"{NV}-graph"

            # 1. which traces carry nodes
            pts = page.evaluate(_JS_POINTS, gid)
            out["points"] = pts
            log(f"traces total={pts.get('n_traces')} marker_traces={len(pts.get('marker_traces') or [])}")
            for mt in (pts.get("marker_traces") or [])[:8]:
                log(f"  curve={mt['curve']:5d} name={mt['name']!r:28s} mode={mt['mode']!r:18s} n={mt['n']:4d} sample0={mt['sample'][0] if mt['sample'] else None}")

            marker_traces = [m for m in (pts.get("marker_traces") or []) if m["n"] > 0 and not m["is3d"]]
            if not marker_traces:
                log("!! no 2-D marker traces -- M-10..12 have no clickable node")
                out["error"] = "no marker traces"
                return 1

            # 2. data -> pixel for the first node of the largest marker trace
            target = max(marker_traces, key=lambda m: m["n"])
            xy = page.evaluate(_JS_XY, [gid, target["curve"], 0])
            out["xy"] = xy
            log(f"target curve={target['curve']} name={target['name']!r} n={target['n']}")
            log(f"  pixel mapping: {xy}")
            if not xy.get("ok"):
                out["error"] = f"pixel mapping failed: {xy.get('why')}"
                return 1

            # 3. modebar + dragmode, for M-11 (box select) and M-14 (camera)
            out["modebar"] = page.evaluate(_JS_MODEBAR, gid)
            out["dragmode"] = page.evaluate(_JS_DRAGMODE, gid)
            log(f"  modebar: {out['modebar']}")
            log(f"  dragmode: {out['dragmode']!r}")

            # 4. does a REAL click select the node? (M-10's contract)
            before = selection_state(page)
            log(f"  selection BEFORE: {before}")
            page.mouse.move(xy["x"], xy["y"])
            page.wait_for_timeout(400)
            page.mouse.click(xy["x"], xy["y"])
            page.wait_for_timeout(2500)
            after = selection_state(page)
            log(f"  selection AFTER : {after}")
            out["click"] = {"before": before, "after": after, "changed": before != after}

            # 5. view-state store, for M-13
            out["view_state_before"] = store_state(page, f"{NV}-view-state")

            log(f"  click changed selection-info: {out['click']['changed']}")
        finally:
            os.makedirs(RUN_DIR, exist_ok=True)
            with open(OUT, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=2, default=str)
            log(f"probe -> {OUT}")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
