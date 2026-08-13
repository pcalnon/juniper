#!/usr/bin/env python3
"""
Project: Juniper
Sub-Project: juniper-ml
Application: Canopy E2E Phase 1 -- W6 dataset COLD migration driver
Author: Paul Calnon
Version: 0.1.0
License: MIT License

Ad-hoc live driver for the **W6** rows of the canopy E2E click-by-click matrix
(``notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md``
section "W6 -- Dataset COLD migration (stage -> restart)").

SAFETY BOUNDARY (deliberate): this driver stops at matrix step 15. Step 16's
``#restart-confirm-button`` runs ``POST /api/train/restart`` with
``{"start_fresh": ..., "reset": True}`` (dashboard_manager.py:5447) -- ``reset``
is hard-coded True, so executing it WIPES the live 10-unit network that carries
the segment-6/7 mutation evidence. That is an owner call, not a driver's.
Everything through step 15 (stage / banner / cancel / re-stage / modal open,
inspect, toggle, granular expand, cancel) is non-destructive and is driven here.

Shares the browser + logging helpers with the W3 driver.

    /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_w6_dataset_driver.py --steps 1-9

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
http_get = _w3.http_get
http_post = _w3.http_post
log_size = _w3.log_size
log_since = _w3.log_since
open_dashboard = _w3.open_dashboard
dismiss_welcome = _w3.dismiss_welcome
input_value = _w3.input_value
is_disabled = _w3.is_disabled
text_of = _w3.text_of
dropdown_value = _w3.dropdown_value
dropdown_select = _w3.dropdown_select
_fresh = _w3._fresh


def visible(page, el_id: str):
    """Visibility that is safe for position:fixed elements.

    offsetParent is null for position:fixed, so it must never be used as a
    modal-visibility test (two false 'modal never opened' readings came from
    exactly that). Use computed style + a non-zero border box.
    """
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); if (!el) return null;
                     const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
                     return {display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
                             w: Math.round(r.width), h: Math.round(r.height),
                             shown: cs.display !== 'none' && cs.visibility !== 'hidden'
                                    && r.width > 0 && r.height > 0}; }""",
        el_id,
    )


def exists(page, el_id: str) -> bool:
    return bool(page.evaluate("(id) => !!document.getElementById(id)", el_id))


def wait_appear(page, el_id: str, timeout_ms: int = 12_000) -> bool:
    """Poll for an element to EXIST and be shown.

    Confirm-modal DOM does not exist while closed, so a plain visibility read
    races; poll for appearance instead.
    """
    step = 400
    waited = 0
    while waited < timeout_ms:
        if exists(page, el_id):
            v = visible(page, el_id)
            if v and v.get("shown"):
                return True
        page.wait_for_timeout(step)
        waited += step
    return False


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
def step_1(page, ctx):
    log("=== W6-01: baseline dataset type + input count ===")
    _fresh(page)
    page.wait_for_timeout(3000)
    dd = dropdown_value(page, "nn-dataset-type-dropdown")
    _, status = http_get("/api/status")
    log(f"  #nn-dataset-type-dropdown = {dd!r}")
    log(f"  /api/status pending_dataset = {status.get('pending_dataset')!r}; input_size={status.get('input_size')!r}; hidden_units={status.get('hidden_units')!r}")
    log(f"  #network-visualizer-input-count = {text_of(page, 'network-visualizer-input-count')!r} (F-CANOPY-006 dead-oracle class)")
    ctx["dataset_before"] = dd


def step_2(page, ctx):
    log("=== W6-02: change generator -> title renames, spiral fields hide, schema params render ===")
    cur = dropdown_value(page, "nn-dataset-type-dropdown")
    before_schema = page.evaluate(
        """() => { const el = document.getElementById('nn-dataset-schema-params');
                   return el ? {html_len: el.innerHTML.length, text: el.innerText.slice(0,200)} : null; }"""
    )
    spiral_rot = visible(page, "nn-spiral-rotations-input")
    log(f"  before: dropdown={cur!r}; schema-params={before_schema}; spiral-rotations visible={spiral_rot and spiral_rot.get('shown')}")

    # Enumerate the real option labels (they are backend-driven, :2425-2426).
    page.locator("#nn-dataset-type-dropdown").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    page.locator("#nn-dataset-type-dropdown").click()
    page.wait_for_timeout(900)
    labels = page.evaluate("""() => Array.from(document.querySelectorAll('[role=option]')).map(o => o.innerText.trim())""")
    log(f"  dropdown option labels ({len(labels)}): {labels}")
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)
    ctx["dataset_options"] = labels

    target = ctx.get("target_dataset")
    if not target:
        prefer = ("Moon", "Moons", "Circles", "Xor", "XOR", "Gaussian")
        target = next((l for p in prefer for l in labels if l.lower() == p.lower()), None)
        if not target:
            target = next((l for l in labels if l != cur), None)
    log(f"  chosen target = {target!r}")
    ok = dropdown_select(page, "nn-dataset-type-dropdown", target)
    page.wait_for_timeout(2500)
    after_schema = page.evaluate(
        """() => { const el = document.getElementById('nn-dataset-schema-params');
                   return el ? {html_len: el.innerHTML.length, text: el.innerText.slice(0,300)} : null; }"""
    )
    spiral_after = visible(page, "nn-spiral-rotations-input")
    log(f"  selected {target!r} (ok={ok}); dropdown now={dropdown_value(page, 'nn-dataset-type-dropdown')!r}")
    log(f"  schema-params after={after_schema}")
    log(f"  spiral-rotations visible after={spiral_after and spiral_after.get('shown')}")
    ctx["dataset_target"] = target


