#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Minimal authenticated client for the Duplicati 2.3.x server REST API on the
Yamaguchi host service (http://127.0.0.1:8300). Exists because
duplicati-server-util exposes no task-abort and no backup-delete verbs.

Auth: POST /api/v1/auth/login with the password read from a credentials file
(never argv, never env of the calling shell); the JWT access token is held in
memory only. Subcommands:

    status              server state + running/scheduled tasks + backup list
    export <id>         print a backup's configuration JSON (for the record)
    abort <taskid>      abort a task (POST /api/v1/task/<id>/abort)
    delete <id>         delete a backup; --remote-files also deletes its
                        uploaded volumes (refuses unless --yes)
    import <file>       create a backup from an export-format JSON file
    run <id>            start the backup
    progress            live progress line of the running task

Safety: talks only to 127.0.0.1:8300; delete requires --yes; nothing here can
touch files under subdirectories of the destination (Duplicati file backends
list non-recursively, so a job whose TargetURL is the folder root cannot see
or delete Ubuntu/ or the scratch dirs).
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8300"
CRED_FILE = "/home/pcalnon/Development/python/Juniper/juniper-ml/.env"
CRED_KEY = "DUPLICATI_WEB_CREDENTIAL"


def read_credential():
    with open(CRED_FILE) as fh:
        for line in fh:
            m = re.match(rf"^\s*(?:export\s+)?{CRED_KEY}=(.*)$", line)
            if m:
                val = m.group(1).strip().strip("'\"")
                if val:
                    return val
    sys.exit(f"FATAL: no {CRED_KEY}= in {CRED_FILE}")


def req(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode(errors="replace")[:500]}


def login():
    status, body = req("POST", "/api/v1/auth/login", body={"Password": read_credential(), "RememberMe": False})
    if status != 200 or "AccessToken" not in body:
        sys.exit(f"FATAL: login failed ({status}): {json.dumps(body)[:300]}")
    return body["AccessToken"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "export", "abort", "delete", "import", "run", "progress"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--remote-files", action="store_true", help="delete: also remove uploaded volumes")
    ap.add_argument("--yes", action="store_true", help="required for delete")
    args = ap.parse_args()
    tok = login()

    if args.cmd == "status":
        _, state = req("GET", "/api/v1/serverstate", tok)
        print(json.dumps({k: state.get(k) for k in ("ProgramState", "ActiveTask", "SchedulerQueueIds", "ProposedSchedule")}, indent=1))
        _, backups = req("GET", "/api/v1/backups", tok)
        for b in backups if isinstance(backups, list) else []:
            bb = b.get("Backup", b)
            print(f"backup id={bb.get('ID')} name={bb.get('Name')!r} target={bb.get('TargetURL')}")
            meta = bb.get("Metadata") or {}
            if meta:
                print(f"  meta: LastBackupDate={meta.get('LastBackupDate')} SourceSize={meta.get('SourceFilesSize')}")

    elif args.cmd == "export":
        status, body = req("GET", f"/api/v1/backup/{args.arg}/export?export-passwords=false", tok)
        print(json.dumps(body, indent=1) if status == 200 else f"export failed {status}: {body}")

    elif args.cmd == "abort":
        status, body = req("POST", f"/api/v1/task/{args.arg}/abort", tok)
        print(f"abort task {args.arg}: {status} {body}")

    elif args.cmd == "delete":
        if not args.yes:
            sys.exit("refusing: delete requires --yes")
        q = "?delete-remote-files=true" if args.remote_files else ""
        status, body = req("DELETE", f"/api/v1/backup/{args.arg}{q}", tok)
        print(f"delete backup {args.arg} (remote={args.remote_files}): {status} {body}")

    elif args.cmd == "import":
        with open(args.arg) as fh:
            cfg = json.load(fh)
        status, body = req("POST", "/api/v1/backups?temporary=false", tok, body=cfg)
        print(f"import: {status} {json.dumps(body)[:400]}")

    elif args.cmd == "run":
        status, body = req("POST", f"/api/v1/backup/{args.arg}/run", tok)
        print(f"run backup {args.arg}: {status} {body}")

    elif args.cmd == "progress":
        _, state = req("GET", "/api/v1/serverstate", tok)
        active = state.get("ActiveTask")
        if not active:
            print("no active task")
            return
        _, prog = req("GET", "/api/v1/progressstate", tok)
        keys = ("BackupID", "TaskID", "Phase", "ProcessedFileCount", "ProcessedFileSize", "TotalFileCount", "TotalFileSize", "CurrentFilename", "BackendSpeed")
        print(json.dumps({k: prog.get(k) for k in keys}, indent=1))


if __name__ == "__main__":
    main()
