#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (store deltas)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Does the dead store's VALUE ever change?

The dispatch probe established the shape of the bug: the writer is dispatched
24x while its consumers are dispatched 0x -- and the working pair shows
writer 21x -> consumer 4x. Dash only re-runs a consumer when its Input prop
actually CHANGES, so a 21:4 ratio is normal change-detection and 24:0 means the
store's value is never changing.

Two ways that happens, and they need different fixes:
  (a) the writer keeps returning ``dash.no_update`` -> the response carries NO
      payload for the store, and the prop is never written at all;
  (b) the writer returns a value that is deep-equal to the previous one -> the
      prop is "written" but Dash correctly skips dependents.

This hooks fetch, pairs each ``_dash-update-component`` response with the
callback its request named, and reports for each watched store: how many
dispatches, how many carried a payload, and how many payloads DIFFERED from the
previous one.

Run with the stack UP and a run live:

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_store_delta.py --seconds 90

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_w3drv", os.path.join(_HERE, "e2e_w3_params_driver.py"))
_w3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w3)

log = _w3.log
open_dashboard = _w3.open_dashboard

WATCH = [
    ("DEAD   ", "candidate-metrics-panel-training-state-store"),
    ("DEAD   ", "dataset-plotter-dataset-store"),
    ("DEAD   ", "decision-boundary-boundary-data"),
    ("WORKING", "metrics-panel-training-state-store"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=int, default=90)
    ap.add_argument("--tab", default="Candidate Metrics")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            for _ in range(12):
                if not page.evaluate(
                    """() => [...document.querySelectorAll('[role=dialog]')]
                         .filter(x=>(x.className||'').includes('show')).length"""
                ):
                    break
                page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
                page.wait_for_timeout(700)
                page.keyboard.press("Escape")
                page.wait_for_timeout(800)

            page.evaluate(
                """(label) => { const t=[...document.querySelectorAll('[role=tab]')]
                       .find(x=>x.textContent.trim()===label); if(t) t.click(); }""",
                args.tab,
            )
            page.wait_for_timeout(2500)

            page.evaluate(
                """(watch) => {
                  window.__d = {};
                  for (const w of watch) window.__d[w] = {dispatch:0, withPayload:0, changed:0, last:null, samples:[]};
                  const orig = window.fetch;
                  window.fetch = async function(...a) {
                    const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
                    let outField = '';
                    try { if (a[1] && a[1].body) outField = (JSON.parse(a[1].body).output)||''; } catch(e){}
                    const res = await orig.apply(this,a);
                    try { if (url.includes('_dash-update-component')) {
                      res.clone().text().then(t => {
                        for (const w of watch) {
                          if (!outField.includes(w)) continue;
                          const d = window.__d[w];
                          d.dispatch++;
                          let payload = null;
                          try { const j = JSON.parse(t);
                                const r = j.response || {};
                                if (r[w] && ('data' in r[w])) payload = JSON.stringify(r[w].data);
                          } catch(e){}
                          if (payload === null) return;
                          d.withPayload++;
                          if (d.last !== null && payload !== d.last) {
                            d.changed++;
                            if (d.samples.length < 2) d.samples.push(payload.slice(0,150));
                          }
                          d.last = payload;
                        }
                      }).catch(()=>{});
                    } } catch(e){}
                    return res;
                  };
                }""",
                [w for _, w in WATCH],
            )
            log(f"observing {args.seconds}s on tab {args.tab!r}")
            page.wait_for_timeout(args.seconds * 1000)
            data = page.evaluate("""() => window.__d""")

            log("")
            for tag, w in WATCH:
                d = data.get(w, {})
                log(
                    f"  [{tag}] {w:<46} dispatched={d.get('dispatch',0):>3}  "
                    f"carried_payload={d.get('withPayload',0):>3}  value_CHANGED={d.get('changed',0):>3}"
                )
            log("")
            for tag, w in WATCH:
                for s in (data.get(w, {}) or {}).get("samples", [])[:1]:
                    log(f"  sample changed payload for {w}:")
                    log(f"    {s}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
