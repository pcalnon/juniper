#!/usr/bin/env python3
"""
Project: Juniper
Sub-Project: juniper-ml
Application: Canopy E2E Phase 1 -- W3 parameter apply round-trip driver
Author: Paul Calnon
Version: 0.1.0
License: MIT License

Ad-hoc live driver for the **W3** rows of the canopy E2E click-by-click matrix
(``notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md``
section "W3 -- Parameter apply round-trip").

Drives the running isolated-stack canopy dashboard with Playwright and prints
timestamped, quotable evidence for each matrix step. Every assertion is printed
rather than ``assert``-ed, because the deliverable is *recorded observed
behaviour* (PASS / FAIL / BLOCKED verdicts), not a red/green test run.

Methodology note (load-bearing): the dashboard's Apply POSTs
``/api/set_params`` **server-side** from the Dash callback
(``dashboard_manager.py:7034``), so that POST is invisible in the browser
network log. "Exactly one POST" is therefore proven from two independent
sides -- one browser ``_dash-update-component`` carrying the button click, and
the canopy server log's ``Parameters applied`` line (read by byte offset, since
the log is >100 MB).

Playwright lives only in the JuniperCanopy1 env:

    /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/e2e_w3_params_driver.py --steps 1,2

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

CANOPY = os.environ.get("JUNIPER_E2E_CANOPY_URL", "http://127.0.0.1:8051")
CANOPY_LOG = os.environ.get("JUNIPER_E2E_CANOPY_LOG", "/tmp/juniper-e2e/logs/juniper-canopy.log")

# The 27-key body the shipped canopy test uses (src/tests/ui/
# test_param_roundtrip_visible.py:37-65) = the dashboard's 25 POST keys minus
# nn_init_output_weights plus the three canopy-local keys.
PAYLOAD_KEYS = [
    "nn_learning_rate",
    "nn_max_hidden_units",
    "nn_max_total_epochs",
    "nn_max_iterations",
    "nn_growth_convergence_threshold",
    "nn_patience",
    "nn_spiral_rotations",
    "nn_spiral_number",
    "nn_dataset_elements",
    "nn_dataset_noise",
    "nn_multi_node_layers",
    "nn_growth_trigger",
    "nn_growth_preset_epochs",
    "cn_pool_size",
    "cn_correlation_threshold",
    "cn_selected_candidates",
    "cn_training_complete",
    "cn_training_iterations",
    "cn_training_convergence_threshold",
    "cn_patience",
    "cn_multi_candidate",
    "cn_candidate_selection",
    "cn_top_candidates",
    "cn_random_candidates",
    "nn_output_epochs",
    "nn_optimizer_type",
    "nn_activation_function_name",
]

_T0 = time.time()


def log(msg: str) -> None:
    print(f"[t={int((time.time() - _T0) * 1000):>7d}ms] {msg}", flush=True)


# --------------------------------------------------------------------------
# HTTP helpers (stdlib only -- this script must run under any env that has
# playwright, without assuming `requests`).
# --------------------------------------------------------------------------
def http_get(path: str, timeout: float = 10.0):
    with urllib.request.urlopen(CANOPY + path, timeout=timeout) as r:  # noqa: S310
        return r.status, json.loads(r.read().decode())


def http_post(path: str, body: dict, timeout: float = 30.0):
    data = json.dumps(body).encode()
    req = urllib.request.Request(CANOPY + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw)
            except ValueError:
                return r.status, raw
    except urllib.error.HTTPError as e:  # noqa: PERF203
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw


def build_payload(state: dict, **overrides) -> dict:
    """The 27-key body seeded from live /api/state, with overrides applied."""
    payload = {k: state.get(k) for k in PAYLOAD_KEYS}
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------
# Canopy server-log reader (byte-offset windowed -- the log is >100 MB).
# --------------------------------------------------------------------------
def log_size() -> int:
    try:
        return os.path.getsize(CANOPY_LOG)
    except OSError:
        return 0


def log_since(offset: int, needles: tuple[str, ...]) -> list[str]:
    out = []
    try:
        with open(CANOPY_LOG, "rb") as fh:
            fh.seek(offset)
            for raw in fh.read().decode("utf-8", "replace").splitlines():
                if any(n in raw for n in needles):
                    out.append(raw)
    except OSError as e:
        out.append(f"<log read failed: {e}>")
    return out


# --------------------------------------------------------------------------
# Browser helpers
# --------------------------------------------------------------------------
def open_dashboard(pw, capture: list):
    browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    ctx = browser.new_context(viewport={"width": 1600, "height": 1100})
    page = ctx.new_page()

    def on_request(req):
        if "_dash-update-component" in req.url or "/api/" in req.url:
            body = None
            try:
                body = req.post_data
            except Exception:  # noqa: BLE001
                body = None
            capture.append(
                {
                    "t_ms": int((time.time() - _T0) * 1000),
                    "method": req.method,
                    "url": req.url.replace(CANOPY, ""),
                    "body": (body or "")[:4000],
                }
            )

    page.on("request", on_request)
    page.on("console", lambda m: log(f"  CONSOLE[{m.type}] {m.text[:300]}") if m.type in ("error", "warning") else None)

    log(f"navigating to {CANOPY}")
    page.goto(CANOPY, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3000)
    dismiss_welcome(page)
    page.wait_for_timeout(2000)
    return browser, ctx, page


def dismiss_welcome(page) -> None:
    """The welcome modal sits over the dashboard after every load."""
    try:
        btn = page.locator("#welcome-modal-close")
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            log("  welcome modal dismissed")
            page.wait_for_timeout(800)
            return
    except Exception as e:  # noqa: BLE001
        log(f"  welcome dismiss raised: {e}")
    log("  welcome modal not present/visible")


def input_value(page, el_id: str):
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); return el ? el.value : null; }""",
        el_id,
    )


