#!/usr/bin/env python3
"""Re-derive the defect-register open set from row markers.

Project:     Juniper
Sub-Project: juniper-ml
Application: defect-register round-28 verification
Author:      Paul Calnon
License:     MIT License

An ID is FIXED if ANY of its rows carries the marker (fixed IDs appear twice:
the section-4 detail row and the section-5.1 verification row).
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

REG = pathlib.Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md")
ROW_RE = re.compile(r"\| (APD-[A-Z]+-\d+[ab]?) ")
FIXED_MARK = "**FIXED"


def parse_register(text: str) -> tuple[set[str], set[str]]:
    """Return ``(seen, fixed)`` unique APD ids from table rows.

    An id is FIXED if ANY of its rows carries the ``**FIXED`` token. That is the
    machine-readable close marker the register's §1 protocol cites; a second
    marker, or ``FIXED`` without the stars, leaves the row counted OPEN.
    """
    seen: set[str] = set()
    fixed: set[str] = set()
    for line in text.split("\n"):
        match = ROW_RE.match(line)
        if not match:
            continue
        entry_id = match.group(1)
        seen.add(entry_id)
        if FIXED_MARK in line:
            fixed.add(entry_id)
    return seen, fixed


def format_report(seen: set[str], fixed: set[str]) -> str:
    """Render the operator headline, prefix histogram, and open-id list."""
    open_ids = seen - fixed
    by_repo = collections.Counter(i.rsplit("-", 1)[0] for i in sorted(open_ids))
    lines = [
        f"{len(seen)} rows | {len(fixed)} fixed | {len(open_ids)} open",
        "",
        "OPEN by prefix:",
    ]
    for key, count in sorted(by_repo.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"  {key:<20} {count}")
    lines.append("")
    lines.append("OPEN ids:")
    for entry_id in sorted(open_ids):
        lines.append(f"  {entry_id}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    del argv  # path stays CWD-relative so operator usage is unchanged
    text = REG.read_text()
    seen, fixed = parse_register(text)
    print(format_report(seen, fixed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
