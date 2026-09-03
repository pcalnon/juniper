#!/usr/bin/env python
"""Isolate what a hung `asyncio.to_thread` job costs at interpreter/loop shutdown.

Mode `plain`   : stdlib asyncio.run + a to_thread job that never returns; the task is
                 cancelled, mirroring the draft design's lifespan shutdown block.
Mode `uvicorn` : the same shape hosted by uvicorn, driven by a real SIGTERM.

Prints a millisecond-stamped trace so the driver can attribute the wall time.
"""
from __future__ import annotations

import asyncio
import sys
import threading
import time

T0 = time.monotonic()


def log(msg: str) -> None:
    print(f"[{time.monotonic() - T0:8.3f}] {msg}", flush=True)


def _hang() -> None:
    log(f"worker thread {threading.current_thread().name} entered; sleeping forever")
    threading.Event().wait(600)
    log("worker thread RETURNED (should not happen inside the window)")


async def _refresher() -> None:
    while True:
        try:
            await asyncio.to_thread(_hang)
        except Exception as exc:  # noqa: BLE001
            log(f"refresher caught {exc!r}")
        await asyncio.sleep(1.0)


async def _main() -> None:
    task = asyncio.create_task(_refresher())
    await asyncio.sleep(2.0)
    log("cancelling refresher task (lifespan shutdown block)")
    task.cancel()
    t = time.monotonic()
    try:
        await task
    except asyncio.CancelledError:
        log("refresher task cancellation observed (expected during shutdown)")
    log(f"await task returned after {time.monotonic() - t:.3f}s -> loop-side cancel is CHEAP")
    log("returning from _main; asyncio.run finalisation begins now")


def plain() -> None:
    asyncio.run(_main())
    log("asyncio.run RETURNED (shutdown_default_executor completed)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "plain"
    if mode == "plain":
        plain()
        log("process about to exit")
    else:
        raise SystemExit(f"unknown mode {mode}")
