#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Hold a real browser session on the Training Metrics tab long enough for
#          the metrics-store poll to fire many times, so the SERVER-side TOPOPROBE
#          instrumentation has samples to log. It measures nothing itself.
#
#          Why a driver at all: `_update_metrics_store_handler` is driven by
#          `fast-update-interval`, and a Dash interval only ticks inside a live
#          browser session. curl cannot produce a single sample.
#
#          Pair with:
#            e2e_f039_topoprobe_instrument.py apply  --checkout <canopy> --target metrics
#            <this script>
#            e2e_f039_topoprobe_instrument.py report --log <canopy log> --target metrics
#            e2e_f039_topoprobe_instrument.py revert --checkout <canopy>
#
#          What the report decides (F-CANOPY-035 / -038 / -039, one defect or three):
#          read the WHOLE series, not its head. Topology's baseline is eq=False x4
#          then eq=True x11 -- a head that disagrees with its tail, and reading only
#          the head is what produced the retracted "never advances" claim.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#     util/ad-hoc/e2e_f039_metrics_store_soak.py --seconds 120
#
# Exit: 0 if the session stayed open for the full soak, 1 otherwise.

import argparse
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str, fname: str):
    """Same loader the sibling drivers use -- these helpers are not a package."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")

log = _w3.log
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seconds", type=int, default=120, help="how long to hold the tab open")
    ap.add_argument("--tab", default="Training Metrics", help="tab to sit on")
    ap.add_argument("--also-candidates", action="store_true", help="spend the second half on Candidate Metrics (F-035 saw the store empty on BOTH)")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    rc = 1
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            if not open_tab(page, args.tab):
                log(f"FAILED: could not open tab {args.tab!r} — no samples will be produced")
                return 1
            half = args.seconds * 1000 // (2 if args.also_candidates else 1)
            log(f"holding {args.tab!r} for {half / 1000:.0f}s …")
            page.wait_for_timeout(half)
            if args.also_candidates:
                if open_tab(page, "Candidate Metrics"):
                    log(f"holding 'Candidate Metrics' for {half / 1000:.0f}s …")
                    page.wait_for_timeout(half)
                else:
                    log("WARNING: could not open Candidate Metrics; staying put")
                    page.wait_for_timeout(half)
            n_dash = sum(1 for c in capture if "_dash-update-component" in (c.get("url") or ""))
            log(f"soak complete: {len(capture)} requests, {n_dash} dash updates")
            # A soak that produced no dash updates produced no samples either --
            # say so, rather than let an empty probe log read as a finding.
            if n_dash == 0:
                log("WARNING: ZERO dash updates — the interval never ticked; any empty probe log is an INSTRUMENT failure, not a result")
            else:
                rc = 0
        finally:
            browser.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
