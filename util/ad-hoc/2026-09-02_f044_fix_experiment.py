#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E arc -- F-CANOPY-044 fix-selection experiment (ad-hoc)
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

CHOOSES BETWEEN TWO CANDIDATE FIXES FOR F-CANOPY-044 BY MEASUREMENT, because the
fact they hinge on is recorded in the ledger as UNKNOWN.

F-CANOPY-044: clicking a node selects nothing. The figure carries 1888 edge
traces (``mode="lines"``, vertices drawn TO node centres) plus 3 node traces, and
every click resolves to an edge, whose points have no ``text`` -- so
``handle_node_selection``'s ``if text:`` guard drops it. Measured 0 of 7.

The ledger deliberately does NOT assert why Plotly picks the edge: the observed
winners were curves 82, 166, 248, 1468, 1884 and 1886, which is not monotonic, so
"lowest trace index wins" does not survive its own data. Two candidate fixes
depend on opposite answers:

  CANDIDATE A -- emit the node traces FIRST and restore paint order with plotly's
      per-trace ``zorder`` (plotly 6.8.0 supports it). This only works if DATA
      ORDER is what breaks the tie. Tested here with ``Plotly.moveTraces``.

  CANDIDATE B -- put the node identity ON the edges: give each edge trace a
      ``customdata`` of ``[from_label, to_label, None]``, so a click landing on an
      edge VERTEX still identifies the node at that vertex, and the handler reads
      ``point.text or point.customdata``. Independent of the tie-break rule.
      Tested here by adding ``customdata`` at runtime and reading it back off the
      click event.

Neither candidate is assumed. The script reports what each one actually does and
leaves the choice to the evidence.

NOT TESTED HERE, and rejected on cost rather than measurement: making the edges
unhittable (``hoverinfo:'skip'``) works -- the earlier probe showed 3 of 3 clicks
resolving to node traces under it -- but it removes the ``"Weight: -0.420"``
tooltip, which is a shipped feature of the edge layer.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/2026-09-02_f044_fix_experiment.py

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
_probe = _load("_evprobe", "2026-09-02_plotly_event_probe.py")

log = _drv.log
open_dashboard = _drv.open_dashboard
open_tab = _drv.open_tab
wake_topology = _drv.wake_topology
NV = _drv.NV
RUN_DIR = _drv.RUN_DIR

_JS_POINTS = _probe._JS_POINTS
_JS_XY = _probe._JS_XY
selection_state = _probe.selection_state

OUT = os.path.join(RUN_DIR, "f044_fix_experiment.json")

_JS_LISTEN = """(id) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  window.__f44 = null;
  if (gd && gd.on) gd.on('plotly_click', (ev) => {
     try { window.__f44 = (ev.points||[]).map(p => ({curve:p.curveNumber, i:p.pointNumber,
                                                      text:p.text, customdata:p.customdata})); }
     catch (e) { window.__f44 = 'unreadable'; }
  });
  return !!(gd && gd.on); }"""


def click_and_read(page, gid, curve, index=0):
    """Click a point by axis coords and return what plotly_click reported."""
    r = page.evaluate(_JS_XY, [gid, curve, index])
    if not r.get("ok"):
        return {"ok": False, "why": r.get("why")}
    page.evaluate("() => { window.__f44 = null; }")
    before = selection_state(page)
    page.mouse.click(r["x"], r["y"])
    page.wait_for_timeout(2500)
    got = page.evaluate("() => window.__f44")
    hit = (got or [{}])[0] if isinstance(got, list) and got else {}
    return {"ok": True, "hit_curve": hit.get("curve"), "hit_text": hit.get("text"), "hit_customdata": hit.get("customdata"), "before": before, "after": selection_state(page)}


def measure_payload(canopy_src: str, n_hidden: int = 40) -> dict:
    """Offline: how much does F-CANOPY-044's ``customdata`` add to the figure?

    This matters more here than it would elsewhere. ``-raw-topology-store`` and the
    topology rebuild are the arc's starvation-prone path (F-CANOPY-037 / -039 /
    -043), and the rebuild's response on this fixture is already ~320 KB across 1891
    traces. Adding a per-point field to 1888 edge traces is not free, so the number
    goes in the PR rather than an estimate.

    Needs no browser: it builds the real traces through ``_create_edge_traces``.
    """
    import json as _json

    sys.path.insert(0, canopy_src)
    import networkx as nx

    from frontend.components.network_visualizer import NetworkVisualizer

    vis = NetworkVisualizer({"show_weights": True, "layout": "hierarchical"}, component_id="network-visualizer")
    g = nx.DiGraph()
    pos = {"input_0": (0.0, 0.0), "input_1": (0.0, 1.0)}
    for i in range(n_hidden):
        g.add_node(f"hidden_{i}")
        pos[f"hidden_{i}"] = (1.0 + i * 0.1, float(i))
    for o in range(2):
        pos[f"output_{o}"] = (10.0, float(o))
    # Mirror the real fan-in: every hidden unit takes both inputs and all earlier
    # hidden units, and both outputs take everything.
    for i in range(n_hidden):
        for src in ("input_0", "input_1", *[f"hidden_{j}" for j in range(i)]):
            g.add_edge(src, f"hidden_{i}", weight=0.1)
    for o in range(2):
        for src in ("input_0", "input_1", *[f"hidden_{j}" for j in range(n_hidden)]):
            g.add_edge(src, f"output_{o}", weight=0.1)

    traces = vis._create_edge_traces(g, pos, show_weights=False)
    edges = [t for t in traces if getattr(t, "mode", None) == "lines"]
    with_cd = len(_json.dumps([t.to_plotly_json() for t in edges], default=str))
    stripped = []
    for t in edges:
        d = t.to_plotly_json()
        d.pop("customdata", None)
        stripped.append(d)
    without_cd = len(_json.dumps(stripped, default=str))
    return {
        "n_edge_traces": len(edges),
        "bytes_with_customdata": with_cd,
        "bytes_without": without_cd,
        "delta_bytes": with_cd - without_cd,
        "pct": round(100.0 * (with_cd - without_cd) / max(1, without_cd), 2),
    }


