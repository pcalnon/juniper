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

import sqlite3
import sys


def _connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


def _snapshot(conn: sqlite3.Connection, table: str) -> dict[str, tuple]:
    """Map a stable row key -> full row tuple, for one table."""
    cur = conn.execute(f'SELECT * FROM "{table}"')
    cols = [d[0] for d in cur.description]
    key_col = "ID" if "ID" in cols else None
    out: dict[str, tuple] = {}
    for i, row in enumerate(cur.fetchall()):
        vals = tuple(row[c] for c in cols)
        key = str(row[key_col]) if key_col else f"#{i}"
        out[key] = vals
    return out, cols


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
            o_rows, cols = _snapshot(old, table)
            n_rows, _ = _snapshot(new, table)
        except sqlite3.DatabaseError as exc:  # pragma: no cover - defensive
            print(f"[{table}] unreadable: {exc}")
            continue

        added = sorted(set(n_rows) - set(o_rows))
        removed = sorted(set(o_rows) - set(n_rows))
        changed = sorted(k for k in set(o_rows) & set(n_rows) if o_rows[k] != n_rows[k])

        if not (added or removed or changed):
            continue
        any_diff = True
        print(f"=== {table} ===")
        for k in removed:
            print(f"  - REMOVED row {k}: {o_rows[k]!r}")
        for k in added:
            print(f"  + ADDED   row {k}: {n_rows[k]!r}")
        for k in changed:
            for col, o_val, n_val in zip(cols, o_rows[k], n_rows[k]):
                if o_val != n_val:
                    print(f"  ~ row {k} .{col}:")
                    print(f"      old = {o_val!r}")
                    print(f"      new = {n_val!r}")
        print()

    if not any_diff:
        print("(no row-level differences)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
