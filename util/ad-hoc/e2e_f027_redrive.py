#!/usr/bin/env python3
"""
Project: Juniper
Sub-Project: juniper-ml
Application: Canopy E2E Phase 2 -- F-CANOPY-027 live-run re-drive driver
Author: Paul Calnon
Version: 0.1.0
License: MIT License

Live re-drive of the matrix rows F-CANOPY-027 froze, after the Stage 1+3
remediation (juniper-canopy#507 + #509): M-CANDIDATES-01/-02/-03/-04/-06
(previously PASS against mount defaults only), -07/-09/-10/-11, and
M-BOUNDARIES-01/-02/-03/-04.  M-DATASET-13/-15/-16 are re-driven separately by
``e2e_seg16_dataset_driver.py --step stats,plots`` against the same live run.

Run under the only env that has playwright, with LD_LIBRARY_PATH cleared --
invoking that python directly bypasses the conda hooks that strip it, and an
ambient rust_mudgeon libtorch then breaks module import:

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_redrive.py --step idle,start,candidates,history,boundaries

Steps (comma-separated, order preserved):
  idle        -- A-arm: pre-run defaults on Candidate Metrics + Decision Boundary
  start       -- click start-button, wait for /api/status is_running (seg16 idiom)
  candidates  -- M-CANDIDATES-01/-02/-03/-04/-06/-07: live-value timeline during the run
  history     -- M-CANDIDATES-09/-10/-11: populated history cards + inert header click
  boundaries  -- M-BOUNDARIES-04/-01/-02/-03: status transition, slider, confidence, refresh

Observation discipline (arc traps): poll for TRANSITIONS with long budgets (settle
times ran 3-39 s under F-CANOPY-004 congestion), read figures off the plotly gd
object rather than the DOM text alone, subscribe to store changes rather than
sampling where cadence matters, and use each component's own exact ids.

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_w3drv", os.path.join(_HERE, "e2e_w3_params_driver.py"))
_w3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w3)

log = _w3.log
http_get = _w3.http_get
http_post = _w3.http_post
open_dashboard = _w3.open_dashboard

CAND_TAB = "Candidate Metrics"
BOUND_TAB = "Decision Boundary"
CID = "candidate-metrics-panel"
DID = "decision-boundary"
SHOTS = os.environ.get("JUNIPER_E2E_SHOTS_DIR", "/tmp/juniper-e2e/shots")

# Redux store access (verbatim idiom from e2e_f027_subscribe_watch.py -- fiber walk).
FIND_STORE = """
() => {
  if (window.__dashStore) return true;
  function fiberOf(el) {
    for (const k of Object.keys(el)) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')
          || k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  for (const sel of ['#react-entry-point', '#_dash-app-content', 'body']) {
    const el = document.querySelector(sel);
    if (!el) continue;
    let f = fiberOf(el), hops = 0;
    while (f && hops < 4000) {
      const mp = f.memoizedProps;
      if (mp && mp.store && typeof mp.store.getState === 'function') {
        window.__dashStore = mp.store; return true;
      }
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return false;
}
"""

SUBSCRIBE = """
(ids) => {
  if (window.__rdUnsub) { try { window.__rdUnsub(); } catch (e) {} }
  window.__rd = {t0: Date.now(), n: 0, series: {}};
  for (const id of ids) window.__rd.series[id] = [];
  const st = window.__dashStore;
  const walk = (obj, path) => path.reduce((o,k) => (o == null ? o : o[k]), obj);
  const read = (state, id) => {
    try {
      const strs = (state.paths && state.paths.strs) ? state.paths.strs : state.paths;
      const p = strs ? strs[id] : null;
      if (!p) return 'NO-PATH';
      const node = walk(state.layout, p);
      if (node == null) return 'NO-NODE';
      const d = node.props ? node.props.data : undefined;
      if (d === undefined) return 'NO-DATA';
      const s = JSON.stringify(d);
      return s.length > 60 ? (s.slice(0, 60) + '...len=' + s.length) : s;
    } catch (e) { return 'ERR'; }
  };
  window.__rdUnsub = st.subscribe(() => {
    const S = window.__rd;
    S.n++;
    const state = st.getState();
    for (const id of ids) {
      const v = read(state, id);
      const arr = S.series[id];
      if (!arr.length || arr[arr.length-1].v !== v) {
        arr.push({n: S.n, t: Date.now() - S.t0, v});
        if (arr.length > 4000) arr.shift();
      }
    }
  });
  return true;
}
"""


# --------------------------------------------------------------------------
# Shared probes (seg16 idioms)
# --------------------------------------------------------------------------
def vis(page, el_id: str):
    """Honest visibility: computed style + rect + text (fixed-position safe)."""
    return page.evaluate(
        """(id) => { const el = document.getElementById(id);
             if (!el) return {present:false};
             const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
             return {present:true, display:cs.display, visibility:cs.visibility,
                     bg:cs.backgroundColor, w:Math.round(r.width), h:Math.round(r.height),
                     text:(el.innerText||'').trim().slice(0,140)}; }""",
        el_id,
    )


def fig_info(page, container_id: str):
    """Read the plotly figure off the gd object inside a dcc.Graph container."""
    return page.evaluate(
        """(id) => { const root = document.getElementById(id);
             if (!root) return {present:false};
             const gd = (root.classList && root.classList.contains('js-plotly-plot'))
                          ? root : root.querySelector('.js-plotly-plot');
             const r = root.getBoundingClientRect();
             const out = {present:true, w:Math.round(r.width), h:Math.round(r.height),
                          plotly: !!gd, modebar: !!root.querySelector('.modebar'),
                          traces: [], annotations: [], sig: 0, fig_hash: null,
                          text:(root.innerText||'').trim().slice(0,100)};
             if (gd && gd.data) {
               out.traces = gd.data.map(t => ({type: t.type || 'scatter', name: t.name || '',
                                               nx: (t.x && t.x.length) || 0, nz: (t.z && t.z.length) || 0,
                                               visible: t.visible === undefined ? true : t.visible}));
               // ``sig`` is a LENGTH, kept unchanged so every sig recorded in the
               // ledger and matrix stays comparable. It is a weak proxy: two
               // different figures can share a byte COUNT, which is exactly what
               // made M-TOPOLOGY-01's distinct_sigs wobble 3->2->3 across runs on
               // an unchanged topology. Prefer ``fig_hash`` for "did the figure
               // change"; keep ``sig`` for continuity with historical records.
               try { out.sig = JSON.stringify(gd.data).length; } catch (e) { out.sig = -1; }
               try {
                 const s = JSON.stringify(gd.data);
                 let h = 0x811c9dc5;                       // FNV-1a, 32-bit
                 for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
                 out.fig_hash = h.toString(16);
               } catch (e) { out.fig_hash = null; }
             }
             if (gd && gd.layout && gd.layout.annotations)
               out.annotations = gd.layout.annotations.map(a => (a.text || '').slice(0, 80));
             // ``plot_area`` = the fraction of the figure the subplots actually
             // occupy. A trace that EXISTS is not a trace that is VISIBLE: a
             // subplot figure whose vertical_spacing equals plotly's own limit
             // renders every row at ZERO height, so the trace objects are all
             // present and the canvas is blank. F-CANOPY-041b shipped exactly
             // that, and M-TOPOLOGY-03's "a heatmap trace exists" predicate
             // passed on it. Any row asserting that something RENDERED must
             // check this, not just the trace list.
             if (gd && gd.layout) {
               let area = 0, n = 0;
               for (const k in gd.layout) {
                 const ax = gd.layout[k];
                 if (k.indexOf('yaxis') === 0 && ax && ax.domain && ax.domain.length === 2) {
                   area += (ax.domain[1] - ax.domain[0]); n++;
                 }
               }
               out.plot_area = Math.round(area * 1000) / 1000;
               out.n_yaxes = n;
             }
             return out; }""",
        container_id,
    )


def ensure_no_modal(page, tries: int = 12) -> None:
    """Close the welcome modal, retrying (it intercepts every click while open)."""
    for i in range(tries):
        n_open = page.evaluate(
            """() => [...document.querySelectorAll('[role=dialog]')]
                     .filter(x => (x.className||'').includes('show')).length"""
        )
        if not n_open:
            if i:
                log(f"  modal cleared after {i} attempt(s)")
            return
        page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
        page.wait_for_timeout(700)
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
    log(f"  !! a modal is STILL open after {tries} attempts -- clicks will be intercepted")


def open_tab(page, label: str) -> bool:
    """Activate a right-panel tab; dbc.Tabs' active_tab gates the per-tab poll lanes."""
    ensure_no_modal(page)
    ok = page.evaluate(
        """(label) => { const t = [...document.querySelectorAll('[role=tab]')]
                          .find(x => x.textContent.trim() === label);
                        if (!t) return false; t.click(); return true; }""",
        label,
    )
    page.wait_for_timeout(3500)
    return bool(ok)


def shot(page, name: str) -> str:
    os.makedirs(SHOTS, exist_ok=True)
    path = os.path.join(SHOTS, name)
    try:
        page.screenshot(path=path)
        log(f"  screenshot: {path}")
    except Exception as exc:  # noqa: BLE001
        log(f"  screenshot FAILED ({name}): {exc}")
    return name


def api_state_slice() -> dict:
    """Server-truth slice of /api/state for cross-checks (candidate + history fields)."""
    try:
        st = http_get("/api/state", timeout=30)[1]
    except Exception as exc:  # noqa: BLE001
        return {"_err": str(exc)[:80]}
    keys = (
        "is_running",
        "phase",
        "current_epoch",
        "candidate_pool_status",
        "candidate_pool_phase",
        "candidate_pool_size",
        "candidate_epoch",
        "candidate_total_epochs",
        "top_candidate_id",
        "top_candidate_score",
        "current_hidden_units",
    )
    out = {k: st.get(k) for k in keys if k in st}
    out["n_epochs"] = len(st.get("epochs") or [])
    out["n_phases_cand"] = sum(1 for p in (st.get("phases") or []) if "candidate" in str(p))
    return out


def cand_snapshot(page) -> dict:
    """One sample of every M-CANDIDATES observable."""
    badge = vis(page, f"{CID}-status-badge")
    phase = vis(page, f"{CID}-phase")
    pool = vis(page, f"{CID}-pool-size")
    prog = vis(page, f"{CID}-progress-section")
    prog_bar = vis(page, f"{CID}-epoch-progress")
    info = vis(page, f"{CID}-pool-info")
    loss = fig_info(page, f"{CID}-loss-plot")
    return {
        "badge": badge.get("text"),
        "badge_bg": badge.get("bg"),
        "phase": phase.get("text"),
        "pool": pool.get("text"),
        "prog_display": prog.get("display"),
        "prog_label": prog_bar.get("text"),
        "info": (info.get("text") or "")[:90].replace("\n", " / "),
        "loss_traces": loss.get("traces"),
        "loss_ann": loss.get("annotations"),
        "loss_wh": (loss.get("w"), loss.get("h")),
    }


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
def step_idle(page, capture):
    """A-arm: capture both panels' pre-run defaults for the A/B record."""
    log("STEP idle -- pre-run defaults (A-arm)")
    open_tab(page, CAND_TAB)
    page.wait_for_timeout(4000)
    snap = cand_snapshot(page)
    log(f"  IDLE candidates: {json.dumps(snap)[:500]}")
    hist = page.evaluate(
        """() => [...document.querySelectorAll('[id*="history-pool-header"]')].length"""
    )
    log(f"  IDLE history cards: {hist}")
    shot(page, "F027-REDRIVE__candidates_idle.png")
    open_tab(page, BOUND_TAB)
    page.wait_for_timeout(4000)
    status = vis(page, f"{DID}-status")
    fig = fig_info(page, f"{DID}-plot")
    log(f"  IDLE boundary status: {json.dumps(status)[:200]}")
    log(f"  IDLE boundary fig: {json.dumps(fig)[:300]}")
    shot(page, "F027-REDRIVE__boundaries_idle.png")
    log(f"  IDLE /api/state: {json.dumps(api_state_slice())}")


def step_start(page, capture):
    """Start a training run (seg16 idiom): click start-button, wait for is_running."""
    log("STEP start -- starting a training run")
    ensure_no_modal(page)
    before = http_get("/api/dataset")[1]
    log(f"  /api/dataset before: {json.dumps(before)[:120]}")
    page.evaluate("""() => { const b = document.getElementById('start-button'); if (b) b.click(); }""")
    for i in range(40):
        page.wait_for_timeout(3000)
        st = http_get("/api/status", timeout=60)[1]
        if st.get("is_running"):
            log(f"  is_running=True after ~{(i + 1) * 3}s (fsm={st.get('fsm_status')}, phase={st.get('phase')})")
            break
    else:
        log("  !! is_running never became True within ~120s")
    ds = http_get("/api/dataset", timeout=90)[1]
    meta = {k: v for k, v in ds.items() if k not in ("inputs", "targets")}
    log(f"  DATASET-META: {json.dumps(meta)[:400]}")


def step_candidates(page, capture, budget_s: int = 480):
    """M-CANDIDATES-01/-02/-03/-04/-06/-07: timeline of live values during the run.

    Candidate phases measured ~10-30 s on this box (run 1: 11 grow iterations in
    ~4.5 min), so sample the DOM at 700 ms and SUBSCRIBE to the panel's own
    training-state-store -- a 3 s sampler missed every candidate phase of run 1.
    """
    log("STEP candidates -- M-CANDIDATES-01/-02/-03/-04/-06/-07 live timeline")
    open_tab(page, CAND_TAB)
    if page.evaluate(FIND_STORE):
        page.evaluate(SUBSCRIBE, [f"{CID}-training-state-store"])
        log("  subscribed to candidate-metrics-panel-training-state-store")
    else:
        log("  !! redux store not reachable -- store-fill series unavailable")
    t0 = time.time()
    last = None
    seen_live_badge = seen_pool = seen_progress = seen_info = seen_loss = False
    first_live_shot = False
    idle_after_run_end = 0
    while time.time() - t0 < budget_s:
        snap = cand_snapshot(page)
        key = json.dumps({k: snap[k] for k in ("badge", "phase", "pool", "prog_display", "prog_label")})
        if key != last:
            last = key
            srv = api_state_slice()
            log(f"  t+{int(time.time() - t0):>3}s UI {key}")
            log(f"        info='{snap['info']}'")
            log(f"        loss traces={json.dumps(snap['loss_traces'])[:200]} ann={snap['loss_ann']} wh={snap['loss_wh']}")
            log(f"        SRV {json.dumps(srv)}")
        if snap["badge"] and snap["badge"] not in ("Inactive", ""):
            seen_live_badge = True
        try:
            if int(snap["pool"] or "0") > 0:
                seen_pool = True
        except ValueError:
            # The pool tile can transiently hold non-numeric text mid-render;
            # skip the sample rather than abort the timeline.
            pass
        if snap["prog_display"] == "block" and "/" in (snap["prog_label"] or ""):
            seen_progress = True
        if snap["info"] and "No active candidate pool" not in snap["info"]:
            seen_info = True
        if any((t.get("name") == "Candidate Training" and t.get("nx", 0) > 0) for t in (snap["loss_traces"] or [])):
            seen_loss = True
        if seen_live_badge and not first_live_shot:
            first_live_shot = True
            shot(page, "F027-REDRIVE__candidates_live.png")
        if all((seen_live_badge, seen_pool, seen_progress, seen_info, seen_loss)):
            log(f"  ALL live observables captured at t+{int(time.time() - t0)}s")
            break
        # Early exit once the run has ENDED: no further candidate phase will occur,
        # so waiting out the budget observes nothing (run 1 lost ~8 min to this).
        if int(time.time() - t0) % 15 == 0:
            try:
                if not http_get("/api/status", timeout=30)[1].get("is_running"):
                    idle_after_run_end += 1
                    if idle_after_run_end >= 2:
                        log(f"  run ENDED (is_running=false twice) -- exiting at t+{int(time.time() - t0)}s")
                        break
            except Exception:  # noqa: BLE001, S110
                # Transient /api/status probe failure (F-CANOPY-004 congestion can
                # exceed the timeout); benign -- the sampler retries next tick.
                pass
        page.wait_for_timeout(700)
    series = page.evaluate(
        """(sid) => { if (!window.__rd) return null;
             const s = window.__rd.series[sid] || [];
             const live = s.filter(e => (e.v||'').includes('Training') || (e.v||'').includes('candidate'));
             return {dispatches: window.__rd.n, fills: s.length, live_fills: live.length,
                     first: s.length ? s[0] : null, last: s.length ? s[s.length-1] : null,
                     live_sample: live.length ? live[0] : null}; }""",
        f"{CID}-training-state-store",
    )
    log(f"  STORE series: {json.dumps(series)[:500]}")
    log(
        "  RESULT candidates: badge_live=%s pool>0=%s progress=%s pool_info=%s loss_trace=%s"
        % (seen_live_badge, seen_pool, seen_progress, seen_info, seen_loss)
    )
    shot(page, "F027-REDRIVE__candidates_final.png")


LIVECARDS_OBSERVER = """
(cid) => {
  window.__lc = {t0: Date.now(), samples: [], gaps: [], click: null, done: false, err: null};
  const S = window.__lc;
  let lastRun = Date.now();
  const sample = () => {
    try {
      const now = Date.now();
      const gap = now - lastRun;
      lastRun = now;
      if (gap > 2000 && S.gaps.length < 200) S.gaps.push({t: now - S.t0, gap: gap});
      const b = document.getElementById(cid + '-status-badge');
      const cards = document.querySelectorAll('[id*="history-pool-header"]');
      const badge = b ? (b.innerText||'').trim() : null;
      const n = cards.length;
      const last = S.samples[S.samples.length-1];
      if (!last || last.badge !== badge || last.cards !== n) {
        S.samples.push({t: Date.now()-S.t0, badge: badge, cards: n});
        if (S.samples.length > 500) S.samples.shift();
      }
      if (n > 0 && !S.click) {
        const h = cards[0];
        const card = h.closest('.card');
        const col = card ? card.querySelector('.collapse') : null;
        const colState = () => col ? {cls: col.className, h: Math.round(col.getBoundingClientRect().height)} : null;
        const sec = document.getElementById(cid + '-history-section');
        S.click = {t: Date.now()-S.t0, header_id: h.id,
                   header_text: (h.innerText||'').trim().slice(0,140),
                   section_text: sec ? (sec.innerText||'').trim().slice(0,200) : null,
                   before: colState()};
        h.click();
        setTimeout(() => { S.click.after5s = colState(); }, 5000);
        setTimeout(() => { S.click.after15s = colState(); S.done = true; }, 15000);
      }
    } catch (e) { S.err = String(e).slice(0,200); }
  };
  window.__lcTimer = setInterval(sample, 500);
  sample();
  return true;
}
"""


def step_livecards(page, capture, budget_s: int = 360):
    """M-CANDIDATES-09 (populated history) / -10/-11 (header click is DEAD-EXPECTED).

    Instrument note: once a training run is live, this dashboard's renderer main
    thread saturates and CDP ``evaluate`` starves for MINUTES (three sessions in
    a row stalled: 3 s cadence, 700 ms cadence, and a single 1 Hz tick alike).
    So do everything IN the page: install a self-contained observer while the
    page is calm, then click start, watch the run purely server-side, and
    harvest the observer's buffer with a single patient evaluate at the end.
    The pool-history store is per-session (memory storage), so the observer's
    session must be the one that catches a candidate-phase store fill.
    """
    log("STEP livecards -- M-CANDIDATES-09/-10/-11 (in-page observer, single harvest)")
    open_tab(page, CAND_TAB)
    page.evaluate(LIVECARDS_OBSERVER, CID)
    log("  in-page observer installed (500 ms sampler + self-driving click test)")
    # Start the run only AFTER the observer is in place, then never touch the
    # page again until harvest -- every probe below is server-side HTTP.
    page.evaluate("""() => { const b = document.getElementById('start-button'); if (b) b.click(); }""")
    t0 = time.time()
    started = False
    ended_at = None
    while time.time() - t0 < budget_s:
        page.wait_for_timeout(5000)  # driver-side timer: keeps CDP event dispatch alive, never touches the renderer
        try:
            st = http_get("/api/status", timeout=30)[1]
        except Exception as exc:  # noqa: BLE001
            log(f"  /api/status probe failed at t+{int(time.time() - t0)}s: {str(exc)[:80]}")
            continue
        if st.get("is_running") and not started:
            started = True
            log(f"  run live at t+{int(time.time() - t0)}s (phase={st.get('phase')})")
        if started and not st.get("is_running"):
            ended_at = time.time()
            log(f"  run ENDED at t+{int(time.time() - t0)}s (epoch={st.get('current_epoch')}, units={st.get('hidden_units')})")
            break
    if ended_at:
        page.wait_for_timeout(25000)  # let late store fills and the observer's timed re-reads land
    log("  harvesting observer buffer (this evaluate may take a while to be served)...")
    t_h = time.time()
    lc = page.evaluate("""() => { if (window.__lcTimer) clearInterval(window.__lcTimer); return window.__lc || null; }""")
    log(f"  harvest served after {int(time.time() - t_h)}s")
    if not lc:
        log("  !! observer buffer missing -- nothing recorded")
        return
    log(f"  observer err: {lc.get('err')}")
    gaps = lc.get("gaps") or []
    if gaps:
        worst = sorted(gaps, key=lambda g: -g["gap"])[:5]
        log(f"  timer starvation: {len(gaps)} sampler gaps >2s; worst: {json.dumps(worst)}")
    for s in (lc.get("samples") or [])[:60]:
        log(f"  LC t+{s['t']/1000:7.1f}s badge={s['badge']!r} cards={s['cards']}")
    click = lc.get("click")
    if not click:
        log("  !! no history card ever appeared in this session -- M-CANDIDATES-09/-10/-11 unreachable this run")
        log(f"  SRV {json.dumps(api_state_slice())}")
        return
    log(f"  M-CANDIDATES-09 section at click time: {json.dumps(click.get('section_text'))[:260]}")
    log(f"  M-CANDIDATES-10 header: id={click.get('header_id')!r} text={click.get('header_text')!r}")
    log(f"  M-CANDIDATES-10 collapse before: {json.dumps(click.get('before'))}  +5s: {json.dumps(click.get('after5s'))}  +15s: {json.dumps(click.get('after15s'))}  done={lc.get('done')}")
    triggered = [c for c in capture if "_dash-update-component" in (c.get("url") or "") and "history-pool-header" in (c.get("body") or "")]
    log(f"  M-CANDIDATES-10 dash POSTs referencing the header pattern across the WHOLE session: {len(triggered)}")
    shot(page, "F027-REDRIVE__history_cards.png")


# Verbatim from e2e_f027_setprops_probe.py -- find the Store's fiber, call its
# Dash-supplied setProps (the same entry point a component uses to push a value).
CARDS_SETPROPS = """
(cfg) => {
  const {id, value} = cfg;
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')
          || k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  const root = document.querySelector('#react-entry-point') || document.body;
  let f = fiberOf(root);
  const seen = new Set();
  const stack = [f];
  let hops = 0;
  while (stack.length && hops < 200000) {
    const n = stack.pop();
    hops++;
    if (!n || seen.has(n)) continue;
    seen.add(n);
    const mp = n.memoizedProps;
    if (mp && mp.id === id) {
      if (typeof mp.setProps === 'function') {
        try { mp.setProps({data: value}); return {ok: true, via: 'memoizedProps.setProps', hops}; }
        catch (e) { return {ok: false, err: String(e).slice(0,140), hops}; }
      }
      if (n.stateNode && n.stateNode.props && typeof n.stateNode.props.setProps === 'function') {
        try { n.stateNode.props.setProps({data: value}); return {ok: true, via: 'stateNode.props.setProps', hops}; }
        catch (e) { return {ok: false, err: String(e).slice(0,140), hops}; }
      }
    }
    if (n.child) stack.push(n.child);
    if (n.sibling) stack.push(n.sibling);
  }
  return {ok: false, err: 'component/setProps not found', hops};
}
"""


def step_cardsprobe(page, capture):
    """Constructive fallback for M-CANDIDATES-09/-10/-11 when no live mid-phase
    store fill lands (short runs + mid-run timer starvation can miss them all):
    push ONE realistic Training-state payload through the store's own setProps on
    the CALM post-run page. The REAL update_pool_history server callback appends,
    the REAL render_pool_history renders the card, and the -10/-11 click test then
    runs against a real card. Piecewise coverage: run 2 separately proved a real
    polled fill rendering live values; this supplies the append+render+click legs.
    """
    log("STEP cardsprobe -- constructive fallback for M-CANDIDATES-09/-10/-11")
    open_tab(page, CAND_TAB)
    payload = {
        # shaped exactly like the live /api/state mid-candidate dump (2026-08-24)
        "status": "Started",
        "phase": "candidate",
        "current_epoch": 7,
        "candidate_pool_status": "Training",
        "candidate_pool_phase": "Training",
        "candidate_pool_size": 40,
        "top_candidate_id": "22",
        "top_candidate_score": 0.2773,
        "second_candidate_id": "10",
        "second_candidate_score": 0.2645,
        "pool_metrics": {},
        "candidate_epoch": 201,
        "candidate_total_epochs": 400,
    }
    before = cand_snapshot(page)
    log(f"  siblings BEFORE: badge={before['badge']!r} phase={before['phase']!r} pool={before['pool']!r} info={before['info']!r}")
    res = page.evaluate(CARDS_SETPROPS, {"id": f"{CID}-training-state-store", "value": payload})
    log(f"  setProps: {json.dumps(res)}")
    if not res.get("ok"):
        return
    cards = 0
    for i in range(30):
        page.wait_for_timeout(2000)
        cards = page.evaluate("""() => document.querySelectorAll('[id*="history-pool-header"]').length""")
        if cards:
            break
        if i == 5:
            mid = cand_snapshot(page)
            log(f"  siblings +12s: badge={mid['badge']!r} phase={mid['phase']!r} pool={mid['pool']!r} info={mid['info']!r}")
            log(f"  (badge flipped={mid['badge'] != before['badge']} -- did the write propagate to ANY consumer?)")
    log(f"  cards after constructive fill: {cards}")
    hist_posts = [c for c in capture if "_dash-update-component" in (c.get("url") or "") and "pool-history-store" in (c.get("body") or "")]
    log(f"  update_pool_history POSTs captured: {len(hist_posts)}")
    for p in hist_posts[-6:]:
        body = p.get("body") or ""
        status = "Training" if '"candidate_pool_status": "Training"' in body or '"candidate_pool_status":"Training"' in body else ("Inactive" if "Inactive" in body else "?")
        log(f"    t={p['t_ms']}ms executed with candidate_pool_status={status} body[:180]={body[:180]!r}")
    if not cards:
        log("  !! no card rendered from the constructive fill either -- update_pool_history/append/render leg broken")
        return
    section = vis(page, f"{CID}-history-section")
    log(f"  M-CANDIDATES-09 history-section: {json.dumps(section)[:300]}")
    card = page.evaluate(
        """() => { const h = document.querySelector('[id*="history-pool-header"]');
             const c = h.closest('.card');
             const col = c ? c.querySelector('.collapse') : null;
             return {header_id: h.id, header_text: (h.innerText||'').trim().slice(0,140),
                     collapse_cls: col ? col.className : null,
                     collapse_h: col ? Math.round(col.getBoundingClientRect().height) : null}; }"""
    )
    log(f"  first card before click: {json.dumps(card)}")
    shot(page, "F027-REDRIVE__history_cards.png")
    n_before = len(capture)
    page.evaluate("""() => { const h = document.querySelector('[id*="history-pool-header"]'); if (h) h.click(); }""")
    page.wait_for_timeout(5000)
    mid = page.evaluate(
        """() => { const h = document.querySelector('[id*="history-pool-header"]');
             const c = h ? h.closest('.card') : null;
             const col = c ? c.querySelector('.collapse') : null;
             return {collapse_cls: col ? col.className : null, collapse_h: col ? Math.round(col.getBoundingClientRect().height) : null}; }"""
    )
    page.wait_for_timeout(10000)
    after = page.evaluate(
        """() => { const h = document.querySelector('[id*="history-pool-header"]');
             const c = h ? h.closest('.card') : null;
             const col = c ? c.querySelector('.collapse') : null;
             return {collapse_cls: col ? col.className : null, collapse_h: col ? Math.round(col.getBoundingClientRect().height) : null}; }"""
    )
    triggered = [c for c in capture[n_before:] if "_dash-update-component" in (c.get("url") or "") and "history-pool-header" in (c.get("body") or "")]
    ambient = sum(1 for c in capture[n_before:] if "_dash-update-component" in (c.get("url") or ""))
    log(f"  M-CANDIDATES-10 collapse before: {json.dumps(card.get('collapse_cls'))}/{card.get('collapse_h')}  +5s: {json.dumps(mid)}  +15s: {json.dumps(after)}")
    log(f"  M-CANDIDATES-10 dash POSTs referencing the header pattern: {len(triggered)} (ambient dash POSTs in window: {ambient})")


def _slider_value(page) -> int | None:
    return page.evaluate(
        """() => { const s = document.querySelector('#decision-boundary-resolution-slider [role=slider]');
             return s ? Number(s.getAttribute('aria-valuenow')) : null; }"""
    )


def _mesh_nx(page) -> int:
    fig = fig_info(page, f"{DID}-plot")
    best = 0
    for t in fig.get("traces") or []:
        if t.get("type") in ("contour", "heatmap") and t.get("nx", 0) > best:
            best = t["nx"]
    return best


def step_boundaries(page, capture, budget_s: int = 300):
    """M-BOUNDARIES-04 (status), -01 (slider), -02 (confidence), -03 (refresh)."""
    log("STEP boundaries -- M-BOUNDARIES-04/-01/-02/-03")
    open_tab(page, BOUND_TAB)
    if not page.evaluate(FIND_STORE):
        log("  !! redux store not reachable -- cadence attribution unavailable")
    else:
        page.evaluate(SUBSCRIBE, [f"{DID}-boundary-data"])
        log("  subscribed to decision-boundary-boundary-data")

    # M-BOUNDARIES-04: status transition off the mount default.
    t0 = time.time()
    status = fig = None
    while time.time() - t0 < budget_s:
        status = vis(page, f"{DID}-status")
        fig = fig_info(page, f"{DID}-plot")
        if status.get("text") and status["text"] != "Status: No network loaded" and (fig.get("traces") or []):
            log(f"  M-BOUNDARIES-04 status transitioned at t+{int(time.time() - t0)}s: '{status['text']}'")
            break
        page.wait_for_timeout(3000)
    log(f"  status: {json.dumps(status)[:200]}")
    log(f"  fig: traces={json.dumps((fig or {}).get('traces'))[:300]} wh=({(fig or {}).get('w')},{(fig or {}).get('h')}) modebar={(fig or {}).get('modebar')}")
    log(f"  SRV {json.dumps(api_state_slice())}")
    shot(page, "F027-REDRIVE__boundaries_live.png")

    # Short settle; the -03 ambient cadence is derived later from the subscribe
    # series' inter-fill gaps (the subscribe has been recording since step entry).
    page.wait_for_timeout(10000)
    series = page.evaluate("""() => window.__rd ? {n: window.__rd.n, fills: window.__rd.series['decision-boundary-boundary-data'].length, t: Date.now() - window.__rd.t0} : null""")
    log(f"  series after settle: {json.dumps(series)}")

    # M-BOUNDARIES-01: slider ArrowRight -> +25, immediate re-render, mesh at new resolution.
    v0 = _slider_value(page)
    nx0 = _mesh_nx(page)
    sig0 = fig_info(page, f"{DID}-plot").get("sig")
    log(f"  M-BOUNDARIES-01 slider before: value={v0} mesh_nx={nx0} sig={sig0}")
    page.evaluate("""() => { const s = document.querySelector('#decision-boundary-resolution-slider [role=slider]'); if (s) s.focus(); }""")
    page.keyboard.press("ArrowRight")
    v1 = None
    for _ in range(15):
        page.wait_for_timeout(1000)
        v1 = _slider_value(page)
        if v1 is not None and v0 is not None and v1 != v0:
            break
    log(f"  M-BOUNDARIES-01 slider after ArrowRight: value={v1}")
    rerender = None
    for _ in range(20):
        page.wait_for_timeout(1500)
        f = fig_info(page, f"{DID}-plot")
        if f.get("sig") != sig0:
            rerender = f
            break
    log(f"  M-BOUNDARIES-01 re-render: sig {sig0} -> {(rerender or {}).get('sig')} (changed={bool(rerender)})")
    nx1 = 0
    for _ in range(30):
        page.wait_for_timeout(2000)
        nx1 = _mesh_nx(page)
        if v1 and nx1 == v1:
            break
    log(f"  M-BOUNDARIES-01 mesh at new resolution: nx {nx0} -> {nx1} (target {v1})")
    shot(page, "F027-REDRIVE__boundaries_slider.png")

    # M-BOUNDARIES-02: confidence toggle -> figure changes, then restore.
    cb = page.evaluate(
        """() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]');
             return i ? {present: true, checked: i.checked} : {present: false}; }"""
    )
    sig_b = fig_info(page, f"{DID}-plot").get("sig")
    traces_b = fig_info(page, f"{DID}-plot").get("traces")
    log(f"  M-BOUNDARIES-02 before: cb={json.dumps(cb)} sig={sig_b} traces={json.dumps(traces_b)[:240]}")
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    changed = None
    for _ in range(20):
        page.wait_for_timeout(1500)
        f = fig_info(page, f"{DID}-plot")
        if f.get("sig") != sig_b:
            changed = f
            break
    cb2 = page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); return i ? i.checked : null; }""")
    log(f"  M-BOUNDARIES-02 after: checked={cb2} sig={(changed or {}).get('sig')} changed={bool(changed)} traces={json.dumps((changed or {}).get('traces'))[:240]}")
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    page.wait_for_timeout(4000)
    shot(page, "F027-REDRIVE__boundaries_confidence.png")

    # M-BOUNDARIES-03: refresh click -- attribute by fill timing vs ambient cadence.
    pre = page.evaluate("""() => window.__rd ? {n: window.__rd.n, fills: window.__rd.series['decision-boundary-boundary-data'].length, t: Date.now() - window.__rd.t0} : null""")
    sig_r = fig_info(page, f"{DID}-plot").get("sig")
    page.evaluate("""() => { const b = document.getElementById('decision-boundary-refresh-btn'); if (b) b.click(); }""")
    t_click = time.time()
    first_fill_ms = None
    for _ in range(30):
        page.wait_for_timeout(1000)
        cur = page.evaluate("""() => window.__rd ? {fills: window.__rd.series['decision-boundary-boundary-data'].length, t: Date.now() - window.__rd.t0} : null""")
        if cur and pre and cur["fills"] > pre["fills"]:
            first_fill_ms = int((time.time() - t_click) * 1000)
            break
    sig_r2 = fig_info(page, f"{DID}-plot").get("sig")
    log(f"  M-BOUNDARIES-03 refresh: pre={json.dumps(pre)} first store fill after click: {first_fill_ms} ms; fig sig {sig_r} -> {sig_r2}")
    tail = page.evaluate("""() => window.__rd ? window.__rd.series['decision-boundary-boundary-data'].slice(-6).map(e => e.t) : null""")
    log(f"  M-BOUNDARIES-03 fill timeline tail (ms since subscribe): {json.dumps(tail)}")


def step_bprobe(page, capture):
    """Request-side discriminator for M-BOUNDARIES-01/-02/-03: which of the
    boundary callbacks actually FIRE (feeder vs render), at what cadence, and
    do refresh / confidence-toggle trigger them? Reads only the request capture
    (POST bodies name their output), so identical-data rewrites are visible --
    the subscribe-series instrument records value CHANGES and is blind to them.
    """
    log("STEP bprobe -- request-side census of boundary callbacks")
    open_tab(page, BOUND_TAB)
    sig0 = fig_info(page, f"{DID}-plot").get("sig")
    n0 = len(capture)
    log(f"  settled; fig sig={sig0}; ambient window 40s...")
    page.wait_for_timeout(40000)
    n1 = len(capture)
    page.evaluate("""() => { const b=document.getElementById('decision-boundary-refresh-btn'); if(b) b.click(); }""")
    log("  refresh clicked; 30s window...")
    page.wait_for_timeout(30000)
    n2 = len(capture)
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    log("  confidence toggled; 30s window...")
    page.wait_for_timeout(30000)
    sig1 = fig_info(page, f"{DID}-plot").get("sig")
    cb = page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); return i ? i.checked : null; }""")

    def census(reqs, label):
        feeder = [c for c in reqs if '"decision-boundary-boundary-data.data"' in (c.get("body") or "") or "decision-boundary-boundary-data.data" in (c.get("body") or "")[:400]]
        dsfeed = [c for c in reqs if "decision-boundary-dataset-data.data" in (c.get("body") or "")[:400]]
        plotcb = [c for c in reqs if "decision-boundary-plot.figure" in (c.get("body") or "")[:600]]
        log(f"  {label}: {len(reqs)} dash POSTs | feeder(boundary-data)={len(feeder)} @ {[c['t_ms'] for c in feeder][:8]}")
        log(f"    dataset-feeder={len(dsfeed)} @ {[c['t_ms'] for c in dsfeed][:8]} | plot-render={len(plotcb)} @ {[c['t_ms'] for c in plotcb][:8]}")
        return feeder, plotcb

    log(f"  windows: ambient {n1 - n0} reqs, post-refresh {n2 - n1} reqs, post-toggle {len(capture) - n2} reqs")
    census([c for c in capture[n0:n1] if "_dash-update-component" in (c.get("url") or "")], "ambient   [0..40s]")
    census([c for c in capture[n1:n2] if "_dash-update-component" in (c.get("url") or "")], "post-refresh[40..70s]")
    census([c for c in capture[n2:] if "_dash-update-component" in (c.get("url") or "")], "post-toggle[70..100s]")
    census([c for c in capture if "_dash-update-component" in (c.get("url") or "")], "FULL session")
    log(f"  fig sig {sig0} -> {sig1} (changed={sig0 != sig1}); checkbox now={cb}")
    # restore the checkbox to its shipped state
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    page.wait_for_timeout(3000)


