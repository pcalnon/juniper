"""
Probe: what does a uvicorn process do the moment its lifespan shutdown returns after SIGTERM?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-CASCOR_DEV-SHM-LEAK-CHARACTERISATION.md §6 (the
         cascor stop-during-training leak); the 2026-08-25 snapshot-arc handoff §2.3

Why this exists
---------------
The §6 diagnosis deduced that a cascor service stopped mid-training was SIGKILLed by the stop
tool 15 s after a graceful lifespan shutdown, because ``atexit`` demonstrably never ran. The
log evidence does not fit a 15 s hang: the training thread (logging every ~6 ms) went silent
within one log interval of ``JuniperCascor API shutting down`` and never emitted the
``Training ended`` line that the interrupt path logs.

uvicorn's ``Server.capture_signals`` (0.29+) restores the ORIGINAL signal handlers when
``serve()`` returns and then ``signal.raise_signal()``s every captured signal. Python leaves
SIGTERM at ``SIG_DFL``, so the re-raised SIGTERM terminates the process instantly — no
``atexit``, no thread joins, no interpreter finalisation. SIGINT differs: Python's default
handler raises ``KeyboardInterrupt``, which unwinds normally and DOES run ``atexit``.

This probe measures exactly that with a two-file-free, self-contained FastAPI app: it records
whether ``atexit`` fires, whether a non-daemon thread gets to exit, the exit status, and the
time from signal to death, for SIGTERM (thread left running / thread joined in lifespan) and
for SIGINT as the control.

Usage
-----
    /opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/uvicorn_sigterm_atexit_probe.py

Prints one JSON object per scenario. Ports 18991-18993 on 127.0.0.1 must be free.
"""

from __future__ import annotations

import atexit
import json
import os
import signal
import subprocess  # nosec B404 — spawns uvicorn on a fixed argv, no shell
import sys
import tempfile
import threading
import time
import urllib.request
from contextlib import asynccontextmanager

_MARK_DIR = os.environ.get("PROBE_MARK_DIR", "")


def _mark(name: str) -> None:
    if _MARK_DIR:
        with open(os.path.join(_MARK_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(f"{time.time():.6f}\n")


# --------------------------------------------------------------------------------------------
# The ASGI app (only constructed inside the uvicorn child, where PROBE_MARK_DIR is set)
# --------------------------------------------------------------------------------------------
_stop = threading.Event()


def _spin() -> None:
    while not _stop.is_set():
        _mark("thread_alive")  # rewritten every tick: its timestamp is the thread's last sign of life
        time.sleep(0.005)
    _mark("thread_exit")


@asynccontextmanager
async def _lifespan(app):
    atexit.register(lambda: _mark("atexit"))
    worker = threading.Thread(target=_spin, name="probe-spin", daemon=False)
    worker.start()
    yield
    _mark("lifespan_shutdown")
    if os.environ.get("PROBE_STOP_THREAD") == "1":
        _stop.set()
        worker.join()
    # else: mirror cascor's shutdown() — the thread is left running when lifespan returns


def _build_app():
    from fastapi import FastAPI

    return FastAPI(lifespan=_lifespan)


app = _build_app() if _MARK_DIR else None


# --------------------------------------------------------------------------------------------
# The driver (parent process)
# --------------------------------------------------------------------------------------------
def _wait_http(url: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:  # nosec B310 — fixed loopback URL
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.05)
    return False


def _read_mark(mark_dir: str, name: str):
    path = os.path.join(mark_dir, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return float(fh.read().strip())


def _run_scenario(sig: signal.Signals, stop_thread: bool, port: int) -> dict:
    mark_dir = tempfile.mkdtemp(prefix="uvicorn-probe-")
    env = dict(os.environ, PROBE_MARK_DIR=mark_dir, PROBE_STOP_THREAD="1" if stop_thread else "0")
    here = os.path.dirname(os.path.abspath(__file__))
    module = os.path.splitext(os.path.basename(__file__))[0]
    argv = [sys.executable, "-m", "uvicorn", f"{module}:app", "--app-dir", here, "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"]
    proc = subprocess.Popen(argv, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec B603
    try:
        if not _wait_http(f"http://127.0.0.1:{port}/openapi.json", 30.0):
            proc.kill()
            return {"scenario": f"{sig.name}/stop_thread={int(stop_thread)}", "error": "server never became healthy"}
        time.sleep(0.2)  # let the spin thread tick a few times
        t_signal = time.time()
        proc.send_signal(sig)
        try:
            rc = proc.wait(timeout=30.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = "TIMEOUT(30s)->killed"
        t_dead = time.time()
    finally:
        if proc.poll() is None:
            proc.kill()

    marks = {name: _read_mark(mark_dir, name) for name in ("lifespan_shutdown", "thread_alive", "thread_exit", "atexit")}
    lifespan_t = marks["lifespan_shutdown"]
    return {
        "scenario": f"{sig.name}/stop_thread={int(stop_thread)}",
        "returncode": rc,
        "returncode_meaning": ("killed by signal %d" % -rc) if isinstance(rc, int) and rc < 0 else ("exit status %s" % rc),
        "signal_to_death_s": round(t_dead - t_signal, 3),
        "lifespan_shutdown_ran": lifespan_t is not None,
        "atexit_ran": marks["atexit"] is not None,
        "thread_exited_cleanly": marks["thread_exit"] is not None,
        "thread_last_seen_after_lifespan_s": (round(marks["thread_alive"] - lifespan_t, 3) if lifespan_t is not None and marks["thread_alive"] is not None else None),
    }


def main() -> int:
    scenarios = [
        (signal.SIGTERM, False, 18991),  # cascor today: shutdown() returns with training still running
        (signal.SIGTERM, True, 18992),  # lifespan joins the thread first: does atexit run then?
        (signal.SIGINT, True, 18993),  # control: SIGINT unwinds via KeyboardInterrupt
    ]
    for sig, stop_thread, port in scenarios:
        print(json.dumps(_run_scenario(sig, stop_thread, port)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
