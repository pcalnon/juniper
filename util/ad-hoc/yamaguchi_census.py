#!/usr/bin/env python3
"""
Census of the Yamaguchi destination reconciled against the server's own run log.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — investigation (Yamaguchi scope-widening re-baseline)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8)

Two independent witnesses, printed side by side so a divergence is visible:

  * the FILESYSTEM: volume counts by type, total bytes, every dlist, newest and
    oldest mtimes (a raw ``ls`` of the destination, no Duplicati involved)
  * the SERVER: job Metadata (KnownFileCount/Size, fileset count) and the
    newest N run results in full -- ParsedResult, examined/added/modified/
    deleted counts and sizes, BackendStatistics (uploaded/deleted/retries),
    DeleteResults.DeletedSets (retention thinning), CompactResults (must stay
    false while --no-auto-compact=true), post-run TestResults, warning/error
    counts.

Nothing is written anywhere by this tool; redirect stdout to keep a record.

    python3 util/ad-hoc/yamaguchi_census.py --runs 5 > /media/pcalnon/temp_backups/_yamaguchi_check/census-post-widening.txt
"""

import argparse
import json
import os
import sys
from urllib.parse import unquote, urlparse
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

RUN_KEYS = ("ParsedResult", "MainOperation", "BeginTime", "EndTime", "Duration", "ExaminedFiles", "SizeOfExaminedFiles",
            "AddedFiles", "SizeOfAddedFiles", "ModifiedFiles", "SizeOfModifiedFiles", "DeletedFiles", "OpenedFiles",
            "NotProcessedFiles", "FilesWithError", "TooLargeFiles", "PartialBackup", "Interrupted")
BACKEND_KEYS = ("BytesUploaded", "BytesDownloaded", "FilesUploaded", "FilesDownloaded", "FilesDeleted",
                "RetryAttempts", "KnownFileCount", "KnownFileSize", "BackupListCount")


