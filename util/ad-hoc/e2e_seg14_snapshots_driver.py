#!/usr/bin/env python3
"""Segment-14 driver: §3.9 the Snapshots tab.

Project:     Juniper
Sub-Project: juniper-ml
Application: Canopy E2E validation arc -- Phase 1 segment 14
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Why this exists
---------------
Browser-MCP availability has been intermittent across the arc, so driving falls
back to a script (segment-8 convention). Run with the only interpreter that has
playwright, and with ``LD_LIBRARY_PATH`` cleared -- invoking the env python
directly bypasses the conda hooks that strip it, and an ambient rust_mudgeon
libtorch then breaks module IMPORT with
``undefined symbol: _PyObject_NextNotImplemented``, which reads exactly like a
test failure and is not one::

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/e2e_seg14_snapshots_driver.py --step tab --step view_detail

Two OPEN findings bound the timing of every step here, so the sampling is built
around them rather than fighting them:

* **F-CANOPY-009** -- the detail panel fills correctly then is WIPED ~7 s later
  by the panel's own 10 s refresh. Detail assertions must sample fast and record
  the wipe rather than treat it as a failure to render.
* **F-CANOPY-010** -- the shared op-confirm modal self-closes ~3.6 s after
  opening. Modal-body assertions must land inside that window; polling once at
  5 s reads as "never opened".

Shared helpers come from ``e2e_w3_params_driver.py`` (browser/log) via the
segment-13 driver, which already resolves them by path.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_s13 = _load("_s13drv", "e2e_seg13_modals_driver.py")

log = _w3.log
http_get = _w3.http_get
log_size = _w3.log_size
log_since = _w3.log_since
open_dashboard = _w3.open_dashboard
text_of = _w3.text_of
is_disabled = _w3.is_disabled

probe = _s13.probe
probe_many = _s13.probe_many
_click = _s13._click
_wait_present = _s13._wait_present

PANEL = "hdf5-snapshots-panel-"


def goto_snapshots_tab(page, timeout_ms: int = 45000):
    """Activate the Snapshots tab and WAIT FOR ITS TABLE, not a fixed delay.

    Panels are hidden, not unmounted, so counters must be read with the tab
    active. Page-load time on this host varies by 5x under load (2.3 s to
    11.7 s observed), and a fixed settle silently yields an empty surface that
    reads exactly like 'no snapshots' -- poll for the rows instead.
    """
    ok = page.evaluate(
        """() => {
             const t = [...document.querySelectorAll('[role=tab], .nav-link, a')]
                        .find(e => (e.textContent || '').trim() === 'Snapshots');
             if (!t) return false; t.click(); return true;
           }"""
    )
    waited = 0
    while waited < timeout_ms:
        page.wait_for_timeout(1000)
        waited += 1000
        if view_button_ids(page):
            return {"clicked": ok, "rows_at_ms": waited}
    return {"clicked": ok, "rows_at_ms": None}


def op_button_ids(page):
    """Pattern-matched op buttons; ids are JSON with keys sorted index/op/type."""
    return page.evaluate(
        """() => [...document.querySelectorAll('button[id]')]
                  .filter(b => b.id.includes('hdf5-snapshots-panel-snapshot-op-btn'))
                  .map(b => ({id: b.id, text: (b.textContent||'').trim().slice(0,40), disabled: b.disabled}))"""
    )


def view_button_ids(page):
    return page.evaluate(
        """() => [...document.querySelectorAll('button[id]')]
                  .filter(b => b.id.includes('hdf5-snapshots-panel-view-btn'))
                  .map(b => ({id: b.id, text: (b.textContent||'').trim().slice(0,40)}))"""
    )


def click_by_id_js(page, el_id):
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); if (!el) return false; el.click(); return true; }""",
        el_id,
    )


