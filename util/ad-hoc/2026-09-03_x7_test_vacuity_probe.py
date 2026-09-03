#!/usr/bin/env python
"""Probe the X7 draft test plan's own feasibility (design 6).

t1_shape      : X7-T1 exactly as specified -- N GETs to a pure-async liveness route
                with a black-holed cascor, asserting all N complete. Run against a
                TODAY-shaped app (blocking call inside `async def`) with no concurrent
                driver, which is what the spec literally says.
t1_with_driver: the same, plus one concurrent request to a blocking route.
t7_exit       : whether a test that leaves a hung `asyncio.to_thread` job can be
                collected/torn down, or whether the interpreter joins it at exit.

Run with pytest:  pytest -x -p no:cacheprovider <thisfile>::<test>
"""
from __future__ import annotations

import asyncio
import os
import threading
import time

import pytest
import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient

BLACKHOLE = os.environ.get("X7_UPSTREAM", "http://127.0.0.1:8399")

today = FastAPI()


@today.get("/v1/health/live")
async def live():
    return {"status": "alive"}


@today.get("/v1/health")
async def health():
    # today's shape: synchronous, retrying requests I/O inside `async def`
    try:
        requests.get(f"{BLACKHOLE}/v1/training/status", timeout=6)
    except Exception:  # noqa: BLE001
        pass
    return {"status": "ok"}


def _hammer(client, path, n, out):
    for _ in range(n):
        t = time.monotonic()
        try:
            r = client.get(path)
            out.append((r.status_code, round(time.monotonic() - t, 3)))
        except Exception as e:  # noqa: BLE001
            out.append((type(e).__name__, round(time.monotonic() - t, 3)))


def test_t1_shape_as_literally_specified():
    """X7-T1 verbatim: only /v1/health/live is exercised. Design claims 0 completions."""
    completed = []
    with TestClient(today) as client:
        _hammer(client, "/v1/health/live", 20, completed)
    n_ok = sum(1 for c, _ in completed if c == 200)
    print(f"\nT1-as-specified: {n_ok}/20 completed, max={max(d for _, d in completed):.3f}s")
    # The design asserts "all N complete" must FAIL today (0 completions in 40 s).
    assert n_ok == 0, f"X7-T1 as specified PASSES on today's blocking code: {n_ok}/20 completed"


def test_t1_needs_a_concurrent_blocking_driver():
    """The same assertion, with the driver the spec omits."""
    completed = []
    driver_done = []

    def drive():
        with TestClient(today) as c2:
            try:
                c2.get("/v1/health")
            except Exception as e:  # noqa: BLE001
                driver_done.append(type(e).__name__)
            else:
                driver_done.append("ok")

    with TestClient(today) as client:
        t = threading.Thread(target=drive, daemon=True)
        t.start()
        time.sleep(0.2)
        _hammer(client, "/v1/health/live", 20, completed)
    n_ok = sum(1 for c, _ in completed if c == 200)
    print(f"\nT1-with-driver: {n_ok}/20 completed, driver={driver_done}")
    assert n_ok == 0, f"even with a driver, {n_ok}/20 completed -- TestClient does not share one loop"


def test_t7_leaves_a_hung_to_thread():
    """X7-T7 shape: a hung to_thread job that the test cannot reclaim."""

    async def body():
        task = asyncio.create_task(asyncio.to_thread(lambda: threading.Event().wait(300)))
        await asyncio.sleep(0.5)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        return "cancelled at the loop, thread still running"

    print("\n" + asyncio.run(body()))
