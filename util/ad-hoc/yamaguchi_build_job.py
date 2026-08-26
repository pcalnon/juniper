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
* Destination: file:///media/pcalnon/temp_backups/Yamaguchi (dedicated
  subdirectory -- never the mount root).

The passphrase is read from ~/.config/duplicati-backup/env (PASSPHRASE, the
fresh-set key) inside this process; it appears in no argv and no output.
"""

import json
import os
import re
import sys

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


def main():
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
        {"Name": "--tempdir", "Value": "/media/pcalnon/temp_backups/_duplicati_tmp"},
    ]

    cfg = {
        "Backup": {
            "Name": "Yamaguchi",
            "Description": "Full /home/pcalnon backup. Recreated 2026-08-25 with the "
                           "GPGFlushError investigation settings (juniper-ml notes, 2026-08-24). "
                           "no-auto-compact is load-bearing; do not remove without reading the notes.",
            "TargetURL": "file:///media/pcalnon/temp_backups/Yamaguchi",
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

    redacted = json.loads(json.dumps(cfg))
    for s in redacted["Backup"]["Settings"]:
        if s["Name"] == "passphrase":
            s["Value"] = "<redacted>"
    with open("/media/pcalnon/temp_backups/_fresh_dlist_check/yamaguchi-config-imported.json", "w") as fh:
        json.dump(redacted, fh, indent=1)
    print(f"config: {len(filters)} filters, {len(settings)} settings; record written (passphrase redacted)")

    tok = login()
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
