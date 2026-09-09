#!/usr/bin/env python3
"""2026-09-08_reconcile_reference_sections.py -- collapse the repeated `##` sections.

Project: juniper-ml
Sub-Project: docs/REFERENCE.md integrity
Application: ad-hoc repair (documentation integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`docs/REFERENCE.md` carries three `##` headings more than once -- eight sections in total,
~570 lines, about 7.5% of the file. The round-2 handoff called this "duplication", but no
two bodies are byte-identical: they are DRIFTED copies that contradict each other, and on
two load-bearing points the LONGEST copy is the WRONG one.

  ## Pointer-Follow Soak                x4
  ## Perf-Lane Split Comparator         x2
  ## F-CANOPY-037 Render Census         x2

The structure gate shipped in #1801 cannot see any of this: it checks a document's SHAPE
(fence balance, swallowed headings, separator-less tables), and eight duplicated sections
are shape-perfect. Detecting them needs
`util/ad-hoc/2026-09-07_duplicate_section_census.py`, a different instrument entirely.

WHY "KEEP THE LONGEST COPY" WOULD HAVE SHIPPED FALSEHOODS

Two contradictions were adjudicated against SOURCE, not by length or recency of prose:

  * dry-run vs a terminal verdict. The richest soak copy says a terminal ledger makes even
    `--dry-run` exit 2 unless `--force`, and its pitfall table tells the operator to pass
    `--force` to see a preview. `util/soak_run_probe.py:146` says otherwise --
    `refuses_terminal_verdict` returns False when `force` OR `dry_run` is set (#1690), and
    `:405` prints a NOTE and proceeds. The shorter copy is correct; the richer one gives
    advice that spends a session for nothing.

  * driving ambiguous probes to n=8-10. One copy recommends it as "the next cheapest
    design"; another REFUTES it with the repo's own `wilson()` (first exclude is 10/31).
    The refutation is newer and is kept.

  * `--status`. One copy calls it "coverage"; another says "post-intervention run counts,
    not a follow/n table". `util/soak_next_probe.py:97` prints per-probe post-intervention
    counts, so the second is precise and the first is loose.

WHAT IS NOT A DUPLICATE

The fourth soak copy carries an `isolated_stack.bash` utility table spliced into its
preamble -- foreign content, and the ONLY place in the file naming
`JUNIPER_E2E_DATA_PORT` and `JUNIPER_E2E_CASCOR_PORT`. Deleting that copy wholesale would
destroy three facts. The table is RELOCATED to `## Isolated Stack E2E Utilities`, where
its companion pointer sentence already lives.

The two Perf-Lane copies are the one clean case: the survivor carries a supersession
banner and marks two defects **Fixed** that the other still reports as open, warning
operators off a workflow that now works. (juniper-ml#1811 had to patch BOTH copies of that
section, applying the same two edits twice -- that is the cost of the duplication, not a
defect in #1811.)

The two census copies genuinely partially overlap: neither subsumes the other, so the
survivor is a union.

Usage:
    python3 util/ad-hoc/2026-09-08_reconcile_reference_sections.py [--apply]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOC = Path("docs") / "REFERENCE.md"
SCRATCH_ENV = "JUNIPER_RECONCILE_SOURCE_DIR"

#: The isolated_stack utility table wrongly spliced into the 4th soak copy's preamble.
#: Verbatim, minus the duplicated pointer sentence that already sits in its destination.
ISOLATED_TABLE = """| Utility | Purpose | Key Overrides |
|---------|---------|---------------|
| `util/isolated_stack.bash --up` | Create the data venv, then launch data → cascor → canopy (health-gated); a mid-leg failure tears the partial trio back down | `JUNIPER_E2E_DATA_PORT`, `JUNIPER_E2E_CASCOR_PORT`, `JUNIPER_E2E_CANOPY_PORT`, `JUNIPER_E2E_HEALTH_TIMEOUT`, `JUNIPER_E2E_DATA_EXTRAS`, `JUNIPER_E2E_RUN_DIR`, `JUNIPER_E2E_*_CONDA` / `*_DIR` |
| `util/isolated_stack.bash --down` | Kill-by-port teardown + clean run / snapshot artifacts | same port / `RUN_DIR` / project overrides |
| `util/isolated_stack.bash --status` | Probe each `/v1/health` and report listening PID | same |
| `util/isolated_stack.bash --dry-run …` | Print every command; execute nothing (safe when ports are busy) | same |
"""


def fence_aware_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(0-based index, level, title) for every real heading -- fences skipped."""
    out: list[tuple[int, int, str]] = []
    in_fence = False
    for i, ln in enumerate(lines):
        if re.match(r"^\s*(```|~~~)", ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def section_spans(lines: list[str], title: str) -> list[tuple[int, int]]:
    """Every [start, end) span of a level-2 section with this exact title."""
    heads = fence_aware_headings(lines)
    spans = []
    for idx, (i, lvl, t) in enumerate(heads):
        if lvl != 2 or t != title:
            continue
        end = len(lines)
        for j, l2, _t in heads[idx + 1:]:
            if l2 <= lvl:
                end = j
                break
        spans.append((i, end))
    return spans


def main(argv: "list[str] | None" = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    apply = "--apply" in argv

    src_dir = None
    for a in argv:
        if a.startswith("--source-dir="):
            src_dir = Path(a.split("=", 1)[1])
    if src_dir is None:
        print("need --source-dir=DIR holding merged_soak.md and merged_census.md", file=sys.stderr)
        return 2

    merged_soak = (src_dir / "merged_soak.md").read_text(encoding="utf-8").rstrip("\n").split("\n")
    merged_census = (src_dir / "merged_census.md").read_text(encoding="utf-8").rstrip("\n").split("\n")

    lines = DOC.read_text(encoding="utf-8").splitlines()

    soak = section_spans(lines, "Pointer-Follow Soak")
    perf = section_spans(lines, "Perf-Lane Split Comparator")
    census = section_spans(lines, "F-CANOPY-037 Render Census")
    iso = section_spans(lines, "Isolated Stack E2E Utilities")

    if (len(soak), len(perf), len(census), len(iso)) != (4, 2, 2, 1):
        print(f"REFUSING: expected 4/2/2/1 sections, found "
              f"{len(soak)}/{len(perf)}/{len(census)}/{len(iso)}", file=sys.stderr)
        return 2

    # The four soak copies must be contiguous, or a wholesale replace would eat something else.
    for (a_start, a_end), (b_start, _b_end) in zip(soak, soak[1:]):
        if a_end != b_start:
            print(f"REFUSING: soak copies are not contiguous ({a_end} != {b_start})", file=sys.stderr)
            return 2

    # The relocated table must still be inside the 4th soak copy, and absent from its destination.
    soak4 = "\n".join(lines[soak[3][0]:soak[3][1]])
    if "isolated_stack.bash --up`" not in soak4:
        print("REFUSING: the isolated_stack table is not in the 4th soak copy", file=sys.stderr)
        return 2
    iso_body = "\n".join(lines[iso[0][0]:iso[0][1]])
    if "| `util/isolated_stack.bash --up`" in iso_body:
        print("REFUSING: the destination already holds the table -- would duplicate it", file=sys.stderr)
        return 2

    # Insertion point: after the four-command bash block at the top of the Isolated Stack
    # section, before the first `####`. Anchor on content, never a raw line number.
    ins = None
    for i in range(iso[0][0], iso[0][1]):
        if lines[i].startswith("#### "):
            ins = i
            break
    if ins is None:
        print("REFUSING: no '#### ' subsection found in Isolated Stack E2E Utilities", file=sys.stderr)
        return 2

    edits: list[tuple[int, int, list[str]]] = []  # (start, end, replacement)
    edits.append((census[1][0], census[1][1], []))                  # drop 2nd census
    edits.append((census[0][0], census[0][1], merged_census + [""]))  # union in place of 1st
    edits.append((perf[1][0], perf[1][1], []))                      # drop stale perf copy
    edits.append((ins, ins, ISOLATED_TABLE.rstrip("\n").split("\n") + [""]))
    edits.append((soak[0][0], soak[3][1], merged_soak + [""]))      # 4 copies -> 1

    out = list(lines)
    for start, end, repl in sorted(edits, key=lambda e: -e[0]):
        out[start:end] = repl

    print(f"  soak    : 4 sections ({soak[0][0]+1}-{soak[3][1]}) -> 1 merged ({len(merged_soak)} lines)")
    print(f"  perf    : dropped the stale copy at {perf[1][0]+1}-{perf[1][1]}")
    print(f"  census  : 2 sections -> 1 union ({len(merged_census)} lines)")
    print(f"  relocate: isolated_stack table -> line {ins+1}, before {lines[ins].strip()!r}")
    print(f"  net     : {len(lines)} -> {len(out)} lines ({len(out) - len(lines):+d})")

    if apply:
        DOC.write_text("\n".join(out) + "\n", encoding="utf-8")
    else:
        print("\n(dry run -- pass --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
