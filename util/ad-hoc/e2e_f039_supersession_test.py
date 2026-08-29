#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: F-CANOPY-039's discriminating test. The renderer trace shows the
#          rebuild's callback lifecycle COMPLETING (AddRequested -> LOADING ->
#          Executed -> LOADED) while no action ever carries the 39 KB figure, and
#          ``Callbacks.RemoveRequested`` firing for it. The hypothesis is
#          SUPERSESSION: the invocation is retired before its response lands, so
#          the payload is discarded rather than applied.
#
#          If that is right, removing the competing cadence should make it paint.
#          ``tabpoll-topology`` ticks every 5 s while the rebuild's own server time
#          is 1.5-5 s, so it is the obvious racer -- and after F-CANOPY-037 it is
#          the only frequent trigger left.
#
#          Method: disable that Interval at RUNTIME via the component's own
#          setProps (no code change, no restart), let anything in flight settle,
#          then trigger the rebuild exactly ONCE through a different Input and
#          watch.
#
#            paints  -> supersession CONFIRMED; the fix is a cadence / no_update
#                       guard, not anything in the component.
#            silent  -> supersession is NOT the mechanism; look elsewhere, and the
#                       hypothesis is falsified cheaply rather than after a source dive.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_f039_supersession_test.py
#
# Exit codes: 0 test ran (read the verdict), 2 a setProps target was unreachable.

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
TABPOLL = "tabpoll-topology"
TRIGGER = "network-visualizer-show-weights"

SETPROPS = """
(cfg) => {
  const {id, payload} = cfg;
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
  return {ok: false, err: found ? 'found but no setProps' : 'not found', hops};
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settle", type=float, default=20.0, help="seconds to let in-flight work drain after disabling the tick")
    ap.add_argument("--watch", type=float, default=90.0, help="seconds to watch after the single trigger")
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
            log(f"  BEFORE            : traces={len(before.get('traces') or [])} sig={before.get('sig')}")

            res = page.evaluate(SETPROPS, {"id": TABPOLL, "payload": {"disabled": True}})
            log(f"  disable {TABPOLL}: {json.dumps(res)}")
            if not res.get("ok"):
                log("  !! could not disable the tick -- this test measured NOTHING")
                return 2

            log(f"  letting in-flight work drain for {args.settle}s ...")
            page.wait_for_timeout(int(args.settle * 1000))
            mid = fig_info(page, GRAPH)
            log(f"  AFTER DISABLE     : traces={len(mid.get('traces') or [])} sig={mid.get('sig')}")

            # One trigger, through an Input that is NOT the interval.
            res2 = page.evaluate(SETPROPS, {"id": TRIGGER, "payload": {"value": []}})
            log(f"  single trigger ({TRIGGER} -> []): {json.dumps(res2)}")
            if not res2.get("ok"):
                log("  !! could not drive the trigger -- this test measured NOTHING")
                return 2

            painted_at = None
            for i in range(int(args.watch // 3)):
                page.wait_for_timeout(3000)
                cur = fig_info(page, GRAPH)
                if len(cur.get("traces") or []) > 0:
                    painted_at = (i + 1) * 3
                    break

            after = fig_info(page, GRAPH)
            log(f"  AFTER TRIGGER     : traces={len(after.get('traces') or [])} sig={after.get('sig')} painted_at={painted_at}s")
            log("")
            if painted_at is not None:
                log("  => PAINTED with the competing 5 s tick disabled.")
                log("     SUPERSESSION CONFIRMED: the rebuild's invocation was being retired before its")
                log("     response landed. The fix is a cadence / no_update guard on that trigger, not")
                log("     anything in the component or the figure.")
            else:
                log("  => STILL BLANK with the competing tick disabled.")
                log("     Supersession by tabpoll-topology is NOT the mechanism -- hypothesis falsified.")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
