#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Select restore-drill candidates: N files predicted GOOD and N predicted DAMAGED.

The drill exists to convert the offline damage analysis into an end-to-end
result. Predictions must therefore be made *before* any restore is attempted and
recorded with a verification oracle, so the drill can falsify them.

Oracle
------
``Blockset.FullHash`` is the file's **SHA-256** (``Configuration.filehash =
SHA256``), base64-encoded, and ``Blockset.Length`` its byte length.  A restored
file is judged correct only if both match -- exit-code-zero from the restore is
not evidence, because Duplicati can emit a short or zero-length file and still
return success.

Selection
---------
* GOOD: uniform random sample from an intact fileset. The offline analysis found
  0 damaged entries there, so any real file qualifies.
* DAMAGED: sampled by walking *random* missing volumes -> their blocks -> the
  blocksets containing them -> files in the damaged fileset. Sampling random
  volumes rather than taking the first N avoids clustering the sample in one
  region of the archive.

Read-only; opens the archived database ``immutable=1``.

Usage
-----
    python3 util/ad-hoc/duplicati_drill_select.py \
        --db "/home/pcalnon/.config/Duplicati/backup SJTCQIIZSJ 20260712033545.sqlite" \
        --dest /mnt/Backups/Ubuntu --count 5 --seed 20260823 \
        --out /path/to/drill_candidates.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sqlite3
from urllib.parse import quote

