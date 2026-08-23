#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (path resolution)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Do the client's ``paths`` entries actually RESOLVE to the component they name?

The client-state probe found the smoking gun: the dead store's client-side
``data`` prop sits at its layout default ``{}`` forever, even though the wire
delivered 29 payloads of which 27 differed. So Dash is not applying the writer's
response to the client's copy of that store -- which is precisely why no consumer
ever fires: from the client's point of view the Input never changed.

Dash applies an output by looking the component id up in ``state.paths`` and
walking that path into ``state.layout``. If the path is stale or wrong, the write
lands somewhere else or nowhere at all, silently.

This walks each watched id's path into the live layout and reports what is
actually sitting there -- the id it finds, the component type, and whether they
match. A mismatch is the root cause.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_path_resolve.py --tab 'Candidate Metrics'

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

WATCH = [
    ("DEAD   ", "candidate-metrics-panel-training-state-store"),
    ("DEAD   ", "candidate-metrics-panel-status-badge"),
    ("DEAD   ", "dataset-plotter-dataset-store"),
    ("DEAD   ", "decision-boundary-boundary-data"),
    ("WORKING", "metrics-panel-training-state-store"),
    ("WORKING", "metrics-panel-progress-detail"),
]

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
        window.__dashStore = mp.store; return {found: true, via: sel};
      }
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return {found: false};
}
"""

RESOLVE = """
(ids) => {
  const st = window.__dashStore.getState();
  const strs = (st.paths && st.paths.strs) ? st.paths.strs : st.paths;
  const walk = (obj, path) => path.reduce((o,k) => (o == null ? o : o[k]), obj);
  const out = {};
  for (const id of ids) {
    const p = strs ? strs[id] : null;
    if (!p) { out[id] = {path: null, note: 'NO PATH ENTRY'}; continue; }
    const node = walk(st.layout, p);
    if (node == null) { out[id] = {path: p.join('/'), note: 'PATH RESOLVES TO NOTHING'}; continue; }
    const props = node.props || {};
    out[id] = {
      pathLen: p.length,
      path: p.join('/'),
      foundId: (props.id === undefined) ? null : String(props.id),
      type: node.type || null,
      matches: props.id === id,
      hasData: ('data' in props),
      dataPreview: ('data' in props) ? JSON.stringify(props.data).slice(0, 70) : null
    };
  }
  return out;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
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
            page.wait_for_timeout(8000)

            f = page.evaluate(FIND_STORE)
            log(f"redux store: {json.dumps(f)}")
            if not f.get("found"):
                return 1

            res = page.evaluate(RESOLVE, [i for _, i in WATCH])
            log("")
            for tag, cid in WATCH:
                r = res.get(cid, {})
                if r.get("note"):
                    log(f"  [{tag}] {cid:<46} {r['note']}")
                    continue
                mark = "OK" if r.get("matches") else "*** MISMATCH ***"
                log(f"  [{tag}] {cid:<46} {mark}")
                log(f"          resolves to id={r.get('foundId')!r} type={r.get('type')!r} pathLen={r.get('pathLen')}")
                if r.get("hasData"):
                    log(f"          data={r.get('dataPreview')}")
            log("")
            log("full paths (for diffing the dead vs working prefix):")
            for tag, cid in WATCH:
                r = res.get(cid, {})
                if r.get("path"):
                    log(f"  [{tag}] {cid}")
                    log(f"        {r['path']}")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