def is_disabled(page, el_id: str):
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); if (!el) return null;
                     return el.disabled === true || el.getAttribute('disabled') !== null
                            || (el.className || '').includes('disabled'); }""",
        el_id,
    )


def text_of(page, el_id: str):
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); return el ? (el.innerText || '').trim() : null; }""",
        el_id,
    )


def dropdown_value(page, dd_id: str):
    """Rendered value text of a Dash 3.x (Radix) dcc.Dropdown."""
    return page.evaluate(
        """(id) => { const root = document.getElementById(id); if (!root) return null;
                     const v = root.querySelector('.dash-dropdown-value-item');
                     return v ? v.innerText.trim() : (root.innerText || '').trim(); }""",
        dd_id,
    )


def dropdown_select(page, dd_id: str, label: str) -> bool:
    """Drive a Dash 3.x dcc.Dropdown.

    This build renders dcc.Dropdown as a Radix Select: the control is a
    ``<button aria-haspopup="listbox">`` and the options are portalled to the
    document body as ``[role="option"]``. Option names are matched EXACTLY --
    substring matching would pick "AdamW"/"NAdam"/"Adamax" for "Adam".
    """
    btn = page.locator(f"#{dd_id}")
    if not btn.count():
        log(f"  !! #{dd_id} absent")
        return False
    try:
        btn.scroll_into_view_if_needed()
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(400)
    btn.first.click()
    page.wait_for_timeout(900)
    state = page.evaluate(
        """(id) => { const el = document.getElementById(id); return el ? el.getAttribute('data-state') : null; }""",
        dd_id,
    )
    log(f"    (menu data-state={state!r}, options visible={page.locator('[role=option]').count()})")
    opt = page.get_by_role("option", name=label, exact=True)
    if not opt.count():
        log(f"  !! option '{label}' not found for #{dd_id}")
        page.keyboard.press("Escape")
        return False
    opt.first.click()
    page.wait_for_timeout(1200)
    return True


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
def step_1(page, ctx):
    log("=== W3-01: read current #nn-learning-rate-input DOM value ===")
    dom = input_value(page, "nn-learning-rate-input")
    _, state = http_get("/api/state")
    log(f"  DOM #nn-learning-rate-input.value = {dom!r}")
    log(f"  /api/state nn_learning_rate      = {state.get('nn_learning_rate')!r}")
    itype = page.evaluate("(id) => { const el = document.getElementById(id); return el ? el.type : null; }", "nn-learning-rate-input")
    log(f"  input type attr = {itype!r}")
    ctx["baseline_lr"] = state.get("nn_learning_rate")
    ctx["dom_lr"] = dom


def step_2(page, ctx):
    """The numeric wall, proven end-to-end rather than asserted from the shipped test."""
    log("=== W3-02: numeric-input wall -- typing fills the DOM but never reaches Dash ===")
    probe = 0.0424
    before_dom = input_value(page, "nn-learning-rate-input")
    page.locator("#nn-learning-rate-input").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    page.fill("#nn-learning-rate-input", str(probe))
    page.wait_for_timeout(1200)
    page.locator("#nn-learning-rate-input").blur()
    page.wait_for_timeout(1500)
    after_dom = input_value(page, "nn-learning-rate-input")
    _, state = http_get("/api/state")
    log(f"  DOM before fill = {before_dom!r}; after fill+blur = {after_dom!r} (probe {probe})")
    log(f"  /api/state nn_learning_rate after fill+blur = {state.get('nn_learning_rate')!r}")
    log("  -> DOM accepts the keystrokes; the question is whether Dash state saw them (see W3-07 apply body)")
    ctx["probe_lr"] = probe


def step_3(page, ctx):
    log("=== W3-03: POST /api/set_params with the 27-key body (new nn_learning_rate) ===")
    _, state = http_get("/api/state")
    new_lr = 0.0789
    payload = build_payload(state, nn_learning_rate=new_lr)
    missing = [k for k, v in payload.items() if v is None]
    log(f"  payload keys = {len(payload)}; None-valued = {missing or 'none'}")
    code, body = http_post("/api/set_params", payload)
    log(f"  POST /api/set_params -> {code}")
    log(f"  body = {json.dumps(body)[:600] if not isinstance(body, str) else body[:600]}")
    ctx["new_lr"] = new_lr


def step_4(page, ctx):
    log("=== W3-04: poll GET /api/state until nn_learning_rate matches (<=5 s) ===")
    target = ctx.get("new_lr", 0.0789)
    deadline = time.time() + 5
    last = None
    hit_at = None
    while time.time() < deadline:
        _, st = http_get("/api/state")
        last = st.get("nn_learning_rate")
        if last is not None and abs(float(last) - target) < 1e-9:
            hit_at = time.time()
            break
        time.sleep(0.25)
    if hit_at:
        log(f"  nn_learning_rate == {target} after {int((hit_at - (deadline - 5)) * 1000)}ms")
    else:
        log(f"  !! did NOT reach {target} within 5s; last={last!r}")


