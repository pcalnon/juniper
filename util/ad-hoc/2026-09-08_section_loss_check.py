#!/usr/bin/env python3
"""2026-09-08_section_loss_check.py -- what does the BEFORE have that the AFTER lacks?

Project: juniper-ml
Sub-Project: docs/REFERENCE.md integrity
Application: ad-hoc verification (documentation integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

A consolidation is verified as a LOSS CHECK, not a step check. Each individual removal in
the section reconciliation is defensible on its own -- "this copy is subsumed", "this copy
is stale" -- and a review that walks the steps agrees with every one of them and still
misses what the combination dropped. That is exactly how the #1814 repair lost a
version-history row: two correct removals, one casualty, found only by asking what the
branch had that the result did not.

So this asks the only question that catches it: enumerate the atoms of the ORIGINAL, and
report every one absent from the RESULT.

An "atom" is a high-signal token a reader would notice missing:

  * inline code spans -- identifiers, paths, flags, env vars, exit codes;
  * markdown link targets;
  * bare `word/word.ext` paths outside code spans.

Prose is deliberately NOT compared: a merge legitimately rewrites sentences, and diffing
prose would bury the real findings under hundreds of rewordings. Anything this reports is
either a genuine loss or a deliberate, explainable drop -- there is no third category, and
every hit must be adjudicated by hand.

Exit 0 = nothing lost. Exit 1 = atoms are missing (read them; some may be intended).

Usage:
    python3 util/ad-hoc/2026-09-08_section_loss_check.py BEFORE.md AFTER.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CODE_SPAN = re.compile(r"`([^`\n]{2,})`")
LINK_TARGET = re.compile(r"\]\(([^)\s]+)")
BARE_PATH = re.compile(r"\b((?:[\w.-]+/)+[\w.-]+\.(?:py|md|bash|sh|json|jsonl|yaml|yml|toml|h5|csv))\b")

#: Tokens whose disappearance is noise rather than signal.
IGNORE = {"---", "--", "|", "..."}


def atoms(text: str) -> set[str]:
    found: set[str] = set()
    for m in CODE_SPAN.finditer(text):
        tok = m.group(1).strip()
        if tok and tok not in IGNORE:
            found.add(tok)
    for m in LINK_TARGET.finditer(text):
        found.add(m.group(1).strip())
    for m in BARE_PATH.finditer(text):
        found.add(m.group(1).strip())
    return found


def main(argv: "list[str] | None" = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2

    before_p, after_p = Path(argv[0]), Path(argv[1])
    for p in (before_p, after_p):
        if not p.is_file():
            print(f"missing {p}", file=sys.stderr)
            return 2

    before = atoms(before_p.read_text(encoding="utf-8"))
    after = atoms(after_p.read_text(encoding="utf-8"))
    lost = sorted(before - after)

    print(f"atoms in BEFORE: {len(before)}")
    print(f"atoms in AFTER : {len(after)}")
    print(f"gained         : {len(after - before)}")
    print(f"LOST           : {len(lost)}")
    if lost:
        print()
        for tok in lost:
            print(f"   {tok}")
        print("\nEvery line above must be adjudicated: a genuine loss, or a deliberate drop.")
        return 1
    print("\nnothing lost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
