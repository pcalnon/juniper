#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-037 — does the topology rebuild fire on REAL cascade growth?

THE GAP THIS CLOSES.

F-CANOPY-037's fix (canopy#531) demoted `metrics-panel-metrics-store` from `Input`
to `State`. After that demotion, cascade growth reaches `update_network_graph`
through exactly ONE Input: ``ws-cascade-add-buffer``
(``network_visualizer.py``, "D-06: WS cascade_add events trigger topo refresh").

Every re-drive of this finding to date ran against a COMPLETED, saturated fixture —
40/40, `early_stopped`, zero cascade adds. So the trigger the fix CREATED, and the
live-contention regime the finding is actually about (the topology store rewriting on
its 5 s poll *while* cascade_add fires), have never been exercised. An adversarial
review on 2026-09-04 named that as the reason the closure could not stand.

This probe watches a real 40 -> 44 growth run and records, per cascade add:

  * whether ``ws-cascade-add-buffer`` is written at all (browser-visible);
  * whether the rebuild's own output is written AFTER it, and how long that took;
  * whether the DOM's hidden-count actually tracks the growth.

WHAT IT DELIBERATELY DOES NOT DO. It does not synthesise a buffer write via
``setProps``. That would exercise the wiring while removing the contention which is
the entire point -- a green result from it would mean nothing about the regime under
test.

READING THE OUTPUT. ``server_growth`` is cascor's own hidden-unit count, polled
independently of the browser; ``dom_growth`` is what canopy rendered. They are
reported separately and never reconciled by the probe, because a disagreement
between them IS the finding.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-05_f037_growth_trigger_probe.py --budget 900
"""

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.request
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
counts = _seg17.counts
_store = _seg17._store

CASCOR = os.environ.get("JUNIPER_E2E_CASCOR_URL", "http://127.0.0.1:8202")
BUFFER = "ws-cascade-add-buffer"
REBUILD = "network-visualizer-graph"
OUT = os.environ.get("F037_RESULTS", "/tmp/juniper-e2e/f037_growth.json")


def _server_hidden():
    """cascor's own hidden-unit count -- the growth oracle, read off the service.

    Deliberately NOT read through canopy: canopy's number is the thing under test,
    and an oracle that shares a path with the subject is not an oracle.
    """
    try:
        with urllib.request.urlopen(f"{CASCOR}/v1/network", timeout=8) as r:  # noqa: S310
            return (json.loads(r.read().decode()).get("data") or {}).get("hidden_units")
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget", type=float, default=900.0, help="seconds to watch")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res = {"canopy": CANOPY, "cascor": CASCOR, "events": [], "server_growth": [], "dom_growth": []}
    seen = {"buffer_writes": 0, "rebuild_writes": 0, "responses": 0}

    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, [])
        try:
            open_tab(page, "Network Topology")
            page.wait_for_timeout(4000)

            start_hidden = _server_hidden()
            res["start_hidden"] = start_hidden
            res["start_dom"] = counts(page)
            b0 = _store(page, BUFFER) or {}
            res["start_buffer"] = {"ok": b0.get("ok"), "via": b0.get("via"), "value": b0.get("value")}
            log(f"  start: server hidden={start_hidden} dom={res['start_dom']} buffer={res['start_buffer']}")

            def on_response(resp):
                if "_dash-update-component" not in resp.url:
                    return
                seen["responses"] += 1
                try:
                    body = resp.text()
                except Exception:  # noqa: BLE001
                    return
                t = round(time.time() - t0, 1)
                # NOTE: this can only ever count SERVER-side responses naming the
                # store. ``ws-cascade-add-buffer`` is written by a CLIENTSIDE
                # callback (dashboard_manager.py:3652), which executes in the browser
                # and produces no ``/_dash-update-component`` response at all. So a
                # zero here is structurally uninformative -- the mirror image of
                # browser-counting a server-side fetch. The store's VALUE, polled
                # below, is the only admissible evidence about this trigger.
                if BUFFER in body:
                    seen["buffer_writes"] += 1
                    res["events"].append({"t": t, "what": f"{BUFFER} named in a response"})
                    log(f"  [t={t}] {BUFFER} named in a callback response  (#{seen['buffer_writes']})")
                if f'"{REBUILD}"' in body and "figure" in body:
                    seen["rebuild_writes"] += 1
                    res["events"].append({"t": t, "what": "rebuild wrote a figure"})
                    log(f"  [t={t}] rebuild wrote {REBUILD}.figure  (#{seen['rebuild_writes']})")

            page.on("response", on_response)

            t0 = time.time()
            last_server, last_dom, last_gen = start_hidden, None, None
            while time.time() - t0 < args.budget:
                page.wait_for_timeout(5000)
                t = round(time.time() - t0, 1)
                sh = _server_hidden()
                if sh is not None and sh != last_server:
                    res["server_growth"].append({"t": t, "hidden": sh})
                    log(f"  [t={t}] *** SERVER GREW: hidden {last_server} -> {sh} ***")
                    last_server = sh
                dom = counts(page).get("hidden")
                if dom != last_dom:
                    res["dom_growth"].append({"t": t, "hidden": dom})
                    log(f"  [t={t}] DOM hidden-count now {dom!r}")
                    last_dom = dom

                # The admissible read of the growth trigger: the clientside drain
                # bumps ``gen`` every time it actually drained cascade_add events.
                # gen > 0 means the WS trigger fired in THIS page session.
                br = _store(page, BUFFER) or {}
                if br.get("ok") and isinstance(br.get("value"), dict):
                    gen = br["value"].get("gen")
                    nev = len(br["value"].get("events") or [])
                    if gen != last_gen:
                        res.setdefault("buffer_gen", []).append({"t": t, "gen": gen, "events": nev})
                        log(f"  [t={t}] *** {BUFFER} gen {last_gen} -> {gen} (events={nev}) ***")
                        last_gen = gen
                elif not br.get("ok"):
                    res.setdefault("buffer_unreadable", []).append({"t": t, "via": br.get("via")})

            res["counters"] = seen
            res["end_hidden"] = _server_hidden()
            res["end_dom"] = counts(page)
            log(f"  end: server hidden={res['end_hidden']} dom={res['end_dom']} counters={seen}")
        finally:
            browser.close()

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
