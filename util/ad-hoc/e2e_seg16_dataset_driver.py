#!/usr/bin/env python3
"""
Project: Juniper
Sub-Project: juniper-ml
Application: Canopy E2E Phase 1 -- segment 16 Dataset View (§3.6) driver
Author: Paul Calnon
Version: 0.1.0
License: MIT License

Live driver for the **§3.6 Tab `dataset` -- "Dataset View"** rows of the canopy
E2E click-by-click matrix (M-DATASET-01..27).

Distinct from ``e2e_w6_dataset_driver.py``, which drives the **W6 workflow**
(sidebar stage -> banner -> restart). This one drives the dataset *panel's own*
toolbar, modal, selectors, stat tiles and the sequence (3-D) control set.

Run under the only env that has playwright, with LD_LIBRARY_PATH cleared --
invoking that python directly bypasses the conda hooks that strip it, and an
ambient rust_mudgeon libtorch then breaks module import with
``undefined symbol: _PyObject_NextNotImplemented`` (reads exactly like a test
failure and is not one):

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_seg16_dataset_driver.py --step toolbar,selector

Steps (comma-separated, order preserved):
  start     -- start a training run so a dataset is actually loaded
  toolbar   -- M-DATASET-01 / -02 / -09  (generate modal open, tabs, cancel)
  upload    -- M-DATASET-05 / -07        (file picker contract, URL input)
  selector  -- M-DATASET-10 / -11 / -12  (generator selector, Load, split)
  stats     -- M-DATASET-13 / -14        (four tiles, theme recolour)
  plots     -- M-DATASET-15 / -16        (scatter + distribution, MANUAL class)
  seq       -- M-DATASET-17..27          (sequence control set / 2-D inverse)

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
http_get = _w3.http_get
http_post = _w3.http_post
open_dashboard = _w3.open_dashboard
text_of = _w3.text_of
is_disabled = _w3.is_disabled
input_value = _w3.input_value
dropdown_value = _w3.dropdown_value
dropdown_select = _w3.dropdown_select

DATASET_TAB = "Dataset View"


# --------------------------------------------------------------------------
# Shared probes
# --------------------------------------------------------------------------
def vis(page, el_id: str):
    """Visibility that is honest for position:fixed and for hidden-not-unmounted panels.

    offsetParent is null for position:fixed and is NOT a visibility test; assert
    computed display/visibility plus a real rect instead.
    """
    return page.evaluate(
        """(id) => { const el = document.getElementById(id);
             if (!el) return {present:false};
             const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
             return {present:true, display:cs.display, visibility:cs.visibility,
                     w:Math.round(r.width), h:Math.round(r.height),
                     text:(el.innerText||'').trim().slice(0,140)}; }""",
        el_id,
    )


def attrs(page, el_id: str, names: list[str]):
    return page.evaluate(
        """([id, names]) => { const el = document.getElementById(id);
             if (!el) return null;
             const o = {tag: el.tagName};
             for (const n of names) o[n] = el.getAttribute(n);
             if ('disabled' in el) o.propDisabled = el.disabled;
             return o; }""",
        [el_id, names],
    )


def ensure_no_modal(page, tries: int = 12) -> None:
    """Close the welcome modal, retrying.

    The shared ``dismiss_welcome`` runs once and can report "not present" when it
    fires BEFORE the modal has rendered -- after which an ``aria-modal`` dialog
    silently intercepts every pointer event on the page and each subsequent click
    fails with a 30 s Playwright timeout that looks like a dead control. Poll for
    it instead, and fall back to Escape.
    """
    for i in range(tries):
        state = page.evaluate(
            """() => { const d=[...document.querySelectorAll('[role=dialog]')]
                         .filter(x => (x.className||'').includes('show'));
                       return {open:d.length,
                               closeBtn: !!document.getElementById('welcome-modal-close')}; }"""
        )
        if not state["open"]:
            if i:
                log(f"  modal cleared after {i} attempt(s)")
            return
        page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
        page.wait_for_timeout(700)
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
    log(f"  !! a modal is STILL open after {tries} attempts -- clicks will be intercepted")


def open_tab(page, label: str) -> bool:
    """Activate a right-panel tab. dbc.Tabs' active_tab is what gates the panels."""
    ensure_no_modal(page)
    ok = page.evaluate(
        """(label) => { const t = [...document.querySelectorAll('[role=tab]')]
                          .find(x => x.textContent.trim() === label);
                        if (!t) return false; t.click(); return true; }""",
        label,
    )
    page.wait_for_timeout(3500)
    return bool(ok)


