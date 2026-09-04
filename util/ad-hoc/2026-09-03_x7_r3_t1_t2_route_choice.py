#!/usr/bin/env python3
"""Round-3 review harness #3: X7-T1's 500 ms threshold and X7-T2's driver-latency
guard, evaluated against BOTH route choices T1 leaves unnamed.

Project      : Juniper - juniper-ml (review harness for juniper-canopy X7 design rev 3)
Author       : Paul Calnon
License      : MIT

X7-T1 (rev 3, §6): "hold >=3 concurrent requests to a cascor-touching route against a
2.0 s bounded stub; assert max latency of /v1/health/live < 500 ms".
X7-T2: "control sample non-empty, AND each driver's latency >= the stub bound (proving
it actually blocked)".

After the fix there are TWO kinds of "cascor-touching route":
  (R) a READ route, which §5.3 converts to a memory read -> no upstream call at all
  (M) a MUTATING route, which §5.4 keeps as a bounded to_thread upstream call
§6 does not say which T1 drives. Measure both arms.

Run: conda run -n JuniperCanopy1 python util/ad-hoc/2026-09-03_x7_r3_t1_t2_route_choice.py
"""

from __future__ import annotations

import asyncio
import socket
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import uvicorn
from fastapi import FastAPI

STUB_BOUND = 2.0
DRIVERS = 3
CONTROL_N = 20
T1_THRESHOLD_MS = 500.0

app = FastAPI()
_sem = asyncio.Semaphore(4)


def _blocking_upstream():
    """Stands in for the synchronous cascor-client call against a BOUNDED stub."""
    time.sleep(STUB_BOUND)
    return {"training_active": True, "state_machine": {"status": "TRAINING"}}


# --- TODAY: sync-in-async on the read path ---------------------------------
@app.get("/today/read")
async def today_read():
    return _blocking_upstream()


# --- AFTER: read served from the cache (no upstream call at all) ------------
_CACHE = {"training_active": True, "state_machine": {"status": "TRAINING"}}


@app.get("/after/read")
async def after_read():
    return dict(_CACHE)


# --- AFTER: mutating route, bounded to_thread ------------------------------
@app.post("/after/mutate")
async def after_mutate():
    async with _sem:
        return await asyncio.to_thread(_blocking_upstream)


@app.get("/v1/health/live")
async def live():
    return {"status": "alive"}


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def run_arm(base, driver_path, method):
    driver_lat = []
    control_lat = []
    stop = threading.Event()

    def drive():
        t0 = time.monotonic()
        try:
            if method == "GET":
                requests.get(base + driver_path, timeout=60)
            else:
                requests.post(base + driver_path, timeout=60)
        except Exception:
            pass
        driver_lat.append(time.monotonic() - t0)

    def control():
        while not stop.is_set():
            t0 = time.monotonic()
            try:
                requests.get(base + "/v1/health/live", timeout=60)
                control_lat.append((time.monotonic() - t0) * 1000)
            except Exception:
                pass
            time.sleep(0.05)

    ct = threading.Thread(target=control, daemon=True)
    ct.start()
    time.sleep(0.3)
    with ThreadPoolExecutor(max_workers=DRIVERS) as ex:
        list(ex.map(lambda _: drive(), range(DRIVERS)))
    time.sleep(0.3)
    stop.set()
    ct.join(timeout=5)
    return driver_lat, control_lat


def report(label, driver_lat, control_lat):
    n = len(control_lat)
    mx = max(control_lat) if control_lat else 0.0
    t1 = "PASS" if (mx < T1_THRESHOLD_MS) else "FAIL"
    guard_nonempty = n > 0
    guard_blocked = all(d >= STUB_BOUND for d in driver_lat) if driver_lat else False
    t2 = "HOLDS" if (guard_nonempty and guard_blocked) else "VIOLATED"
    print(f"\n  {label}")
    print(f"    control samples          : {n}")
    print(f"    control max latency      : {mx:8.1f} ms   -> X7-T1 (<500 ms): {t1}")
    print(f"    driver latencies         : {[f'{d:.3f}s' for d in driver_lat]}")
    print(f"    driver >= stub bound {STUB_BOUND}s ? {guard_blocked}    -> X7-T2 guard: {t2}")
    if t1 == "PASS" and t2 == "VIOLATED":
        print("    ==> T1 passes but T2 says T1 is VOID. Per §6 the test result is discarded.")
    return t1, t2


def main():
    port = free_port()
    cfg = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical", workers=1)
    server = uvicorn.Server(cfg)
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            requests.get(base + "/v1/health/live", timeout=1)
            break
        except Exception:
            time.sleep(0.1)

    print("=" * 110)
    print("X7-T1 / X7-T2 evaluated against each route T1 could mean")
    print("=" * 110)

    results = {}
    results["today"] = report("TODAY  — driver = READ route, sync-in-async (the defect)",
                              *run_arm(base, "/today/read", "GET"))
    results["after_read"] = report("AFTER  — driver = READ route, now served from cache (§5.3)",
                                   *run_arm(base, "/after/read", "GET"))
    results["after_mut"] = report("AFTER  — driver = MUTATING route, bounded to_thread (§5.4)",
                                  *run_arm(base, "/after/mutate", "POST"))

    print()
    print("=" * 110)
    print("VERDICT")
    print("=" * 110)
    print(f"  {'arm':<44}{'X7-T1':<10}{'X7-T2 guard'}")
    for k, (a, b) in results.items():
        print(f"  {k:<44}{a:<10}{b}")
    print()
    print("  X7-T1 discriminates ONLY if the driver route is one that still blocks after")
    print("  the fix. §6 says 'a cascor-touching route' and never names it.")

    server.should_exit = True
    th.join(timeout=10)


if __name__ == "__main__":
    main()
