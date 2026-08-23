#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.3.0
License:     MIT License

Offline equivalent of Duplicati's ``list-broken-files``, computed from an
*archived* job database plus a directory listing of the destination.

Why this exists
---------------
The live ``Ubuntu`` job database is mid-Recreate and unusable, and running the
real ``list-broken-files`` needs the GPG passphrase, which is only reachable
through the authenticated web UI.  The archived 2026-07-12 job database predates
the 2026-07-13 deletion event, so it still holds the complete
block -> blockset -> file -> fileset mapping.  Cross-referencing it against the
volumes that actually survive on disk answers the decisive question -- *are any
of the surviving restore points missing data?* -- with no credential, no
passphrase, and no writes.

Correctness notes
-----------------
* The archived database is opened ``immutable=1``: no ``-wal``/``-shm`` sidecar
  is created and no write can occur.
* The mapping is only valid because **no replacement volumes were written**
  after the archived snapshot (newest destination file 2026-07-11 09:58,
  destination directory mtime 2026-07-13 17:26 -- deletion only).  Had a compact
  repacked blocks into new volumes, ``Block.VolumeID`` would be stale and this
  analysis would be worthless.  ``--verify-no-newer`` re-checks that
  precondition and refuses to run if it no longer holds.
* Damage is evaluated over all three ways a restore can fail:
    1. a **content** block of the file is gone,
    2. a **metadata** block of the file is gone,
    3. a **blocklist** block is gone -- the extra indirection large files use to
       store their block list; losing it makes the file unreadable even if every
       data block survives.
* Set-based throughout.  The naive per-file ``EXISTS`` formulation is ~10^7
  correlated subqueries and does not terminate in useful time.

Usage
-----
    python3 util/ad-hoc/duplicati_offline_broken_files.py \
        --db "/home/pcalnon/.config/Duplicati/backup SJTCQIIZSJ 20260712033545.sqlite" \
        --dest /mnt/Backups/Ubuntu
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sqlite3
import time
from urllib.parse import quote

