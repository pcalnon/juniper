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

Steps (comma-separated, order preserved). **This list is the authority for what is
IMPLEMENTED; it was stale and is corrected here.** An earlier version advertised
``w1grow`` and ``toposel`` and claimed ``topo`` covered M-TOPOLOGY-01..09/16..18 and
``theme`` covered M-TOPOLOGY-09 — none of which is true. A reader who trusted it
would run a step and score rows it never touches, which is a vacuous pass. The
registered set is ``STEPS`` at the bottom of this file; ``--step`` rejects anything
else, so a wrong name fails loudly rather than silently.

  probe    -- dump the REAL DOM shape of the four topology controls (dcc.Dropdown /
              Checklist / RadioItems are NOT native selects; this pins the idiom
              before any row is scored)
  topo     -- scores EXACTLY M-TOPOLOGY-01..08 and -17. Layout cycle, show-weights,
              display-mode, view-mode, depth slider, stats bar, store refresh.
  topoevents -- scores EXACTLY M-TOPOLOGY-09, -10, -12 and -15: the graph's own
              event surface (node click, click-empty-space, hover inertness, and
              the stats bar's theme recolour on the TOPOLOGY tab -- which is a
              different row from `theme`'s M-DATASET-14 on the Dataset tab).
              Uses a REAL mouse click at the point's own pixel, never
              `gd.emit('plotly_click', ...)`: a synthetic emit fabricates the
              payload and so cannot fail the way a user's click fails.
              M-TOPOLOGY-10 requires canopy#564 (F-CANOPY-044/-045); before it,
              the row fails because a click resolves to a co-located edge trace.
  theme    -- scores EXACTLY M-DATASET-14 (dark-mode recolour of the DATASET figures,
              read off ``dataset-plotter-stats-summary`` on the Dataset View tab).
              It does NOT touch M-TOPOLOGY-09, which lives on the Topology tab.
  topodiag / rebuildprobe / wirecensus / quietread / storestorm / f031
           -- diagnostic instruments, not row scorers.

NOT IMPLEMENTED (no step exists; these rows have no scorer anywhere in the repo):
  M-TOPOLOGY-11          -- box / lasso select. Its idiom is NOT pinned: three
                            attempts produced ZERO `plotly_selected` events with
                            `dragmode` re-confirmed 'select' AT DRAG TIME and a box
                            far larger than plotly's ~8 px minimum. plotly never
                            fired the event, so the product code never ran -- a
                            DRIVER gap, deliberately not filed as a finding.
  M-TOPOLOGY-13          -- zoom / pan relayout captured into `-view-state`
  M-TOPOLOGY-14          -- modebar camera (PNG export); needs a Playwright
                            download intercept
  M-TOPOLOGY-16          -- cascade-add glow; MANUAL/VIS, and needs a cascade ADD, so
                            a saturated fixture (40/40) cannot exercise it
  M-TOPOLOGY-18          -- raw-store refresh
  W1-12..14, W4-*        -- walkthrough steps. They live in the MATRIX
                            (JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md)
                            and the ledger (JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md),
                            NOT in the plan. An earlier version of this docstring said
                            "tracked in the plan document"; grep says `W4-` and `W1-1`
                            appear ZERO times in
                            JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md.
                            A reader who went looking there would find nothing and
                            conclude the ids were retired.

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
import re
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
_pred = _load("_topopred", "e2e_topology_row_predicates.py")
score_m_topology_06 = _pred.score_m_topology_06
score_m_topology_07 = _pred.score_m_topology_07
selection_is_cleared = _pred.selection_is_cleared

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


def settle_changed(page, prev_hash, container_id: str = None, transition_budget_s: float = 30.0, settle_budget_s: float = 20.0) -> dict:
    """Wait for the figure to LEAVE ``prev_hash``, then settle. "Stable is not ready", one level up.

    ``settle_figure`` answers "has the figure stopped changing?". That is the wrong
    question immediately after an action, because a figure whose rebuild HAS NOT
    STARTED YET is perfectly stable — the hash holds, three reads agree, and it
    reports ``settled`` while showing the PREVIOUS action's render. ``painted`` does
    not catch it either: the stale figure is fully painted, just stale.

    That is M-TOPOLOGY-02's failure, and it is a level above the one
    ``settle_figure`` was written to fix. Measured (`/tmp/juniper-e2e/seg17_results.json`,
    2026-09-02 06:30): M-01 ends by selecting Hierarchical and waiting a FIXED 2000 ms;
    M-02 then called ``settle_figure``, which settled on Circular's ``26d0f961`` —
    M-01's last layout — and scored ``on``. The weights-off toggle then retired that
    still-pending Hierarchical rebuild (``getUniqueIdentifier`` hashes inputs +
    outputs + state and NOT the trigger, and BOTH controls are Inputs of the same
    rebuild), so ``off`` read ``26d0f961`` as well and the row failed on
    ``on_hash == off_hash`` — two reads of a figure that was neither state.

    The row is a RACE, not a stable defect: the very next run passed it, because a
    dropdown retry earlier in M-01 happened to add ~12 s and the rebuild landed
    before the first read. A verdict that depends on how long an unrelated retry took
    is not a measurement.

    So: wait for the TRANSITION first, then settle. ``changed`` is returned rather
    than asserted, because a transition that never arrives must be visible in the
    record — silently comparing two stale hashes is what produced the original
    wrong reading.
    """
    container_id = container_id or f"{NV}-graph"
    ok, elapsed, _ = wait_for(
        lambda: (fig_info(page, container_id) or {}).get("fig_hash") not in (None, prev_hash),
        budget_s=transition_budget_s,
        every_s=0.5,
        label=f"{container_id} to leave {prev_hash}",
    )
    st = settle_figure(page, container_id=container_id, budget_s=settle_budget_s)
    st["changed"] = ok
    st["transition_s"] = elapsed
    st["from_hash"] = prev_hash
    return st


# --------------------------------------------------------------------------
# Plotly-event idioms (M-TOPOLOGY-10/-12/-15). Pinned against the live app by
# ``util/ad-hoc/2026-09-02_plotly_event_probe.py`` BEFORE any row used them.
#
# A REAL MOUSE CLICK, never ``gd.emit('plotly_click', ...)``. A synthetic emit
# fabricates the event payload, so it proves the callback works when handed a
# payload the driver invented -- it cannot fail the way a user's click fails, and
# it would have been blind to F-CANOPY-044's entire class. A real click at the
# point's own pixel makes plotly do its own hit-testing and build its own event.
# --------------------------------------------------------------------------
_JS_MARKER_TRACES = """(id) => {
  const root = document.getElementById(id);
  if (!root) return {present:false};
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd || !gd.data) return {present:true, plotly:false};
  const out = [];
  gd.data.forEach((t, ci) => {
    if (String(t.mode || '').indexOf('markers') < 0) return;
    out.push({curve: ci, name: t.name || '', n: (t.x && t.x.length) || 0,
              is3d: String(t.type || '').indexOf('3d') >= 0,
              first_text: Array.isArray(t.text) ? t.text[0] : (t.text || null)});
  });
  return {present:true, plotly:true, n_traces: gd.data.length, marker_traces: out};
}"""

# data coords -> VIEWPORT pixels. MUST be re-read after any scroll: both this and
# a marker's bounding box are viewport-relative, and a probe run once "disagreed"
# with itself by exactly the 279 px the page had scrolled between the two reads.
_JS_POINT_XY = """([id, curve, index]) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd || !gd._fullLayout) return {ok:false, why:'no _fullLayout'};
  const fl = gd._fullLayout, xa = fl.xaxis, ya = fl.yaxis;
  if (!xa || !ya || !xa.l2p || !ya.l2p) return {ok:false, why:'no 2-D cartesian axes'};
  const t = gd.data[curve];
  if (!t || t.x[index] === undefined) return {ok:false, why:'no such point'};
  const r = gd.getBoundingClientRect();
  return {ok:true, x: r.left + fl._size.l + xa.l2p(t.x[index]),
                   y: r.top  + fl._size.t + ya.l2p(t.y[index]),
          plot: {l: r.left + fl._size.l, t: r.top + fl._size.t, w: fl._size.w, h: fl._size.h}};
}"""

_JS_HOVERTEXT = """(id) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd) return {present:false};
  const nodes = gd.querySelectorAll('.hoverlayer .hovertext');
  return {present:true, n: nodes.length,
          text: nodes.length ? (nodes[0].textContent || '').trim().slice(0,120) : null};
}"""


def scroll_graph_into_view(page, container_id: str = None) -> dict:
    """Centre the graph in the viewport, then let layout settle.

    NOT cosmetic, and not optional. ``page.mouse`` dispatches at VIEWPORT
    coordinates, so whatever element happens to sit at that point receives the
    event -- a pixel can be inside the viewport and inside the plot's bounding box
    and still be covered. Measured: with the graph left where the tab switch put
    it, a click computed at y=1033 (viewport 1100, plot area 568-1108) produced
    NEITHER a selection NOR a hover tooltip; the identical arithmetic after
    centring produced both.

    Callers must RE-READ any pixel coordinate after this: both ``point_xy`` and a
    marker's bounding box are viewport-relative, and an earlier probe run
    "disagreed" with itself by exactly the 279 px the page had scrolled between
    computing a coordinate and using it.
    """
    container_id = container_id or f"{NV}-graph"
    page.evaluate("(id) => { const el = document.getElementById(id); if (el) el.scrollIntoView({block:'center'}); }", container_id)
    page.wait_for_timeout(700)
    return page.evaluate("() => ({vw: window.innerWidth, vh: window.innerHeight, sy: window.scrollY})")


def _graph_centre(page, container_id: str = None):
    """(x, y) of the graph's centre in VIEWPORT coords -- used to hover the modebar in."""
    container_id = container_id or f"{NV}-graph"
    r = page.evaluate(
        "(id) => { const b = document.getElementById(id).getBoundingClientRect();" " return {x: b.left + b.width / 2, y: b.top + b.height / 2}; }",
        container_id,
    )
    return r["x"], r["y"]


def marker_traces(page, container_id: str = None) -> list:
    """The 2-D node traces (Input / Hidden / Output), with their curve indices."""
    container_id = container_id or f"{NV}-graph"
    info = page.evaluate(_JS_MARKER_TRACES, container_id) or {}
    return [t for t in (info.get("marker_traces") or []) if not t["is3d"] and t["n"] > 0]


def point_xy(page, curve: int, index: int = 0, container_id: str = None) -> dict:
    container_id = container_id or f"{NV}-graph"
    return page.evaluate(_JS_POINT_XY, [container_id, curve, index])


def click_point(page, curve: int, index: int = 0, container_id: str = None, settle_ms: int = 2500) -> dict:
    """Real mouse click at a data point's own pixel. Returns where it clicked.

    Scrolls the graph into view FIRST and computes the pixel AFTER, because the
    coordinate is viewport-relative and the gesture is delivered by viewport
    position (see ``scroll_graph_into_view``).
    """
    scroll_graph_into_view(page, container_id)
    xy = point_xy(page, curve, index, container_id)
    if not xy.get("ok"):
        return xy
    page.mouse.move(xy["x"], xy["y"])
    page.wait_for_timeout(300)
    page.mouse.click(xy["x"], xy["y"])
    page.wait_for_timeout(settle_ms)
    return xy


def selection_info(page) -> dict:
    """-selection-info's text + whether it is displayed (M-10/-11/-12's oracle)."""
    return page.evaluate(
        """(id) => { const el = document.getElementById(id);
             if (!el) return {present:false};
             return {present:true, display: getComputedStyle(el).display,
                     text: (el.innerText || '').trim()}; }""",
        f"{NV}-selection-info",
    )


def click_empty_space(page, container_id: str = None, settle_ms: int = 2500) -> dict:
    """Click a spot inside the plot area that holds no node.

    Chosen as the plot area's top-left inset rather than an arbitrary pixel: the
    hierarchical layout puts every node at x in {input, hidden spread, output}, and
    the top-left corner is empty in all four layouts. Returns the pixel used so a
    failure can be told apart from a mis-aimed click.
    """
    container_id = container_id or f"{NV}-graph"
    scroll_graph_into_view(page, container_id)
    geo = page.evaluate(
        """(id) => { const root = document.getElementById(id);
             const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
             if (!gd || !gd._fullLayout) return null;
             const fl = gd._fullLayout, r = gd.getBoundingClientRect();
             return {l: r.left + fl._size.l, t: r.top + fl._size.t, w: fl._size.w, h: fl._size.h}; }""",
        container_id,
    )
    if not geo:
        return {"ok": False, "why": "no plot geometry"}
    x, y = geo["l"] + geo["w"] * 0.04, geo["t"] + geo["h"] * 0.06
    page.mouse.move(x, y)
    page.wait_for_timeout(200)
    page.mouse.click(x, y)
    page.wait_for_timeout(settle_ms)
    return {"ok": True, "x": x, "y": y}


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
    """Read a dcc.Store's data off the renderer (stores render no DOM).

    RETURNS ``{"ok": bool, "value": ..., "via": str}`` -- never a bare value.

    The previous version returned the value directly and ``None`` when it could not
    read, which made "the store is empty" and "I cannot read this store"
    indistinguishable. That is not a hypothetical: it read ``None`` for EVERY store
    on this app, including ``-raw-topology-store`` while its heatmap was rendering
    at ``plot_area=0.70`` -- which is only possible if that store is populated. A
    row scored off it (M-TOPOLOGY-18) produced a confident FAIL against a working
    gate, and ``step_topodiag`` has been logging ``topology-store (NoneType): None``
    for the whole arc, one inch from F-CANOPY-039's central claim about what that
    store contains. Diagnosed by ``util/ad-hoc/2026-09-03_store_read_probe.py``.

    Why the old paths failed: a ``dcc.Store`` renders no element, so
    ``document.getElementById(id)`` is null and ``_dashprivate_layout`` never
    exists; and the recursive walk over ``state.layout`` does not reach components
    nested through the shapes Dash 3 uses. Dash maintains an id -> path index at
    ``state.paths.strs``, which is the supported way in, so that is tried first.
    """
    return page.evaluate(
        """(id) => {
             const st = window.store && window.store.getState ? window.store.getState() : null;
             if (!st) return {ok:false, value:null, via:'<no redux store>'};
             if (!st.layout) return {ok:false, value:null, via:'<no redux layout>'};
             // 1. the id -> path index Dash maintains.
             try {
               const strs = st.paths && st.paths.strs ? st.paths.strs : null;
               if (strs && strs[id]) {
                 let node = st.layout;
                 for (const key of strs[id]) { if (node == null) break; node = node[key]; }
                 if (node && node.props && 'data' in node.props) return {ok:true, value: node.props.data, via:'paths.strs'};
                 if (node && node.props) return {ok:true, value: null, via:'paths.strs (no data prop)'};
               }
             } catch (e) { /* fall through to the walk */ }
             // 2. exhaustive walk, following children AND any prop that holds
             //    components (Dash 3 nests through more than `children`).
             try {
               const seen = new Set();
               const walk = (n) => {
                 if (!n || typeof n !== 'object' || seen.has(n)) return undefined;
                 seen.add(n);
                 if (n.props && n.props.id === id) return {ok:true, value: n.props.data === undefined ? null : n.props.data, via:'walk'};
                 const p = n.props || {};
                 for (const k of Object.keys(p)) {
                   const v = p[k];
                   const arr = Array.isArray(v) ? v : [v];
                   for (const c of arr) { const r = walk(c); if (r !== undefined) return r; }
                 }
                 return undefined;
               };
               const r = walk(st.layout);
               if (r !== undefined) return r;
             } catch (e) { return {ok:false, value:null, via:'<err ' + e.message + '>'}; }
             return {ok:false, value:null, via:'<id not found in layout>'};
           }""",
        store_id,
    )


def store_value(page, store_id: str):
    """The store's value, or raise if it could not be READ.

    Callers that want to score a row on a store's contents must not silently treat
    an unreadable store as an empty one -- use this and let it fail loudly.
    """
    r = _store(page, store_id) or {}
    if not r.get("ok"):
        raise RuntimeError(f"cannot read store {store_id!r}: {r.get('via')}")
    return r.get("value")


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
    st_read = _store(page, f"{NV}-topology-store")
    store = st_read.get("value") if st_read.get("ok") else None
    # Say WHICH it is. This line logged "topology-store (NoneType): None" for the
    # whole arc while the reader could not reach any store at all, and that reads as
    # "the store is empty" -- an inch from F-CANOPY-039's central claim about this
    # exact store's contents.
    st_kind = type(store).__name__ if st_read.get("ok") else f"UNREADABLE({st_read.get('via')})"
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
    # Return to Hierarchical for M-02. The read that follows must not begin until
    # THIS rebuild has landed: a fixed 2000 ms wait here is what let M-02 settle on
    # the previous layout's figure and score two reads of it (see settle_changed).
    _pre_home = (_graph(page) or {}).get("fig_hash")
    set_dropdown(page, f"{NV}-layout-selector", "Hierarchical")
    home = settle_changed(page, _pre_home)
    if not home.get("changed"):
        log(f"  !! layout never left {_pre_home} on the way back to Hierarchical — M-02 reads may be stale")
    res["M-TOPOLOGY-02-precondition"] = {"from_hash": _pre_home, "changed": home.get("changed"), "transition_s": home.get("transition_s"), "settled_hash": home.get("fig_hash")}

    # M-TOPOLOGY-02 / W4-03 -- show-weights off then on.
    #
    # SETTLE at every read, and compare CONTENT HASHES. This block was the fourth
    # site of the read-inside-the-rebuild-window defect and was missed when the
    # other three were fixed: it settled for a fixed 3 s against a rebuild that
    # takes 1.5-5 s and settles at 2.8-7 s. It passed on timing luck, and adding
    # settle_figure everywhere ELSE slowed the run enough to expose it —
    # `on_sig == off_sig == 394731` with `back_sig` holding the PREVIOUS state,
    # i.e. all three reads shifted one toggle behind.
    #
    # The old `wait_for(sig != previous)` is also wrong twice over: `sig` is a byte
    # LENGTH that can collide, and a wait keyed to "different from the value I read
    # too early" can be satisfied by the render the PREVIOUS action was still
    # completing.
    # NOTE ON THE CONTRACT. ``back`` is expected to EQUAL ``on``: turning weights off
    # and on again returns the graph to its previous render, so demanding three
    # distinct hashes would fail a correctly-behaving toggle. The row asserts the two
    # TRANSITIONS -- off differs from on, and back differs from off -- plus, now,
    # that each transition was actually OBSERVED rather than timed out.
    settle_figure(page)
    on_g = _graph(page)
    set_checklist(page, f"{NV}-show-weights", False)
    off_st = settle_changed(page, on_g.get("fig_hash"))
    off_g = _graph(page)
    set_checklist(page, f"{NV}-show-weights", True)
    back_st = settle_changed(page, off_g.get("fig_hash"))
    back_g = _graph(page)
    hashes_moved = off_g.get("fig_hash") != on_g.get("fig_hash") and back_g.get("fig_hash") != off_g.get("fig_hash")
    # A timed-out transition means the read below is of a figure the toggle never
    # produced. Scoring that as either PASS or FAIL asserts something the run did not
    # measure, so it is called out as its own verdict.
    observed = bool(off_st.get("changed")) and bool(back_st.get("changed"))
    m02_verdict = "PASS" if (hashes_moved and observed) else ("FAIL" if observed else "INDETERMINATE")
    res["M-TOPOLOGY-02"] = {
        "verdict": m02_verdict,
        "on_sig": on_g.get("sig"), "off_sig": off_g.get("sig"), "back_sig": back_g.get("sig"),
        "on_hash": on_g.get("fig_hash"), "off_hash": off_g.get("fig_hash"), "back_hash": back_g.get("fig_hash"),
        "on_ann": len(on_g.get("annotations") or []), "off_ann": len(off_g.get("annotations") or []),
        "off_transition_observed": off_st.get("changed"), "off_transition_s": off_st.get("transition_s"),
        "back_transition_observed": back_st.get("changed"), "back_transition_s": back_st.get("transition_s"),
        "back_equals_on": back_g.get("fig_hash") == on_g.get("fig_hash"),
    }
    log(f"  M-TOPOLOGY-02 show-weights: on={on_g.get('fig_hash')} off={off_g.get('fig_hash')} back={back_g.get('fig_hash')} transitions_observed={observed} -> {m02_verdict}")
    if not observed:
        log("  !! a show-weights transition never landed within budget -- the reads are of a figure the toggle did not produce")

    # M-TOPOLOGY-03 / W4-06 -- Weight Matrix heatmap; connection-count reads the em dash.
    set_radio(page, f"{NV}-display-mode", "weight_matrix")
    page.wait_for_timeout(3000)
    wait_for(lambda: any((t.get("type") == "heatmap") for t in (_graph(page).get("traces") or [])), budget_s=45, every_s=2.0)
    wm = _graph(page)
    wm_counts = counts(page)
    # A trace that EXISTS is not a trace that is VISIBLE. This row used to assert
    # only ``any(type == "heatmap")`` — and canopy#558 shipped a heatmap whose
    # vertical_spacing equalled plotly's own limit, so all 41 rows rendered at ZERO
    # height. Every trace object was present; the canvas was blank; **this row
    # PASSED on it** (F-CANOPY-041b). Require the subplots to own a real share of
    # the figure as well, so the row cannot certify a blank again.
    is_heat = any(t.get("type") == "heatmap" for t in (wm.get("traces") or []))
    plot_area = wm.get("plot_area")
    # ``None`` means an older fig_info without the field — do not fail the row on a
    # missing measurement, but say so rather than silently treating it as passing.
    area_ok = plot_area is None or plot_area >= 0.05
    res["M-TOPOLOGY-03"] = {
        "verdict": "PASS" if (is_heat and area_ok) else "FAIL",
        "heatmap": is_heat, "types": [t.get("type") for t in (wm.get("traces") or [])][:6],
        "plot_area": plot_area, "n_yaxes": wm.get("n_yaxes"),
        "area_measured": plot_area is not None,
        "connection_count": wm_counts["conn"],
    }
    log(f"  M-TOPOLOGY-03 weight matrix: heatmap={is_heat} plot_area={plot_area} n_yaxes={wm.get('n_yaxes')} types={res['M-TOPOLOGY-03']['types']} conn={wm_counts['conn']!r}")
    if is_heat and plot_area is not None and plot_area < 0.05:
        log(f"  !! heatmap traces exist but occupy only {plot_area:.1%} of the figure — this is the blank-canvas class, not a render")

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
    #
    # The label half of that contract was READ but never ASSERTED: the verdict
    # turned on ``display`` alone while ``label`` went into the record as
    # decoration. It read "0 of 40" on every run of this arc and the row still
    # scored PASS -- F-CANOPY-042's defect B, sitting in plain sight inside this
    # scorer's own output. Assert what the row says.
    dv = vis(page, f"{NV}-depth-slider-container")
    dlabel = text_of(page, f"{NV}-depth-label")
    m07 = score_m_topology_07(dv.get("display"), dlabel)
    res["M-TOPOLOGY-07"] = {"verdict": "PASS" if m07 else "FAIL", "display": dv.get("display"), "label": dlabel, "want_label": "all"}
    log(f"  M-TOPOLOGY-07 depth container: display={dv.get('display')!r} label={dlabel!r} want='all'")

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
    # BOTH, not either. The predicate used to be ``label == want OR
    # counts["hidden"] == want``, and it passed on the counts branch: the stats
    # bar tracked the filter while the label beside the slider stayed at
    # "0 of 40". So this row went green on a run where half of what it names was
    # broken -- and F-CANOPY-042 had to be found by eye instead of by this
    # scorer. An OR over two independent claims scores the easier one.
    m06 = score_m_topology_06(sl.get("idiom"), k_label, k_counts["hidden"], want)
    res["M-TOPOLOGY-06"] = {
        "verdict": "PASS" if m06 else "FAIL",
        "slider": sl, "label": k_label, "hidden_count": k_counts["hidden"], "want": want,
        "label_ok": k_label == want, "counts_ok": k_counts["hidden"] == want,
    }
    log(f"  M-TOPOLOGY-06 depth={k}: idiom={sl.get('idiom')} label={k_label!r} hidden={k_counts['hidden']!r} want={want!r} (label_ok={k_label == want} counts_ok={k_counts['hidden'] == want})")

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


def step_topoevents(page, capture):
    """M-TOPOLOGY-09, -10, -12 and -15: the graph's own event surface.

    These four were BLOCKED as "no scorer exists" because the driver had no
    plotly-event idiom at all. The idiom is now pinned
    (``util/ad-hoc/2026-09-02_plotly_event_probe.py``) and two of the rows turned
    out to be blocked by a product defect instead -- F-CANOPY-044, fixed in
    canopy#564. Each row below is written to FAIL on a known bad state, not merely
    to run:

      -10 fails on the F-CANOPY-044 state (click does nothing) AND on the
          F-CANOPY-045 state (every node reports ``Layer: Output``);
      -12 refuses to score at all unless something was actually selected first --
          "the selection cleared" is vacuously true when there was none;
      -15 is DEAD-EXPECTED, so it must prove the hover REACHED plotly before it can
          claim the app stayed inert. An assertion that nothing happened is
          worthless if nothing was done.
    """
    log("STEP topoevents -- M-TOPOLOGY-09/-10/-12/-15 (graph event surface)")
    attach_captures(page)
    res: dict = {}

    open_tab(page, "Network Topology")
    wake = wake_topology(page)
    log(f"  wake_topology: {wake}")
    res["wake"] = wake
    if not wake["woke"]:
        record("topoevents", verdict="BLOCKED", reason="graph never painted", wake=wake)
        log("  !! graph never painted -- rows stay BLOCKED")
        return

    traces = marker_traces(page)
    log(f"  node traces: {[(t['name'], t['curve'], t['n']) for t in traces]}")
    res["node_traces"] = traces
    if not traces:
        record("topoevents", verdict="BLOCKED", reason="no 2-D marker traces", **res)
        return

    # SETTLE BEFORE ACTING. The rebuild takes 1.5-31 s and replaces the whole
    # figure; a gesture computed from one render and delivered into the next lands
    # on nothing. Measured on this very step: without settling, M-TOPOLOGY-10 scored
    # PASS then FAIL on an unchanged stack, and M-15 read a selection change that
    # was really the previous click's response arriving late. Same defect class as
    # M-TOPOLOGY-02, one step further out.
    settle_figure(page, budget_s=30)

    # Start from a known-clear selection so every row below reads a transition.
    click_empty_space(page)
    baseline = selection_info(page)
    log(f"  baseline selection: {baseline}")

    # ---- M-TOPOLOGY-10 / W4-11 -- click a node, it is selected ------------
    # Driven on a HIDDEN unit: it is the only layer with enough members that a
    # wrong Layer label cannot pass by coincidence (an Input node mislabelled
    # "Input" would be indistinguishable from correct).
    hidden = next((t for t in traces if t["name"] == "Hidden Units"), traces[0])
    want_label = f"Hidden {min(3, hidden['n'] - 1)}"
    settle_figure(page, budget_s=30)
    before_click = selection_info(page)
    where = click_point(page, hidden["curve"], min(3, hidden["n"] - 1), settle_ms=800)
    # Wait for the EFFECT, never a fixed sleep: the selection callback competes with
    # the rebuild for renderer slots, so its response can arrive seconds later.
    got, sel_wait_s, _ = wait_for(
        lambda: selection_info(page).get("text") != before_click.get("text"),
        budget_s=25, every_s=0.5, label="-selection-info to change after the node click",
    )
    sel = selection_info(page)
    shown = sel.get("display") not in (None, "none")
    names_node = want_label in (sel.get("text") or "")
    # F-CANOPY-045: the layer must match the trace the node came from. This is the
    # assertion four `test_layer_detection_*` unit tests could not make, because
    # they re-typed the production expression instead of calling it.
    layer_ok = "Layer: Hidden" in (sel.get("text") or "")
    m10 = bool(shown and names_node and layer_ok)
    res["M-TOPOLOGY-10"] = {
        "verdict": "PASS" if m10 else "FAIL",
        "clicked": where, "want_label": want_label, "selection": sel,
        "shown": shown, "names_node": names_node, "layer_ok": layer_ok,
        "effect_observed": got, "effect_wait_s": sel_wait_s, "before": before_click,
    }
    log(f"  M-TOPOLOGY-10 node click: shown={shown} names_node={names_node} layer_ok={layer_ok} -> {res['M-TOPOLOGY-10']['verdict']}")
    if shown and names_node and not layer_ok:
        log("  !! selected the right node but the Layer label is wrong -- F-CANOPY-045")

    # ---- M-TOPOLOGY-12 / W4-13 -- click empty space, selection clears -----
    # PRECONDITION-GATED. If -10 left nothing selected, "it cleared" says nothing.
    if not shown:
        res["M-TOPOLOGY-12"] = {"verdict": "BLOCKED", "reason": "nothing was selected, so 'cleared' is vacuous", "precondition_selected": False}
        log("  M-TOPOLOGY-12 -> BLOCKED (no selection to clear; the row would pass vacuously)")
    else:
        # Count plotly_click events across the gesture. "It did not clear" has two
        # very different causes and the fix differs: the handler ran and failed to
        # clear, or NO EVENT FIRED AT ALL because plotly only emits plotly_click
        # when a POINT is hit -- in which case ``clickData`` never changes, the
        # callback (prevent_initial_call=True) never runs, and the clear path at the
        # end of handle_node_selection is unreachable by this gesture. Recording
        # which one it is keeps the row from being filed against the wrong thing.
        page.evaluate(
            """(id) => { const root = document.getElementById(id);
                 const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                 window.__jn_empty_clicks = 0;
                 if (gd && gd.on) gd.on('plotly_click', () => { window.__jn_empty_clicks++; }); }""",
            f"{NV}-graph",
        )
        settle_figure(page, budget_s=25)
        spot = click_empty_space(page, settle_ms=800)
        # Give the clear the same effect budget the select got, so a slow-but-working
        # clear is not scored as a broken one.
        wait_for(lambda: selection_info(page).get("display") in (None, "none"), budget_s=20, every_s=0.5, label="-selection-info to clear")
        n_click_ev = page.evaluate("() => window.__jn_empty_clicks || 0")
        after = selection_info(page)
        cleared = selection_is_cleared(after)
        res["M-TOPOLOGY-12"] = {
            "verdict": "PASS" if cleared else "FAIL",
            "precondition_selected": True, "clicked": spot, "before": sel, "after": after,
            "plotly_click_events": n_click_ev,
            "unchanged_text": (after.get("text") == sel.get("text")),
        }
        log(f"  M-TOPOLOGY-12 click empty space: cleared={cleared} plotly_click_events={n_click_ev} -> {res['M-TOPOLOGY-12']['verdict']}")
        if not cleared and n_click_ev == 0:
            log("  !! no plotly_click fired -- plotly emits it only for POINT hits, so clickData never changed and the")
            log("     clear path at the end of handle_node_selection is UNREACHABLE by an empty-space click (product, not driver)")

    # ---- M-TOPOLOGY-15 / W4-16 -- hover is INERT (DEAD-EXPECTED) ----------
    # The matrix marks this dead by design: the graph's only Inputs are
    # relayoutData / clickData / selectedData, so there is no hoverData callback.
    # A "nothing happened" verdict is only worth having if the gesture DID happen,
    # so the plotly tooltip is the proof-of-gesture and the row is INDETERMINATE
    # without it.
    # Settle first: a rebuild response landing mid-hover would change the DOM for a
    # reason that has nothing to do with hovering, and this row would blame the hover.
    settle_figure(page, budget_s=25)
    before_hover = selection_info(page)
    n_api_before = len([r for r in RESP if "/api/" in r["url"]])
    scroll_graph_into_view(page)
    hxy = point_xy(page, hidden["curve"], 0)
    tooltip = {"n": 0}
    if hxy.get("ok"):
        page.mouse.move(hxy["x"] - 60, hxy["y"] - 60)
        page.wait_for_timeout(400)
        page.mouse.move(hxy["x"], hxy["y"], steps=6)
        ok_tip, _, _ = wait_for(lambda: (page.evaluate(_JS_HOVERTEXT, f"{NV}-graph") or {}).get("n", 0) > 0, budget_s=12, every_s=0.5, label="plotly hover tooltip")
        tooltip = page.evaluate(_JS_HOVERTEXT, f"{NV}-graph") or {"n": 0}
        page.wait_for_timeout(2500)
    hovered = bool(tooltip.get("n"))
    after_hover = selection_info(page)
    n_api_after = len([r for r in RESP if "/api/" in r["url"]])
    dom_unchanged = (after_hover.get("display") == before_hover.get("display")) and (after_hover.get("text") == before_hover.get("text"))
    no_requests = n_api_after == n_api_before
    m15_verdict = "PASS" if (hovered and dom_unchanged and no_requests) else ("FAIL" if hovered else "INDETERMINATE")
    res["M-TOPOLOGY-15"] = {
        "verdict": m15_verdict,
        "hover_reached_plotly": hovered, "tooltip": tooltip,
        "dom_unchanged": dom_unchanged, "api_calls_during_hover": n_api_after - n_api_before,
        "before": before_hover, "after": after_hover,
    }
    log(f"  M-TOPOLOGY-15 hover inert: hovered={hovered} dom_unchanged={dom_unchanged} api_delta={n_api_after - n_api_before} -> {m15_verdict}")
    if not hovered:
        log("  !! the tooltip never appeared, so the hover never reached plotly -- 'nothing happened' would be vacuous")

    # ---- M-TOPOLOGY-09 / W4-17 -- stats bar recolours on a theme flip -----
    # Scored on the element's COMPUTED colours, not on the toggle's own state:
    # F-CANOPY-001 (open) is a toggle whose glyph desyncs from the store, so the
    # toggle reporting "dark" proves nothing about what rendered.
    def stats_look():
        return page.evaluate(
            """(id) => { const el = document.getElementById(id); if (!el) return {present:false};
                 const cs = getComputedStyle(el);
                 return {present:true, color: cs.color, bg: cs.backgroundColor}; }""",
            f"{NV}-stats-bar",
        )

    sb_before = stats_look()
    toggled = page.evaluate(
        """() => { const ids = ['dark-mode-toggle', 'theme-toggle', 'dark-mode-switch'];
             for (const i of ids) { const el = document.getElementById(i); if (el) { el.click(); return i; } }
             const cand = [...document.querySelectorAll('input[type=checkbox], button')]
                 .find(e => /theme|dark/i.test((e.id || '') + ' ' + (e.getAttribute('aria-label') || '')));
             if (cand) { cand.click(); return cand.id || '<unnamed>'; }
             return null; }"""
    )
    if not sb_before.get("present") or not toggled:
        res["M-TOPOLOGY-09"] = {"verdict": "BLOCKED", "reason": "stats bar absent" if not sb_before.get("present") else "no theme toggle found", "before": sb_before, "toggle": toggled}
        log(f"  M-TOPOLOGY-09 -> BLOCKED ({res['M-TOPOLOGY-09']['reason']})")
    else:
        wait_for(lambda: stats_look().get("bg") != sb_before.get("bg") or stats_look().get("color") != sb_before.get("color"), budget_s=45, every_s=2.0, label="stats bar recolour")
        sb_after = stats_look()
        recoloured = sb_after.get("bg") != sb_before.get("bg") or sb_after.get("color") != sb_before.get("color")
        res["M-TOPOLOGY-09"] = {"verdict": "PASS" if recoloured else "FAIL", "before": sb_before, "after": sb_after, "toggle": toggled}
        log(f"  M-TOPOLOGY-09 stats bar theme: {sb_before.get('bg')} -> {sb_after.get('bg')} recoloured={recoloured} -> {res['M-TOPOLOGY-09']['verdict']}")
        # Put the theme back so a later step in the same run is not read in dark.
        page.evaluate("""(i) => { const el = document.getElementById(i); if (el) el.click(); }""", toggled)
        page.wait_for_timeout(2500)

    shot(page, "seg17_topoevents.png")
    record("topoevents", **res)
    log(f"  topoevents verdicts: {[(k, v.get('verdict')) for k, v in res.items() if isinstance(v, dict) and 'verdict' in v]}")


_JS_MODEBAR_BTNS = """(id) => {
  const root = document.getElementById(id);
  if (!root) return [];
  const bar = root.querySelector('.modebar');
  if (!bar) return [];
  // The buttons are <BUTTON class="modebar-btn"> in this plotly build, NOT <a>.
  // An earlier probe used `a.modebar-btn`, found nothing, and reported the modebar
  // as present-but-empty -- a selector answering an adjacent question.
  return [...bar.querySelectorAll('*')]
    .filter(e => (e.className || '').toString().indexOf('modebar-btn') >= 0)
    .map(b => ({tag: b.tagName, data_title: b.getAttribute('data-title'),
                rect: (r => ({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}))(b.getBoundingClientRect())}));
}"""

_JS_TOIMAGE_CONFIG = """(id) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd || !gd._context) return null;
  const r = gd.getBoundingClientRect();
  return {opts: gd._context.toImageButtonOptions || null,
          displayModeBar: gd._context.displayModeBar, w: r.width, h: r.height};
}"""

# plotly's PNG path is SVG -> Blob -> <img> -> canvas -> toDataURL. This runs that
# path on a 10x10 rectangle TWICE, differing ONLY in the URL scheme.
#
# THE FIRST VERSION OF THIS CONTROL USED ONLY blob: -- the same scheme plotly uses --
# so it shared the mechanism under test and "proved" a browser limitation that does
# not exist. It nearly filed a real product defect as an environment note. Varying
# the scheme is what separates "this browser cannot rasterise SVG" from "this PAGE
# forbids blob: images", and here it is emphatically the latter: canopy serves
# `img-src 'self' data:` (canopy_constants.py DEFAULT_CSP_POLICY), which omits
# blob:, and the browser console says so outright.
_JS_SVG_RASTER_CONTROL = """async () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            + '<rect width="10" height="10" fill="red"/></svg>';
  const load = async (url) => {
    const img = new Image();
    await new Promise((res, rej) => {
      img.onload = res;
      img.onerror = () => rej(new Error('img.onerror'));
      setTimeout(() => rej(new Error('img load timeout')), 8000);
      img.src = url;
    });
    const c = document.createElement('canvas');
    c.width = 10; c.height = 10;
    c.getContext('2d').drawImage(img, 0, 0);
    return c.toDataURL('image/png').length;
  };
  const out = {};
  const burl = URL.createObjectURL(new Blob([svg], {type: 'image/svg+xml'}));
  try { out.blob = {ok: true, len: await load(burl)}; }
  catch (e) { out.blob = {ok: false, why: String(e.message).slice(0, 80)}; }
  finally { URL.revokeObjectURL(burl); }
  try { out.data = {ok: true, len: await load('data:image/svg+xml;base64,' + btoa(svg))}; }
  catch (e) { out.data = {ok: false, why: String(e.message).slice(0, 80)}; }
  // ok = "this browser can rasterise SVG at all", which is the data: answer.
  out.ok = !!(out.data && out.data.ok);
  out.blob_blocked = !!(out.data && out.data.ok) && !(out.blob && out.blob.ok);
  return out;
}"""


def _png_dims(path: str):
    """(width, height) straight out of the PNG IHDR -- no image library needed."""
    import struct

    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def step_topoexport(page, capture):
    """M-TOPOLOGY-14: the modebar camera exports a scale-2 PNG named canopy_network_<ts>.

    THE ROW SPLITS INTO A PRODUCT HALF AND AN ENVIRONMENT HALF, and conflating them
    would file a defect against canopy for something no product change could fix.

    Product-owned and fully testable here: the camera button exists, and the graph's
    ``toImageButtonOptions`` carry ``format: png``, ``scale: 2`` and a
    ``canopy_network_<YYYYmmdd>_<HHMMSS>`` filename. A regression in any of those --
    a broken filename template, a dropped scale -- scores FAIL.

    THE EXPORT ITSELF IS BROKEN, AND IT IS CANOPY'S DOING (F-CANOPY-047). plotly
    rasterises via SVG -> Blob -> <img> -> canvas, and canopy serves
    ``img-src 'self' data:`` (``canopy_constants.py`` ``DEFAULT_CSP_POLICY``), which
    OMITS ``blob:``. The browser blocks the image load, plotly's promise rejects with
    a bare ``[object Event]``, no anchor is ever clicked, and the user gets nothing
    but a console error. Measured 2026-09-03
    (``util/ad-hoc/2026-09-03_modebar_download_probe.py``):

        topology png scale=2      FAIL  [object Event]   (4.4 s)
        topology png scale=1      FAIL  [object Event]   -> not scale-specific
        topology svg              OK    1,211,031 bytes  -> serialisation is fine
        10x10 SVG via blob: URL   FAIL  img.onerror
        10x10 SVG via data: URL   OK    len=170          -> the SCHEME is the difference

        console: Loading the image 'blob:http://127.0.0.1:8051/...' violates the
        following Content Security Policy directive: "img-src 'self' data:".

    **An earlier version of this docstring said the opposite** -- that headless
    chromium cannot rasterise SVG, so the row was environment-BLOCKED rather than a
    defect. That was wrong, and wrong for an instructive reason: the control used a
    ``blob:`` URL, the very scheme under test, so it reproduced the failure and
    "confirmed" a browser limitation. Only varying the scheme exposed the CSP. The
    control now tests both, and the row scores FAIL when ``data:`` works and
    ``blob:`` does not, reserving BLOCKED for a browser that can rasterise neither.
    """
    log("STEP topoexport -- M-TOPOLOGY-14 (modebar camera / PNG export)")
    attach_captures(page)
    res: dict = {}

    open_tab(page, "Network Topology")
    wake = wake_topology(page)
    res["wake"] = wake
    log(f"  wake_topology: {wake}")
    if not wake["woke"]:
        record("topoexport", verdict="BLOCKED", reason="graph never painted", wake=wake)
        return

    settle_figure(page, budget_s=30)
    scroll_graph_into_view(page)
    gid = f"{NV}-graph"

    # ---- the PRODUCT half: config + button --------------------------------
    cfg = page.evaluate(_JS_TOIMAGE_CONFIG, gid) or {}
    opts = (cfg.get("opts") or {}) if isinstance(cfg, dict) else {}
    fmt_ok = opts.get("format") == "png"
    scale_ok = opts.get("scale") == 2
    fname = str(opts.get("filename") or "")
    fname_ok = bool(re.fullmatch(r"canopy_network_\d{8}_\d{6}", fname))

    page.mouse.move(*_graph_centre(page, gid))
    page.wait_for_timeout(1000)
    btns = page.evaluate(_JS_MODEBAR_BTNS, gid) or []
    cam = next((b for b in btns if "png" in str(b.get("data_title", "")).lower()), None)
    log(f"  modebar buttons: {len(btns)}; camera={'yes' if cam else 'NO'}")
    log(f"  toImageButtonOptions: format={opts.get('format')!r} scale={opts.get('scale')!r} filename={fname!r}")
    log(f"    format_ok={fmt_ok} scale_ok={scale_ok} filename_ok={fname_ok}")

    config_ok = bool(cam and fmt_ok and scale_ok and fname_ok)
    res["config"] = {
        "camera_button_present": bool(cam), "n_modebar_buttons": len(btns),
        "format": opts.get("format"), "scale": opts.get("scale"), "filename": fname,
        "format_ok": fmt_ok, "scale_ok": scale_ok, "filename_ok": fname_ok,
        "graph_css": {"w": cfg.get("w"), "h": cfg.get("h")},
    }

    if not config_ok:
        res["M-TOPOLOGY-14"] = {"verdict": "FAIL", "reason": "the export CONFIG is wrong — this is product-owned and needs no download to see", **res["config"]}
        log("  M-TOPOLOGY-14 -> FAIL (export config is wrong; not an environment issue)")
        shot(page, "seg17_topoexport.png")
        record("topoexport", **res)
        return

    # ---- the ENVIRONMENT half: can this browser actually produce the PNG? --
    dest = os.path.join(RUN_DIR, "m14_download")
    os.makedirs(dest, exist_ok=True)
    # dl_res = {"caught": False}
    try:
        with page.expect_download(timeout=90000) as info:
            page.mouse.click(cam["rect"]["x"], cam["rect"]["y"])
        dl = info.value
        saved = os.path.join(dest, dl.suggested_filename)
        dl.save_as(saved)
        dims = _png_dims(saved)
        dl_res = {"caught": True, "suggested_filename": dl.suggested_filename, "saved": saved, "bytes": os.path.getsize(saved), "png": dims}
    except Exception as e:  # noqa: BLE001
        dl_res = {"caught": False, "why": f"{type(e).__name__}: {str(e)[:120]}"}
    res["download"] = dl_res

    if dl_res.get("caught"):
        name_ok = bool(re.fullmatch(r"canopy_network_\d{8}_\d{6}\.png", dl_res.get("suggested_filename") or ""))
        w, h = dl_res.get("png") or (0, 0)
        cw = cfg.get("w") or 0
        # scale: 2 VERIFIED against the real raster, not trusted from the config.
        scale_seen = round(w / cw, 2) if cw else 0
        raster_ok = bool(w and cw and abs(scale_seen - 2.0) <= 0.15)
        verdict = "PASS" if (name_ok and raster_ok) else "FAIL"
        res["M-TOPOLOGY-14"] = {"verdict": verdict, "filename_ok": name_ok, "png_w": w, "png_h": h, "scale_seen": scale_seen, "raster_ok": raster_ok, **res["config"]}
        log(f"  M-TOPOLOGY-14 download: {dl_res.get('suggested_filename')!r} {w}x{h} (scale {scale_seen}) -> {verdict}")
    else:
        control = page.evaluate(_JS_SVG_RASTER_CONTROL)
        res["svg_raster_control"] = control
        log(f"  SVG raster control: blob:={control.get('blob')} data:={control.get('data')}")
        if control.get("blob_blocked"):
            # data: rasterises and blob: does not -> the page's CSP is the blocker,
            # which is canopy's own header. A product defect, not an environment one.
            res["M-TOPOLOGY-14"] = {
                "verdict": "FAIL",
                "reason": "canopy's CSP `img-src 'self' data:` omits blob:, so plotly's SVG->img->canvas raster is blocked and the camera button silently produces nothing (F-CANOPY-047)",
                "svg_raster_control": control, "download": dl_res, **res["config"],
            }
            log("  M-TOPOLOGY-14 -> FAIL (F-CANOPY-047): data: rasterises, blob: is CSP-blocked.")
            log("     The camera button and its config are correct; canopy's own `img-src` header breaks the export")
            log("     for every user in every browser — this is NOT a headless quirk.")
        elif not control.get("ok"):
            res["M-TOPOLOGY-14"] = {
                "verdict": "BLOCKED",
                "reason": "this browser cannot rasterise SVG by ANY scheme (data: fails too), so the row cannot be scored here",
                "svg_raster_control": control, "download": dl_res, **res["config"],
            }
            log("  M-TOPOLOGY-14 -> BLOCKED (environment): neither data: nor blob: rasterises in this browser")
        else:
            res["M-TOPOLOGY-14"] = {
                "verdict": "FAIL",
                "reason": "the browser rasterises SVG by both schemes, yet the camera button produced no download — product-owned, cause unidentified",
                "svg_raster_control": control, "download": dl_res, **res["config"],
            }
            log("  M-TOPOLOGY-14 -> FAIL: the browser rasterises fine, so the missing download is the app's")

    shot(page, "seg17_topoexport.png")
    record("topoexport", **res)
    log(f"  topoexport verdicts: {[(k, v.get('verdict')) for k, v in res.items() if isinstance(v, dict) and 'verdict' in v]}")


def step_topostate(page, capture):
    """M-TOPOLOGY-13 and -18: view-state persistence and the raw-store gate.

      -18 promises the raw-topology poll fires only when the topology tab is active
          AND the view is Weight Matrix. Scored on the STORE, whose two-sided
          transition (empty in Node Graph -> populated in Weight Matrix) is the
          gate's observable effect. It is NOT scored on browser network traffic: the
          first version of this row did that and read 0 hits in every condition,
          because ``/api/topology/raw`` is fetched SERVER-SIDE by canopy's own
          handler and never crosses the browser at all.
      -13 promises a zoom/pan is captured into ``-view-state`` and RE-APPLIED on the
          next 2-D rebuild. The re-application is the contract, so the axis range
          surviving a forced rebuild is the evidence -- reading the store would only
          prove it was written, not that it was honoured.

    Reading a ``dcc.Store`` at all needs care: a Store renders no DOM, so the value
    lives only in the renderer's state, and ``_store()`` returns an explicit
    ``{"ok", "value", "via"}`` precisely so that "unreadable" can never be scored as
    "empty" -- which is how this row first produced a confident FAIL against a
    working gate.
    """
    log("STEP topostate -- M-TOPOLOGY-13 / -18 (view state, raw-store gate)")
    attach_captures(page)
    res: dict = {}

    open_tab(page, "Network Topology")
    wake = wake_topology(page)
    res["wake"] = wake
    log(f"  wake_topology: {wake}")
    if not wake["woke"]:
        record("topostate", verdict="BLOCKED", reason="graph never painted", wake=wake)
        return

    # ---- M-TOPOLOGY-18 / W4-15 -- the raw-topology poll's gate ------------
    #
    # SCORED ON THE STORE, NOT ON THE WIRE. The first version of this row counted
    # browser requests to `/api/topology/raw` and read 0 in every condition,
    # including Weight Matrix -- which looked exactly like F-CANOPY-040's
    # never-fires shape and was completely wrong. That endpoint is fetched
    # SERVER-SIDE by canopy's own handler (`requests.get` inside
    # `_update_raw_topology_store_handler`), so it never crosses the browser and
    # Playwright cannot see it. A driver that counts the wrong traffic reports a
    # confident zero.
    #
    # The gate's observable effect is the STORE: empty while the view is Node
    # Graph, populated once it is Weight Matrix. That is two-sided -- a poll that
    # never fires fails the second half (F-CANOPY-040's shape) and a poll with no
    # gate at all fails the first.
    RAW_STORE = f"{NV}-raw-topology-store"
    set_radio(page, f"{NV}-display-mode", "node_graph")
    settle_figure(page, budget_s=25)
    # Give the 5 s tick several chances to (wrongly) fill it.
    page.wait_for_timeout(13000)
    entry_read = _store(page, RAW_STORE)
    if not entry_read.get("ok"):
        # Refuse to score rather than read "unreadable" as "empty" -- doing exactly
        # that produced a confident FAIL against a working gate on the first run.
        res["M-TOPOLOGY-18"] = {"verdict": "BLOCKED", "reason": f"raw-topology store is unreadable: {entry_read.get('via')}", "read": entry_read}
        log(f"  M-TOPOLOGY-18 -> BLOCKED (store unreadable: {entry_read.get('via')}) -- NOT scored as empty")
        empty_in_node_graph = populated_in_weight_matrix = None
        fill_s = None
        after_store = None
    else:
        empty_in_node_graph = not entry_read.get("value")

        set_radio(page, f"{NV}-display-mode", "weight_matrix")
        filled, fill_s, _ = wait_for(lambda: bool(store_value(page, RAW_STORE)), budget_s=45, every_s=1.0, label="raw-topology store to fill in Weight Matrix")
        after_store = store_value(page, RAW_STORE)
        populated_in_weight_matrix = bool(after_store)

    set_radio(page, f"{NV}-display-mode", "node_graph")
    settle_figure(page, budget_s=25)

    # Only score when the store was actually READABLE; the BLOCKED entry above
    # already stands otherwise, and overwriting it here would reinstate exactly the
    # "unreadable scored as empty" mistake this row was rewritten to avoid.
    if empty_in_node_graph is not None:
        # An entry state that was ALREADY populated cannot test the first half, so
        # say so rather than scoring a half-measured row.
        if not empty_in_node_graph and populated_in_weight_matrix:
            m18 = "INDETERMINATE"
        elif empty_in_node_graph and populated_in_weight_matrix:
            m18 = "PASS"
        else:
            m18 = "FAIL"
        res["M-TOPOLOGY-18"] = {
            "verdict": m18,
            "empty_in_node_graph": empty_in_node_graph,
            "populated_in_weight_matrix": populated_in_weight_matrix,
            "fill_seconds": fill_s,
            "store_keys_after": sorted(after_store.keys()) if isinstance(after_store, dict) else type(after_store).__name__,
        }
        log(f"  M-TOPOLOGY-18 raw-store gate: empty_in_node_graph={empty_in_node_graph} populated_in_weight_matrix={populated_in_weight_matrix} (filled in {fill_s}s) -> {m18}")
        if not populated_in_weight_matrix:
            log("  !! the store never filled even in Weight Matrix -- that is F-CANOPY-040's shape, not a gate that is too tight")
        if not empty_in_node_graph:
            log("  !! the store already held data in Node Graph -- either the gate is gone, or an earlier step filled it (hence INDETERMINATE)")

    # ---- M-TOPOLOGY-13 / W4-14 -- zoom is captured AND re-applied ---------
    # Instrumented the same way the click rows are: a drag that produces no
    # `plotly_relayout` is a DRIVER failure, and scoring it as a product FAIL would
    # file the finding against the wrong thing (M-TOPOLOGY-11's box-select drag
    # produced zero events and is recorded as an unpinned idiom, not a defect).
    settle_figure(page, budget_s=30)
    scroll_graph_into_view(page)
    page.evaluate(
        """(id) => { const root = document.getElementById(id);
             const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
             window.__jn_relayouts = 0;
             if (gd && gd.on) gd.on('plotly_relayout', () => { window.__jn_relayouts++; });
             if (gd && window.Plotly) window.Plotly.relayout(gd, {dragmode: 'zoom'}); }""",
        f"{NV}-graph",
    )
    page.wait_for_timeout(1200)

    def axis_ranges():
        return page.evaluate(
            """(id) => { const root = document.getElementById(id);
                 const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                 if (!gd || !gd._fullLayout) return null;
                 const xa = gd._fullLayout.xaxis, ya = gd._fullLayout.yaxis;
                 return {x: xa && xa.range ? xa.range.slice() : null,
                         y: ya && ya.range ? ya.range.slice() : null,
                         dragmode: gd._fullLayout.dragmode || null}; }""",
            f"{NV}-graph",
        )

    before_zoom = axis_ranges()
    geo = point_xy(page, (marker_traces(page) or [{"curve": 0}])[0]["curve"], 0)
    zoomed = {"ok": False}
    if geo.get("ok") and before_zoom:
        p = geo["plot"]
        x0, y0 = p["l"] + p["w"] * 0.30, p["t"] + p["h"] * 0.30
        x1, y1 = p["l"] + p["w"] * 0.70, p["t"] + p["h"] * 0.70
        page.mouse.move(x0, y0)
        page.mouse.down()
        page.mouse.move((x0 + x1) / 2, (y0 + y1) / 2, steps=10)
        page.mouse.move(x1, y1, steps=10)
        page.mouse.up()
        page.wait_for_timeout(2500)
        zoomed = {"ok": True, "from": [x0, y0], "to": [x1, y1]}
    n_relayout = page.evaluate("() => window.__jn_relayouts || 0")
    after_zoom = axis_ranges()
    range_changed = bool(before_zoom and after_zoom and after_zoom.get("x") != before_zoom.get("x"))

    # Force a rebuild and check the range SURVIVES -- that is the row's contract.
    persisted = None
    if range_changed:
        set_checklist(page, f"{NV}-show-weights", False)
        settle_changed(page, (_graph(page) or {}).get("fig_hash"))
        after_rebuild = axis_ranges()
        persisted = bool(after_rebuild and after_rebuild.get("x") == after_zoom.get("x"))
        set_checklist(page, f"{NV}-show-weights", True)
        settle_figure(page, budget_s=25)
    else:
        after_rebuild = None

    if n_relayout == 0:
        m13 = "INDETERMINATE"
    elif range_changed and persisted:
        m13 = "PASS"
    else:
        m13 = "FAIL"
    res["M-TOPOLOGY-13"] = {
        "verdict": m13,
        "plotly_relayout_events": n_relayout, "gesture": zoomed,
        "before": before_zoom, "after_zoom": after_zoom, "after_rebuild": after_rebuild,
        "range_changed": range_changed, "persisted_across_rebuild": persisted,
    }
    log(f"  M-TOPOLOGY-13 zoom/pan: relayout_events={n_relayout} range_changed={range_changed} persisted={persisted} -> {m13}")
    if n_relayout == 0:
        log("  !! the drag produced NO plotly_relayout -- the zoom gesture never reached plotly, so this is a DRIVER gap")
        log("     (same shape as M-TOPOLOGY-11's box select; do NOT file it as a product defect)")

    shot(page, "seg17_topostate.png")
    record("topostate", **res)
    log(f"  topostate verdicts: {[(k, v.get('verdict')) for k, v in res.items() if isinstance(v, dict) and 'verdict' in v]}")


STEPS = {
    "probe": step_probe,
    "topodiag": step_topodiag,
    "rebuildprobe": step_rebuildprobe,
    "wirecensus": step_wirecensus,
    "quietread": step_quietread,
    "topo": step_topo,
    "topoevents": step_topoevents,
    "topostate": step_topostate,
    "topoexport": step_topoexport,
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
