#!/usr/bin/env python3
"""Segment-13 driver: §2.10 global modals/alerts + the §2.9 tail.

Project:     Juniper
Sub-Project: juniper-ml
Application: Canopy E2E validation arc -- Phase 1 segment 13
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Why this exists
---------------
The browser MCP was unavailable this session (it has been intermittent across
the arc -- present in segments 9/12, absent in 8 and here), so driving falls
back to a script under ``util/ad-hoc/`` run with the only interpreter that has
playwright installed::

    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/e2e_seg13_modals_driver.py --step survey

``LD_LIBRARY_PATH=`` is mandatory: invoking the env's python directly bypasses
the conda hooks that strip it, and an ambient rust_mudgeon libtorch then breaks
module import with ``undefined symbol: _PyObject_NextNotImplemented`` -- which
reads exactly like a test failure and is not one.

Shared browser/log helpers come from ``e2e_w3_params_driver.py`` (the arc's
convention since segment 8), loaded by path so this file needs no package.

Steps are survey-first on purpose: §2.10's first six rows live in a table with
no ``mode`` column and describe *declared surfaces*, so the honest first move is
to read what is actually in the DOM before asserting anything about it.
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


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def probe(page, el_id: str):
    """Existence + computed geometry for one id.

    ``offsetParent`` is deliberately NOT used -- it is null for position:fixed
    elements, which is most of §2.10, and two false 'never opened' readings in
    segment 7 came from exactly that.
    """
    return page.evaluate(
        """(id) => {
             const el = document.getElementById(id);
             if (!el) return {present: false};
             const cs = getComputedStyle(el);
             const r = el.getBoundingClientRect();
             return {present: true, tag: el.tagName, cls: el.className,
                     display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
                     top: cs.top, zIndex: cs.zIndex,
                     w: Math.round(r.width), h: Math.round(r.height),
                     shown: cs.display !== 'none' && cs.visibility !== 'hidden'
                            && r.width > 0 && r.height > 0,
                     text: (el.textContent || '').trim().slice(0, 120)};
           }""",
        el_id,
    )


def probe_many(page, ids):
    return {i: probe(page, i) for i in ids}


# Row -> the ids the matrix names for it (§2.10 declaration table).
DECL_ROWS = {
    "C2.10-01": ["model-selection-modal", "model-search-input", "model-selection-table-container", "model-selection-modal-close"],
    "C2.10-02": ["live-switch-modal", "live-switch-dataset-summary", "live-switch-fallback-button", "live-switch-accept-button"],
    "C2.10-03": ["live-switch-progress-alert", "live-switch-cancel-button", "live-switch-outcome-alert"],
    "C2.10-04": [
        "restart-confirm-modal",
        "restart-confirm-summary",
        "restart-start-fresh-toggle",
        "restart-granular-toggle",
        "restart-granular-collapse",
        "restart-granular-context",
        "restart-modal-baseline",
        "restart-cancel-button",
        "restart-confirm-button",
    ],
    "C2.10-05": ["restart-progress-alert", "restart-outcome-alert", "dataset-stage-outcome-alert"],
    "C2.10-06": ["training-control-outcome-alert"],
}

# §2.9 tail rows still unfilled after segment 12.
TAIL_29 = {
    "C2.9-01": ["pending-dataset-banner"],
    "C2.9-02": ["restart-with-new-dataset-button"],
    "C2.9-03": ["cancel-pending-dataset-button"],
    "C2.9-07": ["experimental-functions-toggle"],
    "C2.9-09": ["experimental-functions-alert"],
    "C2.9-11": ["network-info-panel"],
    "C2.9-13": ["network-info-details-panel"],
    "C2.9-14": ["sidebar-pinned-card"],
    "C2.9-15": ["sidebar-pinned-list"],
}

# The 11 granular restart-modal fields (N3b) -- C2.10-07..17.
RESTART_DS_FIELDS = ["restart-ds-type", "restart-ds-samples", "restart-ds-noise", "restart-ds-rotations", "restart-ds-spirals"]
RESTART_P_FIELDS = [
    "restart-p-nn-learning-rate",
    "restart-p-nn-max-hidden-units",
    "restart-p-nn-patience",
    "restart-p-cn-pool-size",
    "restart-p-cn-selected",
    "restart-p-cn-corr-thresh",
]


def step_survey(page, ctx):
    """Read every §2.10 + §2.9-tail surface as shipped, before any gesture."""
    out = {"decl": {}, "tail": {}}
    for row, ids in DECL_ROWS.items():
        out["decl"][row] = probe_many(page, ids)
    for row, ids in TAIL_29.items():
        out["tail"][row] = probe_many(page, ids)
    # tooltips (C2.9-16): count rendered dbc.Tooltip targets
    out["tooltips"] = page.evaluate(
        """() => {
             const tips = [...document.querySelectorAll('[id]')].filter(e => /tooltip/i.test(e.id));
             return {byIdCount: tips.length, ids: tips.map(t => t.id).slice(0, 40)};
           }"""
    )
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_numeric_attrs(page, ctx):
    """Read min/step/validity for the 11 granular restart-modal fields.

    Segment 10 proved the T-22 numeric wall is obsolete for the ``restart-ds-*``
    fields post-canopy#489; the six ``restart-p-*`` fields were explicitly never
    re-tested. This reads the grid so the re-test is grounded, not assumed.
    The modal must be OPEN first (fields are built on open).
    """
    ids = RESTART_DS_FIELDS + RESTART_P_FIELDS
    res = page.evaluate(
        """(ids) => {
             const out = {};
             for (const id of ids) {
               const el = document.getElementById(id);
               if (!el) { out[id] = 'ABSENT'; continue; }
               out[id] = {tag: el.tagName, type: el.getAttribute('type'),
                          value: el.value, min: el.getAttribute('min'),
                          max: el.getAttribute('max'), step: el.getAttribute('step'),
                          disabled: el.disabled,
                          stepMismatch: el.validity ? el.validity.stepMismatch : null,
                          valid: el.validity ? el.validity.valid : null};
             }
             return out;
           }""",
        ids,
    )
    print(json.dumps(res, indent=1, sort_keys=True))
    return res


def _click(page, el_id: str) -> bool:
    """Raw JS click.

    Segment 12 established this is the reliable instrument on this page:
    Playwright's post-click ack times out here, and during a live run the
    actionability wait never clears at all. A JS ``.click()`` on a button drives
    the real Dash callback chain (proved by a genuine /ws/control command with a
    command_id). The numeric wall was always about ``type=number`` VALUE
    propagation, never about button clicks.
    """
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); if (!el) return false; el.click(); return true; }""",
        el_id,
    )


