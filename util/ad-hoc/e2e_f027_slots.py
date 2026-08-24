#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root cause (renderer slot saturation)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Measure dash-renderer's 12-slot concurrent-callback pool and prove whether the
dashboard keeps it saturated.

dash-renderer's prioritized-callback executor (dash_renderer.dev.js:2846, dash
4.2.0) promotes work out of ``callbacks.prioritized`` with a HARD-CODED cap:

    available = Math.max(0, 12 - executing.length - watched.length);
    pickedSyncCallbacks = syncCallbacks.slice(0, available);

If ``executing + watched >= 12`` then ``available == 0`` and NOTHING leaves
``prioritized`` on that pass. Ordering is by ``sortPriority`` -> ``getPriority``,
a base-36 string of the callback's downstream chain depth and breadth, sorted
DESCENDING. A terminal render callback -- one whose outputs feed no further
callback -- scores the minimum and therefore loses every arbitration while the
pool is contended.

That is a starvation regime, not a wiring fault: the callback is registered,
resolvable and queued, and simply never picked.

This probe samples the pool densely and reports:
  * the distribution of ``available`` (how often the pool is full)
  * which callbacks occupy the slots (``watched``) and for how long
  * which callbacks sit in ``prioritized`` without ever being picked

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_f027_slots.py --tab 'Candidate Metrics' --seconds 60

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_w3drv", os.path.join(_HERE, "e2e_w3_params_driver.py"))
_w3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w3)

log = _w3.log
open_dashboard = _w3.open_dashboard

RENDERER_SLOT_CAP = 12  # dash_renderer.dev.js:2846 -- hard-coded, not configurable

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
      if (mp && mp.store && typeof mp.store.getState === 'function') { window.__dashStore = mp.store; return {found:true}; }
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return {found:false};
}
"""

# Subscribe rather than poll: a 250 ms sample cannot prove "never picked" when the
# renderer churns several times a second (the arc's own instrument rule).
INSTALL_WATCH = """
() => {
  const st = window.__dashStore;
  window.__slots = {samples: [], watched: {}, prioritized: {}, n: 0};
  const name = c => { const d = (c && c.callback) || c || {}; return d.output || '<?>'; };
  st.subscribe(() => {
    const s = st.getState().callbacks || {};
    const ex = (s.executing || []).length, wa = (s.watched || []).length;
    const rec = window.__slots;
    rec.n += 1;
    rec.samples.push([ex, wa, (s.prioritized || []).length, (s.requested || []).length, s.completed || 0]);
    if (rec.samples.length > 40000) rec.samples.shift();
    for (const c of (s.watched || [])) { const k = name(c); rec.watched[k] = (rec.watched[k] || 0) + 1; }
    for (const c of (s.prioritized || [])) { const k = name(c); rec.prioritized[k] = (rec.prioritized[k] || 0) + 1; }
  });
  return true;
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="F-CANOPY-027 renderer slot-saturation probe")
    ap.add_argument("--tab", default="Candidate Metrics")
    ap.add_argument("--seconds", type=int, default=60)
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
            page.wait_for_timeout(5000)
            if not page.evaluate(FIND_STORE).get("found"):
                log("  !! could not reach the redux store")
                return 1
            page.evaluate(INSTALL_WATCH)
            log(f"subscribed; watching {args.seconds}s on tab {args.tab!r}")
            page.wait_for_timeout(args.seconds * 1000)
            data = page.evaluate("() => window.__slots")
        finally:
            browser.close()

    samples = data["samples"]
    log(f"state changes observed: {data['n']}   samples: {len(samples)}")
    if not samples:
        log("no samples")
        return 1

    avail = collections.Counter()
    pri_len = []
    for ex, wa, pr, rq, comp in samples:
        avail[max(0, RENDERER_SLOT_CAP - ex - wa)] += 1
        pri_len.append(pr)

    total = sum(avail.values())
    log("")
    log(f"=== renderer slot availability (cap {RENDERER_SLOT_CAP}) ===")
    for slots in sorted(avail):
        n = avail[slots]
        log(f"  available={slots:<3} {n:>7} samples  ({100.0*n/total:5.1f}%)")
    full = avail.get(0, 0)
    log(f"  POOL FULL (available==0): {full}/{total} samples = {100.0*full/total:.1f}%")
    log("")
    log(f"prioritized queue length: min={min(pri_len)} max={max(pri_len)} last={pri_len[-1]}")
    log(f"completed: {samples[0][4]} -> {samples[-1][4]}  (+{samples[-1][4]-samples[0][4]})")

    log("")
    log("=== slot holders (samples spent in `watched`) ===")
    for k, v in sorted(data["watched"].items(), key=lambda kv: -kv[1])[:16]:
        log(f"  {v:>7}  {k[:120]}")

    log("")
    log("=== starving in `prioritized` (samples spent waiting, never picked) ===")
    for k, v in sorted(data["prioritized"].items(), key=lambda kv: -kv[1])[:20]:
        log(f"  {v:>7}  {k[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
