#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

File-size distribution of the Duplicati backup source, for choosing a size cap.

Why this exists
---------------
Choosing ``--skip-files-larger-than`` from a rule of thumb is how the current
50 MB cap came to silently drop four irreplaceable VM images. The cap should be
chosen against the *actual* distribution: how many files and how many bytes sit
above each candidate threshold, and what they are.

Reports the marginal cost of each candidate cap, plus a by-extension breakdown
of everything above the smallest candidate, so the decision is made against
file *identity* rather than file size alone.

Reads the source root and exclusions from the live server database. Read-only.

Usage
-----
    ionice -c3 nice -n19 python3 util/ad-hoc/duplicati_size_histogram.py
"""

from __future__ import annotations

import argparse
import collections
import os
import sqlite3

SERVER_DB = "/home/pcalnon/.config/Duplicati/Duplicati-server.sqlite"
CANDIDATES_MB = [50, 100, 250, 500, 1024, 2048, 4096, 8192, 16384, 32768]


def human(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PiB"


def load_job(backup_id: int):
    conn = sqlite3.connect(f"file:{SERVER_DB}?mode=ro", uri=True)
    src = conn.execute("SELECT Path FROM Source WHERE BackupID=?", (backup_id,)).fetchone()
    excl = [r[0] for r in conn.execute(
        'SELECT Expression FROM Filter WHERE BackupID=? AND Include=0 ORDER BY "Order"',
        (backup_id,))]
    return (src[0] if src else "%HOME%"), excl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backup-id", type=int, default=2)
    ap.add_argument("--home", default=os.path.expanduser("~"))
    ap.add_argument("--subtree", default=None,
                    help="restrict to a subtree (e.g. ~/Development/python/Juniper)")
    ap.add_argument("--extra-exclude", action="append", default=[],
                    help="model an ADDITIONAL exclusion, repeatable. %%HOME%% is expanded. "
                         "Use to answer 'what would the cap cost if I also excluded X?'")
    args = ap.parse_args()

    src, exclusions = load_job(args.backup_id)
    root = (args.subtree or src.replace("%HOME%", args.home)).rstrip("/")
    exclusions = list(exclusions) + list(args.extra_exclude)
    excl_paths = [e.replace("%HOME%", args.home).rstrip("/") for e in exclusions]
    excl_norm = tuple(p + "/" for p in excl_paths)

    print(f"root       : {root}")
    print(f"exclusions : {len(excl_paths)} ({len(excl_paths) - len(args.extra_exclude)} from job config + {len(args.extra_exclude)} modelled)")
    print()

    sizes: list[int] = []
    big: list[tuple[int, str]] = []
    errors = 0
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        dirnames[:] = [d for d in dirnames
                       if os.path.join(dirpath, d) not in excl_paths
                       and not (os.path.join(dirpath, d) + "/").startswith(excl_norm)]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if full in excl_paths:
                continue
            try:
                if os.path.islink(full):
                    continue
                sz = os.lstat(full).st_size
            except OSError:
                errors += 1
                continue
            sizes.append(sz)
            if sz > CANDIDATES_MB[0] * 1024 * 1024:
                big.append((sz, full))

    total_files = len(sizes)
    total_bytes = sum(sizes)
    print(f"files: {total_files:,}   bytes: {human(total_bytes)}")
    if errors:
        print(f"(unreadable entries skipped: {errors})")
    print()

    print("=== marginal cost of each candidate cap ===")
    print(f"{'cap':>10} {'files above':>13} {'bytes above':>14} "
          f"{'% of bytes':>11}   {'files gained vs 50MB':>21}")
    prev_files = prev_bytes = None
    for mb in CANDIDATES_MB:
        thr = mb * 1024 * 1024
        above = [s for s in sizes if s > thr]
        ab_bytes = sum(above)
        pct = 100.0 * ab_bytes / max(total_bytes, 1)
        if prev_files is None:
            gained = "(baseline)"
        else:
            gained = f"+{prev_files - len(above):,} files, +{human(prev_bytes - ab_bytes)}"
        cap_lbl = f"{mb} MB" if mb < 1024 else f"{mb // 1024} GB"
        print(f"{cap_lbl:>10} {len(above):>13,} {human(ab_bytes):>14} {pct:>10.1f}%   {gained:>21}")
        if prev_files is None:
            prev_files, prev_bytes = len(above), ab_bytes

    print()
    print(f"=== what sits above {CANDIDATES_MB[0]} MB, by extension ===")
    by_ext: dict[str, list[int]] = collections.defaultdict(list)
    for sz, path in big:
        ext = os.path.splitext(path)[1].lower() or "(none)"
        by_ext[ext].append(sz)
    rows = sorted(by_ext.items(), key=lambda kv: -sum(kv[1]))
    print(f"{'ext':>12} {'files':>7} {'total':>12} {'mean':>12} {'max':>12}")
    for ext, ss in rows[:20]:
        print(f"{ext:>12} {len(ss):>7,} {human(sum(ss)):>12} "
              f"{human(sum(ss) / len(ss)):>12} {human(max(ss)):>12}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
