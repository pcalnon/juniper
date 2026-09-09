#!/usr/bin/env python3
"""2026-09-08_repair_notes_tables.py -- repair the eight REAL table defects in live notes/.

Project: juniper-ml
Sub-Project: docs structure debt (owner decision: repair live notes/, ratify the rest)
Application: ad-hoc repair (documentation integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`util/ad-hoc/2026-09-05_markdown_structure_check.py` reports 13 "table has no separator
row" findings across the live `notes/` set. Five are the SCREEN's own false positives -- a
separator cell of a SINGLE hyphen (`| - | ---- |`) is valid GFM, but the screen's regex
demands `-{2,}`. Those documents are correct and are not touched here.

The remaining eight are real, and they are four different defects. A table renders as
plain text the moment any of them lands, so the damage is invisible in the source and
obvious in the rendered page:

  BLANK-SPLIT   A blank line injected mid-table. Everything after it becomes a NEW table
                whose first row is read as a header with no separator. Three sites. This
                is the "whole-line union fragments tables" damage from the docs-fleet
                consolidations.

  WRAPPED-ROW   One logical row hard-wrapped across three physical lines. A table row must
                be one line; the two continuation lines carry no pipes, so the row breaks
                and the next real row is read as a header. One site.

  QUOTE-SPLIT   A 65-line blockquote inserted BETWEEN a row and its own continuation
                cells, orphaning three trailing rows from their table. One site.

  BAD-SEPARATOR A separator typo -- `| --- | -- -| --- |`, a stray space inside the second
                cell's dashes. One site.

  LOST-HEADER   The header row itself is gone. One site: commit 4da40fe9, whose subject is
                "minor formatting changes to design docs", deleted the header AND the
                first four rows of §3.2's suite table while re-padding the survivors.
                Only the HEADER is restored here, verbatim from 22c32bd1. The four rows
                are deliberately NOT restored -- the survivors are exactly the
                model-specific suites and the deleted four are the generic conformance
                items the surrounding text says now live in the companion's §3.3, so the
                row trim reads as editorial while the header loss does not. Reinstating
                three-month-old rows over a plausible deliberate trim is a content
                decision, not a structural repair.

Every edit asserts the current content of its target line first: a stale line number must
abort, never rewrite an unrelated line. Edits apply in DESCENDING line order per file so
an earlier rewrite cannot shift a later target.

Usage:
    python3 util/ad-hoc/2026-09-08_repair_notes_tables.py [--apply]
"""

from __future__ import annotations

import sys
from pathlib import Path

NOTES = Path("notes")

CLI_TEST = NOTES / "JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md"
DEFECTS = NOTES / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
H2H = NOTES / "JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md"
SNAPSHOT = NOTES / "JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md"
RECURSE = NOTES / "JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md"
CANOPY = NOTES / "code-review" / "JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ANALYSIS.md"

#: The header lost by 4da40fe9, recovered verbatim from 22c32bd1.
SUITE_HEADER = "| Suite | What it asserts | Technique |"
SUITE_SEP = "|-------|-----------------|-----------|"


class Repair:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.actions: list[tuple[int, str, object]] = []
        self.log: list[str] = []

    def _at(self, lineno: int) -> str:
        return self.lines[lineno - 1]

    def expect(self, lineno: int, predicate, description: str) -> None:
        actual = self._at(lineno)
        if not predicate(actual):
            raise SystemExit(
                f"REFUSING {self.path}:{lineno} -- expected {description}, found {actual[:70]!r}"
            )

    def delete_blank(self, lineno: int, why: str) -> None:
        self.expect(lineno, lambda s: s.strip() == "", "a blank line")
        self.expect(lineno - 1, lambda s: s.lstrip().startswith("|"), "a table row above")
        self.expect(lineno + 1, lambda s: s.lstrip().startswith("|"), "a table row below")
        self.actions.append((lineno, "delete", 1))
        self.log.append(f"  BLANK-SPLIT  :{lineno}  {why}")

    def replace(self, lineno: int, new: str, why: str, predicate=None) -> None:
        if predicate:
            self.expect(lineno, predicate, "the expected content")
        self.actions.append((lineno, "replace", new))
        self.log.append(f"  {why} :{lineno}")

    def join(self, first: int, count: int, why: str) -> None:
        joined = " ".join(self._at(first + k).strip() for k in range(count))
        self.actions.append((first, "join", (count, joined)))
        self.log.append(f"  WRAPPED-ROW  :{first}-{first + count - 1}  {why}")

    def insert_before(self, lineno: int, new_lines: list[str], why: str) -> None:
        self.actions.append((lineno, "insert", new_lines))
        self.log.append(f"  LOST-HEADER  :{lineno}  {why}")

    def move(self, first: int, count: int, after: int, why: str) -> None:
        block = [self._at(first + k) for k in range(count)]
        self.actions.append((first, "delete", count))
        self.actions.append((after + 1, "insert", block))
        self.log.append(f"  QUOTE-SPLIT  :{first}-{first + count - 1} -> after :{after}  {why}")

    def render(self) -> str:
        out = list(self.lines)
        # Descending by line number so an earlier edit cannot shift a later target.
        for lineno, kind, payload in sorted(self.actions, key=lambda a: -a[0]):
            idx = lineno - 1
            if kind == "delete":
                del out[idx: idx + payload]
            elif kind == "replace":
                out[idx] = payload
            elif kind == "insert":
                out[idx:idx] = payload
            elif kind == "join":
                count, joined = payload
                out[idx: idx + count] = [joined]
        return "\n".join(out) + "\n"


def build() -> list[Repair]:
    repairs = []

    r = Repair(CLI_TEST)
    r.delete_blank(782, "splits the H-1..H-8 hazard table before H-9")
    r.delete_blank(774, "splits the hazard table before H-2")
    repairs.append(r)

    r = Repair(DEFECTS)
    r.delete_blank(1185, "splits the APD defect table before APD-CCLIENT-001")
    repairs.append(r)

    r = Repair(H2H)
    r.join(642, 3, "one row hard-wrapped across three lines")
    repairs.append(r)

    r = Repair(SNAPSHOT)
    r.move(752, 3, 685, "S-5's continuation cells, orphaned by the answer blockquote")
    # :442 is the HEADER; the screen flags a header whose FOLLOWING line is not a valid
    # separator, so the typo itself is on :443.
    r.replace(
        443,
        "| --- | --- | --- |",
        "BAD-SEPARATOR",
        predicate=lambda s: s.strip() == "| --- | -- -| --- |",
    )
    repairs.append(r)

    r = Repair(RECURSE)
    r.expect(373, lambda s: s.startswith("| **Growth-loop correctness**"), "the first suite row")
    r.insert_before(373, [SUITE_HEADER, SUITE_SEP], "header lost by 4da40fe9, restored from 22c32bd1")
    repairs.append(r)

    r = Repair(CANOPY)
    r.delete_blank(1434, "separates the Milestone header from its separator row")
    repairs.append(r)

    return repairs


def main(argv: "list[str] | None" = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    apply = "--apply" in argv

    repairs = build()
    total = 0
    for r in repairs:
        print(f"=== {r.path}")
        for line in r.log:
            print(line)
        total += len(r.log)
        if apply:
            r.path.write_text(r.render(), encoding="utf-8")
    print(f"\n{'repaired' if apply else 'would repair'} {total} defect(s)"
          + ("" if apply else "  (dry run -- pass --apply)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
