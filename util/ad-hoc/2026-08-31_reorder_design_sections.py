#!/usr/bin/env python3
"""One-off: move the newly-added design §9.2/§9.3 block to AFTER §9.1.

Project:     Juniper
Sub-Project: juniper-ml
Author:      Paul Calnon
License:     MIT License

The 2026-08-31 D-1/D-2 ruling was appended immediately after the §9 decision
table, which put it BEFORE the pre-existing "### 9.1 Still open" subsection and
made the document read 9 -> 9.2 -> 9.3 -> 9.1. This lifts the new block out and
re-inserts it after §9.1's bullets, so the numbering reads in order.

Idempotent by construction: it keys on a placeholder anchor that exists only
while the block is misplaced, and exits 0 with a message if the anchor is gone.
"""

import pathlib
import sys

DOC = pathlib.Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md"

ANCHOR = "### 9.2 PLACEHOLDER-MOVE-ANCHOR Owner decisions"
END_OF_BLOCK = "### 9.1 Still open — carried forward"
NEXT_SECTION = "## 10. Naming"


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    if ANCHOR not in text:
        print("anchor absent -- nothing to move (already ordered)")
        return 0

    start = text.index(ANCHOR)
    end = text.index(END_OF_BLOCK, start)
    block = text[start:end].rstrip("\n")
    block = block.replace("### 9.2 PLACEHOLDER-MOVE-ANCHOR Owner decisions", "### 9.2 Owner decisions")

    # Excise the block from its wrong position.
    remainder = text[:start] + text[end:]

    # Re-insert immediately before "## 10. Naming".
    idx = remainder.index(NEXT_SECTION)
    rebuilt = remainder[:idx] + block + "\n\n" + remainder[idx:]

    DOC.write_text(rebuilt, encoding="utf-8")

    # Verify the ordering actually came out right rather than trusting the splice.
    out = DOC.read_text(encoding="utf-8")
    order = [h for h in ("### 9.1 Still open", "### 9.2 Owner decisions", "### 9.3 Derived requirement", "## 10. Naming") if h in out]
    positions = [out.index(h) for h in order]
    if positions != sorted(positions) or len(order) != 4:
        print(f"ORDER STILL WRONG: {order}", file=sys.stderr)
        return 1
    print(f"ordered OK: {' -> '.join(h.split(' ')[1] for h in order)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
