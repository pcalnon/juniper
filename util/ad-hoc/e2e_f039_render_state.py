#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Answer one question directly, because everything downstream of it in
#          F-CANOPY-039 is currently inferred rather than re-measured:
#          **is the topology graph still rendering empty right now?**
#
#          The arc's premise is that the rebuild takes its `input_units == 0` fast
#          path -- i.e. the value its READER receives is empty. But the duplicate-
#          store probe (2026-08-30) found the client's copy of
#          `network-visualizer-topology-store` holding **6,434 bytes** of real
#          topology, as a single instance, with no duplicate anywhere. Those two
#          things cannot both be true of the same moment, so one of them is stale.
#
#          Note what changed since the premise was established: canopy#537 merged,
#          which makes the tick short-circuit actually fire (it had named a lane
#          F-CANOPY-027 replaced, so it was dead code). Both live legs have since
#          been restarted onto that code. The rebuild's behaviour on a bare tick is
#          therefore NOT what it was when F-039 was characterised.
#
#          Reports the store's own client-side content alongside the render, so the
#          two are read from the same instant rather than from two sessions.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#     util/ad-hoc/e2e_f039_render_state.py --settle 30
#
# Exit: 0 measured, 1 could not measure (NOT a verdict).

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")

log = _w3.log
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
fig_info = _f027.fig_info

STORE_AND_COUNTS = """
() => {
  const out = {};
  const store = (window.store && window.store.dispatch) ? window.store
              : (window.dash_stores && window.dash_stores[0]) || null;
  if (store) {
    const st = store.getState();
    const strmap = (st.paths && (st.paths.strs || st.paths)) || {};
    const p = strmap['network-visualizer-topology-store'];
    if (p) {
      let node = st.layout;
      try {
        for (const seg of p) node = node[seg];
        const d = node && node.props ? node.props.data : undefined;
        out.store_len = JSON.stringify(d === undefined ? null : d).length;
        out.input_units = d ? d.input_units : null;
        out.hidden_units = d ? d.hidden_units : null;
        out.connections = (d && d.connections) ? d.connections.length : null;
      } catch (e) { out.store_error = String(e); }
    } else { out.store_error = 'id not in paths'; }
  } else { out.store_error = 'redux store not on window'; }

  for (const [key, id] of [['input','network-visualizer-input-count'],
                           ['hidden','network-visualizer-hidden-count'],
                           ['output','network-visualizer-output-count'],
                           ['conns','network-visualizer-connection-count']]) {
    const el = document.getElementById(id);
    out[key + '_text'] = el ? (el.innerText || '').trim() : null;
  }
  return out;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settle", type=int, default=30)
    ap.add_argument("--samples", type=int, default=3, help="repeat the read, to catch a value that flips between ticks")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    samples = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            if not open_tab(page, "Network Topology"):
                log("could not open Network Topology — NOT a verdict")
                return 1
            for i in range(args.samples):
                page.wait_for_timeout(args.settle * 1000)
                s = page.evaluate(STORE_AND_COUNTS)
                g = fig_info(page, "network-visualizer-graph")
                rec = {
                    "sample": i + 1,
                    "store_len": s.get("store_len"),
                    "store_input_units": s.get("input_units"),
                    "store_hidden_units": s.get("hidden_units"),
                    "store_connections": s.get("connections"),
                    "store_error": s.get("store_error"),
                    "graph_present": g.get("present"),
                    "graph_plotly": g.get("plotly"),
                    "graph_traces": len(g.get("traces") or []),
                    "graph_sig": g.get("sig"),
                    "counts": [s.get("input_text"), s.get("hidden_text"), s.get("output_text"), s.get("conns_text")],
                }
                samples.append(rec)
                log(
                    f"sample {rec['sample']}: STORE len={rec['store_len']} "
                    f"input_units={rec['store_input_units']} hidden={rec['store_hidden_units']} conns={rec['store_connections']}"
                    f"  ||  GRAPH traces={rec['graph_traces']} sig={rec['graph_sig']} counts={rec['counts']}"
                )
        finally:
            browser.close()

    if not samples:
        log("no samples — instrument failure, not a finding")
        return 1
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(samples, fh, indent=2, sort_keys=True)
        log(f"-> {args.out}")

    log("")
    rendered = [s for s in samples if s["graph_traces"] > 0]
    populated = [s for s in samples if (s["store_input_units"] or 0) > 0]
    log(f"VERDICT: store populated in {len(populated)}/{len(samples)} samples; graph rendered in {len(rendered)}/{len(samples)}")
    if populated and not rendered:
        log("  => F-CANOPY-039 STILL REPRODUCES: the reader's store is populated and the graph is empty.")
    elif rendered and populated:
        log("  => F-CANOPY-039 DOES NOT REPRODUCE in this configuration. The graph renders from a populated store.")
        log("     Do not close the finding on this alone -- establish WHAT CHANGED (canopy#537 merged and")
        log("     both legs were restarted onto it) before re-classifying it.")
    elif not populated:
        log("  => the store itself is empty; the rebuild is behaving correctly. The defect is upstream of the graph.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
