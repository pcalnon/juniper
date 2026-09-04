#!/usr/bin/env python3
"""Round-3 review harness #2: does §5.3's `for_ui()` / `for_status()` split show the
operator CONTRADICTORY things, and is the PR #340 "Unreachable" branch actually fed by
the path §5.3 proposes to change?

Project      : Juniper - juniper-ml (review harness for juniper-canopy X7 design rev 3)
Author       : Paul Calnon
License      : MIT

Drives the REAL chain:
    CascorServiceAdapter.get_training_status()
      -> ServiceBackend.get_status()            (src/backend/service_backend.py:165)
      -> /api/status                            (src/main.py:1311)
      -> dashboard_manager status-bar branch    (src/frontend/dashboard_manager.py:6436-6438)

Run: conda run -n JuniperCanopy1 python util/ad-hoc/2026-09-03_x7_r3_view_divergence.py
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

CANOPY_SRC = "/home/pcalnon/Development/python/Juniper/juniper-canopy/src"
if CANOPY_SRC not in sys.path:
    sys.path.insert(0, CANOPY_SRC)

CASE = {"mode": "healthy"}

REAL_LIVE = {
    "state_machine": {"status": "TRAINING", "phase": "output", "started": True},
    "monitor": {"current_epoch": 412, "current_hidden_units": 3},
    "training_state": {"input_size": 2, "output_size": 1, "max_epochs": 1000},
    "network_loaded": True,
    "training_active": True,
    "pending_dataset": None,
    "completion_reason": None,
    "metrics_clear_undo_available": False,
}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body):
        raw = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        m = CASE["mode"]
        if m == "healthy":
            self._send(200, json.dumps({"status": "success", "data": REAL_LIVE}))
        elif m == "half_dead":
            # cascor process alive, its lifecycle/state subsystem returning an
            # empty-but-shaped 200. The shape §5.1 added positive validation for.
            self._send(200, json.dumps({"status": "success", "data": {}}))
        elif m == "half_dead_partial":
            # a shaped 200 that is missing state_machine/training_active
            self._send(200, json.dumps({"status": "success", "data": {"monitor": {}, "network_loaded": True}}))
        else:
            self._send(500, json.dumps({"detail": "x"}))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def pr340_branch(status_data):
    """VERBATIM logic of src/frontend/dashboard_manager.py:6436-6438."""
    error_marker = status_data.get("error") if isinstance(status_data, dict) else None
    if error_marker:
        return f'STATUS BAR = "Unreachable" ({error_marker!r:.40})'
    # the existing elif chain, abbreviated to the branch the PR #340 comment names
    if not isinstance(status_data, dict):
        return 'STATUS BAR = "Stopped" (non-dict)'
    if status_data.get("is_running"):
        return 'STATUS BAR = "Training"'
    if status_data.get("is_paused"):
        return 'STATUS BAR = "Paused"'
    if status_data.get("completed"):
        return 'STATUS BAR = "Completed"'
    return 'STATUS BAR = "Stopped"   <-- the PR #340 defect, verbatim'


def classify_positive(payload, fields=("training_active", "state_machine")):
    """revision 3 §5.1."""
    if payload is None or not isinstance(payload, dict):
        return "UNREACHABLE"
    if payload.get("error"):
        return "UNREACHABLE"
    return "OK" if any(f in payload for f in fields) else "UNREACHABLE"


def main():
    from backend.cascor_service_adapter import CascorServiceAdapter
    from backend.service_backend import ServiceBackend

    port = free_port()
    srv = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    dead_port = free_port()

    print("=" * 118)
    print("A. THE REAL CHAIN — adapter payload -> ServiceBackend.get_status() -> the PR #340 branch")
    print("=" * 118)
    scenarios = [
        ("healthy", port, "cascor healthy + training"),
        ("dead", dead_port, "cascor STOPPED (ECONNREFUSED)"),
        ("half_dead", port, "cascor HALF-DEAD: shaped-but-empty 200"),
        ("half_dead_partial", port, "cascor HALF-DEAD: 200 missing state_machine/training_active"),
    ]
    rows = []
    for mode, p, desc in scenarios:
        CASE["mode"] = mode if mode != "dead" else "healthy"
        ad = CascorServiceAdapter(service_url=f"http://127.0.0.1:{p}")
        sb = ServiceBackend.__new__(ServiceBackend)
        sb._adapter = ad
        raw = ad.get_training_status()
        cls = classify_positive(raw)
        try:
            st = sb.get_status()
        except BaseException as exc:  # noqa: BLE001
            st = f"RAISED {type(exc).__name__}"
        bar = pr340_branch(st) if isinstance(st, dict) else str(st)
        rows.append((desc, cls, bar))
        print(f"\n  {desc}")
        print(f"    adapter.get_training_status() keys : {sorted(raw.keys()) if isinstance(raw, dict) else raw!r}")
        print(f"    §5.1 classifier                    : {cls}")
        print(f"    ServiceBackend.get_status() carries 'error'? {isinstance(st, dict) and 'error' in st}")
        print(f"    {bar}")

    print()
    print("=" * 118)
    print("B. §5.3 DIVERGENCE TABLE — what for_ui() and for_status() tell the operator, side by side")
    print("=" * 118)
    print(f"  {'upstream condition':<48}{'for_status() -> /v1/health':<30}{'for_ui() -> status bar'}")
    print("  " + "-" * 114)
    for desc, cls, bar in rows:
        health = "OK / fresh" if cls == "OK" else "stale:true + age_seconds (UNKNOWN)"
        print(f"  {desc:<48}{health:<30}{bar.replace('STATUS BAR = ', '')}")
    print()
    print("  A row where the left column says UNKNOWN and the right column says a")
    print("  DEFINITE state is a CONTRADICTION shown to the operator, and it is a")
    print("  'fresh negative' on the user-facing channel -> violates C6.")

    print()
    print("=" * 118)
    print("C. does `retries=0` remove the 3.0 s connect-retry cost the refresher would pay per tick?")
    print("=" * 118)
    from juniper_cascor_client import JuniperCascorClient

    for r, t in ((3, 30), (0, 5), (1, 5)):
        cl = JuniperCascorClient(base_url=f"http://127.0.0.1:{dead_port}", timeout=t, retries=r)
        ad = CascorServiceAdapter(service_url=f"http://127.0.0.1:{dead_port}", client=cl)
        t0 = time.monotonic()
        ad.get_training_status()
        el = time.monotonic() - t0
        print(f"    retries={r}, timeout={t}: ECONNREFUSED tick cost = {el:6.3f}s"
              f"   -> effective refresher period with REFRESH_INTERVAL=1.0s: {el + 1.0:.2f}s")

    print()
    print("=" * 118)
    print("D. is_cascor_nested — canopy ALREADY SHIPS the positive discriminator §5.1 leaves unnamed")
    print("=" * 118)
    for name, payload in (
        ("real healthy", REAL_LIVE),
        ("failure payload", {"is_training": False, "error": "boom"}),
        ("circuit-open fallback", {"is_training": False, "error": "circuit open"}),
        ("half-dead {}", {}),
        ("half-dead {'monitor':{}}", {"monitor": {}}),
    ):
        print(f"    is_cascor_nested({name:<26}) = {CascorServiceAdapter.is_cascor_nested(payload)}"
              f"   (src/backend/cascor_service_adapter.py:542 -> :1846)")

    srv.shutdown()


if __name__ == "__main__":
    main()