def step_dstats(page, capture):
    """M-DATASET-13/-15/-16 with a starvation-fair window: 100 s on the dataset
    tab (settle times ran 3-39 s under congestion; a 15 s read is not evidence),
    then tiles + plots + a request census of the dataset-store feeder."""
    log("STEP dstats -- M-DATASET-13/-15/-16, 100 s window + feeder census")
    open_tab(page, "Dataset View")
    for wait_s in (20, 40, 100):
        page.wait_for_timeout((wait_s - (0 if wait_s == 20 else (20 if wait_s == 40 else 40))) * 1000)
        tiles = {t: vis(page, f"dataset-plotter-{t}").get("text") for t in ("sample-count", "feature-count", "class-count", "balance-info")}
        log(f"  t+{wait_s}s tiles: {json.dumps(tiles)}")
    scat = fig_info(page, "dataset-plotter-scatter-plot")
    dist = fig_info(page, "dataset-plotter-distribution-plot")
    log(f"  scatter: {json.dumps({k: scat.get(k) for k in ('w', 'h', 'traces', 'annotations', 'text')})[:280]}")
    log(f"  distribution: {json.dumps({k: dist.get(k) for k in ('w', 'h', 'traces', 'annotations', 'text')})[:280]}")
    feeder = [c for c in capture if "_dash-update-component" in (c.get("url") or "") and "dataset-plotter-dataset-store.data" in (c.get("body") or "")[:400]]
    tilecb = [c for c in capture if "_dash-update-component" in (c.get("url") or "") and "dataset-plotter-sample-count" in (c.get("body") or "")[:800]]
    log(f"  dataset-store feeder POSTs: {len(feeder)} @ {[c['t_ms'] for c in feeder][:10]}")
    log(f"  tile-render POSTs: {len(tilecb)} @ {[c['t_ms'] for c in tilecb][:10]}")
    log(f"  server truth: /api/dataset loaded={http_get('/api/dataset', timeout=60)[1].get('loaded')}")
    shot(page, "F027-REDRIVE__dataset_dstats.png")


