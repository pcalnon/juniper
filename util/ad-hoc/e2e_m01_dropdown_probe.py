#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Canopy E2E arc -- M-TOPOLOGY-01 harness diagnosis (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Say exactly WHY ``set_dropdown`` fails on one layout option, and
#          exactly how much the ``sig`` length-proxy under-counts.
#
#          M-TOPOLOGY-01 fails with driven=3/4 every run. The product is fine —
#          all four layouts produce distinct coordinates when
#          ``_calculate_layout`` is called directly. Two harness causes were
#          inferred and this probe measures both rather than reasoning about them:
#
#            1. which option ``set_dropdown`` cannot commit, and whether it is a
#               "not found in the portal" failure or a "clicked but did not
#               commit" failure — the two need different fixes;
#            2. whether distinct layouts really do collide under
#               ``sig = JSON.stringify(gd.data).length``, by recording BOTH that
#               length and a content hash for each layout.
#
#          The content hash is what tells us the collision is a proxy artifact
#          rather than an unchanged figure. Equal length + different hash =
#          collision. Equal length + equal hash = the layout genuinely did not
#          change, which would be a PRODUCT defect and a different report.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_m01_dropdown_probe.py
#
# Exit codes: 0 probe ran (read the table), 2 the page or control was unreachable.

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")
_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")

log = _w3.log
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal

NV = "network-visualizer"
LAYOUTS = ["Hierarchical", "Staggered", "Spring", "Circular"]

# Content hash alongside the length proxy. Cheap FNV-1a over the serialised
# figure -- the point is only to distinguish "same bytes" from "same byte COUNT".
FIG_HASH = """(id) => {
  const root = document.getElementById(id);
  if (!root) return null;
  const gd = (root.classList && root.classList.contains('js-plotly-plot'))
               ? root : root.querySelector('.js-plotly-plot');
  if (!gd || !gd.data) return null;
  let s;
  try { s = JSON.stringify(gd.data); } catch (e) { return null; }
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  return {len: s.length, hash: h.toString(16)};
}"""

OPTIONS_IN_PORTAL = """() => {
  const sel = '[role=option], .dash-dropdown-option, [class*=dropdown-option], [role=menuitem]';
  return [...document.querySelectorAll(sel)].map(o => ({
    text: (o.textContent || '').trim(),
    disabled: o.getAttribute('aria-disabled') === 'true' || o.hasAttribute('disabled'),
    cls: (o.className || '').toString().slice(0, 60),
  }));
}"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        ensure_no_modal(page)
        if not open_tab(page, "Network Topology"):
            log("could not open the Network Topology tab")
            browser.close()
            return 2
        page.wait_for_timeout(4000)

        rows = []
        for name in LAYOUTS:
            before = _seg17.dropdown_value(page, f"{NV}-layout-selector")
            page.evaluate("""(id) => { const b = document.getElementById(id); if (b) b.click(); }""", f"{NV}-layout-selector")
            page.wait_for_timeout(700)
            portal = page.evaluate(OPTIONS_IN_PORTAL)
            found = [o for o in portal if o["text"] == name]
            clicked = page.evaluate(
                """([id, label]) => {
                     const sel = '[role=option], .dash-dropdown-option, [class*=dropdown-option], [role=menuitem]';
                     const hit = [...document.querySelectorAll(sel)].find(o => (o.textContent || '').trim() === label);
                     if (!hit) return false;
                     hit.click(); return true; }""",
                [f"{NV}-layout-selector", name],
            )
            page.wait_for_timeout(1500)
            after = _seg17.dropdown_value(page, f"{NV}-layout-selector")

            # SETTLE before reading, do not sample once. The rebuild takes 1.5-5 s
            # and both this probe (1500 ms) and set_dropdown (1200 ms) used to read
            # inside that window — so an "identical figure" reading was really a
            # read-too-early. Poll until the hash holds steady across consecutive
            # samples, with a budget well past the slowest observed rebuild.
            fig, stable_for, waited = None, 0, 0
            prev_hash = None
            while waited < 20000 and stable_for < 3:
                page.wait_for_timeout(1000)
                waited += 1000
                fig = page.evaluate(FIG_HASH, f"{NV}-graph")
                h = (fig or {}).get("hash")
                stable_for = stable_for + 1 if h == prev_hash else 0
                prev_hash = h

            if not found:
                why = "OPTION-ABSENT-FROM-PORTAL"
            elif not clicked:
                why = "FOUND-BUT-CLICK-FAILED"
            elif after != name:
                why = f"CLICKED-BUT-DID-NOT-COMMIT (value stayed {after!r})"
            else:
                why = "ok"

            rows.append({
                "layout": name, "before": before, "after": after, "committed": after == name,
                "why": why, "n_options_in_portal": len(portal),
                "portal_texts": [o["text"] for o in portal][:8],
                "len": (fig or {}).get("len"), "hash": (fig or {}).get("hash"),
            })
            log(f"  {name:<13} committed={after == name!s:<5} why={why} len={(fig or {}).get('len')} hash={(fig or {}).get('hash')} settled_after={waited}ms")
            if after != name:
                log(f"      portal had {len(portal)} option(s): {[o['text'] for o in portal][:8]}")

        log("")
        # Only COMMITTED layouts can be compared. An uncommitted one never changed
        # the selection, so its figure is the previous layout's and would read as a
        # false duplicate — which is exactly what the first version of this verdict
        # reported for Staggered, and it would have been published as a product
        # defect. A verdict must exclude the samples it did not actually take.
        comparable = [r for r in rows if r["committed"]]
        skipped = [r["layout"] for r in rows if not r["committed"]]
        if skipped:
            log(f"excluded from the comparison (never committed): {skipped}")

        lens = {}
        hashes = {}
        for r in comparable:
            lens.setdefault(r["len"], []).append(r["layout"])
            hashes.setdefault(r["hash"], []).append(r["layout"])
        collisions = {k: v for k, v in lens.items() if len(v) > 1}
        true_dupes = {k: v for k, v in hashes.items() if len(v) > 1}
        log(f"distinct by LENGTH (current sig): {len(lens)} of {len(comparable)} committed")
        log(f"distinct by CONTENT HASH        : {len(hashes)} of {len(comparable)} committed")
        if collisions and not true_dupes:
            log("VERDICT: the sig length-proxy COLLIDES — " + json.dumps(collisions))
            log("  Different figures share a byte COUNT. distinct_sigs under-counts; use a content hash.")
        elif true_dupes:
            log("VERDICT: figures are genuinely IDENTICAL for " + json.dumps(true_dupes))
            log("  That is a PRODUCT defect (a layout that does not change the figure), not a proxy artifact.")
        else:
            log("VERDICT: no collision this run — all four layouts differ by both length and hash.")

        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump({"rows": rows, "length_collisions": collisions, "content_duplicates": true_dupes}, fh, indent=2)
            log(f"  -> {args.out}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
