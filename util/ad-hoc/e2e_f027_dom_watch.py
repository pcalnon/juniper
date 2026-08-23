#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 (does the panel DOM ever change?)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Direct test of the user-visible claim: with its own tab active and a live run,
does the Candidate Metrics panel's DOM ever change?

Everything else has been measured at the wire. This measures the thing the
finding actually asserts, over a window long enough to clear F-CANOPY-004's
30 s-to-minutes callback lag, and reports every distinct DOM state seen.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_dom_watch.py --seconds 180

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
http_get = _w3.http_get
open_dashboard = _w3.open_dashboard

READ = """() => { const g = id => { const e=document.getElementById(id);
       return e ? (e.innerText||'').trim().slice(0,60) : 'ABSENT'; };
   return {badge:g('candidate-metrics-panel-status-badge'),
           phase:g('candidate-metrics-panel-phase'),
           pool:g('candidate-metrics-panel-pool-size'),
           info:g('candidate-metrics-panel-pool-info')}; }"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=int, default=180)
    ap.add_argument("--step", type=int, default=10)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            for _ in range(10):
                if not page.evaluate(
                    """() => [...document.querySelectorAll('[role=dialog]')]
                         .filter(x=>(x.className||'').includes('show')).length"""
                ):
                    break
                page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
                page.wait_for_timeout(700)
                page.keyboard.press("Escape")
                page.wait_for_timeout(700)

            page.evaluate(
                """(l) => { const t=[...document.querySelectorAll('[role=tab]')]
                       .find(x=>x.textContent.trim()===l); if(t) t.click(); }""",
                "Candidate Metrics",
            )
            page.wait_for_timeout(5000)

            st = http_get("/api/state", timeout=60)[1]
            log(f"backend at start: pool_status={st.get('candidate_pool_status')!r} "
                f"pool_size={st.get('candidate_pool_size')} cand_epoch={st.get('candidate_epoch')}")

            seen = []
            steps = max(1, args.seconds // args.step)
            for i in range(steps):
                page.wait_for_timeout(args.step * 1000)
                d = page.evaluate(READ)
                key = json.dumps(d, sort_keys=True)
                if not seen or seen[-1][1] != key:
                    seen.append((i * args.step, key))
                    log(f"  t={i * args.step:>3}s  DOM CHANGE -> {json.dumps(d)}")

            st2 = http_get("/api/state", timeout=60)[1]
            log("")
            log(f"backend at end  : pool_status={st2.get('candidate_pool_status')!r} "
                f"pool_size={st2.get('candidate_pool_size')} cand_epoch={st2.get('candidate_epoch')}")
            log(f"distinct DOM states across {args.seconds}s: {len(seen)}")
            if len(seen) <= 1:
                log("  VERDICT: panel DOM never changed -> F-CANOPY-027 reproduced")
            else:
                log("  VERDICT: panel DOM DID change -> re-examine the finding")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