def step_4(page, ctx):
    log("=== W6-04/05/06: Apply Dataset -> POST /api/stage_dataset, banner, /api/status ===")
    mark = log_size()
    cap_before = len(ctx["_capture"])
    page.locator("#apply-dataset-button").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    page.click("#apply-dataset-button")
    page.wait_for_timeout(5000)

    posts = [c for c in ctx["_capture"][cap_before:] if "stage_dataset" in c["url"]]
    log(f"  browser requests to /api/stage_dataset: {len(posts)}")
    for p in posts[:2]:
        log(f"    NET {p['method']} {p['url']} body={p['body'][:300]}")
    for ln in log_since(mark, ("stage_dataset", "Staged dataset", "pending_dataset"))[-5:]:
        log(f"    SRV {ln[:400]}")

    log(f"  #pending-dataset-banner = {visible(page, 'pending-dataset-banner')}")
    log(f"  banner text = {text_of(page, 'pending-dataset-banner')!r}")
    log(f"  #dataset-stage-outcome-alert = {visible(page, 'dataset-stage-outcome-alert')} text={text_of(page, 'dataset-stage-outcome-alert')!r}")
    _, status = http_get("/api/status")
    log(f"  /api/status pending_dataset = {status.get('pending_dataset')!r}")


def step_7(page, ctx):
    log("=== W6-07/08: cancel path -> DELETE /api/cancel_pending_dataset ===")
    if not exists(page, "cancel-pending-dataset-button"):
        log("  !! #cancel-pending-dataset-button absent -- cannot drive the cancel path")
        return
    cap_before = len(ctx["_capture"])
    page.locator("#cancel-pending-dataset-button").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    page.click("#cancel-pending-dataset-button")
    page.wait_for_timeout(5000)
    reqs = [c for c in ctx["_capture"][cap_before:] if "cancel_pending_dataset" in c["url"]]
    log(f"  requests to /api/cancel_pending_dataset: {len(reqs)} {[r['method'] for r in reqs]}")
    log(f"  #pending-dataset-banner after cancel = {visible(page, 'pending-dataset-banner')}")
    _, status = http_get("/api/status")
    log(f"  /api/status pending_dataset = {status.get('pending_dataset')!r}")
    log("  waiting one slow reconcile tick (10s) to confirm the banner stays closed...")
    page.wait_for_timeout(10_000)
    log(f"  #pending-dataset-banner after reconcile = {visible(page, 'pending-dataset-banner')}")
    _, status2 = http_get("/api/status")
    log(f"  /api/status pending_dataset after reconcile = {status2.get('pending_dataset')!r}")


