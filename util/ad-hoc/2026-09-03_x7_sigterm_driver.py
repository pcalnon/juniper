#!/usr/bin/env python
"""Drive a SIGTERM at the uvicorn shutdown-trace app and time the exit (X7 design review)."""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "2026-09-03_x7_uvicorn_shutdown.py")
PORT = int(os.environ.get("PORT", "8397"))
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"


def wait_port(port, deadline=20.0):
    t0 = time.monotonic()
    while time.monotonic() - t0 < deadline:
        s = socket.socket()
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except OSError:
            time.sleep(0.1)
        finally:
            s.close()
    return False


def main() -> int:
    log_path = "/tmp/juniper-x7-rev/uvicorn_shutdown.log"
    with open(log_path, "w", encoding="utf-8") as fh:
        p = subprocess.Popen([PY, "-u", APP, str(PORT)], stdout=fh, stderr=subprocess.STDOUT)
        ok = wait_port(PORT)
        print(f"app_started={ok} pid={p.pid}")
        time.sleep(3.0)
        t0 = time.monotonic()
        p.send_signal(signal.SIGTERM)
        rc = None
        while time.monotonic() - t0 < 45:
            if p.poll() is not None:
                rc = p.poll()
                break
            time.sleep(0.02)
        dt = round(time.monotonic() - t0, 3)
        if rc is None:
            print(f"STILL ALIVE after {dt}s -> sending SIGKILL")
            p.kill()
            p.wait()
        else:
            print(f"sigterm_to_exit_s={dt} rc={rc}")
    with open(log_path, encoding="utf-8") as f:
        print("---- app trace ----")
        print(f.read())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
