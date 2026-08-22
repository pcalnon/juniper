#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (mount order)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

DISCRIMINATING TEST: does a store->render chain stop working once its panel has
been unmounted and remounted by a tab switch?

Every panel F-CANOPY-027 implicates (Candidate Metrics, Decision Boundary,
Dataset View) mounts only when the user switches to its tab. The one control that
works (the metrics panel) is the DEFAULT tab, mounted at initial render. If Dash's
client fails to (re)wire dependencies for components that mount later, that single
mechanism explains all three instances.

The prediction is sharp and falsifiable: the WORKING chain should BREAK after a
tab round-trip. Phases:

  A. on the default metrics tab, count dispatches of a known-live consumer
  B. switch away to another tab, then back
  C. count the same consumer again

  A>0 and C==0  -> mount-order is the mechanism (chain dies on remount)
  A>0 and C>0   -> mount order is NOT the mechanism; the metrics chain survives
                   remounting and the difference lies elsewhere

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_mount_order.py --window 45

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

LIVE_CONSUMER = "metrics-panel-progress-detail"
LIVE_STORE = "metrics-panel-stats-update-interval"  # trigger of the metrics writer


def install(page):
    page.evaluate(
        """() => {
          window.__m = {outs: []};
          const orig = window.fetch;
          window.fetch = async function(...a) {
            const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
            try { if (url.includes('_dash-update-component') && a[1] && a[1].body) {
              const o = (JSON.parse(a[1].body).output)||'';
              if (o) window.__m.outs.push({t: Date.now(), o});
            } } catch(e){}
            return orig.apply(this,a);
          };
          window.__mReset = () => { window.__m.outs.length = 0; };
        }"""
    )


def count(page, marker):
    return page.evaluate("""(m) => window.__m.outs.filter(x => x.o.includes(m)).length""", marker)


def switch(page, label):
    page.evaluate(
        """(label) => { const t=[...document.querySelectorAll('[role=tab]')]
               .find(x=>x.textContent.trim()===label); if(t) t.click(); }""",
        label,
    )
    page.wait_for_timeout(4000)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=int, default=45)
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

            install(page)

            # --- Phase A: default tab, never unmounted -------------------------
            log(f"PHASE A: on the default metrics tab for {args.window}s (panel mounted at initial render)")
            page.evaluate("""() => window.__mReset()""")
            page.wait_for_timeout(args.window * 1000)
            a = count(page, LIVE_CONSUMER)
            a_txt = page.evaluate(
                """() => { const e=document.getElementById('metrics-panel-progress-detail');
                     return e ? (e.innerText||'').trim().slice(0,70) : 'ABSENT'; }"""
            )
            log(f"  A: {LIVE_CONSUMER} dispatched {a}x   DOM={a_txt!r}")

            # --- Phase B: unmount + remount via a tab round-trip ---------------
            log("PHASE B: switching away to 'Candidate Metrics' and back to 'Training Metrics'")
            switch(page, "Candidate Metrics")
            page.wait_for_timeout(6000)
            switch(page, "Training Metrics")
            page.wait_for_timeout(6000)

            # --- Phase C: same tab, but the panel was remounted ---------------
            log(f"PHASE C: back on the metrics tab for {args.window}s (panel REMOUNTED by the switch)")
            page.evaluate("""() => window.__mReset()""")
            page.wait_for_timeout(args.window * 1000)
            c = count(page, LIVE_CONSUMER)
            c_txt = page.evaluate(
                """() => { const e=document.getElementById('metrics-panel-progress-detail');
                     return e ? (e.innerText||'').trim().slice(0,70) : 'ABSENT'; }"""
            )
            log(f"  C: {LIVE_CONSUMER} dispatched {c}x   DOM={c_txt!r}")

            log("")
            if a > 0 and c == 0:
                log("  VERDICT: chain DIED on remount -> mount order IS the mechanism")
            elif a > 0 and c > 0:
                log("  VERDICT: chain SURVIVED remount -> mount order is NOT the mechanism")
            else:
                log("  VERDICT: inconclusive (phase A produced no dispatches; control invalid)")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
