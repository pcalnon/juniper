#!/usr/bin/env python
"""Phase B2: does the design's Semaphore(4) queue keep issuing upstream calls for
requests whose clients have already given up?  (X7 draft design, 5.2)

Fires 30 /mutate requests, abandons every one at 1.2 s (the dashboard's own budget),
then watches the black-hole's request counter for 60 s with no further client traffic.
Any growth is work generated for nobody.
"""
from __future__ import annotations

import importlib.util
import json
import os
import signal
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("drv", os.path.join(HERE, "2026-09-03_x7_design_measure.py"))
drv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drv)

APP_PORT = drv.APP_PORT
STATE = drv.STATE


def bh_counts(bh_pid):
    os.kill(bh_pid, signal.SIGUSR1)
    time.sleep(0.3)
    with open(STATE, encoding="utf-8") as fh:
        st = json.load(fh)
    return {"accepts": st["accepts"], "requests": st["requests"], "open": st["open"]}


def main() -> int:
    bh = drv.start_blackhole()
    app, ok = drv.start_app({"X7_TIMEOUT": "5", "X7_RETRIES": "0", "X7_REFRESH": "600"})
    print(json.dumps({"app_started": ok}))
    if not ok:
        app.kill()
        bh.kill()
        return 1
    time.sleep(1.0)
    base = bh_counts(bh.pid)
    print("baseline", base, flush=True)

    from concurrent.futures import ThreadPoolExecutor

    def one(_i):
        try:
            requests.post(f"http://127.0.0.1:{APP_PORT}/mutate", timeout=1.2)
            return "ok"
        except Exception as e:  # noqa: BLE001
            return type(e).__name__

    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=32) as ex:
        res = list(ex.map(one, range(30)))
    print(f"all 30 clients gave up by t={time.monotonic() - t0:.2f}s: {res.count('ReadTimeout')} timeouts, {res.count('ok')} ok", flush=True)

    for t in (2, 10, 20, 30, 45, 60):
        while time.monotonic() - t0 < t:
            time.sleep(0.2)
        c = bh_counts(bh.pid)
        try:
            intro = requests.get(f"http://127.0.0.1:{APP_PORT}/introspect", timeout=5).json()
        except Exception as e:  # noqa: BLE001
            intro = repr(e)
        print(
            f"t+{t:>3}s  upstream_requests={c['requests'] - base['requests']:>3}  "
            f"open_conns={c['open']:>2}  inflight={intro.get('inflight')}  peak={intro.get('peak_inflight')}",
            flush=True,
        )
    app.kill()
    bh.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