def step_5(page, ctx):
    log("=== W3-05: reload -> DOM input equals the new value after params-init-interval ===")
    target = ctx.get("new_lr", 0.0789)
    page.reload(wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3000)
    dismiss_welcome(page)
    ok = False
    try:
        page.wait_for_function(
            """(t) => { const el = document.getElementById('nn-learning-rate-input');
                        return el && Math.abs(parseFloat(el.value) - t) < 1e-6; }""",
            arg=target,
            timeout=15_000,
        )
        ok = True
    except Exception as e:  # noqa: BLE001
        log(f"  wait_for_function timed out: {str(e)[:200]}")
    log(f"  DOM #nn-learning-rate-input.value after init tick = {input_value(page, 'nn-learning-rate-input')!r} (expected {target}) -> {'MATCH' if ok else 'NO MATCH'}")


def _fresh(page):
    page.reload(wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3500)
    dismiss_welcome(page)
    page.wait_for_timeout(2500)


def step_2b(page, ctx):
    """Decisive numeric-wall probe: does a real fill() reach Dash state?

    ``nn-learning-rate-input`` is one of the dirty-tracking Inputs
    (dashboard_manager.py:4394) and the widget carries an *integer* debounce
    (NUMERIC_INPUT_DEBOUNCE_MS = 350), so if Dash ever sees the typed value the
    Apply button must flip from disabled to enabled ~350 ms after typing stops.
    Apply-enabled is therefore a direct oracle for "Dash state received it".
    """
    log("=== W3-02b: does fill() reach Dash state? (Apply-enabled as the oracle) ===")
    _fresh(page)
    before = is_disabled(page, "apply-params-button")
    dom_before = input_value(page, "nn-learning-rate-input")
    log(f"  baseline: #apply-params-button disabled={before!r}, LR DOM={dom_before!r}")

    probe = 0.0512
    page.locator("#nn-learning-rate-input").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    page.fill("#nn-learning-rate-input", str(probe))
    log(f"  filled LR with {probe}; waiting 1500ms (debounce is 350ms)")
    page.wait_for_timeout(1500)
    after = is_disabled(page, "apply-params-button")
    log(f"  after fill (no blur): #apply-params-button disabled={after!r}, LR DOM={input_value(page, 'nn-learning-rate-input')!r}")
    log(f"  -> VERDICT: fill() {'DID' if after is False else 'did NOT'} reach Dash state without a blur")
    ctx["probe_lr_2b"] = probe
    ctx["apply_disabled_after_fill"] = after


def step_2c(page, ctx):
    """Ladder of input techniques against the numeric wall.

    Apply-enabled (dirty tracking, dashboard_manager.py:4394) is the oracle for
    "Dash state received the value". Each rung is tried from a fresh reload so
    a later rung cannot inherit an earlier rung's commit.
    """
    log("=== W3-02c: input-technique ladder vs the numeric wall ===")

    def rung(name, action, settle=2000):
        _fresh(page)
        base = is_disabled(page, "apply-params-button")
        dom0 = input_value(page, "nn-learning-rate-input")
        page.locator("#nn-learning-rate-input").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        try:
            action()
        except Exception as e:  # noqa: BLE001
            log(f"  [{name}] action raised: {str(e)[:200]}")
            return
        page.wait_for_timeout(settle)
        after = is_disabled(page, "apply-params-button")
        dom1 = input_value(page, "nn-learning-rate-input")
        verdict = "REACHED Dash" if after is False else "blocked"
        log(f"  [{name}] Apply disabled {base!r} -> {after!r}; DOM {dom0!r} -> {dom1!r}  ==> {verdict}")

    probe = "0.0611"

    rung("fill only", lambda: page.fill("#nn-learning-rate-input", probe))
    rung(
        "fill + blur",
        lambda: (page.fill("#nn-learning-rate-input", probe), page.locator("#nn-learning-rate-input").blur()),
    )
    rung(
        "fill + Enter",
        lambda: (page.fill("#nn-learning-rate-input", probe), page.press("#nn-learning-rate-input", "Enter")),
    )
    rung(
        "click+selectAll+type (real keystrokes)",
        lambda: (
            page.click("#nn-learning-rate-input"),
            page.keyboard.press("ControlOrMeta+a"),
            page.keyboard.type(probe, delay=90),
        ),
    )
    rung(
        "keystrokes + Tab (blur via keyboard)",
        lambda: (
            page.click("#nn-learning-rate-input"),
            page.keyboard.press("ControlOrMeta+a"),
            page.keyboard.type(probe, delay=90),
            page.keyboard.press("Tab"),
        ),
    )


def _input_value_in_body(body: str, comp_id: str):
    """Pull one component's carried value out of a _dash-update-component body.

    Returns (found, value). Presence of the id proves nothing -- every fire of
    track_param_changes names all 27 Inputs -- so only the VALUE is evidence.
    """
    try:
        doc = json.loads(body)
    except (ValueError, TypeError):
        return False, "<unparseable>"
    for key in ("inputs", "state"):
        for item in doc.get(key) or []:
            if isinstance(item, dict) and item.get("id") == comp_id:
                return True, item.get("value")
    return False, None


