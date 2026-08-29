#!/usr/bin/env python3
"""
Server-run backup watchdog: alert when the Yamaguchi job did not run, did not succeed, or is stuck.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — wip (candidate B for plan §7 criterion 4, "failure notification observed firing";
        promote to util/ + util/systemd/ once Paul picks the alerting architecture)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8),
         util/duplicati_backup_failure.bash (the user lane's reporter this replaces for the server job)

WHY A POLLING WATCHDOG AND NOT ONLY --run-script-after
    "A backup that silently stops is indistinguishable from one that works." A
    job-level --run-script-after fires only when a run HAPPENS. It is silent in
    exactly the cases that produced the 2026-07-13 six-week blind spot: the
    scheduler never fired, the job definition vanished (the portable-mode /
    different-data-root restart trap presents as "job 2 does not exist"), the
    server is down, or a run hangs. This watchdog asks the server from the
    OUTSIDE, on its own timer, and alerts on any of:

      UNREACHABLE  login/serverstate failed (server down / not listening)
      JOB_MISSING  backup --backup-id is not in the server's backup list
      NO_RUNS      the job has no run log at all
      NOT_SUCCESS  the newest run's ParsedResult is not Success
      STALE        the newest run began more than --max-age-hours ago
      STUCK        a task is active and has been running longer than --max-run-hours
      (RUNNING     a task for this job is active and within --max-run-hours: OK, the
                   previous run's age is not judged while the next one is in progress)
      EXCEPTION    UNDETERMINED -- any unexpected failure, still recorded durably

    Durable record FIRST (append-only log + a status file), desktop
    notification best-effort (notify-send may have no session bus). Exit 0 = OK,
    1 = ALERT, 2 = UNDETERMINED (also alerts: an undetermined backup is not a
    verified one).

PROVING IT (plan §7: "test it deliberately")
    --base http://127.0.0.1:1        -> UNREACHABLE must alert
    --max-age-hours 0.001            -> STALE must alert (the newest run is older than ~4 s)
    --backup-id 999                  -> JOB_MISSING must alert
    Each forced alert must land in the log, the status file, and (with a session
    bus) as a critical desktop notification.

    python3 util/ad-hoc/yamaguchi_watchdog.py                # normal check
"""

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above


