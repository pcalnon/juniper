#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Report the dash-renderer redux state's SHAPE, so an itempath walk can be
#          written against what is actually there instead of a guess.
#
#          Written because the first attempt at resolving RESET_COMPONENT_STATE
#          itempaths returned ``resolved=False`` for all 40 samples -- a vacuous
#          zero that would have "proved" F-CANOPY-033 is unrelated to
#          F-CANOPY-039. The walk, not the hypothesis, was wrong.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_f039_state_shape.py

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

SHAPE = """
() => {
  const store = (window.store && window.store.dispatch) ? window.store
              : (window.dash_stores && window.dash_stores[0]) || null;
  if (!store) return {error: 'store not on window'};
  const st = store.getState();
  const out = {top_keys: Object.keys(st)};
  // What does each plausible root look like?
  for (const k of ['layout', 'paths', 'components']) {
    const v = st[k];
    if (v === undefined) { out[k] = 'ABSENT'; continue; }
    out[k] = {type: typeof v, keys: (v && typeof v === 'object') ? Object.keys(v).slice(0, 12) : null};
  }
  // Resolve a KNOWN id through paths -> that is the itempath idiom Dash itself uses.
  try {
    const p = st.paths;
    const strmap = p && (p.strs || p);
    out.paths_kind = p ? Object.keys(p).slice(0, 6) : null;
    const known = strmap && strmap['network-visualizer-graph'];
    out.graph_path = known || null;

    // F-CANOPY-039: ``update_network_graph`` is an EIGHT-output callback. If any one
    // output id is unresolvable in ``paths``, dash-renderer can fail to apply the
    // whole batch -- which would present exactly as "the correct response arrives and
    // nothing changes", with a component that is provably healthy under setProps.
    const outputs = [
      'network-visualizer-graph',
      'network-visualizer-input-count',
      'network-visualizer-hidden-count',
      'network-visualizer-output-count',
      'network-visualizer-connection-count',
      'network-visualizer-topology-hash',
      'network-visualizer-new-node-highlight',
    ];
    out.rebuild_outputs = {};
    for (const id of outputs) out.rebuild_outputs[id] = Boolean(strmap && strmap[id]);
    out.rebuild_outputs_missing = outputs.filter((id) => !(strmap && strmap[id]));
  } catch (e) { out.paths_error = String(e); }
  return out;
}
"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            ensure_no_modal(page)
            open_tab(page, "Network Topology")
            page.wait_for_timeout(3000)
            shape = page.evaluate(SHAPE)
            log("  redux state shape:")
            log("  " + json.dumps(shape, indent=2, default=str)[:2000])
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