def step_2e(page, ctx):
    """The corrected numeric-wall experiment: read the VALUE Dash received.

    Long settle first -- an under-settled page silently drops the callback and
    reads as a wall (the trap that made an earlier ladder run look conclusive).
    """
    log("=== W3-02e: numeric wall, judged on the VALUE Dash received ===")
    cap = ctx["_capture"]
    _fresh(page)
    page.wait_for_timeout(4000)

    probe = "0.0733"
    base = is_disabled(page, "apply-params-button")
    log(f"  settled baseline: Apply disabled={base!r}, LR DOM={input_value(page, 'nn-learning-rate-input')!r}")

    mark = len(cap)
    page.click("#nn-learning-rate-input")
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type(probe, delay=100)
    page.wait_for_timeout(1200)
    page.keyboard.press("Tab")
    page.wait_for_timeout(4000)

    fires = [
        c
        for c in cap[mark:]
        if "_dash-update-component" in c["url"] and '"id":"apply-params-button"' in (c["body"] or "")
    ]
    log(f"  track_param_changes fires after typing: {len(fires)}")
    for f in fires[-3:]:
        found, val = _input_value_in_body(f["body"], "nn-learning-rate-input")
        log(f"    fire t={f['t_ms']}ms -> nn-learning-rate-input carried value = {val!r} (present={found})")
    after = is_disabled(page, "apply-params-button")
    log(f"  Apply disabled after typing = {after!r}")
    log(f"  DOM value = {input_value(page, 'nn-learning-rate-input')!r}")
    carried = [_input_value_in_body(f["body"], "nn-learning-rate-input")[1] for f in fires]
    got = any(str(v) == probe for v in carried)
    log(f"  ==> VERDICT: Dash {'RECEIVED' if got else 'did NOT receive'} the typed value {probe} (carried={carried[-3:]})")


def step_2f(page, ctx):
    """Full causal chain for the numeric field: type -> what Dash holds -> what Apply POSTs.

    Widened window (12 s of polling) so a late debounce/corrective fire cannot
    be missed, then an actual Apply so the consequence is observed end-to-end
    in the canopy server log rather than inferred.
    """
    log("=== W3-02f: type -> Dash value -> Apply consequence (full chain) ===")
    cap = ctx["_capture"]
    _fresh(page)
    page.wait_for_timeout(4000)

    probe = "0.0733"
    log(f"  settled baseline: Apply disabled={is_disabled(page, 'apply-params-button')!r}, LR DOM={input_value(page, 'nn-learning-rate-input')!r}")
    _, st0 = http_get("/api/state")
    log(f"  /api/state nn_learning_rate before = {st0.get('nn_learning_rate')!r}")

    mark = len(cap)
    page.click("#nn-learning-rate-input")
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type(probe, delay=100)
    page.wait_for_timeout(1200)
    page.keyboard.press("Tab")

    # Poll a wide window so a late corrective fire cannot be missed.
    for i in range(12):
        page.wait_for_timeout(1000)
        fires = [c for c in cap[mark:] if "_dash-update-component" in c["url"] and '"id":"apply-params-button"' in (c["body"] or "")]
        if i in (2, 5, 11):
            vals = [_input_value_in_body(f["body"], "nn-learning-rate-input")[1] for f in fires]
            log(f"    +{i + 1}s: fires={len(fires)} carried={vals}")
    fires = [c for c in cap[mark:] if "_dash-update-component" in c["url"] and '"id":"apply-params-button"' in (c["body"] or "")]
    carried = [_input_value_in_body(f["body"], "nn-learning-rate-input")[1] for f in fires]
    log(f"  TOTAL fires={len(fires)}; carried values={carried}")
    log(f"  Apply disabled={is_disabled(page, 'apply-params-button')!r}; DOM={input_value(page, 'nn-learning-rate-input')!r}")

    # Now follow through: click Apply and read the server-side consequence.
    srv_mark = log_size()
    page.locator("#apply-params-button").scroll_into_view_if_needed()
    page.wait_for_timeout(600)
    page.click("#apply-params-button")
    page.wait_for_timeout(7000)
    log(f"  #params-status = {text_of(page, 'params-status')!r}")
    for ln in log_since(srv_mark, ("Parameters applied", "Failed to apply", "not confirmed", "Rate limited"))[-4:]:
        log(f"    SRV {ln[:800]}")
    _, st1 = http_get("/api/state")
    log(f"  /api/state nn_learning_rate after Apply = {st1.get('nn_learning_rate')!r} (typed {probe}, was {st0.get('nn_learning_rate')!r})")


