#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Build and import the complete Yamaguchi backup job on the Duplicati system
server (127.0.0.1:8300). Composition, per the 2026-08-25 direction:

* Sources + exclusion filters: exactly the Ubuntu-fresh set's, parsed LIVE
  from util/duplicati_scheduled_backup.bash (single source of truth -- a
  hand-copied list would drift), plus Paul's own additions from the
  as-created job (*.iso, *.vdi).
* Investigation-derived settings (GPGFlushError note §9 + fresh-set plan):
  blocksize 1MB (IRREVERSIBLE -- pinned explicitly), dblock-size 500MB,
  no-auto-compact (compaction destroyed the old archive; retention marks
  deletions that would otherwise trigger it), allow-missing-source,
  asynchronous-upload-limit 1 (blast radius), gpg-encryption-switches
  --compress-algo none (the 10x tail tax; also neutralizes whatever
  compress-algo ROOT's gpg.conf might set -- the server runs as root),
  tempdir on ext4 (the server's default /tmp is tmpfs -- the run-1 trap).
* Paul's explicit choices preserved: retention-policy 1W:1D,1M:1W,1Y:1M,3Y:2M,
  skip-files-larger-than 8GB, daily 13:00 schedule.
* Destination: file:///mnt/Backups/Ubuntu/Yamaguchi (dedicated subdirectory --
  never the mount root).  Overridable with --target; the default MOVED on
  2026-08-26 when the set migrated to sda1 (note 8.13), and was left stale here
  until note 8.14.

REFUSES BY DEFAULT if a backup job of the same name already exists.  This script
POSTs a NEW job (``?temporary=false``); run bare against a server that already
holds Yamaguchi and you get a SECOND job pointed at whatever this file's
defaults happen to say -- which, while those defaults were stale, meant a
duplicate job silently writing to the retired sdc4 path.  Pass
--allow-duplicate only when a second job is genuinely wanted.

The passphrase is read from ~/.config/duplicati-backup/env (PASSPHRASE, the
fresh-set key) inside this process; it appears in no argv and no output.
"""

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yamaguchi_server_api import login, req  # noqa: E402

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "duplicati_scheduled_backup.bash")
CRED_FILE = os.path.expanduser("~/.config/duplicati-backup/env")


def read_passphrase():
    with open(CRED_FILE) as fh:
        for line in fh:
            m = re.match(r"^\s*(?:export\s+)?PASSPHRASE=(.*)$", line)
            if m and m.group(1).strip():
                return m.group(1).strip().strip('"')
    sys.exit("FATAL: no PASSPHRASE in credentials file")


def runner_excludes():
    out = []
    with open(RUNNER) as fh:
        for line in fh:
            m = re.search(r'"--exclude=([^"]+)"', line)
            if m:
                out.append(m.group(1))
    if len(out) < 40:
        sys.exit(f"FATAL: only {len(out)} excludes parsed from runner -- refusing (expected ~43)")
    return out


DEFAULT_TARGET = "/mnt/Backups/Ubuntu/Yamaguchi"
# ext4, and NOT inside the backup source: filter 36 already excludes /home/pcalnon/.cache/,
# so Duplicati's temp volumes cannot be picked up by the scan that writes them.  The server
# runs as root and its own default is /tmp, which is tmpfs -- the run-1 trap this setting
# exists to avoid.
DEFAULT_TEMPDIR = "/home/pcalnon/.cache/duplicati-tmp"
DEFAULT_RECORD_DIR = "/media/pcalnon/temp_backups/_fresh_dlist_check"


def parse_args():
    ap = argparse.ArgumentParser(description="build and import the Yamaguchi backup job")
    ap.add_argument("--target", default=DEFAULT_TARGET,
                    help=f"destination directory, converted to file:// (default {DEFAULT_TARGET})")
    ap.add_argument("--tempdir", default=DEFAULT_TEMPDIR,
                    help=f"Duplicati --tempdir; must be durable, non-tmpfs, and outside the backup "
                         f"source or filtered out of it (default {DEFAULT_TEMPDIR})")
    ap.add_argument("--record-dir", default=DEFAULT_RECORD_DIR,
                    help="where the redacted config record is written")
    ap.add_argument("--allow-duplicate", action="store_true",
                    help="import even though a job of this name already exists (refused by default)")
    ap.add_argument("--dry-run", action="store_true", help="write the record, send no POST")
    return ap.parse_args()


def existing_named(tok, name):
    """IDs of jobs already called *name* -- this script POSTs a NEW job, so a match means a duplicate."""
    status, backups = req("GET", "/api/v1/backups", tok)
    if status != 200:
        sys.exit(f"FATAL: GET /api/v1/backups -> {status}")
    out = []
    for b in backups if isinstance(backups, list) else []:
        bb = b.get("Backup", b)
        if bb.get("Name") == name:
            out.append((bb.get("ID"), bb.get("TargetURL")))
    return out


def main():
    args = parse_args()
    excludes = runner_excludes()
    filters = [{"Order": i, "Include": False, "Expression": e} for i, e in enumerate(excludes)]
    n = len(filters)
    filters.append({"Order": n, "Include": False, "Expression": "*.iso"})
    filters.append({"Order": n + 1, "Include": False, "Expression": "*.vdi"})

    settings = [
        {"Name": "encryption-module", "Value": "gpg"},
        {"Name": "compression-module", "Value": "zip"},
        {"Name": "passphrase", "Value": read_passphrase()},
        {"Name": "retention-policy", "Value": "1W:1D,1M:1W,1Y:1M,3Y:2M"},
        {"Name": "--blocksize", "Value": "1MB"},
        {"Name": "--dblock-size", "Value": "500MB"},
        {"Name": "--skip-files-larger-than", "Value": "8GB"},
        {"Name": "--no-auto-compact", "Value": "true"},
        {"Name": "--allow-missing-source", "Value": "true"},
        {"Name": "--asynchronous-upload-limit", "Value": "1"},
        {"Name": "--gpg-encryption-switches", "Value": "--compress-algo none"},
        {"Name": "--tempdir", "Value": args.tempdir},
    ]

    cfg = {
        "Backup": {
            "Name": "Yamaguchi",
            "Description": "Full /home/pcalnon backup. Recreated 2026-08-25 with the "
                           "GPGFlushError investigation settings (juniper-ml notes, 2026-08-24). "
                           "no-auto-compact is load-bearing; do not remove without reading the notes.",
            "TargetURL": "file://" + args.target,
            "Sources": ["/home/pcalnon/"],
            "Settings": settings,
            "Filters": filters,
        },
        "Schedule": {
            "Time": "2026-08-25T18:00:00Z",
            "Repeat": "1D",
            "AllowedDays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        },
    }

    print(f"config: {len(filters)} filters, {len(settings)} settings")

    # Guards BEFORE any write.  The record used to be written first, so a run that was then
    # refused had already overwritten the provenance record of the ORIGINAL import -- the
    # 2026-08-25 record naming the pre-migration destination.  A refused run must leave no
    # trace (observed and recovered from the sda1 archive, note 8.14).
    tok = login()
    dupes = existing_named(tok, cfg["Backup"]["Name"])
    if dupes:
        msg = ("REFUSE: a backup named %r already exists (%s). This script POSTs a NEW job, so "
               "continuing would create a SECOND one -- two jobs backing up the same sources to "
               "possibly different destinations. Pass --allow-duplicate only if that is intended."
               % (cfg["Backup"]["Name"], ", ".join(f"id={i} target={t}" for i, t in dupes)))
        if not args.allow_duplicate:
            sys.exit(msg)
        print("WARNING: " + msg.replace("REFUSE: ", ""))
    print(f"target: file://{args.target}   tempdir: {args.tempdir}")
    if args.dry_run:
        print("DRY RUN: no POST sent, no record written")
        return

    redacted = json.loads(json.dumps(cfg))
    for st in redacted["Backup"]["Settings"]:
        if st["Name"] == "passphrase":
            st["Value"] = "<redacted>"
    os.makedirs(args.record_dir, exist_ok=True)
    record = os.path.join(args.record_dir, "yamaguchi-config-imported.json")
    if os.path.exists(record):
        # Never clobber an earlier import's record: each import is a distinct provenance fact.
        record = os.path.join(args.record_dir,
                              f"yamaguchi-config-imported-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    with open(record, "w") as fh:
        json.dump(redacted, fh, indent=1)
    print(f"record: {record} (passphrase redacted)")

    status, body = req("POST", "/api/v1/backups?temporary=false", tok, body=cfg)
    print(f"import: {status} {json.dumps(body)[:300]}")
    if status != 200:
        sys.exit(1)
    status, backups = req("GET", "/api/v1/backups", tok)
    for b in backups if isinstance(backups, list) else []:
        bb = b.get("Backup", b)
        print(f"backup id={bb.get('ID')} name={bb.get('Name')!r} target={bb.get('TargetURL')}")


if __name__ == "__main__":
    main()
