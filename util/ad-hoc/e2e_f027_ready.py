#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (readiness blocker)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Name the callback that keeps F-CANOPY-027's consumers parked in ``requested``.

``e2e_f027_queues.py`` established the shape of the defect: the dead store's five
consumers ARE queued (they are in ``callbacks.requested``) and are never promoted
to ``prioritized`` -- with ``blocked``, ``executing`` and ``executed`` all at 0.
That is not "never wired"; it is "never READY".

dash-renderer promotes a requested callback only when none of its INPUTS is an
OUTPUT of another still-pending callback (``getReadyCallbacks`` in
``actions/dependencies_ts.ts``). So a single callback that never leaves the
pending set will pin every consumer of its outputs in ``requested`` forever.

This probe replicates that readiness test against the live client state and
prints, for every requested callback, which pending callback is blocking it and
which queue that blocker sits in.

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_ready.py --tab 'Candidate Metrics'

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
  for (const sel of ['#react-entry-point', '#_dash-app-content', 'body']) {
    const el = document.querySelector(sel);
    if (!el) continue;
    let f = fiberOf(el), hops = 0;
    while (f && hops < 8000) {
      const mp = f.memoizedProps;
      if (mp && mp.store && typeof mp.store.getState === 'function') { window.__dashStore = mp.store; return {found:true, via:sel}; }
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return {found:false};
}
"""

READY = """
() => {
  const st = window.__dashStore.getState();
  const cbs = st.callbacks || {};
  const QUEUES = ['requested','prioritized','blocked','executing','watched','executed','stored'];

  const norm = c => {
    const d = (c && c.callback) || c || {};
    return {
      output: d.output || '<?>',
      inputs: (d.inputs || []).map(i => `${i.id}.${i.property}`),
      outputs: (d.outputs || []).map(o => `${o.id}.${o.property}`)
    };
  };

  const byQueue = {};
  for (const q of QUEUES) byQueue[q] = (cbs[q] || []).map(norm);

  // Every output currently claimed by a pending callback, mapped to its queue.
  const pendingOutputs = {};
  for (const q of QUEUES) {
    for (const c of byQueue[q]) {
      for (const o of c.outputs) {
        if (!pendingOutputs[o]) pendingOutputs[o] = [];
        pendingOutputs[o].push({queue: q, output: c.output});
      }
    }
  }

  // For each requested callback: which of its inputs are claimed, and by whom.
  const report = byQueue.requested.map(c => ({
    output: c.output,
    blockers: c.inputs
      .filter(i => pendingOutputs[i])
      .map(i => ({input: i, claimedBy: pendingOutputs[i]}))
  }));

  return {
    counts: Object.fromEntries(QUEUES.map(q => [q, byQueue[q].length])),
    completed: cbs.completed,
    report,
    watched: byQueue.watched.map(c => c.output),
    executing: byQueue.executing.map(c => c.output)
  };
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="F-CANOPY-027 readiness-blocker probe")
    ap.add_argument("--tab", default="Candidate Metrics")
    ap.add_argument("--settle", type=int, default=25000)
    ap.add_argument("--filter", default="", help="only print requested callbacks whose output contains this")
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
            page.wait_for_timeout(args.settle)

            found = page.evaluate(FIND_STORE)
            if not found.get("found"):
                log("  !! could not reach the redux store")
                return 1
            data = page.evaluate(READY)
        finally:
            browser.close()

    log(f"queue counts: {json.dumps(data['counts'])}  completed={data['completed']}")
    log("")
    log(f"executing ({len(data['executing'])}): {data['executing']}")
    log("")
    log(f"watched ({len(data['watched'])}):")
    for w in data["watched"]:
        log(f"    {w}")
    log("")
    log("=== requested callbacks and what blocks them ===")
    for entry in data["report"]:
        if args.filter and args.filter not in entry["output"]:
            continue
        log(f"  OUT {entry['output'][:140]}")
        if not entry["blockers"]:
            log("      READY (nothing claims its inputs) -- should have been promoted")
        for b in entry["blockers"]:
            claims = ", ".join(f"{c['queue']}:{c['output'][:80]}" for c in b["claimedBy"])
            log(f"      blocked-by input {b['input']}  <- {claims}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
