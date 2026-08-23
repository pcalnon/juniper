#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Row-level diff between two Duplicati-server.sqlite files.

Purpose
-------
The Duplicati *server* database holds job configuration, schedules, filters and
encrypted credentials.  During the 2026-08-21 recovery session the ``Ubuntu``
job's ``Backup.DBPath`` silently changed to point at the server database itself
(see notes/ handoff, section 1).  Establishing *exactly* what else changed in
that window requires a row-level comparison, because the two files are
byte-different but the same size and there is no upstream tooling for this.

Read-only by construction: both databases are opened with ``mode=ro`` and no
write statement is ever issued.

Usage
-----
    python3 util/ad-hoc/duplicati_server_db_diff.py OLD.sqlite NEW.sqlite
"""

from __future__ import annotations

import os
import sqlite3
import sys
from urllib.parse import quote


def _connect(path: str) -> sqlite3.Connection:
    # quote()+abspath: these databases live next to files whose names contain
    # spaces, which a raw f-string URI mis-parses.
    conn = sqlite3.connect(
        "file:" + quote(os.path.abspath(path)) + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


# Natural keys for the Duplicati server tables that have no `ID` column.
# Without these the fallback was the row's POSITION in an unordered SELECT, which
# is not a row identity: deleting one Filter row shifts every later row and the
# diff reports a wall of phantom "changed" rows while the real deletion never
# appears. 7 of the 15 tables lack `ID`, and they are precisely the ones that
# describe what the job does -- Source, Filter, Option, Metadata.
NATURAL_KEYS: dict[str, tuple[str, ...]] = {
    "Source": ("BackupID", "Path"),
    "Filter": ("BackupID", "Order"),
    "Option": ("BackupID", "Name", "Filter"),
    "Metadata": ("BackupID", "Key"),
    "ErrorLog": ("BackupID", "Timestamp"),
    "Log": ("BackupID", "Start"),
    "UIStorage": ("Scheme", "Key"),
}


def _snapshot(conn: sqlite3.Connection, table: str):
    """Map a stable row key -> full row tuple, for one table.

    Key selection, in order of preference:
      1. an ``ID`` column (a real surrogate key);
      2. a known natural key from NATURAL_KEYS;
      3. the full row tuple itself -- which degrades the comparison to a
         multiset diff (adds/removes only, never "changed"). That is less
         informative but it is *honest*; positional keying was neither.
    """
    cur = conn.execute(f'SELECT * FROM "{table}"')
    cols = [d[0] for d in cur.description]
    if "ID" in cols:
        key_cols: tuple[str, ...] = ("ID",)
    elif table in NATURAL_KEYS and all(c in cols for c in NATURAL_KEYS[table]):
        key_cols = NATURAL_KEYS[table]
    else:
        key_cols = tuple(cols)          # multiset fallback

    out: dict[str, tuple] = {}
    for row in cur.fetchall():
        vals = tuple(row[c] for c in cols)
        key = " | ".join(f"{c}={row[c]!r}" for c in key_cols)
        if key in out and out[key] != vals:
            # Duplicate key with differing values means the chosen key is not
            # unique for this table. Say so rather than silently dropping a row.
            key = f"{key} #dup"
        out[key] = vals
    return out, cols, key_cols


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    old_path, new_path = argv[1], argv[2]
    old, new = _connect(old_path), _connect(new_path)

    print(f"OLD = {old_path}")
    print(f"NEW = {new_path}")
    print()

    old_tables, new_tables = set(_tables(old)), set(_tables(new))
    if old_tables != new_tables:
        print(f"!! table set differs: only-old={old_tables - new_tables} "
              f"only-new={new_tables - old_tables}")

    any_diff = False
    for table in sorted(old_tables & new_tables):
        try:
            o_rows, o_cols, key_cols = _snapshot(old, table)
            n_rows, n_cols, _ = _snapshot(new, table)
        except sqlite3.DatabaseError as exc:  # pragma: no cover - defensive
            print(f"[{table}] unreadable: {exc}")
            continue

        # Never label NEW's values with OLD's column list: if a Duplicati upgrade
        # added or reordered a column between the two captures, zip() would
        # silently misattribute every value after the divergence point.
        if o_cols != n_cols:
            print(f"=== {table} ===")
            print(f"  !! SCHEMA DIFFERS -- old columns {o_cols}")
            print(f"                       new columns {n_cols}")
            print("     Skipping value-level comparison; it would misattribute columns.")
            print()
            any_diff = True
            continue

        added = sorted(set(n_rows) - set(o_rows))
        removed = sorted(set(o_rows) - set(n_rows))
        changed = sorted(k for k in set(o_rows) & set(n_rows) if o_rows[k] != n_rows[k])

        if not (added or removed or changed):
            continue
        any_diff = True
        print(f"=== {table} ===   (keyed by {', '.join(key_cols)})")
        for k in removed:
            print(f"  - REMOVED row [{k}]: {o_rows[k]!r}")
        for k in added:
            print(f"  + ADDED   row [{k}]: {n_rows[k]!r}")
        for k in changed:
            for col, o_val, n_val in zip(o_cols, o_rows[k], n_rows[k]):
                if o_val != n_val:
                    print(f"  ~ row [{k}] .{col}:")
                    print(f"      old = {o_val!r}")
                    print(f"      new = {n_val!r}")
        print()

    if not any_diff:
        print("(no row-level differences)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