def step_2g(page, ctx):
    """Confirmation: mount carries the REAL value; typing turns it to None.

    Rules out "the State was None all along" -- the alternative explanation for
    the 0.01 default substitution at dashboard_manager.py:6975. Also checks a
    second numeric field so the finding is not learning-rate-specific.
    """
    log("=== W3-02g: mount value vs post-typing value (and a 2nd field) ===")
    cap = ctx["_capture"]
    mark_mount = len(cap)
    _fresh(page)
    page.wait_for_timeout(6000)

    def fires(since):
        return [c for c in cap[since:] if "_dash-update-component" in c["url"] and '"id":"apply-params-button"' in (c["body"] or "")]

    mount_fires = fires(mark_mount)
    log(f"  MOUNT: track_param_changes fires={len(mount_fires)}")
    for f in mount_fires[:2]:
        _, lr = _input_value_in_body(f["body"], "nn-learning-rate-input")
        _, pat = _input_value_in_body(f["body"], "nn-patience-input")
        log(f"    mount fire t={f['t_ms']}ms: nn-learning-rate-input={lr!r}  nn-patience-input={pat!r}")
    log(f"  MOUNT: Apply disabled={is_disabled(page, 'apply-params-button')!r} (disabled => State matched the store, i.e. NOT None)")

    for field, probe in (("nn-learning-rate-input", "0.0655"), ("nn-patience-input", "42")):
        mark = len(cap)
        log(f"  --- typing {probe} into #{field} ---")
        page.locator(f"#{field}").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.click(f"#{field}")
        page.keyboard.press("ControlOrMeta+a")
        page.keyboard.type(probe, delay=100)
        page.wait_for_timeout(1200)
        page.keyboard.press("Tab")
        page.wait_for_timeout(5000)
        fs = fires(mark)
        vals = [_input_value_in_body(f["body"], field)[1] for f in fs]
        log(f"    fires={len(fs)}; #{field} carried={vals}; DOM={input_value(page, field)!r}; Apply disabled={is_disabled(page, 'apply-params-button')!r}")


def step_2h(page, ctx):
    """Step-grid hypothesis: is the None caused by HTML5 step validity?

    #nn-learning-rate-input declares step=0.001 but min=0.0001 (MIN_LEARNING_RATE),
    so a 4-decimal value the min advertises as legal is OFF the step grid. An
    off-grid number input reports value '' -> Dash State None. Control: an
    on-grid 3-decimal value must carry through intact.
    """
    log("=== W3-02h: step-grid control (on-grid vs off-grid learning rate) ===")
    cap = ctx["_capture"]

    for probe, expect in (("0.073", "on-grid (3dp, 73*0.001)"), ("0.0733", "off-grid (4dp)")):
        _fresh(page)
        page.wait_for_timeout(4000)
        mark = len(cap)
        page.locator("#nn-learning-rate-input").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.click("#nn-learning-rate-input")
        page.keyboard.press("ControlOrMeta+a")
        page.keyboard.type(probe, delay=100)
        page.wait_for_timeout(1200)
        page.keyboard.press("Tab")
        page.wait_for_timeout(5000)
        fs = [c for c in cap[mark:] if "_dash-update-component" in c["url"] and '"id":"apply-params-button"' in (c["body"] or "")]
        vals = [_input_value_in_body(f["body"], "nn-learning-rate-input")[1] for f in fs]
        validity = page.evaluate(
            """() => { const el = document.getElementById('nn-learning-rate-input');
                       return el ? {value: el.value, valid: el.validity.valid,
                                    stepMismatch: el.validity.stepMismatch,
                                    step: el.step, min: el.min, max: el.max} : null; }"""
        )
        log(f"  probe {probe!r} [{expect}] -> carried={vals}")
        log(f"    DOM validity: {validity}")


def step_grid(page, ctx):
    """Enumerate every number input and flag min/step grids that reject their own value.

    HTML5 bases step validity at ``min`` (valid = min + n*step). Where the
    backend-seeded value is itself a stepMismatch, ANY user edit of that field
    yields Dash State None -- and the apply handler then substitutes the
    hardcoded default (dashboard_manager.py:6973-6999).
    """
    log("=== GRID probe: number inputs whose own value is off their step grid ===")
    _fresh(page)
    page.wait_for_timeout(4000)
    rows = page.evaluate(
        """() => Array.from(document.querySelectorAll('input[type=number]')).map(el => ({
               id: el.id, value: el.value, min: el.min, step: el.step, max: el.max,
               valid: el.validity.valid, stepMismatch: el.validity.stepMismatch }))"""
    )
    bad = [r for r in rows if r["stepMismatch"]]
    log(f"  number inputs found: {len(rows)}; stepMismatch on their OWN seeded value: {len(bad)}")
    for r in rows:
        flag = "  <== OFF-GRID" if r["stepMismatch"] else ""
        log(f"    {r['id']:<42} value={r['value']!r:<12} min={r['min']!r:<10} step={r['step']!r:<8} valid={r['valid']}{flag}")


