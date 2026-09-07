#!/usr/bin/env python3
"""
Remove a re-landed duplicate `##` section, keeping whichever copy is FULLER.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-07
Status: ad-hoc -- one-off (cursor-fleet PR disposition, #1799 re-land repair)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-07_duplicate_section_census.py`, which measured the damage

#1799 re-landed six PRs #1797 had already carried -- 367 of its 391 added lines were already on
`main`. Measured across it: **+23 duplicate headings, +13 duplicate row keys**, including five
whole `##` sections now present twice in `docs/REFERENCE.md`.

WHY NO GATE CAUGHT IT, INCLUDING THE ONE THAT SHIPPED THAT DAY

`markdown_structure_delta.py` gates fences, swallowed headings and separator-less tables -- damage
to a document's SHAPE. A duplicated section damages none of those: every fence is balanced, every
table keeps its separator, and the file scores **0 structural problems**. The gate answers an
adjacent question, and the duplicate census is the instrument for this one.

WHICH COPY SURVIVES

Stated per heading with `--keep first|second`, because length decides exactly one of the five
pairs -- and there it means the OPPOSITE of a "prefer the longer" instinct applied elsewhere:

    ## Canopy E2E Matrix Writes                90 vs 90  differ by one `---`
    ## F-CANOPY-027 Poller Starvation Probes   24 vs 60  the FIRST lost a 36-line bash block
    ## Canopy E2E Finding Triage               47 vs 48  the SECOND adds a cross-reference
    ## Ruleset Scope Guard                     58 vs 55  the FIRST has `### Exit codes` + `Related:`
    ## Suite Report Gate Inputs                71 vs 71  identical

Default `--keep longer` REFUSES when the gap is under MIN_DELTA, rather than guessing.

Usage:
    2026-09-07_dedupe_relanded_sections.py <file> --heading '## Name' --keep second [...] [--apply]

Exit: 0 when every named heading was resolved; 1 when one was ambiguous or not duplicated.
"""

from __future__ import annotations

import argparse
from pathlib import Path

MIN_DELTA = 4  # below this the line-count proxy is not evidence


def _heading_lines(lines: list[str]) -> list[bool]:
    """Which lines are REAL headings -- fence-aware.

    A `# comment` inside a ```bash block is not a heading, and treating it as one cuts a section
    at its own example. Measured 2026-09-07: `## Canopy E2E Matrix Writes` reported 22 lines
    against a 40-line section because `# Ledger: what is still a placeholder?` sits inside its
    fenced block. Deleting that "section" would have orphaned the tail under the surviving copy.
    """
    out: list[bool] = []
    in_fence = False
    for line in lines:
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            out.append(False)
            continue
        out.append(not in_fence and line.startswith("#"))
    return out


def spans(lines: list[str], heading: str) -> list[tuple[int, int]]:
    """`(start, end)` for each occurrence of `heading`, ending at the next same-or-higher heading."""
    level = len(heading) - len(heading.lstrip("#"))
    is_heading = _heading_lines(lines)
    starts = [i for i, ln in enumerate(lines) if ln.rstrip() == heading and is_heading[i]]
    out = []
    for start in starts:
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if not is_heading[j]:
                continue
            stripped = lines[j].rstrip()
            depth = len(stripped) - len(stripped.lstrip("#"))
            if depth <= level and stripped[depth : depth + 1] == " ":
                end = j
                break
        out.append((start, end))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--heading", action="append", required=True)
    parser.add_argument(
        "--keep",
        action="append",
        choices=("first", "second", "longer"),
        help="which copy survives, paired positionally with --heading; default `longer`, which is "
        "only evidence when the gap exceeds MIN_DELTA",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.path)
    lines = path.read_text(encoding="utf-8").splitlines()
    drop: list[tuple[int, int]] = []
    worst = 0

    keeps = list(args.keep or [])
    keeps += ["longer"] * (len(args.heading) - len(keeps))
    for heading, want in zip(args.heading, keeps):
        found = spans(lines, heading)
        if len(found) != 2:
            print(f"[SKIP] {heading!r}: {len(found)} occurrence(s), expected exactly 2")
            worst = 1
            continue
        (a_start, a_end), (b_start, b_end) = found
        a_len, b_len = a_end - a_start, b_end - b_start
        if want == "longer":
            if abs(a_len - b_len) < MIN_DELTA:
                print(f"[HOLD] {heading!r}: {a_len} vs {b_len} lines -- within {MIN_DELTA}, the length proxy is not evidence; pass --keep")
                worst = 1
                continue
            keep_first = a_len > b_len
        else:
            keep_first = want == "first"
        loser = (b_start, b_end) if keep_first else (a_start, a_end)
        keeper = (a_start, a_end) if keep_first else (b_start, b_end)
        print(f"[DROP] {heading!r} (--keep {want}): keeping {keeper[0]+1}-{keeper[1]} ({keeper[1]-keeper[0]} lines), dropping {loser[0]+1}-{loser[1]} ({loser[1]-loser[0]} lines)")
        drop.append(loser)

    if not args.apply:
        print("\n(dry run -- pass --apply to write)")
        return worst

    keep = [True] * len(lines)
    for start, end in drop:
        for i in range(start, end):
            keep[i] = False
    path.write_text("\n".join(ln for i, ln in enumerate(lines) if keep[i]).rstrip("\n") + "\n", encoding="utf-8")
    print(f"\nwrote {path}: {sum(1 for k in keep if not k)} line(s) removed")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
