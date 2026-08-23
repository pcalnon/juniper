#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Verify that destination volumes which are PRESENT are also INTACT.

Why this exists
---------------
``duplicati_offline_broken_files.py`` decides a volume survives by
**filename presence**. Adversarial review correctly identified that as a gap: a
volume that is present but truncated or bit-rotted is silently counted as fully
intact, which would make the damage figure an *under*-estimate and would make
"restorable" claims about the surviving restore points too strong.

This closes that gap using the archived job database's own recorded
``Remotevolume.Size`` and ``Remotevolume.Hash``:

* **size check** — cheap (one ``stat`` per file), run over every present volume;
  catches truncation, which is the overwhelmingly likely corruption mode for an
  interrupted write.
* **hash check** — expensive (reads the whole file), so it runs over a random
  sample by default. ``Remotevolume.Hash`` is the SHA-256 of the *uploaded*
  (encrypted) file, base64-encoded, so this needs no passphrase.

Read-only. Opens the archived database ``immutable=1`` and never writes.

Usage
-----
    python3 util/ad-hoc/duplicati_verify_volumes.py \
        --db "/home/pcalnon/.config/Duplicati/backup SJTCQIIZSJ 20260712033545.sqlite" \
        --dest /mnt/Backups/Ubuntu --hash-sample 40
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import random
import sqlite3
import time
from urllib.parse import quote

T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def human(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PiB"


def sha256_b64(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(4 << 20), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--hash-sample", type=int, default=40,
                    help="how many present volumes to fully hash (0 = none, -1 = all)")
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--min-present", type=int, default=100,
                    help="refuse if fewer than this many recorded volumes are found "
                         "at --dest. Guards against a wrong or unmounted destination, "
                         "which would otherwise report '0 mismatches' and exit 0.")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    conn = sqlite3.connect(
        "file:" + quote(os.path.abspath(args.db)) + "?immutable=1", uri=True)
    conn.row_factory = sqlite3.Row

    rows = list(conn.execute(
        "SELECT Name, Size, Hash, Type, State FROM Remotevolume"))
    log(f"volumes recorded in archived DB: {len(rows)}")

    present, absent = [], 0
    for r in rows:
        p = os.path.join(args.dest, r["Name"])
        if os.path.exists(p):
            present.append((r, p))
        else:
            absent += 1
    log(f"  present on disk: {len(present)}   absent: {absent}")

    # REFUSE rather than report a vacuous pass. With a wrong or unmounted --dest
    # every row is "absent", the size loop never executes, the hash stage takes
    # the `not hashable` branch, and the script prints "0 mismatches" and exits
    # 0 -- indistinguishable from a genuine clean bill of health. This is the
    # tool someone consults before trusting a restore point, so a false "all
    # clear" here is the most expensive failure in the whole toolkit.
    if not os.path.isdir(args.dest):
        log(f"!! REFUSING: --dest is not a directory: {args.dest}")
        return 2
    if len(present) < args.min_present:
        log(f"!! REFUSING: only {len(present)} of {len(rows)} recorded volumes were "
            f"found under {args.dest} (floor --min-present={args.min_present}).")
        log("   That is what a wrong, mistyped, or UNMOUNTED destination looks like.")
        log(f"   Verify first:  mountpoint -q {args.dest} || echo 'NOT MOUNTED'")
        log("   Refusing rather than reporting '0 mismatches', which would read as a pass.")
        return 2
    print(flush=True)

    # ---- size check over every present volume --------------------------------
    size_ok = size_bad = size_unknown = 0
    bad: list[str] = []
    for r, p in present:
        rec = r["Size"]
        if rec is None or rec <= 0:
            size_unknown += 1
            continue
        try:
            actual = os.path.getsize(p)
        except OSError as exc:
            bad.append(f"{r['Name']}: stat failed: {exc}")
            size_bad += 1
            continue
        if actual == rec:
            size_ok += 1
        else:
            size_bad += 1
            delta = actual - rec
            bad.append(f"{r['Name']}: recorded {rec}, on disk {actual} "
                       f"({'+' if delta > 0 else ''}{delta})")

    print("=== SIZE check (every present volume) ===")
    print(f"  matches recorded size : {size_ok}")
    print(f"  MISMATCH              : {size_bad}")
    print(f"  no size recorded      : {size_unknown}")
    for line in bad[:40]:
        print(f"    !! {line}")
    if len(bad) > 40:
        print(f"    ... and {len(bad) - 40} more")
    print(flush=True)

    # ---- hash check over a sample --------------------------------------------
    hashable = [(r, p) for r, p in present if r["Hash"]]
    if args.hash_sample == 0 or not hashable:
        if not hashable:
            print("=== HASH check: NO volume carries a recorded hash — nothing verified ===")
            return 2
        print("=== HASH check skipped (--hash-sample 0) ===")
        return 0 if size_bad == 0 else 1
    sample = hashable if args.hash_sample < 0 else rng.sample(
        hashable, min(args.hash_sample, len(hashable)))
    total_bytes = sum(os.path.getsize(p) for _, p in sample if os.path.exists(p))
    print(f"=== HASH check ({len(sample)} volumes, {human(total_bytes)}) ===")

    h_ok = h_bad = 0
    for i, (r, p) in enumerate(sample, 1):
        try:
            got = sha256_b64(p)
        except OSError as exc:
            print(f"  !! {r['Name']}: read failed: {exc}")
            h_bad += 1
            continue
        if got == r["Hash"]:
            h_ok += 1
        else:
            h_bad += 1
            print(f"  !! {r['Name']}: HASH MISMATCH")
            print(f"       recorded {r['Hash']}")
            print(f"       computed {got}")
        if i % 10 == 0:
            log(f"  hashed {i}/{len(sample)}")

    print()
    print(f"  hash matches : {h_ok}")
    print(f"  HASH BAD     : {h_bad}")
    print()
    verdict = (size_bad == 0 and h_bad == 0)
    print("RESULT:", "all checked volumes INTACT" if verdict
          else "INTEGRITY PROBLEMS FOUND — see above")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
