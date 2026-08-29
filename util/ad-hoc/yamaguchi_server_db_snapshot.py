#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Yamaguchi backup -- server DB snapshot
Author      : Paul Calnon
Version     : 1.0.0
License     : MIT License

Capture a consistent copy of the Duplicati *server* database into a path the
Yamaguchi job actually backs up.

Two databases live in root-only /usr/lib/duplicati/data/, and they have opposite
loss profiles (note section 8.19):

  BMXWPAOGLP.sqlite       the per-job LOCAL INDEX. "Recreate" rebuilds it from
                          the destination. Slow, not fatal. NOT copied here.

  Duplicati-server.sqlite the BRAIN: job definition, 2 sources, 44 filters, 10
                          settings, the schedule, and the encrypted passphrase.
                          "Recreate" does NOT restore it. This is what we copy.

Why sqlite3.backup() and not cp: the server is running and writing. A byte copy
of a live SQLite file can land mid-transaction and restore as a corrupt DB that
still opens. The online-backup API takes a consistent snapshot of a live
database; `PRAGMA integrity_check` on the result then proves it.

Destination default: /home/pcalnon/.local/state/duplicati-server-db/
  - inside backup Source /home/pcalnon/
  - matched by NONE of the job's 44 exclusion filters (verified 2026-08-29;
    filter 36 excludes .cache/ and filter 37 .local/share/Steam/, neither of
    which covers .local/state/)
  - so the snapshot rides along in the next backup

NOTE this does NOT solve key escrow, and must not be mistaken for it. The
passphrase inside this DB is encrypted, and the archive this DB is copied into
is encrypted with the very key you would be trying to recover -- a circle. Key
escrow is yamaguchi_key_escrow.py, and it is a separate, independent control.

Runs as root (the source directory is drwx------ root root).
"""

from __future__ import annotations

import argparse
import os
import pwd
import sqlite3
import sys
from datetime import datetime, timezone

SRC = "/usr/lib/duplicati/data/Duplicati-server.sqlite"
DEST_DIR = "/home/pcalnon/.local/state/duplicati-server-db"
OWNER = "pcalnon"


def human(n):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} GiB"


def main():
    ap = argparse.ArgumentParser(description="Snapshot the Duplicati server DB into a backed-up path.")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--dest-dir", default=DEST_DIR)
    ap.add_argument("--owner", default=OWNER, help="chown the snapshot to this user")
    ap.add_argument("--dry-run", action="store_true", help="check gates, write nothing")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    print(f"== Duplicati server-DB snapshot at {stamp}")

    # Distinguish "absent" from "not root". /usr/lib/duplicati/data is
    # drwx------ root root, so an unprivileged os.path.isfile() on a DB that is
    # perfectly present returns False -- reporting that as "missing" would send
    # an operator hunting for a deleted file instead of prefixing sudo.
    try:
        src_size = os.stat(args.src).st_size
    except PermissionError:
        sys.exit(f"REFUSE: cannot stat {args.src} -- permission denied on its "
                 f"directory. This says nothing about whether the DB exists; "
                 f"re-run as root (sudo).")
    except FileNotFoundError:
        sys.exit(f"REFUSE: source DB genuinely absent: {args.src}")
    if not os.access(args.src, os.R_OK):
        sys.exit(f"REFUSE: {args.src} is present but unreadable -- run as root (sudo).")

    print(f"source      : {args.src} ({human(src_size)})")

    dest = os.path.join(args.dest_dir, os.path.basename(args.src))
    print(f"dest        : {dest}")

    if args.dry_run:
        print("dry run -- nothing written")
        return 0

    try:
        pw = pwd.getpwnam(args.owner)
    except KeyError:
        sys.exit(f"REFUSE: no such user: {args.owner}")

    os.makedirs(args.dest_dir, mode=0o700, exist_ok=True)
    os.chown(args.dest_dir, pw.pw_uid, pw.pw_gid)
    os.chmod(args.dest_dir, 0o700)

    tmp = dest + ".tmp"
    if os.path.exists(tmp):
        os.unlink(tmp)

    # Online backup API: consistent snapshot of a live, actively-written DB.
    src_conn = sqlite3.connect(f"file:{args.src}?mode=ro", uri=True)
    try:
        dst_conn = sqlite3.connect(tmp)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    # Prove the snapshot is not silently corrupt before it replaces the last
    # good one -- a copy that opens is not the same as a copy that is intact.
    check = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
        tables = check.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    finally:
        check.close()

    if result != "ok":
        os.unlink(tmp)
        sys.exit(f"REFUSE: integrity_check on the snapshot returned {result!r}; "
                 "previous snapshot left in place")

    os.chmod(tmp, 0o600)
    os.chown(tmp, pw.pw_uid, pw.pw_gid)
    os.replace(tmp, dest)

    print(f"integrity   : ok ({tables} tables)")
    print(f"wrote       : {dest} ({human(os.path.getsize(dest))}, mode 0600, owner {args.owner})")
    print("this snapshot rides along in the next Yamaguchi backup (14:00Z daily).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
