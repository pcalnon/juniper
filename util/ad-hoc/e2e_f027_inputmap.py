#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (client observer index)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Read Dash's CLIENT-DERIVED observer index (``state.graphs``) and diff the dead
store against the working one.

WHY THIS IS NOT A REPEAT of the already-refuted "invisible to the browser" check.
That check read the SERVED ``/dashboard/_dash-dependencies`` JSON -- the raw
dependency list the server publishes -- and found all five consumers present with
the exact input id. But dash-renderer does not dispatch off that list. At boot it
DERIVES an index from it (``state.graphs``: ``inputMap`` / ``outputMap`` /
``inputPatterns`` ...) and every prop change is routed through:

    getCallbacksByInput(graphs, paths, id, prop)
        const callbacks = (graphs.inputMap[id] || {})[prop];   <-- gate 1
        ...
        if (flatten(callback.getOutputs(paths)).length)         <-- gate 2
            matches.push(callback)

So a consumer can be in the served dependencies AND its Input component can be in
``paths`` and STILL never fire, if either

  gate 1: the store id is missing from ``graphs.inputMap`` (never indexed), or
  gate 2: NONE of that callback's OUTPUT components resolve in ``paths``
          -- dash-renderer drops the callback silently, with no console error.

Gate 2 has never been measured on this arc: the layout-presence audit checked
outputs against the SERVER's ``app.layout`` (Python), not against the client's
``paths``. The A/B injection result -- prop written, verified in redux, consumers
still silent -- is exactly what both gates look like from the outside.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_inputmap.py --tab 'Candidate Metrics'

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_w3drv", os.path.join(_HERE, "e2e_w3_params_driver.py"))
_w3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w3)

log = _w3.log
open_dashboard = _w3.open_dashboard

# Exact ids only -- substring matching on these has misled this arc four times, and
# 'candidate-metrics-panel-training-state-store' CONTAINS 'metrics-panel-training-state-store'.
DEAD_STORES = [
    "candidate-metrics-panel-training-state-store",
    "decision-boundary-boundary-data",
    "dataset-plotter-dataset-store",
]
LIVE_STORES = [
    "metrics-panel-training-state-store",
    "metrics-panel-metrics-store",
]

FIND_STORE = """
() => {
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')) return el[k];
      if (k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  const roots = ['#react-entry-point', '#_dash-app-content', '#_dash-global-error-container', 'body'];
  for (const sel of roots) {
    const el = document.querySelector(sel);
    if (!el) continue;
    let f = fiberOf(el);
    let hops = 0;
    while (f && hops < 4000) {
      const mp = f.memoizedProps;
      if (mp && mp.store && typeof mp.store.getState === 'function') {
        window.__dashStore = mp.store;
        return {found: true, via: sel, hops};
      }
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return {found: false};
}
"""

# Replicates dash-renderer's two gates against the LIVE client state.
PROBE = """
(ids) => {
  const st = window.__dashStore.getState();
  const graphs = st.graphs || {};
  const paths = st.paths || {};
  const strPaths = (paths && paths.strs) ? paths.strs : paths;   // dash>=2 nests string ids under .strs

  const out = {
    stateKeys: Object.keys(st),
    graphKeys: Object.keys(graphs),
    pathsShape: Object.keys(paths).slice(0, 12),
    pathsCount: Object.keys(strPaths).length,
    perStore: {}
  };

  for (const id of ids) {
    const entry = {inPaths: Object.prototype.hasOwnProperty.call(strPaths, id), consumers: []};
    const byProp = (graphs.inputMap || {})[id];
    entry.inInputMap = !!byProp;
    entry.inputMapProps = byProp ? Object.keys(byProp) : [];
    const cbs = byProp ? (byProp['data'] || []) : [];
    entry.consumerCount = cbs.length;
    for (const cb of cbs) {
      const outs = (cb.outputs || []).map(o => (typeof o === 'string' ? o : o.id));
      const missing = outs.filter(o => typeof o === 'string' && !Object.prototype.hasOwnProperty.call(strPaths, o));
      entry.consumers.push({
        outputs: outs,
        outputsMissingFromPaths: missing,
        // gate 2: dash-renderer drops the callback when NO output resolves
        droppedByGate2: outs.length > 0 && missing.length === outs.length
      });
    }
    out.perStore[id] = entry;
  }
  return out;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="F-CANOPY-027 client observer-index probe")
    ap.add_argument("--tab", default="Candidate Metrics")
    ap.add_argument("--settle", type=int, default=8000, help="ms to settle after the tab click")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            page.evaluate(
                """(l) => { const t=[...document.querySelectorAll('[role=tab]')]
                       .find(x=>x.textContent.trim()===l); if(t) t.click(); }""",
                args.tab,
            )
            page.wait_for_timeout(args.settle)

            found = page.evaluate(FIND_STORE)
            log(f"redux store discovery: {json.dumps(found)}")
            if not found.get("found"):
                log("  !! could not reach the redux store via the React fiber")
                return 1

            data = page.evaluate(PROBE, DEAD_STORES + LIVE_STORES)
        finally:
            browser.close()

    log(f"state keys : {data['stateKeys']}")
    log(f"graph keys : {data['graphKeys']}")
    log(f"paths shape: {data['pathsShape']}  (string-id entries: {data['pathsCount']})")
    log("")

    verdict_rows = []
    for label, ids in (("DEAD", DEAD_STORES), ("LIVE", LIVE_STORES)):
        for sid in ids:
            e = data["perStore"][sid]
            log(f"[{label}] {sid}")
            log(f"    in paths        : {e['inPaths']}")
            log(f"    in graphs.inputMap: {e['inInputMap']}   props={e['inputMapProps']}")
            log(f"    consumers on .data: {e['consumerCount']}")
            dropped = 0
            for c in e["consumers"]:
                mark = "  <-- DROPPED (no output in paths)" if c["droppedByGate2"] else ""
                if c["droppedByGate2"]:
                    dropped += 1
                log(f"      outputs={c['outputs']}{mark}")
                if c["outputsMissingFromPaths"] and not c["droppedByGate2"]:
                    log(f"        partially missing from paths: {c['outputsMissingFromPaths']}")
            verdict_rows.append((label, sid, e["inPaths"], e["inInputMap"], e["consumerCount"], dropped))
            log("")

    log("=" * 100)
    log(f"{'':<6} {'store':<48} {'paths':<7} {'inputMap':<9} {'consumers':<10} {'dropped'}")
    for label, sid, in_paths, in_map, n, dropped in verdict_rows:
        log(f"{label:<6} {sid:<48} {str(in_paths):<7} {str(in_map):<9} {n:<10} {dropped}")
    log("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
