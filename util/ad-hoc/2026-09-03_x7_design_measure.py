#!/usr/bin/env python
"""Driver for the X7 draft-design adversarial measurements.

Phases (select with argv[1]):
  A  loop responsiveness + refresher overlap + SIGTERM-to-exit under a HUNG upstream
  B  semaphore-vs-thread bound under client disconnect (design 5.2 / test X7-T7)
  C  urllib3 retry semantics for POST: read-timeout vs connection-refused
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "2026-09-03_x7_design_probe_app.py")
BH = os.path.join(HERE, "2026-09-03_x7_counting_blackhole.py")
PY = sys.executable
BH_PORT = int(os.environ.get("BH_PORT", "8399"))
APP_PORT = int(os.environ.get("APP_PORT", "8398"))
STATE = "/tmp/juniper-x7-rev/bh_state.json"


def _mkstate():
    os.makedirs(os.path.dirname(STATE), exist_ok=True)


def _wait_port(port, deadline=15.0):
    t0 = time.monotonic()
    while time.monotonic() - t0 < deadline:
        s = socket.socket()
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except OSError:
            time.sleep(0.1)
        finally:
            try:
                s.close()
            except OSError:
                pass
    return False


def _threads_of(pid):
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("Threads:"):
                    return int(line.split()[1])
    except OSError:
        return -1
    return -1


def start_blackhole():
    _mkstate()
    log = open("/tmp/juniper-x7-rev/bh.log", "w", encoding="utf-8")
    try:
        p = subprocess.Popen([PY, BH, str(BH_PORT), STATE], stdout=log, stderr=subprocess.STDOUT)
        _wait_port(BH_PORT)
    except Exception:
        log.close()
        raise
    p._x7_log_handle = log
    return p


def start_app(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    env["X7_PORT"] = str(APP_PORT)
    env["X7_UPSTREAM"] = f"http://127.0.0.1:{BH_PORT}"
    log = open("/tmp/juniper-x7-rev/app.log", "w", encoding="utf-8")
    try:
        p = subprocess.Popen([PY, APP], env=env, stdout=log, stderr=subprocess.STDOUT)
        ok = _wait_port(APP_PORT, 25.0)
    except Exception:
        log.close()
        raise
    p._x7_log_handle = log
    return p, ok


def phase_a():
    """Loop responsiveness, overlap, executor slot occupancy, SIGTERM-to-exit."""
    out = {}
    bh = start_blackhole()
    timeout = int(os.environ.get("X7_TIMEOUT", "30"))
    retries = int(os.environ.get("X7_RETRIES", "3"))
    app, ok = start_app({"X7_TIMEOUT": str(timeout), "X7_RETRIES": str(retries), "X7_REFRESH": "1.0"})
    out["app_started"] = ok
    out["params"] = {"timeout": timeout, "retries": retries, "refresh": 1.0}
    if not ok:
        app.kill()
        bh.kill()
        return out

    # --- probe /live for 20s while the refresher is stuck on the hung upstream ---
    lat = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < 20.0:
        s = time.monotonic()
        try:
            r = requests.get(f"http://127.0.0.1:{APP_PORT}/live", timeout=5)
            lat.append((round(time.monotonic() - s, 4), r.status_code))
        except Exception as e:  # noqa: BLE001
            lat.append((round(time.monotonic() - s, 4), f"ERR {type(e).__name__}"))
        time.sleep(0.25)
    codes = [c for _, c in lat]
    vals = [v for v, c in lat if c == 200]
    out["live_probe"] = {
        "n": len(lat),
        "n_200": codes.count(200),
        "max_latency_s": max(vals) if vals else None,
        "mean_latency_s": round(sum(vals) / len(vals), 5) if vals else None,
    }

    # --- refresher overlap: starts vs returns, and threads in the process ---
    try:
        intro = requests.get(f"http://127.0.0.1:{APP_PORT}/introspect", timeout=5).json()
    except Exception as e:  # noqa: BLE001
        intro = {"err": repr(e)}
    out["introspect_at_20s"] = intro
    out["proc_threads_at_20s"] = _threads_of(app.pid)
    os.kill(bh.pid, signal.SIGUSR1)
    time.sleep(0.4)
    try:
        with open(STATE, encoding="utf-8") as fh:
            out["blackhole_at_20s"] = json.load(fh)
    except OSError:
        out["blackhole_at_20s"] = None

    # --- SIGTERM-to-exit: the design's refresher is mid-to_thread almost always ---
    t_kill = time.monotonic()
    app.send_signal(signal.SIGTERM)
    exited = None
    while time.monotonic() - t_kill < 200:
        if app.poll() is not None:
            exited = round(time.monotonic() - t_kill, 3)
            break
        time.sleep(0.05)
    out["sigterm_to_exit_s"] = exited
    out["sigterm_rc"] = app.poll()
    if exited is None:
        app.kill()
        out["sigterm_to_exit_s"] = ">200 (SIGKILLed)"
    try:
        with open("/tmp/juniper-x7-rev/app.log", encoding="utf-8") as fh:
            out["app_log_tail"] = fh.read()[-1500:]
    except OSError:
        pass
    bh.kill()
    return out


def phase_a_control():
    """Control: same app, SIGTERM while the upstream is CLOSED (fast failure)."""
    out = {}
    # no blackhole -> ECONNREFUSED, refresher fails fast every tick
    app, ok = start_app({"X7_TIMEOUT": "30", "X7_RETRIES": "3", "X7_REFRESH": "1.0"})
    out["app_started"] = ok
    if not ok:
        app.kill()
        return out
    time.sleep(6)
    try:
        out["introspect"] = requests.get(f"http://127.0.0.1:{APP_PORT}/introspect", timeout=5).json()
    except Exception as e:  # noqa: BLE001
        out["introspect"] = repr(e)
    t_kill = time.monotonic()
    app.send_signal(signal.SIGTERM)
    exited = None
    while time.monotonic() - t_kill < 60:
        if app.poll() is not None:
            exited = round(time.monotonic() - t_kill, 3)
            break
        time.sleep(0.05)
    out["sigterm_to_exit_s"] = exited if exited is not None else ">60"
    if exited is None:
        app.kill()
    return out


def phase_b():
    """Does Semaphore(4) actually bound OUTBOUND CONCURRENCY when clients disconnect?"""
    out = {}
    bh = start_blackhole()
    app, ok = start_app({"X7_TIMEOUT": "30", "X7_RETRIES": "0", "X7_REFRESH": "600"})
    out["app_started"] = ok
    if not ok:
        app.kill()
        bh.kill()
        return out
    time.sleep(1.0)

    # Fire waves of /mutate and ABANDON each after 1.2s (browser tab closed / dashboard
    # timeout at 1.0s fast lane / 2.0s normal lane -- design C3).
    def one(i):
        try:
            requests.post(f"http://127.0.0.1:{APP_PORT}/mutate", timeout=1.2)
            return "ok"
        except Exception as e:  # noqa: BLE001
            return type(e).__name__

    results = []
    with ThreadPoolExecutor(max_workers=32) as ex:
        for wave in range(5):
            futs = [ex.submit(one, i) for i in range(6)]
            results.extend(f.result() for f in futs)
            time.sleep(0.2)
    time.sleep(1.0)
    try:
        out["introspect"] = requests.get(f"http://127.0.0.1:{APP_PORT}/introspect", timeout=10).json()
    except Exception as e:  # noqa: BLE001
        out["introspect"] = repr(e)
    out["client_results"] = results
    out["proc_threads"] = _threads_of(app.pid)
    os.kill(bh.pid, signal.SIGUSR1)
    time.sleep(0.4)
    try:
        with open(STATE, encoding="utf-8") as fh:
            st = json.load(fh)
        st.pop("events", None)
        out["blackhole"] = st
    except OSError:
        out["blackhole"] = None
    app.kill()
    bh.kill()
    return out


def phase_c():
    """urllib3 retry semantics for POST: read-timeout vs connection-refused."""
    from juniper_cascor_client import JuniperCascorClient
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    out = {}
    bh = start_blackhole()
    time.sleep(0.5)

    def make(allowed):
        c = JuniperCascorClient(f"http://127.0.0.1:{BH_PORT}", timeout=2, retries=3)
        if allowed is not None:
            r = Retry(total=3, backoff_factor=0.5, status_forcelist=[502, 503, 504], allowed_methods=allowed)
            a = HTTPAdapter(max_retries=r, pool_maxsize=10)
            c.session.mount("http://", a)
            c.session.mount("https://", a)
        return c

    for label, allowed in (("default_RETRY_ALLOWED_METHODS", None), ("restricted_HEAD_GET_PUT", ["HEAD", "GET", "PUT"])):
        # reset counters
        os.kill(bh.pid, signal.SIGUSR1)
        time.sleep(0.3)
        with open(STATE, encoding="utf-8") as fh:
            before = json.load(fh)
        c = make(allowed)
        t0 = time.monotonic()
        err = None
        try:
            c.session.post(f"http://127.0.0.1:{BH_PORT}/v1/training/start", json={}, timeout=2)
        except Exception as e:  # noqa: BLE001
            err = type(e).__name__
        dt = round(time.monotonic() - t0, 2)
        os.kill(bh.pid, signal.SIGUSR1)
        time.sleep(0.3)
        with open(STATE, encoding="utf-8") as fh:
            after = json.load(fh)
        out[f"readtimeout::{label}"] = {
            "elapsed_s": dt,
            "requests_reaching_server": after["requests"] - before["requests"],
            "tcp_accepts": after["accepts"] - before["accepts"],
            "error": err,
        }
    bh.kill()

    # connection-refused arm: nothing listening on BH_PORT+1
    dead = BH_PORT + 1
    for label, allowed in (("default_RETRY_ALLOWED_METHODS", None), ("restricted_HEAD_GET_PUT", ["HEAD", "GET", "PUT"])):
        c = JuniperCascorClient(f"http://127.0.0.1:{dead}", timeout=2, retries=3)
        if allowed is not None:
            r = Retry(total=3, backoff_factor=0.5, status_forcelist=[502, 503, 504], allowed_methods=allowed)
            a = HTTPAdapter(max_retries=r, pool_maxsize=10)
            c.session.mount("http://", a)
            c.session.mount("https://", a)
        t0 = time.monotonic()
        err = None
        try:
            c.session.post(f"http://127.0.0.1:{dead}/v1/training/start", json={}, timeout=2)
        except Exception as e:  # noqa: BLE001
            err = type(e).__name__
        out[f"connrefused::{label}"] = {"elapsed_s": round(time.monotonic() - t0, 2), "error": err}
    return out


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "A"
    fn = {"A": phase_a, "Actrl": phase_a_control, "B": phase_b, "C": phase_c}[phase]
    print(json.dumps(fn(), indent=2, default=str))