def dash_posts(capture, needle: str, since_ms: int = 0):
    return [c for c in capture if c["t_ms"] >= since_ms and needle in (c.get("url") or "")]


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
def step_start(page, capture):
    """Start a run so cascor actually loads a dataset (/api/dataset loaded:false otherwise)."""
    log("STEP start -- starting a training run so a dataset is loaded")
    before = http_get("/api/dataset")[1]
    log(f"  /api/dataset before: {json.dumps(before)[:120]}")
    page.evaluate("""() => { const b = document.getElementById('start-button'); if (b) b.click(); }""")
    for i in range(40):
        page.wait_for_timeout(3000)
        st = http_get("/api/status")[1]
        if st.get("is_running"):
            log(f"  is_running=True after ~{(i + 1) * 3}s (fsm={st.get('fsm_status')}, phase={st.get('phase')})")
            break
    page.wait_for_timeout(6000)
    # F-CANOPY-004: a plain GET can exceed the 10s default while the callback
    # backlog drains at run start -- the same call is ~30ms when idle.
    ds = http_get("/api/dataset", timeout=90)[1]
    log(f"  /api/dataset after: keys={list(ds)[:12]} loaded={ds.get('loaded')}")
    log(f"  DATASET-META: {json.dumps({k: v for k, v in ds.items() if k != 'inputs' and k != 'targets'})[:400]}")


def step_toolbar(page, capture):
    """M-DATASET-01 (generate modal opens) / -02 (3 modal tabs) / -09 (cancel closes, no request)."""
    log("STEP toolbar -- M-DATASET-01 / -02 / -09")
    open_tab(page, DATASET_TAB)
    log(f"  modal before open: {vis(page, 'dataset-plotter-generate-modal')}")
    page.evaluate("""() => { const b=document.getElementById('dataset-plotter-generate-btn'); if(b) b.click(); }""")
    page.wait_for_timeout(3000)
    log(f"  M-DATASET-01 modal after click: {vis(page, 'dataset-plotter-generate-modal')}")

    tabs = page.evaluate(
        """() => { const root = document.getElementById('dataset-plotter-modal-tabs');
             if (!root) return null;
             return [...root.querySelectorAll('[role=tab], .nav-link')]
                      .map(t => ({text:t.textContent.trim(), cls:(t.className||'').slice(0,40)})); }"""
    )
    log(f"  M-DATASET-02 modal tabs: {json.dumps(tabs)[:400]}")
    for pane in ("dataset-plotter-tab-generate", "dataset-plotter-tab-upload", "dataset-plotter-tab-url"):
        log(f"    pane {pane}: {vis(page, pane)}")

    n_before = len(capture)
    page.evaluate("""() => { const b=document.getElementById('dataset-plotter-gen-cancel'); if(b) b.click(); }""")
    page.wait_for_timeout(3000)
    new_reqs = [c for c in capture[n_before:] if "/api/" in (c.get("url") or "")]
    log(f"  M-DATASET-09 modal after cancel: {vis(page, 'dataset-plotter-generate-modal')}")
    log(f"  M-DATASET-09 /api/ requests during cancel: {len(new_reqs)} -> {json.dumps(new_reqs)[:300]}")


