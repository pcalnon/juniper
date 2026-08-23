#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (Dash client redux state)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Read Dash's CLIENT-SIDE redux state and diff the dead store against the working one.

This is next-step (a) recorded in the F-CANOPY-027 ledger entry. Everything from
the layout through the served ``/dashboard/_dash-dependencies`` is provably
correct and the server is provably reachable, so the break is in the client. The
redux state is where that becomes visible:

  * ``paths``     -- the id -> layout-path map. A component missing here is
                     invisible to the client's dependency resolution even though
                     it is in the served layout.
  * ``layout``    -- the LIVE props. Lets us read the store's actual client-side
                     ``data`` and compare it against what the wire delivered.
  * ``callbacks`` -- Dash's own queues (requested / prioritized / blocked /
                     executing / watched / executed / stored). A consumer parked
                     in ``blocked`` forever is a different defect from one that is
                     never queued at all.

Reaches the store through the React fiber on the Dash mount node, since Dash does
not expose it on ``window`` in a production build.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_client_state.py --tab 'Candidate Metrics' --seconds 60

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
open_dashboard = _w3.open_dashboard

DEAD_STORE = "candidate-metrics-panel-training-state-store"
LIVE_STORE = "metrics-panel-training-state-store"
DEAD_CONSUMER = "candidate-metrics-panel-status-badge"
LIVE_CONSUMER = "metrics-panel-progress-detail"

# Walk the React fiber to find the react-redux Provider's store.
FIND_STORE = """
() => {
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')) return el[k];
      if (k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  const roots = ['#react-entry-point', '#_dash-app-content', '#_dash-global-error-container', 'body'];
  for (const sel of roots) {
    const el = document.querySelector(sel);
    if (!el) continue;
    let f = fiberOf(el);
    let hops = 0;
    while (f && hops < 4000) {
      const mp = f.memoizedProps;
      if (mp && mp.store && typeof mp.store.getState === 'function') {
        window.__dashStore = mp.store;
        return {found: true, via: sel, hops};
      }
      // descend then advance: child -> sibling -> return
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return {found: false};
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tab", default="Candidate Metrics")
    ap.add_argument("--seconds", type=int, default=60)
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
            page.wait_for_timeout(6000)

            found = page.evaluate(FIND_STORE)
            log(f"redux store discovery: {json.dumps(found)}")
            if not found.get("found"):
                log("  !! could not reach the redux store via the React fiber")
                return 1

            keys = page.evaluate("""() => Object.keys(window.__dashStore.getState())""")
            log(f"redux state keys: {keys}")
            log("")

            # --- paths: is each component known to the client? ----------------
            paths = page.evaluate(
                """(ids) => { const st = window.__dashStore.getState();
                     const p = st.paths || {};
                     const strs = p.strs || p;
                     const out = {};
                     for (const id of ids) out[id] = (strs && strs[id]) ? JSON.stringify(strs[id]) : null;
                     return {count: strs ? Object.keys(strs).length : -1, hits: out}; }""",
                [DEAD_STORE, LIVE_STORE, DEAD_CONSUMER, LIVE_CONSUMER],
            )
            log(f"paths entries: {paths.get('count')}")
            for k, v in (paths.get("hits") or {}).items():
                mark = "" if v else "   <-- NOT IN paths"
                log(f"  {k:<46} {str(v)[:60]}{mark}")
            log("")

            # --- live props: what does the client think the store holds? ------
            def read_props():
                return page.evaluate(
                    """(ids) => { const st = window.__dashStore.getState();
                         const strs = (st.paths && st.paths.strs) ? st.paths.strs : st.paths;
                         const get = (obj, path) => path.reduce((o,k) => (o==null?o:o[k]), obj);
                         const out = {};
                         for (const id of ids) {
                           const pth = strs ? strs[id] : null;
                           if (!pth) { out[id] = 'NO-PATH'; continue; }
                           const node = get(st.layout, pth);
                           const d = node && node.props ? node.props.data : undefined;
                           out[id] = (d === undefined) ? 'NO-DATA-PROP'
                                     : JSON.stringify(d).slice(0, 90);
                         }
                         return out; }""",
                    [DEAD_STORE, LIVE_STORE],
                )

            p1 = read_props()
            log("client-side store props (sample 1):")
            for k, v in p1.items():
                log(f"  {k:<46} {v}")

            page.wait_for_timeout(args.seconds * 1000)

            p2 = read_props()
            log("")
            log(f"client-side store props (sample 2, +{args.seconds}s):")
            for k, v in p2.items():
                changed = "CHANGED" if p1.get(k) != v else "unchanged"
                log(f"  {k:<46} {v}   <- {changed}")

            # --- Dash's own callback queues -----------------------------------
            log("")
            qs = page.evaluate(
                """() => { const cb = window.__dashStore.getState().callbacks || {};
                     const out = {};
                     for (const k of Object.keys(cb)) {
                       const v = cb[k];
                       out[k] = Array.isArray(v) ? v.length : typeof v;
                     }
                     return out; }"""
            )
            log(f"callback queue sizes: {json.dumps(qs)}")
            stuck = page.evaluate(
                """(marker) => { const cb = window.__dashStore.getState().callbacks || {};
                     const res = {};
                     for (const k of Object.keys(cb)) {
                       const v = cb[k];
                       if (!Array.isArray(v)) continue;
                       const hits = v.filter(c => JSON.stringify(c.output||c).includes(marker));
                       if (hits.length) res[k] = hits.length;
                     }
                     return res; }""",
                DEAD_CONSUMER,
            )
            log(f"queues containing {DEAD_CONSUMER!r}: {json.dumps(stuck)}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