def step_blur(page, ctx):
    """Severity discriminator: does Apply corrupt LR without the user touching it?

    Seeds a step-VALID, non-default learning rate (0.0011 = min + 1*step) via
    the API, then applies a dropdown-only change two ways:
      A. Apply clicked with focus elsewhere (no LR interaction at all)
      B. Apply clicked with the LR input focused (blur-commit re-reads it)
    If LR survives in A but not B, the corruption needs field interaction; if it
    dies in both, every params Apply rewrites it.
    """
    log("=== BLUR probe: does a dropdown-only Apply preserve a step-valid LR? ===")

    for arm, focus_lr in (("A: focus elsewhere", False), ("B: LR focused before click", True)):
        _, st = http_get("/api/state")
        seed = 0.0011  # min 0.0001 + 1 * step 0.001 -> on-grid
        http_post("/api/set_params", build_payload(st, nn_learning_rate=seed))
        _, st0 = http_get("/api/state")
        log(f"  --- {arm} --- seeded LR={st0.get('nn_learning_rate')!r}")

        _fresh(page)
        page.wait_for_timeout(4000)
        val = page.evaluate(
            """() => { const el = document.getElementById('nn-learning-rate-input');
                       return {v: el.value, valid: el.validity.valid, sm: el.validity.stepMismatch}; }"""
        )
        log(f"    DOM after reload: {val}")

        cur = dropdown_value(page, "nn-optimizer-type-dropdown")
        tgt = "Adam" if (cur or "") != "Adam" else "AdamW"
        dropdown_select(page, "nn-optimizer-type-dropdown", tgt)
        page.wait_for_timeout(1500)

        if focus_lr:
            page.focus("#nn-learning-rate-input")
            page.wait_for_timeout(500)
        else:
            page.focus("#apply-params-button")
            page.wait_for_timeout(500)
        log(f"    activeElement before Apply = {page.evaluate('() => document.activeElement.id')!r}")

        srv_mark = log_size()
        page.click("#apply-params-button")
        page.wait_for_timeout(7000)
        _, st1 = http_get("/api/state")
        applied = log_since(srv_mark, ("Parameters applied",))
        lr_in_post = None
        if applied:
            import re as _re

            m = _re.search(r"'nn_learning_rate': ([0-9.eE+-]+)", applied[-1])
            lr_in_post = m.group(1) if m else None
        log(f"    optimizer {cur!r}->{tgt!r}; POSTed nn_learning_rate={lr_in_post!r}")
        log(f"    /api/state LR after = {st1.get('nn_learning_rate')!r} (seeded {seed}) -> {'PRESERVED' if st1.get('nn_learning_rate') == seed else 'OVERWRITTEN'}")


def step_blur2(page, ctx):
    """The P1-vs-P2 discriminator.

    Seeds a learning rate that is BOTH step-invalid AND != DEFAULT_LEARNING_RATE
    (0.0789), so "preserved" and "silently replaced by the default" are
    distinguishable -- the ambiguity in the earlier 0.01 run. Then applies a
    dropdown-only change without ever editing the LR field.
    """
    log("=== BLUR2: off-grid, non-default LR + dropdown-only Apply (no LR edit) ===")
    seed = 0.0789  # off-grid (stepMismatch) AND != DEFAULT_LEARNING_RATE 0.01

    for arm, focus_lr in (("A: focus elsewhere", False), ("B: LR focused (blur re-read)", True)):
        _, st = http_get("/api/state")
        http_post("/api/set_params", build_payload(st, nn_learning_rate=seed))
        _, st0 = http_get("/api/state")
        log(f"  --- {arm} --- seeded LR={st0.get('nn_learning_rate')!r}")

        _fresh(page)
        page.wait_for_timeout(4000)
        val = page.evaluate(
            """() => { const el = document.getElementById('nn-learning-rate-input');
                       return {v: el.value, valid: el.validity.valid, sm: el.validity.stepMismatch}; }"""
        )
        log(f"    DOM after reload: {val}")

        cur = dropdown_value(page, "nn-optimizer-type-dropdown")
        tgt = "Adam" if (cur or "") != "Adam" else "AdamW"
        dropdown_select(page, "nn-optimizer-type-dropdown", tgt)
        page.wait_for_timeout(1500)
        page.focus("#nn-learning-rate-input" if focus_lr else "#apply-params-button")
        page.wait_for_timeout(500)

        srv_mark = log_size()
        page.click("#apply-params-button")
        page.wait_for_timeout(7000)
        _, st1 = http_get("/api/state")
        applied = log_since(srv_mark, ("Parameters applied",))
        lr_posted = None
        if applied:
            import re as _re

            m = _re.search(r"'nn_learning_rate': ([0-9.eE+-]+)", applied[-1])
            lr_posted = m.group(1) if m else None
        after = st1.get("nn_learning_rate")
        verdict = "PRESERVED" if after == seed else f"OVERWRITTEN -> {after!r}"
        log(f"    POSTed nn_learning_rate={lr_posted!r}; /api/state after={after!r} (seeded {seed}) -> {verdict}")


def step_pos(page, ctx):
    """Positive control: an ON-GRID typed learning rate must commit and apply.

    Isolates the cause to the step grid rather than the field/widget: 0.0021 is
    min(0.0001) + 2*step(0.001), the only kind of value the field accepts.
    """
    log("=== POS control: on-grid typed learning rate (0.0021) ===")
    cap = ctx["_capture"]
    _fresh(page)
    page.wait_for_timeout(4000)
    probe = "0.0021"
    mark = len(cap)
    page.locator("#nn-learning-rate-input").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    page.click("#nn-learning-rate-input")
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type(probe, delay=100)
    page.wait_for_timeout(1200)
    page.keyboard.press("Tab")
    page.wait_for_timeout(5000)
    fs = [c for c in cap[mark:] if "_dash-update-component" in c["url"] and '"id":"apply-params-button"' in (c["body"] or "")]
    vals = [_input_value_in_body(f["body"], "nn-learning-rate-input")[1] for f in fs]
    validity = page.evaluate(
        """() => { const el = document.getElementById('nn-learning-rate-input');
                   return {v: el.value, valid: el.validity.valid, sm: el.validity.stepMismatch}; }"""
    )
    log(f"  typed {probe}: carried={vals}; DOM validity={validity}")

    srv_mark = log_size()
    page.click("#apply-params-button")
    page.wait_for_timeout(7000)
    _, st = http_get("/api/state")
    applied = log_since(srv_mark, ("Parameters applied",))
    lr_posted = None
    if applied:
        import re as _re

        m = _re.search(r"'nn_learning_rate': ([0-9.eE+-]+)", applied[-1])
        lr_posted = m.group(1) if m else None
    log(f"  after Apply: POSTed nn_learning_rate={lr_posted!r}; /api/state={st.get('nn_learning_rate')!r}")
    log(f"  #params-status = {text_of(page, 'params-status')!r}")
    log(f"  ==> on-grid typed value {'COMMITTED correctly' if st.get('nn_learning_rate') == 0.0021 else 'did NOT commit'}")


