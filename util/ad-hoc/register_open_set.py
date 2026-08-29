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
import collections
import pathlib
import re

REG = pathlib.Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md")
text = REG.read_text()
fixed, seen = set(), set()
for line in text.split("\n"):
    m = re.match(r"\| (APD-[A-Z]+-\d+[ab]?) ", line)
    if not m:
        continue
    seen.add(m.group(1))
    if "**FIXED" in line:
        fixed.add(m.group(1))
print(f"{len(seen)} rows | {len(fixed)} fixed | {len(seen - fixed)} open")
by_repo = collections.Counter(i.rsplit("-", 1)[0] for i in sorted(seen - fixed))
print("\nOPEN by prefix:")
for k, v in sorted(by_repo.items(), key=lambda kv: (-kv[1], kv[0])):
    print(f"  {k:<20} {v}")
print("\nOPEN ids:")
for i in sorted(seen - fixed):
    print(f"  {i}")
