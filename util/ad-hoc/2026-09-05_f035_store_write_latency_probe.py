#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-035 — why does a write that lands on the wire never reach the store?

THE STATE THIS PROBE ENTERS.

``util/ad-hoc/2026-09-04_f035_candidate_loss_redrive.py`` established, on canopy
main, that ``metrics-panel-metrics-store`` is WRITTEN and never APPLIED: 14 parsed
writes of 500 rows in a 30 s window (``omitted=0``, ``unparsed=0``) with the store
reading ``len=0`` immediately before and immediately after. Three explanations were
then eliminated by measurement rather than argument:

  * a SECOND store instance -- refuted by ``/dashboard/_dash-layout``, which is
    server-rendered and therefore blind to nothing: 465 id-bearing nodes, 465
    distinct, zero duplicate ids anywhere, ``metrics-panel-metrics-store`` exactly
    once with ``data=[]``. (``paths.strs`` cannot answer this; the layout can.)
  * the UNGUARDED ``allow_duplicate`` writer clobbering it
    (``append_ws_metrics_store``, dashboard_manager.py:3910) -- refuted twice:
    statically it returns ``dash.no_update`` when it drained no events, so it can
    never write an empty value; empirically ``ws-metrics-buffer`` held its mount
    default with ``gen`` 0 -> 0 across the window, so it never fired at all.
  * the server-side view being stale -- refuted by the F-039 topoprobe, which logs
    the guarded handler's own ``State``: 98 comparisons, every one ``eq=False`` at
    a constant ``cur_len=2`` (the serialised ``[]``) against ``new_len=164570``.

That last one is the load-bearing fact. The handler receives its OWN output back as
``State`` on the next tick. If the browser had applied any write, the following
tick's ``State`` would carry 500 rows. It carried ``[]`` ninety-eight times. So the
response reaches the browser and the browser does not apply it.

WHAT THIS PROBE MEASURES, AND WHY IT IS THE RIGHT NEXT ONE.

The arc already carries a mechanism with exactly this signature: dash-renderer's
callback concurrency cap, where a RE-REQUEST retires the IN-FLIGHT call and its
response is discarded on arrival. ``update_metrics_store`` is driven by
``fast-update-interval`` at ``FAST_UPDATE_INTERVAL_MS = 1000``. The redrive's own
numbers give a store-write cadence of ~1 per 2.1 s -- slower than the 1 s tick that
re-requests it. If each response is superseded before it lands, the store can never
advance while every response on the wire carries a full payload.

So the discriminating quantity is **per-request latency against the re-request
interval**, measured at the browser, per callback round trip:

    duration     request start -> response end, for responses writing the store
    gap          time since the PREVIOUS request that wrote the store

``duration > gap`` for a request means a successor was issued while it was still in
flight -- the retirement precondition. This probe reports the distribution of both
and the fraction of overlapped requests; it does NOT assert the mechanism.

