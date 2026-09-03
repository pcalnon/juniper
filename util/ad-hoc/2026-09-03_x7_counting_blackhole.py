#!/usr/bin/env python
"""Counting black-hole listener for the X7 design review.

Accepts every TCP connection, reads (and counts) the bytes the peer sends, then
never replies. Unlike the plain black-hole listener it distinguishes:

  * ACCEPTS  -- TCP connections established (a connect-level retry adds one)
  * REQUESTS -- connections on which a complete HTTP request head was received
                (a read-timeout retry adds one)
  * PEAK     -- maximum simultaneously-open connections (the real concurrency bound)

Writes a JSON summary to the path given by X7_BH_STATE on SIGUSR1 or at exit,
and prints one line per event so a driver can tail it.

Usage: python 2026-09-03_x7_counting_blackhole.py <port> [state_json_path]
"""
from __future__ import annotations

import json
import signal
import socket
import sys
import threading
import time

STATE = {"accepts": 0, "requests": 0, "open": 0, "peak_open": 0, "events": []}
LOCK = threading.Lock()
STATE_PATH = None
T0 = time.monotonic()


def _dump(*_a):
    if STATE_PATH:
        with LOCK:
            snap = {k: v for k, v in STATE.items()}
        with open(STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump(snap, fh, indent=2)


def _hold(conn: socket.socket, addr) -> None:
    with LOCK:
        STATE["accepts"] += 1
        STATE["open"] += 1
        if STATE["open"] > STATE["peak_open"]:
            STATE["peak_open"] = STATE["open"]
        STATE["events"].append(["accept", round(time.monotonic() - T0, 3), STATE["open"]])
        n_acc = STATE["accepts"]
    print(f"accept #{n_acc} from {addr} t={time.monotonic() - T0:.3f}", flush=True)
    buf = b""
    try:
        while b"\r\n\r\n" not in buf:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
        if b"\r\n\r\n" in buf:
            with LOCK:
                STATE["requests"] += 1
                STATE["events"].append(["request", round(time.monotonic() - T0, 3), buf.split(b"\r\n", 1)[0].decode("latin1")])
                n_req = STATE["requests"]
            print(f"request #{n_req} {buf.split(chr(13).encode())[0].decode('latin1').strip()} t={time.monotonic() - T0:.3f}", flush=True)
        # never reply; hold until the peer gives up
        threading.Event().wait(600)
    except OSError:
        pass
    finally:
        with LOCK:
            STATE["open"] -= 1
        try:
            conn.close()
        except OSError:
            pass


def main() -> int:
    global STATE_PATH
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8399
    STATE_PATH = sys.argv[2] if len(sys.argv) > 2 else None
    signal.signal(signal.SIGUSR1, _dump)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", port))
    server.listen(256)
    print(f"counting black-hole on 127.0.0.1:{port} state={STATE_PATH}", flush=True)
    while True:
        conn, addr = server.accept()
        threading.Thread(target=_hold, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    raise SystemExit(main())
