#!/usr/bin/env python3
"""Measure the word-length distribution of archived thread-handoff prompts.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-30
Status:      ad-hoc -- census run for the handoff-length question raised as
             item C.6 of the 2026-08-28 shared-session-memory arc handoff
             (prompts/thread-handoff_automated-prompts/), and recorded on
             tracker juniper-ml#1326. NOTE: "C.6" numbers an item in that
             HANDOFF document, not a row of the plan's Sec 5 owner-decision
             table -- an earlier version of this line cited it in a way that
             read as a plan reference and was correctly reported UNTRACEABLE by
             an independent reviewer who searched the plan for it.
Retire when: the figure in
             notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md
             is settled and nobody needs to re-derive it.

Why a script and not a one-liner
--------------------------------
The output is being used to CHANGE a procedure, so it has to be re-runnable by
someone who doubts the number. An inline pipeline that produced "1,190" once
and vanished is exactly the shape that makes a documented figure unfalsifiable.

Counting choices, stated because they move the answer
-----------------------------------------------------
- A "word" is a whitespace-separated token, matching how the procedure's own
  "~500 words" would naturally be checked.
- Fenced code blocks are counted SEPARATELY and excluded from the prose figure.
  Handoffs carry verification-command blocks that are not prose, and including
  them inflates every file by a variable amount.
- Front matter is NOT special-cased. An earlier draft of this docstring claimed
  it was; the code never did. Checked before relying on the figure: zero of the
  148 archived handoffs open with a `---` front-matter fence, so the two
  behaviours cannot differ on this corpus. Stated rather than silently dropped,
  because a docstring describing a filter the code does not apply is exactly
  how an instrument gets trusted for a property it does not have.
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parents[2] / "prompts" / "thread-handoff_automated-prompts"


def _fence(line: str) -> tuple[str, int] | None:
    """Return (char, run_length) if this line opens/closes a fence, else None."""
    s = line.lstrip()
    for ch in ("`", "~"):
        if s.startswith(ch * 3):
            run = len(s) - len(s.lstrip(ch))
            return ch, run
    return None


def split_prose_and_code(text: str) -> tuple[int, int, bool]:
    """Return (prose_words, code_words, unbalanced).

    Fence handling follows CommonMark rather than a naive toggle, because the
    naive version was wrong by more than 100% on a real file in this corpus.

    Two rules matter, and the original toggle had neither:

    1. A fence is closed only by a delimiter of the SAME character that is at
       least as long as the opener. A ``` line inside a ````-fenced block is
       content, not a close. The toggle treated it as a close, silently moving
       real code into the prose bucket.
    2. ``~~~`` is a fence too. The toggle ignored tildes entirely, swallowing
       such blocks -- delimiters included -- into prose.

    `unbalanced` reports a file whose final fence never closed. That is not
    hypothetical: HANDOFF_2026-08-24_t6-rebaseline-campaign.md contains its own
    text twice, and the seam leaves an unclosed ```bash at line 450. The naive
    reader silently returned 4,422 prose words for a file that reads 8,930 when
    the fence is repaired -- and it is the longest file in the archive, so it
    was missing from the "five longest" list while the census looked healthy.
    An instrument that cannot say "this input broke me" reports a number for
    every file and is trusted for all of them.
    """
    prose: list[str] = []
    code: list[str] = []
    open_fence: tuple[str, int] | None = None

    for line in text.split("\n"):
        f = _fence(line)
        if open_fence is None:
            if f is not None:
                open_fence = f
                continue
            prose.append(line)
        else:
            ch, run = open_fence
            if f is not None and f[0] == ch and f[1] >= run:
                open_fence = None
                continue
            code.append(line)

    return (
        len(" ".join(prose).split()),
        len(" ".join(code).split()),
        open_fence is not None,
    )


def main() -> int:
    files = sorted(ARCHIVE.glob("*.md"))
    if not files:
        print(f"no handoffs found under {ARCHIVE}", file=sys.stderr)
        return 2

    rows = []
    broken: list[str] = []
    for f in files:
        prose, code, unbalanced = split_prose_and_code(
            f.read_text(encoding="utf-8", errors="replace")
        )
        if unbalanced:
            broken.append(f.name)
        rows.append((prose, code, f.name))

    prose_counts = sorted(r[0] for r in rows)
    total_counts = sorted(r[0] + r[1] for r in rows)

    def describe(label: str, xs: list[int]) -> None:
        print(f"  {label:18s} n={len(xs)}  median={statistics.median(xs):,.0f}  "
              f"mean={statistics.mean(xs):,.0f}  min={min(xs):,}  max={max(xs):,}")

    print(f"archive: {ARCHIVE}")
    describe("prose words", prose_counts)
    describe("prose + code", total_counts)

    for threshold in (500, 1000, 1200, 2000):
        under = sum(1 for x in prose_counts if x <= threshold)
        print(f"  <= {threshold:5,} prose words: {under:3d}/{len(prose_counts)}  "
              f"({100 * under / len(prose_counts):.1f}%)")

    print("\n  five longest (prose words):")
    for prose, _code, name in sorted(rows, reverse=True)[:5]:
        print(f"    {prose:6,}  {name}")

    if broken:
        print(
            f"\n  WARNING: {len(broken)} file(s) end inside an unclosed fence. Their prose/code\n"
            "  split is NOT trustworthy and their word counts are understated. Fix the file,\n"
            "  or exclude it, before citing any figure that depends on it:"
        )
        for name in broken:
            print(f"    {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