def step_bfinal(page, capture):
    """M-BOUNDARIES-01/-02/-03 interactions, SUBSCRIBE-FREE (post-Stage-2 form).

    The subscribe instrument stringifies the ~166 KB mesh on every Redux
    dispatch (~90/s) and that alone can stall the page (two sessions wedged in
    ``step_boundaries``'s settle right after it subscribed, while the
    request-capture-only ``bprobe`` ran clean post-run twice). Everything the
    three rows need is available without touching the store:
    - re-renders: the plot's own fig sig (short evaluates on a calm page);
    - the resolution refetch: the feeder POST body CARRIES the slider value;
    - refresh attribution: at the 5 s Stage-2 cadence, a fetch initiated
      off-cadence right after the click is attributable from timestamps alone.
    """
    log("STEP bfinal -- M-BOUNDARIES-01/-02/-03, request-capture only")
    open_tab(page, BOUND_TAB)
    page.wait_for_timeout(8000)
    status = vis(page, f"{DID}-status")
    sig0 = fig_info(page, f"{DID}-plot").get("sig")
    log(f"  status: {status.get('text')!r}  sig={sig0}")

    def feeder_posts(since):
        return [c for c in capture[since:] if "_dash-update-component" in (c.get("url") or "") and "decision-boundary-boundary-data.data" in (c.get("body") or "")[:400]]

    # M-BOUNDARIES-01: slider ArrowRight -> value commit, resolution in the next
    # feeder POST body, and a re-render (sig change: a 125-mesh differs from a 100-mesh).
    v0 = _slider_value(page)
    n0 = len(capture)
    page.evaluate("""() => { const s = document.querySelector('#decision-boundary-resolution-slider [role=slider]'); if (s) s.focus(); }""")
    page.keyboard.press("ArrowRight")
    v1 = None
    for _ in range(10):
        page.wait_for_timeout(1000)
        v1 = _slider_value(page)
        if v1 is not None and v1 != v0:
            break
    log(f"  M-BOUNDARIES-01 slider: {v0} -> {v1}")
    sig1 = None
    for _ in range(20):
        page.wait_for_timeout(1500)
        sig1 = fig_info(page, f"{DID}-plot").get("sig")
        if sig1 != sig0:
            break
    res_posts = [(c["t_ms"], ("resolution" in (c.get("body") or "")) and (str(v1) in (c.get("body") or ""))) for c in feeder_posts(n0)]
    log(f"  M-BOUNDARIES-01 re-render: sig {sig0} -> {sig1} (changed={sig1 != sig0})")
    log(f"  M-BOUNDARIES-01 feeder POSTs since slider move (t_ms, carries-{v1}): {res_posts[:6]}")
    shot(page, "F027-REDRIVE__bfinal_slider.png")

    # M-BOUNDARIES-02: confidence toggle -> re-render with shading flipped, then restore.
    sig_b = fig_info(page, f"{DID}-plot").get("sig")
    cb0 = page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); return i ? i.checked : None; }""".replace("None", "null"))
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    sig_c = None
    for _ in range(14):
        page.wait_for_timeout(1500)
        sig_c = fig_info(page, f"{DID}-plot").get("sig")
        if sig_c != sig_b:
            break
    cb1 = page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); return i ? i.checked : null; }""")
    log(f"  M-BOUNDARIES-02 checkbox {cb0} -> {cb1}; sig {sig_b} -> {sig_c} (changed={sig_c != sig_b})")
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    page.wait_for_timeout(4000)
    shot(page, "F027-REDRIVE__bfinal_confidence.png")

    # M-BOUNDARIES-03: refresh -> an off-cadence feeder POST within ~3 s of the
    # click (ambient cadence is 5 s), plus the render that follows it.
    n1 = len(capture)
    amb = [c["t_ms"] for c in feeder_posts(0)][-4:]
    sig_r0 = fig_info(page, f"{DID}-plot").get("sig")
    page.evaluate("""() => { const b = document.getElementById('decision-boundary-refresh-btn'); if (b) b.click(); }""")
    page.wait_for_timeout(6000)
    fresh = [c["t_ms"] for c in feeder_posts(n1)]
    page.wait_for_timeout(8000)
    sig_r1 = fig_info(page, f"{DID}-plot").get("sig")
    log(f"  M-BOUNDARIES-03 ambient feeder cadence tail: {amb}")
    log(f"  M-BOUNDARIES-03 feeder POSTs within 6s of refresh click: {fresh} (click at capture-clock ~{fresh[0] if fresh else 'n/a'})")
    log(f"  M-BOUNDARIES-03 sig {sig_r0} -> {sig_r1} (changed={sig_r0 != sig_r1})")


