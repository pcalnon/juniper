#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""M-CANDIDATES-07 / F-CANOPY-035 — is the candidate loss plot still empty?

WHY THIS EXISTS SEPARATELY FROM `e2e_p1wave_redrive.py --step f035`.

F-CANOPY-035's fix merged as canopy#524 on 2026-08-26 and its live re-drive has been
owed ever since, blocked twice over:

1. the shared ``metrics-panel-metrics-store`` was measured **empty on the client**
   while the server offered 155,392 B every tick (server-side probe inside
   ``_update_metrics_store_handler``, 79 samples, 2026-08-29) — the F-CANOPY-039
   family;
2. the client-side ``storeprobe`` used for the first attempt was later ruled
   **inadmissible** — it read ``None`` for *every* store on this app, including one
   whose heatmap was visibly rendering, and reported that as "empty".

Both blockers have moved. F-CANOPY-039 is FIXED, and the store reader was repaired
to go through Dash's id→path index at ``state.paths.strs``
(``2026-09-03_store_read_probe.py``). So this re-drive uses the FIXED reader,
imported from the seg17 driver rather than re-implemented, and it **refuses to score
an unreadable store as an empty one** — that conflation is the exact mistake that
produced a confident FAIL against a working gate on M-TOPOLOGY-18.

WHAT IT SEPARATES. Four outcomes, not two:

  BLOCKED(server)   /api/metrics/history has no candidate-phase entries — the
                    fixture cannot exercise the row, and nothing about the client
                    is being tested.
  BLOCKED(reader)   the store could not be READ. Not "empty". Say so and stop.
  FAIL              store readable and empty, or readable-and-populated but no
                    `Candidate Training` trace — a real product defect.
  PASS              the trace renders with points.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-04_f035_candidate_loss_redrive.py
"""

import importlib.util
import json
import os
import sys
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
fig_info = _seg17.fig_info
wait_for = _seg17.wait_for
http_get = _seg17.http_get
_store = _seg17._store

METRICS_STORE = "metrics-panel-metrics-store"
LOSS_FIG = "candidate-metrics-panel-loss-plot"
OUT = os.environ.get("F035_RESULTS", "/tmp/juniper-e2e/f035_redrive.json")


def _candidate_history():
    """Server truth: does the history canopy serves carry candidate-phase rows?"""
    try:
        status, payload = http_get("/api/metrics/history")
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        return {"ok": False, "why": f"{type(exc).__name__}: {exc}"}
    if status != 200:
        return {"ok": False, "why": f"HTTP {status}"}
    rows = payload.get("data") if isinstance(payload, dict) and "data" in payload else payload
    if isinstance(rows, dict):
        rows = rows.get("history") or rows.get("metrics") or []
    if not isinstance(rows, list):
        return {"ok": False, "why": f"unexpected shape {type(rows).__name__}"}
    tally: dict = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        p = r.get("phase") or r.get("cascade_phase") or "?"
        tally[p] = tally.get(p, 0) + 1
    return {"ok": True, "total": len(rows), "phases": tally, "candidate": tally.get("candidate", 0)}


def _loss_traces(page):
    """The candidate loss figure's traces, by name, with point counts."""
    info = fig_info(page, LOSS_FIG) or {}
    out = []
    for t in info.get("traces") or []:
        # fig_info reports x/z lengths as ``nx``/``nz`` -- there is no ``n``.
        # Reading a key the producer never emits is the F-CANOPY-035 defect
        # itself; do not reproduce it in the instrument that measures it.
        out.append({"name": t.get("name"), "n": t.get("nx") or t.get("nz") or 0, "type": t.get("type")})
    return {"present": bool(info), "traces": out, "annotations": info.get("annotations")}


