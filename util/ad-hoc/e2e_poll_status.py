#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-1 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Poll canopy's GET /api/status until a field reaches a target (or a
#          timeout expires), printing one compact line per tick. Written during
#          the 2026-08-14 Phase-1 segment-9 session because the W6 restart lane
#          needs to wait on FSM/units transitions repeatedly, and the session
#          sandbox refuses multi-command bash poll loops.
#
# Usage:
#   python3 util/ad-hoc/e2e_poll_status.py                       # one shot, print status
#   python3 util/ad-hoc/e2e_poll_status.py --until-units 2       # wait for >=2 hidden units
#   python3 util/ad-hoc/e2e_poll_status.py --until-fsm STOPPED   # wait for an fsm_status
#   python3 util/ad-hoc/e2e_poll_status.py --until-pending-clear # wait for pending_dataset None
#
# Exit codes: 0 target reached (or one-shot), 1 timeout, 2 transport error.

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

FIELDS = (
    "fsm_status",
    "phase",
    "current_epoch",
    "hidden_units",
    "input_size",
    "network_connected",
    "pending_dataset",
)


def fetch(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 - fixed loopback URL
        return json.loads(resp.read().decode("utf-8"))


def line(elapsed: float, status: dict) -> str:
    parts = [f"t={elapsed:5.1f}s"]
    for key in FIELDS:
        value = status.get(key)
        if key == "pending_dataset":
            value = "none" if value in (None, {}, "") else "SET"
        parts.append(f"{key.replace('_', '-')}={value}")
    return " ".join(parts)


def reached(status: dict, args: argparse.Namespace) -> bool:
    if args.until_units is not None and status.get("hidden_units", 0) >= args.until_units:
        return True
    if args.until_fsm is not None and status.get("fsm_status") == args.until_fsm:
        return True
    if args.until_pending_clear and status.get("pending_dataset") in (None, {}, ""):
        return True
    if args.until_pending_set and status.get("pending_dataset") not in (None, {}, ""):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Poll canopy /api/status until a condition holds.")
    ap.add_argument("--url", default="http://127.0.0.1:8051/api/status")
    ap.add_argument("--interval", type=float, default=4.0)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--until-units", type=int, default=None, help="wait for hidden_units >= N")
    ap.add_argument("--until-fsm", default=None, help="wait for fsm_status == VALUE")
    ap.add_argument("--until-pending-clear", action="store_true", help="wait for pending_dataset empty")
    ap.add_argument("--until-pending-set", action="store_true", help="wait for pending_dataset non-empty")
    ap.add_argument("--json", action="store_true", help="print the final status as JSON")
    args = ap.parse_args()

    has_target = (
        args.until_units is not None
        or args.until_fsm is not None
        or args.until_pending_clear
        or args.until_pending_set
    )

    start = time.monotonic()
    status: dict = {}
    while True:
        elapsed = time.monotonic() - start
        try:
            status = fetch(args.url, timeout=5.0)
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            print(f"t={elapsed:5.1f}s TRANSPORT-ERROR {exc}", flush=True)
            return 2
        print(line(elapsed, status), flush=True)

        if not has_target:
            break
        if reached(status, args):
            print("target reached", flush=True)
            break
        if elapsed >= args.timeout:
            print(f"TIMEOUT after {elapsed:.1f}s without reaching target", flush=True)
            if args.json:
                print(json.dumps(status, indent=2))
            return 1
        time.sleep(args.interval)

    if args.json:
        print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
