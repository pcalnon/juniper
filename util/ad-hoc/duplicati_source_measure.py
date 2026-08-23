#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Measure what the Duplicati ``Ubuntu`` job would actually back up, and what the
``--skip-files-larger-than`` cap silently drops.

Why this exists
---------------
Two numbers gate the fresh-backup-set decision and both are stale:

* the source size cached in the server database is from 2026-07-09, and this
  tree changes daily;
* the 50 MB cap's cost was last estimated at "~121 GB across 74 files", which
  needs a recount and, more importantly, a breakdown of *what* it drops --
  the useful axis is regenerable vs irreplaceable, not file size.

Reads the source root and the exclusion list straight from the live server
database so the measurement cannot drift from the real job configuration.

Read-only. Walks the filesystem; writes nothing anywhere.

Usage
-----
    ionice -c3 nice -n19 python3 util/ad-hoc/duplicati_source_measure.py
    python3 util/ad-hoc/duplicati_source_measure.py --skip-threshold 50MB --top 40
"""

from __future__ import annotations

import argparse
import os
import sqlite3

SERVER_DB = "/home/pcalnon/.config/Duplicati/Duplicati-server.sqlite"


def parse_size(text: str) -> int:
    text = text.strip().upper()
    mult = 1
    for suffix, factor in (("KB", 1024), ("MB", 1024**2), ("GB", 1024**3), ("TB", 1024**4)):
        if text.endswith(suffix):
            mult, text = factor, text[: -len(suffix)]
            break
    return int(float(text) * mult)


def human(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PiB"


def load_job(backup_id: int) -> tuple[str, list[str], str]:
    conn = sqlite3.connect(f"file:{SERVER_DB}?mode=ro", uri=True)
    src = conn.execute("SELECT Path FROM Source WHERE BackupID = ?", (backup_id,)).fetchone()
    excl = [r[0] for r in conn.execute(
        'SELECT Expression FROM Filter WHERE BackupID = ? AND Include = 0 ORDER BY "Order"',
        (backup_id,))]
    cap = conn.execute(
        "SELECT Value FROM Option WHERE BackupID = ? AND Name = '--skip-files-larger-than'",
        (backup_id,)).fetchone()
    return (src[0] if src else "%HOME%"), excl, (cap[0] if cap else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backup-id", type=int, default=2)
    ap.add_argument("--home", default=os.path.expanduser("~"))
    ap.add_argument("--skip-threshold", default=None,
                    help="override the cap read from the job config")
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()

    src, exclusions, cap_cfg = load_job(args.backup_id)
    cap_text = args.skip_threshold or cap_cfg or "50MB"
    cap = parse_size(cap_text)

    root = src.replace("%HOME%", args.home).rstrip("/")
    excl_paths = [e.replace("%HOME%", args.home).rstrip("/") for e in exclusions]
    excl_norm = tuple(p + "/" for p in excl_paths)

    print(f"source root      : {root}")
    print(f"exclusions       : {len(excl_paths)}")
    print(f"size cap         : {cap_text} ({cap} bytes)")
    print(flush=True)

    included_bytes = included_files = 0
    excluded_tree_bytes = excluded_tree_files = 0
    over_cap: list[tuple[int, str]] = []
    errors = 0

    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        # Prune excluded subtrees. Their cost is measured separately below --
        # accounting for them here would be dead code, because pruning dirnames
        # stops os.walk from ever yielding those directories.
        dirnames[:] = [d for d in dirnames
                       if os.path.join(dirpath, d) not in excl_paths
                       and not (os.path.join(dirpath, d) + "/").startswith(excl_norm)]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if full in excl_paths:
                continue
            try:
                st = os.lstat(full)
            except OSError:
                errors += 1
                continue
            if not os.path.isfile(full) or os.path.islink(full):
                continue
            size = st.st_size
            if size > cap:
                over_cap.append((size, full))
            else:
                included_bytes += size
                included_files += 1

    # Measure each excluded subtree on its own, so the number reflects what the
    # exclusion list is actually buying.
    for ep in excl_paths:
        if not os.path.exists(ep):
            continue
        if os.path.isfile(ep):
            try:
                excluded_tree_bytes += os.lstat(ep).st_size
                excluded_tree_files += 1
            except OSError:
                errors += 1
            continue
        for edir, _, efiles in os.walk(ep, onerror=lambda e: None):
            for fn in efiles:
                try:
                    excluded_tree_bytes += os.lstat(os.path.join(edir, fn)).st_size
                    excluded_tree_files += 1
                except OSError:
                    errors += 1

    over_bytes = sum(s for s, _ in over_cap)
    print("=== what the job would actually store ===")
    print(f"  included files          : {included_files:,}")
    print(f"  included bytes          : {human(included_bytes)}")
    print()
    print(f"=== dropped by the {cap_text} cap ===")
    print(f"  files over cap          : {len(over_cap):,}")
    print(f"  bytes over cap          : {human(over_bytes)}")
    if included_bytes + over_bytes:
        pct = 100.0 * over_bytes / (included_bytes + over_bytes)
        print(f"  share of eligible data  : {pct:.1f}%")
    print()
    print(f"=== pruned by the {len(excl_paths)} path exclusions ===")
    print(f"  files                   : {excluded_tree_files:,}")
    print(f"  bytes                   : {human(excluded_tree_bytes)}")
    print()
    if errors:
        print(f"(unreadable entries skipped: {errors})")
        print()

    over_cap.sort(reverse=True)
    print(f"=== largest {min(args.top, len(over_cap))} files dropped by the cap ===")
    for size, path in over_cap[: args.top]:
        print(f"  {human(size):>12}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