def main() -> int:
    if "--measure-payload" in sys.argv:
        src = sys.argv[sys.argv.index("--measure-payload") + 1]
        r = measure_payload(src)
        log(f"payload: {r['n_edge_traces']} edge traces  {r['bytes_without']} -> {r['bytes_with_customdata']} bytes  (+{r['delta_bytes']}, +{r['pct']}%)")
        return 0

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
            gid = f"{NV}-graph"
            page.evaluate(_JS_LISTEN, gid)

            pts = page.evaluate(_JS_POINTS, gid)
            node_traces = [t for t in (pts.get("marker_traces") or []) if not t["is3d"] and t["n"] > 0]
            node_curves = [t["curve"] for t in node_traces]
            hidden = next((t for t in node_traces if t["name"] == "Hidden Units"), None)
            log(f"node traces: {[(t['name'], t['curve'], t['n']) for t in node_traces]}")
            out["node_curves"] = node_curves

            # ---- BASELINE -------------------------------------------------
            base = click_and_read(page, gid, hidden["curve"], 0)
            out["baseline"] = base
            log(f"BASELINE     click Hidden[0] -> curve {base.get('hit_curve')} text={base.get('hit_text')!r}")

            # ---- CANDIDATE B first: does clickData carry customdata? ------
            # Done before A because moveTraces renumbers everything.
            addcd = page.evaluate(
                """([id, nodeCurves]) => {
                     const root = document.getElementById(id);
                     const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                     if (!gd || !window.Plotly) return {ok:false};
                     // Tag every EDGE vertex with a synthetic label so a click on an
                     // edge still says which node sits at that vertex. Production
                     // would carry the real from/to node ids.
                     const edges = [];
                     const cds = [];
                     for (let i = 0; i < gd.data.length; i++) {
                       if (nodeCurves.indexOf(i) >= 0) continue;
                       edges.push(i);
                       cds.push([['edge' + i + ':from'], ['edge' + i + ':to'], [null]]);
                     }
                     // restyle takes one value per targeted trace
                     window.Plotly.restyle(gd, {customdata: cds.map(c => c.map(x => x[0]))}, edges);
                     return {ok:true, n_edges: edges.length}; }""",
                [gid, node_curves],
            )
            page.wait_for_timeout(2000)
            log(f"CANDIDATE B  customdata added to {addcd.get('n_edges')} edge traces")
            b = click_and_read(page, gid, hidden["curve"], 0)
            out["candidate_b"] = {"restyle": addcd, "click": b}
            log(f"CANDIDATE B  click Hidden[0] -> curve {b.get('hit_curve')} text={b.get('hit_text')!r} customdata={b.get('hit_customdata')!r}")
            out["candidate_b_works"] = bool(b.get("hit_customdata"))

            # ---- CANDIDATE A: does DATA ORDER break the tie? --------------
            moved = page.evaluate(
                """([id, nodeCurves]) => {
                     const root = document.getElementById(id);
                     const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                     if (!gd || !window.Plotly) return {ok:false};
                     const sorted = nodeCurves.slice().sort((a,b) => a-b);
                     window.Plotly.moveTraces(gd, sorted, [0,1,2]);
                     return {ok:true, moved: sorted}; }""",
                [gid, node_curves],
            )
            page.wait_for_timeout(3000)
            after_pts = page.evaluate(_JS_POINTS, gid)
            new_nodes = [(t["name"], t["curve"], t["n"]) for t in (after_pts.get("marker_traces") or [])]
            log(f"CANDIDATE A  moveTraces -> node traces now at {new_nodes}")
            new_hidden = next((t for t in (after_pts.get("marker_traces") or []) if t["name"] == "Hidden Units"), None)
            a = click_and_read(page, gid, new_hidden["curve"], 0) if new_hidden else {"ok": False}
            out["candidate_a"] = {"move": moved, "node_traces_after": new_nodes, "click": a}
            out["candidate_a_works"] = bool(new_hidden and a.get("hit_curve") == new_hidden["curve"])
            log(f"CANDIDATE A  click Hidden[0] -> curve {a.get('hit_curve')} text={a.get('hit_text')!r} (wanted {new_hidden['curve'] if new_hidden else '?'})")

            log("")
            log(f"  CANDIDATE A (reorder, data-order tie-break) : {'WORKS' if out['candidate_a_works'] else 'DOES NOT WORK'}")
            log(f"  CANDIDATE B (customdata on edges)           : {'WORKS' if out['candidate_b_works'] else 'DOES NOT WORK'}")
        finally:
            os.makedirs(RUN_DIR, exist_ok=True)
            with open(OUT, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=2, default=str)
            log(f"experiment -> {OUT}")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