def step_upload(page, capture):
    """M-DATASET-05 (file picker contract + confirm ships disabled) / -07 (type=url fill)."""
    log("STEP upload -- M-DATASET-05 / -07")
    open_tab(page, DATASET_TAB)
    page.evaluate("""() => { const b=document.getElementById('dataset-plotter-generate-btn'); if(b) b.click(); }""")
    page.wait_for_timeout(2500)

    log(f"  M-DATASET-05 upload control: {attrs(page, 'dataset-plotter-import-file-upload', ['accept', 'multiple', 'type'])}")
    inner = page.evaluate(
        """() => { const r=document.getElementById('dataset-plotter-import-file-upload');
             if(!r) return null; const i=r.querySelector('input[type=file]');
             return i ? {accept:i.getAttribute('accept'), multiple:i.hasAttribute('multiple')} : 'no-inner-input'; }"""
    )
    log(f"  M-DATASET-05 inner <input type=file>: {json.dumps(inner)}")
    log(f"  M-DATASET-05 file-name label: {vis(page, 'dataset-plotter-import-file-name')}")
    log(f"  M-DATASET-05 confirm ships disabled: {is_disabled(page, 'dataset-plotter-import-file-confirm')}")

    log(f"  M-DATASET-07 url input attrs: {attrs(page, 'dataset-plotter-import-url-input', ['type', 'placeholder'])}")
    page.evaluate(
        """() => { const el=document.getElementById('dataset-plotter-import-url-input'); if(!el) return;
             const s=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set;
             s.call(el,'https://example.invalid/data.csv');
             el.dispatchEvent(new Event('input',{bubbles:true}));
             el.dispatchEvent(new Event('change',{bubbles:true})); }"""
    )
    page.wait_for_timeout(2500)
    log(f"  M-DATASET-07 url value after fill: {input_value(page, 'dataset-plotter-import-url-input')!r}")
    page.evaluate("""() => { const b=document.getElementById('dataset-plotter-gen-cancel'); if(b) b.click(); }""")
    page.wait_for_timeout(1500)


def step_selector(page, capture):
    """M-DATASET-10 (options + select is inert) / -11 (Load -> 400 LIVE arm) / -12 (split refilter)."""
    log("STEP selector -- M-DATASET-10 / -11 / -12")
    open_tab(page, DATASET_TAB)

    st, gens = http_get("/api/dataset/generators")
    names = [g["name"] for g in gens.get("generators", [])]
    log(f"  /api/dataset/generators -> {st}, {len(names)} generators: {names}")

    opts = page.evaluate(
        """() => { const dd=document.getElementById('dataset-plotter-dataset-selector');
             if(!dd) return null; dd.click(); return true; }"""
    )
    page.wait_for_timeout(1500)
    # SCOPE by the trigger's aria-controls. A bare [role=option] sweep also picks up
    # every OTHER open Radix menu on the page (sidebar switches, view toggles) and
    # manufactures a wrong option list.
    shown = page.evaluate(
        """() => { const dd=document.getElementById('dataset-plotter-dataset-selector');
             const box = document.getElementById(dd.getAttribute('aria-controls'));
             if (!box) return {scoped:false, opts:[]};
             return {scoped:true, opts:[...box.querySelectorAll('[role=option]')].map(o=>o.textContent.trim())}; }"""
    )
    log(f"  M-DATASET-10 scoped option scrape: {json.dumps(shown)[:400]}")
    shown = shown.get("opts", []) if isinstance(shown, dict) else []
    log(f"  M-DATASET-10 selector opened={opts} options={shown}")
    log(f"  M-DATASET-10 default value: {dropdown_value(page, 'dataset-plotter-dataset-selector')!r}")

    n_before = len(capture)
    if shown:
        target = "xor" if "xor" in shown else shown[min(1, len(shown) - 1)]
        page.evaluate(
            """(label) => { const o=[...document.querySelectorAll('[role=option]')]
                   .find(x=>x.textContent.trim()===label); if(o) o.click(); }""",
            target,
        )
        page.wait_for_timeout(4000)
        log(f"  M-DATASET-10 selected {target!r}; value now {dropdown_value(page, 'dataset-plotter-dataset-selector')!r}")
        sel_reqs = [c for c in capture[n_before:] if "/api/dataset" in (c.get("url") or "")]
        log(f"  M-DATASET-10 /api/dataset* requests caused by SELECT alone: {len(sel_reqs)} (expected 0 -- select is inert by design)")
        log(f"    {json.dumps(sel_reqs)[:300]}")

    log(f"  M-DATASET-11 load-status before: {vis(page, 'dataset-plotter-load-status')}")
    n_before = len(capture)
    page.evaluate("""() => { const b=document.getElementById('dataset-plotter-load-selected-btn'); if(b) b.click(); }""")
    for _ in range(20):
        page.wait_for_timeout(2000)
        t = text_of(page, "dataset-plotter-load-status")
        if t:
            break
    log(f"  M-DATASET-11 load-status after: {vis(page, 'dataset-plotter-load-status')}")

    log(f"  M-DATASET-12 split selector: {vis(page, 'dataset-plotter-split-selector')}")
    n_before = len(capture)
    for label in ("Training Only", "Test Only", "All Data"):
        if dropdown_select(page, "dataset-plotter-split-selector", label):
            page.wait_for_timeout(2500)
            log(f"    M-DATASET-12 split -> {label!r}; value={dropdown_value(page, 'dataset-plotter-split-selector')!r}")
    split_reqs = [c for c in capture[n_before:] if "/api/" in (c.get("url") or "")]
    log(f"  M-DATASET-12 /api/ requests during split changes: {len(split_reqs)} (expected 0 -- pure client re-filter)")


