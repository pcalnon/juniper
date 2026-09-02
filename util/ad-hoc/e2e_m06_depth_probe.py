#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Canopy E2E arc -- M-TOPOLOGY-16/06 depth-filter diagnosis (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Decide whether M-TOPOLOGY-06 is a HARNESS limit or a PRODUCT defect,
#          which the row's own verdict cannot distinguish.
#
#          After the driver was taught to settle (the fix that made
#          M-TOPOLOGY-01 pass), M-TOPOLOGY-06 STILL fails: set_slider moves the
#          widget to 20 -- verified in the DOM, now=0 -> now=20 -- yet the depth
#          label stays "0 of 40" and the stats bar stays 40.
#
#          The trap: set_slider verifies by re-reading the DOM
#          (``aria-valuenow`` / ``input.value``). That proves the WIDGET shows 20.
#          It does NOT prove Dash's callback received 20 -- and those two come
#          apart exactly in the Dash-3 controlled-input case this arc has already
#          been bitten by ("keystrokes don't land").
#
#          The discriminator is the FIGURE, because ``-depth-slider.value`` is a
#          real Input of ``update_network_graph``:
#
#            figure CHANGES  -> Dash received the depth. The filter ran; a stale
#                               label / stats bar is then a PRODUCT defect in
#                               whatever feeds them.
#            figure UNCHANGED-> Dash never received it. The DOM moved and the
#                               state did not: a HARNESS limit, and the row is
#                               undriveable until the widget is driven another way.
#
# Usage:
#   LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
#       util/ad-hoc/e2e_m06_depth_probe.py
#
# Exit codes: 0 probe ran (read the verdict), 2 the page or control was unreachable.

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
NV = "network-visualizer"