def _set_checkbox(page, el_id: str, value: bool) -> bool:
    """Set a dbc.Switch / dbc.Checkbox and make Dash see it.

    A raw ``.click()`` drives BUTTONS correctly on this page but is inert on
    these switches -- proved on ``experimental-functions-toggle``, where
    ``.click()`` left both ``.checked`` and the backend untouched while the
    React-controlled idiom below flipped the backend to ``enabled: true``.
    Same mechanism as the numeric inputs: set through the native property
    descriptor, then dispatch the event React actually listens for.
    """
    return page.evaluate(
        """([id, val]) => {
             let el = document.getElementById(id);
             if (!el) return {ok: false, why: 'absent'};
             // dbc sometimes puts the id on a wrapper; find the real input.
             if (el.tagName !== 'INPUT') {
               const inner = el.querySelector('input[type=checkbox]');
               if (!inner) return {ok: false, why: 'no input under ' + el.tagName};
               el = inner;
             }
             const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
             setter.call(el, val);
             el.dispatchEvent(new Event('click', {bubbles: true}));
             el.dispatchEvent(new Event('change', {bubbles: true}));
             return {ok: true, tag: el.tagName, checked: el.checked};
           }""",
        [el_id, value],
    )


def _wait_present(page, el_id: str, timeout_ms: int = 15000, poll_ms: int = 500):
    """Poll for an id to APPEAR. Absence is the normal closed state here."""
    waited = 0
    while waited < timeout_ms:
        page.wait_for_timeout(poll_ms)
        waited += poll_ms
        p = probe(page, el_id)
        if p.get("present"):
            return waited, p
    return None, probe(page, el_id)


