#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: F-CANOPY-039 item 3 -- test at RUNTIME whether a store id is declared
#          more than once, and if so whether its instances hold DIFFERENT values.
#
# WHY THIS CANNOT BE A DOM CHECK OR A STATIC CHECK, both of which already passed:
#
#   * `dcc.Store` renders NO DOM. The live element count and
#     `e2e_f039_dom_apply_probe.py` (which measured
#     `n_elements_with_graph_id = 1`, attached) are blind to it by construction.
#   * The static layout check `e2e_f027_dup_ids.py` came back 464 ids / 464
#     distinct -- but it reads the DECLARED layout. A store created during the
#     A1-iii-b1 tab rebuild is not in it.
#   * `paths.strs` is keyed by the id STRING, so a duplicated id has exactly ONE
#     entry: the registration that won. Asking `paths` "is this id duplicated"
#     always answers no. That is precisely F-CANOPY-027's recorded trap --
#     "if a store is declared twice, Dash writes one instance and the consumers
#     read the other" -- and it is why this walks the layout TREE instead.
#
# WHAT IT MEASURES, per target id:
#     occurrences   how many nodes in the live layout tree carry that id
#     distinct_data how many DIFFERENT values those nodes hold
#     winner_path   what `paths.strs[id]` resolves to (the instance Dash writes)
#     value at each occurrence, summarised by length + hash
#
#   occurrences > 1 with distinct_data > 1 is the finding: one id, two values,
#   which is what both stores' server-side probes implied from opposite ends
#   (topology: the writer sees a correct value while the reader renders empty;
#   metrics: the writer's own next read comes back empty).
#
#   occurrences == 1 REFUTES the duplicate-instance hypothesis for that id and
#   sends the investigation back to how the single instance is updated.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#     util/ad-hoc/e2e_f039_duplicate_store_probe.py --settle 25
#
# Exit: 0 probe ran and reported, 1 the probe could not run (NOT a verdict).

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")

log = _w3.log
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab

TARGETS = [
    "network-visualizer-topology-store",
    "metrics-panel-metrics-store",
    # Controls. The first is the store F-CANOPY-038 names as the OTHER writer's
    # trigger; the last two are ordinary stores with no reported anomaly, so if
    # every id in the app reports occurrences>1 the probe is measuring itself.
    "ws-metrics-buffer",
    "metrics-panel-display-mode-store",
    "ws-liveness-store",
]

