#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-035 — does the payload reach dash-renderer's reducer, or not at all?

THE ONE QUESTION LEFT.

The 2026-09-05 work established, and recorded in
``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md``, that
``metrics-panel-metrics-store`` is WRITTEN and never APPLIED, and closed three
competing explanations by measurement:

  * a SECOND store instance -- refuted by ``/dashboard/_dash-layout`` (465 id-bearing
    nodes, 465 distinct, zero duplicates; the store exactly once with ``data=[]``);
  * the ungated ``allow_duplicate`` appender clobbering it -- refuted statically
    (``dashboard_manager.py:6732`` returns ``no_update`` when it drained nothing, so
    it cannot write an empty value) and empirically (``ws-metrics-buffer`` held its
    mount default, ``gen`` 0 -> 0, so it never fired);
  * a stale server-side view -- refuted by the F-039 topoprobe: 130 comparisons, all
    ``eq=False`` at a constant ``cur_len=2`` (the serialised ``[]``).

So: one store, one active writer, full 500-row payloads on the wire, and neither the
browser's copy nor the server's own ``State`` ever advancing. The response reaches the
browser and the browser does not apply it. The leading hypothesis -- dash-renderer
retiring an in-flight call on re-request -- was MEASURED at 69% request overlap and
explicitly NOT adopted, because nine unopposed responses also failed to land and the
server-side ``State`` was empty in 130 of 130, not 69% of them.

WHAT THIS PROBE DECIDES. It splits "the browser does not apply it" into the two
things that phrase conflates, by watching dash-renderer's own Redux store:

  ARRIVES-AND-DROPPED   an action carrying the store's new value is dispatched, and
                        the state does not move (or moves and is reverted)
  NEVER-ARRIVES         no dispatched action ever carries a value for this store --
                        the response is discarded before the reducer sees it

``window.store`` IS dash-renderer's Redux store (it is what the arc's ``_store``
reader already calls ``getState()`` on). Redux exposes ``dispatch`` and ``subscribe``,
so both halves are observable from the page with no product change at all -- unlike
the F-039 topoprobe, this probe patches NOTHING on the server and requires no revert.

HOW THE HOOK SURVIVES. ``window.store`` does not exist at document start, so the hook
is installed by an init script that polls for it and patches on first sight, before
any callback response can land. Patching after ``open_dashboard`` returns would race
the very first writes, and this store's whole question is about writes that happen
early and often.

WHAT IS RECORDED, AND WHY BOTH HALVES ARE NEEDED.

  dispatches   every action whose payload carries a value for the store id, with the
               action ``type`` and the row count. Catches ARRIVES.
  transitions  every observed CHANGE in the store's value length, sampled on Redux's
               subscribe. Catches APPLIED, independently of how the action got in.

Either alone is ambiguous: a dispatch log without state transitions cannot tell an
applied write from a dropped one, and a state log without dispatches cannot tell a
dropped write from an absent one. Together they are a decision procedure.

WHAT THIS PROBE DELIBERATELY DOES NOT DO. It does not synthesise a dispatch to prove
the reducer *can* apply a value. That would demonstrate the wiring while removing the
contention which is the entire subject, and a green result from it would mean nothing
about the regime under test -- the same reason the F-037 growth probe refused to fake
a ``setProps``.

