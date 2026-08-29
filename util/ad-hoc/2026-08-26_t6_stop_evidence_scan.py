#!/usr/bin/env python3
"""
Scan a set of experiment run dirs and classify what each teardown SIGTERM actually stopped.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc — investigation (juniper-cascor#589 production verification, §3.2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-CASCOR_DEV-SHM-LEAK-CHARACTERISATION.md §6.5;
         the T6 re-baseline campaign (t6-rebaseline-20260826T075112Z);
         util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash

Why this exists
---------------
The T6 re-baseline ran 23 cells against the cascor#589 fix and left a clean /dev/shm ledger,
which was reported as "clean live confirmation of the fix under real training load". This scan
tests a narrower, load-bearing question the ledger alone cannot answer: **did any of those 23
teardown stops actually land WHILE training was running?** run_experiment.py drives training to
a terminal state and only then tears the stack down, and CascadeCorrelationNetwork.fit() already
releases the candidate pool in its `finally` on normal completion — so a stop that lands after
"Training ended" exercises the fix's *idle* path (join finds no future, 0.00s, nothing to
release), not the stop-during-training path the fix was written for.

For each run dir it reads the per-run cascor engine log (logs/juniper_cascor.log[.N], the
redirected per-run copy — NOT the shared checkout's) and reports, per cell:
  * whether "Training ended" was logged before "JuniperCascor API shutting down" (=> idle stop),
  * the gap between them in seconds,
  * the "TrainingLifecycleManager shut down (Xs)" elapsed the fix prints,
  * any "training thread still running" / "did not unwind" WARNING (the mid-round abandon path),
  * worker-log-lines stamped after the parent's last line (orphaned workers still running).

Usage: 2026-08-26_t6_stop_evidence_scan.py <run-dir> [<run-dir> ...]
Read-only. Prints a table and a one-line verdict to stdout; writes nothing.
"""
import glob
import os
import re
import sys
from datetime import datetime

PARENT_TS = re.compile(r"\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)(?:,(\d{3}))?\)")
SHUTDOWN_ELAPSED = re.compile(r"TrainingLifecycleManager shut down \(([0-9.]+)s\)")


def _ts(m):
    base = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
    return base + (int(m.group(2)) / 1000.0 if m.lastindex and m.group(2) else 0.0)


def _rot_key(path):
    suf = path.rsplit(".", 1)[1]
    return -int(suf) if suf.isdigit() else 0  # .log last (newest), .log.N older


# The shutdown stanza ("Training ended", "shutting down", "shut down (Xs)", "did not unwind")
# is always in the small CURRENT juniper_cascor.log, written after the rotation that dumps the
# multi-hundred-MB training history to .log.1/.log.2. Reading those giant files line-by-line
# costs ~40 GB of I/O for markers that are never in them, so skip anything over this cap. The
# worker-after-parent cross-check is then best-effort (absent when the shutdown log is tiny).
_MAX_LOG_BYTES = 32 * 1024 * 1024


def scan(run_dir):
    logs = sorted(glob.glob(os.path.join(run_dir, "logs", "juniper_cascor.log*")), key=_rot_key)
    r = {
        "run": os.path.basename(run_dir),
        "logs": len(logs),
        "training_ended_ts": None,
        "shutting_down_ts": None,
        "shutdown_elapsed_s": None,
        "did_not_unwind": 0,
        "last_parent_ts": None,
        "last_worker_ts": None,
    }
    last_parent = last_worker = None
    r["skipped_big_logs"] = 0
    for path in logs:
        try:
            if os.path.getsize(path) > _MAX_LOG_BYTES:
                r["skipped_big_logs"] += 1
                continue
        except OSError:
            continue
        with open(path, errors="replace") as fh:
            for line in fh:
                if "Training ended" in line and r["training_ended_ts"] is None:
                    m = PARENT_TS.search(line)
                    if m:
                        r["training_ended_ts"] = _ts(m)
                if "JuniperCascor API shutting down" in line:
                    m = PARENT_TS.search(line)
                    if m:
                        r["shutting_down_ts"] = _ts(m)
                me = SHUTDOWN_ELAPSED.search(line)
                if me:
                    r["shutdown_elapsed_s"] = float(me.group(1))
                if "did not unwind" in line or "training thread still running" in line:
                    r["did_not_unwind"] += 1
                m = PARENT_TS.search(line)
                if m:
                    if line.startswith("+"):
                        last_worker = _ts(m)
                    else:
                        last_parent = _ts(m)
    r["last_parent_ts"] = last_parent
    r["last_worker_ts"] = last_worker
    return r


def main(argv):
    rows = [scan(d) for d in argv if os.path.isdir(d)]
    if not rows:
        print("no run dirs", file=sys.stderr)
        return 2
    idle = live = unknown = 0
    print(f"{'run':<24} {'stop_class':<12} {'end->stop(s)':>12} {'shutdown(s)':>11} {'unwind_warn':>11} {'worker_after_parent(s)':>22}")
    for r in rows:
        gap = wa = None
        if r["training_ended_ts"] and r["shutting_down_ts"]:
            gap = round(r["shutting_down_ts"] - r["training_ended_ts"], 3)
            cls = "idle" if gap >= 0 else "LIVE"
        elif r["shutting_down_ts"] and not r["training_ended_ts"]:
            cls = "LIVE?"  # a stop with no preceding "Training ended" in the log
        else:
            cls = "unknown"
        if r["last_parent_ts"] and r["last_worker_ts"]:
            wa = round(r["last_worker_ts"] - r["last_parent_ts"], 3)
        if cls == "idle":
            idle += 1
        elif cls.startswith("LIVE"):
            live += 1
        else:
            unknown += 1
        print(f"{r['run']:<24} {cls:<12} {str(gap):>12} {str(r['shutdown_elapsed_s']):>11} {r['did_not_unwind']:>11} {str(wa):>22}")
    print()
    print(f"VERDICT: {len(rows)} cells — idle(post-completion) stops: {idle}, live(mid-training) stops: {live}, unknown: {unknown}; "
          f"total did-not-unwind warnings: {sum(r['did_not_unwind'] for r in rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
