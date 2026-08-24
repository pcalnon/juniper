#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   E2E validation arc — F-CANOPY-027 forensics
# File Name:     e2e_f027_cleanroom.py
# Author:        Paul Calnon
# Version:       1.0.0
# License:       MIT License
#
# Description:
#    Clean-room reproduction attempt for F-CANOPY-027.
#
#    Every mechanism refuted so far was refuted IN SITU, against the full canopy dashboard.
#    This script goes the other way: it builds the smallest possible app that has canopy's
#    `visualization-tabs` SHAPE, on the same dash / dash-bootstrap-components versions, and
#    asks whether the symptom appears at all.
#
#    Shape reproduced (juniper-canopy/src/frontend/dashboard_manager.py:1705-1712, :2363-2370):
#      * a `dbc.Tabs(id="visualization-tabs", active_tab=<first>)` holding N `dbc.Tab` panes
#      * each pane owns  dcc.Interval -> (callback) -> dcc.Store -> (callback) -> html.Div
#        i.e. exactly the candidate-metrics writer/consumer chain
#      * OPTIONALLY a `model-class-store` whose mount-time hydration rewrites
#        `visualization-tabs.children` exactly once, as canopy's `suppress_cascade_tabs` does
#
#    The surviving hypothesis from the ledger is that panes which are never the initially-active
#    pane lose their client-side observer wiring. `--rebuild` / `--no-rebuild` isolates whether
#    the children-rebuild is what breaks them.
#
# Usage:
#    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_f027_cleanroom.py
#    ... --no-rebuild          # omit the model-class children rebuild
#    ... --serve               # run only the server (used internally by the driver)
#
#####################################################################################################################################################################################################
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from typing import Any, Dict, List

DEFAULT_PORT = 8399
# dash_renderer.dev.js:2846 -- available = Math.max(0, 12 - executing.length - watched.length)
RENDERER_SLOT_CAP = 12


def pane_names(count: int) -> List[str]:
    return [f"p{i:02d}" for i in range(count)]


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Server side
# ─────────────────────────────────────────────────────────────────────────────────────────────
def build_app(rebuild: bool, panes: List[str], delay: float):
    import dash
    import dash_bootstrap_components as dbc
    from dash import Input, Output, dcc, html

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

    def pane_layout(pane: str):
        """One pane = the candidate-metrics chain: interval -> store -> rendered div."""
        return html.Div(
            [
                html.H5(f"pane {pane}"),
                html.Div("INIT", id=f"{pane}-out"),
                dcc.Store(id=f"{pane}-store", data={}),
                dcc.Interval(id=f"{pane}-iv", interval=500, n_intervals=0),
            ],
            style={"padding": "15px"},
        )

    def all_tabs():
        return [dbc.Tab(pane_layout(pane), label=pane.title(), tab_id=pane) for pane in panes]

    children: List[Any] = [
        dbc.Tabs(all_tabs(), id="visualization-tabs", active_tab=panes[0]),
        dcc.Store(id="model-class-store", storage_type="memory", data="live"),
        dcc.Interval(id="hydrate-iv", interval=1200, n_intervals=0, max_intervals=1),
    ]
    app.layout = html.Div(children)

    # Per-pane writer + consumer, mirroring candidate_metrics_panel.register_callbacks.
    for pane in panes:

        def _mk(pane_id: str):
            @app.callback(
                Output(f"{pane_id}-store", "data"),
                Input(f"{pane_id}-iv", "n_intervals"),
                prevent_initial_call=False,
            )
            def _write(n_intervals):
                # A slow writer is what makes a 1 Hz poller unable to finish inside
                # its own period once the renderer's 12 slots are contended.
                if delay:
                    time.sleep(delay)
                return {"n": n_intervals, "pane": pane_id}

            @app.callback(
                Output(f"{pane_id}-out", "children"),
                Input(f"{pane_id}-store", "data"),
                prevent_initial_call=False,
            )
            def _render(data):
                if not data:
                    return "INIT"
                return f"n={data.get('n')}"

        _mk(pane)

    # canopy's model-class hydration: one mount-time write of the SAME value ("live"),
    # which fires suppress_cascade_tabs once and replaces visualization-tabs.children.
    @app.callback(
        Output("model-class-store", "data"),
        Input("hydrate-iv", "n_intervals"),
        prevent_initial_call=True,
    )
    def _hydrate(_n):
        return "live"

    if rebuild:

        @app.callback(
            Output("visualization-tabs", "children"),
            Input("model-class-store", "data"),
            prevent_initial_call=True,
        )
        def _suppress(_model_class):
            return all_tabs()

    return app