def step_bfinal2(page, capture):
    """M-BOUNDARIES-02/-03 only, with SPARSE evaluates (≥6 s apart, six total).

    Empirical driving law, refined across seven sessions: rapid-fire evaluate
    sequences (1-1.5 s fig polls) eventually hit one the renderer never serves,
    regardless of subscribe or run state, while sparse evaluates (bprobe's,
    spaced 30-40 s) always serve. So: one read per phase, patient spacing,
    request-capture for everything countable.
    """
    log("STEP bfinal2 -- M-BOUNDARIES-02/-03, sparse evaluates")
    open_tab(page, BOUND_TAB)
    page.wait_for_timeout(10000)

    def feeder_posts(since):
        return [c["t_ms"] for c in capture[since:] if "_dash-update-component" in (c.get("url") or "") and "decision-boundary-boundary-data.data" in (c.get("body") or "")[:400]]

    # M-BOUNDARIES-02
    st = page.evaluate(
        """(id) => { const root = document.getElementById(id);
             const gd = root && (root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot'));
             const cb = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]');
             let sig = -1; try { sig = gd && gd.data ? JSON.stringify(gd.data).length : 0; } catch (e) {}
             return {sig: sig, checked: cb ? cb.checked : null}; }""",
        f"{DID}-plot",
    )
    log(f"  M-BOUNDARIES-02 before: {json.dumps(st)}")
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    page.wait_for_timeout(12000)
    st2 = page.evaluate(
        """(id) => { const root = document.getElementById(id);
             const gd = root && (root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot'));
             const cb = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]');
             let sig = -1; try { sig = gd && gd.data ? JSON.stringify(gd.data).length : 0; } catch (e) {}
             return {sig: sig, checked: cb ? cb.checked : null}; }""",
        f"{DID}-plot",
    )
    log(f"  M-BOUNDARIES-02 after toggle+12s: {json.dumps(st2)} (sig changed={st2['sig'] != st['sig']}, checkbox flipped={st2['checked'] != st['checked']})")
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    page.wait_for_timeout(8000)

    # M-BOUNDARIES-03
    amb = feeder_posts(0)
    n1 = len(capture)
    page.evaluate("""() => { const b = document.getElementById('decision-boundary-refresh-btn'); if (b) b.click(); }""")
    page.wait_for_timeout(7000)
    fresh = feeder_posts(n1)
    page.wait_for_timeout(8000)
    st3 = page.evaluate(
        """(id) => { const root = document.getElementById(id);
             const gd = root && (root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot'));
             let sig = -1; try { sig = gd && gd.data ? JSON.stringify(gd.data).length : 0; } catch (e) {}
             return {sig: sig}; }""",
        f"{DID}-plot",
    )
    log(f"  M-BOUNDARIES-03 ambient feeder t_ms tail: {amb[-5:]}")
    log(f"  M-BOUNDARIES-03 feeder POSTs within 7s of refresh click: {fresh}")
    log(f"  M-BOUNDARIES-03 fig sig after: {st3['sig']} (vs before-toggle {st['sig']})")


