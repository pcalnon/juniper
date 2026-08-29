#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: F-CANOPY-039, the constructive half. Everything so far is negative --
#          the response is correct, the element is single/visible/initialised, no
#          reset touches it, and the DOM still never changes. This writes the
#          ``figure`` prop BY HAND through the component's own Dash-supplied
#          ``setProps`` and watches whether the graph updates.
#
#            DOM updates  -> the component accepts props fine; the defect is
#                            confined to Dash APPLYING the callback response.
#            DOM silent   -> the component itself ignores the prop, and the
#                            unapplied response is a symptom rather than the cause.
#
#          Adapted from ``e2e_f027_setprops_probe.py``, whose fiber walk is
#          hardcoded to ``{data: ...}`` for a ``dcc.Store``; a ``dcc.Graph`` takes
#          ``{figure: ...}``, and its plotly state lives on an inner
#          ``.js-plotly-plot``, not on the element carrying the id.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_f039_setprops_graph.py
#
# Exit codes: 0 probe completed (read the verdict), 2 setProps could not be reached.

import argparse
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


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")

log = _w3.log
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal
fig_info = _f027.fig_info

GRAPH = "network-visualizer-graph"

SETPROPS = """
(cfg) => {
  const {id, prop, value} = cfg;
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')
          || k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  const root = document.querySelector('#react-entry-point') || document.body;
  const stack = [fiberOf(root)];
  const seen = new Set();
  let hops = 0, found = false;
  while (stack.length && hops < 400000) {
    const n = stack.pop();
    hops++;
    if (!n || seen.has(n)) continue;
    seen.add(n);
    const mp = n.memoizedProps;
    if (mp && mp.id === id) {
      found = true;
      const payload = {}; payload[prop] = value;
      if (typeof mp.setProps === 'function') {
        try { mp.setProps(payload); return {ok: true, via: 'memoizedProps.setProps', hops}; }
        catch (e) { return {ok: false, err: String(e).slice(0, 160), hops}; }
      }
      if (n.stateNode && n.stateNode.props && typeof n.stateNode.props.setProps === 'function') {
        try { n.stateNode.props.setProps(payload); return {ok: true, via: 'stateNode.props.setProps', hops}; }
        catch (e) { return {ok: false, err: String(e).slice(0, 160), hops}; }
      }
    }
    if (n.child) stack.push(n.child);
    if (n.sibling) stack.push(n.sibling);
  }
  return {ok: false, err: found ? 'component found but no setProps' : 'component not found', hops};
}
"""

# Deliberately unmistakable: a single named trace nothing else would produce.
PROBE_FIGURE = {
    "data": [{"x": [1, 2, 3], "y": [3, 1, 2], "type": "scatter", "mode": "lines+markers", "name": "F039-PROBE"}],
    "layout": {"title": {"text": "F039 setProps probe"}},
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settle", type=float, default=6.0, help="seconds to wait after setProps")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            ensure_no_modal(page)
            open_tab(page, "Network Topology")
            page.wait_for_timeout(4000)

            before = fig_info(page, GRAPH)
            log(f"  BEFORE: plotly={before.get('plotly')} traces={len(before.get('traces') or [])} sig={before.get('sig')}")

            res = page.evaluate(SETPROPS, {"id": GRAPH, "prop": "figure", "value": PROBE_FIGURE})
            log(f"  setProps: {json.dumps(res)}")
            if not res.get("ok"):
                log("  !! could not reach setProps -- this probe measured NOTHING")
                return 2

            page.wait_for_timeout(int(args.settle * 1000))
            after = fig_info(page, GRAPH)
            names = [t.get("name") for t in (after.get("traces") or [])]
            log(f"  AFTER : plotly={after.get('plotly')} traces={len(after.get('traces') or [])} sig={after.get('sig')} names={names[:4]}")

            applied = "F039-PROBE" in names
            log("")
            if applied:
                log("  => The component APPLIED a hand-written figure.")
                log("     The graph accepts props fine, so the defect is confined to Dash applying the")
                log("     CALLBACK RESPONSE to this prop -- the F-CANOPY-006 half, not the component.")
            else:
                log("  => The component IGNORED a hand-written figure.")
                log("     The unapplied callback response is then a SYMPTOM, not the cause: this graph")
                log("     does not render from its own ``figure`` prop at all in this state.")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
