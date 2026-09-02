#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E Phase 2 -- topology / W4 / fix-independent re-drive driver
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

Drives the §6.3 rows that never depended on a fix and were blocked only by
F-CANOPY-006 / -027 (both closed) or by the absence of a live bring-up:

  W1-12..14        cascade growth visible on the Network Topology tab
  M-TOPOLOGY-01..18 the whole topology control surface
  W4-01..17        topology exploration walkthrough
  M-DATASET-14     theme flip recolours the dataset figures

Run under the only env that has playwright, with LD_LIBRARY_PATH cleared:

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/e2e_seg17_topology_driver.py --step probe

Steps (comma-separated, order preserved):
  probe    -- dump the REAL DOM shape of the four topology controls (dcc.Dropdown /
              Checklist / RadioItems are NOT native selects; this pins the idiom
              before any row is scored)
  w1grow   -- W1-12..14: tab entry fires GET /api/topology, the graph renders, a
              cascade add increments -hidden-count, top bar == topology count
  topo     -- M-TOPOLOGY-01..09/16..18 + W4-02..10: layout cycle, show-weights,
              display-mode, view-mode, depth slider, stats bar, store refresh
  toposel  -- M-TOPOLOGY-10..15 + W4-11..16: node click, box select, clear, zoom/pan
              restore, camera PNG, hover-is-inert
  theme    -- M-TOPOLOGY-09 + W4-17 + M-DATASET-14: dark-mode flip recolours

Observation discipline (arc traps): poll for TRANSITIONS with long budgets, read
figures off the plotly gd object, verify every widget write by its EFFECT (never by
the write returning true), use each component's own exact ids, and never cap a
capture buffer. Renders lag under F-CANOPY-004 congestion -- every wait budget here
is sized for that, and a miss is re-read quiescent before it is scored.

See util/ad-hoc/README.md for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
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
open_dashboard = _w3.open_dashboard
text_of = _w3.text_of
vis = _f027.vis
fig_info = _f027.fig_info
ensure_no_modal = _f027.ensure_no_modal
open_tab = _f027.open_tab
shot = _f027.shot

CANOPY = _w3.CANOPY
RUN_DIR = os.environ.get("JUNIPER_E2E_RUN_DIR", "/tmp/juniper-e2e")
RESULTS_PATH = os.environ.get("JUNIPER_E2E_SEG17_RESULTS", os.path.join(RUN_DIR, "seg17_results.json"))

NV = "network-visualizer"

RESULTS: dict = {}
RESP: list = []


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
def record(step: str, **kv) -> None:
    RESULTS.setdefault(step, {}).update(kv)
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(RESULTS, fh, indent=2, default=str)


def attach_captures(page) -> None:
    def on_response(resp):
        url = resp.url
        if "/api/" in url or "/v1/" in url:
            RESP.append({"t": time.time(), "status": resp.status, "method": resp.request.method, "url": url.replace(CANOPY, "")})

    page.on("response", on_response)


def api_hits(needle: str, since_t: float) -> list:
    return [r for r in RESP if needle in r["url"] and r["t"] >= since_t]


def counts(page) -> dict:
    """The stats-bar four counts, as text (M-TOPOLOGY-08)."""
    return {
        "input": text_of(page, f"{NV}-input-count"),
        "hidden": text_of(page, f"{NV}-hidden-count"),
        "output": text_of(page, f"{NV}-output-count"),
        "conn": text_of(page, f"{NV}-connection-count"),
    }


def wait_for(pred, budget_s: float, every_s: float = 0.5, label: str = ""):
    """Poll a predicate for a TRANSITION; returns (ok, elapsed, last)."""
    t0 = time.time()
    last = None
    while time.time() - t0 < budget_s:
        last = pred()
        if last:
            return True, round(time.time() - t0, 1), last
        time.sleep(every_s)
    if label:
        log(f"  !! timed out after {budget_s}s waiting for {label} (last={last!r})")
    return False, round(time.time() - t0, 1), last


# --------------------------------------------------------------------------
# Widget idioms -- dcc.Dropdown / Checklist / RadioItems are NOT native selects
# --------------------------------------------------------------------------
def probe_control(page, el_id: str) -> dict:
    """Dump the real markup of one control so the driving idiom is pinned, not guessed."""
    return page.evaluate(
        """(id) => { const el = document.getElementById(id);
             if (!el) return {present:false};
             const inputs = [...el.querySelectorAll('input')].map(i => ({
                 type:i.type, value:i.value, checked:i.checked,
                 cls:(i.className||'').slice(0,60)}));
             return {present:true, tag:el.tagName, cls:(el.className||'').slice(0,120),
                     html:(el.innerHTML||'').slice(0,700), inputs:inputs,
                     text:(el.innerText||'').trim().slice(0,140)}; }""",
        el_id,
    )


def set_radio(page, el_id: str, value: str) -> bool:
    """dcc.RadioItems: click the input whose value matches. Verified by .checked."""
    return bool(
        page.evaluate(
            """([id, v]) => { const el = document.getElementById(id); if (!el) return false;
                 const inp = [...el.querySelectorAll('input[type=radio]')].find(i => i.value === v);
                 if (!inp) return false; inp.click(); return inp.checked; }""",
            [el_id, value],
        )
    )


def set_checklist(page, el_id: str, want_checked: bool) -> bool:
    """dcc.Checklist: click the checkbox only when its state differs (memory: checkbox=CLICK)."""
    return bool(
        page.evaluate(
            """([id, want]) => { const el = document.getElementById(id); if (!el) return false;
                 const inp = el.querySelector('input[type=checkbox]');
                 if (!inp) return false;
                 if (inp.checked !== want) inp.click();
                 return inp.checked === want; }""",
            [el_id, want_checked],
        )
    )


def dropdown_value(page, el_id: str):
    """Read the Dash-3 dropdown's displayed value off its own -value span."""
    return page.evaluate(
        """(id) => { const v = document.getElementById(id + '-value');
             return v ? (v.innerText || '').trim() : null; }""",
        el_id,
    )


def settle_figure(page, container_id: str = None, budget_s: float = 20.0, stable_reads: int = 3) -> dict:
    """Block until the plotly figure stops changing, then return its final state.

    THE reason M-TOPOLOGY-01 and -06 failed, and neither was a product defect.
    The topology rebuild takes 1.5-5 s and settles at 4-7 s on a 40-unit network
    (measured, `util/ad-hoc/e2e_m01_dropdown_probe.py`), while the driver waited
    1200-1500 ms and read. Everything downstream of that read was a race:

      * layouts appeared to render identically (Spring's figure hash matched
        Hierarchical's on a fast read and DIFFERED once settled), so
        ``distinct_sigs`` under-counted non-deterministically -- 3, then 2, then 3
        across three runs of an unchanged topology;
      * the next interaction landed while the page was still re-rendering, so the
        dropdown portal never opened and "Staggered" scored driven=False;
      * the depth-filter label and stats bar were read before the rebuild that
        would have updated them.

    Verified by EFFECT (the hash holding steady), never by a fixed sleep -- a
    fixed sleep is what produced the wrong readings in the first place.
    """
    container_id = container_id or f"{NV}-graph"
    prev, stable, waited = None, 0, 0.0
    info = {}
    while waited < budget_s and stable < stable_reads:
        page.wait_for_timeout(700)
        waited += 0.7
        info = fig_info(page, container_id) or {}
        cur = info.get("fig_hash")
        stable = stable + 1 if (cur is not None and cur == prev) else 0
        prev = cur
    n_traces = len(info.get("traces") or [])
    # STABLE IS NOT READY. An unpainted graph is perfectly stable -- hash constant,
    # zero traces -- so this returns "settled" while the page has not loaded its
    # topology yet. A caller that reads state off that gets all-zero counts and an
    # empty figure, and any verdict drawn from it is vacuous (observed: a probe
    # concluded "the widget could not move" when the page simply was not ready).
    # ``painted`` is reported so a caller cannot silently treat the two as the same.
    return {
        "fig_hash": prev,
        "settled_s": round(waited, 1),
        "settled": stable >= stable_reads,
        "painted": n_traces > 0,
        "traces": n_traces,
        "info": info,
    }


