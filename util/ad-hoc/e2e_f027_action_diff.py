#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (action-sequence diff)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Side-by-side diff of what Dash DOES when a payload lands, dead store vs working store.

Established by the client-state work: for the dead store the client's ``data`` prop
never leaves ``{}`` even though 23 responses carrying data arrived, while the
working store updates normally. ``paths`` resolves correctly for both, and redux
dispatches name both. So the two differ somewhere in the action sequence that
follows a response.

This records the FULL ordered redux action stream with timestamps, and separately
timestamps each response arrival per store. It then prints the action window around
matched arrivals for each store and diffs the action-type sequences, so the branch
Dash takes for one and not the other becomes visible.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_action_diff.py --seconds 90

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

INSTALL = """
(cfg) => {
  const {dead, live} = cfg;
  window.__ad = {t0: Date.now(), actions: [], arrivals: [], seq: 0};

  // --- full ordered action stream -----------------------------------------
  const st = window.__dashStore;
  const origDispatch = st.dispatch.bind(st);
  st.dispatch = function(action) {
    try {
      const A = window.__ad;
      const ty = (action && action.type) ? String(action.type) : typeof action;
      let names = [];
      try {
        const s = JSON.stringify(action);
        if (s.includes(dead)) names.push('DEAD');
        if (s.includes(live)) names.push('LIVE');
      } catch (e) {}
      A.actions.push({i: A.seq++, t: Date.now() - A.t0, ty, names: names.join('+')});
      if (A.actions.length > 60000) A.actions.shift();
    } catch (e) {}
    return origDispatch(action);
  };

  // --- response arrivals, per store ---------------------------------------
  const origFetch = window.fetch;
  window.fetch = async function(...a) {
    const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
    let out = '';
    try { if (url.includes('_dash-update-component') && a[1] && a[1].body) {
      out = (JSON.parse(a[1].body).output) || '';
    } } catch(e){}
    const res = await origFetch.apply(this,a);
    try {
      if (out) {
        // exact-ish: DEAD contains LIVE as a substring, so test DEAD first
        let which = null;
        if (out.includes(dead)) which = 'DEAD';
        else if (out.includes(live)) which = 'LIVE';
        if (which) {
          res.clone().text().then(t => {
            let hasData = false;
            try {
              const j = JSON.parse(t); const r = j.response || {};
              const key = (which === 'DEAD') ? dead : live;
              hasData = !!(r[key] && ('data' in r[key]));
            } catch(e){}
            window.__ad.arrivals.push({
              which, hasData,
              t: Date.now() - window.__ad.t0,
              seqAt: window.__ad.seq
            });
          }).catch(()=>{});
        }
      }
    } catch(e){}
    return res;
  };
  return true;
}
"""


def window_after(actions, seq_at, n=14):
    """Actions dispatched at or after the sequence index where a response landed."""
    return [a for a in actions if a["i"] >= seq_at][:n]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=int, default=90)
    ap.add_argument("--tab", default="Candidate Metrics")
    ap.add_argument("--windows", type=int, default=3, help="matched arrivals to print per store")
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
            page.evaluate(INSTALL, {"dead": DEAD, "live": LIVE})
            log(f"recording action stream + arrivals for {args.seconds}s")
            page.wait_for_timeout(args.seconds * 1000)

            data = page.evaluate("""() => window.__ad""")
            actions = data.get("actions", [])
            arrivals = data.get("arrivals", [])
            log("")
            log(f"actions recorded : {len(actions)}")
            for which in ("DEAD", "LIVE"):
                mine = [a for a in arrivals if a["which"] == which]
                withd = sum(1 for a in mine if a.get("hasData"))
                log(f"arrivals {which:<5}: {len(mine)} (carrying data: {withd})")
            log("")

            for which, label in (("DEAD", DEAD), ("LIVE", LIVE)):
                mine = [a for a in arrivals if a["which"] == which and a.get("hasData")]
                log("=" * 78)
                log(f"{which}  {label}")
                if not mine:
                    log("  no data-carrying arrivals in this window")
                    continue
                for arr in mine[: args.windows]:
                    log(f"  --- arrival at t={arr['t']/1000.0:0.1f}s (seq {arr['seqAt']}) ---")
                    for a in window_after(actions, arr["seqAt"]):
                        tag = f"  [{a['names']}]" if a["names"] else ""
                        log(f"      +{a['i'] - arr['seqAt']:>3}  t={a['t']/1000.0:>7.1f}s  {a['ty']}{tag}")
                log("")

            # Compact type-sequence comparison
            log("=" * 78)
            log("action-TYPE sequence immediately after a data-carrying arrival:")
            for which in ("DEAD", "LIVE"):
                mine = [a for a in arrivals if a["which"] == which and a.get("hasData")]
                if not mine:
                    continue
                seqs = []
                for arr in mine[:5]:
                    seqs.append([a["ty"] for a in window_after(actions, arr["seqAt"], 8)])
                log(f"  {which}:")
                for s in seqs:
                    log(f"    {' -> '.join(s)}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