BOBSERVER = """
() => {
  window.__bo = {t0: Date.now(), steps: [], done: false, err: null};
  const S = window.__bo;
  const sig = () => {
    try {
      const root = document.getElementById('decision-boundary-plot');
      const gd = root && (root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot'));
      return gd && gd.data ? JSON.stringify(gd.data).length : 0;
    } catch (e) { return -1; }
  };
  const cb = () => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); return i ? i.checked : null; };
  const rec = (label) => S.steps.push({t: Date.now() - S.t0, label: label, sig: sig(), checked: cb()});
  try {
    rec('before');
    const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]');
    if (i) i.click();
    rec('toggled');
    setTimeout(() => {
      rec('after-toggle-12s');
      if (i) i.click();
      setTimeout(() => {
        rec('restored-8s');
        const b = document.getElementById('decision-boundary-refresh-btn');
        S.refreshClickAt = Date.now() - S.t0;
        if (b) b.click();
        setTimeout(() => { rec('after-refresh-14s'); S.done = true; }, 14000);
      }, 8000);
    }, 12000);
  } catch (e) { S.err = String(e).slice(0, 200); }
  return true;
}
"""


def step_bfinal3(page, capture):
    """M-BOUNDARIES-02/-03 via a fully self-driving in-page script + ONE harvest.

    The only observation architecture that has never wedged on this dashboard
    (run-4/5 livecards): install everything at attach time (attach-window
    evaluates always serve), let in-page timeouts do the driving and the
    reading, harvest once at the end. The feeder timing for -03 comes from the
    python-side request capture, which needs no page cooperation at all.
    """
    log("STEP bfinal3 -- M-BOUNDARIES-02/-03, in-page self-driver + single harvest")
    open_tab(page, BOUND_TAB)
    page.wait_for_timeout(9000)
    n0 = len(capture)
    page.evaluate(BOBSERVER)
    log("  in-page self-driver installed (toggle -> restore -> refresh, self-recorded)")
    time_budget = 60
    t0 = time.time()
    while time.time() - t0 < time_budget:
        page.wait_for_timeout(5000)  # driver-side timer; no renderer contact
    bo = page.evaluate("""() => window.__bo || null""")
    if not bo:
        log("  !! self-driver buffer missing")
        return
    log(f"  err={bo.get('err')} done={bo.get('done')} refreshClickAt={bo.get('refreshClickAt')}ms")
    for s in bo.get("steps") or []:
        log(f"  BO t+{s['t'] / 1000:6.1f}s {s['label']:<18s} sig={s['sig']} checked={s['checked']}")
    feeder = [c["t_ms"] for c in capture[n0:] if "_dash-update-component" in (c.get("url") or "") and "decision-boundary-boundary-data.data" in (c.get("body") or "")[:400]]
    log(f"  feeder POSTs (t_ms since session start): {feeder}")