def parse_iso(s):
    """Duplicati timestamps: 2026-08-25T19:14:49.2056618Z or with a numeric offset."""
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # trim sub-microsecond digits (.NET gives 7) so fromisoformat accepts it
    if "." in s:
        head, tail = s.split(".", 1)
        frac = ""
        rest = ""
        for i, ch in enumerate(tail):
            if ch.isdigit():
                frac += ch
            else:
                rest = tail[i:]
                break
        s = f"{head}.{frac[:6]}{rest}"
    d = dt.datetime.fromisoformat(s)
    if d.tzinfo is None:  # a naive stamp would make the age arithmetic raise TypeError
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def check(args):
    """Return (verdict, code, details) without side effects."""
    api.BASE = args.base
    try:
        tok = api.login()
    except SystemExit as exc:
        return "ALERT", "UNREACHABLE", f"login failed: {exc}"
    except Exception as exc:  # noqa: BLE001 -- any transport failure is the alert condition
        return "ALERT", "UNREACHABLE", f"login raised {type(exc).__name__}: {exc}"
    st, state = api.req("GET", "/api/v1/serverstate", tok)
    if st != 200:
        return "ALERT", "UNREACHABLE", f"serverstate -> {st}"
    st, backups = api.req("GET", "/api/v1/backups", tok)
    ids = {str((b.get("Backup", b)).get("ID")) for b in backups} if isinstance(backups, list) else set()
    if str(args.backup_id) not in ids:
        return "ALERT", "JOB_MISSING", f"backup id {args.backup_id} not in server list {sorted(ids)} (different data root? see the portable-mode trap)"

    now = dt.datetime.now(dt.timezone.utc)
    active = state.get("ActiveTask")
    if active:
        # serverstate.ActiveTask is a (taskid, backupid) tuple serialized as Item1/Item2
        task_id = active.get("Item1") if isinstance(active, dict) else active
        task_backup = str(active.get("Item2")) if isinstance(active, dict) else None
        st, task = api.req("GET", f"/api/v1/task/{task_id}", tok)
        started = task.get("TaskStarted") if st == 200 else None
        if started:
            hours = (now - parse_iso(started)).total_seconds() / 3600
            if hours > args.max_run_hours:
                return "ALERT", "STUCK", f"task {task_id} (backup {task_backup}) running {hours:.1f} h > {args.max_run_hours} h"
            if task_backup == str(args.backup_id):
                # a run in progress is the healthy case; the newest LOG entry is still the
                # previous run and must not be judged stale while this one is going
                return "OK", "RUNNING", f"task {task_id} for backup {task_backup} running {hours:.1f} h"

    st, log = api.req("GET", f"/api/v1/backup/{args.backup_id}/log?pagesize=1", tok)
    if st != 200 or not isinstance(log, list):
        return "UNDETERMINED", "LOG_UNAVAILABLE", f"log -> {st}"
    if not log:
        return "ALERT", "NO_RUNS", "job has no run log"
    m = log[0].get("Message")
    m = json.loads(m) if isinstance(m, str) else (m or {})
    result = m.get("ParsedResult")
    begin = m.get("BeginTime")
    age_h = (now - parse_iso(begin)).total_seconds() / 3600 if begin else None
    summary = f"newest run {begin} ParsedResult={result} age={age_h:.1f}h" if age_h is not None else f"newest run ParsedResult={result} (no BeginTime)"
    if result != "Success":
        return "ALERT", "NOT_SUCCESS", summary
    if age_h is None or age_h > args.max_age_hours:
        return "ALERT", "STALE", f"{summary} > {args.max_age_hours} h"
    return "OK", "OK", summary


def record(args, verdict, code, details):
    os.makedirs(args.state_dir, exist_ok=True)
    when = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    line = f"{when} {verdict} {code} backup={args.backup_id} {details}"
    with open(os.path.join(args.state_dir, "server-watchdog.log"), "a") as fh:
        fh.write(line + "\n")
    with open(os.path.join(args.state_dir, "server-watchdog.status"), "w") as fh:
        fh.write(line + "\n")
    if verdict != "OK":
        with open(os.path.join(args.state_dir, "server-failures.log"), "a") as fh:
            fh.write(line + "\n")
        if args.notify and shutil.which("notify-send"):
            # best-effort: no session bus is not a reason to lose the durable record above
            proc = subprocess.run(["notify-send", "--urgency=critical", "Duplicati (Yamaguchi) backup ALERT",
                                   f"{code}: {details}\n{when}\nsee {args.state_dir}/server-failures.log"],
                                  check=False, capture_output=True)
            line += f" [notify-send rc={proc.returncode}]"
    return line


def main():
    ap = argparse.ArgumentParser(description="alert when the server-run Yamaguchi backup did not run, did not succeed, or is stuck")
    ap.add_argument("--base", default=api.BASE)
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--max-age-hours", type=float, default=26.0, help="newest run older than this = STALE (daily job + slack)")
    ap.add_argument("--max-run-hours", type=float, default=6.0, help="an active task older than this = STUCK (full run was 2h12m)")
    ap.add_argument("--state-dir", default=os.path.expanduser("~/.local/state/duplicati"))
    ap.add_argument("--no-notify", dest="notify", action="store_false")
    args = ap.parse_args()

    try:
        verdict, code, details = check(args)
    except Exception as exc:  # noqa: BLE001 -- an undetermined check must still leave a durable record
        verdict, code, details = "UNDETERMINED", "EXCEPTION", f"{type(exc).__name__}: {exc}"
    print(record(args, verdict, code, details))
    sys.exit(0 if verdict == "OK" else (1 if verdict == "ALERT" else 2))


if __name__ == "__main__":
    main()