def step_model_modal(page, ctx):
    """C2.10-01 + C2.6-17/18/19 -- the model picker, opened from the sidebar."""
    out = {"before": probe_many(page, DECL_ROWS["C2.10-01"])}
    out["summary_before"] = text_of(page, "nn-model-summary")
    out["hint_before"] = text_of(page, "nn-model-dataset-hint")
    out["clicked"] = _click(page, "nn-model-change-button")
    at, _ = _wait_present(page, "model-selection-modal")
    out["opened_at_ms"] = at
    out["after"] = probe_many(page, DECL_ROWS["C2.10-01"])
    out["table_rows"] = page.evaluate(
        """() => { const c = document.getElementById('model-selection-table-container');
                   if (!c) return null;
                   return {rowCount: c.querySelectorAll('tr').length,
                           text: (c.textContent || '').trim().slice(0, 300)}; }"""
    )
    # keyboard=False / backdrop static are documented for the OTHER two modals;
    # record this one's escape behaviour anyway since it is cheap.
    page.keyboard.press("Escape")
    page.wait_for_timeout(2500)
    out["after_escape"] = probe(page, "model-selection-modal")
    if probe(page, "model-selection-modal-close").get("present"):
        _click(page, "model-selection-modal-close")
        page.wait_for_timeout(3000)
    out["after_close"] = probe(page, "model-selection-modal")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_experimental(page, ctx):
    """C2.9-07/08/09 -- server-authoritative reconcile, then toggle ON."""
    out = {}
    out["api_before"] = http_get("/api/admin/experimental_functions")
    out["checked_before"] = page.evaluate(
        """() => { const el = document.getElementById('experimental-functions-toggle');
                   return el ? {checked: el.checked, type: el.type} : null; }"""
    )
    off = log_size()
    out["clicked"] = page.evaluate(
        """() => { const el = document.getElementById('experimental-functions-toggle');
                   if (!el) return false; el.click(); return true; }"""
    )
    samples = []
    for _ in range(12):
        page.wait_for_timeout(700)
        samples.append(
            {
                "checked": page.evaluate("""() => { const e = document.getElementById('experimental-functions-toggle'); return e ? e.checked : null; }"""),
                "alert": probe(page, "experimental-functions-alert").get("shown"),
                "alert_text": probe(page, "experimental-functions-alert").get("text"),
            }
        )
    out["samples"] = samples
    out["api_after"] = http_get("/api/admin/experimental_functions")
    out["server_log"] = log_since(off, ("experimental",))[:10]
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_tooltips(page, ctx):
    """C2.9-16 -- dbc.Tooltip renders only while hovered, so hover to prove it."""
    out = {}
    out["targets_declared"] = page.evaluate(
        """() => {
             // every element that has a tooltip attached renders one on hover;
             // count the parameter inputs + apply button the matrix names.
             const ids = [...document.querySelectorAll('input[id^="nn-"], input[id^="cn-"]')].map(e => e.id);
             return {numeric_inputs: ids.length, ids: ids};
           }"""
    )
    # Playwright's page.hover() hits the same actionability wall as its click on
    # this page (30 s timeout), so dispatch the pointer events dbc.Tooltip
    # actually listens for.
    def js_hover(el_id: str):
        return page.evaluate(
            """(id) => {
                 const el = document.getElementById(id);
                 if (!el) return false;
                 for (const t of ['pointerover', 'mouseover', 'mouseenter']) {
                   el.dispatchEvent(new MouseEvent(t, {bubbles: true, cancelable: true, view: window}));
                 }
                 return true;
               }""",
            el_id,
        )

    def tips():
        return page.evaluate(
            """() => {
                 const t = [...document.querySelectorAll('.tooltip, [role="tooltip"]')];
                 return {count: t.length, texts: t.map(x => (x.textContent || '').trim().slice(0, 140))};
               }"""
        )

    out["tips_idle"] = tips()
    for target in ("nn-learning-rate-input", "apply-params-button", "cn-pool-size-input"):
        out[f"hover_{target}"] = {"dispatched": js_hover(target)}
        found = None
        for _ in range(10):
            page.wait_for_timeout(500)
            t = tips()
            if t["count"] > out["tips_idle"]["count"]:
                found = t
                break
        out[f"hover_{target}"]["tooltip"] = found or tips()
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_stage_dataset(page, ctx):
    """C2.9-01/02/03 -- Apply Dataset opens the banner; the two buttons live in it."""
    out = {"banner_before": probe(page, "pending-dataset-banner")}
    off = log_size()
    out["clicked_apply_dataset"] = _click(page, "apply-dataset-button")
    at, p = _wait_present(page, "pending-dataset-banner", timeout_ms=20000)
    out["banner_opened_at_ms"] = at
    out["banner_after"] = p
    out["banner_children"] = probe_many(page, ["restart-with-new-dataset-button", "cancel-pending-dataset-button"])
    out["stage_outcome_alert"] = probe(page, "dataset-stage-outcome-alert")
    out["server_log"] = log_since(off, ("stage_dataset", "pending"))[:10]
    out["api_status"] = http_get("/api/status")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_restart_modal(page, ctx):
    """C2.10-04 + C2.10-07..17 -- open the restart modal and read its fields.

    Requires the pending-dataset banner to be open (run --step stage_dataset
    first in the same browser session).
    """
    out = {"modal_before": probe(page, "restart-confirm-modal")}
    # On a COLD load the banner is not opened by the Apply-Dataset callback; it
    # is reconciled from /api/status.pending_dataset on a slow tick, which takes
    # longer than the driver's initial settle. Waiting for it is also the
    # independent proof of C2.9-01's reconcile path.
    at_banner, _ = _wait_present(page, "restart-with-new-dataset-button", timeout_ms=40000)
    out["banner_reconciled_at_ms"] = at_banner
    out["clicked"] = _click(page, "restart-with-new-dataset-button")
    at, p = _wait_present(page, "restart-confirm-modal", timeout_ms=20000)
    out["opened_at_ms"] = at
    out["modal_after"] = p
    out["children"] = probe_many(page, DECL_ROWS["C2.10-04"])
    out["summary"] = text_of(page, "restart-confirm-summary")
    # granular fields are built behind the toggle
    out["granular_before"] = probe(page, "restart-granular-collapse")
    # restart-granular-toggle is a dbc.Button ("▸ Verify / modify what will
    # happen"), not a Switch -- a raw .click() is the right instrument.
    out["granular_clicked"] = _click(page, "restart-granular-toggle")
    page.wait_for_timeout(8000)
    out["granular_after"] = probe(page, "restart-granular-collapse")
    out["numeric_attrs"] = step_numeric_attrs(page, ctx)
    # backdrop="static" / keyboard=False are documented for this modal
    page.keyboard.press("Escape")
    page.wait_for_timeout(2500)
    out["after_escape"] = probe(page, "restart-confirm-modal")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_exp_diag(page, ctx):
    """Diagnose why the experimental switch does not respond to a JS click.

    Tries, in order: structure dump, fast sampling around a raw .click(), a
    real trusted Playwright click on the input, and a click on its label. The
    first approach that moves ``GET /api/admin/experimental_functions`` is the
    one the row should be driven with.
    """
    out = {}
    out["structure"] = page.evaluate(
        """() => {
             const el = document.getElementById('experimental-functions-toggle');
             if (!el) return 'ABSENT';
             const p = el.parentElement, gp = p && p.parentElement;
             const cs = getComputedStyle(el);
             return {tag: el.tagName, type: el.type, cls: el.className, checked: el.checked,
                     disabled: el.disabled, pointerEvents: cs.pointerEvents,
                     opacity: cs.opacity, position: cs.position,
                     parentTag: p && p.tagName, parentCls: p && p.className,
                     parentHTML: p ? p.outerHTML.slice(0, 400) : null,
                     labels: [...(el.labels || [])].map(l => ({cls: l.className, text: (l.textContent||'').trim().slice(0,60)}))};
           }"""
    )

    def api_enabled():
        r = http_get("/api/admin/experimental_functions")
        try:
            return r[1]["data"]["enabled"]
        except Exception:  # noqa: BLE001
            return f"unparsed:{r}"

    out["api_start"] = api_enabled()

    # (a) raw .click() with FAST sampling — does it flip then revert?
    page.evaluate("""() => { const e = document.getElementById('experimental-functions-toggle'); e.click(); }""")
    fast = []
    for _ in range(10):
        page.wait_for_timeout(150)
        fast.append(page.evaluate("""() => { const e = document.getElementById('experimental-functions-toggle'); return e ? e.checked : null; }"""))
    out["a_raw_click_fast_samples"] = fast
    page.wait_for_timeout(4000)
    out["a_api"] = api_enabled()

    # (b) native setter + change event (the React-controlled idiom)
    page.evaluate(
        """() => { const e = document.getElementById('experimental-functions-toggle');
                   const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
                   s.call(e, true);
                   e.dispatchEvent(new Event('click', {bubbles: true}));
                   e.dispatchEvent(new Event('change', {bubbles: true})); }"""
    )
    page.wait_for_timeout(5000)
    out["b_checked"] = page.evaluate("""() => document.getElementById('experimental-functions-toggle').checked""")
    out["b_api"] = api_enabled()

    # (c) a real trusted Playwright click on the input
    try:
        page.click("#experimental-functions-toggle", timeout=4000)
    except Exception as e:  # noqa: BLE001
        out["c_click_error"] = str(e)[:200]
    page.wait_for_timeout(5000)
    out["c_checked"] = page.evaluate("""() => document.getElementById('experimental-functions-toggle').checked""")
    out["c_api"] = api_enabled()

    out["alert"] = probe(page, "experimental-functions-alert")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def _set_number(page, el_id: str, value: str):
    """React-controlled numeric set (native descriptor + input/change)."""
    return page.evaluate(
        """([id, val]) => {
             const el = document.getElementById(id);
             if (!el) return {ok: false};
             const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
             s.call(el, val);
             el.dispatchEvent(new Event('input', {bubbles: true}));
             el.dispatchEvent(new Event('change', {bubbles: true}));
             return {ok: true, value: el.value, valid: el.validity.valid, stepMismatch: el.validity.stepMismatch};
           }""",
        [el_id, value],
    )