PROBE = """
(targets) => {
  const store = (window.store && window.store.dispatch) ? window.store
              : (window.dash_stores && window.dash_stores[0]) || null;
  if (!store) return {error: 'redux store not on window'};
  const st = store.getState();
  if (!st || st.layout === undefined) return {error: 'no layout in redux state'};

  const want = new Set(targets);
  const hits = {};
  for (const t of targets) hits[t] = [];

  // Cheap stable digest -- enough to say "same value or not" without shipping
  // 155 KB per occurrence back across the bridge.
  const digest = (v) => {
    let s;
    try { s = JSON.stringify(v); } catch (e) { return {len: -1, hash: 'unserialisable'}; }
    if (s === undefined) return {len: -1, hash: 'undefined'};
    let h = 5381;
    for (let i = 0; i < s.length; i++) { h = ((h * 33) ^ s.charCodeAt(i)) >>> 0; }
    return {len: s.length, hash: h.toString(16), head: s.slice(0, 60)};
  };

  let visited = 0;
  const LIMIT = 400000;
  const seen = new WeakSet();

  const walk = (node, path) => {
    if (visited++ > LIMIT || node === null || typeof node !== 'object') return;
    if (seen.has(node)) return;
    seen.add(node);

    if (Array.isArray(node)) {
      for (let i = 0; i < node.length; i++) walk(node[i], path + '.' + i);
      return;
    }
    const props = node.props;
    if (props && typeof props === 'object') {
      const id = props.id;
      if (typeof id === 'string' && want.has(id)) {
        hits[id].push({
          path: path,
          type: node.type || null,
          namespace: node.namespace || null,
          data: digest(props.data),
        });
      }
      for (const k of Object.keys(props)) {
        // `figure` and a Store's own `data` are the big ones; never recurse into
        // them -- they hold no components and would blow the visit budget.
        if (k === 'figure' || k === 'data') continue;
        const v = props[k];
        if (v && typeof v === 'object') walk(v, path + '.props.' + k);
      }
    } else {
      for (const k of Object.keys(node)) {
        const v = node[k];
        if (v && typeof v === 'object') walk(v, path + '.' + k);
      }
    }
  };

  walk(st.layout, 'layout');

  // What `paths` believes -- the single instance Dash resolves writes to.
  const p = st.paths;
  const strmap = (p && (p.strs || p)) || {};
  const winners = {};
  for (const t of targets) winners[t] = strmap[t] ? JSON.stringify(strmap[t]) : null;

  const summary = {};
  for (const t of targets) {
    const occ = hits[t];
    const distinct = new Set(occ.map((o) => o.data.hash));
    summary[t] = {
      occurrences: occ.length,
      distinct_data: distinct.size,
      winner_path: winners[t],
      instances: occ,
    };
  }
  return {visited: visited, truncated: visited > LIMIT, summary: summary};
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settle", type=int, default=25, help="seconds to let each tab settle before probing")
    ap.add_argument("--out", default=None, help="write the full JSON result here")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    results = {}
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        try:
            # Probe on each tab that owns one of the suspect stores, because the
            # duplicate is hypothesised to be CREATED by the tab rebuild -- so a
            # single-tab reading could miss it.
            for tab in ("Network Topology", "Training Metrics", "Candidate Metrics"):
                if not open_tab(page, tab):
                    log(f"  could not open tab {tab!r} — skipping")
                    continue
                page.wait_for_timeout(args.settle * 1000)
                res = page.evaluate(PROBE, TARGETS)
                if res.get("error"):
                    log(f"[{tab}] PROBE ERROR: {res['error']} — this is NOT a verdict")
                    continue
                results[tab] = res
                log(f"[{tab}] visited={res['visited']} truncated={res['truncated']}")
                for tid, s in res["summary"].items():
                    flag = ""
                    if s["occurrences"] > 1:
                        flag = "  <== DUPLICATE" + (" WITH DIVERGENT VALUES" if s["distinct_data"] > 1 else " (same value)")
                    elif s["occurrences"] == 0:
                        flag = "  (absent on this tab)"
                    log(f"    {tid}: occurrences={s['occurrences']} distinct_data={s['distinct_data']}{flag}")
                    for inst in s["instances"]:
                        log(f"        {inst['type']} len={inst['data']['len']} hash={inst['data']['hash']} at {inst['path'][:110]}")
                    log(f"        paths.strs winner: {s['winner_path']}")
        finally:
            browser.close()

    if not results:
        log("NO RESULTS — the probe never ran successfully. This is an instrument failure, not a finding.")
        return 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, sort_keys=True)
        log(f"full result -> {args.out}")

    log("")
    log("VERDICT per store id (across all tabs probed):")
    for tid in TARGETS:
        occ = {t: r["summary"][tid]["occurrences"] for t, r in results.items()}
        div = {t: r["summary"][tid]["distinct_data"] for t, r in results.items()}
        worst = max(occ.values()) if occ else 0
        if worst > 1:
            log(f"  {tid}: DUPLICATED — occurrences {occ}, distinct values {div}")
        elif worst == 1:
            log(f"  {tid}: single instance everywhere {occ} — duplicate-instance hypothesis REFUTED for this id")
        else:
            log(f"  {tid}: never present in any probed layout {occ} — check the id spelling before concluding")
    return 0


if __name__ == "__main__":
    sys.exit(main())
