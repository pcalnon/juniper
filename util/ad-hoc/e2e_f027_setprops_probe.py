#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (constructive setProps test)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

If the prop is written BY HAND, do the dead consumers fire?

Confirmed by subscribing to all 5974 state changes: the dead store's client-side
``data`` never holds anything but ``{}``, while its consumers are registered, in
the browser's dependency graph, and resolve through ``paths`` to the right
component. The remaining question is which half is broken.

This finds the Store component's React instance and calls its Dash-supplied
``setProps({data: ...})`` -- the same entry point a component uses to push a value
back into Dash -- and then watches whether the consumer callbacks dispatch.

  consumers fire  -> the dependency wiring is FINE; the defect is confined to Dash
     applying the callback response to this component's prop.
  consumers silent -> the wiring itself is broken for this component, and the
     unapplied response is a symptom rather than the cause.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_setprops_probe.py

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
CONSUMERS = [
    "candidate-metrics-panel-status-badge",
    "candidate-metrics-panel-pool-info",
    "candidate-metrics-panel-pool-history-store",
]

# Find the React fiber whose memoizedProps.id matches, and grab setProps from it.
SETPROPS = """
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
      // some builds put it on the instance
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

HOOK = """
() => {
  window.__sp = {outs: []};
  const orig = window.fetch;
  window.fetch = async function(...a) {
    const url = (typeof a[0]==='string') ? a[0] : ((a[0]&&a[0].url)||'');
    try { if (url.includes('_dash-update-component') && a[1] && a[1].body) {
      const o = (JSON.parse(a[1].body).output)||'';
      if (o) window.__sp.outs.push({t: Date.now(), o});
    } } catch(e){}
    return orig.apply(this,a);
  };
  window.__spReset = () => { window.__sp.outs.length = 0; };
  return true;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tab", default="Candidate Metrics")
    ap.add_argument("--settle", type=int, default=45)
    ap.add_argument("--store", default=STORE, help="component id to inject into")
    ap.add_argument("--consumers", default=",".join(CONSUMERS), help="comma-separated consumer ids to watch")
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
            page.evaluate(HOOK)

            # Read the DOM of whatever consumers we were asked to watch -- hardcoding
            # the candidate ids made this line meaningless in a control run.
            watch_pre = [c.strip() for c in args.consumers.split(",") if c.strip()]
            DOM_READ = """(ids) => { const o={};
                 for (const id of ids) { const e=document.getElementById(id);
                   o[id] = e ? (e.innerText||'').trim().slice(0,40) : 'ABSENT'; }
                 return o; }"""
            before = page.evaluate(DOM_READ, watch_pre)
            log(f"DOM before setProps: {before}")

            page.evaluate("""() => window.__spReset()""")
            payload = {
                "candidate_pool_status": "PROBE-INJECTED",
                "candidate_pool_phase": "PROBE-PHASE",
                "candidate_pool_size": 4242,
                "candidate_epoch": 7,
                "candidate_total_epochs": 400,
            }
            res = page.evaluate(SETPROPS, {"id": args.store, "value": payload})
            log(f"setProps result: {res}")
            if not res.get("ok"):
                log("  !! could not call setProps; test inconclusive")
                return 1

            # CONTROL: did setProps actually change the redux prop? Without this the
            # "consumers stayed silent" result is meaningless -- a no-op write would
            # produce the same silence.
            page.wait_for_timeout(3000)
            prop_now = page.evaluate(
                """(id) => {
                  function fiberOf(el) { for (const k in el) {
                    if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')
                        || k.startsWith('__reactContainer$')) return el[k]; } return null; }
                  let f = fiberOf(document.querySelector('#react-entry-point') || document.body), hops=0;
                  while (f && hops < 4000) {
                    const mp = f.memoizedProps;
                    if (mp && mp.store && typeof mp.store.getState === 'function') {
                      const st = mp.store.getState();
                      const strs = (st.paths && st.paths.strs) ? st.paths.strs : st.paths;
                      const p = strs ? strs[id] : null;
                      if (!p) return 'NO-PATH';
                      const node = p.reduce((o,k)=> (o==null?o:o[k]), st.layout);
                      const d = node && node.props ? node.props.data : undefined;
                      return d === undefined ? 'NO-DATA' : JSON.stringify(d).slice(0,90);
                    }
                    f = f.child || f.sibling || (f.return ? f.return.sibling : null); hops++;
                  }
                  return 'NO-STORE';
                }""",
                args.store,
            )
            log(f"CONTROL -- redux prop after setProps: {prop_now}")
            if prop_now in ("{}", "NO-DATA"):
                log("  !! setProps did NOT change the prop -- the silence below proves nothing about wiring")

            log(f"waiting {args.settle}s for consumers...")
            page.wait_for_timeout(args.settle * 1000)

            outs = page.evaluate("""() => window.__sp.outs""")
            log("")
            log(f"dispatches after the injection: {len(outs)}")
            watch = [c.strip() for c in args.consumers.split(",") if c.strip()]
            for cid in watch:
                n = sum(1 for o in outs if cid in (o.get("o") or ""))
                log(f"  {cid:<48} {n:>3} dispatch(es)  <- {'FIRED' if n else 'silent'}")

            after = page.evaluate(DOM_READ, watch_pre)
            log("")
            log(f"DOM after  setProps: {after}")
            log(f"DOM changed: {before != after}")
            log("")
            fired = any(sum(1 for o in outs if c in (o.get("o") or "")) for c in watch)
            if fired:
                log("  VERDICT: wiring is FINE -- defect confined to Dash applying the response to this prop")
            else:
                log("  VERDICT: consumers stayed silent even on a hand-written prop -> the wiring itself is broken")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