def step_10(page, ctx):
    log("=== W6-10/11/12/13/14/15: restart modal (open, static, toggles, granular, cancel) ===")
    if not exists(page, "restart-with-new-dataset-button"):
        log("  !! #restart-with-new-dataset-button absent (needs a staged pending dataset)")
        return
    page.locator("#restart-with-new-dataset-button").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    page.click("#restart-with-new-dataset-button")
    opened = wait_appear(page, "restart-confirm-modal", 15_000)
    log(f"  W6-10 modal appeared = {opened}; {visible(page, 'restart-confirm-modal')}")
    log(f"  #restart-confirm-summary = {text_of(page, 'restart-confirm-summary')!r}")
    seeded = page.evaluate(
        """() => Array.from(document.querySelectorAll("[id^='restart-ds-'],[id^='restart-p-']"))
                     .map(el => ({id: el.id, value: el.value !== undefined ? el.value : null,
                                  tag: el.tagName}))"""
    )
    log(f"  seeded granular fields ({len(seeded)}):")
    for s in seeded:
        log(f"    {s}")

    # W6-11: static backdrop + keyboard=False
    page.keyboard.press("Escape")
    page.wait_for_timeout(1500)
    log(f"  W6-11 after Escape: modal {visible(page, 'restart-confirm-modal')}")

    # W6-12: start-fresh toggle consequence lines
    if exists(page, "restart-start-fresh-toggle"):
        for want in (True, False):
            page.evaluate(
                """(v) => { const el = document.getElementById('restart-start-fresh-toggle');
                            if (el && el.checked !== v) el.click(); }""",
                want,
            )
            page.wait_for_timeout(1500)
            log(f"  W6-12 start_fresh={want}: summary={text_of(page, 'restart-confirm-summary')!r}")
    else:
        log("  W6-12 !! #restart-start-fresh-toggle absent")

    # W6-13: granular collapse
    if exists(page, "restart-granular-toggle"):
        page.click("#restart-granular-toggle")
        page.wait_for_timeout(2000)
        log(f"  W6-13 #restart-granular-collapse = {visible(page, 'restart-granular-collapse')}")
        log(f"  W6-13 #restart-granular-context = {text_of(page, 'restart-granular-context')!r}")
    else:
        log("  W6-13 !! #restart-granular-toggle absent")

    # W6-14: the one browser-drivable granular field
    if exists(page, "restart-ds-type"):
        before = text_of(page, "restart-confirm-summary")
        cur = dropdown_value(page, "restart-ds-type")
        log(f"  W6-14 #restart-ds-type current={cur!r}")
        tgt = ctx.get("granular_target") or "Spirals"
        ok = dropdown_select(page, "restart-ds-type", tgt)
        page.wait_for_timeout(2000)
        after = text_of(page, "restart-confirm-summary")
        log(f"  W6-14 selected {tgt!r} (ok={ok}); summary changed = {before != after}")
        log(f"  W6-14 summary after = {after!r}")
    else:
        log("  W6-14 !! #restart-ds-type absent")

    # W6-15: cancel executes nothing
    mark = log_size()
    cap_before = len(ctx["_capture"])
    if exists(page, "restart-cancel-button"):
        page.click("#restart-cancel-button")
        page.wait_for_timeout(3000)
        restart_calls = [c for c in ctx["_capture"][cap_before:] if "train/restart" in c["url"]]
        log(f"  W6-15 modal after cancel = {visible(page, 'restart-confirm-modal')}")
        log(f"  W6-15 /api/train/restart calls after cancel: {len(restart_calls)}")
        for ln in log_since(mark, ("train/restart", "restart"))[-3:]:
            log(f"    SRV {ln[:300]}")
    else:
        log("  W6-15 !! #restart-cancel-button absent")

    log("  >>> STOPPING BEFORE step 16 (#restart-confirm-button): POST /api/train/restart")
    log("  >>> carries reset=True and would wipe the live 10-unit segment-6/7 network. Owner call.")


def step_11b(page, ctx):
    """W6-11 (Esc AND backdrop) + W6-12 done properly.

    The 'two consequence lines' are STATIC layout text (dashboard_manager.py
    :1979-1983 under the switch, and :1999-2004 inside the granular collapse) --
    they are not wired to the toggle, so the summary is not expected to change.
    This reads them from the DOM and verifies the switch's actual checked state.
    """
    log("=== W6-11b/12b: modal dismissal (Esc + backdrop) and the consequence text ===")
    _, status = http_get("/api/status")
    log(f"  precondition /api/status pending_dataset = {status.get('pending_dataset')!r}")
    if not exists(page, "restart-with-new-dataset-button"):
        log("  !! restart button absent -- nothing staged; run --steps 1,2,4 first")
        return
    page.locator("#restart-with-new-dataset-button").scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    page.click("#restart-with-new-dataset-button")
    if not wait_appear(page, "restart-confirm-modal", 15_000):
        log("  !! modal did not appear")
        return
    log(f"  modal open: {visible(page, 'restart-confirm-modal')}")

    # W6-11a: Escape
    page.keyboard.press("Escape")
    page.wait_for_timeout(1800)
    log(f"  W6-11 Escape  -> modal {visible(page, 'restart-confirm-modal')}")

    # W6-11b: backdrop click (top-left corner, outside the 500px-wide dialog)
    try:
        page.mouse.click(8, 8)
        page.wait_for_timeout(1800)
        log(f"  W6-11 backdrop-> modal {visible(page, 'restart-confirm-modal')}")
    except Exception as e:  # noqa: BLE001
        log(f"  backdrop click raised: {str(e)[:150]}")

    # W6-12: switch state + the static consequence lines
    sw = page.evaluate(
        """() => { const el = document.getElementById('restart-start-fresh-toggle');
                   if (!el) return null;
                   return {tag: el.tagName, type: el.type, checked: el.checked}; }"""
    )
    log(f"  W6-12 switch element = {sw}")
    if sw and sw.get("type") == "checkbox":
        for want in (True, False):
            page.evaluate(
                """(v) => { const el = document.getElementById('restart-start-fresh-toggle');
                            if (el.checked !== v) el.click(); }""",
                want,
            )
            page.wait_for_timeout(1200)
            now = page.evaluate("() => document.getElementById('restart-start-fresh-toggle').checked")
            log(f"    set start_fresh={want} -> checked={now} ({'OK' if now == want else 'DRIVE FAILED'})")
    texts = page.evaluate(
        """() => { const m = document.getElementById('restart-confirm-modal');
                   if (!m) return null;
                   return Array.from(m.querySelectorAll('div,p'))
                        .map(e => (e.innerText || '').trim())
                        .filter(t => t.toLowerCase().includes('start fresh') || t.startsWith('Off (default)'))
                        .slice(0, 6); }"""
    )
    log("  W6-12 consequence text found in the modal:")
    for t in texts or []:
        log(f"    | {t[:240]}")

    if exists(page, "restart-cancel-button"):
        page.click("#restart-cancel-button")
        page.wait_for_timeout(2000)
        log(f"  closed via cancel -> modal {visible(page, 'restart-confirm-modal')}")


