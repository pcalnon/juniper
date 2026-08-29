#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E stack support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Restart ONE leg of a running isolated stack, in place, preserving its
#          exact environment, cwd and argv -- without touching the other legs.
#
#          `isolated_stack.bash` has --up / --down / --status and nothing between
#          them: --up restarts the WHOLE trio. That is unusable when one leg holds
#          irreplaceable in-memory state. Concretely (2026-08-29): the cascor leg
#          held a completed 2/10/2/89 network that took ~17 h to produce and is the
#          fixture the F-CANOPY-039 probes are defined against, while the canopy leg
#          needed restarting to pick up a temporary source probe. Restarting both
#          would have destroyed the thing being measured.
#
#          The environment is the hard part: these legs are launched by
#          `experiment_stack.bash` / `isolated_stack.bash` under `nohup` with ~10
#          JUNIPER_CANOPY_* settings that do not exist in any file -- they are
#          composed at launch. Re-launching from a hand-written env silently gives a
#          DIFFERENT service (wrong ports, wrong upstreams, auth on instead of off).
#          So this reads /proc/<pid>/environ and reuses it verbatim.
#
# SECRETS: the captured environment routinely contains PyPI tokens and API keys.
#          This script NEVER prints, logs or serialises it. It is read from /proc
#          and passed straight to the child. Do not add a debug dump.
#
# ORPHAN-REAPER NOTE: the relaunched process is nohup-detached and so reparents to
#          `systemd --user`, which is exactly the predicate
#          `util/reap_pytest_orphans.bash` treats as an orphan. Its cmdline still
#          references the run root, which is one of the two protection keys -- but
#          do not run the reaper while this stack is up regardless.
#
# Usage:
#   python3 util/ad-hoc/restart_leg_preserving_env.py --pid 1379952 --log <path>
#   python3 util/ad-hoc/restart_leg_preserving_env.py --pid 1379952 --log <path> --dry-run
#
# Exit: 0 restarted (new pid printed), 1 failed, 2 invocation error.

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request


def read_proc(pid):
    base = f"/proc/{pid}"
    if not os.path.isdir(base):
        print(f"no such process: {pid}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(f"{base}/cmdline", "rb") as fh:
            argv = [a.decode() for a in fh.read().split(b"\0") if a]
        with open(f"{base}/environ", "rb") as fh:
            env = {}
            for item in fh.read().split(b"\0"):
                if not item or b"=" not in item:
                    continue
                key, _, value = item.partition(b"=")
                env[key.decode(errors="replace")] = value.decode(errors="replace")
        cwd = os.readlink(f"{base}/cwd")
    except OSError as exc:  # PermissionError is an OSError subclass; this covers both
        print(f"cannot read /proc/{pid}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not argv:
        print(f"pid {pid} has an empty cmdline (kernel thread?)", file=sys.stderr)
        sys.exit(2)
    return argv, env, cwd


def wait_gone(pid, timeout=20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not os.path.isdir(f"/proc/{pid}"):
            return True
        time.sleep(0.3)
    return False


def wait_healthy(url, timeout):
    """Poll until the leg answers, so 'restarted' is measured and not assumed."""
    deadline = time.time() + timeout
    last = "no attempt"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 - fixed localhost URL
                if 200 <= resp.status < 500:
                    return True, f"HTTP {resp.status}"
                last = f"HTTP {resp.status}"
        except urllib.error.HTTPError as exc:
            # A 4xx still proves the server is listening and routing.
            return True, f"HTTP {exc.code}"
        except (urllib.error.URLError, OSError) as exc:
            last = type(exc).__name__
        time.sleep(1.0)
    return False, last


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pid", type=int, required=True, help="pid of the leg to restart")
    ap.add_argument("--log", required=True, help="file to append the relaunched leg's stdout+stderr to")
    ap.add_argument("--health-url", help="poll this until it answers before declaring success")
    ap.add_argument("--health-timeout", type=float, default=90.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    argv, env, cwd = read_proc(args.pid)
    # Deliberately summarised, never dumped -- this mapping holds live credentials.
    print(f"pid {args.pid}: argv={argv} cwd={cwd} env={len(env)} vars (not shown: contains secrets)")

    if args.dry_run:
        print("DRY RUN — nothing killed, nothing started")
        return 0

    os.kill(args.pid, signal.SIGTERM)
    if not wait_gone(args.pid):
        print(f"pid {args.pid} still alive after SIGTERM; sending SIGKILL")
        try:
            os.kill(args.pid, signal.SIGKILL)
        except ProcessLookupError:
            # Benign and expected: the leg finished its SIGTERM shutdown in the
            # window between wait_gone() giving up and this kill. The goal is
            # "process is gone", which is already satisfied -- so there is
            # nothing to handle. The wait_gone() check below is what actually
            # decides success, and it re-checks rather than trusting this.
            pass
        if not wait_gone(args.pid, timeout=10.0):
            print(f"FAILED: pid {args.pid} will not die", file=sys.stderr)
            return 1
    print(f"pid {args.pid} stopped")

    with open(args.log, "ab") as logfh:
        proc = subprocess.Popen(  # noqa: S603 - argv reused verbatim from the process being replaced
            argv,
            cwd=cwd,
            env=env,
            stdout=logfh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    print(f"relaunched as pid {proc.pid} (log: {args.log})")

    if not args.health_url:
        print("no --health-url given; NOT verified to be serving")
        return 0

    ok, detail = wait_healthy(args.health_url, args.health_timeout)
    if ok:
        print(f"healthy: {args.health_url} -> {detail}")
        return 0
    print(f"FAILED: {args.health_url} never answered within {args.health_timeout}s (last: {detail})", file=sys.stderr)
    print(f"  the process may still be starting; check {args.log}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
