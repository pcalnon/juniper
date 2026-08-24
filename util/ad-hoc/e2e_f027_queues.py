#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (renderer callback queues)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Answer the one question the F-CANOPY-027 dossier posed and never recorded an
answer for: when the dead store's prop changes, is its consumer QUEUED AND STUCK,
or never queued at all?

``e2e_f027_client_state.py``'s own docstring names Dash's queues (requested /
prioritized / blocked / executing / watched / executed / stored) and says "a
consumer parked in ``blocked`` forever is a different defect from one that is
never queued at all" -- but no queue measurement appears anywhere in the ledger.
Every recorded probe measured either the served dependency graph, ``paths``, the
redux ``layout``, or action TYPES. None read the queues themselves.

This probe hooks ``store.dispatch`` BEFORE injecting, so it sees every action with
its payload, then injects a novel value into the target store via the component's
own Dash-supplied ``setProps`` and reports:

  * which queue (if any) each consumer entered, sampled while it happens
  * every dispatched action naming the store or its consumers, with payload keys
  * the final resting queue contents

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_queues.py --tab 'Candidate Metrics'
    # control arm:
    ... --tab 'Training Metrics' --store metrics-panel-training-state-store

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

FIND_STORE = """
() => {
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')) return el[k];
      if (k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  const roots = ['#react-entry-point', '#_dash-app-content', 'body'];
  for (const sel of roots) {
    const el = document.querySelector(sel);
    if (!el) continue;
    let f = fiberOf(el);
    let hops = 0;
    while (f && hops < 8000) {
      const mp = f.memoizedProps;
      if (mp && mp.store && typeof mp.store.getState === 'function') {
        window.__dashStore = mp.store;
        return {found: true, via: sel, hops};
      }
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return {found: false};
}
"""

# Hook dispatch so nothing is missed between injection and reaction.
INSTALL_HOOK = """
(storeId) => {
  const st = window.__dashStore;
  window.__f027 = {actions: [], queueSnaps: [], storeId};
  const orig = st.dispatch.bind(st);
  st.dispatch = (action) => {
    try {
      let blob = '';
      try { blob = JSON.stringify(action).slice(0, 4000); } catch (e) { blob = '<unserialisable>'; }
      if (blob.indexOf(storeId) !== -1) {
        window.__f027.actions.push({type: action && action.type, blob: blob.slice(0, 1200)});
      }
    } catch (e) { /* never let the hook break the app */ }
    return orig(action);
  };
  return true;
}
"""

# Proper depth-first fiber walk (the older probes' child||sibling||return.sibling
# walk can terminate early); find the component instance whose Dash id matches.
INJECT = """
(args) => {
  const {storeId, payload} = args;
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')) return el[k];
      if (k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  const root = fiberOf(document.querySelector('#react-entry-point') || document.body);
  if (!root) return {ok: false, why: 'no root fiber'};
  const hits = [];
  const stack = [root];
  let hops = 0;
  while (stack.length && hops < 400000) {
    const f = stack.pop();
    hops++;
    const mp = f.memoizedProps;
    if (mp && mp.id === storeId && typeof mp.setProps === 'function') hits.push(f);
    if (f.child) stack.push(f.child);
    if (f.sibling) stack.push(f.sibling);
  }
  if (!hits.length) return {ok: false, why: 'no fiber with that id + setProps', hops};
  // If more than one fiber carries the id, a stale detached instance exists -- report it.
  hits[hits.length - 1].memoizedProps.setProps({data: payload});
  return {ok: true, hops, fiberMatches: hits.length};
}
"""

SNAP_QUEUES = """
() => {
  const cb = window.__dashStore.getState().callbacks || {};
  const out = {};
  for (const k of Object.keys(cb)) {
    const v = cb[k];
    if (Array.isArray(v)) {
      out[k] = v.map(c => {
        const d = (c && c.callback) || c || {};
        return d.output || d.outputs || '<?>';
      });
    } else {
      out[k] = v;
    }
  }
  return out;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="F-CANOPY-027 renderer-queue probe")
    ap.add_argument("--tab", default="Candidate Metrics")
    ap.add_argument("--store", default="candidate-metrics-panel-training-state-store")
    ap.add_argument("--watch", type=int, default=20, help="seconds to watch after injection")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            page.evaluate(
                """(l) => { const t=[...document.querySelectorAll('[role=tab]')]
                       .find(x=>x.textContent.trim()===l); if(t) t.click(); }""",
                args.tab,
            )
            page.wait_for_timeout(7000)

            found = page.evaluate(FIND_STORE)
            log(f"redux store discovery: {json.dumps(found)}")
            if not found.get("found"):
                log("  !! could not reach the redux store")
                return 1

            page.evaluate(INSTALL_HOOK, args.store)
            log(f"dispatch hook installed for {args.store}")

            before = page.evaluate(SNAP_QUEUES)
            log(f"queues BEFORE: { {k: (len(v) if isinstance(v, list) else v) for k, v in before.items()} }")

            payload = {"candidate_pool_status": "QUEUE-PROBE", "candidate_pool_size": 4242, "candidate_epoch": 7}
            res = page.evaluate(INJECT, {"storeId": args.store, "payload": payload})
            log(f"inject: {json.dumps(res)}")
            if not res.get("ok"):
                return 1
            if res.get("fiberMatches", 1) > 1:
                log(f"  !! {res['fiberMatches']} fibers carry id {args.store} -- STALE DUPLICATE INSTANCE")

            # Sample queues densely right after the injection.
            for i in range(args.watch * 2):
                page.wait_for_timeout(500)
                snap = page.evaluate(SNAP_QUEUES)
                nonempty = {k: v for k, v in snap.items() if isinstance(v, list) and v}
                if nonempty and i < 8:
                    log(f"  t+{(i+1)*0.5:.1f}s queues: { {k: len(v) for k, v in nonempty.items()} }")

            after = page.evaluate(SNAP_QUEUES)
            actions = page.evaluate("() => window.__f027.actions")
        finally:
            browser.close()

    log("")
    log(f"queues AFTER : { {k: (len(v) if isinstance(v, list) else v) for k, v in after.items()} }")
    for k, v in after.items():
        if isinstance(v, list) and v:
            log(f"  {k}: {v[:20]}")
    log("")
    log(f"actions naming {args.store}: {len(actions)}")
    for a in actions[:40]:
        log(f"  {a['type']}")
        log(f"      {a['blob'][:400]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