def step_tab(page, ctx):
    """Survey the Snapshots panel with its own tab active (M-SNAPSHOTS-04..06)."""
    out = {"tab_clicked": goto_snapshots_tab(page)}
    ids = [
        PANEL + "create-name",
        PANEL + "create-button",
        PANEL + "refresh-button",
        PANEL + "table-body",
        PANEL + "status",
        PANEL + "empty-state",
        PANEL + "detail-panel",
        PANEL + "history-toggle",
        PANEL + "history-collapse",
        PANEL + "history-content",
        PANEL + "dataset-swaps-content",
        PANEL + "restore-modal-body",
        PANEL + "restore-cancel",
        PANEL + "restore-confirm",
        PANEL + "restore-status",
    ]
    out["surface"] = probe_many(page, ids)
    out["op_buttons"] = op_button_ids(page)
    out["view_buttons"] = view_button_ids(page)
    out["api_snapshots"] = http_get("/api/v1/snapshots")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_refresh(page, ctx):
    """M-SNAPSHOTS-04 (manual refresh) and -05 (the 10 s auto interval)."""
    goto_snapshots_tab(page)
    seen = []

    def on_request(req):
        if "/api/v1/snapshots" in req.url and req.method == "GET":
            seen.append({"t": len(seen), "url": req.url.split("/dashboard")[-1][:80]})

    page.on("request", on_request)
    out = {}
    # baseline: how many list GETs happen with NO interaction over ~25 s?
    before = len(seen)
    page.wait_for_timeout(25000)
    out["auto_gets_in_25s"] = len(seen) - before
    # now the manual refresh
    mark = len(seen)
    out["refresh_clicked"] = _click(page, PANEL + "refresh-button")
    page.wait_for_timeout(4000)
    out["gets_after_refresh_click"] = len(seen) - mark
    out["table_text"] = (probe(page, PANEL + "table-body").get("text") or "")[:200]
    out["status_text"] = text_of(page, PANEL + "status")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_view_detail(page, ctx):
    """M-SNAPSHOTS-07 (View writes selected-id) and -08 (detail render).

    F-CANOPY-009: the detail panel is wiped ~7 s later by the panel's own 10 s
    refresh, so sample fast and RECORD the wipe instead of reading it as a
    failure to render.
    """
    goto_snapshots_tab(page)
    out = {"views": view_button_ids(page)}
    if not out["views"]:
        print(json.dumps(out, indent=1, sort_keys=True))
        return out
    target = out["views"][0]["id"]
    out["target"] = target
    out["detail_before"] = probe(page, PANEL + "detail-panel").get("text")
    off = log_size()
    # Use a TRUSTED click and tolerate the documented ack timeout. A JS click
    # also reaches Dash here (proved on the wire), but F-CANOPY-009 means the
    # store is CLEARED and re-set around the click, so the trusted path gives a
    # cleaner fill to time the wipe against.
    sel = "[id='" + target.replace("'", "\\'") + "']"
    try:
        page.click(sel, timeout=4000)
        out["clicked"] = "trusted"
    except Exception:  # noqa: BLE001
        out["clicked"] = "trusted(ack-timeout, expected)"
    EMPTY = "Select a snapshot"
    samples = []
    for i in range(60):
        page.wait_for_timeout(500)
        p = probe(page, PANEL + "detail-panel")
        t = (p.get("text") or "")[:110]
        samples.append({"t_ms": (i + 1) * 500, "h": p.get("h"), "filled": bool(t) and EMPTY not in t, "text": t})
    out["samples"] = samples
    filled = [s for s in samples if s["filled"]]
    out["first_filled_ms"] = filled[0]["t_ms"] if filled else None
    out["last_filled_ms"] = filled[-1]["t_ms"] if filled else None
    wiped = None
    if filled:
        for s in samples:
            if s["t_ms"] > filled[0]["t_ms"] and not s["filled"]:
                wiped = s["t_ms"]
                break
    out["wiped_at_ms"] = wiped
    out["survived_ms"] = (wiped - filled[0]["t_ms"]) if (wiped and filled) else None
    out["server_log"] = log_since(off, ("snapshots",))[:6]
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_ops_modal(page, ctx):
    """M-SNAPSHOTS-09..14: each op opens the shared confirm modal.

    F-CANOPY-010: the modal self-closes ~3.6 s after opening, so each op is
    sampled every 400 ms from the click and the body captured on first sight.
    """
    goto_snapshots_tab(page)
    ops = op_button_ids(page)
    out = {"op_buttons_found": len(ops)}
    by_op = {}
    for b in ops:
        for name in ("restore", "replay", "resume", "retrain"):
            if f'"op":"{name}"' in b["id"] and name not in by_op:
                by_op[name] = b["id"]
    out["op_ids"] = by_op
    def try_open(name, attempt):
        """Re-query the id immediately before clicking.

        The table rebuilds every 10 s (the same refresh behind F-CANOPY-009),
        so an id captured earlier can name a detached node by click time --
        which presents as 'the modal never opened'.
        """
        fresh = op_button_ids(page)
        el_id = next((b["id"] for b in fresh if f'"op":"{name}"' in b["id"]), None)
        if not el_id:
            return {"op": name, "attempt": attempt, "verdict": "NO-BUTTON"}
        click_by_id_js(page, el_id)
        body_seen, opened_at, closed_at = None, None, None
        for i in range(24):
            page.wait_for_timeout(300)
            p = probe(page, PANEL + "restore-modal-body")
            if p.get("present") and (p.get("text") or "").strip():
                if opened_at is None:
                    opened_at = (i + 1) * 300
                    body_seen = (p.get("text") or "")[:600]
            elif opened_at is not None and closed_at is None:
                closed_at = (i + 1) * 300
                break
        return {
            "op": name,
            "attempt": attempt,
            "opened_at_ms": opened_at,
            "closed_at_ms": closed_at,
            "visible_ms": (closed_at - opened_at) if (opened_at and closed_at) else None,
            "body": body_seen,
        }

    results = []
    for name in ("restore", "replay", "resume", "retrain"):
        r = try_open(name, 1)
        if r.get("opened_at_ms") is None:
            page.wait_for_timeout(3000)
            r = try_open(name, 2)
        results.append(r)
        page.wait_for_timeout(2500)
    out["ops"] = results
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_cancel(page, ctx):
    """M-SNAPSHOTS-14: Cancel closes the modal and issues NO request."""
    goto_snapshots_tab(page)
    ops = op_button_ids(page)
    target = next((b["id"] for b in ops if '"op":"restore"' in b["id"]), None)
    out = {"target": target}
    if not target:
        print(json.dumps(out, indent=1, sort_keys=True))
        return out
    posts = []

    def on_request(req):
        if req.method == "POST" and "/api/v1/snapshots" in req.url:
            posts.append(req.url[:120])

    page.on("request", on_request)
    # F-CANOPY-010 makes the open racy (its early-out returns (False, "", None)),
    # so retry with a fresh id rather than scoring the race as a failure.
    opened, attempts = None, 0
    for attempt in range(4):
        attempts = attempt + 1
        fresh = op_button_ids(page)
        target = next((b["id"] for b in fresh if '"op":"restore"' in b["id"]), target)
        click_by_id_js(page, target)
        for i in range(12):
            page.wait_for_timeout(250)
            if probe(page, PANEL + "restore-modal-body").get("present"):
                opened = (i + 1) * 250
                break
        if opened:
            break
        page.wait_for_timeout(2500)
    out["attempts"] = attempts
    out["opened_at_ms"] = opened
    out["cancel_clicked"] = _click(page, PANEL + "restore-cancel")
    closed = None
    for i in range(14):
        page.wait_for_timeout(300)
        if not probe(page, PANEL + "restore-modal-body").get("present"):
            closed = (i + 1) * 300
            break
    out["closed_at_ms"] = closed
    page.wait_for_timeout(2000)
    out["posts_seen"] = posts
    out["restore_status"] = text_of(page, PANEL + "restore-status")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_dead(page, ctx):
    """M-SNAPSHOTS-20/21 are DEAD-EXPECTED -- clicking must do NOTHING.

    The passing terminal value is DEAD-CONFIRMED (matrix §1.1), which requires
    all three of: no request, no DOM change, no console error.
    """
    goto_snapshots_tab(page)
    reqs, errors = [], []
    page.on("request", lambda r: reqs.append(r.url[:100]))
    page.on("console", lambda m: errors.append(m.text[:160]) if m.type == "error" else None)
    out = {}
    found = page.evaluate(
        """() => [...document.querySelectorAll('button[id]')]
                  .filter(b => b.id.includes('swap-restore-pre-btn') || b.id.includes('swap-restore-post-btn'))
                  .map(b => b.id)"""
    )
    out["dead_buttons_found"] = found
    if not found:
        out["note"] = "no swap-restore pre/post buttons rendered (they live in dataset-swap cards)"
        print(json.dumps(out, indent=1, sort_keys=True))
        return out
    for el_id in found[:2]:
        dom_before = page.evaluate("""() => document.body.innerHTML.length""")
        n_before = len(reqs)
        click_by_id_js(page, el_id)
        page.wait_for_timeout(4000)
        out[el_id] = {
            "requests_after_click": len(reqs) - n_before,
            "dom_len_delta": page.evaluate("""() => document.body.innerHTML.length""") - dom_before,
            "console_errors": len(errors),
        }
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_history(page, ctx):
    """M-SNAPSHOTS-17 (history toggle + GET) and -18 (dataset-swaps content)."""
    goto_snapshots_tab(page)
    hits = []
    page.on("request", lambda r: hits.append(r.url[-70:]) if "snapshots/history" in r.url else None)
    out = {"collapse_before": probe(page, PANEL + "history-collapse")}
    # The 10 s table rebuild makes every click here racy (same root as
    # F-CANOPY-009/010), so retry rather than score a race as a failure.
    opened, attempts = None, 0
    for attempt in range(4):
        attempts = attempt + 1
        out[f"clicked_{attempts}"] = _click(page, PANEL + "history-toggle")
        for i in range(12):
            page.wait_for_timeout(600)
            if probe(page, PANEL + "history-collapse").get("shown"):
                opened = (i + 1) * 600
                break
        if opened:
            break
        page.wait_for_timeout(2000)
    out["attempts"] = attempts
    out["collapse_opened_at_ms"] = opened
    # content can lag the collapse; poll for it to stop saying "Loading"
    for _ in range(20):
        page.wait_for_timeout(700)
        t = full_text(page, PANEL + "history-content") or ""
        if t and "Loading history" not in t:
            break
    out["history_requests"] = hits[:4]
    out["history_content"] = (full_text(page, PANEL + "history-content") or "")[:400]
    out["dataset_swaps_content"] = (full_text(page, PANEL + "dataset-swaps-content") or "")[:300]
    out["api_history"] = http_get("/api/v1/snapshots/history")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_view_wire(page, ctx):
    """Did the View click reach Dash at all? Read it off the wire.

    A component id in a REQUEST proves nothing (a many-Input callback names all
    of them); only the carried VALUE in the RESPONSE is evidence. This captures
    both directions so 'my click was inert' and 'the callback ran and returned
    nothing' are distinguishable -- the same discriminator that settled
    F-CANOPY-025.
    """
    goto_snapshots_tab(page)
    reqs, resps = [], []

    def on_request(req):
        if "_dash-update-component" in req.url:
            try:
                b = req.post_data or ""
            except Exception:  # noqa: BLE001
                b = ""
            if "view-btn" in b or "selected-id" in b:
                reqs.append(b[:400])

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        try:
            txt = json.dumps(resp.json())
        except Exception:  # noqa: BLE001
            return
        if "selected-id" in txt or "detail-panel" in txt:
            resps.append(txt[:400])

    page.on("request", on_request)
    page.on("response", on_response)

    views = view_button_ids(page)
    out = {"views": len(views)}
    if not views:
        print(json.dumps(out, indent=1, sort_keys=True))
        return out
    target = views[0]["id"]
    out["target"] = target
    # n_clicks BEFORE (Dash tracks it on the component, not the DOM, but the
    # DOM node carries no counter -- so record what we can and rely on the wire)
    out["clicked"] = click_by_id_js(page, target)
    page.wait_for_timeout(8000)
    out["req_count"] = len(reqs)
    out["reqs"] = reqs[:2]
    out["resp_count"] = len(resps)
    out["resps"] = resps[:3]
    out["detail_text"] = (probe(page, PANEL + "detail-panel").get("text") or "")[:160]
    # also try a TRUSTED click, tolerating the documented ack timeout
    sel = "[id='" + target.replace("'", "\\'") + "']"
    try:
        page.click(sel, timeout=4000)
        out["trusted"] = "ok"
    except Exception as e:  # noqa: BLE001
        out["trusted"] = f"ack-timeout(expected): {str(e)[:60]}"
    page.wait_for_timeout(6000)
    out["resp_count_after_trusted"] = len(resps)
    out["detail_after_trusted"] = (probe(page, PANEL + "detail-panel").get("text") or "")[:160]
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def _confirm_op(page, op):
    """Open an op modal and hit Confirm INSIDE the F-CANOPY-010 window.

    The modal self-closes ~3.6 s after opening and discards the pending op id,
    so Confirm has to be clicked the moment the body appears -- polling at 300 ms
    and acting on first sight, not waiting for a settle.
    """
    posts = []

    def on_request(req):
        if req.method == "POST" and "/api/v1/snapshots" in req.url:
            posts.append(req.url.split("/api")[-1][:100])

    page.on("request", on_request)
    opened_at, confirmed_at, attempts = None, None, 0
    for attempt in range(4):
        attempts = attempt + 1
        # Re-query every attempt: the 10 s rebuild detaches nodes, and
        # F-CANOPY-010's early-out returns (False, "", None) at random.
        fresh = op_button_ids(page)
        el_id = next((b["id"] for b in fresh if f'"op":"{op}"' in b["id"]), None)
        if not el_id:
            return {"op": op, "verdict": "NO-BUTTON", "attempts": attempts}
        click_by_id_js(page, el_id)
        for i in range(16):
            page.wait_for_timeout(250)
            p = probe(page, PANEL + "restore-modal-body")
            if p.get("present") and (p.get("text") or "").strip():
                opened_at = (i + 1) * 250
                _click(page, PANEL + "restore-confirm")
                confirmed_at = opened_at
                break
        if opened_at:
            break
        page.wait_for_timeout(2500)
    status = None
    for _ in range(20):
        page.wait_for_timeout(600)
        status = text_of(page, PANEL + "restore-status")
        if status:
            break
    return {
        "op": op,
        "attempts": attempts,
        "opened_at_ms": opened_at,
        "confirm_clicked_at_ms": confirmed_at,
        "posts": posts[:4],
        "restore_status": (status or "")[:220],
        "active_tab": page.evaluate(
            """() => { const a = document.querySelector('[role=tab][aria-selected=true], .nav-link.active');
                       return a ? (a.textContent||'').trim().slice(0,40) : null; }"""
        ),
    }