def set_dropdown(page, el_id: str, label: str) -> bool:
    """Dash 3 native dropdown: the control is a <button>; options render in a portal.

    NOT react-select -- the 2026-08-26 probe found ``tag=BUTTON cls='dash-dropdown'``
    with a ``.dash-dropdown-trigger`` span and the current value in ``#<id>-value``.
    Verified by EFFECT (the -value span changing), never by the click returning true.
    """
    before = dropdown_value(page, el_id)

    # SETTLE FIRST. A click that lands while the previous rebuild is still
    # re-rendering is swallowed -- the portal never opens, and the option query
    # then matches OTHER controls' options that are always in the DOM. That is
    # exactly how "Staggered" scored driven=False on every run while the three
    # layouts around it committed fine: it was simply the one whose turn came
    # soonest after a slow rebuild.
    settle_figure(page)

    clicked = {"ok": False}
    for attempt in range(3):
        page.evaluate("""(id) => { const b = document.getElementById(id); if (b) b.click(); }""", el_id)
        page.wait_for_timeout(700)
        clicked = page.evaluate(
            """([id, label]) => {
                 const sel = '[role=option], .dash-dropdown-option, [class*=dropdown-option], [role=menuitem]';
                 const opts = [...document.querySelectorAll(sel)];
                 const hit = opts.find(o => (o.textContent || '').trim() === label);
                 if (!hit) return {ok:false, seen: opts.map(o => (o.textContent||'').trim()).slice(0, 12)};
                 hit.click(); return {ok:true}; }""",
            [el_id, label],
        )
        if clicked.get("ok"):
            break
        # Not an error yet: the portal may not have opened. Close anything that
        # did open, let the page quiesce, and try again before declaring failure.
        log(f"  .. dropdown {el_id}: {label!r} absent on attempt {attempt + 1}; seen {clicked.get('seen')}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(900)

    if not clicked.get("ok"):
        log(f"  !! dropdown option {label!r} not found on {el_id} after 3 attempts; options seen: {clicked.get('seen')}")
        page.keyboard.press("Escape")
        return False

    # SETTLE AFTER too, so the caller's figure read reflects THIS selection rather
    # than the previous one still on screen.
    settle_figure(page)
    after = dropdown_value(page, el_id)
    if after != label:
        log(f"  !! dropdown {el_id} did not commit: {before!r} -> {after!r} (wanted {label!r})")
    return after == label


def slider_state(page, container_id: str, thumb_index: int = 0):
    """Read a Dash-3 (Radix) slider's value + bounds.

    Dash 3 ships Radix UI sliders (``.dash-slider-root`` / ``.dash-slider-track`` /
    a ``[role=slider]`` thumb) beside a companion ``input[type=number]`` -- there is
    NO ``.rc-slider-handle`` anywhere in the tree. That is the real reason the arc's
    rc-slider drag helper reported ``driven=False`` without erroring: it was looking
    for a widget this Dash version does not render.
    """
    return page.evaluate(
        """([id, i]) => { const root = document.getElementById(id); if (!root) return null;
             const thumbs = [...root.querySelectorAll('[role=slider]')];
             const num = root.querySelector('input[type=number]');
             const t = thumbs[i] || null;
             const rd = (el, a) => { const v = el && el.getAttribute(a); return v === null || v === undefined ? null : Number(v); };
             return {n_thumbs: thumbs.length,
                     now: t ? rd(t, 'aria-valuenow') : (num ? Number(num.value) : null),
                     min: t ? rd(t, 'aria-valuemin') : (num ? Number(num.min) : null),
                     max: t ? rd(t, 'aria-valuemax') : (num ? Number(num.max) : null),
                     num_value: num ? Number(num.value) : null,
                     num_min: num ? Number(num.min) : null,
                     num_max: num ? Number(num.max) : null}; }""",
        [container_id, thumb_index],
    )


def slider_value(page, container_id: str, thumb_index: int = 0):
    st = slider_state(page, container_id, thumb_index)
    return None if st is None else st.get("now")


def set_slider(page, container_id: str, target: int, thumb_index: int = 0, budget_s: float = 25, effect=None) -> dict:
    """Move a Dash-3 slider to ``target``, trying three idioms, verified by EFFECT.

    Idioms, in order of reliability on this widget: (1) the companion
    ``input[type=number]`` driven with the React native-value-setter (the arc's
    established idiom for React-controlled inputs); (2) keyboard arrows on the
    ``[role=slider]`` thumb, which Radix handles natively; (3) a mouse drag of the
    thumb along the track. Each is scored by re-reading the widget, never by the
    dispatch returning true.

    ``effect`` -- OPTIONAL predicate, and the reason M-TOPOLOGY-06 stayed stuck.
    Re-reading the widget proves the DOM moved; it does NOT prove **Dash** saw the
    value, and on this slider those come apart. Measured on the live 40-unit
    network: idiom 1 moved ``now`` 0 -> 20 and ``num_value`` 0 -> 20, so idiom 1
    "succeeded" and returned early — while the figure stayed byte-identical
    (``de463bff``, 1891 traces) and the depth label never changed, because
    ``-depth-slider.value`` never reached ``update_network_graph``. The DOM-only
    check thus SHORT-CIRCUITED the very fallbacks (keyboard, drag) that might have
    reached Dash.

    Pass ``effect`` to require an observable downstream change as well; an idiom
    that satisfies the DOM but not the effect is treated as a FAILURE and the next
    idiom is tried. Callers that only care about the widget can omit it and keep
    the old behaviour.
    """

    def _ok(idiom_name):
        """DOM must show the target, and (if given) the effect must have landed."""
        if slider_value(page, container_id, thumb_index) != target:
            return False
        if effect is None:
            return True
        landed = bool(effect())
        if not landed:
            log(f"  .. slider {container_id}: {idiom_name} moved the DOM but the effect did not land; trying the next idiom")
        return landed
    st = slider_state(page, container_id, thumb_index)
    out = {"target": target, "idiom": None, "before": st}
    if st is None:
        out["error"] = "container absent"
        return out
    lo, hi = st.get("min"), st.get("max")
    if lo is None or hi is None:
        out["error"] = "no bounds"
        return out
    if hi <= lo:
        out["error"] = f"slider has no range (min={lo} max={hi}) -- upstream data is empty, not a drive failure"
        return out
    target = int(max(lo, min(hi, target)))
    out["target"] = target

    # DRAG FIRST when the caller demands a downstream effect, because the ORDER is
    # itself a trap. dcc.Slider here is ``updatemode="mouseup"``: Dash is notified
    # only by a mouseup concluding a real drag, so the synthetic idioms below CANNOT
    # deliver the value by design. Worse, running them first moves the DOM to the
    # target, after which the drag computes a destination the thumb already occupies
    # and degenerates into a no-op gesture. That sequence made a WORKING control look
    # dead: measured, drag-first moves the figure de463bff -> ab8c6d50 (1891 -> 551
    # traces) and the stats bar 40 -> "20 of 40", while drag-after-synthetic changed
    # nothing at all.
    if effect is not None:
        frac0 = (target - lo) / float(hi - lo)
        box0 = page.evaluate(
            """(id) => { const r = document.querySelector('#' + id + ' .dash-slider-track');
                 if (!r) return null; const bb = r.getBoundingClientRect();
                 return {x: bb.x, y: bb.y, w: bb.width, h: bb.height}; }""",
            container_id,
        )
        thumb0 = page.locator(f"#{container_id} [role=slider]")
        if box0 and box0["w"] > 0 and thumb0.count() > thumb_index:
            hb0 = thumb0.nth(thumb_index).bounding_box()
            if hb0 and (st or {}).get("now") != target:
                cy0 = hb0["y"] + hb0["height"] / 2
                page.mouse.move(hb0["x"] + hb0["width"] / 2, cy0)
                page.mouse.down()
                page.mouse.move(box0["x"] + box0["w"] * frac0, cy0, steps=25)
                page.wait_for_timeout(250)
                page.mouse.up()
                page.wait_for_timeout(1200)
                if _ok("drag-first"):
                    out["idiom"] = "drag"
                    out["after"] = slider_state(page, container_id, thumb_index)
                    return out

    # Idiom 1 -- the companion number input, via the React native value setter.
    ok = page.evaluate(
        """([id, v]) => { const root = document.getElementById(id); if (!root) return false;
             const el = root.querySelector('input[type=number]'); if (!el) return false;
             const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
             setter.call(el, String(v));
             el.dispatchEvent(new Event('input', {bubbles:true}));
             el.dispatchEvent(new Event('change', {bubbles:true}));
             el.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', bubbles:true}));
             el.blur();
             return true; }""",
        [container_id, target],
    )
    if ok:
        page.wait_for_timeout(1500)
        if _ok("number-input"):
            out["idiom"] = "number-input"
            out["after"] = slider_state(page, container_id, thumb_index)
            return out

    # Idiom 2 -- keyboard arrows on the Radix thumb.
    page.evaluate(
        """([id, i]) => { const root = document.getElementById(id); if (!root) return;
             const t = root.querySelectorAll('[role=slider]')[i]; if (t) t.focus(); }""",
        [container_id, thumb_index],
    )
    t0 = time.time()
    guard = 0
    while time.time() - t0 < budget_s and guard < 200:
        cur = slider_value(page, container_id, thumb_index)
        if cur is None or cur == target:
            break
        page.keyboard.press("ArrowRight" if cur < target else "ArrowLeft")
        page.wait_for_timeout(120)
        guard += 1
    if _ok("keyboard"):
        out["idiom"] = "keyboard"
        out["after"] = slider_state(page, container_id, thumb_index)
        return out

    # Idiom 3 -- drag the thumb along the track.
    frac = (target - lo) / float(hi - lo)
    box = page.evaluate(
        """(id) => { const r = document.querySelector('#' + id + ' .dash-slider-track');
             if (!r) return null; const bb = r.getBoundingClientRect();
             return {x: bb.x, y: bb.y, w: bb.width, h: bb.height}; }""",
        container_id,
    )
    thumb = page.locator(f"#{container_id} [role=slider]")
    if box and box["w"] > 0 and thumb.count() > thumb_index:
        hb = thumb.nth(thumb_index).bounding_box()
        if hb:
            cy = hb["y"] + hb["height"] / 2
            page.mouse.move(hb["x"] + hb["width"] / 2, cy)
            page.mouse.down()
            page.mouse.move(box["x"] + box["w"] * frac, cy, steps=15)
            page.mouse.up()
            page.wait_for_timeout(1200)
    out["after"] = slider_state(page, container_id, thumb_index)
    if _ok("drag"):
        out["idiom"] = "drag"
    elif (out["after"] or {}).get("now") == target:
        # The widget reached the target but no idiom made Dash observe it. Say so
        # explicitly rather than reporting a bare idiom=None, which reads as "the
        # slider would not move" and sent this row's diagnosis the wrong way once.
        out["dom_only"] = True
        out["error"] = "widget reached the target in the DOM, but no idiom produced the downstream effect (Dash never received the value)"
    return out


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
def step_probe(page, capture):
    """Pin the real markup of every topology control before scoring any row."""
    log("STEP probe -- real DOM shape of the topology controls")
    attach_captures(page)
    open_tab(page, "Network Topology")
    page.wait_for_timeout(4000)
    out = {}
    for cid in ("layout-selector", "show-weights", "display-mode", "view-mode", "depth-slider", "depth-slider-container"):
        out[cid] = probe_control(page, f"{NV}-{cid}")
        p = out[cid]
        if p.get("present"):
            log(f"  {cid}: tag={p['tag']} cls={p['cls'][:50]!r} inputs={p['inputs']}")
        else:
            log(f"  {cid}: ABSENT")
    out["counts"] = counts(page)
    out["depth_bounds"] = slider_state(page, f"{NV}-depth-slider")
    out["graph"] = fig_info(page, f"{NV}-graph")
    log(f"  counts={out['counts']}  depth_bounds={out['depth_bounds']}")
    g = out["graph"]
    log(f"  graph: plotly={g.get('plotly')} traces={len(g.get('traces') or [])} modebar={g.get('modebar')} sig={g.get('sig')}")
    for cid in ("layout-selector", "display-mode", "view-mode"):
        h = (out[cid].get("html") or "")[:300]
        log(f"  --- {cid} html --- {h!r}")
    record("probe", **{k: v for k, v in out.items() if k in ("counts", "depth_bounds")})
    with open(os.path.join(RUN_DIR, "seg17_probe.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    log(f"  full probe -> {os.path.join(RUN_DIR, 'seg17_probe.json')}")


def _store(page, store_id: str):
    """Read a dcc.Store's data off the renderer (stores render no DOM)."""
    return page.evaluate(
        """(id) => { try {
             const ctx = window.dash_component_api || null;
             const el = document.getElementById(id);
             if (el && el._dashprivate_layout) return el._dashprivate_layout.props.data;
           } catch (e) {}
           try {
             const st = window.store && window.store.getState ? window.store.getState() : null;
             if (!st || !st.layout) return '<no redux layout>';
             const walk = (n) => { if (!n || typeof n !== 'object') return null;
               if (n.props && n.props.id === id) return n.props.data === undefined ? null : n.props.data;
               const ch = n.props && n.props.children;
               const arr = Array.isArray(ch) ? ch : (ch ? [ch] : []);
               for (const c of arr) { const r = walk(c); if (r !== null && r !== undefined) return r; }
               return null; };
             return walk(st.layout);
           } catch (e) { return '<err ' + e.message + '>'; } }""",
        store_id,
    )


def step_topodiag(page, capture):
    """Why is the topology graph empty? Separate 'backend wrong' from 'render late'.

    The arc's standing trap (handoff): a fix's live render lagging or blanking during
    a congested run is F-CANOPY-004, not a regression -- so establish the MECHANISM
    (API correct? store filled? tab actually active?) before any row is scored.
    """
    log("STEP topodiag -- why the topology graph is empty")
    attach_captures(page)
    t_enter = time.time()
    opened = open_tab(page, "Network Topology")
    log(f"  open_tab returned {opened}; active tab now {_p1_active_tab(page)!r}")

    api = http_get("/api/topology", timeout=60)[1]
    server = {
        "input_units": api.get("input_units"),
        "hidden_units": api.get("hidden_units"),
        "output_units": api.get("output_units"),
        "n_nodes": len(api.get("nodes") or []),
        "n_conns": len(api.get("connections") or api.get("edges") or []),
    }
    log(f"  SERVER /api/topology: {server}")

    # Poll for a TRANSITION with a long budget -- F-CANOPY-004 renders land 3-16 s
    # after an interaction and 20-40 s on a fresh session; 240 s is well past both.
    def painted():
        c = counts(page)
        g = fig_info(page, f"{NV}-graph")
        return c["hidden"] not in ("0", None) or (g.get("sig") or 0) > 8

    ok, elapsed, _ = wait_for(painted, budget_s=240, every_s=3.0, label="topology graph to paint")
    c = counts(page)
    g = fig_info(page, f"{NV}-graph")
    store = _store(page, f"{NV}-topology-store")
    st_kind = type(store).__name__
    st_summary = store if not isinstance(store, dict) else {k: (len(v) if isinstance(v, list) else v) for k, v in store.items()}
    hits = api_hits("/api/topology", t_enter)
    log(f"  painted={ok} after {elapsed}s; counts={c}")
    log(f"  graph: traces={len(g.get('traces') or [])} sig={g.get('sig')} plotly={g.get('plotly')}")
    log(f"  topology-store ({st_kind}): {str(st_summary)[:300]}")
    log(f"  browser /api/topology hits since tab entry: {len(hits)} -> {[h['status'] for h in hits][:8]}")
    log(f"  depth slider: {slider_state(page, f'{NV}-depth-slider')}")
    shot(page, "seg17_topodiag.png")

    verdict = "PASS" if ok else "FAIL"
    record(
        "topodiag",
        verdict=verdict,
        server=server,
        counts=c,
        traces=len(g.get("traces") or []),
        sig=g.get("sig"),
        store=st_summary,
        api_hits=len(hits),
        elapsed_s=elapsed,
        depth=slider_state(page, f"{NV}-depth-slider"),
    )


def _p1_active_tab(page):
    return page.evaluate("""() => { const t = document.querySelector('[role=tab].active'); return t ? t.textContent.trim() : null; }""")


def step_rebuildprobe(page, capture):
    """Intercept the rebuild callback itself: does it fire, and what does it return?

    Every dash POST body names its output, so the rebuild
    (``network-visualizer-graph.figure``) is identifiable on the wire without
    touching the page. This is the instrument that exonerated the server in the
    original F-CANOPY-006 isolation; re-running it says whether the current empty
    graph is a server render that is never applied (the F-006 signature) or a
    callback that never executes at all (a different, new mechanism).
    """
    log("STEP rebuildprobe -- intercept network-visualizer-graph.figure on the wire")
    seen: list = []
    bodies: dict = {}

    # Stash each POST body on the REQUEST event. Reading ``resp.request.post_data``
    # inside the response handler silently yielded nothing on this build (the first
    # cut of this probe reported 0 rebuilds while the wire census counted 12) --
    # so the request side is the reliable capture point and the response handler
    # only joins to it.
    def on_request(req):
        if "_dash-update-component" in req.url and req.method == "POST":
            try:
                bodies[req] = req.post_data or ""
            except Exception:  # noqa: BLE001
                pass

    def on_response(resp):
        body = bodies.pop(resp.request, None)
        if body is None or f"{NV}-graph" not in body:
            return
        rec = {"t": time.time(), "status": resp.status, "req_len": len(body)}
        try:
            payload = json.loads(body)
            out = payload.get("output")
            rec["output"] = out if isinstance(out, str) else str(out)[:160]
            rec["changed"] = [c.get("prop_id") for c in (payload.get("changedPropIds") or [])] or payload.get("changedPropIds")
            inputs = payload.get("inputs") or []
            rec["n_inputs"] = len(inputs)
            for i in inputs:
                pid = i.get("id")
                if pid == f"{NV}-topology-store":
                    v = i.get("value")
                    rec["in_store"] = None if v is None else {
                        "hidden_units": (v or {}).get("hidden_units"),
                        "n_nodes": len((v or {}).get("nodes") or []),
                    }
                if pid == f"{NV}-depth-slider":
                    rec["in_depth"] = i.get("value")
        except Exception as exc:  # noqa: BLE001
            rec["parse_error"] = str(exc)[:120]
        try:
            txt = resp.text()
            rec["resp_len"] = len(txt)
            rec["n_traces"] = txt.count('"type":')
            rec["empty_fig"] = '"data":[]' in txt.replace(" ", "")
            rec["resp_head"] = txt[:200]
        except Exception as exc:  # noqa: BLE001
            rec["resp_error"] = str(exc)[:120]
        seen.append(rec)

    page.on("request", on_request)
    page.on("response", on_response)
    attach_captures(page)

    watch_s = int(os.environ.get("JUNIPER_E2E_REBUILD_WATCH_S", "120"))
    stop_after = int(os.environ.get("JUNIPER_E2E_REBUILD_STOP_AFTER", "3"))
    open_tab(page, "Network Topology")
    log(f"  topology tab active; watching the wire for {watch_s}s (stop_after={stop_after})")
    t0 = time.time()
    marks: list = []
    while time.time() - t0 < watch_s:
        page.wait_for_timeout(2000)
        # Sample the DOM alongside the wire so a TRANSIENT paint (rendered, then
        # cleared) is distinguishable from one that never lands at all.
        if int(time.time() - t0) % 10 < 2:
            g = fig_info(page, f"{NV}-graph")
            marks.append({"t": round(time.time() - t0, 1), "sig": g.get("sig"), "hidden": text_of(page, f"{NV}-hidden-count")})
        if stop_after and len(seen) >= stop_after:
            break

    if marks:
        log("  DOM sig timeline: " + ", ".join(f"{m['t']}s:sig={m['sig']}/h={m['hidden']}" for m in marks[:18]))
    log(f"  rebuild POSTs naming {NV}-graph: {len(seen)}")
    for r in seen[:6]:
        log(
            f"    status={r.get('status')} req={r.get('req_len')}B resp={r.get('resp_len')}B "
            f"traces~{r.get('n_traces')} empty_fig={r.get('empty_fig')} "
            f"store={r.get('in_store')} depth={r.get('in_depth')} changed={r.get('changed')}"
        )
        if r.get("resp_head"):
            log(f"      resp_head: {r['resp_head'][:180]!r}")
    g = fig_info(page, f"{NV}-graph")
    c = counts(page)
    log(f"  DOM after: counts={c} traces={len(g.get('traces') or [])} sig={g.get('sig')}")
    record(
        "rebuildprobe",
        n_rebuild_posts=len(seen),
        posts=seen[:6],
        dom_counts=c,
        dom_traces=len(g.get("traces") or []),
        dom_sig=g.get("sig"),
    )
    with open(os.path.join(RUN_DIR, "seg17_rebuildprobe.json"), "w", encoding="utf-8") as fh:
        json.dump(seen, fh, indent=2, default=str)
    log(f"  full capture -> {os.path.join(RUN_DIR, 'seg17_rebuildprobe.json')}")


def step_wirecensus(page, capture):
    """Census EVERY dash callback POST on the topology tab, by output.

    Separates "the whole callback lane is dead" from "only the rebuild never runs",
    and reads the ``tabpoll-topology`` interval's own ``disabled`` prop -- the gate
    the F-CANOPY-027 remediation put in front of the rebuild.
    """
    log("STEP wirecensus -- every dash POST output on the topology tab")
    outputs: dict = {}

    def on_request(req):
        if "_dash-update-component" not in req.url or req.method != "POST":
            return
        try:
            payload = json.loads(req.post_data or "{}")
        except Exception:  # noqa: BLE001
            return
        out = payload.get("output")
        key = out if isinstance(out, str) else str(out)
        outputs[key] = outputs.get(key, 0) + 1

    page.on("request", on_request)
    attach_captures(page)

    def interval_state(iid: str):
        return page.evaluate(
            """(id) => { const st = window.store && window.store.getState ? window.store.getState() : null;
                 if (!st || !st.layout) return '<no redux>';
                 const walk = (n) => { if (!n || typeof n !== 'object') return undefined;
                   if (n.props && n.props.id === id) return {disabled: n.props.disabled, interval: n.props.interval, n: n.props.n_intervals};
                   const ch = n.props && n.props.children;
                   const arr = Array.isArray(ch) ? ch : (ch ? [ch] : []);
                   for (const c of arr) { const r = walk(c); if (r !== undefined) return r; }
                   return undefined; };
                 const r = walk(st.layout); return r === undefined ? '<not found>' : r; }""",
            iid,
        )

    log(f"  before tab: tabpoll-topology = {interval_state('tabpoll-topology')}")
    open_tab(page, "Network Topology")
    page.wait_for_timeout(4000)
    log(f"  after tab : tabpoll-topology = {interval_state('tabpoll-topology')}")
    log(f"  active tab: {_p1_active_tab(page)!r}")

    outputs.clear()
    log("  counting dash POSTs for 60 s ...")
    page.wait_for_timeout(60000)

    ranked = sorted(outputs.items(), key=lambda kv: -kv[1])
    log(f"  distinct callback outputs seen: {len(ranked)} (total POSTs {sum(outputs.values())})")
    for k, v in ranked[:25]:
        log(f"    {v:>4}x  {k[:150]}")
    if not ranked:
        log("  !! ZERO dash callback POSTs -- the whole callback lane is silent on this tab")
    nv_outs = [k for k in outputs if NV in k]
    log(f"  outputs mentioning {NV}: {len(nv_outs)} -> {[k[:100] for k in nv_outs][:6]}")
    record(
        "wirecensus",
        total_posts=sum(outputs.values()),
        distinct=len(ranked),
        top=[{"output": k[:200], "n": v} for k, v in ranked[:25]],
        nv_outputs=[k[:200] for k in nv_outs],
        tabpoll=interval_state("tabpoll-topology"),
    )


def step_quietread(page, capture):
    """Open the tab, wait in SILENCE, then read the DOM exactly once.

    Controlled against ``topodiag``, which is identical except that it polls the DOM
    (4x text_of + a JSON.stringify-ing fig_info) every 3 s. topodiag reports an empty
    graph for 245 s; ``rebuildprobe``, which only waits and watches the wire, sees the
    same graph painted in ~22 s. If this step -- same wait, zero evaluates -- paints,
    then the POLLING is the suppressor and every row this arc scored by polling a
    live DOM needs re-reading with a quiet instrument.
    """
    wait_s = int(os.environ.get("JUNIPER_E2E_QUIET_WAIT_S", "90"))
    log(f"STEP quietread -- open tab, wait {wait_s}s with NO evaluates, read once")
    open_tab(page, "Network Topology")
    log(f"  tab open; sleeping {wait_s}s in silence")
    page.wait_for_timeout(wait_s * 1000)
    c = counts(page)
    g = fig_info(page, f"{NV}-graph")
    painted = c["hidden"] not in ("0", None) or (g.get("sig") or 0) > 8
    log(f"  SINGLE read: counts={c} traces={len(g.get('traces') or [])} sig={g.get('sig')} painted={painted}")
    shot(page, "seg17_quietread.png")
    record("quietread", verdict="PASS" if painted else "FAIL", wait_s=wait_s, counts=c, traces=len(g.get("traces") or []), sig=g.get("sig"))


def _graph(page):
    return fig_info(page, f"{NV}-graph")


def _painted(page) -> bool:
    g = _graph(page)
    return (g.get("sig") or 0) > 8


def wake_topology(page, budget_s: float = 90) -> dict:
    """Force the topology rebuild by TOUCHING one of its own Inputs.

    The tab-poll lane is intermittently starved (measured 2026-08-26: 0 rebuild POSTs
    in 180 s in one session, 12 in 60 s in another, on the same quiescent stack), so
    waiting for the poll is not a reliable way to reach a painted graph. But
    ``update_network_graph`` takes ``show-weights``/``layout-selector``/``view-mode``/
    ``display-mode``/``depth-slider`` as direct Inputs, so a user interaction drives
    it without depending on the poll at all -- which is also exactly what the
    M-TOPOLOGY rows do. Toggling show-weights off-and-on is value-neutral.
    """
    out = {"already": _painted(page), "woke": False, "elapsed_s": None}
    if out["already"]:
        out["woke"] = True
        out["elapsed_s"] = 0.0
        return out
    t0 = time.time()
    for attempt in range(3):
        set_checklist(page, f"{NV}-show-weights", False)
        page.wait_for_timeout(1500)
        set_checklist(page, f"{NV}-show-weights", True)
        ok, elapsed, _ = wait_for(lambda: _painted(page), budget_s=budget_s / 3, every_s=2.0)
        if ok:
            out["woke"] = True
            out["elapsed_s"] = round(time.time() - t0, 1)
            out["attempts"] = attempt + 1
            return out
    out["elapsed_s"] = round(time.time() - t0, 1)
    return out


def step_topo(page, capture):
    """M-TOPOLOGY-01..09/16..18 and W4-02..10: the topology control surface."""
    log("STEP topo -- the topology control surface")
    attach_captures(page)
    res: dict = {}

    api = http_get("/api/topology", timeout=60)[1]
    server = {
        "input": str(api.get("input_units")),
        "hidden": str(api.get("hidden_units")),
        "output": str(api.get("output_units")),
        "conn": str(len(api.get("connections") or api.get("edges") or [])),
    }
    log(f"  SERVER truth: {server}")

    open_tab(page, "Network Topology")
    wake = wake_topology(page)
    log(f"  wake_topology: {wake}")
    res["wake"] = wake
    if not wake["woke"]:
        log("  !! graph never painted even after driving its own Inputs -- rows stay BLOCKED")
        record("topo", verdict="BLOCKED", reason="graph never painted", wake=wake, server=server)
        return

    base = _graph(page)
    c = counts(page)
    log(f"  painted: counts={c} traces={len(base.get('traces') or [])} sig={base.get('sig')} annotations={len(base.get('annotations') or [])}")

    # M-TOPOLOGY-08 / W1-14 -- stats bar equals server truth.
    m08 = c == server
    res["M-TOPOLOGY-08"] = {"verdict": "PASS" if m08 else "FAIL", "dom": c, "server": server}
    log(f"  M-TOPOLOGY-08 stats bar == server: {m08} ({c} vs {server})")

    # M-TOPOLOGY-01 / W4-02 -- cycle all four layouts; counts must not change.
    layouts = ["Hierarchical", "Staggered", "Spring", "Circular"]
    lay: dict = {}
    for name in layouts:
        ok = set_dropdown(page, f"{NV}-layout-selector", name)
        wait_for(lambda: _painted(page), budget_s=30, every_s=2.0)
        st = settle_figure(page)  # read only once the figure has stopped changing
        g = _graph(page)
        lay[name] = {
            "driven": ok, "sig": g.get("sig"), "fig_hash": g.get("fig_hash"),
            "traces": len(g.get("traces") or []), "counts": counts(page),
            "settled_s": st.get("settled_s"), "settled": st.get("settled"),
        }
        log(f"    layout {name}: driven={ok} sig={g.get('sig')} hash={g.get('fig_hash')} settled={st.get('settled_s')}s traces={lay[name]['traces']} counts={lay[name]['counts']}")

    driven = [v for v in lay.values() if v["driven"]]
    counts_stable = all(v["counts"] == server for v in driven)
    # Distinctness is judged on the CONTENT HASH, not on ``sig``. ``sig`` is a byte
    # LENGTH, and two different layouts collided on it — which is what made this
    # row's distinct count wobble 3 -> 2 -> 3 across runs of an unchanged topology.
    # Only DRIVEN layouts are compared: an undriven one still shows the previous
    # layout's figure and would read as a false duplicate.
    hashes = {v["fig_hash"] for v in driven if v["fig_hash"] is not None}
    relaid = len(hashes) > 1
    res["M-TOPOLOGY-01"] = {
        "verdict": "PASS" if (len(driven) == 4 and relaid and counts_stable) else "FAIL",
        "driven": len(driven), "distinct_figs": len(hashes),
        "distinct_sigs": len({v["sig"] for v in driven}),  # kept for continuity with older runs
        "counts_stable": counts_stable, "detail": lay,
    }
    log(f"  M-TOPOLOGY-01 layouts: driven={len(driven)}/4 distinct_figs={len(hashes)} (sigs={len({v['sig'] for v in driven})}) counts_stable={counts_stable}")
    set_dropdown(page, f"{NV}-layout-selector", "Hierarchical")
    page.wait_for_timeout(2000)

    # M-TOPOLOGY-02 / W4-03 -- show-weights off then on.
    on_g = _graph(page)
    set_checklist(page, f"{NV}-show-weights", False)
    page.wait_for_timeout(3000)
    wait_for(lambda: _graph(page).get("sig") != on_g.get("sig"), budget_s=30, every_s=2.0)
    off_g = _graph(page)
    set_checklist(page, f"{NV}-show-weights", True)
    page.wait_for_timeout(3000)
    wait_for(lambda: _graph(page).get("sig") != off_g.get("sig"), budget_s=30, every_s=2.0)
    back_g = _graph(page)
    m02 = off_g.get("sig") != on_g.get("sig") and back_g.get("sig") != off_g.get("sig")
    res["M-TOPOLOGY-02"] = {
        "verdict": "PASS" if m02 else "FAIL",
        "on_sig": on_g.get("sig"), "off_sig": off_g.get("sig"), "back_sig": back_g.get("sig"),
        "on_ann": len(on_g.get("annotations") or []), "off_ann": len(off_g.get("annotations") or []),
    }
    log(f"  M-TOPOLOGY-02 show-weights: on={on_g.get('sig')} off={off_g.get('sig')} back={back_g.get('sig')} -> {m02}")

    # M-TOPOLOGY-03 / W4-06 -- Weight Matrix heatmap; connection-count reads the em dash.
    set_radio(page, f"{NV}-display-mode", "weight_matrix")
    page.wait_for_timeout(3000)
    wait_for(lambda: any((t.get("type") == "heatmap") for t in (_graph(page).get("traces") or [])), budget_s=45, every_s=2.0)
    wm = _graph(page)
    wm_counts = counts(page)
    is_heat = any(t.get("type") == "heatmap" for t in (wm.get("traces") or []))
    res["M-TOPOLOGY-03"] = {
        "verdict": "PASS" if is_heat else "FAIL",
        "heatmap": is_heat, "types": [t.get("type") for t in (wm.get("traces") or [])][:6],
        "connection_count": wm_counts["conn"],
    }
    log(f"  M-TOPOLOGY-03 weight matrix: heatmap={is_heat} types={res['M-TOPOLOGY-03']['types']} conn={wm_counts['conn']!r}")

    # M-TOPOLOGY-04 / W4-07 -- back to Node Graph, connection count restored.
    set_radio(page, f"{NV}-display-mode", "node_graph")
    page.wait_for_timeout(3000)
    wait_for(lambda: counts(page)["conn"] == server["conn"], budget_s=45, every_s=2.0)
    ng_counts = counts(page)
    m04 = ng_counts == server
    res["M-TOPOLOGY-04"] = {"verdict": "PASS" if m04 else "FAIL", "counts": ng_counts, "server": server}
    log(f"  M-TOPOLOGY-04 back to node graph: counts={ng_counts} -> {m04}")

    # M-TOPOLOGY-05 / W4-04 -- 3-D scene.
    set_radio(page, f"{NV}-view-mode", "3d")
    page.wait_for_timeout(3000)
    wait_for(lambda: any(str(t.get("type", "")).endswith("3d") for t in (_graph(page).get("traces") or [])), budget_s=45, every_s=2.0)
    g3 = _graph(page)
    is3d = any(str(t.get("type", "")).endswith("3d") for t in (g3.get("traces") or []))
    res["M-TOPOLOGY-05"] = {"verdict": "PASS" if is3d else "FAIL", "types": [t.get("type") for t in (g3.get("traces") or [])][:6]}
    log(f"  M-TOPOLOGY-05 3-D: {is3d} types={res['M-TOPOLOGY-05']['types']}")
    set_radio(page, f"{NV}-view-mode", "2d")
    page.wait_for_timeout(3000)

    # M-TOPOLOGY-07 / W4-08 -- depth container visible, label reads "all".
    dv = vis(page, f"{NV}-depth-slider-container")
    dlabel = text_of(page, f"{NV}-depth-label")
    m07 = dv.get("display") not in (None, "none")
    res["M-TOPOLOGY-07"] = {"verdict": "PASS" if m07 else "FAIL", "display": dv.get("display"), "label": dlabel}
    log(f"  M-TOPOLOGY-07 depth container: display={dv.get('display')!r} label={dlabel!r}")

    # M-TOPOLOGY-06 / W4-09 -- filter to k < N.
    n_hidden = int(server["hidden"]) if server["hidden"].isdigit() else 0
    k = max(1, n_hidden // 2)
    want = f"{k} of {n_hidden}"
    before_hash = (_graph(page) or {}).get("fig_hash")

    # Require the DOWNSTREAM effect, not just the widget. ``-depth-slider.value``
    # is a real Input of update_network_graph, so a value Dash actually received
    # must change the figure. Without this the number-input idiom "succeeds" on a
    # DOM-only move and set_slider returns before trying keyboard or drag — which
    # is precisely why this row read idiom=number-input while the figure, label and
    # stats bar were all unchanged.
    def _depth_landed():
        st = settle_figure(page, budget_s=12)
        return bool(st.get("painted")) and st.get("fig_hash") not in (None, before_hash)

    sl = set_slider(page, f"{NV}-depth-slider", k, effect=_depth_landed)

    # The old wait was VACUOUS: it waited for the label to become != "all", but the
    # label is "0 of N" at rest (the slider sits at 0), so the predicate was already
    # true on entry and it returned instantly without waiting for anything. It then
    # read the label and counts inside the 1.5-5 s rebuild window and scored the
    # stale values -- which is why this row reported label='0 of 40' hidden='40'
    # even though set_slider had VERIFIED the widget reached the target.
    #
    # Wait for the thing that actually signals the change: the label reaching the
    # wanted text, or the figure settling on a hash different from the pre-drive
    # one. Either is a real transition; neither is true on entry.
    wait_for(
        lambda: (text_of(page, f"{NV}-depth-label") or "") == want
        or ((_graph(page) or {}).get("fig_hash") not in (None, before_hash)),
        budget_s=45,
        every_s=2.0,
    )
    settle_figure(page)
    k_label = text_of(page, f"{NV}-depth-label")
    k_counts = counts(page)
    m06 = sl.get("idiom") is not None and (k_label == want or k_counts["hidden"] == want)
    res["M-TOPOLOGY-06"] = {
        "verdict": "PASS" if m06 else "FAIL",
        "slider": sl, "label": k_label, "hidden_count": k_counts["hidden"], "want": want,
    }
    log(f"  M-TOPOLOGY-06 depth={k}: idiom={sl.get('idiom')} label={k_label!r} hidden={k_counts['hidden']!r} want={want!r}")

    # RESET THE FILTER, AND VERIFY IT LANDED. This reset already existed but was
    # called without an ``effect``, so it used the synthetic idioms that cannot
    # satisfy ``updatemode="mouseup"``: the DOM went back to 0 while Dash kept 20.
    # That did not matter while M-TOPOLOGY-06 was broken and never applied a filter
    # in the first place — every earlier PASS of M-TOPOLOGY-17 was only valid
    # BECAUSE of that. The moment M-06 started working, the filtered state leaked
    # into M-17, which read hidden="20 of 40" / conn=274 against a server truth of
    # 40 / 944 and failed. Fixing one row exposed an ordering dependency that had
    # been there the whole time.
    filtered_hash = (_graph(page) or {}).get("fig_hash")

    def _reset_landed():
        s = settle_figure(page, budget_s=12)
        return bool(s.get("painted")) and s.get("fig_hash") not in (None, filtered_hash)

    reset = set_slider(page, f"{NV}-depth-slider", 0, effect=_reset_landed)
    settle_figure(page)
    reset_counts = counts(page)
    if reset_counts != server:
        # Say so loudly rather than letting the next row inherit a filtered graph
        # and report a defect that belongs to this one.
        log(f"  !! depth filter did NOT reset (idiom={reset.get('idiom')}): counts={reset_counts} vs server={server}")
        log("     downstream rows in this step will be reading a FILTERED graph")

    # M-TOPOLOGY-17 -- the store refreshes on tab re-entry.
    open_tab(page, "Training Metrics")
    page.wait_for_timeout(3000)
    open_tab(page, "Network Topology")
    ok17, el17, _ = wait_for(lambda: counts(page) == server, budget_s=90, every_s=2.0)
    res["M-TOPOLOGY-17"] = {"verdict": "PASS" if ok17 else "FAIL", "elapsed_s": el17, "counts": counts(page)}
    log(f"  M-TOPOLOGY-17 re-entry refresh: {ok17} after {el17}s")

    shot(page, "seg17_topo.png")
    passes = sum(1 for k2, v in res.items() if isinstance(v, dict) and v.get("verdict") == "PASS")
    log(f"  topo verdicts: {[(k2, v.get('verdict')) for k2, v in res.items() if isinstance(v, dict) and 'verdict' in v]}")
    record("topo", verdict=f"{passes} PASS", server=server, **res)


def step_storestorm(page, capture):
    """Is ``metrics-panel-metrics-store`` rewritten with IDENTICAL data post-run?

    ``update_network_graph`` takes that store as one of its 12 Inputs (the source
    comment says so explicitly: "still chained off metrics-panel-metrics-store (a
    global 1 Hz store), so gating the interval reduces but does not eliminate its
    off-tab work -- that chained-store class is Stage 2"). If the store is rewritten
    ~1/s with identical content on a COMPLETED run, the rebuild's Input is
    permanently claimed by a pending feeder and the render can only land when it
    wins the race -- which is exactly the intermittency measured here (rendered in
    2 of 8 sessions; correct and fast when it did).

    Counts writes and compares successive response bodies to separate a real data
    stream from a no-op rewrite storm.
    """
    watch_s = int(os.environ.get("JUNIPER_E2E_STORM_WATCH_S", "60"))
    log(f"STEP storestorm -- metrics-store rewrite census over {watch_s}s")
    bodies: dict = {}
    writes: list = []
    target = "metrics-panel-metrics-store"

    def on_request(req):
        if "_dash-update-component" in req.url and req.method == "POST":
            try:
                bodies[req] = req.post_data or ""
            except Exception:  # noqa: BLE001
                pass

    def on_response(resp):
        body = bodies.pop(resp.request, None)
        if body is None:
            return
        try:
            out = json.loads(body).get("output")
        except Exception:  # noqa: BLE001
            return
        out_s = out if isinstance(out, str) else str(out)
        if target not in out_s:
            return
        try:
            txt = resp.text()
        except Exception:  # noqa: BLE001
            return
        writes.append({"t": round(time.time(), 2), "len": len(txt), "hash": hash(txt), "no_update": '"no_update"' in txt or txt.strip() in ("{}", '{"multi":true,"response":{}}')})

    page.on("request", on_request)
    page.on("response", on_response)

    open_tab(page, "Network Topology")
    log(f"  topology tab active; counting {target} writes for {watch_s}s")
    page.wait_for_timeout(watch_s * 1000)

    n = len(writes)
    dup = 0
    for a, b in zip(writes, writes[1:]):
        if a["hash"] == b["hash"]:
            dup += 1
    n_noupd = sum(1 for w in writes if w["no_update"])
    rate = round(n / float(watch_s), 2)
    log(f"  {target} writes: {n} in {watch_s}s ({rate}/s); identical-to-previous: {dup}; no_update: {n_noupd}")
    if writes:
        log(f"  body lengths (first 12): {[w['len'] for w in writes[:12]]}")
    g = _graph(page)
    log(f"  graph now: sig={g.get('sig')} traces={len(g.get('traces') or [])} counts={counts(page)}")
    record(
        "storestorm",
        writes=n, rate_per_s=rate, identical_consecutive=dup, no_update=n_noupd,
        watch_s=watch_s, graph_sig=g.get("sig"), counts=counts(page),
    )


def step_f031(page, capture):
    """The owed F-CANOPY-031 driver step: the panel renders against the live corpus.

    F-031 is FIXED (canopy#517) but its driver probes were lost to /tmp, so the
    closure has never been re-driven from a script. Checks the panel leaves
    "Loading snapshots..." and renders bounded rows against the full corpus, and
    re-checks the SECOND defect the original finding flagged: ``data-snapshot-row``
    / ``data-snapshot-id``, which `snapshot_context_menu.js:29-30` needs to build
    its menu, appeared on ZERO elements (M-SNAPSHOTS-19's blocker).
    """
    log("STEP f031 -- snapshots panel against the live corpus")
    attach_captures(page)
    api = http_get("/api/v1/snapshots?limit=3&offset=0", timeout=120)[1]
    total = api.get("total")
    log(f"  SERVER total={total}, limit=3 returned {len(api.get('snapshots') or [])}")

    open_tab(page, "Snapshots")
    SNAP = "hdf5-snapshots-panel"

    def rows_rendered():
        return page.evaluate(
            """(sid) => { const b = document.getElementById(sid + '-table-body');
                 return b ? b.querySelectorAll('tr').length : -1; }""",
            SNAP,
        )

    ok, elapsed, _ = wait_for(lambda: (rows_rendered() or 0) > 0, budget_s=120, every_s=2.0, label="snapshot rows")
    n_rows = rows_rendered()
    status_txt = text_of(page, f"{SNAP}-status") or ""
    empty_state = vis(page, f"{SNAP}-empty-state")
    log(f"  rows={n_rows} after {elapsed}s; status={status_txt[:120]!r}; empty_state.display={empty_state.get('display')}")

    # The second defect flagged by the original finding.
    attrs = page.evaluate(
        """() => ({row: document.querySelectorAll('[data-snapshot-row]').length,
                  id: document.querySelectorAll('[data-snapshot-id]').length})"""
    )
    log(f"  context-menu attributes present on: data-snapshot-row={attrs['row']} data-snapshot-id={attrs['id']}")

    stuck_loading = "loading" in status_txt.lower()
    verdict = "PASS" if (ok and n_rows > 0 and not stuck_loading) else "FAIL"
    log(f"  f031 -> {verdict} (rows={n_rows}, stuck_loading={stuck_loading})")
    shot(page, "seg17_f031.png")
    record(
        "f031", verdict=verdict, server_total=total, rows=n_rows, elapsed_s=elapsed,
        status_text=status_txt[:200], empty_state_display=empty_state.get("display"),
        ctx_menu_attrs=attrs,
    )


def step_theme(page, capture):
    """M-DATASET-14: the Dataset View stats summary recolours on a theme flip.

    Scored on the COMPUTED colours of the element itself, not on the toggle's own
    state -- F-CANOPY-001 (open) is precisely a toggle whose glyph desyncs from the
    store, so the toggle reporting "dark" proves nothing about what rendered.
    """
    log("STEP theme -- M-DATASET-14 stats summary recolours on theme flip")
    attach_captures(page)
    DP = "dataset-plotter"
    open_tab(page, "Dataset View")
    page.wait_for_timeout(4000)

    def look():
        return page.evaluate(
            """(id) => { const el = document.getElementById(id); if (!el) return {present:false};
                 const cs = getComputedStyle(el);
                 return {present:true, color: cs.color, bg: cs.backgroundColor,
                         border: cs.borderColor,
                         theme: document.documentElement.getAttribute('data-bs-theme')
                                || document.body.getAttribute('data-bs-theme') || null}; }""",
            f"{DP}-stats-summary",
        )

    before = look()
    log(f"  before: {before}")
    if not before.get("present"):
        record("theme", verdict="BLOCKED", reason="dataset-plotter-stats-summary absent", before=before)
        log("  !! stats summary absent -- needs a loaded dataset on this tab")
        return

    toggled = page.evaluate(
        """() => { const ids = ['dark-mode-toggle', 'theme-toggle', 'dark-mode-switch'];
             for (const i of ids) { const el = document.getElementById(i); if (el) { el.click(); return i; } }
             const cand = [...document.querySelectorAll('input[type=checkbox], button')]
                 .find(e => /theme|dark/i.test((e.id || '') + ' ' + (e.getAttribute('aria-label') || '')));
             if (cand) { cand.click(); return cand.id || '<unnamed>'; }
             return null; }"""
    )
    log(f"  toggled via: {toggled!r}")
    if not toggled:
        record("theme", verdict="BLOCKED", reason="no theme toggle found", before=before)
        return

    ok, elapsed, _ = wait_for(lambda: look().get("color") != before.get("color") or look().get("bg") != before.get("bg"), budget_s=60, every_s=2.0, label="stats summary recolour")
    after = look()
    log(f"  after ({elapsed}s): {after}")
    changed = after.get("color") != before.get("color") or after.get("bg") != before.get("bg")
    verdict = "PASS" if changed else "FAIL"
    log(f"  M-DATASET-14 -> {verdict} (recoloured={changed})")
    shot(page, "seg17_theme.png")
    record("theme", verdict=verdict, before=before, after=after, elapsed_s=elapsed, toggle=toggled)


STEPS = {
    "probe": step_probe,
    "topodiag": step_topodiag,
    "rebuildprobe": step_rebuildprobe,
    "wirecensus": step_wirecensus,
    "quietread": step_quietread,
    "topo": step_topo,
    "storestorm": step_storestorm,
    "f031": step_f031,
    "theme": step_theme,
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
            # A missing/partial/corrupt results file just means this invocation starts fresh.
            pass
    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            for name in wanted:
                STEPS[name](page, capture)
        finally:
            log(f"results -> {RESULTS_PATH}")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
