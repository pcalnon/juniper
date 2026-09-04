#!/usr/bin/env python
"""Does the draft design's refresher ever see a FAILURE?  (X7 design 5.1 / 5.5, tests T3-T5)

The design's tick is:

    try:
        payload = await asyncio.to_thread(adapter.get_training_status)
        cache.record_success(payload)
    except Exception as exc:
        cache.record_failure(exc)

`record_failure` fires only if the call RAISES.  This drives the real
`CascorServiceAdapter` against a dead cascor and reports, tick by tick, whether the
call raised or returned -- and what it returned.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-canopy/src")
os.environ.setdefault("JUNIPER_CANOPY_DEMO_MODE", "0")

from backend.cascor_service_adapter import CascorServiceAdapter  # noqa: E402
from juniper_cascor_client import JuniperCascorClient  # noqa: E402

DEAD = "http://127.0.0.1:8395"  # nothing listening -> ECONNREFUSED, fast


def main() -> int:
    client = JuniperCascorClient(DEAD, timeout=1, retries=0)
    adapter = CascorServiceAdapter(service_url=DEAD, client=client)
    print(f"breaker threshold={adapter._circuit.failure_threshold} recovery={adapter._circuit.recovery_timeout}s")
    print(f"{'tick':>4} {'outcome':>9} {'breaker':>10} {'elapsed':>8}  payload / exception")
    for i in range(1, 9):
        t = time.monotonic()
        try:
            payload = adapter.get_training_status()
            outcome = "RETURNED"
            detail = repr(payload)[:90]
        except Exception as exc:  # noqa: BLE001
            outcome = "RAISED"
            detail = f"{type(exc).__name__}: {exc}"[:90]
        dt = time.monotonic() - t
        print(f"{i:>4} {outcome:>9} {adapter._circuit.state.value:>10} {dt:>7.3f}s  {detail}")

    print()
    print("Same question for the interlock path (is_training_in_progress, NOT breakered):")
    for i in range(1, 4):
        try:
            v = adapter.is_training_in_progress()
            print(f"  tick {i}: RETURNED {v!r}")
        except Exception as exc:  # noqa: BLE001
            print(f"  tick {i}: RAISED {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
