#!/usr/bin/env python3
"""Round-2 review harness: enumerate every shape CascorServiceAdapter.get_training_status()
can return, and test whether the revised design's PAYLOAD-based failure classifier
(§5.1 revision: "classify a tick as failed when the payload carries an `error` key")
is sufficient.

Project      : Juniper - juniper-ml (review harness for juniper-canopy X7 design rev 2)
Sub-Project  : X7 event-loop-blocking remediation design, round-2 adversarial review
Author       : Paul Calnon
License      : MIT

Read-only against juniper-canopy: imports the adapter, points it at a local stub
HTTP server whose response shape is controlled per-case.

Run:  conda run -n JuniperCanopy1 python util/ad-hoc/2026-09-03_x7_r2_payload_classification_census.py
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

# The case the stub server should serve, set per test.
CASE = {"mode": "ok"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def _send(self, code, body, ctype="application/json"):
        raw = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        m = CASE["mode"]
        if m == "ok":
            self._send(200, json.dumps({"data": {"is_training": True, "epoch": 412}}))
        elif m == "ok_flat":
            self._send(200, json.dumps({"is_training": True, "epoch": 412}))
        elif m == "data_null":
            self._send(200, json.dumps({"data": None}))
        elif m == "data_list":
            self._send(200, json.dumps({"data": []}))
        elif m == "top_null":
            self._send(200, "null")
        elif m == "top_list":
            self._send(200, "[]")
        elif m == "empty_dict":
            self._send(200, json.dumps({}))
        elif m == "no_keys_of_interest":
            self._send(200, json.dumps({"data": {"state": "IDLE"}}))
        elif m == "legit_error_field":
            # cascor reporting a *training* error while alive and training.
            self._send(200, json.dumps({"data": {"is_training": True, "epoch": 88, "error": "candidate pool diverged"}}))
        elif m == "legit_error_null":
            self._send(200, json.dumps({"data": {"is_training": True, "epoch": 88, "error": None}}))
        elif m == "http_500":
            self._send(500, json.dumps({"detail": "boom"}))
        elif m == "http_503":
            self._send(503, json.dumps({"detail": "unavailable"}))
        elif m == "http_404":
            self._send(404, json.dumps({"detail": "nope"}))
        elif m == "bad_json":
            self._send(200, "<html>proxy error</html>", ctype="text/html")
        elif m == "slow":
            time.sleep(5)
            self._send(200, json.dumps({"data": {"is_training": True}}))
        else:
            self._send(200, json.dumps({"data": {}}))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def classify(payload):
    """The revised design's rule, §5.1 revision: 'classify a tick as failed when the
    payload carries an `error` key (and specifically "circuit open")'."""
    try:
        has_error = "error" in payload
    except TypeError as exc:
        return f"CLASSIFIER-CRASH({type(exc).__name__})"
    return "FAILED" if has_error else "SUCCESS(->FRESH)"


def main():
    from backend.cascor_service_adapter import CascorServiceAdapter  # noqa: E402

    port = free_port()
    srv = HTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    cases = [
        ("ok", "healthy, enveloped"),
        ("ok_flat", "healthy, un-enveloped"),
        ("data_null", "200, {'data': null}"),
        ("data_list", "200, {'data': []}"),
        ("top_null", "200, body `null`"),
        ("top_list", "200, body `[]`"),
        ("empty_dict", "200, {}"),
        ("no_keys_of_interest", "200, {'data':{'state':'IDLE'}} (half-dead: no is_training)"),
        ("legit_error_field", "200, HEALTHY+TRAINING with a legit 'error' field"),
        ("legit_error_null", "200, HEALTHY+TRAINING with error=None"),
        ("http_500", "HTTP 500"),
        ("http_503", "HTTP 503"),
        ("http_404", "HTTP 404"),
        ("bad_json", "200 non-JSON (proxy/ingress error page)"),
    ]

    print(f"{'case':<22} {'raised':<26} {'type':<8} {'has error':<10} {'design classifier':<26} payload")
    print("-" * 150)
    for mode, desc in cases:
        CASE["mode"] = mode
        # Fresh adapter per case so the shared circuit breaker never carries over.
        ad = CascorServiceAdapter(service_url=f"http://127.0.0.1:{port}")
        raised = "-"
        payload = None
        try:
            payload = ad.get_training_status()
        except BaseException as exc:  # noqa: BLE001
            raised = f"{type(exc).__name__}"
        if raised != "-":
            print(f"{mode:<22} {raised:<26} {'-':<8} {'-':<10} {'(exception backstop)':<26} -")
        else:
            has = "n/a"
            try:
                has = str("error" in payload)
            except TypeError:
                has = "TypeError"
            print(f"{mode:<22} {'-':<26} {type(payload).__name__:<8} {has:<10} {classify(payload):<26} {payload!r}")

    # ------------------------------------------------------------------
    # Breaker interaction: does the FIRST failure raise, or fall back?
    # ------------------------------------------------------------------
    print()
    print("== breaker ladder against a DEAD upstream (connection refused) ==")
    dead_port = free_port()  # nothing listening
    ad = CascorServiceAdapter(service_url=f"http://127.0.0.1:{dead_port}")
    for tick in range(1, 9):
        raised = "-"
        payload = None
        t0 = time.monotonic()
        try:
            payload = ad.get_training_status()
        except BaseException as exc:  # noqa: BLE001
            raised = type(exc).__name__
        el = time.monotonic() - t0
        st = ad._circuit.state.value
        print(f"tick {tick}: raised={raised:<12} breaker={st:<10} {el:6.3f}s payload={payload!r}")

    # ------------------------------------------------------------------
    # is_training_in_progress: the method §5.5 targets. Payload-classifiable?
    # ------------------------------------------------------------------
    print()
    print("== is_training_in_progress() against DEAD upstream (the method §5.5 targets) ==")
    ad2 = CascorServiceAdapter(service_url=f"http://127.0.0.1:{dead_port}")
    for tick in range(1, 4):
        raised = "-"
        val = None
        try:
            val = ad2.is_training_in_progress()
        except BaseException as exc:  # noqa: BLE001
            raised = type(exc).__name__
        print(f"tick {tick}: raised={raised:<12} return={val!r} type={type(val).__name__}  -> payload has NO error key to classify")

    # ------------------------------------------------------------------
    # is_training_in_progress against a HEALTHY upstream + the shared breaker.
    # ------------------------------------------------------------------
    print()
    print("== breaker is SHARED across adapter methods: does a get_network_data failure open it for get_training_status? ==")
    CASE["mode"] = "ok"
    ad3 = CascorServiceAdapter(service_url=f"http://127.0.0.1:{port}")
    print(f"  healthy get_training_status -> {ad3.get_training_status()!r}  breaker={ad3._circuit.state.value}")
    CASE["mode"] = "http_500"
    for _ in range(5):
        try:
            ad3.get_network_data()
        except BaseException:  # noqa: BLE001
            pass
    print(f"  after 5 failing get_network_data(): breaker={ad3._circuit.state.value} failures={ad3._circuit.failure_count}")
    CASE["mode"] = "ok"
    out = ad3.get_training_status()
    print(f"  now healthy get_training_status -> {out!r}")
    print("  ^ if this reads 'circuit open' while the upstream is HEALTHY, payload classification marks a live backend FAILED")

    srv.shutdown()


if __name__ == "__main__":
    main()