def fs_census(dest):
    names = sorted(os.listdir(dest))
    kinds = {"dlist": [], "dblock": [], "dindex": [], "other": []}
    total = 0
    mtimes = []
    for n in names:
        st = os.stat(os.path.join(dest, n))
        total += st.st_size
        mtimes.append((st.st_mtime, n))
        for k in ("dlist", "dblock", "dindex"):
            if f".{k}." in n:
                kinds[k].append(n)
                break
        else:
            kinds["other"].append(n)
    print(f"== filesystem census of {dest} at {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    print(f"files      : {len(names)} = {len(kinds['dlist'])} dlist + {len(kinds['dblock'])} dblock + {len(kinds['dindex'])} dindex + {len(kinds['other'])} other")
    print(f"bytes      : {total} ({total / 2**30:.3f} GiB)")
    for n in kinds["dlist"]:
        print(f"dlist      : {n}")
    if kinds["other"]:
        print(f"OTHER      : {kinds['other'][:10]}")
    if mtimes:
        mtimes.sort()
        print(f"oldest     : {time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(mtimes[0][0]))} {mtimes[0][1]}")
        print(f"newest     : {time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(mtimes[-1][0]))} {mtimes[-1][1]}")
    return len(names), total


def main():
    ap = argparse.ArgumentParser(description="destination census reconciled against the Duplicati server's run log")
    ap.add_argument("--dest", default=None, help="destination directory; default: DERIVED from the job's own TargetURL")
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--runs", type=int, default=5, help="newest N run results to print in full")
    args = ap.parse_args()

    tok = api.login()
    status, cfg = api.req("GET", f"/api/v1/backup/{args.backup_id}", tok)
    if status != 200:
        sys.exit(f"FATAL: GET backup {args.backup_id} -> {status}")
    b = cfg["Backup"]

    # The destination is DERIVED from the job, never assumed.  A hardcoded default
    # survives a destination migration and then censuses the PRE-migration directory:
    # the reconcile line compares the wrong filesystem against the right server
    # metadata and prints a false DIVERGE -- and once the old directory is retired it
    # would census zero files and read as catastrophic loss.  Observed 2026-08-26
    # (note 8.13): this tool printed DIVERGE while both witnesses were in fact
    # perfectly consistent, because only one of them had followed the move.
    dest = args.dest
    if dest is None:
        target = b.get("TargetURL") or ""
        if not target.startswith("file://"):
            sys.exit(f"FATAL: job {args.backup_id} TargetURL is not a local file:// path ({target}); pass --dest explicitly")
        dest = unquote(urlparse(target).path)
    if not os.path.isdir(dest):
        sys.exit(f"FATAL: destination {dest} is not a directory")
    # Mount guard, also derived: walk up to the containing mountpoint rather than
    # naming one filesystem, so it cannot rot the way the hardcoded sdc4 check did.
    mp = os.path.abspath(dest)
    while mp != "/" and not os.path.ismount(mp):
        mp = os.path.dirname(mp)
    if mp == "/":
        sys.exit(f"FATAL: destination {dest} is not on a mounted filesystem (walked up to /)")
    n_files, n_bytes = fs_census(dest)

    _, state = api.req("GET", "/api/v1/serverstate", tok)
    print(f"\n== server state: ProgramState={state.get('ProgramState')} ActiveTask={state.get('ActiveTask')} ProposedSchedule={state.get('ProposedSchedule')}")
    meta = b.get("Metadata") or {}
    sch = cfg.get("Schedule") or {}
    print(f"job        : id={b.get('ID')} name={b.get('Name')!r} target={b.get('TargetURL')} dbpath={b.get('DBPath')}")
    print(f"schedule   : Time={sch.get('Time')} Repeat={sch.get('Repeat')} LastRun={sch.get('LastRun')}")
    print("metadata   : " + ", ".join(f"{k}={meta.get(k)}" for k in (
        "LastBackupDate", "LastBackupStarted", "LastBackupFinished", "LastBackupDuration", "BackupListCount",
        "TargetFilesCount", "TargetFilesSize", "TargetFilesetsCount", "SourceFilesCount", "SourceFilesSize")))
    tc, ts = meta.get("TargetFilesCount"), meta.get("TargetFilesSize")
    agree = str(tc) == str(n_files) and str(ts) == str(n_bytes)
    print(f"reconcile  : filesystem {n_files} files / {n_bytes} B vs server TargetFilesCount={tc} TargetFilesSize={ts} -> {'AGREE' if agree else 'DIVERGE'}")

    status, log = api.req("GET", f"/api/v1/backup/{args.backup_id}/log?pagesize={args.runs}", tok)
    if status != 200 or not isinstance(log, list):
        sys.exit(f"FATAL: log -> {status}")
    log = log[: args.runs]  # the server ignores pagesize on this build (always returns 5) -- cut client-side
    print(f"\n== newest {len(log)} run(s), newest first")
    for entry in log:
        m = entry.get("Message")
        m = json.loads(m) if isinstance(m, str) else (m or {})
        print("--")
        print("  " + ", ".join(f"{k}={m.get(k)}" for k in RUN_KEYS))
        bs = m.get("BackendStatistics") or {}
        print("  backend: " + ", ".join(f"{k}={bs.get(k)}" for k in BACKEND_KEYS))
        d = m.get("DeleteResults") or {}
        print(f"  DeleteResults.DeletedSets={json.dumps(d.get('DeletedSets')) if isinstance(d, dict) else d}  CompactResults={bool(m.get('CompactResults')) or (bool(d.get('CompactResults')) if isinstance(d, dict) else False)}")
        t = m.get("TestResults") or {}
        print(f"  TestResults: {t.get('ParsedResult')} on {t.get('VerificationsActualLength')} file(s)  Warnings={len(m.get('Warnings') or [])} Errors={len(m.get('Errors') or [])}")
        for w in (m.get("Warnings") or [])[:5]:
            print(f"    WARN: {str(w)[:300]}")
        for e in (m.get("Errors") or [])[:5]:
            print(f"    ERR : {str(e)[:300]}")


if __name__ == "__main__":
    main()