def step_bcausal(page, capture):
    """M-BOUNDARIES-02/-03 causal attribution from ``changedPropIds`` alone.

    Every ``_dash-update-component`` POST body names the props that triggered
    it. So: click the confidence toggle, click refresh — three attach-window
    evaluates total (the only class with a 100% service record on the
    boundaries tab) — then prove causation ENTIRELY python-side:
    - a plot-render POST whose changedPropIds contains ``show-confidence``
      == the toggle fired the render (M-BOUNDARIES-02's observable);
    - a feeder POST whose changedPropIds contains ``refresh-btn``
      == the button forced the refetch (M-BOUNDARIES-03's observable).
    No polling, no subscribe, no late evaluates: the page can wedge freely
    after the clicks and the capture still answers.
    """
    log("STEP bcausal -- changedPropIds attribution for M-BOUNDARIES-02/-03")
    open_tab(page, BOUND_TAB)
    page.wait_for_timeout(8000)
    page.evaluate("""() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""")
    log("  confidence checkbox clicked")
    t0 = time.time()
    while time.time() - t0 < 14:
        page.wait_for_timeout(2000)
    page.evaluate("""() => { const b = document.getElementById('decision-boundary-refresh-btn'); if (b) b.click(); }""")
    log("  refresh clicked")
    t0 = time.time()
    while time.time() - t0 < 14:
        page.wait_for_timeout(2000)

    def posts(pred):
        out = []
        for c in capture:
            body = c.get("body") or ""
            if "_dash-update-component" in (c.get("url") or "") and pred(body):
                out.append(c["t_ms"])
        return out

    toggle_render = posts(lambda b: "decision-boundary-plot.figure" in b[:600] and "show-confidence" in b)
    toggle_any = posts(lambda b: "show-confidence" in b and "changedPropIds" in b and '"decision-boundary-show-confidence.value"' in b.split("changedPropIds", 1)[-1][:300])
    refresh_feeder = posts(lambda b: "decision-boundary-boundary-data.data" in b[:400] and "refresh-btn" in b)
    refresh_any = posts(lambda b: "changedPropIds" in b and '"decision-boundary-refresh-btn.n_clicks"' in b.split("changedPropIds", 1)[-1][:300])
    ambient_feeder = posts(lambda b: "decision-boundary-boundary-data.data" in b[:400])
    log(f"  M-BOUNDARIES-02 plot-render POSTs carrying show-confidence: {toggle_render}")
    log(f"  M-BOUNDARIES-02 POSTs with show-confidence.value in changedPropIds: {toggle_any}")
    log(f"  M-BOUNDARIES-03 feeder POSTs carrying refresh-btn: {refresh_feeder}")
    log(f"  M-BOUNDARIES-03 POSTs with refresh-btn.n_clicks in changedPropIds: {refresh_any}")
    log(f"  (all boundary-data-writing POSTs this session: {ambient_feeder})")