def step_stats(page, capture):
    """M-DATASET-13 (four tiles) / -14 (stats summary recolours on theme change)."""
    log("STEP stats -- M-DATASET-13 / -14")
    open_tab(page, DATASET_TAB)
    for tid in (
        "dataset-plotter-sample-count",
        "dataset-plotter-feature-count",
        "dataset-plotter-class-count",
        "dataset-plotter-balance-info",
    ):
        log(f"  M-DATASET-13 {tid}: {vis(page, tid)}")

    before = page.evaluate(
        """() => { const el=document.getElementById('dataset-plotter-stats-summary');
             if(!el) return null; const cs=getComputedStyle(el);
             return {color:cs.color, bg:cs.backgroundColor,
                     html:(el.getAttribute('style')||'').slice(0,120)}; }"""
    )
    log(f"  M-DATASET-14 stats-summary BEFORE theme flip: {json.dumps(before)}")
    page.evaluate("""() => { const b=document.getElementById('dark-mode-toggle'); if(b) b.click(); }""")
    page.wait_for_timeout(6000)
    after = page.evaluate(
        """() => { const el=document.getElementById('dataset-plotter-stats-summary');
             if(!el) return null; const cs=getComputedStyle(el);
             return {color:cs.color, bg:cs.backgroundColor,
                     html:(el.getAttribute('style')||'').slice(0,120),
                     rootDark:document.documentElement.className}; }"""
    )
    log(f"  M-DATASET-14 stats-summary AFTER theme flip:  {json.dumps(after)}")
    log(f"  M-DATASET-14 changed={before != after}")
    page.evaluate("""() => { const b=document.getElementById('dark-mode-toggle'); if(b) b.click(); }""")
    page.wait_for_timeout(4000)


def step_plots(page, capture):
    """M-DATASET-15 (scatter) / -16 (distribution, modebar off)."""
    log("STEP plots -- M-DATASET-15 / -16")
    open_tab(page, DATASET_TAB)
    for pid in ("dataset-plotter-scatter-plot", "dataset-plotter-distribution-plot"):
        info = page.evaluate(
            """(id) => { const el=document.getElementById(id); if(!el) return {present:false};
                 const r=el.getBoundingClientRect();
                 const gd=el.querySelector('.js-plotly-plot')||el;
                 let traces=null, pts=null;
                 try { traces = gd.data ? gd.data.length : null;
                       pts = (gd.data && gd.data[0] && (gd.data[0].x||[]).length) || 0; } catch(e){}
                 return {present:true, w:Math.round(r.width), h:Math.round(r.height),
                         traces, pts, modebar: !!el.querySelector('.modebar'),
                         text:(el.innerText||'').trim().slice(0,100)}; }""",
            pid,
        )
        log(f"  {pid}: {json.dumps(info)}")


def step_seq(page, capture):
    """M-DATASET-17..26 (sequence control set) and -27 (the 2-D inverse: all stay hidden)."""
    log("STEP seq -- M-DATASET-17..27")
    open_tab(page, DATASET_TAB)
    # F-CANOPY-004: a plain GET can exceed the 10s default while the callback
    # backlog drains at run start -- the same call is ~30ms when idle.
    ds = http_get("/api/dataset", timeout=90)[1]
    log(f"  /api/dataset loaded={ds.get('loaded')} keys={list(ds)[:12]}")
    seq_ids = [
        "dataset-plotter-seq-controls",
        "dataset-plotter-seq-mode",
        "dataset-plotter-seq-group-signals",
        "dataset-plotter-seq-window-single",
        "dataset-plotter-seq-signal-select",
        "dataset-plotter-seq-group-windows",
        "dataset-plotter-seq-signal-single",
        "dataset-plotter-seq-window-multi",
        "dataset-plotter-seq-arrange",
        "dataset-plotter-seq-target-toggle",
        "dataset-plotter-seq-target-plot",
        "dataset-plotter-seq-grid-toggle",
        "dataset-plotter-seq-grid-container",
        "dataset-plotter-seq-char-toggle",
        "dataset-plotter-seq-char-collapse",
        "dataset-plotter-seq-char-companion",
    ]
    for sid in seq_ids:
        log(f"  {sid}: {json.dumps(vis(page, sid))}")