def step_granular_modify(page, ctx):
    """C2.10-08..17 MODIFY half -- the matrix calls this MANUAL-only (T-22).

    The claim rests on the numeric wall, which canopy#489 retired. Segment 10
    drove one ``restart-ds-*`` field this way; the six ``restart-p-*`` fields
    were explicitly never re-tested. This drives one of each and scores by the
    row's own stated effect: ``#restart-confirm-summary`` re-renders the delta
    against ``restart-modal-baseline``.
    """
    out = {}
    at_banner, _ = _wait_present(page, "restart-with-new-dataset-button", timeout_ms=40000)
    out["banner_at_ms"] = at_banner
    _click(page, "restart-with-new-dataset-button")
    at, _ = _wait_present(page, "restart-confirm-modal", timeout_ms=20000)
    out["modal_at_ms"] = at
    _click(page, "restart-granular-toggle")
    page.wait_for_timeout(8000)
    out["granular_open"] = probe(page, "restart-granular-collapse").get("shown")
    out["summary_baseline"] = text_of(page, "restart-confirm-summary")

    trials = [
        ("C2.10-10", "restart-ds-rotations", "2.5"),  # segment-10 control
        ("C2.10-08", "restart-ds-samples", "1500"),
        ("C2.10-09", "restart-ds-noise", "0.4"),
        ("C2.10-11", "restart-ds-spirals", "3"),
        ("C2.10-14", "restart-p-nn-patience", "77"),  # the never-retested class
        ("C2.10-12", "restart-p-nn-learning-rate", "0.0733"),
        ("C2.10-13", "restart-p-nn-max-hidden-units", "7"),
        ("C2.10-15", "restart-p-cn-pool-size", "33"),
        ("C2.10-16", "restart-p-cn-selected", "2"),
        ("C2.10-17", "restart-p-cn-corr-thresh", "0.0077"),
    ]
    results = []
    for row, field, val in trials:
        before = text_of(page, "restart-confirm-summary")
        setres = _set_number(page, field, val)
        changed_at = None
        after = before
        for i in range(16):
            page.wait_for_timeout(700)
            after = text_of(page, "restart-confirm-summary")
            if after != before:
                changed_at = (i + 1) * 700
                break
        results.append(
            {
                "row": row,
                "field": field,
                "set": val,
                "set_result": setres,
                "summary_changed_at_ms": changed_at,
                "summary_after": (after or "")[:400],
            }
        )
    out["trials"] = results

    # C2.10-07: restart-ds-type is the one field the matrix already calls AUTO —
    # a Dash 3.x Radix select (a <button aria-haspopup=listbox> with options
    # portalled to body). Match the label EXACTLY; scope by aria-controls.
    before = text_of(page, "restart-confirm-summary")
    out["ds_type_before"] = dropdown_value(page, "restart-ds-type")
    picked = dropdown_select(page, "restart-ds-type", "XOR")
    if not picked:
        picked = dropdown_select(page, "restart-ds-type", "Xor")
    out["ds_type_selected"] = picked
    changed_at = None
    after = before
    for i in range(16):
        page.wait_for_timeout(700)
        after = text_of(page, "restart-confirm-summary")
        if after != before:
            changed_at = (i + 1) * 700
            break
    out["ds_type_after"] = dropdown_value(page, "restart-ds-type")
    out["ds_type_summary_changed_at_ms"] = changed_at
    out["ds_type_summary"] = (after or "")[:300]

    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_cancel_pending(page, ctx):
    """C2.9-03 -- DELETE /api/cancel_pending_dataset closes the banner."""
    out = {}
    at, _ = _wait_present(page, "cancel-pending-dataset-button", timeout_ms=40000)
    out["banner_at_ms"] = at
    out["status_before"] = http_get("/api/status")[1].get("pending_dataset")
    off = log_size()
    out["clicked"] = _click(page, "cancel-pending-dataset-button")
    closed_at = None
    for i in range(20):
        page.wait_for_timeout(700)
        if not probe(page, "pending-dataset-banner").get("present"):
            closed_at = (i + 1) * 700
            break
    out["banner_closed_at_ms"] = closed_at
    out["status_after"] = http_get("/api/status")[1].get("pending_dataset")
    out["server_log"] = log_since(off, ("cancel_pending", "cancel"))[:8]
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_panels(page, ctx):
    """C2.9-11 / C2.9-13 -- both panels are refilled every slow tick.

    Read a panel's content only with its own surface reachable; sample twice
    with a gap so 'refilled' is demonstrated rather than assumed.
    """
    out = {}
    out["info_1"] = probe(page, "network-info-panel").get("text")
    out["details_1"] = probe(page, "network-info-details-panel").get("text")
    # open the details level so the second panel is genuinely rendered
    _click(page, "network-info-details-header")
    page.wait_for_timeout(4000)
    out["details_collapse_shown"] = probe(page, "network-info-details-collapse").get("shown")
    page.wait_for_timeout(12000)
    out["info_2"] = probe(page, "network-info-panel").get("text")
    out["details_2"] = probe(page, "network-info-details-panel").get("text")
    out["info_stable"] = out["info_1"] == out["info_2"]
    out["details_stable"] = out["details_1"] == out["details_2"]
    # a slow-tick refill is observable as a network call even when the value is
    # unchanged; count the /api/ traffic the page made during the window.
    out["api_calls_seen"] = len([c for c in ctx["capture"] if "/api/" in c["url"]])
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_live_switch(page, ctx):
    """C2.7-10 + C2.10-02/03 -- the hot-swap gate and its two-step modal.

    ``live-dataset-switch-button`` ships disabled and is enabled ONLY when
    experimental_functions AND training-status.is_running are both true
    (``_gate_live_switch_button_handler``). This starts a run to satisfy the
    second half, then opens the modal. Also re-samples the two network-info
    panels: with a live network their values MOVE, which is what proves the
    slow-tick refill (C2.9-11 / C2.9-13) rather than assuming it.
    """
    out = {}
    out["experimental"] = http_get("/api/admin/experimental_functions")[1]
    out["gate_before"] = {
        "present": probe(page, "live-dataset-switch-button").get("present"),
        "disabled": is_disabled(page, "live-dataset-switch-button"),
    }
    out["panel_idle"] = probe(page, "network-info-panel").get("text")
    out["details_idle"] = probe(page, "network-info-details-panel").get("text")

    out["start_clicked"] = _click(page, "start-button")
    running_at = None
    for i in range(30):
        page.wait_for_timeout(1000)
        st = http_get("/v1/health")
        try:
            if http_get("/api/status")[1].get("is_running"):
                running_at = (i + 1) * 1000
                break
        except Exception:  # noqa: BLE001
            pass
    out["running_at_ms"] = running_at
    out["api_status"] = {k: v for k, v in (http_get("/api/status")[1] or {}).items() if k in ("is_running", "fsm_status", "hidden_units", "current_epoch")}

    # gate should now be open
    gate_at = None
    for i in range(20):
        page.wait_for_timeout(1000)
        if is_disabled(page, "live-dataset-switch-button") is False:
            gate_at = (i + 1) * 1000
            break
    out["gate_enabled_at_ms"] = gate_at
    out["gate_after"] = {"disabled": is_disabled(page, "live-dataset-switch-button")}

    # panels with a LIVE network -- values must move
    page.wait_for_timeout(8000)
    out["panel_live"] = probe(page, "network-info-panel").get("text")
    out["details_live"] = probe(page, "network-info-details-panel").get("text")
    out["panel_moved"] = out["panel_idle"] != out["panel_live"]
    out["details_moved"] = out["details_idle"] != out["details_live"]

    # C2.10-02 / C2.10-03: open the two-step modal
    out["switch_clicked"] = _click(page, "live-dataset-switch-button")
    at, p = _wait_present(page, "live-switch-modal", timeout_ms=25000)
    out["modal_at_ms"] = at
    out["modal"] = p
    out["c2_10_02"] = probe_many(page, DECL_ROWS["C2.10-02"])
    out["c2_10_03"] = probe_many(page, DECL_ROWS["C2.10-03"])
    out["summary_text"] = text_of(page, "live-switch-dataset-summary")
    # backdrop="static", keyboard=False -> Escape must NOT close it
    page.keyboard.press("Escape")
    page.wait_for_timeout(2500)
    out["after_escape_present"] = probe(page, "live-switch-modal").get("present")
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_pinned(page, ctx):
    """C2.9-14 / C2.9-15 -- the sidebar 'Pinned Parameters' mirror.

    The card ships ``display:none`` and is shown only when
    ``pinned-params-store`` is non-empty. The store's only writer is the
    pattern-matched pin checkbox set ``{"type": "param-pin", "key": ALL}`` in
    the Parameters tab, so the card can only be driven from there.
    """
    wire = {"store": [], "card": []}

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        try:
            txt = json.dumps(resp.json())
        except Exception:  # noqa: BLE001
            return
        if "pinned-params-store" in txt:
            wire["store"].append(txt[:260])
        if "sidebar-pinned-card" in txt:
            wire["card"].append(txt[:260])

    page.on("response", on_response)
    out = {"card_before": probe(page, "sidebar-pinned-card"), "list_before": probe(page, "sidebar-pinned-list")}
    # switch to the Parameters tab
    out["tab_clicked"] = page.evaluate(
        """() => {
             const t = [...document.querySelectorAll('[role=tab], .nav-link, a')]
                        .find(e => (e.textContent || '').trim() === 'Parameters');
             if (!t) return false; t.click(); return true;
           }"""
    )
    page.wait_for_timeout(6000)
    out["pins_found"] = page.evaluate(
        """() => {
             const els = [...document.querySelectorAll('input[type=checkbox]')]
               .filter(e => (e.id || '').includes('param-pin'));
             return {count: els.length, ids: els.map(e => e.id).slice(0, 5)};
           }"""
    )
    # check the first pin using the React-controlled idiom
    out["pin_set"] = page.evaluate(
        """() => {
             const el = [...document.querySelectorAll('input[type=checkbox]')]
               .find(e => (e.id || '').includes('param-pin'));
             if (!el) return {ok: false};
             const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
             s.call(el, true);
             el.dispatchEvent(new Event('click', {bubbles: true}));
             el.dispatchEvent(new Event('change', {bubbles: true}));
             return {ok: true, id: el.id, checked: el.checked};
           }"""
    )
    # The native-setter idiom that drives dbc.Switch did NOT reach this
    # dbc.Checkbox's ``value`` prop (the store callback fired but read all
    # falsy), so follow up with a TRUSTED click. Its ack times out on this page
    # -- that is expected and documented; verify by effect, not by return.
    sel = "[id='{\"key\":\"max_iterations\",\"type\":\"param-pin\"}']"
    try:
        page.check(sel, timeout=4000, force=True)
        out["trusted_check"] = "ok"
    except Exception as e:  # noqa: BLE001
        out["trusted_check"] = f"ack-timeout(expected): {str(e)[:80]}"
    shown_at = None
    for i in range(20):
        page.wait_for_timeout(700)
        if probe(page, "sidebar-pinned-card").get("shown"):
            shown_at = (i + 1) * 700
            break
    out["card_shown_at_ms"] = shown_at
    out["card_after"] = probe(page, "sidebar-pinned-card")
    out["list_after"] = probe(page, "sidebar-pinned-list")
    out["wire_store_count"] = len(wire["store"])
    out["wire_store"] = wire["store"][:3]
    out["wire_card_count"] = len(wire["card"])
    out["wire_card"] = wire["card"][:3]
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_interval_clamp(page, ctx):
    """C2.9-06 -- the apply-in-flight interval clamp must never freeze the page.

    ``dcc.Interval`` emits no DOM node, so the clamp cannot be read directly;
    the row's stated invariant is behavioural ('Dashboard must never stay
    frozen'), so score it that way: make the page dirty, Apply, then prove the
    dashboard is still updating afterwards and the console stayed clean.
    """
    out = {}
    errors = []
    page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
    # dirty one tracked field so Apply enables
    _set_number(page, "nn-patience-input", "44")
    for _ in range(14):
        page.wait_for_timeout(500)
        if is_disabled(page, "apply-params-button") is False:
            break
    out["apply_enabled"] = is_disabled(page, "apply-params-button") is False
    out["clicked"] = _click(page, "apply-params-button")
    statuses = []
    for _ in range(14):
        page.wait_for_timeout(900)
        statuses.append(text_of(page, "params-status"))
    out["status_trail"] = statuses
    # after the apply settles, is the dashboard still alive? the network-info
    # panel is refilled on the slow tick, so a later re-read proves the
    # intervals were re-enabled rather than left disabled.
    a = probe(page, "network-info-panel").get("text")
    page.wait_for_timeout(12000)
    b = probe(page, "network-info-panel").get("text")
    out["panel_a"] = (a or "")[:90]
    out["panel_b"] = (b or "")[:90]
    out["panel_still_updating"] = a != b
    out["console_errors"] = errors[:6]
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_gate_watch(page, ctx):
    """C2.7-10 -- does the live-switch gate EVER open with both conditions true?

    A 20 s window showed it still disabled while the backend reported
    experimental enabled AND is_running. F-CANOPY-004 documents server-side
    callbacks lagging 30 s to minutes during a live run, so a short window
    cannot tell 'lagging' from 'never'. Watch for two minutes and report the
    first moment it flips, alongside the backend truth at each sample.
    """
    out = {"samples": []}
    out["experimental"] = http_get("/api/admin/experimental_functions")[1]
    flipped_at = None
    for i in range(24):
        page.wait_for_timeout(5000)
        st = http_get("/api/status")[1] or {}
        dis = is_disabled(page, "live-dataset-switch-button")
        out["samples"].append(
            {
                "t_ms": (i + 1) * 5000,
                "gate_disabled": dis,
                "is_running": st.get("is_running"),
                "fsm": st.get("fsm_status"),
                "units": st.get("hidden_units"),
            }
        )
        if dis is False:
            flipped_at = (i + 1) * 5000
            break
    out["gate_enabled_at_ms"] = flipped_at
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_gate_force(page, ctx):
    """Force ``experimental-flags-store`` to CHANGE and see if the gate fires.

    The store values observed on the wire are byte-identical every tick
    (``{"is_running": true, "phase": "candidate"}``), so if Dash only
    propagates on a changed value the gate would never re-fire. Toggling
    experimental OFF then ON forces a genuine true->false->true transition;
    if the gate fires on that, the trigger condition is the discriminator.
    """
    seen = []

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        try:
            txt = json.dumps(resp.json())
        except Exception:  # noqa: BLE001
            return
        if "live-dataset-switch-button" in txt:
            seen.append(txt[:200])

    page.on("response", on_response)
    out = {"gate_at_start": is_disabled(page, "live-dataset-switch-button")}

    def set_toggle(v):
        return page.evaluate(
            """(val) => { const el = document.getElementById('experimental-functions-toggle');
                          const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
                          s.call(el, val);
                          el.dispatchEvent(new Event('click', {bubbles: true}));
                          el.dispatchEvent(new Event('change', {bubbles: true}));
                          return el.checked; }""",
            v,
        )

    out["set_off"] = set_toggle(False)
    page.wait_for_timeout(8000)
    out["gate_after_off"] = is_disabled(page, "live-dataset-switch-button")
    out["api_after_off"] = (http_get("/api/admin/experimental_functions")[1] or {}).get("data", {}).get("enabled")
    out["set_on"] = set_toggle(True)
    page.wait_for_timeout(10000)
    out["gate_after_on"] = is_disabled(page, "live-dataset-switch-button")
    out["api_after_on"] = (http_get("/api/admin/experimental_functions")[1] or {}).get("data", {}).get("enabled")
    out["api_running"] = (http_get("/api/status")[1] or {}).get("is_running")
    out["gate_responses"] = seen[:5]
    out["gate_response_count"] = len(seen)
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_gate_wire(page, ctx):
    """Read the gate's two store inputs off the _dash-update-component wire.

    A component id appearing in a REQUEST proves nothing (every fire of a
    many-Input callback names them all) -- only the carried VALUE is evidence,
    and that lives in the RESPONSE. This hooks responses and reports exactly
    what ``training-status-store`` and ``experimental-flags-store`` receive, and
    whether any response carries the button's ``disabled`` prop.
    """
    seen = {"training_status": [], "experimental_flags": [], "button_disabled": []}

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            return
        txt = json.dumps(body)
        if "training-status-store" in txt:
            seen["training_status"].append(txt[:300])
        if "experimental-flags-store" in txt:
            seen["experimental_flags"].append(txt[:300])
        if "live-dataset-switch-button" in txt:
            seen["button_disabled"].append(txt[:300])

    page.on("response", on_response)
    page.reload(wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3000)
    dismiss_welcome(page)
    page.wait_for_timeout(30000)
    out = {
        "training_status_count": len(seen["training_status"]),
        "training_status_samples": seen["training_status"][:3],
        "experimental_flags_count": len(seen["experimental_flags"]),
        "experimental_flags_samples": seen["experimental_flags"][:3],
        "button_disabled_count": len(seen["button_disabled"]),
        "button_disabled_samples": seen["button_disabled"][:3],
        "gate_disabled_now": is_disabled(page, "live-dataset-switch-button"),
        "api_running": (http_get("/api/status")[1] or {}).get("is_running"),
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


def step_gate_inputs(page, ctx):
    """Which of the gate's two store inputs is not True?

    ``load_reconcile_experimental_functions`` writes the toggle value AND
    ``experimental-flags-store`` from the same response, so the toggle's checked
    state is a faithful proxy for the flags store. ``training-status-store`` has
    no such proxy, but the top status bar is fed from the same poll.
    """
    out = {}
    for i in range(8):
        page.wait_for_timeout(4000)
        out[f"t{(i+1)*4000}"] = {
            "toggle_checked": page.evaluate("""() => { const e = document.getElementById('experimental-functions-toggle'); return e ? e.checked : null; }"""),
            "gate_disabled": is_disabled(page, "live-dataset-switch-button"),
            "api_enabled": (http_get("/api/admin/experimental_functions")[1] or {}).get("data", {}).get("enabled"),
            "api_running": (http_get("/api/status")[1] or {}).get("is_running"),
            "status_bar": (probe(page, "unified-status-bar").get("text") or probe(page, "training-status").get("text") or "")[:90],
        }
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


STEPS = {
    "survey": step_survey,
    "pinned": step_pinned,
    "gate_watch": step_gate_watch,
    "gate_inputs": step_gate_inputs,
    "gate_wire": step_gate_wire,
    "gate_force": step_gate_force,
    "interval_clamp": step_interval_clamp,
    "numeric": step_numeric_attrs,
    "exp_diag": step_exp_diag,
    "granular_modify": step_granular_modify,
    "cancel_pending": step_cancel_pending,
    "panels": step_panels,
    "live_switch": step_live_switch,
    "model_modal": step_model_modal,
    "experimental": step_experimental,
    "tooltips": step_tooltips,
    "stage_dataset": step_stage_dataset,
    "restart_modal": step_restart_modal,
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", action="append", required=True, choices=sorted(STEPS), help="step(s) to run, in order")
    args = ap.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        print(f"playwright unavailable: {exc}", file=sys.stderr)
        return 2

    capture: list = []
    with sync_playwright() as pw:
        browser, ctx_, page = open_dashboard(pw, capture)
        ctx = {"capture": capture}
        try:
            for name in args.step:
                log(f"=== step {name} ===")
                STEPS[name](page, ctx)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
