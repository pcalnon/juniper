#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (is the payload applied?)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Correlate wire payloads against the CLIENT-SIDE prop, at high frequency.

Established so far: the wire delivers ~29 payloads for the dead store (27 of them
changing), the client's ``paths`` entry resolves correctly to the right ``Store``
component, and that component's client-side ``data`` sits at its declared default
``{}`` forever. So Dash is not applying the writer's response.

Two possibilities remain and they need different fixes:
  (a) never applied      -> the prop never leaves ``{}`` even momentarily;
  (b) applied then reset -> the prop briefly holds real data and something puts it
      back (e.g. the ``visualization-tabs.children`` rebuild re-creating the panel
      from its layout defaults).

Samples the redux prop every 400 ms, logs every distinct value, and timestamps
each arriving wire payload so the two series can be lined up.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_apply_watch.py --seconds 90

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

STORE = "candidate-metrics-panel-training-state-store"

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

WATCH = """
(storeId) => {
  window.__aw = {props: [], wire: [], t0: Date.now()};
  const walk = (obj, path) => path.reduce((o,k) => (o == null ? o : o[k]), obj);
  const readProp = () => {
    try {
      const st = window.__dashStore.getState();
      const strs = (st.paths && st.paths.strs) ? st.paths.strs : st.paths;
      const p = strs ? strs[storeId] : null;
      if (!p) return 'NO-PATH';
      const node = walk(st.layout, p);
      if (node == null) return 'NO-NODE';
      const d = node.props ? node.props.data : undefined;
      return d === undefined ? 'NO-DATA' : JSON.stringify(d).slice(0, 60);
    } catch (e) { return 'ERR:' + e.message.slice(0,40); }
  };
  window.__awTick = setInterval(() => {
    const v = readProp();
    const a = window.__aw.props;
    if (!a.length || a[a.length-1].v !== v) {
      a.push({t: Date.now() - window.__aw.t0, v});
    }
  }, 400);

  const orig = window.fetch;
  window.fetch = async function(...a) {
    const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
    let out = '';
    try { if (url.includes('_dash-update-component') && a[1] && a[1].body) {
      out = (JSON.parse(a[1].body).output) || '';
    } } catch(e){}
    const res = await orig.apply(this,a);
    try {
      if (out && out.includes(storeId)) {
        res.clone().text().then(t => {
          let hasData = false;
          try { const j = JSON.parse(t); const r = j.response || {};
                hasData = !!(r[storeId] && ('data' in r[storeId])); } catch(e){}
          window.__aw.wire.push({t: Date.now() - window.__aw.t0, hasData});
        }).catch(()=>{});
      }
    } catch(e){}
    return res;
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
            page.evaluate(WATCH, STORE)
            log(f"watching {STORE} for {args.seconds}s (prop sampled every 400ms)")
            page.wait_for_timeout(args.seconds * 1000)

            data = page.evaluate("""() => { clearInterval(window.__awTick); return window.__aw; }""")
            props = data.get("props", [])
            wire = data.get("wire", [])
            log("")
            log(f"wire payloads for this store : {len(wire)} (with data: {sum(1 for w in wire if w.get('hasData'))})")
            log(f"distinct CLIENT prop values  : {len(props)}")
            log("")
            log("client prop timeline (every distinct value):")
            for e in props[:24]:
                log(f"    t={e['t']/1000.0:>7.1f}s   {e['v']}")
            log("")
            if wire:
                ts = [round(w["t"] / 1000.0, 1) for w in wire]
                log(f"wire payload arrival times (s): {ts[:20]}")
            log("")
            if len(props) <= 1:
                log("  VERDICT (a): the client prop NEVER leaves its default -> payload is never applied")
            else:
                log("  VERDICT (b): the client prop DOES change -> something resets it; see the timeline")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