def step_wire(page, capture):
    """Does the dataset store fill, and do its consumers fire?

    The shared ``capture`` records REQUESTS only. A component id in a request
    proves nothing -- every fire of a many-Input callback names them all. Only
    the value carried in the RESPONSE is evidence, so hook fetch and match
    against the FULL response text (never a slice: real responses on this page
    run to hundreds of KB) with counters that never evict.
    """
    log("STEP wire -- does dataset-plotter-dataset-store fill, and do consumers fire?")
    open_tab(page, DATASET_TAB)
    page.evaluate(
        """() => {
          window.__w = {n:0, hits:{}, samples:{}};
          const WATCH = ['dataset-plotter-dataset-store','dataset-plotter-sample-count',
                         'dataset-plotter-scatter-plot','dataset-plotter-distribution-plot',
                         'dataset-plotter-balance-info'];
          for (const k of WATCH) window.__w.hits[k]=0;
          const orig = window.fetch;
          window.fetch = async function(...a) {
            const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
            const res = await orig.apply(this,a);
            try { if (url.includes('_dash-update-component')) {
              res.clone().text().then(t => { const w=window.__w; w.n++;
                for (const k of WATCH) if (t.includes(k)) { w.hits[k]++;
                  if (!w.samples[k]) { const i=t.indexOf(k); w.samples[k]=t.slice(Math.max(0,i-20), i+200); } } }).catch(()=>{});
            } } catch(e){}
            return res;
          };
        }"""
    )
    for wait_s in (30, 60, 90):
        page.wait_for_timeout(30000)
        out = page.evaluate("""() => ({n:window.__w.n, hits:window.__w.hits})""")
        log(f"  after ~{wait_s}s on the dataset tab: {json.dumps(out)}")
    samples = page.evaluate("""() => window.__w.samples""")
    for k, v in (samples or {}).items():
        log(f"  SAMPLE {k}: {v[:220]}")
    for tid in ("dataset-plotter-sample-count", "dataset-plotter-feature-count", "dataset-plotter-class-count"):
        log(f"  tile {tid} now: {vis(page, tid)}")


def step_inputs(page, capture):
    """Are the plot callback's 9 Inputs actually RENDERED?

    Dash will not dispatch a callback whose Input component is missing from the
    rendered tree (silently, under suppress_callback_exceptions). Probe each Input
    after a LONG settle -- a short settle already produced one false 'absent'
    (split-selector), so patience is part of the measurement.
    """
    log("STEP inputs -- is every Input of the 6-output plot callback rendered?")
    open_tab(page, DATASET_TAB)
    page.wait_for_timeout(90000)
    ids = ["dataset-plotter-dataset-store", "dataset-plotter-split-selector", "theme-state",
           "dataset-plotter-seq-signal-select", "dataset-plotter-seq-arrange",
           "dataset-plotter-seq-mode", "dataset-plotter-seq-window-single",
           "dataset-plotter-seq-signal-single", "dataset-plotter-seq-window-multi"]
    for i in ids:
        present = page.evaluate("""(id) => !!document.getElementById(id)""", i)
        log(f"  Input {i:<44} renderedInDOM={present}")


