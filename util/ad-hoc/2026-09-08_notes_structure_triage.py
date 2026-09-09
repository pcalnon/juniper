#!/usr/bin/env python3
"""2026-09-08_notes_structure_triage.py -- classify a structure finding before "fixing" it.

Project: juniper-ml
Sub-Project: docs structure debt (owner decision: repair live notes/, ratify the rest)
Application: ad-hoc analysis (documentation integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`util/ad-hoc/2026-09-05_markdown_structure_check.py` reports 63 problems across the 12
live `notes/` files. They are NOT one thing, and three of the four classes must be
repaired differently -- or not at all:

  SAMPLE      An H2 inside a BARE ``` fence whose content is a sample markdown document
              (a handoff skeleton, a prompt template). The H2s are the point. The screen
              already exempts ```markdown / ```md, so the honest repair is to TAG the
              fence -- which also turns on syntax highlighting. Not damage.

  TRANSCRIPT  An H2 inside an explicitly tagged non-markdown fence (```text, ```console)
              holding captured output whose lines happen to start with "## ". The fence
              opens and closes correctly; the screen's heuristic misfires. Editing the
              captured text to satisfy a heuristic would FALSIFY a transcript, so these
              are reported, never rewritten.

  LOST-FENCE  An H2 inside a fence that genuinely lost its closing ```. This is the
              juniper-ml#1746 defect the screen was built for -- real damage, real repair.

  TABLE       A header row with no `| --- |` separator, which renders the table as plain
              text. Almost always real damage.

The distinction that matters: SAMPLE and LOST-FENCE both show "H2 inside a fence" and are
opposite defects. Telling them apart needs the fence's CONTENT, not its count -- a sample
block is self-contained markdown, while a lost-fence block runs to the end of the document
or swallows unrelated prose.

Usage:
    python3 util/ad-hoc/2026-09-08_notes_structure_triage.py [PATH ...]
    (default: the live notes/ set -- notes/**.md excluding notes/legacy/)
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

FENCE_OPEN = re.compile(r"^```(.*)$")
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
MARKDOWN_INFO = {"markdown", "md"}

#: An info string that names a NON-markdown language. An H2 inside one of these is far
#: more likely to be captured output than a dropped fence, because the author took the
#: trouble to label it.
TEXTUAL_INFO = {"text", "txt", "console", "shell-session", "output", "log"}


def classify_file(path: Path) -> list[tuple[str, int, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    findings: list[tuple[str, int, str]] = []

    # Walk fences, recording each block's opener info string and its body.
    blocks: list[tuple[int, str, list[str], bool]] = []  # (open_line, info, body, closed)
    i = 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        # lstrip("`") to match the screen's own `_is_markdown_example`: a FOUR-backtick
        # ````markdown fence (used to wrap samples that themselves contain ```) otherwise
        # yields info "`markdown" and is misread as an unlabelled block.
        info = m.group(1).strip().lstrip("`").strip().lower()
        body: list[str] = []
        j = i + 1
        closed = False
        while j < len(lines):
            if lines[j].startswith("```"):
                closed = True
                break
            body.append(lines[j])
            j += 1
        blocks.append((i + 1, info, body, closed))
        i = j + 1

    for open_line, info, body, closed in blocks:
        h2s = [b for b in body if b.startswith("## ")]
        if not h2s:
            continue
        if info in MARKDOWN_INFO:
            continue  # already exempt
        if not closed:
            findings.append(("LOST-FENCE", open_line, f"fence never closed; {len(h2s)} H2 inside"))
            continue
        if info in TEXTUAL_INFO:
            findings.append(("TRANSCRIPT", open_line, f"```{info} with {len(h2s)} '## ' output line(s)"))
            continue
        if info == "":
            # A bare fence. Sample markdown if the body reads as a document skeleton --
            # i.e. it is mostly headings and short lines, with no shell/code punctuation.
            heading_ratio = len(h2s) / max(1, len([b for b in body if b.strip()]))
            findings.append((
                "SAMPLE" if heading_ratio >= 0.4 else "LOST-FENCE?",
                open_line,
                f"bare fence, {len(h2s)} H2 of {len([b for b in body if b.strip()])} non-blank lines",
            ))
            continue
        findings.append(("LOST-FENCE?", open_line, f"```{info} with {len(h2s)} H2 inside"))

    # Tables with no separator row (fence-aware).
    in_fence = False
    for idx, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line[:4] == "    ":
            continue
        stripped = line.strip()
        if stripped.startswith("|") and line.count("|") >= 2:
            prev = lines[idx - 1] if idx else ""
            nxt = lines[idx + 1] if idx + 1 < len(lines) else ""
            if not prev.strip().startswith("|") and nxt.strip().startswith("|") and not SEPARATOR.match(nxt):
                findings.append(("TABLE", idx + 1, stripped[:60]))
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        paths = [Path(a) for a in argv]
    else:
        paths = sorted(
            p for p in Path("notes").rglob("*.md")
            if "legacy" not in p.parts and p.exists()
        )

    totals: Counter = Counter()
    for path in paths:
        findings = classify_file(path)
        if not findings:
            continue
        print(f"=== {path}")
        for kind, line, detail in findings:
            totals[kind] += 1
            print(f"   {kind:12s} line {line:5d}  {detail}")
        print()

    print("totals by class:")
    for kind, n in totals.most_common():
        print(f"  {n:3d}  {kind}")
    print(f"  {sum(totals.values()):3d}  TOTAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