def _one_gesture_session(page, capture, click_js, label, scans):
    """One gesture per session: the attach-window evaluates (open_tab + one
    click ≤ ~20 s into page life) are the only evaluate class that has never
    starved on the boundaries tab across nine sessions. Everything after the
    click is python-side capture analysis — the page may wedge freely.

    Registers its OWN full-body request handler: the shared capture truncates
    bodies at 4000 chars, and the plot callback's ``changedPropIds`` serializes
    AFTER its inputs — which include the ~166 KB boundary store — so the
    attribution field never survives the shared slice.
    """
    full = []

    def on_request(req):
        if "_dash-update-component" in req.url:
            try:
                body = req.post_data or ""
            except Exception:  # noqa: BLE001
                # post_data can raise on non-text bodies; irrelevant here.
                body = ""
            full.append({"t_ms": int((time.time()) * 1000) % 10_000_000, "body": body})

    page.on("request", on_request)
    open_tab(page, BOUND_TAB)
    page.wait_for_timeout(6000)
    page.evaluate(click_js)
    log(f"  {label} clicked at ~t+20s of page life")
    t0 = time.time()
    while time.time() - t0 < 16:
        page.wait_for_timeout(2000)
    for name, pred in scans:
        hits = [c["t_ms"] for c in full if pred(c.get("body") or "")]
        log(f"  {name}: {hits}")


def step_btoggle(page, capture):
    """M-BOUNDARIES-02 causal capture: does the confidence toggle FIRE the render?"""
    log("STEP btoggle -- one-gesture causal capture for M-BOUNDARIES-02")
    _one_gesture_session(
        page,
        capture,
        """() => { const i = document.querySelector('#decision-boundary-show-confidence input[type=checkbox]'); if (i) i.click(); }""",
        "confidence checkbox",
        [
            ("plot-render POSTs with show-confidence.value in changedPropIds", lambda b: "decision-boundary-plot.figure" in b[:600] and '"decision-boundary-show-confidence.value"' in b),
            ("ALL plot-render POSTs", lambda b: "decision-boundary-plot.figure" in b[:600]),
        ],
    )


def step_brefresh(page, capture):
    """M-BOUNDARIES-03 causal capture: does ↻ Refresh FORCE the feeder refetch?"""
    log("STEP brefresh -- one-gesture causal capture for M-BOUNDARIES-03")
    _one_gesture_session(
        page,
        capture,
        """() => { const b = document.getElementById('decision-boundary-refresh-btn'); if (b) b.click(); }""",
        "refresh button",
        [
            ("feeder POSTs with refresh-btn.n_clicks in changedPropIds", lambda b: "decision-boundary-boundary-data.data" in b[:400] and '"decision-boundary-refresh-btn.n_clicks"' in b),
            ("ALL feeder POSTs", lambda b: "decision-boundary-boundary-data.data" in b[:400]),
        ],
    )


