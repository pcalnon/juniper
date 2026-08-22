#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (in-flight requests)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Do the dead consumers' requests ever COMPLETE?

The mount probe showed ``dataset-plotter-scatter-plot`` dispatching exactly once
(~40 s in) and never again, while cheap text consumers dispatched 5x. Dash's
client will not re-dispatch a callback that still has an outstanding request, so
"fires once then never again" is the signature of a request that never returns.

That reframes F-CANOPY-027 from "the callback never fires" to "the callback fires
and hangs" -- a different defect with a different fix.

Pairs every ``_dash-update-component`` request with its response and reports, per
watched callback: dispatches, completions, and the duration of anything still in
flight when the window closes.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_inflight.py --seconds 180

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
CANOPY = _w3.CANOPY

WATCH = [
    ("DEAD   ", "candidate-metrics-panel-status-badge"),
    ("DEAD   ", "candidate-metrics-panel-pool-info"),
    ("DEAD   ", "candidate-metrics-panel-loss-plot"),
    ("DEAD   ", "decision-boundary-plot"),
    ("DEAD   ", "dataset-plotter-scatter-plot"),
    ("WORKING", "metrics-panel-progress-detail"),
    ("WORKING", "metrics-panel-current-lr"),
]

HOOK = """
window.__f = {rows: []};
(function(){
  const orig = window.fetch;
  window.fetch = async function(...a) {
    const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
    let out = '';
    try { if (url.includes('_dash-update-component') && a[1] && a[1].body) {
      out = (JSON.parse(a[1].body).output) || '';
    } } catch(e){}
    if (!out) return orig.apply(this,a);
    const row = {o: out, start: Date.now(), end: null, status: null, err: null};
    window.__f.rows.push(row);
    try {
      const res = await orig.apply(this,a);
      row.end = Date.now(); row.status = res.status;
      return res;
    } catch (e) {
      row.end = Date.now(); row.err = String(e).slice(0,120);
      throw e;
    }
  };
})();
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=int, default=180)
    ap.add_argument("--tab", default=None, help="optional tab to activate after load")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width": 1600, "height": 1100})
        ctx.add_init_script(HOOK)
        page = ctx.new_page()
        try:
            page.goto(CANOPY, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6000)
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
            if args.tab:
                page.evaluate(
                    """(label) => { const t=[...document.querySelectorAll('[role=tab]')]
                           .find(x=>x.textContent.trim()===label); if(t) t.click(); }""",
                    args.tab,
                )
                log(f"activated tab {args.tab!r}")
            log(f"observing {args.seconds}s")
            page.wait_for_timeout(args.seconds * 1000)

            rows = page.evaluate("""() => window.__f.rows""")
            now = page.evaluate("""() => Date.now()""")
            log(f"total dispatches tracked: {len(rows)}")
            done = [r for r in rows if r.get("end")]
            log(f"  completed: {len(done)}   still IN FLIGHT: {len(rows) - len(done)}")
            log("")
            for tag, marker in WATCH:
                mine = [r for r in rows if marker in (r.get("o") or "")]
                fin = [r for r in mine if r.get("end")]
                pend = [r for r in mine if not r.get("end")]
                durs = sorted(round((r["end"] - r["start"]) / 1000.0, 1) for r in fin)
                pend_age = sorted(round((now - r["start"]) / 1000.0, 1) for r in pend)
                log(
                    f"  [{tag}] {marker:<44} dispatched={len(mine):>2} "
                    f"completed={len(fin):>2} inflight={len(pend):>2}"
                )
                if durs:
                    log(f"        completed durations (s): {durs[:8]}")
                if pend_age:
                    log(f"        IN-FLIGHT ages (s): {pend_age[:8]}   <-- never returned")
            log("")
            slow = sorted(
                ({"o": r["o"][:70], "s": round((now - r["start"]) / 1000.0, 1)} for r in rows if not r.get("end")),
                key=lambda x: -x["s"],
            )[:12]
            if slow:
                log("longest-running IN-FLIGHT requests:")
                for s in slow:
                    log(f"    {s['s']:>6}s   {s['o']}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
