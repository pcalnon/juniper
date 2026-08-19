#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc forensics
Author:      Paul Calnon
License:     MIT License

Extract a byte window from the shipped Claude Code single-file executable so the
embedded (plaintext) JS bundle can be read.  Single-use forensics helper for the
2026-08-18 memory-file size-limit investigation.

Usage:
    python3 2026-08-18_extract_claude_binary_region.py <offset> <before> <after> <outfile>
"""

import sys

BIN = "/home/pcalnon/.local/share/claude/versions/2.1.235"


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    offset, before, after, outfile = (
        int(sys.argv[1]),
        int(sys.argv[2]),
        int(sys.argv[3]),
        sys.argv[4],
    )
    start = max(0, offset - before)
    length = before + after
    with open(BIN, "rb") as fh:
        fh.seek(start)
        blob = fh.read(length)
    text = blob.decode("utf-8", errors="replace")
    with open(outfile, "w", encoding="utf-8") as out:
        out.write(text)
    print(f"wrote {len(text)} chars from byte {start} to {outfile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
