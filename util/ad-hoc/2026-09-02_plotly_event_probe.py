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

# The SECOND idiom: find the marker's own rendered SVG element and click ITS
# centre. Plotly draws scatter markers as <path> inside `g.points` within the
# trace's <g>, so this clicks exactly what a user would click and needs no axis
# arithmetic at all -- no `l2p`, no `_size` margins, no assumptions about which
# axis a trace is bound to. If the two idioms disagree, THIS one is right,
# because it is reading the geometry the browser actually laid out.
_JS_MARKER_RECT = """([id, curveName, index]) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd) return {ok:false, why:'no gd'};
  // Trace <g> order follows gd.data order within the scatter layer.
  const layer = gd.querySelector('.scatterlayer');
  if (!layer) return {ok:false, why:'no .scatterlayer'};
  const traces = [...layer.querySelectorAll('g.trace')];
  // Match by the rendered point count, since only the three node traces carry
  // markers (every edge trace is mode:"lines" and renders no g.points).
  const withPoints = traces
      .map((t, i) => ({i: i, g: t, pts: [...t.querySelectorAll('g.points > path')]}))
      .filter(t => t.pts.length > 0);
  if (!withPoints.length) return {ok:false, why:'no rendered marker paths', n_traces_dom: traces.length};
  const summary = withPoints.map(t => ({dom_index: t.i, n_points: t.pts.length}));
  // Pick the trace with the most points (Hidden Units, n=40).
  const target = withPoints.reduce((a, b) => (b.pts.length > a.pts.length ? b : a));
  const p = target.pts[Math.min(index, target.pts.length - 1)];
  if (!p) return {ok:false, why:'no such marker path', summary: summary};
  const r = p.getBoundingClientRect();
  return {ok:true, summary: summary, n_points: target.pts.length,
          x: r.left + r.width / 2, y: r.top + r.height / 2,
          rect: {left: Math.round(r.left), top: Math.round(r.top),
                 w: Math.round(r.width), h: Math.round(r.height)}};
}"""