def _wire_census(page, seconds: float = 25.0):
    """Count Dash callback responses that WRITE the metrics store.

    NOT browser requests to ``/api/metrics/history``: canopy fetches that
    SERVER-SIDE from inside ``_update_metrics_store_handler``, so it never crosses
    the browser and a count of it is structurally zero in every condition. That is
    the exact instrument error that produced a confident FAIL on M-TOPOLOGY-18 --
    "browser-counting a SERVER-side fetch". The browser-visible artefact is the
    ``/_dash-update-component`` response whose output names the store.
    """
    # NOTE THE KEY NAME. This counts responses whose body MENTIONS the store, which
    # is not the same as writes: a ``no_update`` for that output can still name it.
    # So a non-zero count establishes only that the callback is producing responses
    # about this store -- i.e. that it is not starved or silent. It does NOT
    # establish that a value landed. Calling it ``store_writes`` would be a third
    # instrument in this arc answering an adjacent question in confident numbers.
    hits = {"responses_naming_store": 0, "responses": 0}

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        hits["responses"] += 1
        try:
            body = resp.text()
        except Exception:  # noqa: BLE001 - a body we cannot read is not a hit
            return
        if METRICS_STORE in body:
            hits["responses_naming_store"] += 1

    page.on("response", on_response)
    page.wait_for_timeout(int(seconds * 1000))
    # DETACH, then return a COPY. Leaving the handler attached and returning the
    # live dict made this census report its whole listening lifetime rather than
    # its window: the log printed 15/80 at t=61 s and the JSON dumped 62/296 at
    # t=139 s, from the SAME run. A census that does not stop counting when its
    # window closes is not a census. The window is now closed twice over.
    page.remove_listener("response", on_response)
    hits["window_s"] = seconds
    return dict(hits)


def _write_census(page, seconds: float = 30.0):
    """Classify what the callback WRITES to the metrics store, not that it spoke.

    The count in ``_wire_census`` is responses whose body *mentions* the store, and a
    ``no_update`` for that output can still name it. That distinction is the whole
    question here: "the callback is running" and "a value is landing" are different
    claims, and only the second explains an empty store.

    Dash's ``/_dash-update-component`` response carries ``{"response": {"<id>":
    {"<prop>": <value>}}}`` and OMITS outputs the handler no_update'd. So parsing the
    body separates three outcomes that the mention-count conflates:

      wrote_n      the store id is present with a ``data`` list -> that many rows landed
      omitted      a response naming the store elsewhere, but no value for it
      unparsed     body unavailable or not JSON (reported, never silently dropped)
    """
    out = {"responses": 0, "wrote": [], "omitted": 0, "unparsed": 0}

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        out["responses"] += 1
        try:
            body = resp.text()
        except Exception:  # noqa: BLE001
            out["unparsed"] += 1
            return
        if METRICS_STORE not in body:
            return
        try:
            payload = json.loads(body)
        except ValueError:
            out["unparsed"] += 1
            return
        resp_map = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(resp_map, dict) or METRICS_STORE not in resp_map:
            out["omitted"] += 1
            return
        val = (resp_map.get(METRICS_STORE) or {}).get("data")
        out["wrote"].append(len(val) if isinstance(val, list) else f"<{type(val).__name__}>")

    page.on("response", on_response)
    page.wait_for_timeout(int(seconds * 1000))
    page.remove_listener("response", on_response)  # see _wire_census: same leak, same fix
    out["window_s"] = seconds
    return {**out, "wrote": list(out["wrote"])}