WHAT IT DELIBERATELY DOES NOT CLAIM. Overlap is the PRECONDITION for retirement, not
retirement itself: dash-renderer could still apply a superseded response. A high
overlap fraction makes the hypothesis live and tells the fix which knob to reach for
(suppress the TRIGGER, not the work); it does not close the finding. Reporting it as
a cause would be this arc's recurring error -- a well-formed measurement of an
ADJACENT question, returned in confident numbers.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-05_f035_store_write_latency_probe.py --window 60
"""

import argparse
import importlib.util
import json
import os
import statistics
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")

log = _seg17.log
CANOPY = _seg17.CANOPY
open_dashboard = _seg17.open_dashboard
open_tab = _seg17.open_tab
_store = _seg17._store

METRICS_STORE = "metrics-panel-metrics-store"
TICK_MS = 1000  # DashboardConstants.FAST_UPDATE_INTERVAL_MS, canopy_constants.py:370
OUT = os.environ.get("F035_LATENCY_RESULTS", "/tmp/juniper-e2e/f035_latency.json")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=float, default=60.0, help="seconds to observe")
    ap.add_argument("--tab", default="Candidate Metrics", help="tab to drive")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res = {"canopy": CANOPY, "tick_ms": TICK_MS, "window_s": args.window, "writes": []}
    started: dict = {}

    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, [])
        try:
            open_tab(page, args.tab)
            page.wait_for_timeout(4000)

            before = _store(page, METRICS_STORE) or {}
            res["store_before"] = {
                "ok": before.get("ok"),
                "len": len(before["value"]) if isinstance(before.get("value"), list) else None,
            }

            def on_request(req):
                if "_dash-update-component" in req.url:
                    started[req] = time.time()

            def on_response(resp):
                if "_dash-update-component" not in resp.url:
                    return
                t_end = time.time()
                t_start = started.pop(resp.request, None)
                try:
                    body = resp.text()
                except Exception:  # noqa: BLE001
                    return
                if METRICS_STORE not in body:
                    return
                try:
                    payload = json.loads(body)
                except ValueError:
                    return
                rmap = payload.get("response") if isinstance(payload, dict) else None
                if not isinstance(rmap, dict) or METRICS_STORE not in rmap:
                    return  # named but no value -- a no_update; not a write
                val = (rmap.get(METRICS_STORE) or {}).get("data")
                if not isinstance(val, list):
                    return
                res["writes"].append(
                    {
                        "t_start": None if t_start is None else round(t_start - t0, 3),
                        "t_end": round(t_end - t0, 3),
                        "duration_s": None if t_start is None else round(t_end - t_start, 3),
                        "rows": len(val),
                    }
                )

            page.on("request", on_request)
            page.on("response", on_response)
            t0 = time.time()
            page.wait_for_timeout(int(args.window * 1000))
            page.remove_listener("request", on_request)
            page.remove_listener("response", on_response)

            after = _store(page, METRICS_STORE) or {}
            res["store_after"] = {
                "ok": after.get("ok"),
                "len": len(after["value"]) if isinstance(after.get("value"), list) else None,
            }
        finally:
            browser.close()

    w = res["writes"]
    durs = [x["duration_s"] for x in w if x["duration_s"] is not None]
    # Gap = spacing between consecutive store-writing REQUESTS. A request whose
    # duration exceeds the gap to its successor was still in flight when that
    # successor was issued -- the retirement precondition.
    starts = sorted(x["t_start"] for x in w if x["t_start"] is not None)
    gaps = [round(b - a, 3) for a, b in zip(starts, starts[1:])]
    overlapped = sum(1 for x in w if x["duration_s"] is not None and x["t_start"] is not None and any(s > x["t_start"] and s < x["t_start"] + x["duration_s"] for s in starts))

    res["summary"] = {
        "writes": len(w),
        "rows_each": sorted({x["rows"] for x in w}),
        "duration_s": {
            "n": len(durs),
            "min": min(durs) if durs else None,
            "median": round(statistics.median(durs), 3) if durs else None,
            "max": max(durs) if durs else None,
        },
        "request_gap_s": {
            "n": len(gaps),
            "min": min(gaps) if gaps else None,
            "median": round(statistics.median(gaps), 3) if gaps else None,
            "max": max(gaps) if gaps else None,
        },
        "overlapped_requests": overlapped,
        "overlap_fraction": round(overlapped / len(w), 3) if w else None,
        "tick_ms": TICK_MS,
    }

    log(f"  store len before={res['store_before'].get('len')} after={res['store_after'].get('len')}")
    log(f"  writes={len(w)} rows={res['summary']['rows_each']}")
    log(f"  duration_s  {res['summary']['duration_s']}")
    log(f"  req gap_s   {res['summary']['request_gap_s']}")
    log(f"  OVERLAPPED (a successor was issued while this one was in flight): "
        f"{overlapped}/{len(w)} = {res['summary']['overlap_fraction']}")
    log("  NOTE: overlap is the PRECONDITION for renderer retirement, not retirement itself.")

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