def step_restore(page, ctx):
    """Cleanup: put the sidebar params back to the segment-8 starting baseline."""
    log("=== RESTORE: return params to the captured baseline ===")
    _, st = http_get("/api/state")
    payload = build_payload(st, nn_learning_rate=0.1, nn_optimizer_type="Adam", nn_activation_function_name="Tanh")
    code, _ = http_post("/api/set_params", payload)
    _, st2 = http_get("/api/state")
    log(f"  POST -> {code}; nn_learning_rate={st2.get('nn_learning_rate')!r} nn_optimizer_type={st2.get('nn_optimizer_type')!r} nn_activation_function_name={st2.get('nn_activation_function_name')!r}")


def step_2d(page, ctx):
    """Mechanism probe: does the BROWSER ever send the typed numeric value?

    Controlled A/B on one page load, against the same callback
    (``track_param_changes``, dashboard_manager.py:4385-4430):
      A. real keystrokes into #nn-learning-rate-input  (numeric dbc.Input)
      B. a dcc.Dropdown change on #nn-optimizer-type-dropdown
    If A produces no ``_dash-update-component`` naming the input while B does,
    the value never leaves the browser -- a widget-level failure, not a
    server-side one.
    """
    log("=== W3-02d: mechanism A/B -- does the browser emit the numeric value? ===")
    cap = ctx["_capture"]
    _fresh(page)

    def dash_reqs_naming(needle, since):
        return [c for c in cap[since:] if "_dash-update-component" in c["url"] and needle in (c["body"] or "")]

    # --- A: numeric input, real keystrokes ---
    mark_a = len(cap)
    page.click("#nn-learning-rate-input")
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type("0.0733", delay=100)
    page.wait_for_timeout(1000)
    page.keyboard.press("Tab")
    page.wait_for_timeout(3000)
    a_hits = dash_reqs_naming("nn-learning-rate-input", mark_a)
    a_total = len([c for c in cap[mark_a:] if "_dash-update-component" in c["url"]])
    log(f"  [A numeric] dash-update requests total={a_total}, naming nn-learning-rate-input={len(a_hits)}")
    for h in a_hits[:3]:
        log(f"    A-BODY {h['body'][:300]}")
    log(f"  [A numeric] Apply disabled now = {is_disabled(page, 'apply-params-button')!r}")

    # --- B: dropdown, same callback ---
    mark_b = len(cap)
    cur = dropdown_value(page, "nn-optimizer-type-dropdown")
    tgt = "SGD" if (cur or "") != "SGD" else "Adam"
    dropdown_select(page, "nn-optimizer-type-dropdown", tgt)
    page.wait_for_timeout(3000)
    b_hits = dash_reqs_naming("nn-optimizer-type-dropdown", mark_b)
    b_total = len([c for c in cap[mark_b:] if "_dash-update-component" in c["url"]])
    log(f"  [B dropdown] {cur!r} -> {tgt!r}; dash-update total={b_total}, naming nn-optimizer-type-dropdown={len(b_hits)}")
    for h in b_hits[:2]:
        log(f"    B-BODY {h['body'][:300]}")
    log(f"  [B dropdown] Apply disabled now = {is_disabled(page, 'apply-params-button')!r}")


def step_dom(page, ctx):
    """Markup probe -- learn how dcc.Dropdown actually renders in this build."""
    log("=== DOM probe: dropdown + apply-button markup ===")
    for dd in ("nn-optimizer-type-dropdown", "nn-init-output-weights-dropdown"):
        html = page.evaluate(
            """(id) => { const el = document.getElementById(id); return el ? el.outerHTML : '<<absent>>'; }""",
            dd,
        )
        log(f"  #{dd} outerHTML[:900] =\n{html[:900]}\n")
    btn = page.evaluate(
        """() => { const el = document.getElementById('apply-params-button');
                   return el ? {tag: el.tagName, disabled: el.disabled, cls: el.className,
                                attr: el.getAttribute('disabled')} : null; }"""
    )
    log(f"  #apply-params-button = {btn}")
    st = page.evaluate(
        """() => { const el = document.getElementById('params-status');
                   return el ? el.innerText.slice(0,200) : null; }"""
    )
    log(f"  #params-status = {st!r}")


def step_6(page, ctx):
    log("=== W3-06: browser-only dirty check via a real dropdown ===")
    _fresh(page)
    before = is_disabled(page, "apply-params-button")
    cur = dropdown_value(page, "nn-optimizer-type-dropdown")
    log(f"  baseline: Apply disabled={before!r}, optimizer={cur!r}")
    target = "AdamW" if (cur or "").strip() != "AdamW" else "SGD"
    ok = dropdown_select(page, "nn-optimizer-type-dropdown", target)
    page.wait_for_timeout(1200)
    after = is_disabled(page, "apply-params-button")
    log(f"  selected {target!r} (ok={ok}); optimizer now={dropdown_value(page, 'nn-optimizer-type-dropdown')!r}")
    log(f"  Apply disabled={after!r} -> {'ENABLED (expected)' if after is False else 'STILL DISABLED (unexpected)'}")
    ctx["optimizer_target"] = target