def serve(port: int, rebuild: bool, panes: List[str], delay: float) -> None:
    app = build_app(rebuild=rebuild, panes=panes, delay=delay)
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Driver side
# ─────────────────────────────────────────────────────────────────────────────────────────────
def drive(port: int, settle: float, per_tab: float, panes: List[str]) -> Dict[str, Any]:
    from playwright.sync_api import sync_playwright

    url = f"http://127.0.0.1:{port}/"
    result: Dict[str, Any] = {"url": url, "panes": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        errors: List[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        # NOT networkidle — the per-pane dcc.Intervals poll forever, so it never fires.
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_selector("#visualization-tabs", timeout=30_000)

        # Let the mount burst AND the children-rebuild land.
        time.sleep(settle)

        for pane in panes:
            entry: Dict[str, Any] = {}
            # Value while the pane has never been activated (dbc renders all panes; hidden != absent).
            entry["before_click"] = page.evaluate(
                "id => { const el = document.getElementById(id); return el ? el.textContent : null; }",
                f"{pane}-out",
            )

            # Activate the pane by clicking its tab link, then poll for a CHANGE (never a fixed sleep).
            page.locator(f"#visualization-tabs >> a:has-text('{pane.title()}')").first.click()
            deadline = time.time() + per_tab
            seen: List[str] = []
            while time.time() < deadline:
                txt = page.evaluate(
                    "id => { const el = document.getElementById(id); return el ? el.textContent : null; }",
                    f"{pane}-out",
                )
                if txt is not None and (not seen or seen[-1] != txt):
                    seen.append(txt)
                if len(seen) >= 3:  # INIT -> n=x -> n=y  is enough to prove the chain is live
                    break
                time.sleep(0.25)
            entry["observed"] = seen
            entry["after_click"] = seen[-1] if seen else None
            entry["live"] = len([s for s in seen if s.startswith("n=")]) >= 1 and len(set(seen)) >= 2
            result["panes"][pane] = entry

        result["page_errors"] = errors
        browser.close()
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="F-CANOPY-027 clean-room reproduction")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--serve", action="store_true", help="run the Dash server only")
    ap.add_argument("--no-rebuild", dest="rebuild", action="store_false", help="omit the children rebuild")
    ap.add_argument("--settle", type=float, default=6.0)
    ap.add_argument("--per-tab", type=float, default=8.0)
    ap.add_argument("--panes", type=int, default=5, help="number of tab panes (2 callbacks each)")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds the writer callback sleeps")
    args = ap.parse_args()

    panes = pane_names(args.panes)

    if args.serve:
        serve(args.port, args.rebuild, panes, args.delay)
        return 0

    cmd = [sys.executable, __file__, "--serve", "--port", str(args.port),
           "--panes", str(args.panes), "--delay", str(args.delay)]
    if not args.rebuild:
        cmd.append("--no-rebuild")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        # Wait for the port rather than sleeping blind.
        import urllib.error
        import urllib.request

        deadline = time.time() + 45
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{args.port}/", timeout=1).read(1)
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.4)
        else:
            print("server did not come up", file=sys.stderr)
            return 2

        result = drive(args.port, args.settle, args.per_tab, panes)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    result["rebuild"] = args.rebuild
    result["panes_n"] = args.panes
    result["delay"] = args.delay
    print()
    print(f"=== panes={args.panes} (callbacks={2*args.panes}) delay={args.delay}s "
          f"rebuild={args.rebuild} renderer_cap={RENDERER_SLOT_CAP} ===")
    for pane, entry in result["panes"].items():
        flag = "LIVE" if entry["live"] else "DEAD"
        print(f"  {pane:<8} {flag:<5} before_click={entry['before_click']!r:<12} observed={entry['observed']}")
    dead = [p for p, e in result["panes"].items() if not e["live"]]
    print(f"\ndead panes: {dead if dead else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