def step_ctxmenu(page, capture):
    """M-TUTORIAL-04 and M-SNAPSHOTS-19 -- both are CUSTOM JS context menus, not
    browser-native ones, so both are drivable despite the matrix's MANUAL class.

    context_menus.js builds #juniper-context-menu with a 'View tutorial' button;
    snapshot_context_menu.js builds #juniper-snapshot-context-menu with the four
    operation entries.
    """
    log("STEP ctxmenu -- M-TUTORIAL-04 / M-SNAPSHOTS-19")

    # ---- M-TUTORIAL-04: right-click a tooltipped control ----
    open_tab(page, "Training Metrics")
    target = "nn-learning-rate-input"
    present = page.evaluate("(id) => !!document.getElementById(id)", target)
    log(f"  right-click target #{target} present={present}")
    try:
        page.locator(f"#{target}").first.click(button="right", timeout=15000)
    except Exception as e:
        log(f"  right-click via locator raised ({type(e).__name__}); falling back to dispatched event")
        page.evaluate(
            """(id) => { const el=document.getElementById(id); if(!el) return;
                 const r=el.getBoundingClientRect();
                 el.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,
                     clientX:Math.round(r.left+r.width/2), clientY:Math.round(r.top+r.height/2)})); }""",
            target,
        )
    page.wait_for_timeout(2500)
    menu = page.evaluate(
        """() => { const m=document.getElementById('juniper-context-menu');
             if(!m) return {present:false};
             const cs=getComputedStyle(m); const r=m.getBoundingClientRect();
             return {present:true, display:cs.display, w:Math.round(r.width), h:Math.round(r.height),
                     items:[...m.querySelectorAll('button')].map(b=>b.textContent.trim()),
                     text:(m.innerText||'').trim().slice(0,180)}; }"""
    )
    log(f"  M-TUTORIAL-04 context menu: {json.dumps(menu)[:400]}")
    if menu.get("present") and menu.get("display") != "none":
        clicked = page.evaluate(
            """() => { const m=document.getElementById('juniper-context-menu');
                 const b=[...m.querySelectorAll('button')].find(x=>x.textContent.includes('View tutorial'));
                 if(!b) return false; b.click(); return true; }"""
        )
        log(f"  clicked 'View tutorial' = {clicked}")
        for _ in range(20):
            page.wait_for_timeout(2000)
            act = page.evaluate(
                """() => { const t=[...document.querySelectorAll('#visualization-tabs a, #visualization-tabs button')]
                       .filter(a=>(a.className||'').includes('active')).map(a=>a.textContent.trim());
                     return t; }"""
            )
            if act and act[0] == "Tutorial":
                break
        log(f"  M-TUTORIAL-04 active tab after: {act}")

    # ---- M-SNAPSHOTS-19: right-click a snapshot row ----
    open_tab(page, "Snapshots")
    page.wait_for_timeout(6000)
    inv = page.evaluate(
        """() => ({ids:[...document.querySelectorAll('[id^="hdf5-snapshots-panel"]')]
                       .map(e=>e.id).slice(0,25),
                    tables:document.querySelectorAll('table').length,
                    anyTr:document.querySelectorAll('table tbody tr').length,
                    opBtns:document.querySelectorAll('[id*="snapshot-op-btn"]').length})"""
    )
    log(f"  snapshot panel inventory: {json.dumps(inv)[:600]}")
    rows = {"rows": inv.get("anyTr", 0)}
    log(f"  snapshot table rows: {json.dumps(rows)}")
    # snapshot_context_menu.js walks up from the event target for data-snapshot-row
    # and reads data-snapshot-id. If the rendered rows lack those, the menu can
    # never open regardless of how the contextmenu event is delivered.
    hooks = page.evaluate(
        """() => ({rowAttr: document.querySelectorAll('[data-snapshot-row]').length,
                   idAttr: document.querySelectorAll('[data-snapshot-id]').length,
                   sampleRowHTML: (() => { const tr=document.querySelector('table tbody tr');
                       return tr ? tr.outerHTML.slice(0,240) : null; })()})"""
    )
    log(f"  M-SNAPSHOTS-19 menu hooks: {json.dumps(hooks)[:500]}")
    # Use the PANEL'S OWN ids. A bare 'table tbody tr' sweep counts the Network
    # Info detail table and reports rows that have nothing to do with snapshots.
    panel = page.evaluate(
        """() => { const tb=document.getElementById('hdf5-snapshots-panel-table-body');
             const es=document.getElementById('hdf5-snapshots-panel-empty-state');
             const st=document.getElementById('hdf5-snapshots-panel-status');
             const csEs = es ? getComputedStyle(es) : null;
             return {tableBodyRows: tb ? tb.querySelectorAll('tr').length : 'ABSENT',
                     tableBodyText: tb ? (tb.innerText||'').trim().slice(0,120) : null,
                     emptyStateDisplay: csEs ? csEs.display : 'ABSENT',
                     emptyStateText: es ? (es.innerText||'').trim().slice(0,120) : null,
                     statusText: st ? (st.innerText||'').trim().slice(0,120) : null}; }"""
    )
    log(f"  M-SNAPSHOTS-19 PANEL: {json.dumps(panel)[:600]}")
    page.evaluate(
        """() => { const btn=document.querySelector('[id*="snapshot-op-btn"]');
             const tr = btn ? btn.closest('tr') : document.querySelector('table tbody tr');
             if(!tr) return;
             const r=tr.getBoundingClientRect();
             tr.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,
                 clientX:Math.round(r.left+r.width/2), clientY:Math.round(r.top+r.height/2)})); }"""
    )
    page.wait_for_timeout(2500)
    smenu = page.evaluate(
        """() => { const m=document.getElementById('juniper-snapshot-context-menu');
             if(!m) return {present:false};
             const cs=getComputedStyle(m); const r=m.getBoundingClientRect();
             return {present:true, display:cs.display, w:Math.round(r.width), h:Math.round(r.height),
                     text:(m.innerText||'').trim().slice(0,220)}; }"""
    )
    log(f"  M-SNAPSHOTS-19 snapshot context menu: {json.dumps(smenu)[:400]}")

    # ---- M-SNAPSHOTS-20/-21: do the swap-restore buttons exist at all? ----
    swap = page.evaluate(
        """() => ({pre: document.querySelectorAll('[id*="swap-restore-pre-btn"]').length,
                   post: document.querySelectorAll('[id*="swap-restore-post-btn"]').length,
                   swapCards: document.body.innerText.includes('dataset swap')
                              || document.body.innerText.includes('Dataset swap')})"""
    )
    log(f"  M-SNAPSHOTS-20/-21 swap-restore buttons in DOM: {json.dumps(swap)}")


