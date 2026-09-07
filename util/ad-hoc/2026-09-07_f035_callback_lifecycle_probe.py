#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-035 — is the store-writing callback RETIRED before its result is applied?

WHERE THIS PICKS UP.

``util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py`` established, and
``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` records, that
the 500-row payload for ``metrics-panel-metrics-store`` is discarded **before
dash-renderer's reducer sees it**: over four runs (5,230 / 9,794 / 10,425 / 10,616
dispatches) not one dispatched action carried a value for that store, while the wire
carried full payloads throughout. One run in eight went ``0 -> 500`` and STAYED, which
is why the finding is a **lost race** and not a dead path.

What that measurement could NOT do is name the mechanism. "No dispatch ever carries the
value" is consistent with dash-renderer retiring a superseded in-flight call -- the
arc's documented 12-slot behaviour, and the 69% request overlap measured 2026-09-05 --
but equally with any other discard between response receipt and the aggregate action.

WHAT THIS PROBE ADDS. dash-renderer keeps its pending-callback bookkeeping **in the
same Redux store** the arc already reads, under ``state.callbacks``. So the lifecycle
is observable without touching the minified bundle at all: watch which lists a
store-writing callback passes through, and whether it ever reaches the one that means
"its result was applied".

The decision procedure, written as TESTS rather than as an expected story (the
previous probe's reading rule asserted a revert it never checked for, and mislabelled
its single most important run):

  RETIRED-BEFORE-EXECUTION   entries for this output appear in the pre-execution lists
                             and NEVER in the executed/stored list -> the renderer drops
                             the call before its result can be applied. This is what
                             retirement looks like.
  EXECUTED-NOT-APPLIED       entries DO reach the executed list, yet the store's value
                             never advances -> the discard is after execution, and
                             retirement is NOT the mechanism.
  NEVER-REQUESTED            no entry for this output appears in any list -> the
                             callback is not being scheduled at all, which would
                             contradict the wire evidence and indict the instrument.
  APPLIED                    the store advances, as it did in 1 of 8 runs. Reported so a
                             winning race is never silently folded into a loss.

SHAPE IS DISCOVERED, NOT ASSUMED. ``state.callbacks``'s sub-lists have been renamed
across dash-renderer versions, so ``--discover`` dumps the real keys and a sample entry
against the running leg, and the classifier keys off substring matching on list NAMES
rather than a hard-coded schema. An instrument that assumes a schema it did not check
is how a confident zero gets produced.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py --discover
    ... then the same command with --window 60
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
OUT = os.environ.get("F035_LIFECYCLE_RESULTS", "/tmp/juniper-e2e/f035_lifecycle.json")

# Dump the real shape of state.callbacks so the classifier is written against what is
# there rather than what a version's docs say should be.
_DISCOVER = r"""
() => {
  const st = window.store && window.store.getState ? window.store.getState() : null;
  if (!st) return {ok:false, why:'<no redux store>'};
  const cb = st.callbacks;
  if (!cb) return {ok:false, why:'<no state.callbacks>', stateKeys:Object.keys(st)};
  const out = {ok:true, stateKeys:Object.keys(st), callbackKeys:Object.keys(cb), lists:{}};
  for (const k of Object.keys(cb)) {
    const v = cb[k];
    out.lists[k] = {type: Array.isArray(v) ? 'array' : typeof v,
                    len: Array.isArray(v) ? v.length : null};
    if (Array.isArray(v) && v.length) {
      try { out.lists[k].sample = JSON.parse(JSON.stringify(v[0])); } catch (e) { out.lists[k].sample = '<unserialisable>'; }
      // SHAPE CENSUS -- the matcher's own adequacy, per list.
      //
      // `isOutput` reads a callback's outputs from one of three positions. If a list's
      // entries expose NONE of them, the matcher can never match anything in that list
      // and an empty bucket for it is STRUCTURAL, not a measurement. A 2026-09-07
      // positive control made this concrete: the HEALTHY topology store produced the
      // same empty terminal bucket as the broken metrics store, so the verdict was not
      // discriminating. This census is what tells you which case you are in, and it is
      // reported for every list whether or not the target id appears anywhere.
      let cbOut = 0, pOut = 0, erOut = 0, ids = 0;
      for (const e of v) {
        if (e && e.callback && Array.isArray(e.callback.outputs)) cbOut++;
        if (e && e.payload && Array.isArray(e.payload.outputs)) pOut++;
        if (e && e.executionResult && e.executionResult.payload
            && Array.isArray(e.executionResult.payload.outputs)) erOut++;
        try {
          const L = (e && e.callback && e.callback.outputs) || (e && e.payload && e.payload.outputs) || [];
          for (const o of L) { if (o && o.id) ids++; }
        } catch (err) { /* shape census must never throw */ }
      }
      out.lists[k].shapes = {entries: v.length, has_callback_outputs: cbOut,
                             has_payload_outputs: pOut, has_executionResult_outputs: erOut,
                             total_output_ids_visible: ids};
    }
  }
  return out;
}
"""

# The watcher. Samples state.callbacks on every Redux notify and records, per list,
# how many entries mention the target output -- plus a high-water mark, because a
# callback can enter and leave a list between two notifies and a last-value-only
# reading would miss it entirely.
_HOOK = r"""
(targetId) => {
  window.__f035c = {armed:false, seen:{}, everSeen:{}, touchHigh:{}, samples:[], notifies:0,
                    storeLen:null, storeLenSeq:[], errors:[],
                    // RUN STRUCTURE. "present in `watched` for 1682 notifies" is satisfied
                    // by two mechanisms needing OPPOSITE fixes: a SERIES of entries each
                    // superseded before resolving (retirement -> suppress the trigger), or
                    // ONE entry whose promise never resolves (a hung request -> a different
                    // defect entirely). A presence COUNT cannot separate them; the number of
                    // contiguous present-blocks can. `entries` counts absent->present
                    // transitions per list; `maxRun` is the longest unbroken presence.
                    entries:{}, curRun:{}, maxRun:{}, present:{}};
  const R = window.__f035c;

  // MATCH ON THE OUTPUT POSITION, NOT ANYWHERE IN THE ENTRY.
  //
  // A substring test over the serialised entry would count every callback that merely
  // TOUCHES this store -- and it is a `State` of its writer and an `Input` of the
  // metrics plots, the stats tiles and the candidate panel, so nearly every entry in
  // every list mentions it. That measures "callbacks near the store", not "the
  // callback that writes it", and would put a large confident number on the wrong
  // question. It is the same wrong-position error that made the previous probe count
  // dash-renderer's paths index as data (577 bogus hits at len=18).
  //
  // Both shapes seen in the discovery dump are checked: `callback.outputs[]` and
  // `payload.outputs[]`, each `{id, property}`.
  const isOutput = (entry) => {
    try {
      const lists = [];
      if (entry && entry.callback && Array.isArray(entry.callback.outputs)) lists.push(entry.callback.outputs);
      if (entry && entry.payload && Array.isArray(entry.payload.outputs)) lists.push(entry.payload.outputs);
      if (entry && entry.executionResult && entry.executionResult.payload
          && Array.isArray(entry.executionResult.payload.outputs)) lists.push(entry.executionResult.payload.outputs);
      for (const L of lists) { for (const o of L) { if (o && o.id === targetId) return true; } }
      return false;
    } catch (e) { return false; }
  };
  // Kept as a deliberate CONTRAST, never as the measurement: if `touches` is large
  // while `isOutput` is zero, that is the store being read everywhere and written
  // nowhere -- which is the finding, not an instrument failure.
  const touches = (entry) => {
    try { return JSON.stringify(entry).indexOf(targetId) !== -1; } catch (e) { return false; }
  };

  const readStoreLen = (st) => {
    try {
      const strs = st.paths && st.paths.strs ? st.paths.strs : null;
      if (!strs || !strs[targetId] || !st.layout) return null;
      let node = st.layout;
      for (const key of strs[targetId]) { if (node == null) break; node = node[key]; }
      if (node && node.props && Array.isArray(node.props.data)) return node.props.data.length;
      return null;
    } catch (e) { return null; }
  };

  const sample = () => {
    const s = window.store;
    if (!s || !s.getState) return;
    const st = s.getState();
    const cb = st.callbacks || {};
    R.notifies++;
    for (const k of Object.keys(cb)) {
      const v = cb[k];
      if (!Array.isArray(v)) continue;
      const outs = v.filter(isOutput);
      const n = outs.length;
      const was = !!R.present[k];
      const now = n > 0;
      if (now && !was) { R.entries[k] = (R.entries[k] || 0) + 1; R.curRun[k] = 0; }
      if (now) { R.curRun[k] = (R.curRun[k] || 0) + 1; R.maxRun[k] = Math.max(R.maxRun[k] || 0, R.curRun[k]); }
      else if (was) { R.curRun[k] = 0; }
      R.present[k] = now;
      if (n > 0) {
        R.seen[k] = (R.seen[k] || 0) + 1;                       // notifies where it was present
        R.everSeen[k] = Math.max(R.everSeen[k] || 0, n);        // high-water count in that list
        if (R.samples.length < 12) {
          try { R.samples.push({list:k, entry: JSON.parse(JSON.stringify(outs[0]))}); }
          catch (e) { /* a sample we cannot serialise is not worth failing over */ }
        }
      }
      const t = v.filter(touches).length;
      if (t > 0) R.touchHigh[k] = Math.max(R.touchHigh[k] || 0, t);
    }
    const L = readStoreLen(st);
    if (L !== R.storeLen) { R.storeLenSeq.push({t:Date.now(), from:R.storeLen, to:L}); R.storeLen = L; }
  };

  const arm = () => {
    const s = window.store;
    if (!s || !s.subscribe || !s.getState) return false;
    if (R.armed) return true;
    s.subscribe(function () { try { sample(); } catch (e) { R.errors.push(String(e.message)); } });
    try { sample(); } catch (e) { R.errors.push(String(e.message)); }
    R.armed = true;
    return true;
  };

  if (!arm()) {
    const iv = setInterval(() => { if (arm()) clearInterval(iv); }, 20);
    setTimeout(() => clearInterval(iv), 60000);
  }
}
"""

# List-name classification. dash-renderer has renamed these across versions, so match
# on substrings of the NAME and record which names actually matched, so a future rename
# shows up as "matched nothing" rather than as a silent zero.
_TERMINAL_HINTS = ("executed", "stored", "completed")
_PRE_HINTS = ("requested", "prioritized", "blocked", "executing", "watched")


def _classify(lists_seen: dict) -> dict:
    terminal = {k: v for k, v in lists_seen.items() if any(h in k.lower() for h in _TERMINAL_HINTS)}
    pre = {k: v for k, v in lists_seen.items() if any(h in k.lower() for h in _PRE_HINTS)}
    unmatched = {k: v for k, v in lists_seen.items() if k not in terminal and k not in pre}
    return {"terminal": terminal, "pre_execution": pre, "unclassified": unmatched}


def _verdict(res: dict) -> dict:
    if not res.get("armed"):
        return {"verdict": "BLOCKED", "why": "the watcher never armed -- nothing was measured"}

    # An empty terminal bucket is only evidence if the terminal lists were actually
    # there to be looked at. If the inventory does not show them, say so instead of
    # returning a confident RETIRED-BEFORE-EXECUTION off a zero that may be structural.
    inv = ((res.get("callbacks_list_inventory") or {}).get("lists") or {})
    if inv and not any(any(h in k.lower() for h in _TERMINAL_HINTS) for k in inv):
        return {
            "verdict": "BLOCKED",
            "why": (f"state.callbacks exposes {sorted(inv)} and NONE of them matches the terminal "
                    f"hints {list(_TERMINAL_HINTS)}. An empty terminal bucket here is a naming "
                    "mismatch, not a measurement. Extend the hints and re-run."),
        }

    seq = [x for x in (res.get("storeLenSeq") or []) if isinstance(x.get("to"), int)]
    applied = any(x["to"] > 0 for x in seq)
    buckets = res.get("buckets") or {}
    pre = buckets.get("pre_execution") or {}
    term = buckets.get("terminal") or {}
    unc = buckets.get("unclassified") or {}

    if applied:
        return {
            "verdict": "APPLIED",
            "why": (f"the store advanced to {[x['to'] for x in seq if x['to'] > 0][:6]} on this run. "
                    "A winning race, reported as such rather than folded into the losses."),
        }
    if not pre and not term and not unc:
        touch = res.get("touchHigh") or {}
        if touch:
            return {
                "verdict": "NEVER-SCHEDULED-AS-OUTPUT",
                "why": ("no callback with this store as an OUTPUT appeared in any state.callbacks "
                        f"list, while callbacks merely touching it were present throughout ({touch}). "
                        "The store is read everywhere and scheduled to be written nowhere -- the "
                        "writer is not entering the renderer's queue at all. The contrast rules out "
                        "a dead instrument: it was reading the lists fine."),
            }
        return {
            "verdict": "NEVER-REQUESTED",
            "why": ("no entry appeared in ANY state.callbacks list, not even one merely touching the "
                    "store. That contradicts the wire evidence (full payloads on "
                    "/_dash-update-component), so suspect this instrument -- a list rename would look "
                    "exactly like this."),
        }
    if pre and not term:
        entries = res.get("entries") or {}
        maxrun = res.get("maxRun") or {}
        # Where did it spend its life? The list with the most presence is the one whose
        # run structure decides between supersession and a stuck promise.
        seen = res.get("seen") or {}
        host = max(pre, key=lambda k: seen.get(k, 0)) if pre else None
        n_entries = entries.get(host, 0)
        run = maxrun.get(host, 0)
        base = (f"entries appeared in pre-execution lists {sorted(pre)} and NEVER in a terminal "
                f"list ({list(_TERMINAL_HINTS)}). The renderer drops the call before its result can "
                "be applied. ")
        if n_entries >= 5:
            return {
                "verdict": "RETIRED-BEFORE-EXECUTION",
                "why": (base + f"In {host!r} it entered {n_entries} SEPARATE times (longest unbroken "
                        f"presence {run} notifies), so this is a SERIES of calls each replaced before "
                        "resolving -- supersession, not one stuck request. That names the mechanism "
                        "the dispatch probe could only bound, and points the fix at the TRIGGER."),
            }
        if n_entries <= 2 and run > 50:
            return {
                "verdict": "STUCK-BEFORE-EXECUTION",
                "why": (base + f"But in {host!r} it entered only {n_entries} time(s) and stayed for "
                        f"{run} consecutive notifies. That is ONE call whose promise never resolves, "
                        "NOT supersession -- the retirement hypothesis does not fit, and the fix is a "
                        "different defect entirely."),
            }
        return {
            "verdict": "PRE-EXECUTION-INDETERMINATE",
            "why": (base + f"In {host!r} it entered {n_entries} time(s) with a longest run of {run} "
                    "notifies -- too few entries to call it supersession and too short to call it "
                    "stuck. Widen the window and re-run before naming a mechanism."),
        }
    if term:
        return {
            "verdict": "EXECUTED-NOT-APPLIED",
            "why": (f"entries DID reach terminal list(s) {sorted(term)} and the store still never "
                    "advanced. The discard is AFTER execution, so renderer retirement is NOT the "
                    "mechanism and the retirement hypothesis should be dropped."),
        }
    return {
        "verdict": "INDETERMINATE",
        "why": (f"entries appeared only in list(s) this classifier could not bucket: {sorted(unc)}. "
                "Read the samples and extend the hint lists before drawing anything from this run."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=float, default=60.0, help="seconds to observe")
    ap.add_argument("--tab", default="Candidate Metrics", help="tab to drive")
    ap.add_argument("--discover", action="store_true", help="dump the real state.callbacks shape and exit")
    ap.add_argument(
        "--store",
        default=METRICS_STORE,
        help=(
            "which store id to track. THE POSITIVE CONTROL LIVES HERE. Pointed at the subject "
            "(the default) this probe can only ever report an empty terminal bucket, and an empty "
            "bucket has two causes that look identical: the callback never got there, or this "
            "sampler cannot see that list at all. Pointing it at a store that demonstrably WORKS "
            "-- e.g. network-visualizer-topology-store, healthy since canopy#549 -- makes the "
            "instrument prove it can produce a non-empty terminal bucket. Without that run, "
            "RETIRED-BEFORE-EXECUTION is an uncontrolled zero."
        ),
    )
    args = ap.parse_args()
    target = args.store  # the tracked store id; METRICS_STORE is only its default

    from playwright.sync_api import sync_playwright

    res: dict = {"canopy": CANOPY, "store": target, "window_s": args.window}

    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, [])
        try:
            open_tab(page, args.tab)
            page.wait_for_timeout(5000)

            if args.discover:
                shape = page.evaluate(_DISCOVER)
                # The compact census FIRST. The full dump below is truncated to keep it
                # readable, and the truncation lands inside the biggest list's sample --
                # which is exactly the list (`stored`) whose reachability matters most.
                # A diagnostic whose most important line is cut off by its own pretty
                # printing is the shape of every other instrument failure in this arc.
                print("per-list output-shape reachability (does isOutput stand a chance?):")
                for name, info in sorted((shape.get("lists") or {}).items()):
                    sh = info.get("shapes")
                    if sh is None:
                        print(f"  {name:14s} len={info.get('len')}  <empty at sample time - no shape evidence>")
                    else:
                        print(f"  {name:14s} len={info.get('len'):<4} callback.outputs={sh['has_callback_outputs']}/"
                              f"{sh['entries']}  payload.outputs={sh['has_payload_outputs']}/{sh['entries']}  "
                              f"executionResult.outputs={sh['has_executionResult_outputs']}/{sh['entries']}  "
                              f"visible_output_ids={sh['total_output_ids_visible']}")
                print()
                print(json.dumps(shape, indent=2, default=str)[:6000])
                return 0

            page.evaluate(f"({_HOOK})({json.dumps(target)});")
            page.wait_for_timeout(int(args.window * 1000))

            # The list INVENTORY, recorded in the artifact itself. Without it, a future
            # reader cannot distinguish "the terminal lists existed and never held our
            # callback" from "the terminal lists were never iterated" -- the two produce
            # an identical empty bucket, and the second would make the verdict a
            # structural zero rather than a measurement.
            res["callbacks_list_inventory"] = page.evaluate(
                """() => {
                     const st = window.store && window.store.getState ? window.store.getState() : null;
                     const cb = st && st.callbacks ? st.callbacks : null;
                     if (!cb) return {ok:false};
                     const out = {ok:true, lists:{}};
                     for (const k of Object.keys(cb)) out.lists[k] = Array.isArray(cb[k]) ? cb[k].length : null;
                     return out;
                   }"""
            )

            snap = page.evaluate(
                """() => {
                     const R = window.__f035c || {};
                     return {armed: !!R.armed, seen: R.seen || {}, everSeen: R.everSeen || {},
                             touchHigh: R.touchHigh || {},
                             entries: R.entries || {}, maxRun: R.maxRun || {},
                             samples: R.samples || [], notifies: R.notifies || 0,
                             storeLenSeq: R.storeLenSeq || [], errors: R.errors || []};
                   }"""
            )
            res.update(snap)
            rd = _store(page, target) or {}
            res["independent_read"] = {
                "ok": rd.get("ok"),
                "len": len(rd["value"]) if isinstance(rd.get("value"), list) else None,
            }
        finally:
            browser.close()

    res["buckets"] = _classify(res.get("everSeen") or {})
    res["result"] = _verdict(res)

    log(f"  armed={res.get('armed')} notifies={res.get('notifies')} errors={len(res.get('errors') or [])}")
    log(f"  lists with {target} as an OUTPUT (high-water): {res.get('everSeen')}")
    log(f"  lists merely TOUCHING it -- contrast only, not the measurement: {res.get('touchHigh')}")
    log(f"  notifies present in each list: {res.get('seen')}")
    log(f"  DISTINCT ENTRIES per list (absent->present transitions): {res.get('entries')}")
    log(f"  longest unbroken presence (notifies): {res.get('maxRun')}")
    log(f"  state.callbacks inventory (proves which lists exist): {res.get('callbacks_list_inventory')}")
    log(f"  buckets: pre={sorted(res['buckets']['pre_execution'])} "
        f"terminal={sorted(res['buckets']['terminal'])} unclassified={sorted(res['buckets']['unclassified'])}")
    log(f"  store length sequence: {[(x.get('from'), x.get('to')) for x in res.get('storeLenSeq') or []][:8]}")
    log(f"  independent read: {res.get('independent_read')}")
    log(f"  => VERDICT: {res['result']['verdict']}")
    log(f"     {res['result']['why']}")

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