# Keep drill files small: a multi-GB restore proves nothing extra and costs
# a full dblock download per block.
MIN_SIZE = 1024
MAX_SIZE = 8 * 1024 * 1024


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect("file:" + quote(os.path.abspath(path)) + "?immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def fileset_by_date(conn, present) -> list[dict]:
    out = []
    for r in conn.execute(
        "SELECT f.ID, f.Timestamp, r.Name AS VolName "
        "FROM Fileset f JOIN Remotevolume r ON r.ID = f.VolumeID ORDER BY f.Timestamp DESC"):
        out.append({
            "id": r["ID"],
            "ts": r["Timestamp"],
            "date": dt.datetime.fromtimestamp(r["Timestamp"]).strftime("%Y-%m-%d %H:%M"),
            "volume": r["VolName"],
            "on_disk": r["VolName"] in present,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--good-fileset", default="2025-11-12")
    ap.add_argument("--bad-fileset", default="2026-07-11")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    present = {n for n in os.listdir(args.dest) if n.endswith(".gpg")}
    conn = connect(args.db)
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -1000000")

    filesets = fileset_by_date(conn, present)
    surviving = [f for f in filesets if f["on_disk"]]

    # DO NOT emit a positional --version index. The archived database predates
    # the deletion and still holds ALL filesets, including those whose dlist is
    # gone; indexing within the surviving subset does NOT agree with indexing
    # over every database row, and it is the database that resolves --version.
    # Measured on this archive: surviving-index 5 is 2025-11-12 (id 341) while
    # all-rows index 5 is 2026-07-06 (id 580) -- a DAMAGED fileset. Worse, the
    # error is invisible to a drill whose sampled files are unchanged between
    # the two, because Duplicati reuses the BlocksetID and both selections then
    # produce byte-identical output. Select by TIMESTAMP instead, which names
    # exactly one fileset regardless of how versions are numbered.
    print("filesets in the archived DB (ALL rows, newest first):")
    for i, f in enumerate(filesets):
        mark = "on-disk" if f["on_disk"] else "DELETED"
        print(f"  all-idx {i:>2}  {f['date']}  id={f['id']:>4}  {mark}")
    print()
    print("NOTE: positional --version is deliberately NOT reported; the drill "
          "selects by --time= instead. See the comment in this file.")
    print()

    good_fs = next(f for f in surviving if f["date"].startswith(args.good_fileset))
    bad_fs = next(f for f in surviving if f["date"].startswith(args.bad_fileset))
    # Duplicati's --time selects the version at-or-before the given instant, so
    # naming the fileset's own timestamp identifies it unambiguously.
    good_time = dt.datetime.fromtimestamp(good_fs["ts"]).strftime("%Y-%m-%dT%H:%M:%S")
    bad_time = dt.datetime.fromtimestamp(bad_fs["ts"]).strftime("%Y-%m-%dT%H:%M:%S")
    print(f"GOOD    fileset {good_fs['date']} (id {good_fs['id']}) -> --time={good_time}")
    print(f"DAMAGED fileset {bad_fs['date']} (id {bad_fs['id']}) -> --time={bad_time}")
    print()

    # ---- missing volumes -----------------------------------------------------
    missing = [r["ID"] for r in conn.execute(
        "SELECT ID, Name FROM Remotevolume WHERE Type='Blocks'") if r["Name"] not in present]
    print(f"missing Blocks volumes: {len(missing)}")
    conn.execute("CREATE TEMP TABLE missing_vol (ID INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO missing_vol VALUES (?)", [(i,) for i in missing])

    # ---- DAMAGED candidates --------------------------------------------------
    rng.shuffle(missing)
    damaged: list[dict] = []
    seen_paths: set[str] = set()
    for vol_id in missing:
        if len(damaged) >= args.count:
            break
        # The NOT EXISTS clause mirrors duplicati_offline_broken_files.py: a block
        # whose primary copy is in a missing volume may still have a surviving
        # copy recorded in DuplicateBlock. Without this, the selector can predict
        # "DAMAGED" for a file Duplicati will restore perfectly -- which would
        # read at drill time as a failed prediction rather than what it is, a
        # selection bug. The two scripts must define "lost" identically.
        rows = conn.execute("""
            SELECT p.Prefix || fl.Path AS path, bs.Length AS len, bs.FullHash AS hash,
                   fl.BlocksetID AS bsid
            FROM Block b
            JOIN BlocksetEntry be ON be.BlockID = b.ID
            JOIN Blockset bs      ON bs.ID = be.BlocksetID
            JOIN FileLookup fl    ON fl.BlocksetID = bs.ID
            JOIN PathPrefix p     ON p.ID = fl.PrefixID
            JOIN FilesetEntry fe  ON fe.FileID = fl.ID AND fe.FilesetID = ?
            WHERE b.VolumeID = ? AND bs.Length BETWEEN ? AND ?
              AND NOT EXISTS (
                  SELECT 1 FROM DuplicateBlock d
                  WHERE d.BlockID = b.ID
                    AND d.VolumeID NOT IN (SELECT ID FROM missing_vol))
            LIMIT 40
        """, (bad_fs["id"], vol_id, MIN_SIZE, MAX_SIZE)).fetchall()
        if not rows:
            continue
        r = rng.choice(rows)
        if r["path"] in seen_paths:
            continue
        seen_paths.add(r["path"])
        damaged.append({"path": r["path"], "size": r["len"], "sha256_b64": r["hash"],
                        "blockset_id": r["bsid"], "from_volume_id": vol_id})
        print(f"  damaged candidate: {r['len']:>10,} B  {r['path']}")

    # ---- GOOD candidates -----------------------------------------------------
    print()
    total = conn.execute("SELECT COUNT(*) FROM FilesetEntry WHERE FilesetID=?",
                         (good_fs["id"],)).fetchone()[0]
    good: list[dict] = []
    tries = 0
    while len(good) < args.count and tries < 400:
        tries += 1
        off = rng.randrange(max(total - 1, 1))
        r = conn.execute("""
            SELECT p.Prefix || fl.Path AS path, bs.Length AS len, bs.FullHash AS hash,
                   fl.BlocksetID AS bsid
            FROM FilesetEntry fe
            JOIN FileLookup fl ON fl.ID = fe.FileID
            JOIN Blockset bs   ON bs.ID = fl.BlocksetID
            JOIN PathPrefix p  ON p.ID = fl.PrefixID
            WHERE fe.FilesetID = ? AND bs.Length BETWEEN ? AND ?
            LIMIT 1 OFFSET ?
        """, (good_fs["id"], MIN_SIZE, MAX_SIZE, off)).fetchone()
        if not r or r["path"] in seen_paths:
            continue
        seen_paths.add(r["path"])
        good.append({"path": r["path"], "size": r["len"], "sha256_b64": r["hash"],
                     "blockset_id": r["bsid"]})
        print(f"  good candidate   : {r['len']:>10,} B  {r['path']}")

    payload = {
        "generated": "seed=%d" % args.seed,
        "good": {"fileset": good_fs["date"], "fileset_id": good_fs["id"],
                 "time": good_time,
                 "predicted": "RESTORES OK", "files": good},
        "damaged": {"fileset": bad_fs["date"], "fileset_id": bad_fs["id"],
                    "time": bad_time,
                    "predicted": "RESTORE FAILS OR HASH MISMATCH", "files": damaged},
    }
    with open(args.out, "w") as fh:
        json.dump(payload, fh, indent=1)
    print()
    print(f"wrote {len(good)} good + {len(damaged)} damaged candidates -> {args.out}")

    # A short list must not look like success. Sampling can under-deliver (the
    # OFFSET is drawn against an unfiltered row count, and the damaged loop can
    # exhaust its pool of missing volumes), and a drill run against an empty or
    # truncated candidate set would silently prove nothing.
    if len(good) < args.count or len(damaged) < args.count:
        print(f"!! UNDER-DELIVERED: asked for {args.count} of each, got "
              f"{len(good)} good / {len(damaged)} damaged. Do NOT treat this run "
              f"as a complete drill.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