def step_f025(page, capture):
    """F-CANOPY-025 allow-arm, post-Stage-2: does the Live Switch gate OPEN?

    Hypothesis: the gate callback consumes ``training-status-store``, whose old
    dedicated poller rewrote it every fast tick — the same claimed-Input
    promotion race Stage 2 removed (the store is now written by the status-bar
    callback and suppressed on no-change). Preconditions are set via HTTP
    BEFORE attach (experimental flag ON + training started), so at mount both
    gate inputs are live and one attach-window read answers the arm the deny
    trap hid for five segments.
    """
    log("STEP f025 -- Live Switch gate allow-arm (post-Stage-2)")
    code, body = http_post("/api/admin/experimental_functions", {"enabled": True})
    log(f"  experimental_functions ON -> {code} {json.dumps(body)[:120]}")
    code, body = http_post("/api/train/start", {})
    log(f"  train/start -> {code} {json.dumps(body)[:120]}")
    for _ in range(8):
        time.sleep(1)
        if http_get("/api/status", timeout=30)[1].get("is_running"):
            break
    log(f"  /api/status: {json.dumps({k: v for k, v in http_get('/api/status', timeout=30)[1].items() if k in ('is_running', 'phase')})}")
    # RELOAD so the one-shot flag reconciliation runs AFTER the flag was set —
    # the initial attach's reconcile read the pre-POST state, and the flags
    # store only hydrates at mount. The reload also resets the attach window.
    page.reload(wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(12000)
    state = page.evaluate(
        """() => { const b = document.getElementById('live-dataset-switch-button');
             return {disabled: b ? b.disabled : null}; }"""
    )
    log(f"  post-reload early read: {json.dumps(state)}")
    page.wait_for_timeout(2000)
    state = page.evaluate(
        """() => { const b = document.getElementById('live-dataset-switch-button');
             return {present: !!b, disabled: b ? b.disabled : null,
                     text: b ? (b.innerText||'').trim() : null}; }"""
    )
    log(f"  live-dataset-switch-button attach-window read: {json.dumps(state)}")
    # Then 60 s of pure python-side capture watching: the ORIGINAL finding was
    # "zero responses ever carry live-dataset-switch-button across a 120 s
    # watch" — any gate POST now (with is_running:true + flag:true inputs in
    # its body) refutes the never-fires observation.
    t0 = time.time()
    while time.time() - t0 < 60:
        page.wait_for_timeout(3000)
    gate_posts = [c for c in capture if "_dash-update-component" in (c.get("url") or "") and "live-dataset-switch-button.disabled" in (c.get("body") or "")]
    log(f"  gate-callback POSTs (output live-dataset-switch-button.disabled): {[c['t_ms'] for c in gate_posts]}")
    for c in gate_posts[:3]:
        body = c.get("body") or ""
        log(f"    inputs snippet: running={'\"is_running\": true' in body or '\"is_running\":true' in body} flag={'\"experimental_functions\": true' in body or '\"experimental_functions\":true' in body}")
    # Post-window DOM re-read (page may be starved by now; failure is non-fatal evidence-wise).
    try:
        state2 = page.evaluate(
            """() => { const b = document.getElementById('live-dataset-switch-button');
                 return {disabled: b ? b.disabled : null}; }"""
        )
        log(f"  post-window read: {json.dumps(state2)}")
    except Exception as exc:  # noqa: BLE001
        log(f"  post-window read starved (expected under run load): {str(exc)[:80]}")


def step_f002(page, capture):
    """F-CANOPY-002 post-fix: does the WS metrics fast path deliver during a run?

    Pre-fix signature: 401 metrics frames measured on /ws/training dispatching
    ONLY into the latency sampler; ``_juniperWsDrain._metricsBuffer`` stayed 0
    and ``_metricsReceived`` false/stale for whole runs. Post-fix (per-type
    fan-out): the bridge's intake and the beacon COEXIST — the drain fills and
    stamps during the run while the beacon keeps sampling.

    Observables (one attach-window read + python-side capture scans):
    - drain state ~t+15 s into a live run (fresh _lastMetricsFrameMs);
    - M-METRICS-32's server half: append POSTs whose changedPropIds carry
      ``ws-metrics-buffer.data``;
    - beacon coexistence: browser-side ``/api/ws_latency`` POSTs continuing.
    """
    log("STEP f002 -- WS metrics fast path under a live run")
    code, body = http_post("/api/train/start", {})
    log(f"  train/start -> {code} {json.dumps(body)[:80]}")
    for _ in range(8):
        time.sleep(1)
        if http_get("/api/status", timeout=30)[1].get("is_running"):
            break
    page.wait_for_timeout(9000)
    drain = page.evaluate(
        """() => { const d = window._juniperWsDrain || {};
             const now = Date.now();
             return {present: !!window._juniperWsDrain,
                     metricsReceived: d._metricsReceived === undefined ? null : d._metricsReceived,
                     lastMetricsAgeMs: d._lastMetricsFrameMs ? (now - d._lastMetricsFrameMs) : null,
                     lastStateAgeMs: d._lastStateFrameMs ? (now - d._lastStateFrameMs) : null,
                     bufferLen: Array.isArray(d._metricsBuffer) ? d._metricsBuffer.length : null}; }"""
    )
    log(f"  drain at ~t+15s of run: {json.dumps(drain)}")
    t0 = time.time()
    while time.time() - t0 < 45:
        page.wait_for_timeout(3000)
    appends = [c["t_ms"] for c in capture if "_dash-update-component" in (c.get("url") or "") and '"ws-metrics-buffer.data"' in (c.get("body") or "")]
    beacons = [c["t_ms"] for c in capture if "/api/ws_latency" in (c.get("url") or "")]
    log(f"  M-METRICS-32 append POSTs (changedPropIds ws-metrics-buffer.data): n={len(appends)} @ {appends[:8]}")
    log(f"  beacon /api/ws_latency POSTs (coexistence): n={len(beacons)} @ {beacons[:6]}")
    try:
        drain2 = page.evaluate(
            """() => { const d = window._juniperWsDrain || {};
                 const now = Date.now();
                 return {lastMetricsAgeMs: d._lastMetricsFrameMs ? (now - d._lastMetricsFrameMs) : null,
                         bufferLen: Array.isArray(d._metricsBuffer) ? d._metricsBuffer.length : null}; }"""
        )
        log(f"  drain after 45s window: {json.dumps(drain2)}")
    except Exception as exc:  # noqa: BLE001
        log(f"  late drain read starved (non-fatal): {str(exc)[:60]}")


def step_f025idle(page, capture):
    """F-CANOPY-025 mechanism seal: at IDLE, does the gate fire at mount?

    If the gate executes at idle (feeder round-trips ~30 ms → promotion gaps
    everywhere) but never under a run (feeder ~always in flight → its output
    store permanently claimed), the mechanism is the same claimed-Input
    promotion race — via the feeder's in-flight window, which Stage 2's write
    suppression cannot remove.
    """
    log("STEP f025idle -- gate mount/idle census")
    st = http_get("/api/status", timeout=30)[1]
    log(f"  /api/status: {json.dumps({k: st.get(k) for k in ('is_running', 'phase')})}")
    t0 = time.time()
    while time.time() - t0 < 30:
        page.wait_for_timeout(3000)
    gate_posts = [c["t_ms"] for c in capture if "_dash-update-component" in (c.get("url") or "") and "live-dataset-switch-button.disabled" in (c.get("body") or "")]
    log(f"  gate-callback POSTs at idle (30 s incl. mount): {gate_posts}")
    try:
        state = page.evaluate("""() => { const b = document.getElementById('live-dataset-switch-button'); return {disabled: b ? b.disabled : null}; }""")
        log(f"  button state: {json.dumps(state)}")
    except Exception as exc:  # noqa: BLE001
        log(f"  read starved: {str(exc)[:60]}")


def step_f006(page, capture):
    """F-CANOPY-006 post-Stage-2: does the topology graph render in the live lane?

    The renderer was the 8-output callback forced at 1 Hz from every tab
    (#509 gated it to tabpoll-topology; Stage 2 suppressed its metrics-store
    chain). Attach-window reads of the counts, the figure, and the depth
    slider — plus a request-side census of the renderer callback.
    """
    log("STEP f006 -- topology render (post-Stage-2)")
    st = http_get("/api/status", timeout=30)[1]
    log(f"  /api/status: {json.dumps({k: st.get(k) for k in ('is_running', 'phase', 'hidden_units')})}")
    open_tab(page, "Network Topology")
    page.wait_for_timeout(15000)
    state = page.evaluate(
        """() => { const fig = (() => { const root = document.getElementById('network-visualizer-graph');
                     if (!root) return {present:false};
                     const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                     let n = -1; try { n = gd && gd.data ? gd.data.length : 0; } catch (e) {}
                     const r = root.getBoundingClientRect();
                     return {present:true, traces:n, w:Math.round(r.width), h:Math.round(r.height)}; })();
             const counts = {};
             for (const id of ['network-visualizer-input-count','network-visualizer-hidden-count','network-visualizer-output-count','network-visualizer-connection-count']) {
               const el = document.getElementById(id); counts[id.replace('network-visualizer-','')] = el ? (el.innerText||'').trim() : null;
             }
             const s = document.querySelector('#network-visualizer-depth-slider [role=slider]');
             const label = document.getElementById('network-visualizer-depth-label');
             return {fig: fig, counts: counts,
                     slider: s ? {now: s.getAttribute('aria-valuenow'), max: s.getAttribute('aria-valuemax')} : null,
                     depth_label: label ? (label.innerText||'').trim() : null}; }"""
    )
    log(f"  topology at ~t+15s: {json.dumps(state)[:500]}")
    render_posts = [c["t_ms"] for c in capture if "_dash-update-component" in (c.get("url") or "") and "network-visualizer-graph" in (c.get("body") or "")[:800]]
    log(f"  renderer-callback POSTs: {render_posts[:10]} (n={len(render_posts)})")
    shot(page, "F006-REDRIVE__topology.png")


STEPS = {
    "idle": step_idle,
    "start": step_start,
    "candidates": step_candidates,
    "livecards": step_livecards,
    "cardsprobe": step_cardsprobe,
    "boundaries": step_boundaries,
    "bprobe": step_bprobe,
    "dstats": step_dstats,
    "bfinal": step_bfinal,
    "bfinal2": step_bfinal2,
    "bfinal3": step_bfinal3,
    "bcausal": step_bcausal,
    "btoggle": step_btoggle,
    "brefresh": step_brefresh,
    "f025": step_f025,
    "f025idle": step_f025idle,
    "f006": step_f006,
    "f002": step_f002,
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
            log(f"capture summary: {len(capture)} requests ({n_dash} dash updates, {n_api} /api)")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