READING THE OUTPUT. The verdict is printed from a rule fixed BEFORE the run (see
``_verdict``), so a surprising number cannot be reinterpreted after the fact.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py --window 60
"""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")

log = _seg17.log
CANOPY = _seg17.CANOPY
open_dashboard = _seg17.open_dashboard
open_tab = _seg17.open_tab
_store = _seg17._store

METRICS_STORE = "metrics-panel-metrics-store"
OUT = os.environ.get("F035_RENDERER_RESULTS", "/tmp/juniper-e2e/f035_renderer.json")

# The hook. Installed at document start; arms itself the moment window.store exists.
#
# Two independent observers on ONE store:
#   * a dispatch wrapper, recording actions that carry a value for the target id;
#   * a subscribe callback, recording CHANGES in the target's value length.
# Nothing is mutated -- the original dispatch is always called with the original
# action, and a failure inside the hook must never break the app, so every observer
# body is wrapped and swallows its own errors (recorded in `errors`, never silent).
_HOOK = r"""
(targetId) => {
  window.__f035 = {armed:false, dispatches:[], transitions:[], actionTypes:{},
                   totalDispatches:0, totalNotifies:0, errors:[], lastLen:null};
  const R = window.__f035;

  // Find a value for the target id inside an arbitrary action payload. Dash-renderer
  // has used several shapes across versions, so search rather than assume one.
  //
  // THE FIRST VERSION OF THIS OVER-COUNTED BY 192x, and the way it did is worth
  // keeping: a bare "is the id a key here?" test also matches dash-renderer's PATHS
  // INDEX, where `paths.strs[id]` is an array of layout keys. That yielded 577
  // `SET_PATHS` "dispatches carrying a value for the store", each reported with
  // len=18 -- the length of the PATH, presented as a row count. 580 hits, of which
  // exactly 3 were real. A key match is not a value match: require the payload
  // position to actually look like a props write.
  const isPathsAction = (a) => a && a.type === 'SET_PATHS';
  const findForId = (obj, depth) => {
    if (!obj || typeof obj !== 'object' || depth > 6) return undefined;
    if (Object.prototype.hasOwnProperty.call(obj, targetId)) {
      const v = obj[targetId];
      // A props write looks like {props:{...}} or {data:...}; anything else with
      // this id as a key is an index entry, not a value.
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        if ('data' in v) return v.data;
        if (v.props && typeof v.props === 'object' && 'data' in v.props) return v.props.data;
      }
      return undefined;
    }
    for (const k of Object.keys(obj)) {
      const v = obj[k];
      if (v && typeof v === 'object') {
        const r = findForId(v, depth + 1);
        if (r !== undefined) return r;
      }
    }
    return undefined;
  };

  const lenOf = (v) => Array.isArray(v) ? v.length : (v === null || v === undefined ? null : -1);

  // Read the target's CURRENT value out of state, by the same paths.strs index the
  // arc's reader uses -- so a transition here is comparable with a _store() read.
  const readLen = (st) => {
    try {
      if (!st || !st.layout) return null;
      const strs = st.paths && st.paths.strs ? st.paths.strs : null;
      if (!strs || !strs[targetId]) return null;
      let node = st.layout;
      for (const key of strs[targetId]) { if (node == null) break; node = node[key]; }
      if (node && node.props && Array.isArray(node.props.data)) return node.props.data.length;
      if (node && node.props && 'data' in node.props) return -1;
      return null;
    } catch (e) { return null; }
  };

  const arm = () => {
    if (R.armed) return true;
    const s = window.store;
    if (!s || !s.dispatch || !s.subscribe) return false;

    const orig = s.dispatch.bind(s);
    s.dispatch = function (action) {
      try {
        R.totalDispatches++;
        if (action && typeof action === 'object' && action.type) {
          R.actionTypes[action.type] = (R.actionTypes[action.type] || 0) + 1;
        }
        if (action && typeof action === 'object' && !isPathsAction(action)) {
          const v = findForId(action, 0);
          if (v !== undefined) {
            R.dispatches.push({t: Date.now(), type: action.type || '<no type>', len: lenOf(v)});
          }
        } else if (typeof action === 'function') {
          R.actionTypes['<thunk>'] = (R.actionTypes['<thunk>'] || 0) + 1;
        }
      } catch (e) { R.errors.push('dispatch:' + e.message); }
      return orig(action);   // never alter behaviour
    };

    s.subscribe(function () {
      try {
        R.totalNotifies++;
        const n = readLen(s.getState());
        if (n !== R.lastLen) {
          R.transitions.push({t: Date.now(), from: R.lastLen, to: n});
          R.lastLen = n;
        }
      } catch (e) { R.errors.push('subscribe:' + e.message); }
    });

    R.lastLen = readLen(s.getState());
    R.transitions.push({t: Date.now(), from: null, to: R.lastLen, note: 'initial'});
    R.armed = true;
    return true;
  };

  if (!arm()) {
    const iv = setInterval(() => { if (arm()) clearInterval(iv); }, 20);
    setTimeout(() => clearInterval(iv), 60000);
  }
}
"""


def _verdict(res: dict) -> dict:
    """The reading rule, fixed before the run.

    Four outcomes, each with a different owner. Written here rather than composed
    from the numbers afterwards, so a surprising result cannot be reinterpreted into
    whichever finding is most convenient -- the failure mode this arc has already
    paid for once.
    """
    d = res.get("dispatches") or []
    tr = [t for t in (res.get("transitions") or []) if not t.get("note")]
    carrying = [x for x in d if isinstance(x.get("len"), int) and x["len"] > 0]
    reached = [t for t in tr if isinstance(t.get("to"), int) and t["to"] > 0]

    if not res.get("armed"):
        return {"verdict": "BLOCKED", "why": "the hook never armed -- window.store not found; nothing was measured"}
    if not d:
        return {
            "verdict": "NEVER-ARRIVES",
            "why": ("no dispatched action ever carried a value for this store, over "
                    f"{res.get('totalDispatches')} dispatches. The response is discarded before the "
                    "reducer sees it -- consistent with renderer-level retirement of a superseded "
                    "in-flight call, and NOT with a reducer that drops a value it was handed."),
        }
    if carrying and not reached:
        return {
            "verdict": "ARRIVES-AND-DROPPED",
            "why": (f"{len(carrying)} dispatches carried a non-empty value and the store's state never "
                    "reached a non-empty length. The reducer is handed the payload and does not apply "
                    "it -- ownership moves to the reducer / props path, not the request layer."),
        }
    if carrying and reached:
        # A REVERT MUST BE CHECKED FOR, NOT ASSUMED. The first version of this rule
        # returned APPLIED-THEN-LOST for this whole branch, and mislabelled the one
        # run in eight where the store actually WORKED: it went 0 -> 500 and stayed
        # there, with the independent reader agreeing at 500 and no downward
        # transition anywhere. A pre-registered rule protects against reinterpreting
        # a number after the fact; it does nothing about a branch that encodes the
        # expected answer. Split the branch on the evidence instead.
        ends_empty = tr and not (isinstance(tr[-1].get("to"), int) and tr[-1]["to"] > 0)
        fell = any(
            isinstance(a.get("to"), int) and isinstance(b.get("to"), int) and b["to"] < a["to"] and a["to"] > 0
            for a, b in zip(tr, tr[1:])
        )
        if fell or ends_empty:
            return {
                "verdict": "APPLIED-THEN-LOST",
                "why": (f"{len(carrying)} dispatches carried a value, the state reached non-empty "
                        f"({[t['to'] for t in reached][:8]}), and it did not stay. Something reverts it; "
                        "read the transition list for the shape of the revert."),
            }
        return {
            "verdict": "APPLIED",
            "why": (f"{len(carrying)} dispatches carried a value, the state reached "
                    f"{[t['to'] for t in reached][:8]} and STAYED. On this run the store worked. "
                    "Against runs that read empty this is the load-bearing observation: the path is "
                    "functional, so the defect is a LOST RACE rather than a dead path."),
        }
    return {
        "verdict": "DISPATCHED-EMPTY",
        "why": ("actions naming the store were dispatched but every one carried an empty or non-list "
                "value, while the wire carries 500 rows. What is dispatched is not what was received."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=float, default=60.0, help="seconds to observe")
    ap.add_argument("--tab", default="Candidate Metrics", help="tab to drive")
    ap.add_argument(
        "--no-reload",
        action="store_true",
        help=(
            "install the hook WITHOUT reloading. The reload is not a detail: on 2026-09-07 the "
            "reloading run read the store at 500 while the unchanged 2026-09-04 re-drive, on the "
            "same leg and commit minutes apart, read 0. This flag is what isolates that variable."
        ),
    )
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res: dict = {"canopy": CANOPY, "store": METRICS_STORE, "window_s": args.window, "tab": args.tab}

    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, [])
        try:
            # Arm BEFORE anything can fire, then reload so the init script runs on a
            # document that has not yet built the store. Patching after the dashboard
            # is up would race the first writes, which is where this store's whole
            # question lives.
            ctx.add_init_script(f"({_HOOK})({json.dumps(METRICS_STORE)});")
            res["reloaded"] = not args.no_reload
            if args.no_reload:
                # No reload: the init script cannot have run on THIS document, so the
                # hook is injected directly into the live page instead. It arms later
                # than the reloading path -- which is exactly the difference under
                # test, and the reason the two arms are reported separately rather
                # than averaged.
                page.evaluate(f"({_HOOK})({json.dumps(METRICS_STORE)});")
            else:
                page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(6000)

            armed = page.evaluate("() => !!(window.__f035 && window.__f035.armed)")
            log(f"  hook armed: {armed}")

            open_tab(page, args.tab)
            page.wait_for_timeout(int(args.window * 1000))

            snap = page.evaluate(
                """() => {
                     const R = window.__f035 || {};
                     return {armed: !!R.armed, dispatches: R.dispatches || [],
                             transitions: R.transitions || [], actionTypes: R.actionTypes || {},
                             totalDispatches: R.totalDispatches || 0,
                             totalNotifies: R.totalNotifies || 0, errors: R.errors || []};
                   }"""
            )
            res.update(snap)

            # An independent read of the same store, so the hook's own view can be
            # cross-checked against the reader the ledger already quotes.
            rd = _store(page, METRICS_STORE) or {}
            res["independent_read"] = {
                "ok": rd.get("ok"),
                "via": rd.get("via"),
                "len": len(rd["value"]) if isinstance(rd.get("value"), list) else None,
            }
        finally:
            browser.close()

    res["result"] = _verdict(res)

    log(f"  armed={res.get('armed')} totalDispatches={res.get('totalDispatches')} "
        f"totalNotifies={res.get('totalNotifies')} hookErrors={len(res.get('errors') or [])}")
    log(f"  dispatches CARRYING a value for {METRICS_STORE}: {len(res.get('dispatches') or [])}")
    for x in (res.get("dispatches") or [])[:10]:
        log(f"     type={x['type']!r} len={x['len']}")
    log(f"  state transitions: {[(t.get('from'), t.get('to')) for t in (res.get('transitions') or [])][:10]}")
    log(f"  independent read: {res.get('independent_read')}")
    top = sorted((res.get("actionTypes") or {}).items(), key=lambda kv: -kv[1])[:8]
    log(f"  top action types: {top}")
    log(f"  => VERDICT: {res['result']['verdict']}")
    log(f"     {res['result']['why']}")

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