def step_7(page, ctx):
    """Click Apply; prove blur-first + exactly one POST from two sides."""
    log("=== W3-07: click #apply-params-button -> blur, then exactly one POST ===")
    mark = log_size()
    ctx["_capture_len_at_7"] = len(ctx.get("_capture", []))

    # Focus a numeric field so the blur-commit has something to blur.
    page.locator("#nn-learning-rate-input").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    page.focus("#nn-learning-rate-input")
    active_before = page.evaluate("() => document.activeElement ? document.activeElement.id : null")
    log(f"  document.activeElement before click = {active_before!r}")

    page.locator("#apply-params-button").scroll_into_view_if_needed()
    page.wait_for_timeout(600)
    page.click("#apply-params-button")
    page.wait_for_timeout(400)
    active_after = page.evaluate("() => document.activeElement ? document.activeElement.id : null")
    log(f"  document.activeElement right after click = {active_after!r} (blur-commit sink fires on n_clicks)")
    page.wait_for_timeout(6000)

    srv = log_since(mark, ("Parameters applied", "Failed to apply", "Rate limited", "not confirmed"))
    log(f"  canopy server log lines since click: {len(srv)}")
    for ln in srv[-6:]:
        log(f"    SRV {ln[:700]}")
    ctx["_srv_apply"] = srv


def step_8(page, ctx):
    log("=== W3-08: read #params-status literal string ===")
    txt = text_of(page, "params-status")
    log(f"  #params-status = {txt!r}")
    _, st = http_get("/api/state")
    log(f"  /api/state nn_learning_rate={st.get('nn_learning_rate')!r} nn_optimizer_type={st.get('nn_optimizer_type')!r}")


def step_16(page, ctx):
    """DIVERGENCE probe D-2 — init-output-weights is absent from dirty tracking."""
    log("=== W3-16: D-2 probe -- #nn-init-output-weights-dropdown must NOT dirty Apply ===")
    _fresh(page)
    before = is_disabled(page, "apply-params-button")
    cur = dropdown_value(page, "nn-init-output-weights-dropdown")
    log(f"  baseline: Apply disabled={before!r}, init_output_weights={cur!r}")
    target = "Random" if (cur or "").strip().lower() != "random" else "Zero"
    ok = dropdown_select(page, "nn-init-output-weights-dropdown", target)
    page.wait_for_timeout(1500)
    after = is_disabled(page, "apply-params-button")
    log(f"  selected {target!r} (ok={ok}); now={dropdown_value(page, 'nn-init-output-weights-dropdown')!r}")
    log(f"  Apply disabled={after!r} -> D-2 {'CONFIRMED (stays disabled)' if after is not False else 'NOT reproduced (became enabled)'}")


STEPS = {
    "1": step_1,
    "2": step_2,
    "2b": step_2b,
    "2c": step_2c,
    "2d": step_2d,
    "2e": step_2e,
    "2f": step_2f,
    "2g": step_2g,
    "2h": step_2h,
    "grid": step_grid,
    "blur": step_blur,
    "blur2": step_blur2,
    "pos": step_pos,
    "restore": step_restore,
    "dom": step_dom,
    "3": step_3,
    "4": step_4,
    "5": step_5,
    "6": step_6,
    "7": step_7,
    "8": step_8,
    "16": step_16,
}


def parse_steps(spec: str) -> list[str]:
    out: list[str] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(str(i) for i in range(int(a), int(b) + 1))
        else:
            out.append(part)
    return [s for s in out if s in STEPS]


def main() -> int:
    ap = argparse.ArgumentParser(description="W3 parameter apply round-trip live driver")
    ap.add_argument("--steps", default="1-5", help="e.g. '1-5' or '1,3,7'")
    ap.add_argument("--dump-net", action="store_true", help="print captured browser requests at the end")
    args = ap.parse_args()

    steps = parse_steps(args.steps)
    if not steps:
        print(f"no runnable steps in {args.steps!r}; known: {sorted(STEPS)}", file=sys.stderr)
        return 2

    from playwright.sync_api import sync_playwright

    capture: list = []
    ctx: dict = {"_capture": capture}
    log(f"canopy={CANOPY} steps={steps}")
    mark = log_size()

    with sync_playwright() as pw:
        browser, bctx, page = open_dashboard(pw, capture)
        try:
            for s in steps:
                STEPS[s](page, ctx)
        finally:
            server_lines = log_since(mark, ("Parameters applied", "Failed to apply", "set_params", "Rate limited"))
            if server_lines:
                log(f"--- canopy server log ({len(server_lines)} matching lines since start) ---")
                for ln in server_lines[-25:]:
                    log(f"  SRV {ln[:400]}")
            else:
                log("--- canopy server log: no matching lines since start ---")
            if args.dump_net:
                log(f"--- browser requests captured: {len(capture)} ---")
                for c in capture:
                    log(f"  NET {c['t_ms']:>7d} {c['method']} {c['url']} body={c['body'][:300]}")
            bctx.close()
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
