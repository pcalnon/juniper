#!/usr/bin/env python3
"""Round-3 review harness: drive the REAL CascorServiceAdapter against a stub that
serves every reachable response shape, and evaluate revision 3's §5.1 POSITIVE
classifier table against each.

Project      : Juniper - juniper-ml (review harness for juniper-canopy X7 design rev 3)
Sub-Project  : X7 event-loop-blocking remediation design, round-3 adversarial review
Author       : Paul Calnon
License      : MIT

Read-only against juniper-canopy and juniper-cascor.

The decisive addition over the r2 census: the stub serves juniper-cascor's REAL
``lifecycle.get_status()`` shape (juniper-cascor/src/api/lifecycle/manager.py:2758-2789
wrapped by success_response(), src/api/models/common.py:116), so we can ask what
"the expected status field" actually is on a healthy backend.

Run:  conda run -n JuniperCanopy1 python util/ad-hoc/2026-09-03_x7_r3_classifier_census.py
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

CASE = {"mode": "real_healthy_idle"}

# juniper-cascor/src/api/lifecycle/manager.py:2768-2789 — verbatim key set.
REAL_STATUS_IDLE = {
    "state_machine": {"state": "IDLE", "started": False},
    "monitor": {"epoch": 0},
    "training_state": {"input_size": 2, "output_size": 1},
    "network_loaded": True,
    "training_active": False,
    "pending_dataset": None,
    "completion_reason": None,
    "metrics_clear_undo_available": False,
}
REAL_STATUS_LIVE = {
    "state_machine": {"state": "TRAINING", "started": True},
    "monitor": {"epoch": 412},
    "training_state": {"input_size": 2, "output_size": 1},
    "network_loaded": True,
    "training_active": True,
    "pending_dataset": None,
    "completion_reason": None,
    "metrics_clear_undo_available": False,
    # training.py:219-220 adds these when ws_manager is present
    "snapshot_seq": 91,
    "server_instance_id": "abc123",
}
# A run that finished. Still a perfectly healthy backend.
REAL_STATUS_STOPPED = dict(REAL_STATUS_IDLE, state_machine={"state": "COMPLETED", "started": False}, completion_reason="below_threshold")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        raw = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _env(self, data):
        return json.dumps({"status": "success", "data": data})

    def do_GET(self):
        m = CASE["mode"]
        if m == "real_healthy_idle":
            self._send(200, self._env(REAL_STATUS_IDLE))
        elif m == "real_healthy_live":
            self._send(200, self._env(REAL_STATUS_LIVE))
        elif m == "real_healthy_stopped":
            self._send(200, self._env(REAL_STATUS_STOPPED))
        elif m == "half_dead_empty":
            self._send(200, self._env({}))
        elif m == "half_dead_state_only":
            self._send(200, self._env({"state": "IDLE"}))
        elif m == "data_null":
            self._send(200, self._env(None))
        elif m == "data_list":
            self._send(200, self._env([]))
        elif m == "top_null":
            self._send(200, "null")
        elif m == "top_list":
            self._send(200, "[]")
        elif m == "no_envelope":
            self._send(200, json.dumps(REAL_STATUS_LIVE))
        elif m == "err_field_but_healthy":
            self._send(200, self._env(dict(REAL_STATUS_LIVE, error="candidate pool diverged")))
        elif m == "err_field_none":
            self._send(200, self._env(dict(REAL_STATUS_LIVE, error=None)))
        elif m == "err_field_empty":
            self._send(200, self._env(dict(REAL_STATUS_LIVE, error="")))
        elif m == "cascor_error_envelope_200":
            # cascor error_response() shape returned with a 200 (proxy rewrite / partial)
            self._send(200, json.dumps({"status": "error", "error": {"code": "X", "message": "y"}}))
        elif m == "http_500":
            self._send(500, json.dumps({"detail": "boom"}))
        elif m == "http_503":
            self._send(503, json.dumps({"detail": "Lifecycle manager not initialized"}))
        elif m == "http_404":
            self._send(404, json.dumps({"detail": "nope"}))
        elif m == "http_401":
            self._send(401, json.dumps({"detail": "bad key"}))
        elif m == "bad_json":
            self._send(200, "<html>502 Bad Gateway</html>", ctype="text/html")
        elif m == "empty_body":
            self._send(200, "")
        else:
            self._send(200, self._env({}))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


# --- revision 3 §5.1's table, mechanised. -----------------------------------
# The table's success row reads: "dict, no truthy error, carries the expected
# field(s)". The document NEVER NAMES the field, so we evaluate every candidate
# a reader could plausibly pick.
CANDIDATE_FIELDS = {
    "is_training": ("is_training",),
    "training_active": ("training_active",),
    "state_machine": ("state_machine",),
    "is_training|training_active": ("is_training", "training_active"),
}


def classify(payload, expected_fields):
    """Revision 3 §5.1, positive classification."""
    if payload is None:
        return "UNREACHABLE"
    if not isinstance(payload, dict):
        return "UNREACHABLE"
    err = payload.get("error")
    if err:
        return "UNREACHABLE"
    for f in expected_fields:
        if f in payload:
            return "OK"
    return "UNREACHABLE"


TRUTH = {
    # mode -> is the backend genuinely healthy & reachable?
    "real_healthy_idle": True,
    "real_healthy_live": True,
    "real_healthy_stopped": True,
    "half_dead_empty": False,
    "half_dead_state_only": False,
    "data_null": False,
    "data_list": False,
    "top_null": False,
    "top_list": False,
    "no_envelope": True,
    "err_field_but_healthy": True,
    "err_field_none": True,
    "err_field_empty": True,
    "cascor_error_envelope_200": False,
    "http_500": False,
    "http_503": False,
    "http_404": False,
    "http_401": False,
    "bad_json": False,
    "empty_body": False,
}


def main():
    from backend.cascor_service_adapter import CascorServiceAdapter  # noqa: E402

    port = free_port()
    srv = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    print("=" * 130)
    print("A. WHAT get_training_status() ACTUALLY RETURNS, and how §5.1 classifies it")
    print("=" * 130)
    hdr = f"{'case':<28}{'healthy?':<10}{'returned type':<15}{'keys / value':<62}"
    print(hdr + "".join(f"{k:<26}" for k in CANDIDATE_FIELDS))
    print("-" * 200)

    wrong = []
    for mode in TRUTH:
        CASE["mode"] = mode
        ad = CascorServiceAdapter(service_url=f"http://127.0.0.1:{port}")
        raised = None
        payload = None
        try:
            payload = ad.get_training_status()
        except BaseException as exc:  # noqa: BLE001
            raised = type(exc).__name__
        if raised:
            desc = f"RAISED {raised}"
            cells = "".join(f"{'(escapes refresher)':<26}" for _ in CANDIDATE_FIELDS)
            print(f"{mode:<28}{str(TRUTH[mode]):<10}{'-':<15}{desc:<62}{cells}")
            continue
        if isinstance(payload, dict):
            shown = ",".join(sorted(payload.keys()))[:58]
        else:
            shown = repr(payload)[:58]
        cells = ""
        for name, fields in CANDIDATE_FIELDS.items():
            cls = classify(payload, fields)
            ok = cls == "OK"
            bad = ok != TRUTH[mode]
            cells += f"{(cls + ('  <== WRONG' if bad else '')):<26}"
            if bad:
                wrong.append((mode, name, cls, TRUTH[mode], payload))
        print(f"{mode:<28}{str(TRUTH[mode]):<10}{type(payload).__name__:<15}{shown:<62}{cells}")

    print()
    print("=" * 130)
    print("B. MISCLASSIFICATIONS, grouped by which 'expected status field' the implementer picks")
    print("=" * 130)
    by_field = {}
    for mode, field, cls, truth, payload in wrong:
        by_field.setdefault(field, []).append((mode, cls, truth))
    for field in CANDIDATE_FIELDS:
        rows = by_field.get(field, [])
        print(f"\n  expected field = {field!r}:  {len(rows)} misclassification(s)")
        for mode, cls, truth in rows:
            kind = "HEALTHY -> UNREACHABLE" if truth else "DEAD -> OK"
            print(f"      {mode:<28} classified {cls:<14} truth healthy={truth}   [{kind}]")

    print()
    print("=" * 130)
    print("C. Does a healthy cascor payload contain 'is_training'?  (the field the FAILURE path invents)")
    print("=" * 130)
    CASE["mode"] = "real_healthy_live"
    ad = CascorServiceAdapter(service_url=f"http://127.0.0.1:{port}")
    good = ad.get_training_status()
    print(f"  healthy keys      : {sorted(good.keys())}")
    print(f"  'is_training' in it? {'is_training' in good}")
    dead_port = free_port()
    ad_dead = CascorServiceAdapter(service_url=f"http://127.0.0.1:{dead_port}")
    try:
        bad = ad_dead.get_training_status()
    except BaseException as exc:  # noqa: BLE001
        bad = f"RAISED {type(exc).__name__}"
    print(f"  failure payload   : {bad!r}")
    print("  => 'is_training' is present ONLY on the failure path; 'error' only on the failure path.")

    print()
    print("=" * 130)
    print("D. Shared-breaker success feed: does moving the poller to a DEDICATED breaker")
    print("   change failure semantics for the OTHER callers of the shared _cb?")
    print("=" * 130)
    CASE["mode"] = "real_healthy_live"
    ad2 = CascorServiceAdapter(service_url=f"http://127.0.0.1:{port}")
    print("  today: interleaved poll(ok) + network(fail) — the poll RESETS the shared counter")
    for i in range(1, 13):
        CASE["mode"] = "http_500"
        try:
            ad2.get_network_data()
        except BaseException:  # noqa: BLE001
            pass
        f_after_net = ad2._circuit.failure_count
        CASE["mode"] = "real_healthy_live"
        try:
            ad2.get_training_status()
        except BaseException:  # noqa: BLE001
            pass
        print(f"    round {i:>2}: after failing get_network_data -> failures={f_after_net}; "
              f"after polling status -> failures={ad2._circuit.failure_count} state={ad2._circuit.state.value}")
        if i >= 8:
            break
    print("  after change: the poller no longer touches the shared breaker.")
    ad3 = CascorServiceAdapter(service_url=f"http://127.0.0.1:{port}")
    for i in range(1, 8):
        CASE["mode"] = "http_500"
        try:
            ad3.get_network_data()
        except BaseException:  # noqa: BLE001
            pass
        print(f"    round {i}: failures={ad3._circuit.failure_count} state={ad3._circuit.state.value}")
        if ad3._circuit.state.value == "open":
            print("    ^^ shared breaker now OPEN; every other shared-breaker caller "
                  "(extract_network_topology, get_raw_topology, get_dataset_info) is short-circuited for 60 s")
            break

    print()
    print("=" * 130)
    print("E. Dedicated-breaker recovery lag for the refresher itself (REFRESH_INTERVAL 1.0 s)")
    print("=" * 130)
    dead2 = free_port()
    ad4 = CascorServiceAdapter(service_url=f"http://127.0.0.1:{dead2}")
    t0 = time.monotonic()
    for tick in range(1, 9):
        raised = None
        payload = None
        try:
            payload = ad4.get_training_status()
        except BaseException as exc:  # noqa: BLE001
            raised = type(exc).__name__
        print(f"    tick {tick}: raised={str(raised):<26} breaker={ad4._circuit.state.value:<6} "
              f"payload={payload!r}  t={time.monotonic()-t0:5.2f}s")
    print(f"    recovery_timeout = {ad4._circuit.recovery_timeout}s, failure_threshold = {ad4._circuit.failure_threshold}")

    srv.shutdown()


if __name__ == "__main__":
    main()
