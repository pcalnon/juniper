#!/usr/bin/env python
"""Trace uvicorn's SIGTERM path when a `to_thread` worker is hung (X7 design review)."""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

T0 = time.monotonic()


def log(msg: str) -> None:
    print(f"[{time.monotonic() - T0:8.3f}] pid={os.getpid()} {msg}", flush=True)


def _hang() -> None:
    log("worker thread entered, hanging")
    threading.Event().wait(600)


async def _refresher() -> None:
    while True:
        try:
            await asyncio.to_thread(_hang)
        except asyncio.CancelledError:
            log("refresher: CancelledError while awaiting to_thread")
            raise
        await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log("lifespan startup")
    t = asyncio.create_task(_refresher())
    yield
    log("lifespan shutdown: cancelling refresher")
    t.cancel()
    try:
        await t
    except asyncio.CancelledError:
        pass
    log("lifespan shutdown: refresher awaited")


app = FastAPI(lifespan=lifespan)


@app.get("/live")
async def live():
    return {"status": "alive"}


if __name__ == "__main__":
    import atexit

    import uvicorn

    atexit.register(lambda: log("ATEXIT ran"))
    loop = os.environ.get("X7_LOOP", "auto")
    log(f"calling uvicorn.run loop={loop}")
    uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8397, log_level="warning", loop=loop)
    log("uvicorn.run RETURNED")
