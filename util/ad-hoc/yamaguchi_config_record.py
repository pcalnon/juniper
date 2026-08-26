#!/usr/bin/env python3
"""
Export the live Yamaguchi job (id 2) as a passphrase-redacted config-of-record JSON.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — investigation (Yamaguchi scope-widening re-baseline)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§3, §8)

The server's /export endpoint 400s on this host, so the record is the raw
``GET /api/v1/backup/<id>`` body (Schedule + Backup + DisplayNames -- the same
shape as ``_yamaguchi_check/yamaguchi-config-final.json``) with every
``passphrase`` setting value replaced by ``<redacted>``. Nothing else is
altered, so two records diff cleanly. A one-screen summary (sources, filter
count, settings, schedule, metadata) is printed for the certification note.

    python3 util/ad-hoc/yamaguchi_config_record.py --out /media/pcalnon/temp_backups/_yamaguchi_check/yamaguchi-config-post-widening.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

REDACT_NAMES = {"passphrase", "--passphrase", "auth-password", "--auth-password"}


def redact(cfg):
    n = 0
    for s in (cfg.get("Backup") or {}).get("Settings") or []:
        if s.get("Name") in REDACT_NAMES and s.get("Value"):
            s["Value"] = "<redacted>"
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="passphrase-redacted config-of-record export of a Duplicati server job")
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tok = api.login()
    status, cfg = api.req("GET", f"/api/v1/backup/{args.backup_id}", tok)
    if status != 200 or "Backup" not in cfg:
        sys.exit(f"FATAL: GET backup {args.backup_id} -> {status}: {json.dumps(cfg)[:300]}")
    n = redact(cfg)
    if n == 0:
        sys.exit("FATAL: no passphrase setting found to redact -- refusing to write a record whose secret handling is unverified")
    with open(args.out, "w") as fh:
        json.dump(cfg, fh, indent=1)
    if "redacted" not in open(args.out).read():
        os.unlink(args.out)
        sys.exit("FATAL: redaction marker missing from the written file")

    b = cfg["Backup"]
    sch = cfg.get("Schedule") or {}
    meta = b.get("Metadata") or {}
    print(f"record      : {args.out} ({n} secret value(s) redacted)")
    print(f"backup      : id={b.get('ID')} name={b.get('Name')!r} target={b.get('TargetURL')} dbpath={b.get('DBPath')}")
    print(f"sources     : {json.dumps(b.get('Sources'))}")
    print(f"filters     : {len(b.get('Filters') or [])}")
    print("settings    : " + ", ".join(f"{s.get('Name')}={s.get('Value')}" for s in b.get("Settings") or []))
    print(f"schedule    : Time={sch.get('Time')} Repeat={sch.get('Repeat')} LastRun={sch.get('LastRun')} AllowedDays={sch.get('AllowedDays')}")
    print("metadata    : " + ", ".join(f"{k}={meta.get(k)}" for k in (
        "LastBackupDate", "LastBackupStarted", "LastBackupFinished", "LastBackupDuration", "BackupListCount",
        "TargetFilesCount", "TargetFilesSize", "TargetFilesetsCount", "SourceFilesCount", "SourceFilesSize",
        "LastErrorDate", "LastErrorMessage")))


if __name__ == "__main__":
    main()
