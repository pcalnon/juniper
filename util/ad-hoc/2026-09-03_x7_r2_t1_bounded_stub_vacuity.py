#!/usr/bin/env python3
"""Round-2 review harness: does X7-T1 (design rev 2, §6) still fail on today's code
once §6's OTHER revision -- "the stubs must be bounded so the thread always returns"
-- is applied?

T1 (rev 2): hold >=3 concurrent in-flight requests to a cascor-touching route against
a hung stub, and assert ALL N control requests to /v1/health/live complete.
Harness rule (rev 2): stubs must be BOUNDED, never hung forever.

The two are applied together here. T1's assertion as written carries no deadline,
so the question is whether "all N complete" can still discriminate.

Project      : Juniper - juniper-ml (review harness for juniper-canopy X7 design rev 2)
Author       : Paul Calnon
License      : MIT

Run: conda run -n JuniperCanopy1 python util/ad-hoc/2026-09-03_x7_r2_t1_bounded_stub_vacuity.py
"""

from __future__ import annotations

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import uvicorn
from fastapi import FastAPI

STUB_BOUND_SECONDS = 2.0  # "bounded" per the rev-2 harness rule
DRIVERS = 3  # ">=3 concurrent in-flight requests" per rev-2 T1
CONTROL_N = 20

app = FastAPI()


@app.get("/v1/health")
async def blocking_route():
    """Today's shape: synchronous, retrying I/O inside `async def`.
    The stub it talks to is BOUNDED (returns after STUB_BOUND_SECONDS)."""
    time.sleep(STUB_BOUND_SECONDS)  # stands in for requests.get() against a bounded stub
    return {"status": "ok"}


@app.get("/v1/health/live")
async def liveness():
    return {"status": "alive"}


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main():
    port = free_port()
    cfg = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", workers=1)
    server = uvicorn.Server(cfg)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            requests.get(f"{base}/v1/health/live", timeout=0.5)
            break
        except Exception:
            time.sleep(0.05)

    results = {}

    def driver(i):
        t0 = time.monotonic()
        try:
            r = requests.get(f"{base}/v1/health", timeout=60)
            return ("driver", i, "completed", round(time.monotonic() - t0, 3), r.status_code)
        except Exception as e:  # noqa: BLE001
            return ("driver", i, f"failed:{type(e).__name__}", round(time.monotonic() - t0, 3), None)

    def control(i):
        t0 = time.monotonic()
        try:
            r = requests.get(f"{base}/v1/health/live", timeout=60)  # T1 states no deadline
            return ("control", i, "completed", round(time.monotonic() - t0, 3), r.status_code)
        except Exception as e:  # noqa: BLE001
            return ("control", i, f"failed:{type(e).__name__}", round(time.monotonic() - t0, 3), None)

    pool = ThreadPoolExecutor(max_workers=DRIVERS + CONTROL_N)
    t_start = time.monotonic()
    dfut = [pool.submit(driver, i) for i in range(DRIVERS)]
    time.sleep(0.2)  # let the drivers land first
    cfut = [pool.submit(control, i) for i in range(CONTROL_N)]

    drows = [f.result() for f in dfut]
    crows = [f.result() for f in cfut]
    total = time.monotonic() - t_start

    dcomp = sum(1 for r in drows if r[2] == "completed")
    ccomp = sum(1 for r in crows if r[2] == "completed")
    cmax = max((r[3] for r in crows), default=0)

    print(f"stub bound       : {STUB_BOUND_SECONDS}s (BOUNDED, per rev-2 harness rule)")
    print(f"drivers          : {DRIVERS} concurrent to /v1/health (rev-2 T1 mandatory driver)")
    print(f"driver completed : {dcomp}/{DRIVERS}   (rev-2 X7-T2 asserts these did NOT complete)")
    print(f"control completed: {ccomp}/{CONTROL_N} (rev-2 X7-T1 asserts ALL N complete)")
    print(f"control max lat  : {cmax}s   wall={total:.2f}s")
    print()
    print("X7-T1 as written in rev 2 ('assert all N control requests complete', no deadline):")
    print(f"  -> {'PASSES' if ccomp == CONTROL_N else 'FAILS'} on today's blocking code")
    print("X7-T2 as written in rev 2 ('assert the driver actually blocked -- its requests did NOT complete'):")
    print(f"  -> {'PASSES' if dcomp == 0 else 'FAILS'} (drivers completed: {dcomp})")

    server.should_exit = True
    t.join(timeout=10)
    pool.shutdown(wait=False)


if __name__ == "__main__":
    main()
