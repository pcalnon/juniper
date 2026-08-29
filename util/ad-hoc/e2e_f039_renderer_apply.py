#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: F-CANOPY-039's last cheap question. Six candidates are ruled out and the
#          component provably renders a hand-written ``figure``, so the defect is
#          in dash-renderer writing the callback RESPONSE into that prop. This asks
#          the one thing that splits that remaining step in half:
#
#            when a 39 KB rebuild response lands, does the renderer dispatch ANY
#            action naming ``network-visualizer-graph``?
#
#            actions dispatched -> the renderer DOES try to apply it; something
#                                  downstream of the dispatch drops or overwrites it.
#            no actions         -> the renderer never tries; the response is being
#                                  discarded before the apply step.
#
#          Records the callback-lifecycle sub-types alongside, because Dash routes
#          the apply through ``Callbacks.*`` aggregates rather than a single
#          obviously-named action -- a bare type histogram hides it.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_f039_renderer_apply.py --seconds 60
#
# Exit codes: 0 probe completed (read the verdict), 2 the redux store was not reachable.

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

TARGET = "network-visualizer-graph"

INSTALL = """
(target) => {
  const store = (window.store && window.store.dispatch) ? window.store
              : (window.dash_stores && window.dash_stores[0]) || null;
  if (!store || !store.dispatch) return false;
  window.__f039r = {naming: [], types: {}, sub: {}, total: 0, target: target};
  const orig = store.dispatch.bind(store);
  store.dispatch = (action) => {
    try {
      const w = window.__f039r;
      w.total++;
      const t = (action && action.type) || typeof action;
      w.types[t] = (w.types[t] || 0) + 1;
      // Callbacks.* carries an array payload of sub-actions; count those separately,
      // because the apply is routed through them rather than a distinctly-named type.
      if (action && Array.isArray(action.payload)) {
        for (const p of action.payload) {
          const st = (p && p.type) || '?';
          w.sub[st] = (w.sub[st] || 0) + 1;
        }
      }
      let s = '';
      try { s = JSON.stringify(action); } catch (e) { s = String(action); }
      if (s && s.indexOf(w.target) !== -1) {
        if (w.naming.length < 25) {
          w.naming.push({type: t, len: s.length, head: s.slice(0, 260)});
        }
        w.naming_count = (w.naming_count || 0) + 1;
      }
    } catch (e) { /* never let the probe break the app */ }
    return orig(action);
  };
  return true;
}
"""

REPORT = """
() => {
  const w = window.__f039r || {};
  return {
    total: w.total || 0,
    naming_count: w.naming_count || 0,
    samples: w.naming || [],
    types: w.types || {},
    sub: w.sub || {},
  };
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--out", default="/tmp/juniper-e2e/f039_renderer_apply.json")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    responses = {"n": 0}
    capture: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            ensure_no_modal(page)
            open_tab(page, "Network Topology")
            page.wait_for_timeout(3000)

            if not page.evaluate(INSTALL, TARGET):
                log("  !! redux store not reachable -- this probe measured NOTHING")
                return 2

            def on_response(resp):
                if "_dash-update-component" not in resp.url:
                    return
                try:
                    body = resp.text()
                except Exception:
                    return
                if f'"{TARGET}"' in body:
                    responses["n"] += 1

            page.on("response", on_response)

            log(f"  dispatch wrapped; watching {args.seconds}s for responses naming {TARGET!r}")
            page.wait_for_timeout(int(args.seconds * 1000))

            rep = page.evaluate(REPORT)
            rep["rebuild_responses"] = responses["n"]

            log(f"  rebuild responses carrying the graph : {responses['n']}")
            log(f"  total redux actions                  : {rep['total']}")
            log(f"  actions NAMING {TARGET} : {rep['naming_count']}")
            log("  action types:")
            for t, n in sorted(rep["types"].items(), key=lambda kv: -kv[1])[:8]:
                log(f"    {n:6d}x  {t}")
            if rep["sub"]:
                log("  Callbacks.* sub-action types:")
                for t, n in sorted(rep["sub"].items(), key=lambda kv: -kv[1])[:10]:
                    log(f"    {n:6d}x  {t}")
            for s in rep["samples"][:4]:
                log(f"    NAMING [{s['type']}] len={s['len']} {s['head'][:200]}")

            log("")
            if responses["n"] == 0:
                log("  !! no rebuild response arrived in the window -- inconclusive, re-run longer")
            elif rep["naming_count"] == 0:
                log("  => The renderer dispatches NOTHING naming the graph while its responses arrive.")
                log("     The response is discarded BEFORE the apply step, not overwritten after it.")
            else:
                log("  => The renderer DOES dispatch for the graph; the value is dropped/overwritten")
                log("     downstream of the dispatch. Inspect the sample payloads above.")

            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(rep, fh, indent=2, default=str)
            log(f"  -> {args.out}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
