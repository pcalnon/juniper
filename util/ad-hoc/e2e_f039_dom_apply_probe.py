#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: F-CANOPY-039 -- the topology rebuild returns a provably CORRECT figure
#          (200 / 39,319 B / ~206 traces / empty_fig=False) and the DOM never
#          applies it. This probe runs that finding's three named next-probes in
#          ONE session, because they are cheap and they discriminate each other:
#
#            1. LIVE duplicate ids. The static layout check is already clean
#               (464 declarations, 464 distinct), so a duplicated ``dcc.Store`` is
#               excluded -- but the A1-iii-b1 tab rebuild reconstructs the tab bar,
#               and a stale DETACHED ``network-visualizer-graph`` would take the
#               response while the probe reads the live one.
#            2. Visibility. A graph inside a ``display:none`` pane can receive a
#               figure without laying out, which reads as "not applied".
#            3. Application. Sample ``gd.data`` immediately BEFORE and AFTER each
#               rebuild response lands, so "the response arrived" and "the DOM
#               changed" are two separate observations joined on one event rather
#               than two independent polls that can each be wrong.
#
#          Deliberately reports the plotly instance's own init state too: an
#          element with no ``_fullLayout`` has never been rendered by plotly at
#          all, which is a different failure from one that renders empty.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_f039_dom_apply_probe.py --seconds 120
#
# Exit codes: 0 probe completed (read the report; it does not judge), 2 setup failed.

import argparse
import importlib.util
import json
import os
import sys
import time

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

NV = "network-visualizer"
GRAPH = f"{NV}-graph"

# One evaluate, so every field describes the SAME instant.
INSPECT = """
() => {
  const id = 'network-visualizer-graph';
  const all = Array.from(document.querySelectorAll('[id="' + id + '"]'));
  const describe = (el) => {
    // ``dcc.Graph(id=X)`` renders a WRAPPER div carrying the id; the plotly
    // instance (``.data`` / ``_fullLayout``) lives on an inner ``.js-plotly-plot``.
    // Reading the wrapper reports "plotly never initialised" for a perfectly
    // healthy graph -- resolve it the way the driver's ``fig_info`` does.
    const gd = (el.classList && el.classList.contains('js-plotly-plot'))
                 ? el : el.querySelector('.js-plotly-plot');
    const attached = document.body.contains(el);
    // Walk the ancestor chain for anything that would suppress layout.
    let hidden = null, node = el;
    while (node && node !== document.body) {
      const cs = window.getComputedStyle(node);
      if (cs.display === 'none' || cs.visibility === 'hidden') {
        hidden = (node.id || node.className || node.tagName) + ':' + cs.display + '/' + cs.visibility;
        break;
      }
      node = node.parentElement;
    }
    const r = el.getBoundingClientRect();
    return {
      attached: attached,
      hidden_by: hidden,
      rect: [Math.round(r.width), Math.round(r.height)],
      plotly_found: Boolean(gd),
      n_traces: (gd && gd.data && gd.data.length) || 0,
      plotly_inited: Boolean(gd && gd._fullLayout),
      has_modebar: Boolean(el.querySelector('.modebar')),
      // A cheap content signature, same idea as the driver's ``sig``.
      sig: JSON.stringify((gd && gd.data) || []).length,
    };
  };
  const counts = {};
  for (const key of ['input', 'hidden', 'output', 'connection']) {
    const n = document.getElementById('network-visualizer-' + key + '-count');
    counts[key] = n ? n.textContent.trim() : null;
  }
  return {
    n_elements_with_graph_id: all.length,
    elements: all.map(describe),
    counts: counts,
    active_tab: (document.querySelector('[role=tab].active') || {}).textContent || null,
  };
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seconds", type=float, default=120.0, help="how long to watch for rebuild responses")
    ap.add_argument("--out", default="/tmp/juniper-e2e/f039_dom_apply.json")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    report: dict = {"responses": []}
    capture: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            ensure_no_modal(page)
            open_tab(page, "Network Topology")
            page.wait_for_timeout(4000)

            report["at_entry"] = page.evaluate(INSPECT)
            log(f"  AT TAB ENTRY: {json.dumps(report['at_entry'])[:500]}")

            # Join "a rebuild response landed" to "did gd.data change?" on ONE event.
            pending: list = []

            def on_response(resp):
                if "_dash-update-component" not in resp.url:
                    return
                try:
                    body = resp.text()
                except Exception:
                    return
                if f'"{GRAPH}"' not in body:
                    return
                pending.append({"t": time.time(), "bytes": len(body), "status": resp.status})

            page.on("response", on_response)

            t_end = time.time() + args.seconds
            seen = 0
            while time.time() < t_end:
                page.wait_for_timeout(500)
                while len(pending) > seen:
                    ev = pending[seen]
                    seen += 1
                    before = page.evaluate(INSPECT)
                    page.wait_for_timeout(1500)
                    after = page.evaluate(INSPECT)
                    first_b = (before.get("elements") or [{}])[0]
                    first_a = (after.get("elements") or [{}])[0]
                    row = {
                        "resp_bytes": ev["bytes"],
                        "status": ev["status"],
                        "n_elements": after.get("n_elements_with_graph_id"),
                        "traces_before": first_b.get("n_traces"),
                        "traces_after": first_a.get("n_traces"),
                        "sig_before": first_b.get("sig"),
                        "sig_after": first_a.get("sig"),
                        "hidden_by": first_a.get("hidden_by"),
                        "rect": first_a.get("rect"),
                        "plotly_inited": first_a.get("plotly_inited"),
                        "counts_after": after.get("counts"),
                    }
                    report["responses"].append(row)
                    log(f"  RESPONSE {ev['bytes']}B -> elements={row['n_elements']} traces {row['traces_before']}->{row['traces_after']} sig {row['sig_before']}->{row['sig_after']} hidden_by={row['hidden_by']} rect={row['rect']} plotly_inited={row['plotly_inited']} counts={row['counts_after']}")

            report["at_end"] = page.evaluate(INSPECT)
            log(f"  AT END: {json.dumps(report['at_end'])[:500]}")

            applied = [r for r in report["responses"] if (r["traces_after"] or 0) > (r["traces_before"] or 0)]
            log("")
            log(f"  rebuild responses observed : {len(report['responses'])}")
            log(f"  responses that CHANGED the DOM: {len(applied)}")
            log(f"  duplicate graph elements   : {report['at_end'].get('n_elements_with_graph_id')}  (1 = no duplicate)")
            log(f"  hidden ancestor            : {(report['at_end'].get('elements') or [{}])[0].get('hidden_by')}")
            log(f"  plotly initialised         : {(report['at_end'].get('elements') or [{}])[0].get('plotly_inited')}")
        finally:
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2, default=str)
            log(f"  -> {args.out}")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