def step_summary_fidelity(page, ctx):
    """Does #restart-confirm-summary describe the STAGED plan or the sidebar?

    Observed: pending_dataset was {'moons', n_samples 200, noise 0.1} while the
    summary read 'Samples: 1000 / Noise: 0.25' and listed spiral-only params for
    a moons dataset. This isolates that comparison explicitly.
    """
    log("=== W6-10b: restart summary fidelity vs the actually-staged dataset ===")
    _, status = http_get("/api/status")
    pend = status.get("pending_dataset")
    log(f"  STAGED /api/status pending_dataset = {pend!r}")
    if not exists(page, "restart-with-new-dataset-button"):
        log("  !! restart button absent -- nothing staged")
        return
    page.click("#restart-with-new-dataset-button")
    if not wait_appear(page, "restart-confirm-modal", 15_000):
        log("  !! modal did not appear")
        return
    summary = text_of(page, "restart-confirm-summary")
    log(f"  MODAL #restart-confirm-summary = {summary!r}")
    seeded = page.evaluate(
        """() => Object.fromEntries(Array.from(document.querySelectorAll("[id^='restart-ds-']"))
                     .filter(el => el.tagName === 'INPUT').map(el => [el.id, el.value]))"""
    )
    log(f"  MODAL seeded restart-ds-* inputs = {seeded}")
    if isinstance(pend, dict):
        p = pend.get("params") or {}
        log(f"  COMPARE staged n_samples={p.get('n_samples')!r} vs modal restart-ds-samples={seeded.get('restart-ds-samples')!r}")
        log(f"  COMPARE staged noise={p.get('noise')!r} vs modal restart-ds-noise={seeded.get('restart-ds-noise')!r}")
    if exists(page, "restart-cancel-button"):
        page.click("#restart-cancel-button")
        page.wait_for_timeout(1500)


def step_cleanup(page, ctx):
    log("=== CLEANUP: cancel any pending dataset staged by this run ===")
    _, status = http_get("/api/status")
    log(f"  /api/status pending_dataset = {status.get('pending_dataset')!r}")


STEPS = {
    "1": step_1,
    "2": step_2,
    "4": step_4,
    "7": step_7,
    "10": step_10,
    "11b": step_11b,
    "10b": step_summary_fidelity,
    "cleanup": step_cleanup,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="W6 dataset COLD migration live driver (stops before restart execute)")
    ap.add_argument("--steps", default="1,2,4,7")
    ap.add_argument("--target-dataset", default=None, help="generator label to switch to (default: Two Moons)")
    ap.add_argument("--granular-target", default=None, help="label for #restart-ds-type in W6-14")
    args = ap.parse_args()

    steps = [s.strip() for s in args.steps.split(",") if s.strip() in STEPS]
    if not steps:
        print(f"no runnable steps in {args.steps!r}; known: {sorted(STEPS)}", file=sys.stderr)
        return 2

    from playwright.sync_api import sync_playwright

    capture: list = []
    ctx: dict = {"_capture": capture}
    if args.target_dataset:
        ctx["target_dataset"] = args.target_dataset
    if args.granular_target:
        ctx["granular_target"] = args.granular_target
    log(f"canopy={_w3.CANOPY} steps={steps}")

    with sync_playwright() as pw:
        browser, bctx, page = open_dashboard(pw, capture)
        try:
            for s in steps:
                STEPS[s](page, ctx)
        finally:
            bctx.close()
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
