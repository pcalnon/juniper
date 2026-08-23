#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (subscribe, don't sample)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Re-test "the prop never changes" WITHOUT sampling.

The earlier apply-watch polled the client-side prop every 400 ms and concluded the
dead store's ``data`` never leaves ``{}``. That conclusion is only safe if nothing
writes-then-reverts inside a sample gap -- and ``SET_PATHS`` fires ~2/s while
``RESET_COMPONENT_STATE`` fires ~13/s, so a transient write could easily hide
between samples. Sampling an idle-looking value proves nothing; subscribing does.

``store.subscribe`` fires after EVERY dispatch, so this observes every state the
prop ever holds. Records each distinct value with the action count at which it
appeared, for the dead store and a working control.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_subscribe_watch.py --seconds 90

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

SUBSCRIBE = """
(ids) => {
  window.__sw = {t0: Date.now(), n: 0, series: {}};
  for (const id of ids) window.__sw.series[id] = [];
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
      // keep it short but distinguishing
      return s.length > 70 ? (s.slice(0, 70) + '...len=' + s.length) : s;
    } catch (e) { return 'ERR'; }
  };

  window.__swUnsub = st.subscribe(() => {
    const S = window.__sw;
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
            page.evaluate(SUBSCRIBE, [DEAD, LIVE])
            log(f"subscribed to every state change for {args.seconds}s")
            page.wait_for_timeout(args.seconds * 1000)

            sw = page.evaluate("""() => { if (window.__swUnsub) window.__swUnsub(); return window.__sw; }""")
            log("")
            log(f"state changes observed: {sw.get('n')}")
            for tag, cid in (("DEAD   ", DEAD), ("WORKING", LIVE)):
                series = (sw.get("series") or {}).get(cid, [])
                log("")
                log(f"[{tag}] {cid}")
                log(f"    distinct values observed: {len(series)}")
                for e in series[:20]:
                    log(f"      change#{e['n']:<6} t={e['t']/1000.0:>7.1f}s  {e['v']}")
                if len(series) > 20:
                    log(f"      ... {len(series)-20} more")
            log("")
            dead_series = (sw.get("series") or {}).get(DEAD, [])
            non_default = [e for e in dead_series if e["v"] not in ("{}", "NO-PATH", "NO-NODE", "NO-DATA")]
            if non_default:
                log(f"  VERDICT (b): the dead prop DID hold real data {len(non_default)} time(s) -> it is written then reverted")
                for e in non_default[:5]:
                    log(f"      change#{e['n']} t={e['t']/1000.0:0.1f}s  {e['v'][:70]}")
            else:
                log("  VERDICT (a): the dead prop NEVER held anything but its default, across every state change")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