def step_badge(page, capture):
    """C2.4-02 -- the `WS: Demo` badge, DEMO lane only.

    isolated_stack.bash hard-codes JUNIPER_CANOPY_DEMO_MODE=0 inside its nohup env
    list, so this lane requires a HAND-LAUNCHED canopy. That launch must clear
    LD_LIBRARY_PATH: the demo backend imports torch (demo_backend.py:45) where the
    service backend does not, so an ambient rust_mudgeon libtorch aborts startup
    with `undefined symbol: _PyObject_NextNotImplemented`.

    Point the driver at it with JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8053.
    """
    log("STEP badge -- C2.4-02 (WS: Demo)")
    hp = http_get("/v1/health", timeout=60)[1]
    log(f"  /v1/health demo_mode={hp.get('demo_mode')} (must be True for this lane)")
    sh = http_get("/api/stream_health", timeout=60)[1]
    log(f"  /api/stream_health overall={sh.get('overall')!r} mode={sh.get('mode')!r}")
    b = None
    for _ in range(20):
        page.wait_for_timeout(3000)
        b = page.evaluate(
            """() => { const el=document.getElementById('ws-connection-indicator');
                 if(!el) return null; const cs=getComputedStyle(el);
                 return {text:(el.innerText||'').trim(), color:cs.color, bg:cs.backgroundColor}; }"""
        )
        if b and "demo" in (b.get("text") or "").lower():
            break
    log(f"  C2.4-02 badge: {json.dumps(b)}")


def step_degraded(page, capture):
    """C2.4-05 (WS: Upstream degraded badge) and M-WORKERS-02 (worker error display).

    Requires the degraded induction ALREADY in place: relay healthy + control
    unhealthy. Induce it by restarting CASCOR with a control-WS origin allowlist
    that excludes canopy -- taking cascor down entirely yields 'reconnecting',
    not 'degraded' (get_stream_health: overall = relay status, then downgraded to
    'degraded' only when relay is healthy AND control is not).

    Never restart CANOPY for this: W14's T-2 silent demo fallback would re-create
    a demo backend while /v1/health still reads ok, and every later verdict would
    be scored against demo.
    """
    log("STEP degraded -- C2.4-05 / M-WORKERS-02")
    sh = http_get("/api/stream_health", timeout=60)[1]
    log(
        f"  /api/stream_health overall={sh.get('overall')!r} "
        f"relay={(sh.get('relay') or {}).get('status')!r} control={(sh.get('control') or {}).get('status')!r}"
    )
    hp = http_get("/v1/health", timeout=60)[1]
    log(f"  /v1/health demo_mode={hp.get('demo_mode')} (must be False -- else the T-2 fallback happened)")

    b = None
    for _ in range(20):
        page.wait_for_timeout(3000)
        b = page.evaluate(
            """() => { const el=document.getElementById('ws-connection-indicator');
                 if(!el) return null; const cs=getComputedStyle(el);
                 return {text:(el.innerText||'').trim(), color:cs.color,
                         bg:cs.backgroundColor, style:el.getAttribute('style')}; }"""
        )
        if b and "degrad" in (b.get("text") or "").lower():
            break
    log(f"  C2.4-05 badge: {json.dumps(b)}")

    open_tab(page, "Workers")
    w = None
    for _ in range(20):
        page.wait_for_timeout(3000)
        w = vis(page, "worker-panel-error-display")
        if w.get("present") and w.get("h"):
            break
    log(f"  M-WORKERS-02 worker-panel-error-display: {json.dumps(w)}")
    others = page.evaluate(
        """() => [...document.querySelectorAll('[id^="worker-panel"]')]
             .map(e=>({id:e.id, txt:(e.innerText||'').trim().slice(0,60)})).slice(0,12)"""
    )
    log(f"  worker panel ids: {json.dumps(others)[:500]}")