def step_confirm_restore(page, ctx):
    """M-SNAPSHOTS-15 -- Confirm issues POST /api/v1/snapshots/{id}/{op}."""
    goto_snapshots_tab(page)
    out = {"fsm_before": (http_get("/api/status")[1] or {}).get("fsm_status")}
    out["result"] = _confirm_op(page, "restore")
    out["fsm_after"] = (http_get("/api/status")[1] or {}).get("fsm_status")
    out["network_after"] = http_get("/v1/health")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_confirm_replay(page, ctx):
    """M-SNAPSHOTS-16 -- a confirmed replay also switches active_tab to Replay."""
    goto_snapshots_tab(page)
    out = {"tab_before": page.evaluate("""() => { const a = document.querySelector('[role=tab][aria-selected=true], .nav-link.active'); return a ? (a.textContent||'').trim().slice(0,40) : null; }""")}
    out["result"] = _confirm_op(page, "replay")
    page.wait_for_timeout(6000)
    out["tab_after"] = page.evaluate("""() => { const a = document.querySelector('[role=tab][aria-selected=true], .nav-link.active'); return a ? (a.textContent||'').trim().slice(0,40) : null; }""")
    out["replay_panel_present"] = probe(page, "replay-player-panel").get("present")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def full_text(page, el_id):
    """Untruncated textContent -- probe() slices to 120 chars for readability."""
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); return el ? (el.textContent || '').trim() : null; }""",
        el_id,
    )


def step_refresh_quiet(page, ctx):
    """M-SNAPSHOTS-04 / -05 measured on the SERVER log, not browser requests.

    The panel's list fetch is issued SERVER-side from the Dash callback, so zero
    browser GETs is EXPECTED (the arc's standing rule) -- browser-side request
    counting reads as 'never refreshes' and is the wrong instrument. Instead:
    sit idle on the tab and read the canopy log's own
    'Fetching snapshots from API' lines, which is the interval's real footprint.
    Idle matters: any interaction triggers its own re-list and poisons the gaps
    (a first attempt measured a 0.33 s to 92 s spread purely from my own clicks).
    """
    goto_snapshots_tab(page)
    out = {}
    off = log_size()
    page.wait_for_timeout(60000)  # strictly idle
    idle_lines = log_since(off, ("Fetching snapshots from API",))
    out["idle_window_s"] = 60
    out["idle_fetches"] = len(idle_lines)
    out["idle_samples"] = idle_lines[:12]
    # The manual button, measured as a RATE against the idle baseline. A single
    # 3 s window after one click is too tight to separate signal from the
    # interval's own jitter (idle gaps ranged 4-29 s), so drive several clicks
    # inside a fixed window and compare fetch counts.
    idle_rate_per_20s = out["idle_fetches"] * 20.0 / 60.0
    off2 = log_size()
    clicks = 0
    for _ in range(4):
        if _click(page, PANEL + "refresh-button"):
            clicks += 1
        page.wait_for_timeout(5000)
    driven = log_since(off2, ("Fetching snapshots from API",))
    out["clicks_issued"] = clicks
    out["driven_window_s"] = 20
    out["fetches_in_driven_window"] = len(driven)
    out["idle_rate_per_20s"] = round(idle_rate_per_20s, 2)
    out["exceeds_idle_baseline"] = len(driven) > idle_rate_per_20s
    out["click_samples"] = driven[:6]
    out["status_text"] = text_of(page, PANEL + "status")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_restore_diag(page, ctx):
    """Why does the RESTORE op modal not open when its 3 siblings do?

    Also captures the modal body UNTRUNCATED, which M-SNAPSHOTS-13 needs (the
    row asserts a ⚠️ 'Training must be paused or stopped' line that probe()'s
    120-char slice was cutting off).
    """
    goto_snapshots_tab(page)
    resps = []

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        try:
            txt = json.dumps(resp.json())
        except Exception:  # noqa: BLE001
            return
        if "restore-modal" in txt or "pending-op" in txt or "restore-status" in txt:
            resps.append(txt[:300])

    page.on("response", on_response)
    out = {}
    for op in ("resume", "restore"):
        fresh = op_button_ids(page)
        el_id = next((b["id"] for b in fresh if f'"op":"{op}"' in b["id"]), None)
        mark = len(resps)
        click_by_id_js(page, el_id)
        body, opened = None, None
        for i in range(20):
            page.wait_for_timeout(250)
            t = full_text(page, PANEL + "restore-modal-body")
            if t:
                opened = (i + 1) * 250
                body = t
                break
        out[op] = {
            "button_found": bool(el_id),
            "opened_at_ms": opened,
            "body_len": len(body or ""),
            "body": body,
            "has_warning": bool(body and "paused or stopped" in body),
            "responses": resps[mark : mark + 3],
        }
        page.wait_for_timeout(5000)
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


STEPS = {
    "tab": step_tab,
    "view_wire": step_view_wire,
    "restore_diag": step_restore_diag,
    "refresh_quiet": step_refresh_quiet,
    "confirm_restore": step_confirm_restore,
    "confirm_replay": step_confirm_replay,
    "refresh": step_refresh,
    "view_detail": step_view_detail,
    "ops_modal": step_ops_modal,
    "cancel": step_cancel,
    "dead": step_dead,
    "history": step_history,
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", action="append", required=True, choices=sorted(STEPS))
    args = ap.parse_args(argv)
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        print(f"playwright unavailable: {exc}", file=sys.stderr)
        return 2
    capture: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        ctx = {"capture": capture}
        try:
            for name in args.step:
                log(f"=== step {name} ===")
                STEPS[name](page, ctx)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
