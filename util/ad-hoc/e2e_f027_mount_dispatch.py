#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (mount dispatch)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Do the dead consumers fire at INITIAL MOUNT?

Every previous probe installed its fetch hook AFTER ``open_dashboard`` had already
navigated, waited ~3 s and dismissed the welcome modal -- so all of them were
blind to the initial-mount burst. Those callbacks carry ``prevent_initial_call``
unset, so Dash should invoke each of them once as the app hydrates.

  fires at mount, never again -> the callbacks ARE wired; the failure is in
     change-propagation from the store afterwards
  never fires at all          -> the callbacks are not wired into the client's
     graph despite appearing in /dashboard/_dash-dependencies

Uses ``add_init_script`` so the hook is installed before the page's own scripts
run and cannot miss anything.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_mount_dispatch.py --seconds 60

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time

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
    ("WORKING", "metrics-panel-loss-plot"),
]

HOOK = """
window.__mount = [];
(function(){
  const orig = window.fetch;
  window.fetch = async function(...a) {
    const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
    try { if (url.includes('_dash-update-component') && a[1] && a[1].body) {
      const b = JSON.parse(a[1].body);
      window.__mount.push({t: Date.now(), o: b.output || '',
                           changed: (b.changedPropIds||[]).join(',')});
    } } catch(e){}
    return orig.apply(this,a);
  };
})();
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=int, default=60)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width": 1600, "height": 1100})
        # installed BEFORE any page script runs -- this is the whole point
        ctx.add_init_script(HOOK)
        page = ctx.new_page()
        try:
            t0 = time.time()
            log(f"navigating with the hook pre-installed: {CANOPY}")
            page.goto(CANOPY, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(args.seconds * 1000)

            outs = page.evaluate("""() => window.__mount""")
            log(f"dispatches captured from first byte: {len(outs)}")
            log("")
            for tag, marker in WATCH:
                hits = [o for o in outs if marker in (o.get("o") or "")]
                first = ""
                if hits:
                    dt = (hits[0]["t"] / 1000.0) - t0
                    first = f"  first at ~{dt:0.1f}s  changedPropIds={hits[0].get('changed','')[:60]!r}"
                log(f"  [{tag}] {marker:<44} {len(hits):>3} dispatch(es){first}")

            log("")
            # what DID fire in the first few seconds?
            early = sorted(outs, key=lambda o: o["t"])[:14]
            log("first 14 dispatches overall (mount burst):")
            for o in early:
                log(f"    {str(o.get('o'))[:96]}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
