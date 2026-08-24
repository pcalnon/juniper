#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Answer one question: is a running job still using the secret its file holds?

Why this exists
---------------
On 2026-08-23 the ``Ubuntu-fresh`` backup launched, read ``PASSPHRASE`` into its
process environment, and 30 minutes later that entry in ``.env`` was overwritten
with a different value. The backup carried on encrypting ~36 GB under a secret
that then existed **only in its own memory** -- one process exit from being
permanently unrecoverable.

**A file-vs-process divergence is invisible to any check that only reads the
file.** Nothing else in this toolkit could have seen it.

Design
------
Compares in-process, and prints only ``MATCH`` / ``DIFFER``. No hash, no length,
no fragment of any secret ever reaches stdout or a log. That is not merely
prudent: it is what lets this run in CI or a cron job without becoming the
clear-text-logging hazard it exists to prevent. (An earlier design logged a
truncated hash from inside the backup runners; CodeQL flagged the taint, and it
was right that a password-derived value reaching a log sink is the wrong shape
even when the particular derivation is safe.)

Reading ``/proc/<pid>/environ`` requires being the process owner or root.

Usage
-----
    python3 util/ad-hoc/duplicati_secret_check.py --pid 779263 \\
        --file .env --key PASSPHRASE
    python3 util/ad-hoc/duplicati_secret_check.py --match-cmd 'duplicati-cli backup' \\
        --file .env --key PASSPHRASE

Exit: 0 = MATCH, 1 = DIFFER, 2 = could not determine.
"""

from __future__ import annotations

import argparse
import re
import subprocess


def secret_from_file(path: str, key: str) -> str | None:
    with open(path) as fh:
        raw = fh.read()
    m = re.search(rf"^[ \t]*(?:export[ \t]+)?{re.escape(key)}=(.*)$", raw, re.M)
    if not m:
        return None
    val = m.group(1).strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
        val = val[1:-1]
    return val


def secret_from_pid(pid: int, var: str) -> str | None:
    with open(f"/proc/{pid}/environ", "rb") as fh:
        blob = fh.read().decode("utf-8", "replace")
    for entry in blob.split("\0"):
        if entry.startswith(var + "="):
            return entry[len(var) + 1:]
    return None


def find_pid(pattern: str) -> list[int]:
    out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True,
                         text=True).stdout
    hits = []
    for line in out.splitlines()[1:]:
        pid, _, args = line.strip().partition(" ")
        # Skip our own process and anything merely mentioning the pattern in a
        # grep/pgrep invocation -- a self-match is how a dead process gets
        # reported as running.
        if pattern in args and "duplicati_secret_check" not in args \
                and not args.lstrip().startswith(("grep", "pgrep")):
            try:
                hits.append(int(pid))
            except ValueError:
                continue
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--match-cmd", default=None,
                    help="find the pid by command-line substring instead")
    ap.add_argument("--file", required=True, help="credential file")
    ap.add_argument("--key", required=True, help="KEY= entry to compare against")
    ap.add_argument("--env-var", default="PASSPHRASE",
                    help="environment variable name inside the process")
    args = ap.parse_args()

    if args.pid is None and not args.match_cmd:
        print("REFUSING: give --pid or --match-cmd")
        return 2

    pids = [args.pid] if args.pid else find_pid(args.match_cmd)
    if not pids:
        print(f"UNDETERMINED: no process matches {args.match_cmd!r} "
              f"(if it already exited, its secret is gone unless recorded)")
        return 2
    if len(pids) > 1:
        print(f"UNDETERMINED: {len(pids)} processes match: {pids}. Use --pid.")
        return 2
    pid = pids[0]

    try:
        in_proc = secret_from_pid(pid, args.env_var)
    except PermissionError:
        print(f"UNDETERMINED: /proc/{pid}/environ not readable (need owner or root)")
        return 2
    except FileNotFoundError:
        print(f"UNDETERMINED: pid {pid} is gone")
        return 2
    if in_proc is None:
        print(f"UNDETERMINED: pid {pid} has no {args.env_var} in its environment")
        return 2

    on_disk = secret_from_file(args.file, args.key)
    if on_disk is None:
        print(f"DIFFER: {args.file} has no {args.key}= entry, but pid {pid} "
              f"is running with a {args.env_var}")
        return 1

    started = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)],
                             capture_output=True, text=True).stdout.strip()
    print(f"pid {pid} (started {started})")
    print(f"  process {args.env_var}  vs  {args.file}:{args.key}")
    if in_proc == on_disk:
        print("  MATCH — the file still holds what the process is using")
        return 0
    print("  *** DIFFER ***")
    print(f"  The running job is using a secret that {args.file}:{args.key} no")
    print("  longer holds. If that process exits before the value is recorded")
    print("  elsewhere, whatever it encrypted becomes unrecoverable. Capture it:")
    print(f"    tr '\\0' '\\n' < /proc/{pid}/environ | grep '^{args.env_var}='")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