T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def connect_immutable(path: str) -> sqlite3.Connection:
    uri = "file:" + quote(os.path.abspath(path)) + "?immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--verify-no-newer", default="2026-07-12")
    args = ap.parse_args()

    present = {n for n in os.listdir(args.dest) if n.endswith(".gpg")}
    log(f"destination volumes present: {len(present)}")

    newest = max((os.path.getmtime(os.path.join(args.dest, n)) for n in present),
                 default=0.0)
    newest_s = dt.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M:%S")
    log(f"newest destination volume mtime: {newest_s}")
    if newest_s[:10] > args.verify_no_newer:
        log("!! PRECONDITION FAILED: destination has volumes newer than the "
            "archived DB; Block.VolumeID may be stale. Refusing.")
        return 3
    log("precondition OK: deletion-only since the archived snapshot")

    conn = connect_immutable(args.db)
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -2000000")  # ~2 GB page cache

    # ---- 1. which Blocks-type volumes are gone? ------------------------------
    vols = list(conn.execute(
        "SELECT ID, Name, State FROM Remotevolume WHERE Type = 'Blocks'"))
    missing, live = [], []
    for v in vols:
        (live if v["Name"] in present else missing).append(v)
    by_state: dict[str, int] = {}
    for v in missing:
        by_state[v["State"]] = by_state.get(v["State"], 0) + 1
    log(f"Blocks volumes in archived DB: {len(vols)}  "
        f"present={len(live)}  MISSING={len(missing)}")
    log(f"  missing by recorded state: {by_state}")
    if not missing:
        log("nothing missing")
        return 0

    conn.execute("CREATE TEMP TABLE missing_vol (ID INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO missing_vol VALUES (?)",
                     [(v["ID"],) for v in missing])

    # ---- 2. blocks that lived in those volumes -------------------------------
    # A block is only genuinely lost if EVERY copy of it is gone.  Duplicati
    # records additional copies in DuplicateBlock, so a block whose primary
    # Block.VolumeID is missing may still be readable from a surviving volume.
    # Ignoring this over-reports damage; it is the difference between an upper
    # bound and the real answer.
    conn.execute("CREATE TEMP TABLE lost_block (ID INTEGER PRIMARY KEY)")
    conn.execute("""
        INSERT INTO lost_block
        SELECT b.ID FROM Block b
        WHERE b.VolumeID IN (SELECT ID FROM missing_vol)
          AND NOT EXISTS (
              SELECT 1 FROM DuplicateBlock d
              WHERE d.BlockID = b.ID
                AND d.VolumeID NOT IN (SELECT ID FROM missing_vol))
    """)
    n_lost = conn.execute("SELECT COUNT(*) FROM lost_block").fetchone()[0]
    n_all = conn.execute("SELECT COUNT(*) FROM Block").fetchone()[0]
    n_naive = conn.execute(
        "SELECT COUNT(*) FROM Block WHERE VolumeID IN (SELECT ID FROM missing_vol)"
    ).fetchone()[0]
    log(f"blocks: {n_all} total, {n_naive} with primary copy in a missing volume")
    log(f"  of those, RESCUED by a surviving duplicate: {n_naive - n_lost}")
    log(f"  genuinely lost (no surviving copy)        : {n_lost} "
        f"({100.0 * n_lost / max(n_all, 1):.1f}% of all blocks)")

    # hashes of genuinely-lost blocks, for the blocklist-indirection check
    conn.execute("CREATE TEMP TABLE lost_hash (Hash TEXT PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO lost_hash "
                 "SELECT Hash FROM Block WHERE ID IN (SELECT ID FROM lost_block)")
    log("lost-block hash set built")

    # ---- 3. blocksets that lose at least one block ---------------------------
    conn.execute("CREATE TEMP TABLE lost_blockset (ID INTEGER PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO lost_blockset "
                 "SELECT DISTINCT BlocksetID FROM BlocksetEntry "
                 "WHERE BlockID IN (SELECT ID FROM lost_block)")
    n_bs_direct = conn.execute("SELECT COUNT(*) FROM lost_blockset").fetchone()[0]
    log(f"blocksets losing a CONTENT block: {n_bs_direct}")

    # blocksets whose blocklist block is gone (large-file indirection)
    conn.execute("INSERT OR IGNORE INTO lost_blockset "
                 "SELECT DISTINCT BlocksetID FROM BlocklistHash "
                 "WHERE Hash IN (SELECT Hash FROM lost_hash)")
    n_bs_all = conn.execute("SELECT COUNT(*) FROM lost_blockset").fetchone()[0]
    log(f"blocksets unreadable incl. lost BLOCKLIST blocks: {n_bs_all} "
        f"(+{n_bs_all - n_bs_direct} via blocklist indirection)")

    # ---- 4. metadatasets built on a lost blockset ----------------------------
    conn.execute("CREATE TEMP TABLE lost_meta (ID INTEGER PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO lost_meta "
                 "SELECT ID FROM Metadataset "
                 "WHERE BlocksetID IN (SELECT ID FROM lost_blockset)")
    n_meta = conn.execute("SELECT COUNT(*) FROM lost_meta").fetchone()[0]
    log(f"metadatasets affected: {n_meta}")

    # ---- 5. filesets, surviving vs deleted -----------------------------------
    fs = list(conn.execute(
        "SELECT f.ID, f.Timestamp, r.Name AS VolName "
        "FROM Fileset f JOIN Remotevolume r ON r.ID = f.VolumeID "
        "ORDER BY f.Timestamp"))
    surviving = [r for r in fs if r["VolName"] in present]
    deleted = [r for r in fs if r["VolName"] not in present]
    log(f"filesets in archived DB: {len(fs)}  "
        f"surviving={len(surviving)}  deleted-since={len(deleted)}")
    print(flush=True)

    print("=== restore points DELETED between the snapshot and today ===",
          flush=True)
    for r in deleted:
        print("   %s" % dt.datetime.fromtimestamp(r["Timestamp"])
              .strftime("%Y-%m-%d %H:%M"), flush=True)
    print(flush=True)

    # ---- 6. damage per surviving fileset -------------------------------------
    print("=== SURVIVING restore points: damage assessment ===", flush=True)
    print(f"{'restore point':20} {'entries':>10} {'damaged':>9}   verdict", flush=True)
    results = []
    for r in surviving:
        fid = r["ID"]
        ts = dt.datetime.fromtimestamp(r["Timestamp"]).strftime("%Y-%m-%d %H:%M")
        total = conn.execute(
            "SELECT COUNT(*) FROM FilesetEntry WHERE FilesetID = ?", (fid,)
        ).fetchone()[0]
        damaged = conn.execute("""
            SELECT COUNT(*)
            FROM FilesetEntry fe
            JOIN FileLookup fl ON fl.ID = fe.FileID
            WHERE fe.FilesetID = ?
              AND (fl.BlocksetID IN (SELECT ID FROM lost_blockset)
                OR fl.MetadataID IN (SELECT ID FROM lost_meta))
        """, (fid,)).fetchone()[0]
        verdict = "OK" if damaged == 0 else "BROKEN"
        results.append((ts, total, damaged, verdict))
        print(f"{ts:20} {total:10d} {damaged:9d}   {verdict}", flush=True)

    print(flush=True)
    broken = [r for r in results if r[3] == "BROKEN"]
    if broken:
        print(f"OVERALL: DAMAGE FOUND in {len(broken)} of {len(results)} "
              f"surviving restore points", flush=True)
    else:
        print(f"OVERALL: all {len(results)} surviving restore points are "
              f"COMPLETE -- no reference to any missing volume", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