def drag_only(page, container_id: str, target: int, thumb_index: int = 0) -> dict:
    """Drag the thumb with Playwright's REAL mouse, and nothing else.

    This exists because the sequenced ``set_slider`` cannot test the drag honestly.
    Its idioms run in order, so by the time the drag runs the number-input setter
    has ALREADY moved the DOM to the target — the drag then computes a destination
    the thumb already occupies, and mousedown/mouseup land on the same point. That
    is a no-op gesture, and reading "no effect" from it says nothing about whether
    a real drag works. (Measured: exactly that, and it briefly looked like evidence
    of a dead control.)

    It matters because the slider is ``updatemode="mouseup"``: Dash is notified ONLY
    on a mouseup that concludes a real drag. Synthetic value-setting and keyboard
    arrows cannot satisfy that by design, so their failure is expected and benign.
    A genuine drag is the only idiom that SHOULD work, and therefore the only one
    whose failure would implicate the product.

    Requires the slider to start away from ``target`` — the caller must not have
    moved it first.
    """
    st = _seg17.slider_state(page, container_id, thumb_index)
    lo, hi = (st or {}).get("min"), (st or {}).get("max")
    if st is None or lo is None or hi is None or hi <= lo:
        return {"error": f"slider unusable for a drag test: {st}"}
    if st.get("now") == target:
        return {"error": f"slider already AT {target} before the drag — the test would be a no-op gesture"}

    frac = (target - lo) / float(hi - lo)
    box = page.evaluate(
        """(id) => { const r = document.querySelector('#' + id + ' .dash-slider-track');
             if (!r) return null; const bb = r.getBoundingClientRect();
             return {x: bb.x, y: bb.y, w: bb.width, h: bb.height}; }""",
        container_id,
    )
    thumb = page.locator(f"#{container_id} [role=slider]")
    if not box or box["w"] <= 0 or thumb.count() <= thumb_index:
        return {"error": f"no track/thumb to drag (box={box})"}
    hb = thumb.nth(thumb_index).bounding_box()
    if not hb:
        return {"error": "thumb has no bounding box"}

    cy = hb["y"] + hb["height"] / 2
    x0 = hb["x"] + hb["width"] / 2
    x1 = box["x"] + box["w"] * frac
    log(f"  DRAG-ONLY from x={x0:.1f} to x={x1:.1f} (frac={frac:.3f}) on y={cy:.1f}")
    page.mouse.move(x0, cy)
    page.mouse.down()
    # Several intermediate moves: a single jump can be treated as a click rather
    # than a drag by some widgets.
    page.mouse.move(x1, cy, steps=25)
    page.wait_for_timeout(250)
    page.mouse.up()
    page.wait_for_timeout(1200)
    return {"from_x": x0, "to_x": x1, "after": _seg17.slider_state(page, container_id, thumb_index)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--depth", type=int, default=20)
    ap.add_argument("--drag-only", action="store_true", help="drag with the real mouse and NOTHING else (updatemode='mouseup' means this is the only idiom that should work)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = _w3.open_dashboard(pw, capture)
        _f027.ensure_no_modal(page)
        if not _f027.open_tab(page, "Network Topology"):
            log("could not open the Network Topology tab")
            browser.close()
            return 2
        # WAIT FOR PAINT BEFORE MEASURING. settle_figure alone is not enough: an
        # unpainted graph is stably empty, so it reports settled while the page has
        # no topology yet. A first run of this probe did exactly that and concluded
        # "the widget could not move" when the slider simply had max=0 because the
        # store had not loaded.
        _seg17.wait_for(
            lambda: len(((_seg17.fig_info(page, f"{NV}-graph") or {}).get("traces")) or []) > 0,
            budget_s=180,
            every_s=3.0,
            label="topology graph to paint",
        )
        st0 = _seg17.settle_figure(page, budget_s=30)
        if not st0.get("painted"):
            log("graph never painted; the stack has no topology to filter — not a drive result")
            browser.close()
            return 2

        before_fig = _seg17.fig_info(page, f"{NV}-graph") or {}
        before = {
            "slider": _seg17.slider_state(page, f"{NV}-depth-slider"),
            "label": _seg17.text_of(page, f"{NV}-depth-label"),
            "counts": _seg17.counts(page),
            "fig_hash": before_fig.get("fig_hash"),
            "traces": len(before_fig.get("traces") or []),
        }
        log(f"  BEFORE slider={before['slider']} label={before['label']!r} counts={before['counts']} hash={before['fig_hash']} traces={before['traces']}")

        # Demand the DOWNSTREAM effect so every idiom is actually tried. Without
        # this, the number-input idiom "succeeds" on a DOM-only move and set_slider
        # returns before keyboard or drag are attempted — so the probe would only
        # ever be testing idiom 1 and would report "Dash never received it" without
        # having tried the two idioms that might have delivered it.
        base_hash = before["fig_hash"]

        if args.drag_only:
            sl = drag_only(page, f"{NV}-depth-slider", args.depth)
            log(f"  drag_only -> {json.dumps({k: v for k, v in sl.items() if k != 'after'})}")
            if sl.get("error"):
                log("  the drag test could not run cleanly; its result would not be interpretable")
                browser.close()
                return 2
        else:
            def _landed():
                s = _seg17.settle_figure(page, budget_s=12)
                return bool(s.get("painted")) and s.get("fig_hash") not in (None, base_hash)

            sl = _seg17.set_slider(page, f"{NV}-depth-slider", args.depth, effect=_landed)
            log(f"  set_slider -> idiom={sl.get('idiom')} dom_only={sl.get('dom_only')} error={sl.get('error')}")
        st = _seg17.settle_figure(page, budget_s=30)

        after_fig = _seg17.fig_info(page, f"{NV}-graph") or {}
        after = {
            "slider": _seg17.slider_state(page, f"{NV}-depth-slider"),
            "label": _seg17.text_of(page, f"{NV}-depth-label"),
            "counts": _seg17.counts(page),
            "fig_hash": after_fig.get("fig_hash"),
            "traces": len(after_fig.get("traces") or []),
        }
        log(f"  AFTER  slider={after['slider']} label={after['label']!r} counts={after['counts']} hash={after['fig_hash']} traces={after['traces']} settled={st.get('settled_s')}s")

        dom_moved = (after["slider"] or {}).get("now") == args.depth
        fig_moved = after["fig_hash"] is not None and after["fig_hash"] != before["fig_hash"]
        label_moved = after["label"] != before["label"]
        counts_moved = after["counts"] != before["counts"]

        log("")
        log(f"  DOM widget moved to {args.depth}: {dom_moved}")
        log(f"  FIGURE changed              : {fig_moved}   ({before['fig_hash']} -> {after['fig_hash']}, traces {before['traces']} -> {after['traces']})")
        log(f"  depth LABEL changed         : {label_moved} ({before['label']!r} -> {after['label']!r})")
        log(f"  stats-bar COUNTS changed    : {counts_moved}")
        log("")

        if not dom_moved:
            verdict = "HARNESS: set_slider could not even move the widget in the DOM."
        elif not fig_moved:
            # WHICH idioms were tried decides this, and an earlier version of this
            # branch did not ask. "DOM moved, no effect" is only a HARNESS verdict
            # while the failing idioms are SYNTHETIC (a JS setter, dispatched
            # events). Idiom 3 drags with Playwright's real mouse, which emits
            # TRUSTED events — the same thing a human hand produces. If that also
            # fails to reach Dash, a real user's drag would do nothing either, and
            # calling it "harness" would file a live dead control as a test-rig quirk.
            tried_trusted = args.drag_only or sl.get("dom_only") is True
            if tried_trusted:
                verdict = (
                    "PRODUCT-SUSPECT: every idiom moved the widget and NONE reached Dash — including a real "
                    "mouse drag (trusted events). A user dragging this slider would see the thumb move and "
                    "nothing happen. Do NOT file this as a harness limit; the remaining innocent explanation "
                    "is that dcc.Slider defers setProps in a way this page never commits (e.g. no mouseup on "
                    "the thumb, or an updatemode the drag does not satisfy) — check the component's "
                    "updatemode and whether ANY interaction path updates it before concluding."
                )
            else:
                verdict = (
                    "HARNESS (provisional): the DOM moved but Dash never received the value, and only "
                    "SYNTHETIC idioms were tried. Re-run demanding the downstream effect so the trusted-event "
                    "drag is exercised before classifying this."
                )
        elif not (label_moved or counts_moved):
            verdict = (
                "PRODUCT: Dash DID receive the depth (the figure changed), but the depth label and the "
                "stats bar did not follow. The filter runs and its readouts are stale — a real defect in "
                "whatever feeds them, and the row's expectation is right to fail."
            )
        else:
            verdict = "PASS-SHAPED: the figure and at least one readout both moved; re-read the row's exact expectation."
        log("VERDICT: " + verdict)

        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump({"before": before, "after": after, "set_slider": sl, "verdict": verdict}, fh, indent=2, default=str)
            log(f"  -> {args.out}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