_JS_VIEWPORT = """() => ({vw: window.innerWidth, vh: window.innerHeight,
                          sx: window.scrollX, sy: window.scrollY})"""

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

            # 2b. the DOM idiom -- click the marker's own rendered <path>.
            page.evaluate("(id) => document.getElementById(id).scrollIntoView({block:'center'})", gid)
            page.wait_for_timeout(600)
            out["viewport"] = page.evaluate(_JS_VIEWPORT)
            # RECOMPUTE the axis-math coords after the scroll. Both idioms return
            # VIEWPORT coordinates from a bounding rect, so a scroll invalidates any
            # value captured before it -- the first probe run clicked 279 px low for
            # exactly this reason, and the two idioms then "disagreed" for a reason
            # that had nothing to do with either.
            xy = page.evaluate(_JS_XY, [gid, target["curve"], 0])
            out["xy_after_scroll"] = xy
            log(f"  pixel mapping AFTER scroll: x={xy.get('x')} y={xy.get('y')}")
            mrect = page.evaluate(_JS_MARKER_RECT, [gid, target["name"], 0])
            out["marker_rect"] = mrect
            log(f"  viewport: {out['viewport']}")
            log(f"  marker rect (DOM idiom): {mrect}")

            # 3. modebar + dragmode, for M-11 (box select) and M-14 (camera).
            # The modebar only mounts its buttons once the graph is hovered.
            page.mouse.move(xy["x"], max(10, xy["y"] - 200))
            page.wait_for_timeout(800)
            out["modebar"] = page.evaluate(_JS_MODEBAR, gid)
            out["dragmode"] = page.evaluate(_JS_DRAGMODE, gid)
            log(f"  modebar (after hover): {out['modebar']}")
            log(f"  dragmode: {out['dragmode']!r}")

            # 3b. SPLIT THE QUESTION before scoring anything. "The click did
            # nothing" has two very different causes, and the fix differs:
            #   (a) Plotly never emitted `plotly_click` -> the IDIOM is wrong;
            #   (b) Plotly emitted it and Dash posted it, but the DOM never
            #       changed -> the idiom is right and this is a PRODUCT defect
            #       (or callback starvation), which is a finding, not a driver bug.
            # A counter on the graph's own emitter answers (a); the captured
            # `_dash-update-component` bodies answer (b).
            page.evaluate(
                """(id) => { const root = document.getElementById(id);
                     const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                     window.__jn_clicks = 0; window.__jn_last = null;
                     if (gd && gd.on) gd.on('plotly_click', (ev) => {
                        window.__jn_clicks++;
                        try { window.__jn_last = (ev.points||[]).map(p => ({curve:p.curveNumber, i:p.pointNumber,
                                                                            x:p.x, y:p.y, text:p.text})); }
                        catch (e) { window.__jn_last = 'unreadable'; }
                     });
                     return !!(gd && gd.on); }""",
                gid,
            )
            out["selection_info_present"] = page.evaluate(
                """(sid) => { const el = document.getElementById(sid);
                     return el ? {present:true, tag:el.tagName, display:getComputedStyle(el).display,
                                  html:(el.innerHTML||'').slice(0,200)} : {present:false}; }""",
                f"{NV}-selection-info",
            )
            log(f"  -selection-info element: {out['selection_info_present']}")
            _cap_before = len(capture)

            # 4. does a REAL click select the node? (M-10's contract)
            # Try the DOM-element idiom first -- it needs no axis arithmetic, so a
            # disagreement between the two is itself the answer about which to use.
            out["click"] = {}
            for label, pt in (("dom_marker", mrect if mrect.get("ok") else None), ("axis_l2p", xy)):
                if not pt:
                    continue
                # Re-read the oracle each time: a previous click may have selected a
                # node, and M-10's contract is that clicking the SAME node again
                # clears it -- so a stale "before" would invert the reading.
                before = selection_state(page)
                page.mouse.move(pt["x"], pt["y"])
                page.wait_for_timeout(400)
                page.mouse.click(pt["x"], pt["y"])
                page.wait_for_timeout(3000)
                after = selection_state(page)
                out["click"][label] = {"at": {"x": pt["x"], "y": pt["y"]}, "before": before, "after": after, "changed": before != after}
                log(f"  click via {label:11s} at ({pt['x']:.0f},{pt['y']:.0f}): {before} -> {after}  changed={before != after}")

            # 6. IS IT ROBUST? One click resolving to an edge could be a fluke of
            # where that marker sits. Click several nodes across all three node
            # traces and record which curve Plotly actually reports, so the finding
            # rests on a distribution rather than a single sample.
            sweep = []
            for tr in (pts.get("marker_traces") or []):
                if tr["is3d"] or tr["n"] <= 0:
                    continue
                for idx in {0, tr["n"] // 2, tr["n"] - 1}:
                    r = page.evaluate(_JS_XY, [gid, tr["curve"], idx])
                    if not r.get("ok"):
                        continue
                    page.evaluate("() => { window.__jn_last = null; }")
                    page.mouse.click(r["x"], r["y"])
                    page.wait_for_timeout(1200)
                    got = page.evaluate("() => window.__jn_last")
                    hit = (got or [{}])[0] if isinstance(got, list) and got else {}
                    sweep.append(
                        {
                            "node_trace": tr["name"], "node_curve": tr["curve"], "point": idx,
                            "hit_curve": hit.get("curve"), "hit_text": hit.get("text"),
                            "is_node_trace": hit.get("curve") == tr["curve"],
                        }
                    )
                    log(f"    click {tr['name']:14s}[{idx:3d}] (curve {tr['curve']}) -> hit curve {hit.get('curve')} text={hit.get('text')!r} node_trace={hit.get('curve') == tr['curve']}")
            out["hit_sweep"] = sweep
            n_node = sum(1 for s in sweep if s["is_node_trace"])
            out["hit_sweep_summary"] = {"clicks": len(sweep), "resolved_to_node_trace": n_node, "resolved_to_edge": len(sweep) - n_node}
            log(f"  HIT SWEEP: {n_node}/{len(sweep)} clicks resolved to a NODE trace; {len(sweep) - n_node} to an edge")

            # 7. FIX-HYPOTHESIS TEST for F-CANOPY-044, run rather than argued.
            # Hypothesis: the edge traces are stealing the hit because their
            # vertices sit exactly on the node centres, and excluding them from
            # hit-testing is enough to restore node selection. Setting
            # `hoverinfo:'skip'` on every edge trace at RUNTIME tests exactly that
            # and nothing else -- it does not tell us the production fix should be
            # this (edges carry the "Weight: -0.420" tooltip, which `skip` would
            # kill), only whether the mechanism is what the finding says.
            node_curves = [t["curve"] for t in (pts.get("marker_traces") or [])]
            restyled = page.evaluate(
                """([id, nodeCurves]) => {
                     const root = document.getElementById(id);
                     const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                     if (!gd || !window.Plotly) return {ok:false, why:'no Plotly'};
                     const edges = [];
                     for (let i = 0; i < gd.data.length; i++) if (nodeCurves.indexOf(i) < 0) edges.push(i);
                     window.Plotly.restyle(gd, {hoverinfo: 'skip'}, edges);
                     return {ok:true, n_edges: edges.length}; }""",
                [gid, node_curves],
            )
            page.wait_for_timeout(2500)
            log(f"  edges made unhittable: {restyled}")
            hyp = []
            for tr in (pts.get("marker_traces") or []):
                if tr["is3d"] or tr["n"] <= 0:
                    continue
                r = page.evaluate(_JS_XY, [gid, tr["curve"], 0])
                if not r.get("ok"):
                    continue
                page.evaluate("() => { window.__jn_last = null; }")
                before = selection_state(page)
                page.mouse.click(r["x"], r["y"])
                page.wait_for_timeout(2500)
                got = page.evaluate("() => window.__jn_last")
                hit = (got or [{}])[0] if isinstance(got, list) and got else {}
                after = selection_state(page)
                hyp.append({"node_trace": tr["name"], "node_curve": tr["curve"], "hit_curve": hit.get("curve"), "hit_text": hit.get("text"), "is_node_trace": hit.get("curve") == tr["curve"], "selection_changed": before != after, "after": after})
                log(f"    [edges skipped] click {tr['name']:14s} -> hit curve {hit.get('curve')} text={hit.get('text')!r} selection_changed={before != after} after={after}")
            out["fix_hypothesis_edges_unhittable"] = hyp
            out["fix_hypothesis_summary"] = {"clicks": len(hyp), "resolved_to_node_trace": sum(1 for h in hyp if h["is_node_trace"]), "selection_changed": sum(1 for h in hyp if h["selection_changed"])}
            log(f"  FIX HYPOTHESIS: {out['fix_hypothesis_summary']}")

            # 5. view-state store, for M-13
            out["view_state_before"] = store_state(page, f"{NV}-view-state")

            # The split: did Plotly emit, and did Dash receive?
            out["plotly_click_events"] = page.evaluate("() => ({n: window.__jn_clicks || 0, last: window.__jn_last})")
            posts = [c for c in capture[_cap_before:] if "_dash-update-component" in c.get("url", "")]
            out["dash_posts_during_click"] = [{"t_ms": p["t_ms"], "has_clickData": "clickData" in (p.get("body") or ""), "body_head": (p.get("body") or "")[:220]} for p in posts]
            log(f"  plotly_click emitted: {out['plotly_click_events']}")
            log(f"  dash posts during clicks: {len(posts)}, carrying clickData: {sum(1 for p in out['dash_posts_during_click'] if p['has_clickData'])}")

            worked = [k for k, v in out["click"].items() if v["changed"]]
            log(f"  idioms that moved the oracle: {worked or 'NONE'}")
        finally:
            os.makedirs(RUN_DIR, exist_ok=True)
            with open(OUT, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=2, default=str)
            log(f"probe -> {OUT}")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
