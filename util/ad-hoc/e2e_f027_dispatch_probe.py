#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (dispatch)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Does the BROWSER ever dispatch the dead consumers?

Static analysis is exhausted: the callbacks are registered, every component is in
the layout, and the browser's dependency list carries them. The remaining fork is
runtime, and one field settles it.

Every ``_dash-update-component`` REQUEST carries an ``output`` field naming
exactly which callback the client decided to invoke. (This is NOT the documented
"a component id in a request proves nothing" trap -- that warns about *inputs*,
which a many-Input callback names wholesale. ``output`` identifies the callback
itself.)

  - ``output`` seen  -> the client DOES dispatch; the server's return value is
    failing to change the prop. The bug is in the handler / its return.
  - ``output`` never seen -> the client never dispatches; the store's prop is not
    actually changing client-side even though the writer's response carries data.

Run with the isolated stack UP and a training run live:

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_dispatch_probe.py --seconds 90

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

# (label, marker that appears in the request's "output" field)
WATCH = [
    ("DEAD  candidate badge   ", "candidate-metrics-panel-status-badge"),
    ("DEAD  candidate poolinfo", "candidate-metrics-panel-pool-info"),
    ("DEAD  boundary plot     ", "decision-boundary-plot"),
    ("DEAD  dataset plots     ", "dataset-plotter-scatter-plot"),
    ("LIVE  metrics progress  ", "metrics-panel-progress-detail"),
    ("LIVE  metrics lr        ", "metrics-panel-current-lr"),
    ("CONSUM candidate history", "candidate-metrics-panel-pool-history-store"),
    ("CONSUM candidate progress", "candidate-metrics-panel-progress-section"),
    ("WRITE candidate store   ", "candidate-metrics-panel-training-state-store"),
    ("WRITE dataset store     ", "dataset-plotter-dataset-store"),
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
        # Full console capture. If Dash's client throws while applying a response,
        # everything downstream stops and NO consumer is ever dispatched -- which
        # would look exactly like the F-CANOPY-027 signature. The shared helper
        # only forwards error/warning, so hook everything including pageerror.
        console_all: list = []
        page.on("console", lambda m: console_all.append(f"[{m.type}] {m.text[:220]}"))
        page.on("pageerror", lambda e: console_all.append(f"[pageerror] {str(e)[:300]}"))
        try:
            # clear any modal, then activate the tab under test
            for _ in range(12):
                opened = page.evaluate(
                    """() => [...document.querySelectorAll('[role=dialog]')]
                         .filter(x=>(x.className||'').includes('show')).length"""
                )
                if not opened:
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
            log(f"activated tab {args.tab!r}; observing {args.seconds}s")
            page.wait_for_timeout(args.seconds * 1000)

            reqs = [c for c in capture if "_dash-update-component" in (c.get("url") or "")]
            log(f"_dash-update-component REQUESTS captured: {len(reqs)}")

            def out_field(body: str):
                try:
                    return json.loads(body).get("output", "")
                except Exception:  # noqa: BLE001
                    return ""

            outs = [out_field(r.get("body") or "") for r in reqs]
            log(f"requests with a parseable output field: {sum(1 for o in outs if o)}")
            log("")
            for label, marker in WATCH:
                n = sum(1 for o in outs if marker in o)
                verdict = "DISPATCHED" if n else "never dispatched"
                log(f"  {label}  {marker:<46} {n:>4} dispatch(es)  <- {verdict}")

            log("")
            log(f"console messages captured: {len(console_all)}")
            errs = [c for c in console_all if c.startswith("[error]") or c.startswith("[pageerror]")]
            warns = [c for c in console_all if c.startswith("[warning]")]
            log(f"  errors: {len(errs)}  warnings: {len(warns)}")
            for c in (errs + warns)[:14]:
                log(f"    {c}")

            log("")
            distinct = {}
            for o in outs:
                if o:
                    distinct[o] = distinct.get(o, 0) + 1
            log(f"distinct callbacks dispatched in the window: {len(distinct)}")
            for o, n in sorted(distinct.items(), key=lambda kv: -kv[1])[:18]:
                log(f"    {n:>4}x  {o[:110]}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
