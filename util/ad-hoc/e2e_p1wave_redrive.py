#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E Phase 2 -- P1 fix-wave live re-drive driver
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

Live re-drive of the canopy P1 fix wave (2026-08-25/26) after the T6 GPU window:
F-CANOPY-005 (+ its blast-radius rows W2-step-2 / C2.5-10), F-CANOPY-003 (C2.5-09),
F-CANOPY-008 (canopy restart with a tab open), F-CANOPY-009/-010 (W5 step 4 held past two
refresh ticks; the confirm modal surviving >= 20 s), F-CANOPY-014 (W5-19..26, the M-REPLAY
control surface), F-CANOPY-011 + D-0 (W5-09/-10/-12..15, the Network Editor active surface),
F-CANOPY-035 (M-CANDIDATES-07 traces the candidate epochs of a live run), F-CANOPY-007 (W5
step 3 WITHOUT the harness's JUNIPER_CANOPY_SNAPSHOT_DIR workaround), OBS-1 (About "App
Version" == /v1/health) and the depth-label "0 of N" cosmetic.

Run under the only env that has playwright, with LD_LIBRARY_PATH cleared:

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/e2e_p1wave_redrive.py --step obs1,depth

Steps (comma-separated, order preserved):
  obs1     -- About tab "App Version" vs GET /v1/health (OBS-1)
  depth    -- Network Topology depth label reads "all" for the unfiltered case
  start    -- click start-button, wait for /api/status is_running (seg16 idiom)
  f035     -- Candidate Metrics loss plot gains a non-empty candidate trace during the run
  f005     -- control cycles under congestion: zero /api/train/* POSTs and zero 409s from the
              browser; F-003 re-enable latency per command; pause-while-paused and
              pause-while-STOPPED surface a danger alert with NO /api/train/* POST
  f008     -- restart the canopy leg with the tab open, on an EMPTY local snapshot dir:
              ws_csrf_rejected events, NO "Per-IP limit reached", control plane works after reload
  f007     -- W5 step 3: create a snapshot; the table lists cascor's inventory although canopy's
              local snapshot dir is empty
  f009     -- W5 step 4: View Details stays filled past two 10 s refresh ticks
  f010     -- the restore confirm modal survives >= 20 s, cancel closes it without a request
  f014     -- W5-16..26: replay via the UI; play/pause/speed/seek/range/stop through the panel
  f011     -- W5-07..15: restore -> Investigating -> Network Editor active surface, patch, append,
              remove through the UI
Observation discipline (arc traps): poll for TRANSITIONS with long budgets, read figures off
the plotly gd object, verify a click by its EFFECT, use each component's own exact ids, and
never cap a capture buffer. See util/ad-hoc/README.md for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess  # noqa: S404 -- restarts the canopy leg via the arc's own helper script
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")

log = _w3.log
http_get = _w3.http_get
http_post = _w3.http_post
open_dashboard = _w3.open_dashboard
is_disabled = _w3.is_disabled
text_of = _w3.text_of
vis = _f027.vis
fig_info = _f027.fig_info
ensure_no_modal = _f027.ensure_no_modal
open_tab = _f027.open_tab
shot = _f027.shot
cand_snapshot = _f027.cand_snapshot

CANOPY = _w3.CANOPY
CASCOR = os.environ.get("JUNIPER_E2E_CASCOR_URL", "http://127.0.0.1:8202")
CANOPY_LOG = _w3.CANOPY_LOG
PROJECT_DIR = os.environ.get("JUNIPER_E2E_PROJECT_DIR", "/home/pcalnon/Development/python/Juniper")
RUN_DIR = os.environ.get("JUNIPER_E2E_RUN_DIR", "/tmp/juniper-e2e")
EMPTY_SNAPDIR = os.environ.get("JUNIPER_E2E_EMPTY_SNAPDIR", os.path.join(RUN_DIR, "empty-snapdir"))
RESULTS_PATH = os.environ.get("JUNIPER_E2E_P1WAVE_RESULTS", os.path.join(RUN_DIR, "p1wave_results.json"))

SNAP = "hdf5-snapshots-panel"
RP = "replay-player-panel"
NE = "network-editor-panel"
NV = "network-visualizer"
CID = "candidate-metrics-panel"
ALERT = "training-control-outcome-alert"

RESULTS: dict = {}
RESP: list = []  # /api/ responses (status codes) -- open_dashboard captures requests only
CONSOLE: list = []  # every console line mentioning Phase D / WS / fallback


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
def record(step: str, **kv) -> None:
    RESULTS.setdefault(step, {}).update(kv)
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(RESULTS, fh, indent=2, default=str)


def attach_captures(page) -> None:
    """Response + console capture on top of open_dashboard's request capture."""

    def on_response(resp):
        url = resp.url
        if "/api/" in url or "/v1/" in url:
            RESP.append({"t": time.time(), "status": resp.status, "method": resp.request.method, "url": url.replace(CANOPY, "")})

    def on_console(msg):
        txt = msg.text
        if any(k in txt for k in ("Phase D", "[WS", "fallback", "Command timeout", "ws/control", "CSRF", "csrf")):
            CONSOLE.append({"t": time.time(), "type": msg.type, "text": txt[:400]})

    page.on("response", on_response)
    page.on("console", on_console)


def status() -> dict:
    return http_get("/api/status", timeout=60)[1]


def wait_status(pred, budget_s: float, every_s: float = 0.5, label: str = ""):
    """Poll /api/status until pred(status) is truthy; returns (seconds, status) or (None, last)."""
    t0 = time.time()
    last = {}
    while time.time() - t0 < budget_s:
        try:
            last = status()
        except Exception as exc:  # noqa: BLE001
            last = {"_err": str(exc)[:80]}
        if pred(last):
            return round(time.time() - t0, 2), last
        time.sleep(every_s)
    log(f"  !! wait_status({label}) exhausted {budget_s}s; last={json.dumps(last)[:200]}")
    return None, last


def click(page, el_id: str) -> bool:
    return bool(page.evaluate("""(id) => { const b = document.getElementById(id); if (!b) return false; b.click(); return true; }""", el_id))


def wait_enabled(page, el_id: str, budget_s: float, every_ms: int = 250):
    """Seconds until the button is no longer disabled (None if it never re-enables)."""
    t0 = time.time()
    while time.time() - t0 < budget_s:
        if is_disabled(page, el_id) is False:
            return round(time.time() - t0, 2)
        page.wait_for_timeout(every_ms)
    return None


def wait_disabled(page, el_id: str, budget_s: float, every_ms: int = 100):
    t0 = time.time()
    while time.time() - t0 < budget_s:
        if is_disabled(page, el_id):
            return round(time.time() - t0, 2)
        page.wait_for_timeout(every_ms)
    return None


def alert_state(page) -> dict:
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); if (!el) return {present:false};
             const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
             return {present:true, display:cs.display, w:Math.round(r.width), h:Math.round(r.height),
                     cls:(el.className||'').slice(0,80), text:(el.innerText||'').trim().slice(0,240)}; }""",
        ALERT,
    )


def wait_alert(page, budget_s: float, needle: str = ""):
    t0 = time.time()
    while time.time() - t0 < budget_s:
        a = alert_state(page)
        if a.get("present") and a.get("text") and (needle.lower() in a["text"].lower() if needle else True) and a.get("h", 0) > 0:
            return round(time.time() - t0, 2), a
        page.wait_for_timeout(250)
    return None, alert_state(page)


def train_posts(capture: list, since_t_ms: int | None = None) -> list:
    out = []
    for c in capture:
        if c.get("method") == "POST" and "/api/train/" in (c.get("url") or ""):
            if since_t_ms is None or c.get("t_ms", 0) >= since_t_ms:
                out.append(c)
    return out


def train_responses(since_t: float | None = None) -> list:
    return [r for r in RESP if "/api/train/" in r["url"] and (since_t is None or r["t"] >= since_t)]


def cap_now_ms() -> int:
    return int((time.time() - _w3._T0) * 1000)


def set_native_value(page, el_id: str, value: str) -> bool:
    """React-safe fill for <input>/<textarea> (the native value-setter idiom from the arc)."""
    return bool(
        page.evaluate(
            """([id, v]) => { const el = document.getElementById(id); if (!el) return false;
                 const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
                 const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
                 setter.call(el, v);
                 el.dispatchEvent(new Event('input', {bubbles:true}));
                 el.dispatchEvent(new Event('change', {bubbles:true}));
                 return true; }""",
            [el_id, value],
        )
    )


def select_native(page, el_id: str, value: str | None = None, index: int | None = None):
    """Set a native <select> (dbc.Select) by value or index; returns the resulting value."""
    return page.evaluate(
        """([id, v, i]) => { const el = document.getElementById(id); if (!el) return null;
             if (v !== null) el.value = v; else if (i !== null) el.selectedIndex = i;
             el.dispatchEvent(new Event('change', {bubbles:true}));
             el.dispatchEvent(new Event('input', {bubbles:true}));
             return {value: el.value, n: el.options.length,
                     options: [...el.options].map(o => o.value).slice(0, 40)}; }""",
        [el_id, value, index],
    )


def active_tab_label(page) -> str | None:
    return page.evaluate("""() => { const t = document.querySelector('[role=tab].active'); return t ? t.textContent.trim() : null; }""")


def pane_text(page, limit: int = 4000) -> str:
    return page.evaluate("""(n) => [...document.querySelectorAll('.tab-pane.active')].map(e => e.innerText || '').join('\\n').slice(0, n)""", limit)


def first_id_matching(page, needle: str, op: str | None = None) -> str | None:
    """Return the DOM id of the first element whose id contains needle (and op, when given)."""
    return page.evaluate(
        """([needle, op]) => { const els = [...document.querySelectorAll('[id*="' + needle + '"]')];
             for (const el of els) { if (!op || el.id.includes('"op":"' + op + '"')) return el.id; }
             return null; }""",
        [needle, op],
    )


def click_id(page, dom_id: str) -> bool:
    return bool(page.evaluate("""(id) => { const b = document.getElementById(id); if (!b) return false; b.click(); return true; }""", dom_id))


def drag_handle(page, container_id: str, dx: int, handle_index: int = 0) -> bool:
    """Mouse-drag an rc-slider handle inside a dcc.Slider/RangeSlider container."""
    loc = page.locator(f"#{container_id} .rc-slider-handle")
    if loc.count() <= handle_index:
        return False
    box = loc.nth(handle_index).bounding_box()
    if not box:
        return False
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx + dx, cy, steps=10)
    page.mouse.up()
    return True


def canopy_log_text() -> str:
    try:
        with open(CANOPY_LOG, "rb") as fh:
            return fh.read().decode("utf-8", "replace")
    except OSError as exc:
        return f"<log read failed: {exc}>"


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
def step_obs1(page, capture):
    log("STEP obs1 -- About 'App Version' vs /v1/health")
    ok = open_tab(page, "About")
    page.wait_for_timeout(2500)
    txt = pane_text(page)
    m = re.search(r"Version\s+v?([0-9][0-9A-Za-z.+\-]*)", txt)
    about_v = m.group(1) if m else None
    click(page, "about-panel-system-info-toggle")
    page.wait_for_timeout(2500)
    sysinfo = text_of(page, "about-panel-system-info-content") or ""
    m2 = re.search(r"App Version:\s*v?([0-9][0-9A-Za-z.+\-]*)", sysinfo)
    about_sys_v = m2.group(1) if m2 else None
    health = http_get("/v1/health")[1]
    hv = health.get("version")
    verdict = "PASS" if (about_v and about_v == hv and (about_sys_v in (None, hv))) else "FAIL"
    log(f"  tab_ok={ok} about_static={about_v} about_sysinfo={about_sys_v} health={hv} -> {verdict}")
    shot(page, "p1wave_obs1_about.png")
    record("obs1", verdict=verdict, about_static=about_v, about_sysinfo=about_sys_v, health_version=hv, pane_excerpt=txt[:300])


def step_depth(page, capture):
    log("STEP depth -- topology depth label for the unfiltered case")
    open_tab(page, "Network Topology")
    page.wait_for_timeout(8000)
    lab = vis(page, f"{NV}-depth-label")
    cont = vis(page, f"{NV}-depth-slider-container")
    hid = vis(page, f"{NV}-hidden-count")
    log(f"  label={lab.get('text')!r} container_display={cont.get('display')} hidden_count={hid.get('text')!r}")
    verdict = "PASS" if (lab.get("text") or "").strip().lower() == "all" else "FAIL"
    record("depth", verdict=verdict, label=lab.get("text"), container_display=cont.get("display"), hidden_count=hid.get("text"))


def step_start(page, capture):
    attach_captures(page)
    _f027.step_start(page, capture)
    record("start", status=status())


def _history_candidate_count() -> tuple[int, int]:
    """(total, candidate-phase) entry counts from /api/metrics/history."""
    try:
        h = http_get("/api/metrics/history?limit=8000", timeout=60)[1]
    except Exception:  # noqa: BLE001
        return 0, 0
    rows = h if isinstance(h, list) else (h.get("history") or h.get("metrics") or h.get("data") or [])
    cand = sum(1 for e in rows if isinstance(e, dict) and "candidate" in str(e.get("phase") or e.get("cascade_phase") or ""))
    return len(rows), cand


def _loss_trace_points(page) -> int:
    """Max data-point count across the candidate loss figure's traces (0 = empty plot)."""
    fi = fig_info(page, f"{CID}-loss-plot")
    return max([(t.get("nx") or 0) for t in (fi.get("traces") or [])], default=0)


def step_f035(page, capture, budget_s: int = 300):
    """M-CANDIDATES-07: the loss plot must trace the candidate epochs of a run.

    The fix (#524) sources the figure from /api/metrics/history via the shared metrics store,
    not the dead 3-key /api/state read. The live-DURING-run render is gated by the still-open
    F-CANOPY-004 congestion (the whole panel's REST-fed observables lag), so the verdict rests
    on the FIGURE tracing candidate points once the store holds them -- watched during the run
    and, decisively, confirmed after it (congestion cleared, history populated).
    """
    log("STEP f035 -- M-CANDIDATES-07: candidate loss plot traces the run's candidate epochs")
    open_tab(page, "Candidate Metrics")
    t0 = time.time()
    seen = []
    live_hits = 0
    saw_candidate_api = False
    while time.time() - t0 < budget_s:
        s = cand_snapshot(page)
        st = _f027.api_state_slice()
        pts = _loss_trace_points(page)
        if (st or {}).get("candidate_pool_status") not in (None, "Inactive"):
            saw_candidate_api = True
        sample = {"t": round(time.time() - t0, 1), "badge": s.get("badge"), "pool": s.get("pool"), "loss_points": pts, "api_pool": (st or {}).get("candidate_pool_status")}
        seen.append(sample)
        log(f"  t+{sample['t']:>5}s badge={s.get('badge')!r} pool={s.get('pool')!r} loss_points={pts} api_pool={(st or {}).get('candidate_pool_status')!r}")
        if pts > 0:
            live_hits += 1
        try:
            live_now = status().get("is_running") or status().get("is_paused")
        except Exception:  # noqa: BLE001
            live_now = True
        if not live_now and time.time() - t0 > 30:
            log("  run finished (per /api/status) -- proceeding to the post-run figure confirmation")
            break
        page.wait_for_timeout(5000)
    # Post-run confirmation: history holds candidate entries -> the figure must trace them.
    total_h, cand_h = _history_candidate_count()
    log(f"  post-run /api/metrics/history: total={total_h} candidate={cand_h}")
    post_pts = 0
    t0 = time.time()
    while time.time() - t0 < 90:
        post_pts = _loss_trace_points(page)
        if post_pts > 0:
            break
        # nudge the store's display mode to force a re-read of the full history
        page.wait_for_timeout(3000)
    fi = fig_info(page, f"{CID}-loss-plot")
    trace_names = [t.get("name") for t in (fi.get("traces") or [])]
    log(f"  post-run loss figure: points={post_pts} traces={trace_names} ann={fi.get('annotations')}")
    if (live_hits > 0 or post_pts > 0) and cand_h > 0:
        verdict = "PASS"
    elif cand_h == 0 and not saw_candidate_api:
        verdict = "INCONCLUSIVE"  # the run never reached a candidate phase
    else:
        verdict = "FAIL"  # candidate data present, figure never traced it
    log(f"  f035 -> {verdict} (live_hits={live_hits}, post_run_points={post_pts}, candidate_history={cand_h})")
    shot(page, "p1wave_f035_candidates.png")
    record("f035", verdict=verdict, live_hits=live_hits, post_run_points=post_pts, candidate_history=cand_h, total_history=total_h, trace_names=trace_names, samples=seen[-4:])


def _read_store(page, store_id: str):
    """Read a dcc.Store's .data straight off the redux layout (mechanism-level, not DOM)."""
    page.evaluate(_f027.FIND_STORE)
    return page.evaluate(
        """(id) => { const st = window.__dashStore; if (!st) return {err:'no-store'};
             const state = st.getState();
             const strs = (state.paths && state.paths.strs) ? state.paths.strs : state.paths;
             const p = strs ? strs[id] : null;
             if (!p) return {err:'no-path'};
             let node = state.layout; for (const k of p) { node = node && node[k]; }
             const d = node && node.props ? node.props.data : undefined;
             if (d === undefined) return {err:'no-data'};
             if (Array.isArray(d)) {
               const ph = {}; for (const e of d) { const k = (e && (e.phase || e.cascade_phase)) || '?'; ph[k]=(ph[k]||0)+1; }
               return {len:d.length, phases:ph, first:d[0], last:d[d.length-1]};
             }
             return {type: typeof d, keys: d && typeof d==='object' ? Object.keys(d).slice(0,20) : null, value: JSON.stringify(d).slice(0,200)}; }""",
        store_id,
    )


def step_storeprobe(page, capture):
    """Mechanism probe: what does the shared metrics store hold, and is it tab-specific?"""
    log("STEP storeprobe -- read metrics-panel-metrics-store on BOTH the metrics and candidates tabs")
    total_h, cand_h = _history_candidate_count()
    # (a) Training Metrics tab -- the store's "native" panel
    open_tab(page, "Training Metrics")
    page.wait_for_timeout(12000)
    store_on_metrics = _read_store(page, "metrics-panel-metrics-store")
    metrics_loss_pts = max([(t.get("nx") or 0) for t in (fig_info(page, "metrics-panel-loss-plot").get("traces") or [])], default=0)
    log(f"  [metrics tab] store={json.dumps(store_on_metrics, default=str)[:300]} main-loss-plot points={metrics_loss_pts}")
    # (b) Candidate Metrics tab -- where the F-035 loss plot lives
    open_tab(page, "Candidate Metrics")
    page.wait_for_timeout(12000)
    store_on_candidates = _read_store(page, "metrics-panel-metrics-store")
    mode_store = _read_store(page, "metrics-panel-display-mode-store")
    cand_loss_pts = _loss_trace_points(page)
    log(f"  [candidates tab] store={json.dumps(store_on_candidates, default=str)[:300]} candidate-loss-plot points={cand_loss_pts}")
    log(f"  display-mode={json.dumps(mode_store, default=str)[:120]}; /api/metrics/history total={total_h} candidate={cand_h}")
    record("storeprobe", store_on_metrics_tab=store_on_metrics, metrics_loss_points=metrics_loss_pts, store_on_candidates_tab=store_on_candidates, candidate_loss_points=cand_loss_pts, display_mode_store=mode_store, history_total=total_h, history_candidate=cand_h)


def step_f035probe(page, capture):
    """No-train probe: read the loss figure + history against the CURRENT (post-run) state."""
    log("STEP f035probe -- read the loss figure against the current post-run state (no retrain)")
    open_tab(page, "Candidate Metrics")
    total_h, cand_h = _history_candidate_count()
    log(f"  /api/metrics/history total={total_h} candidate={cand_h}")
    pts = 0
    t0 = time.time()
    while time.time() - t0 < 60:
        pts = _loss_trace_points(page)
        if pts > 0:
            break
        page.wait_for_timeout(3000)
    fi = fig_info(page, f"{CID}-loss-plot")
    log(f"  loss figure points={pts} traces={[t.get('name') for t in (fi.get('traces') or [])]} ann={fi.get('annotations')}")
    verdict = "PASS" if (pts > 0 and cand_h > 0) else ("INCONCLUSIVE" if cand_h == 0 else "FAIL")
    shot(page, "p1wave_f035probe.png")
    record("f035probe", verdict=verdict, points=pts, candidate_history=cand_h)


def _control_cycle(page, capture, cmd: str, expect):
    """Click <cmd>-button, wait for the API to reflect it, then for the button to re-enable."""
    btn = f"{cmd}-button"
    pre_wait = wait_enabled(page, btn, 120)
    if pre_wait is None:
        log(f"  !! {btn} never became enabled before the click")
        return {"cmd": cmd, "clicked": False}
    t_ms = cap_now_ms()
    t_wall = time.time()
    clicked = click(page, btn)
    t_dis = wait_disabled(page, btn, 5)
    api_s, st = wait_status(expect, 90, label=cmd)
    re_s = wait_enabled(page, btn, 120)
    posts = train_posts(capture, t_ms)
    resps = train_responses(t_wall)
    out = {"cmd": cmd, "clicked": clicked, "optimistic_disable_s": t_dis, "api_reflect_s": api_s, "reenable_s": re_s, "train_posts": posts, "train_responses": resps, "api_after": {k: st.get(k) for k in ("is_running", "is_paused", "fsm_status", "phase")}}
    log(f"  {cmd}: disable={t_dis}s api={api_s}s re-enable={re_s}s posts={len(posts)} resp={[(r['status'], r['url']) for r in resps]} api_after={out['api_after']}")
    return out


def _rejection_arm(page, capture, cmd: str, label: str):
    """Click a command the backend must reject; expect a danger alert and NO /api/train POST."""
    btn = f"{cmd}-button"
    pre = wait_enabled(page, btn, 120)
    if pre is None:
        log(f"  !! {btn} disabled -- the rejection arm cannot be driven ({label})")
        return {"arm": label, "clicked": False}
    t_ms = cap_now_ms()
    t_wall = time.time()
    click(page, btn)
    al_s, al = wait_alert(page, 90, needle=cmd)
    re_s = wait_enabled(page, btn, 120)
    posts = train_posts(capture, t_ms)
    resps = train_responses(t_wall)
    cons = [c for c in CONSOLE if c["t"] >= t_wall]
    out = {"arm": label, "clicked": True, "alert_s": al_s, "alert": al, "reenable_s": re_s, "train_posts": posts, "train_responses": resps, "console": cons[-8:]}
    log(f"  {label}: alert={al_s}s text={al.get('text')!r} re-enable={re_s}s posts={len(posts)} resp={[(r['status'], r['url']) for r in resps]}")
    for c in cons[-8:]:
        log(f"    console[{c['type']}] {c['text'][:200]}")
    shot(page, f"p1wave_f005_{label}.png")
    return out


def step_f005(page, capture):
    log("STEP f005 -- control cycles under congestion (F-CANOPY-005 + F-CANOPY-003), then the rejection arms")
    if not RESP and not CONSOLE:
        attach_captures(page)
    st = status()
    if not st.get("is_running"):
        log("  !! no run in progress -- f005 needs a live run (run the start step first)")
        record("f005", verdict="BLOCKED", reason="no live run")
        return
    cycles = []
    cycles.append(_control_cycle(page, capture, "pause", lambda s: s.get("is_paused") is True))
    cycles.append(_control_cycle(page, capture, "resume", lambda s: s.get("is_paused") is False and s.get("is_running")))
    cycles.append(_control_cycle(page, capture, "pause", lambda s: s.get("is_paused") is True))
    # W2 step 2 / C2.5-10: pause while paused -> business rejection -> danger alert, no HTTP re-issue
    arm_paused = _rejection_arm(page, capture, "pause", "pause_while_paused")
    # W2 step 3: dismiss
    page.evaluate("""() => { const a = document.getElementById('training-control-outcome-alert'); const b = a && a.querySelector('.btn-close'); if (b) b.click(); }""")
    page.wait_for_timeout(1500)
    cycles.append(_control_cycle(page, capture, "resume", lambda s: s.get("is_paused") is False and s.get("is_running")))
    cycles.append(_control_cycle(page, capture, "stop", lambda s: s.get("is_running") is False))
    # pause while STOPPED -> business rejection
    # pause-while-STOPPED: the pause button is CORRECTLY disabled when stopped, so this business
    # rejection is unreachable through the UI (clicking a disabled button sends nothing). That is
    # correct behaviour, not the F-005 defect; the reachable business-rejection arm is pause-while-
    # paused above. Record it as N-A when the button is disabled rather than failing on it.
    if is_disabled(page, "pause-button"):
        arm_stopped = {"arm": "pause_while_stopped", "clicked": False, "note": "pause-button correctly disabled when STOPPED (unreachable arm; not the F-005 defect)", "train_posts": [], "train_responses": []}
        log("  pause_while_stopped: N-A (pause-button correctly disabled when STOPPED)")
    else:
        arm_stopped = _rejection_arm(page, capture, "pause", "pause_while_stopped")
    cycles.append(_control_cycle(page, capture, "reset", lambda s: s.get("is_running") is False))
    all_posts = [p for c in cycles for p in c.get("train_posts", [])] + arm_paused.get("train_posts", []) + arm_stopped.get("train_posts", [])
    all_resps = [r for c in cycles for r in c.get("train_responses", [])] + arm_paused.get("train_responses", []) + arm_stopped.get("train_responses", [])
    n409 = sum(1 for r in all_resps if r["status"] == 409)
    reenables = [c.get("reenable_s") for c in cycles if c.get("clicked")]
    f005_ok = not all_posts and n409 == 0
    f003_ok = all(r is not None and r <= 15 for r in reenables) if reenables else False
    # F-005's reachable rejection arm (pause-while-paused) must surface a danger alert with NO
    # /api/train POST; the stopped arm counts only if it was actually driveable.
    reachable_arms = [arm_paused] + ([arm_stopped] if arm_stopped.get("clicked") else [])
    arms_ok = bool(arm_paused.get("alert_s") is not None) and all(not a.get("train_posts") for a in reachable_arms)
    verdict_f005 = "PASS" if (f005_ok and arms_ok) else "FAIL"
    verdict_f003 = "PASS" if f003_ok else "FAIL"
    log(f"  F-005 -> {verdict_f005} (train POSTs from browser={len(all_posts)}, 409s={n409}, arms_ok={arms_ok}); F-003 -> {verdict_f003} (re-enable s={reenables})")
    record("f005", verdict=verdict_f005, cycles=cycles, arm_pause_while_paused=arm_paused, arm_pause_while_stopped=arm_stopped, n_train_posts=len(all_posts), n_409=n409)
    record("f003", verdict=verdict_f003, reenable_s=reenables)


def step_f008(page, capture):
    log("STEP f008 -- restart the canopy leg with the tab open (F-CANOPY-008), on an EMPTY snapshot dir (F-CANOPY-007 posture)")
    if not RESP and not CONSOLE:
        attach_captures(page)
    os.makedirs(EMPTY_SNAPDIR, exist_ok=True)
    env = dict(os.environ)
    env.update({"JUNIPER_E2E_PROJECT_DIR": PROJECT_DIR, "JUNIPER_E2E_RECURRENCE_PORT": os.environ.get("JUNIPER_E2E_RECURRENCE_PORT", "8212"), "JUNIPER_E2E_CANOPY_SNAPSHOT_DIR": EMPTY_SNAPDIR})
    env.pop("LD_LIBRARY_PATH", None)
    t_restart = time.time()
    proc = subprocess.run(["bash", os.path.join(_HERE, "e2e_canopy_leg_restart.bash")], env=env, capture_output=True, text=True, timeout=300, check=False)  # noqa: S603
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
    for line in tail:
        log(f"    restart| {line[:200]}")
    log(f"  restart rc={proc.returncode}")
    # health gate on the new process
    h_s, _ = wait_status(lambda s: "is_running" in s, 90, label="canopy back")
    health = http_get("/v1/health")[1]
    log(f"  canopy back after {h_s}s: {json.dumps(health)[:200]}")
    # let the browser's auto-reconnect present the stale token
    page.wait_for_timeout(30000)
    text = canopy_log_text()
    n_rej = text.count("ws_csrf_rejected")
    n_lock = text.count("Per-IP limit reached")
    cons_before = [c for c in CONSOLE if c["t"] >= t_restart]
    log(f"  after 30 s: ws_csrf_rejected={n_rej} per-ip-lock={n_lock} console(since restart)={len(cons_before)}")
    for c in cons_before[-6:]:
        log(f"    console[{c['type']}] {c['text'][:200]}")
    # reload -> fresh token -> control plane must work
    page.reload(wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(4000)
    _w3.dismiss_welcome(page)
    page.wait_for_timeout(4000)
    badge = vis(page, "ws-connection-indicator")
    t_ms = cap_now_ms()
    t_wall = time.time()
    click(page, "reset-button")
    re_s = wait_enabled(page, "reset-button", 60)
    posts = train_posts(capture, t_ms)
    resps = train_responses(t_wall)
    text2 = canopy_log_text()
    n_rej2 = text2.count("ws_csrf_rejected")
    n_lock2 = text2.count("Per-IP limit reached")
    al = alert_state(page)
    log(f"  after reload: badge={badge.get('text')!r} reset re-enable={re_s}s posts={len(posts)} resp={[(r['status'], r['url']) for r in resps]} rejected_total={n_rej2} per-ip-lock={n_lock2} alert={al.get('text')!r}")
    verdict = "PASS" if (n_rej >= 1 and n_lock2 == 0 and re_s is not None and not posts) else "FAIL"
    shot(page, "p1wave_f008_after_reload.png")
    record("f008", verdict=verdict, restart_rc=proc.returncode, rejected_after_restart=n_rej, rejected_total=n_rej2, per_ip_lock=n_lock2, badge=badge.get("text"), reset_reenable_s=re_s, train_posts=posts, train_responses=resps, health=health, restart_tail=tail)


def _snapshot_rows(page) -> dict:
    return page.evaluate(
        """(p) => { const body = document.getElementById(p + '-table-body');
             const rows = body ? [...body.querySelectorAll('tr')] : [];
             const st = document.getElementById(p + '-status'); const es = document.getElementById(p + '-empty-state');
             return {n_rows: rows.length, first: rows.length ? (rows[0].innerText||'').trim().slice(0,160) : null,
                     status: st ? (st.innerText||'').trim().slice(0,120) : null,
                     empty_display: es ? getComputedStyle(es).display : null,
                     view_ids: [...document.querySelectorAll('[id*="' + p + '-view-btn"]')].map(e => e.id).slice(0,5)}; }""",
        SNAP,
    )


def step_f007(page, capture):
    log("STEP f007 -- W5 step 3 with an EMPTY local snapshot dir (F-CANOPY-007)")
    st = status()
    if st.get("is_running"):
        log("  !! training is running -- stopping first (W5 precondition)")
        click(page, "stop-button")
        wait_status(lambda s: not s.get("is_running"), 90, label="stop")
    open_tab(page, "Snapshots")
    page.wait_for_timeout(4000)
    before = _snapshot_rows(page)
    log(f"  before: {json.dumps(before)[:300]}")
    name = f"p1wave_{int(time.time())}"
    set_native_value(page, f"{SNAP}-create-name", name)
    set_native_value(page, f"{SNAP}-create-description", "P1-wave re-drive, F-CANOPY-007 arm (empty local dir)")
    page.wait_for_timeout(800)
    t_ms = cap_now_ms()
    click(page, f"{SNAP}-create-button")
    t0 = time.time()
    created = None
    while time.time() - t0 < 90:
        cs = text_of(page, f"{SNAP}-create-status") or ""
        if cs:
            created = cs
            break
        page.wait_for_timeout(500)
    log(f"  create-status after {round(time.time() - t0, 1)}s: {created!r}")
    m = re.search(r"(snapshot_[0-9TZ]+)", created or "")
    snap_id = m.group(1) if m else None
    # table must list cascor's inventory although the local dir is empty
    t0 = time.time()
    rows = None
    while time.time() - t0 < 60:
        rows = _snapshot_rows(page)
        if rows.get("n_rows") and (snap_id is None or (snap_id in json.dumps(rows) or rows["n_rows"] > before.get("n_rows", 0))):
            break
        page.wait_for_timeout(1000)
    log(f"  table after {round(time.time() - t0, 1)}s: {json.dumps(rows)[:300]}")
    canopy_list = http_get("/api/v1/snapshots", timeout=60)[1]
    cascor_list = None
    try:
        import urllib.request

        with urllib.request.urlopen(CASCOR + "/v1/snapshots", timeout=30) as r:  # noqa: S310
            cascor_list = json.loads(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        cascor_list = {"_err": str(exc)[:120]}
    local_h5 = [f for f in os.listdir(EMPTY_SNAPDIR) if f.endswith(".h5")] if os.path.isdir(EMPTY_SNAPDIR) else None
    n_canopy = len(canopy_list.get("snapshots") or []) if isinstance(canopy_list, dict) else None
    n_cascor = len((cascor_list or {}).get("data") or []) if isinstance(cascor_list, dict) else None
    src = canopy_list.get("source") if isinstance(canopy_list, dict) else None
    log(f"  canopy list n={n_canopy} source={src!r} total={canopy_list.get('total') if isinstance(canopy_list, dict) else None}; cascor n={n_cascor}; local .h5 in empty dir={local_h5}")
    verdict = "PASS" if (snap_id and rows and rows.get("n_rows") and (n_canopy or 0) >= 1 and not local_h5) else "FAIL"
    shot(page, "p1wave_f007_snapshots.png")
    record("f007", verdict=verdict, snapshot_id=snap_id, create_status=created, table=rows, canopy_n=n_canopy, canopy_source=src, cascor_n=n_cascor, local_h5=local_h5, posts=[c for c in capture if c.get("t_ms", 0) >= t_ms and "/api/v1/snapshots" in (c.get("url") or "")][:5])


def step_f009(page, capture):
    log("STEP f009 -- W5 step 4: View Details held past two 10 s refresh ticks")
    open_tab(page, "Snapshots")
    page.wait_for_timeout(3000)
    vid = first_id_matching(page, f"{SNAP}-view-btn")
    if not vid:
        log("  !! no view button rendered (no rows?)")
        record("f009", verdict="BLOCKED", reason="no view button")
        return
    click_id(page, vid)
    t0 = time.time()
    timeline = []
    filled_at = None
    wiped_at = None
    last = None
    while time.time() - t0 < 32:
        txt = (text_of(page, f"{SNAP}-detail-panel") or "").replace("\n", " / ")
        filled = "ID:" in txt or "Name:" in txt or "snapshot_" in txt
        if filled and filled_at is None:
            filled_at = round(time.time() - t0, 1)
        if filled_at is not None and not filled and wiped_at is None:
            wiped_at = round(time.time() - t0, 1)
        if txt[:80] != (last or "")[:80]:
            timeline.append((round(time.time() - t0, 1), txt[:120]))
            last = txt
        page.wait_for_timeout(500)
    log(f"  filled_at={filled_at}s wiped_at={wiped_at}s timeline={timeline[:8]}")
    verdict = "PASS" if (filled_at is not None and wiped_at is None) else "FAIL"
    shot(page, "p1wave_f009_detail.png")
    record("f009", verdict=verdict, view_id=vid, filled_at=filled_at, wiped_at=wiped_at, timeline=timeline[:10])


def _modal_state(page) -> dict:
    return page.evaluate(
        """(p) => { const dlg = [...document.querySelectorAll('[role=dialog]')].filter(x => (x.className||'').includes('show'));
             const body = document.getElementById(p + '-restore-modal-body');
             return {n_open: dlg.length, body: body ? (body.innerText||'').trim().slice(0,200) : null,
                     body_visible: body ? (body.getBoundingClientRect().height > 0) : false}; }""",
        SNAP,
    )


def step_f010(page, capture):
    log("STEP f010 -- the restore confirm modal must survive >= 20 s; cancel closes it without a request")
    open_tab(page, "Snapshots")
    page.wait_for_timeout(3000)
    oid = first_id_matching(page, f"{SNAP}-snapshot-op-btn", "restore")
    if not oid:
        log("  !! no restore op button rendered")
        record("f010", verdict="BLOCKED", reason="no restore button")
        return
    t_ms = cap_now_ms()
    click_id(page, oid)
    t0 = time.time()
    timeline = []
    opened_at = None
    closed_at = None
    while time.time() - t0 < 24:
        ms = _modal_state(page)
        if ms["n_open"] and ms["body"] and opened_at is None:
            opened_at = round(time.time() - t0, 1)
        if opened_at is not None and (not ms["n_open"] or not ms["body"]) and closed_at is None:
            closed_at = round(time.time() - t0, 1)
        timeline.append((round(time.time() - t0, 1), ms["n_open"], (ms["body"] or "")[:60]))
        page.wait_for_timeout(1000)
    log(f"  opened_at={opened_at}s closed_at={closed_at}s last={timeline[-1]}")
    click(page, f"{SNAP}-restore-cancel")
    page.wait_for_timeout(1500)
    after = _modal_state(page)
    posts = [c for c in capture if c.get("t_ms", 0) >= t_ms and "/api/v1/snapshots" in (c.get("url") or "") and c.get("method") == "POST"]
    log(f"  after cancel: open={after['n_open']} snapshot POSTs from browser={len(posts)}")
    verdict = "PASS" if (opened_at is not None and closed_at is None and after["n_open"] == 0 and not posts) else "FAIL"
    shot(page, "p1wave_f010_modal.png")
    record("f010", verdict=verdict, op_id=oid, opened_at=opened_at, closed_at=closed_at, after_cancel=after, browser_posts=posts, timeline=timeline[::4])


def _rp_status(page) -> str:
    return (text_of(page, f"{RP}-status") or "").replace("\n", " / ")[:200]


def _wait_rp_status_change(page, prev: str, budget_s: float = 40):
    t0 = time.time()
    while time.time() - t0 < budget_s:
        cur = _rp_status(page)
        if cur and cur != prev:
            return round(time.time() - t0, 1), cur
        page.wait_for_timeout(500)
    return None, _rp_status(page)


def step_f014(page, capture):
    log("STEP f014 -- W5-16..26: replay via the UI, then the panel's controls (F-CANOPY-014)")
    open_tab(page, "Snapshots")
    page.wait_for_timeout(3000)
    oid = first_id_matching(page, f"{SNAP}-snapshot-op-btn", "replay")
    if not oid:
        record("f014", verdict="BLOCKED", reason="no replay button")
        return
    click_id(page, oid)
    t0 = time.time()
    while time.time() - t0 < 20 and not _modal_state(page)["n_open"]:
        page.wait_for_timeout(500)
    log(f"  replay modal open after {round(time.time() - t0, 1)}s: {_modal_state(page)['body']!r}")
    click(page, f"{SNAP}-restore-confirm")
    t0 = time.time()
    rs = ""
    while time.time() - t0 < 90:
        rs = text_of(page, f"{SNAP}-restore-status") or ""
        if rs:
            break
        page.wait_for_timeout(500)
    log(f"  restore-status after {round(time.time() - t0, 1)}s: {rs!r}")
    t0 = time.time()
    while time.time() - t0 < 60 and active_tab_label(page) != "Replay":
        page.wait_for_timeout(500)
    tab = active_tab_label(page)
    page.wait_for_timeout(3000)
    header = {"tab": tab, "snapshot_id": text_of(page, f"{RP}-snapshot-id"), "fsm": text_of(page, f"{RP}-fsm-badge"), "weights": vis(page, f"{RP}-weights-badge"), "idle": vis(page, f"{RP}-idle"), "active": vis(page, f"{RP}-active")}
    log(f"  header: tab={tab!r} id={header['snapshot_id']!r} fsm={header['fsm']!r} weights={header['weights'].get('text')!r} idle_display={header['idle'].get('display')} active_display={header['active'].get('display')}")
    results = {}
    prev = _rp_status(page)
    for label, action in (("play", lambda: click(page, f"{RP}-play-btn")), ("pause", lambda: click(page, f"{RP}-pause-btn")), ("speed", lambda: drag_handle(page, f"{RP}-speed", 60)), ("seek", lambda: drag_handle(page, f"{RP}-scrubber", 80)), ("range", lambda: drag_handle(page, f"{RP}-range", -60, 1)), ("stop", lambda: click(page, f"{RP}-stop-btn"))):
        ok = action()
        s, cur = _wait_rp_status_change(page, prev, 40)
        readouts = {"epoch": text_of(page, f"{RP}-epoch-readout"), "speed": text_of(page, f"{RP}-speed-readout"), "range": text_of(page, f"{RP}-range-readout"), "last_sample": text_of(page, f"{RP}-last-sample-readout")}
        results[label] = {"driven": ok, "status_after_s": s, "status": cur, "readouts": readouts}
        log(f"  {label}: driven={ok} status(+{s}s)={cur!r} readouts={readouts}")
        prev = cur
        page.wait_for_timeout(1500)
    bad = [k for k, v in results.items() if (not v["driven"]) or ("No scheme" in (v["status"] or "")) or ("error" in (v["status"] or "").lower() and "success" not in (v["status"] or "").lower())]
    verdict = "PASS" if (tab == "Replay" and header["snapshot_id"] and not bad) else "FAIL"
    log(f"  f014 -> {verdict} (bad={bad})")
    shot(page, "p1wave_f014_replay.png")
    record("f014", verdict=verdict, restore_status=rs, header={k: (v if isinstance(v, str) or v is None else v.get("text")) for k, v in header.items()}, controls=results, bad=bad)


def step_f011check(page, capture):
    """Re-read the Network Editor active surface NOW (quiescent) -- confirms an F-004 lag vs an F-011 regression."""
    log("STEP f011check -- editor active surface + topology, congestion cleared")
    st = status()
    top = http_get("/api/topology", timeout=30)[1]
    log(f"  /api/status fsm={st.get('fsm_status')!r} hidden={st.get('hidden_units')}; /api/topology I/H/O={top.get('input_units')}/{top.get('hidden_units')}/{top.get('output_units')}")
    open_tab(page, "Network Editor")
    page.wait_for_timeout(10000)
    idle = vis(page, f"{NE}-idle")
    active = vis(page, f"{NE}-active")
    badge = text_of(page, f"{NE}-idle-fsm-badge")
    readout = text_of(page, f"{NE}-topology-readout")
    rem = select_native(page, f"{NE}-remove-idx")
    log(f"  editor: idle_display={idle.get('display')} active_display={active.get('display')} badge={badge!r} readout={readout!r} remove-opts={rem}")
    active_shown = active.get("display") not in (None, "none") and idle.get("display") == "none"
    fsm_ok = "investigat" in (badge or "").lower()
    topo_ok = bool(readout) and "No topology loaded" not in readout
    verdict = "PASS" if (active_shown and fsm_ok and topo_ok) else "FAIL"
    log(f"  f011check -> {verdict} (active_shown={active_shown}, fsm_ok={fsm_ok}, topo_ok={topo_ok})")
    shot(page, "p1wave_f011check_editor.png")
    record("f011check", verdict=verdict, api_fsm=st.get("fsm_status"), api_topology={"I": top.get("input_units"), "H": top.get("hidden_units"), "O": top.get("output_units")}, idle_display=idle.get("display"), active_display=active.get("display"), badge=badge, readout=readout, remove_options=rem)


def step_f011(page, capture):
    log("STEP f011 -- W5-07..15: restore -> Investigating -> Network Editor active surface (F-CANOPY-011 + D-0)")
    st = status()
    if st.get("is_running"):
        click(page, "stop-button")
        wait_status(lambda s: not s.get("is_running"), 90, label="stop")
    open_tab(page, "Snapshots")
    page.wait_for_timeout(3000)
    oid = first_id_matching(page, f"{SNAP}-snapshot-op-btn", "restore")
    if not oid:
        record("f011", verdict="BLOCKED", reason="no restore button")
        return
    click_id(page, oid)
    t0 = time.time()
    while time.time() - t0 < 20 and not _modal_state(page)["n_open"]:
        page.wait_for_timeout(500)
    click(page, f"{SNAP}-restore-confirm")
    t0 = time.time()
    rs = ""
    while time.time() - t0 < 90:
        rs = text_of(page, f"{SNAP}-restore-status") or ""
        if rs:
            break
        page.wait_for_timeout(500)
    log(f"  W5-07 restore-status after {round(time.time() - t0, 1)}s: {rs!r}")
    inv_s, st = wait_status(lambda s: str(s.get("fsm_status", "")).lower().startswith("investigat"), 120, label="Investigating")
    log(f"  W5-08 fsm={st.get('fsm_status')!r} after {inv_s}s")
    open_tab(page, "Network Editor")
    page.wait_for_timeout(6000)
    idle = vis(page, f"{NE}-idle")
    active = vis(page, f"{NE}-active")
    badge = text_of(page, f"{NE}-idle-fsm-badge")
    readout = text_of(page, f"{NE}-topology-readout")
    rem = select_native(page, f"{NE}-remove-idx")
    log(f"  W5-09 idle_display={idle.get('display')} active_display={active.get('display')} badge={badge!r}")
    log(f"  W5-10 readout={readout!r} remove-idx options={rem}")
    # W5-11 counts
    open_tab(page, "Network Topology")
    page.wait_for_timeout(6000)
    n_in = text_of(page, f"{NV}-input-count")
    n_hid = text_of(page, f"{NV}-hidden-count")
    n_out = text_of(page, f"{NV}-output-count")
    log(f"  W5-11 counts I={n_in!r} H={n_hid!r} O={n_out!r}")
    try:
        in_u, hid_u, out_u = int(n_in), int(n_hid), int(n_out)
    except (TypeError, ValueError):
        in_u, hid_u, out_u = None, None, None
    open_tab(page, "Network Editor")
    page.wait_for_timeout(3000)
    # W5-12 patch (output_weights is the shipped default target; F-CANOPY-012 says its shape is structurally impossible -- record verbatim)
    patch = {}
    if in_u is not None:
        select_native(page, f"{NE}-patch-target", "output_weights")
        vals = ",".join(["0.01"] * ((in_u + hid_u) * out_u))
        set_native_value(page, f"{NE}-patch-values", vals)
        page.wait_for_timeout(500)
        prev = text_of(page, f"{NE}-status") or ""
        click(page, f"{NE}-patch-submit")
        t0 = time.time()
        cur = prev
        while time.time() - t0 < 60:
            cur = text_of(page, f"{NE}-status") or ""
            if cur and cur != prev:
                break
            page.wait_for_timeout(500)
        patch = {"n_values": (in_u + hid_u) * out_u, "status": cur[:300], "after_s": round(time.time() - t0, 1)}
        log(f"  W5-12 patch({patch['n_values']} values): {cur[:200]!r}")
    # W5-13 append
    append = {}
    if in_u is not None:
        set_native_value(page, f"{NE}-add-weights", ",".join(["0.1"] * (in_u + hid_u)))
        page.wait_for_timeout(500)
        prev = text_of(page, f"{NE}-status") or ""
        click(page, f"{NE}-add-submit")
        t0 = time.time()
        cur = prev
        while time.time() - t0 < 60:
            cur = text_of(page, f"{NE}-status") or ""
            if cur and cur != prev:
                break
            page.wait_for_timeout(500)
        append = {"n_weights": in_u + hid_u, "status": cur[:300], "after_s": round(time.time() - t0, 1)}
        log(f"  W5-13 append({in_u + hid_u} weights): {cur[:200]!r}")
        open_tab(page, "Network Topology")
        page.wait_for_timeout(8000)
        h2 = text_of(page, f"{NV}-hidden-count")
        append["hidden_after"] = h2
        log(f"  W5-14 hidden count after append: {h2!r} (was {n_hid!r})")
        open_tab(page, "Network Editor")
        page.wait_for_timeout(4000)
    # W5-15 remove through the UI (D-0 fixed -> the dropdown is populated)
    remove = {}
    rem2 = select_native(page, f"{NE}-remove-idx")
    if rem2 and rem2.get("n", 0) > 0 and any(o != "" for o in rem2.get("options", [])):
        last_opt = [o for o in rem2["options"] if o != ""][-1]
        select_native(page, f"{NE}-remove-idx", last_opt)
        page.wait_for_timeout(500)
        click(page, f"{NE}-remove-submit")
        t0 = time.time()
        while time.time() - t0 < 20:
            n_open = page.evaluate("""() => [...document.querySelectorAll('[role=dialog]')].filter(x => (x.className||'').includes('show')).length""")
            if n_open:
                break
            page.wait_for_timeout(500)
        body = text_of(page, f"{NE}-remove-modal-body")
        prev = text_of(page, f"{NE}-status") or ""
        click(page, f"{NE}-remove-confirm")
        t0 = time.time()
        cur = prev
        while time.time() - t0 < 90:
            cur = text_of(page, f"{NE}-status") or ""
            if cur and cur != prev:
                break
            page.wait_for_timeout(500)
        remove = {"idx": last_opt, "modal_body": (body or "")[:200], "status": cur[:300], "after_s": round(time.time() - t0, 1)}
        log(f"  W5-15 remove idx={last_opt}: modal={body!r} status={cur[:200]!r}")
        open_tab(page, "Network Topology")
        page.wait_for_timeout(8000)
        remove["hidden_after"] = text_of(page, f"{NV}-hidden-count")
        log(f"  hidden count after remove: {remove['hidden_after']!r}")
    else:
        log(f"  W5-15 remove dropdown still empty: {rem2}")
    w5_09 = active.get("display") not in (None, "none") and idle.get("display") == "none" and "investigat" in (badge or "").lower()
    w5_10 = bool(readout) and "No topology loaded" not in readout and rem is not None and rem.get("n", 0) > 0
    verdict = "PASS" if (w5_09 and w5_10) else "FAIL"
    shot(page, "p1wave_f011_editor.png")
    record("f011", verdict=verdict, restore_status=rs, investigating_after_s=inv_s, fsm=st.get("fsm_status"), idle_display=idle.get("display"), active_display=active.get("display"), badge=badge, readout=readout, remove_options=rem, counts={"I": n_in, "H": n_hid, "O": n_out}, patch=patch, append=append, remove=remove, w5_09=w5_09, w5_10=w5_10)


STEPS = {
    "obs1": step_obs1,
    "depth": step_depth,
    "start": step_start,
    "f035": step_f035,
    "f035probe": step_f035probe,
    "storeprobe": step_storeprobe,
    "f005": step_f005,
    "f008": step_f008,
    "f007": step_f007,
    "f009": step_f009,
    "f010": step_f010,
    "f014": step_f014,
    "f011check": step_f011check,
    "f011": step_f011,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", required=True, help="comma-separated step names (order preserved): " + ", ".join(STEPS))
    args = ap.parse_args()
    wanted = [s.strip() for s in args.step.split(",") if s.strip()]
    bad = [s for s in wanted if s not in STEPS]
    if bad:
        print(f"unknown step(s): {bad}; valid: {list(STEPS)}", file=sys.stderr)
        return 2
    if os.path.exists(RESULTS_PATH):
        try:
            with open(RESULTS_PATH, encoding="utf-8") as fh:
                RESULTS.update(json.load(fh))
        except (OSError, ValueError):
            pass
    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            for name in wanted:
                STEPS[name](page, capture)
        finally:
            n_dash = sum(1 for c in capture if "_dash-update-component" in (c.get("url") or ""))
            n_api = sum(1 for c in capture if "/api/" in (c.get("url") or ""))
            log(f"capture summary: {len(capture)} requests ({n_dash} dash updates, {n_api} /api); responses={len(RESP)}; console={len(CONSOLE)}")
            log(f"results -> {RESULTS_PATH}: " + json.dumps({k: v.get("verdict") for k, v in RESULTS.items()}))
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
