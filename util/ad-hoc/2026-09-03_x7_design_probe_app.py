#!/usr/bin/env python
"""X7 design-review harness: a FastAPI app implementing the DRAFT design's 5.1/5.2 shape.

Mirrors the proposed remediation exactly so its runtime behaviour can be measured:
  * one background asyncio refresher task, `await asyncio.to_thread(client.get_training_status)`
    followed by `await asyncio.sleep(REFRESH_INTERVAL)`  (design 5.1)
  * read routes served from the in-memory cache (never touch upstream)
  * one mutating route: `async with Semaphore(4): await asyncio.to_thread(...)` (design 5.2)

Env knobs: X7_UPSTREAM, X7_TIMEOUT, X7_RETRIES, X7_REFRESH, X7_SEM, X7_PORT.
"""
from __future__ import annotations

import asyncio
import os
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from juniper_cascor_client import JuniperCascorClient

UPSTREAM = os.environ.get("X7_UPSTREAM", "http://127.0.0.1:8399")
TIMEOUT = int(os.environ.get("X7_TIMEOUT", "30"))
RETRIES = int(os.environ.get("X7_RETRIES", "3"))
REFRESH = float(os.environ.get("X7_REFRESH", "1.0"))
SEM_BOUND = int(os.environ.get("X7_SEM", "4"))

client = JuniperCascorClient(UPSTREAM, timeout=TIMEOUT, retries=RETRIES)

cache = {"value": None, "fetched_at": None, "failures": 0, "ticks": 0, "starts": 0, "returns": 0, "last_error": ""}
sem: asyncio.Semaphore | None = None
_inflight = {"n": 0, "peak": 0}
_lock = threading.Lock()


def _call():
    with _lock:
        _inflight["n"] += 1
        if _inflight["n"] > _inflight["peak"]:
            _inflight["peak"] = _inflight["n"]
    try:
        return client.get_training_status()
    finally:
        with _lock:
            _inflight["n"] -= 1


async def _refresher() -> None:
    while True:
        cache["starts"] += 1
        try:
            payload = await asyncio.to_thread(_call)
            cache["value"] = payload
            cache["fetched_at"] = time.monotonic()
        except Exception as exc:  # noqa: BLE001
            cache["failures"] += 1
            cache["last_error"] = repr(exc)[:120]
        cache["returns"] += 1
        cache["ticks"] += 1
        await asyncio.sleep(REFRESH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sem
    sem = asyncio.Semaphore(SEM_BOUND)
    task = asyncio.create_task(_refresher())
    app.state.refresher = task
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


@app.get("/live")
async def live():
    return {"status": "alive"}


@app.get("/status")
async def status():
    return {"cached": cache["value"] is not None, "failures": cache["failures"], "ticks": cache["ticks"]}


@app.get("/introspect")
async def introspect():
    return {
        "threads": threading.active_count(),
        "starts": cache["starts"],
        "returns": cache["returns"],
        "inflight": _inflight["n"],
        "peak_inflight": _inflight["peak"],
        "failures": cache["failures"],
        "last_error": cache["last_error"],
    }


@app.post("/mutate")
async def mutate():
    async with sem:
        await asyncio.to_thread(_call)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("X7_PORT", "8398")), log_level="warning")
