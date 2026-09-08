#!/usr/bin/env python3
"""Insert a block of bullets into a Keep-a-Changelog ``[Unreleased]`` section, in place.

Project:     Juniper
Sub-Project: juniper-ml
Application: cross-repo tooling (ad-hoc)
Author:      Paul Calnon
Created:     2026-09-08
Status:      ad-hoc (decision-11 release train)

Why this exists
---------------
The decision-11 release train needs CHANGELOG bullets added to several sibling repos
whose ``[Unreleased]`` sections already carry many hand-written entries, sometimes with
the same ``### Category`` heading appearing twice. A ``sed`` with a broad anchor edits
every match (a mutation check in the predecessor session rewrote eight ``continue``
blocks that way), so this does the one thing needed deterministically:

* ``--after-heading "### Changed"`` -- insert the block right after the FIRST such
  heading found INSIDE ``[Unreleased]`` (never a heading in a released section);
* ``--new-heading "### Removed"`` -- create that heading (plus the block) immediately
  after the ``## [Unreleased]`` line, i.e. as the first category of the section.

The block file's text is inserted verbatim, surrounded by single blank lines. Exit 0 =
written, 1 = anchor not found / block empty, 2 = usage error. The target file is edited
IN PLACE; run on a scratch copy.

Usage
-----
    python3 util/ad-hoc/2026-09-08_changelog_insert.py CHANGELOG.md \
        --after-heading "### Changed" --block changed.md
    python3 util/ad-hoc/2026-09-08_changelog_insert.py CHANGELOG.md \
        --new-heading "### Removed" --block removed.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_UNRELEASED = re.compile(r"^##\s*\[?unreleased\]?", re.IGNORECASE)
_H2 = re.compile(r"^##\s")
_H3 = re.compile(r"^###")


def _unreleased_span(lines: list) -> "tuple[int, int] | None":
    start = None
    for i, line in enumerate(lines):
        if _UNRELEASED.match(line.strip()):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _H2.match(lines[j]) and not _H3.match(lines[j]):
            end = j
            break
    return start, end


def insert(text: str, block: str, *, after_heading: "str | None", new_heading: "str | None") -> "str | None":
    lines = text.splitlines()
    span = _unreleased_span(lines)
    if span is None:
        return None
    start, end = span
    block_lines = block.rstrip("\n").splitlines()
    if not block_lines:
        return None

    if new_heading:
        insert_at = start + 1
        payload = ["", new_heading, ""] + block_lines
    else:
        anchor = None
        for k in range(start + 1, end):
            if lines[k].strip() == after_heading.strip():
                anchor = k
                break
        if anchor is None:
            return None
        insert_at = anchor + 1
        payload = [""] + block_lines

    rebuilt = lines[:insert_at] + payload + lines[insert_at:]
    # Normalise: ensure exactly one blank line after the inserted block.
    if insert_at + len(payload) < len(rebuilt) and rebuilt[insert_at + len(payload)].strip() != "":
        rebuilt.insert(insert_at + len(payload), "")
    out = "\n".join(rebuilt)
    if text.endswith("\n"):
        out += "\n"
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="Insert a bullet block into a CHANGELOG [Unreleased] section")
    ap.add_argument("changelog")
    ap.add_argument("--block", required=True, help="file whose text is inserted verbatim")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--after-heading", help="insert after the FIRST matching '### X' heading inside [Unreleased]")
    g.add_argument("--new-heading", help="create this '### X' heading first in [Unreleased] and insert under it")
    args = ap.parse_args(argv)

    path = Path(args.changelog)
    text = path.read_text(encoding="utf-8")
    block = Path(args.block).read_text(encoding="utf-8")
    out = insert(text, block, after_heading=args.after_heading, new_heading=args.new_heading)
    if out is None:
        print("refused: no [Unreleased] section, anchor heading not found, or empty block", file=sys.stderr)
        return 1
    path.write_text(out, encoding="utf-8")
    print(f"inserted {len(block.rstrip().splitlines())} lines into {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
