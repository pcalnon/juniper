#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Resolve what ``RESET_COMPONENT_STATE`` is actually resetting, and test
#          whether F-CANOPY-033 is the CAUSE of F-CANOPY-039.
#
#          F-039: the topology rebuild returns a correct 39 KB figure and the DOM
#          never shows it -- the graph sits at its layout default (sig=2, traces=0,
#          stats bar all "0"). F-033: ``RESET_COMPONENT_STATE`` fires ~13-15/s and
#          "returns components to their layout defaults". Those are the same
#          sentence from two directions, so the question is simply: does the reset
#          target the network-visualizer subtree?
#
#          F-033 recorded the itempath under ``children/12`` and attributed it to
#          the Cassandra panel; a live trace on 2026-08-28 shows ``children/11``.
#          Index-based attribution is exactly the kind that goes stale when a tab
#          list is rebuilt, so this resolves the path against the LIVE redux tree
#          and reports every ``id`` along it rather than trusting the index.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_f039_reset_target.py --seconds 45
#
# Exit codes: 0 probe completed (read the report), 2 the redux store was not reachable.

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

# Wrap dispatch, keep the RESET itempaths, then resolve each against the live tree.
INSTALL = """
() => {
  const el = document.getElementById('_dash-app-content') || document.getElementById('react-entry-point');
  let store = null;
  const hunt = (node) => {
    for (const k in node) {
      if (k.startsWith('__reactContainer') || k.startsWith('_reactRootContainer')) return node[k];
    }
    return null;
  };
  // dash-renderer exposes its store on the window in recent versions.
  store = (window.store && window.store.dispatch) ? window.store
        : (window.dash_stores && window.dash_stores[0]) || null;
  if (!store && el) { hunt(el); }
  if (!store || !store.dispatch) return false;
  window.__f039 = {resets: [], other: 0};
  const orig = store.dispatch.bind(store);
  store.dispatch = (action) => {
    try {
      if (action && action.type === 'RESET_COMPONENT_STATE' && action.payload && action.payload.itempath) {
        if (window.__f039.resets.length < 40) window.__f039.resets.push(action.payload.itempath);
      }
    } catch (e) { /* never let the probe break the app */ }
    return orig(action);
  };
  window.__f039.store = store;
  return true;
}
"""

RESOLVE = """
() => {
  const st = window.__f039 && window.__f039.store;
  if (!st) return {error: 'no store'};
  const state = st.getState();
  // Dash's OWN id -> itempath map is the ground truth. The first version of this
  // probe walked the component tree by hand, failed on every sample, and reported
  // a clean-looking zero -- resolve against ``paths.strs`` instead of guessing.
  const strs = (state.paths && state.paths.strs) || {};
  const graphPath = strs['network-visualizer-graph'];
  if (!graphPath) return {error: 'network-visualizer-graph absent from paths.strs'};

  const isPrefix = (a, b) => a.length <= b.length && a.every((v, i) => v === b[i]);
  const owners = Object.entries(strs);
  // Which declared id owns (or contains) this itempath? Deepest match wins.
  const nameFor = (path) => {
    let best = null;
    for (const [id, p] of owners) {
      if (isPrefix(p, path) && (!best || p.length > best.len)) best = {id: id, len: p.length};
    }
    return best ? best.id : null;
  };

  const rows = [];
  for (const path of (window.__f039.resets || [])) {
    rows.push({
      // The ONLY way a reset could blank the graph: it targets the graph or an ancestor.
      clears_graph: isPrefix(path, graphPath),
      owner: nameFor(path),
      diverges_at: path.findIndex((v, i) => v !== graphPath[i]),
      depth: path.length,
    });
  }
  const byOwner = {};
  for (const r of rows) { const k = r.owner || '(unresolved)'; byOwner[k] = (byOwner[k] || 0) + 1; }
  return {
    count: rows.length,
    graph_path_depth: graphPath.length,
    clears_graph: rows.filter((r) => r.clears_graph).length,
    by_owner: byOwner,
    samples: rows.slice(0, 8),
  };
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seconds", type=float, default=45.0)
    ap.add_argument("--tab", default="Network Topology")
    ap.add_argument("--out", default="/tmp/juniper-e2e/f039_reset_target.json")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            ensure_no_modal(page)
            open_tab(page, args.tab)
            page.wait_for_timeout(2500)

            if not page.evaluate(INSTALL):
                log("  !! redux store not reachable -- cannot trace dispatch")
                return 2
            log(f"  dispatch wrapped; collecting RESET itempaths for {args.seconds}s on {args.tab!r}")
            page.wait_for_timeout(int(args.seconds * 1000))

            report = page.evaluate(RESOLVE)
            if report.get("error"):
                log(f"  !! {report['error']} -- this probe measured NOTHING; do not read a zero from it")
                return 2
            log(f"  RESET_COMPONENT_STATE captured : {report.get('count')}")
            log(f"  graph itempath depth           : {report.get('graph_path_depth')}")
            log(f"  resets AT-OR-ABOVE the graph   : {report.get('clears_graph')}   <-- the only ones that could blank it")
            log("  reset targets by owning id:")
            for owner, n in sorted((report.get("by_owner") or {}).items(), key=lambda kv: -kv[1]):
                log(f"    {n:4d}x  {owner}")
            for s in report.get("samples") or []:
                log(f"    depth={s.get('depth')} diverges_at={s.get('diverges_at')} clears_graph={s.get('clears_graph')} owner={s.get('owner')}")
            log("")
            if report.get("clears_graph"):
                log("  => RESET_COMPONENT_STATE DOES target the graph or an ancestor: F-CANOPY-033 is a candidate CAUSE of F-CANOPY-039.")
            else:
                log("  => No reset targets the graph or an ancestor: F-CANOPY-033 is NOT F-CANOPY-039's cause; they stay separate findings.")

            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2, default=str)
            log(f"  -> {args.out}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
