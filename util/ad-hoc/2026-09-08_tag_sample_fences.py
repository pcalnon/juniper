#!/usr/bin/env python3
"""2026-09-08_tag_sample_fences.py -- label a bare fence that holds a markdown SAMPLE.

Project: juniper-ml
Sub-Project: docs structure debt (owner decision: repair live notes/, ratify the rest)
Application: ad-hoc repair (documentation integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`util/ad-hoc/2026-09-05_markdown_structure_check.py` flags an H2 inside a code fence,
because that is the shape a DROPPED CLOSING FENCE produces -- the juniper-ml#1746 defect
that swallowed 36 headings in `docs/REFERENCE.md`.

A bare ``` fence holding a sample document -- a handoff skeleton, a prompt template --
produces the identical shape and is not damage at all. The screen already exempts
```markdown / ```md, precisely so a sample can say what it is. These fences simply never
declared themselves.

So the honest repair is to LABEL the fence, not to restructure the document: the finding
clears because the file now states its intent, and the reader gets syntax highlighting.
It is not a suppression -- an unlabelled fence that genuinely lost its close still fails.

Edits run in DESCENDING line order so an earlier rewrite cannot shift a later target, and
every target is asserted to be a bare ``` before it is touched: a stale line number must
abort, never relabel an unrelated fence.

Usage:
    python3 util/ad-hoc/2026-09-08_tag_sample_fences.py [--apply]
"""

from __future__ import annotations

import sys
from pathlib import Path

#: path -> the 1-based lines carrying a bare ``` that opens a markdown sample.
#: Derived from util/ad-hoc/2026-09-08_notes_structure_triage.py's SAMPLE class.
TARGETS = {
    "notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md": [
        349,
        373,
        394,
        417,
        439,
        461,
    ],
    "notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md": [246],
}


def main(argv: "list[str] | None" = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    apply = "--apply" in argv

    total = 0
    for path, linenos in TARGETS.items():
        p = Path(path)
        if not p.is_file():
            print(f"MISSING {path}", file=sys.stderr)
            return 2
        lines = p.read_text(encoding="utf-8").splitlines()
        for lineno in sorted(linenos, reverse=True):
            idx = lineno - 1
            if idx >= len(lines) or lines[idx] != "```":
                actual = lines[idx] if idx < len(lines) else "<past end of file>"
                print(f"REFUSING {path}:{lineno} is {actual!r}, expected a bare '```'", file=sys.stderr)
                return 2
            lines[idx] = "```markdown"
            total += 1
        if apply:
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{'tagged' if apply else 'would tag'} {len(linenos)} fence(s) in {path}")

    print(f"\n{'tagged' if apply else 'would tag'} {total} fence(s)"
          + ("" if apply else "  (dry run -- pass --apply)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