def main() -> int:
    from playwright.sync_api import sync_playwright

    res: dict = {"canopy": CANOPY}

    server = _candidate_history()
    res["server_history"] = server
    log(f"  server /api/metrics/history: {server}")
    if not server.get("ok"):
        res["M-CANDIDATES-07"] = {"verdict": "BLOCKED", "reason": f"history unreadable: {server.get('why')}"}
        log("  M-CANDIDATES-07 -> BLOCKED (server history unreadable)")
    elif server.get("candidate", 0) == 0:
        res["M-CANDIDATES-07"] = {
            "verdict": "BLOCKED",
            "reason": "no candidate-phase entries on this fixture — the row cannot be exercised",
            "phases": server.get("phases"),
        }
        log("  M-CANDIDATES-07 -> BLOCKED (fixture has no candidate-phase history)")

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            open_tab(page, "Candidate Metrics")
            page.wait_for_timeout(4000)

            # The store, through the FIXED reader. Unreadable is NOT empty.
            read = _store(page, METRICS_STORE) or {}
            res["store_read"] = {"ok": read.get("ok"), "via": read.get("via")}
            val = read.get("value")
            if read.get("ok"):
                n = len(val) if isinstance(val, list) else None
                res["store_read"]["len"] = n
                res["store_read"]["type"] = type(val).__name__
                log(f"  {METRICS_STORE}: ok via {read.get('via')!r} type={type(val).__name__} len={n}")
            else:
                log(f"  {METRICS_STORE}: UNREADABLE via {read.get('via')!r} — NOT scored as empty")

            # WHICH of the three candidate mechanisms is it? Read the gate's own
            # input and count the writes, rather than reasoning from the source.
            live = _store(page, "ws-liveness-store") or {}
            res["ws_liveness"] = {"ok": live.get("ok"), "via": live.get("via"), "value": live.get("value")}
            log(f"  ws-liveness-store: ok={live.get('ok')} value={live.get('value')!r}")

            # DISCRIMINATE BY WRITER. ``metrics-panel-metrics-store`` has TWO writers:
            # the liveness-gated REST poll (``update_metrics_store``) and an UNGUARDED
            # ``allow_duplicate`` appender (``append_ws_metrics_store``,
            # dashboard_manager.py:3910). The topoprobe instrument's report demands this
            # discrimination before its verdict is read. The appender fires ONLY on a
            # ``ws-metrics-buffer`` change, and that store is written by a CLIENTSIDE
            # callback -- so a response census cannot see it and its VALUE is the only
            # admissible evidence. ``gen`` is bumped by the drain on every real drain,
            # so gen==0 throughout means the appender never fired in this page session.
            wsb = _store(page, "ws-metrics-buffer") or {}
            res["ws_metrics_buffer_before"] = {"ok": wsb.get("ok"), "via": wsb.get("via"), "value": wsb.get("value")}
            log(f"  ws-metrics-buffer BEFORE: ok={wsb.get('ok')} value={wsb.get('value')!r}")

            census = _wire_census(page, seconds=25.0)
            res["wire_census_25s"] = census
            log(f"  wire census (25 s): {census}")

            writes = _write_census(page, seconds=30.0)
            res["write_census_30s"] = writes
            log(f"  WRITE census (30 s): responses={writes['responses']} wrote={writes['wrote']} "
                f"omitted={writes['omitted']} unparsed={writes['unparsed']}")

            # RE-READ THE STORE AFTER THE WRITES. The read above happens ~25 s in,
            # BEFORE the census window -- so on its own it cannot distinguish "the
            # store never populates" from "it had not populated yet". Reading once,
            # early, and calling the result final is exactly the ordering artifact
            # M-TOPOLOGY-18 produces. Two reads bracketing the writes settle it.
            after = _store(page, METRICS_STORE) or {}
            res["store_read_after_writes"] = {
                "ok": after.get("ok"),
                "via": after.get("via"),
                "len": len(after["value"]) if isinstance(after.get("value"), list) else None,
                "type": type(after.get("value")).__name__,
            }
            log(f"  {METRICS_STORE} AFTER {len(writes['wrote'])} writes: {res['store_read_after_writes']}")

            wsb2 = _store(page, "ws-metrics-buffer") or {}
            res["ws_metrics_buffer_after"] = {"ok": wsb2.get("ok"), "via": wsb2.get("via"), "value": wsb2.get("value")}
            _b = (res.get("ws_metrics_buffer_before") or {}).get("value")
            g0 = _b.get("gen") if isinstance(_b, dict) else None
            _a = wsb2.get("value")
            g1 = _a.get("gen") if isinstance(_a, dict) else None
            res["ws_appender_fired"] = None if (g0 is None or g1 is None) else bool(g1 != g0 or (g1 or 0) > 0)
            log(f"  ws-metrics-buffer AFTER: gen {g0} -> {g1}  => ws appender fired: {res['ws_appender_fired']}")

            # Give the plot the same effect budget the panel's other consumers get.
            wait_for(
                lambda: any((t.get("n") or 0) > 0 for t in (_loss_traces(page).get("traces") or [])),
                budget_s=45,
                every_s=2.0,
                label="candidate loss plot to render a populated trace",
            )
            fig = _loss_traces(page)
            res["loss_figure"] = fig
            log(f"  loss figure: {fig}")

            if "M-CANDIDATES-07" not in res:
                named = [t for t in fig.get("traces") or [] if (t.get("name") or "").strip().lower().startswith("candidate")]
                populated = [t for t in named if (t.get("n") or 0) > 0]
                if not read.get("ok"):
                    verdict, why = "BLOCKED", "the metrics store could not be read; 'empty' is not established"
                elif populated:
                    verdict, why = "PASS", f"{populated[0]['name']!r} rendered {populated[0]['n']} points"
                elif isinstance(val, list) and not val:
                    verdict, why = "FAIL", "store readable and EMPTY while the server serves candidate history"
                else:
                    verdict, why = "FAIL", "store populated but no candidate trace rendered"
                res["M-CANDIDATES-07"] = {"verdict": verdict, "reason": why, "named_traces": named}
                log(f"  M-CANDIDATES-07 -> {verdict}: {why}")
        finally:
            browser.close()

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
