#!/usr/bin/env python3
#####################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-05_changelog_section_reorder.py
# Author:        Paul Calnon
# Version:       0.1.0
# Date:          2026-09-05
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Description:   One-off: merge duplicate `### <Kind>` blocks within a
#                single Keep-a-Changelog release section and reorder
#                them canonically. Written for juniper-cascor-client
#                `[0.8.0]`, which accumulated TWO `### Fixed` and TWO
#                `### Changed` blocks in the order
#                Deprecated/Fixed/Changed/Added/Fixed/Changed.
#####################################################################
"""Reorder one release section of a Keep-a-Changelog file, merging duplicate kinds.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-05
Status: ad-hoc — one-off (reusable: any repo's CHANGELOG can drift the same way)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor-client#157 (the `[0.8.0]` reorder it performed); drift introduced by
    juniper-cascor-client#154.


**Content preservation is the whole game.** A reorder that silently drops an entry is
worse than leaving the section out of order, and a structural check ("6 headings before,
4 after") cannot see it -- so this asserts on the multiset of NON-heading lines, which is
invariant under any pure move/merge. See the juniper-ml memory note
`reference_check_unit_must_match_identity`: a check coarser than the thing's identity
cannot see damage to it.

Usage:
    python3 2026-09-05_changelog_section_reorder.py <CHANGELOG.md> <section>  [--write]

`<section>` is the literal release heading, e.g. `## [0.8.0] - 2026-09-05`.
Without --write it prints the plan and the preservation verdict, changing nothing.
"""

from __future__ import annotations

import argparse
import collections
import sys

# Keep a Changelog 1.1.0 canonical order.
CANONICAL = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


def split_section(lines: list[str], heading: str) -> tuple[int, int]:
    """Return [start, end) line indices of the release section body."""
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip() == heading)
    except StopIteration:
        raise SystemExit(f"section heading not found: {heading!r}")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return start, end


def parse_blocks(body: list[str]) -> tuple[list[str], "collections.OrderedDict[str, list[str]]"]:
    """Split a section body into (preamble, {kind: block_lines}), merging duplicates."""
    preamble: list[str] = []
    blocks: collections.OrderedDict[str, list[str]] = collections.OrderedDict()
    current: str | None = None
    for ln in body:
        if ln.startswith("### "):
            current = ln[4:].strip()
            blocks.setdefault(current, [])
            continue
        if current is None:
            preamble.append(ln)
        else:
            blocks[current].append(ln)
    return preamble, blocks


def strip_edges(block: list[str]) -> list[str]:
    while block and not block[0].strip():
        block.pop(0)
    while block and not block[-1].strip():
        block.pop()
    return block


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("section")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    original = open(args.path, encoding="utf-8").read().splitlines()
    start, end = split_section(original, args.section)
    body = original[start + 1 : end]

    preamble, blocks = parse_blocks(body)
    dupes = {k: v for k, v in blocks.items()}
    print(f"section: {args.section}")
    print(f"  blocks found (post-merge): {list(blocks)}")

    unknown = [k for k in blocks if k not in CANONICAL]
    if unknown:
        print(f"  NOTE: non-canonical kind(s) kept in place at the end: {unknown}")

    ordered = [k for k in CANONICAL if k in dupes] + unknown

    rebuilt: list[str] = [args.section, ""]
    rebuilt.extend(strip_edges(list(preamble)))
    if strip_edges(list(preamble)):
        rebuilt.append("")
    for kind in ordered:
        rebuilt.append(f"### {kind}")
        rebuilt.append("")
        rebuilt.extend(strip_edges(list(dupes[kind])))
        rebuilt.append("")

    new_doc = original[:start] + rebuilt + original[end:]

    # ---- the check that matters: non-heading content is a pure permutation ----
    def payload(lines: list[str]) -> collections.Counter:
        return collections.Counter(
            ln for ln in lines if ln.strip() and not ln.startswith("### ")
        )

    before, after = payload(original), payload(new_doc)
    lost = before - after
    gained = after - before
    print(f"  non-heading lines before={sum(before.values())} after={sum(after.values())}")
    if lost or gained:
        print("  CONTENT NOT PRESERVED -- refusing to write")
        for ln in list(lost)[:10]:
            print(f"    LOST:   {ln[:110]}")
        for ln in list(gained)[:10]:
            print(f"    GAINED: {ln[:110]}")
        return 1
    print("  CONTENT PRESERVED (exact multiset match on non-heading lines)")

    if args.write:
        open(args.path, "w", encoding="utf-8").write("\n".join(new_doc) + "\n")
        print(f"  WROTE {args.path}")
    else:
        print("  dry run -- pass --write to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
