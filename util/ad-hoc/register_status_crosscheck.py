#!/usr/bin/env python3
"""Cross-check the defect register's §2 prose against its §4 tables.

Project:     Juniper
Sub-Project: juniper-ml
Application: defect-register tooling
Author:      Paul Calnon
Version:     0.1.0
License:     MIT

`util/ad-hoc/register_open_set.py` and the §1 `grep -cE '\\*\\*FIXED'` count both
read the SAME source -- the §4 table rows -- so they can agree with each other and
still both be wrong. They are one measurement reported twice, not two measurements.

This is the independent third reading: the §2 Status paragraph enumerates every
fixed id in prose, and §5.1 carries one verification row per fixed id. A row can be
marked ``**FIXED`` in its §4 table row and never reach §2 or §5.1 (the close protocol
missed a touch), or be listed in §2 prose while its table row still reads open.
Either way the register lies to the next reader and every count-based check passes.

Exit status is 0 when the three sets agree, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REGISTER = (
    Path(__file__).resolve().parents[2]
    / "notes"
    / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
)

ID_RE = re.compile(r"APD-[A-Z]+-\d+[ab]?")
# A §4 table row: leading pipe, the id, then the status cell.
TABLE_ROW_RE = re.compile(r"^\| (APD-[A-Z]+-\d+[ab]?) *†? *\|")


def _status_cell(line: str) -> str:
    """Second pipe cell -- the status marker on a §4 row, the finding on a §5.1 row.

    ``**FIXED`` is only a close when it lives HERE. A whole-line search treats a
    §5.1 verification cell that *mentions* ``**FIXED`` as a table close -- the
    exact false-AGREE the third reading exists to catch.
    """
    cells = line.split("|")
    return cells[2] if len(cells) > 2 else ""


def crosscheck(text: str) -> int:
    """Compare §4 **FIXED rows against the §2 prose list and the §5.1 table.

    Extracted so a fixture can drive the three-set agreement without touching
    the living register. Exit 0 on AGREE, 1 on DISAGREE or missing headings.
    """
    lines = text.splitlines()

    # -- §4 table rows: the machine-readable source of truth -------------------
    table_fixed: set[str] = set()
    table_all: set[str] = set()
    for line in lines:
        match = TABLE_ROW_RE.match(line)
        if not match:
            continue
        entry_id = match.group(1)
        # A row can appear in both a §4 table and a §5.1 verification table;
        # §5.1 rows are the ones whose second cell is not a status marker.
        table_all.add(entry_id)
        if "**FIXED" in _status_cell(line):
            table_fixed.add(entry_id)

    # -- §2 Status paragraph: the prose enumeration ----------------------------
    status_line = ""
    for line in lines:
        if line.startswith("**Seventy") or "have since been fixed**" in line:
            status_line = line
            break
    prose_fixed = set(ID_RE.findall(status_line))

    # -- §5.1 verification rows ------------------------------------------------
    # Everything from the §5.1 heading to the §5.2 heading.
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("### 5.1"))
        end = next(i for i, line in enumerate(lines) if line.startswith("### 5.2"))
    except StopIteration:
        print("could not locate §5.1/§5.2 headings", file=sys.stderr)
        return 1
    verified: set[str] = set()
    for line in lines[start:end]:
        if line.startswith("| APD-"):
            verified.update(ID_RE.findall(line.split("|")[1]))

    print(f"§4 tables      : {len(table_all)} rows, {len(table_fixed)} marked **FIXED")
    print(f"§2 prose list  : {len(prose_fixed)} ids enumerated")
    print(f"§5.1 verified  : {len(verified)} verification rows")

    ok = True
    for label, other in (("§2 prose", prose_fixed), ("§5.1 rows", verified)):
        missing = table_fixed - other
        extra = other - table_fixed
        if missing:
            ok = False
            print(f"\nFIXED in §4 but absent from {label}: {sorted(missing)}")
        if extra:
            ok = False
            print(f"\nIn {label} but NOT **FIXED in §4: {sorted(extra)}")

    print("\nAGREE" if ok else "\nDISAGREE")
    return 0 if ok else 1


def main() -> int:
    return crosscheck(REGISTER.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
