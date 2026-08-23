#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (redux action trace)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

What does Dash actually DO when the dead store's response lands?

Established: 23 wire payloads arrive carrying data, the ``paths`` entry resolves
to the correct ``Store`` component, and the client-side ``data`` prop never leaves
``{}`` even at 400 ms sampling. So the response is received and never applied.

This wraps ``store.dispatch`` and records every redux action, so the moment a
payload arrives we can see whether Dash emits a prop-update action for this
component at all -- and if it does, what path it targets.

  no action naming the store      -> Dash decides not to apply it (the interesting
                                     case; compare against the working store's
                                     actions in the same window)
  action present but prop unchanged -> the reducer is dropping it

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_redux_actions.py --seconds 90

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_w3drv", os.path.join(_HERE, "e2e_w3_params_driver.py"))
_w3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w3)

log = _w3.log
open_dashboard = _w3.open_dashboard

DEAD = "candidate-metrics-panel-training-state-store"
LIVE = "metrics-panel-training-state-store"

FIND_STORE = """
() => {
  function fiberOf(el) {
    for (const k in el) {
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

TRACE = """
(ids) => {
  window.__ra = {types: {}, hits: [], total: 0};
  const st = window.__dashStore;
  const orig = st.dispatch.bind(st);
  st.dispatch = function(action) {
    try {
      const a = window.__ra;
      a.total++;
      const ty = (action && action.type) ? String(action.type) : typeof action;
      a.types[ty] = (a.types[ty] || 0) + 1;
      let s = '';
      try { s = JSON.stringify(action).slice(0, 4000); } catch (e) { s = ''; }
      // RESET_COMPONENT_STATE returns components to their LAYOUT DEFAULTS. At ~10/s
      // it is the prime suspect for wiping the dead store back to {}. Record what it
      // targets so the reset can be attributed to a subtree.
      if (ty === 'RESET_COMPONENT_STATE') {
        a.resets = a.resets || {n: 0, ids: {}, samples: []};
        a.resets.n++;
        try {
          const pl = action.payload;
          const arr = Array.isArray(pl) ? pl : [pl];
          for (const it of arr) {
            const key = (it && it.id) ? String(it.id) : (it && it.path ? it.path.join('/').slice(-60) : 'unknown');
            a.resets.ids[key] = (a.resets.ids[key] || 0) + 1;
          }
          if (a.resets.samples.length < 3) a.resets.samples.push(s.slice(0, 300));
        } catch (e) {}
      }
      for (const id of ids) {
        if (s.includes(id)) {
          a.hits.push({id, type: ty, snippet: s.slice(0, 260)});
        }
      }
    } catch (e) {}
    return orig(action);
  };
  return true;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=int, default=90)
    ap.add_argument("--tab", default="Candidate Metrics")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            for _ in range(10):
                if not page.evaluate(
                    """() => [...document.querySelectorAll('[role=dialog]')]
                         .filter(x=>(x.className||'').includes('show')).length"""
                ):
                    break
                page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
                page.wait_for_timeout(700)
                page.keyboard.press("Escape")
                page.wait_for_timeout(700)
            page.evaluate(
                """(l) => { const t=[...document.querySelectorAll('[role=tab]')]
                       .find(x=>x.textContent.trim()===l); if(t) t.click(); }""",
                args.tab,
            )
            page.wait_for_timeout(5000)

            if not page.evaluate(FIND_STORE):
                log("!! redux store not reachable")
                return 1
            page.evaluate(TRACE, [DEAD, LIVE])
            log(f"tracing redux dispatch for {args.seconds}s")
            page.wait_for_timeout(args.seconds * 1000)

            ra = page.evaluate("""() => window.__ra""")
            log("")
            log(f"total redux actions: {ra.get('total')}")
            types = ra.get("types", {})
            for t, n in sorted(types.items(), key=lambda kv: -kv[1])[:14]:
                log(f"    {n:>5}x  {t}")
            log("")
            hits = ra.get("hits", [])
            for cid in (DEAD, LIVE):
                mine = [h for h in hits if h["id"] == cid]
                tag = "DEAD   " if cid == DEAD else "WORKING"
                log(f"  [{tag}] {cid:<46} actions naming it: {len(mine)}")
                bytype = {}
                for h in mine:
                    bytype[h["type"]] = bytype.get(h["type"], 0) + 1
                for t, n in sorted(bytype.items(), key=lambda kv: -kv[1])[:6]:
                    log(f"        {n:>4}x  {t}")
                if mine:
                    log(f"        sample: {mine[0]['snippet'][:230]}")

            resets = ra.get("resets") or {}
            if resets:
                log("")
                log(f"RESET_COMPONENT_STATE dispatches: {resets.get('n')}")
                ids = resets.get("ids", {})
                log(f"  distinct reset targets: {len(ids)}")
                for k, n in sorted(ids.items(), key=lambda kv: -kv[1])[:16]:
                    log(f"    {n:>5}x  {k}")
                for s in resets.get("samples", [])[:2]:
                    log(f"  sample payload: {s[:280]}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
