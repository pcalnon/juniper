"""Poll a running cascor training session to completion and print the final figures (R-5).

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-14
Status:      ad-hoc -- one-off (R-5 arm S1 collector)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: R-5 is written up and merged; delete then.
Related:     P4 §7 R-5; ml#1074 (Q-2 stall threshold).

Exists because run_experiment.py's Q-2 stall detector watches `current_epoch`, which does not
advance while the CANDIDATE pool trains. At pool 8 the driver gives up at its 120 s default
while the service keeps training happily -- and a re-run then hits HTTP 409 "Training already
in progress". This attaches to that live session instead of restarting it, so the started run
is not thrown away.

Read-only against the service: GETs /v1/training/status until the run leaves STARTED, then
GETs the final metrics. Writes only the JSON summary it is told to write.

Usage: python util/ad-hoc/2026-08-14_r5_poll_training.py --cascor-url URL --out PATH
                                                          [--interval S] [--timeout S]
Exit:  0 completed, 1 timed out while still training, 2 request error.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def get_json(url, timeout=15):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - loopback experiment service
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cascor-url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=20.0)
    ap.add_argument("--timeout", type=float, default=5400.0)
    args = ap.parse_args()

    base = args.cascor_url.rstrip("/")
    started = time.monotonic()
    last_units = None

    while True:
        try:
            status = get_json(f"{base}/v1/training/status")["data"]
        except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
            print(f"R-5 poll: status request failed: {exc}", file=sys.stderr)
            return 2

        sm = status.get("state_machine", {})
        mon = status.get("monitor", {})
        ts = status.get("training_state", {})
        units = mon.get("current_hidden_units")
        elapsed = time.monotonic() - started

        if units != last_units:
            print(f"[{elapsed:7.0f}s] units={units} iter={ts.get('grow_iteration')}/{ts.get('grow_max')} " f"phase={sm.get('phase')} best_corr={ts.get('best_correlation')}", flush=True)
            last_units = units

        if not status.get("training_active") and sm.get("status") != "STARTED":
            print(f"[{elapsed:7.0f}s] training finished: status={sm.get('status')} " f"completion_reason={status.get('completion_reason')}", flush=True)
            break

        if elapsed > args.timeout:
            print(f"R-5 poll: still training after {elapsed:.0f}s (timeout)", file=sys.stderr)
            return 1

        time.sleep(args.interval)

    # Final figures. /v1/metrics is the scalar surface the driver's eval block reads.
    summary = {"status": status}
    for name, path in (("metrics", "/v1/metrics"), ("network", "/v1/network")):
        try:
            summary[name] = get_json(f"{base}{path}")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            summary[name] = {"error": str(exc)}

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(f"R-5 poll: wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