def step_inventory(page, capture):
    """Dump every dataset-plotter-* id actually in the DOM, with honest visibility.

    Read id lists from the DOM inventory rather than assuming a control is absent
    because one getElementById returned null at an unlucky moment.
    """
    log("STEP inventory -- every dataset-plotter-* id present, with visibility")
    open_tab(page, DATASET_TAB)
    # Settle times on this dashboard are far longer than 1.5-2s; poll for the
    # panel to stop growing rather than sampling once.
    prev = -1
    for _ in range(12):
        page.wait_for_timeout(2500)
        n = page.evaluate("""() => document.querySelectorAll('[id^="dataset-plotter-"]').length""")
        if n == prev and n:
            break
        prev = n
    log(f"  settled at {prev} elements")
    log(f"  any id containing 'split': {page.evaluate('''() => [...document.querySelectorAll('[id*=split]')].map(e=>e.id)''')}")
    # The toolbar's "Split:" <label> carries no id. If the LABEL rendered but the
    # dropdown did not, the failure is specific to that component; if neither
    # rendered, the toolbar was truncated after load-status.
    log(
        "  toolbar tail probe: "
        + json.dumps(
            page.evaluate(
                """() => { const lbls=[...document.querySelectorAll('label')].map(l=>l.textContent.trim());
                     const tb=document.getElementById('dataset-plotter-load-status');
                     const parent=tb?tb.parentElement:null;
                     return {splitLabelPresent: lbls.includes('Split:'),
                             datasetLabelPresent: lbls.includes('Dataset:'),
                             toolbarChildIds: parent?[...parent.children].map(c=>c.id||c.tagName):null,
                             toolbarText: parent?(parent.innerText||'').trim().slice(0,160):null}; }"""
            )
        )
    )
    rows = page.evaluate(
        """() => [...document.querySelectorAll('[id^="dataset-plotter-"]')].map(el => {
             const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
             return {id: el.id, tag: el.tagName, display: cs.display,
                     w: Math.round(r.width), h: Math.round(r.height)}; })"""
    )
    log(f"  {len(rows)} dataset-plotter-* elements in DOM")
    for r in rows:
        log(f"    {r['id']:<48} {r['tag']:<8} display={r['display']:<12} {r['w']}x{r['h']}")


STEPS = {
    "start": step_start,
    "inventory": step_inventory,
    "wire": step_wire,
    "inputs": step_inputs,
    "ctxmenu": step_ctxmenu,
    "badge": step_badge,
    "degraded": step_degraded,
    "toolbar": step_toolbar,
    "upload": step_upload,
    "selector": step_selector,
    "stats": step_stats,
    "plots": step_plots,
    "seq": step_seq,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", required=True, help="comma-separated step names (order preserved): " + ", ".join(STEPS))
    args = ap.parse_args()

    wanted = [s.strip() for s in args.step.split(",") if s.strip()]
    bad = [s for s in wanted if s not in STEPS]
    if bad:
        print(f"unknown step(s): {bad}; known: {list(STEPS)}", file=sys.stderr)
        return 2

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            for name in wanted:
                log("=" * 78)
                STEPS[name](page, capture)
        finally:
            log("=" * 78)
            log(f"captured {len(capture)} requests")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
