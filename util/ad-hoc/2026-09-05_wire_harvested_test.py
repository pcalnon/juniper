#!/usr/bin/env python3
"""2026-09-05_wire_harvested_test.py -- register a harvested test in all three lists.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

juniper-ml's test inventory is **hand-maintained in three places**, and a new test
file registers itself in none of them:

    .github/workflows/ci.yml   the `Regression Tests` job's explicit command list
    AGENTS.md                  the agent-facing run list
    docs/REFERENCE.md          the Test Suite Reference

A harvested suite that is added to the tree and to none of these passes locally,
passes review, and **never runs in CI**. That is a vacuous green: the file is present,
the suite is real, and nothing executes it.

Taking the source PR's own versions of those three files is not an option -- each was
written against a stale base and would revert whatever the other concurrent sessions
have since added. The registration has to be re-derived against current `main`, which
is what this does: insert one line per list, in place, idempotently.

IDEMPOTENT: a path already present in a list is left alone, so re-running after a
partial edit is safe.

Usage:
    2026-09-05_wire_harvested_test.py --test tests/test_x.py --desc "one line" [...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

CI = Path(".github/workflows/ci.yml")
AGENTS = Path("AGENTS.md")
REFERENCE = Path("docs/REFERENCE.md")


def _wire_ci(test: str, desc: str) -> str:
    text = CI.read_text()
    line = f"          python3 -m unittest -v {test}"
    if line in text:
        return "ci.yml: already wired"
    # Anchor on the last existing unittest invocation so the new entry joins the list
    # rather than landing in whatever block happens to sort first.
    marker = "          python3 -m unittest -v tests/"
    idx = text.rfind(marker)
    if idx < 0:
        return "ci.yml: ANCHOR NOT FOUND -- wire by hand"
    eol = text.index("\n", idx) + 1
    block = f"          # {test}: {desc}\n{line}\n"
    CI.write_text(text[:eol] + block + text[eol:])
    return "ci.yml: wired"


def _wire_agents(test: str) -> str:
    text = AGENTS.read_text()
    line = f"python3 -m unittest -v {test}"
    if line in text:
        return "AGENTS.md: already wired"
    marker = "python3 -m unittest -v tests/"
    idx = text.rfind(marker)
    if idx < 0:
        return "AGENTS.md: ANCHOR NOT FOUND -- wire by hand"
    eol = text.index("\n", idx) + 1
    AGENTS.write_text(text[:eol] + line + "\n" + text[eol:])
    return "AGENTS.md: wired"


def _wire_reference(test: str, desc: str) -> str:
    text = REFERENCE.read_text()
    entry = f"- `{test}` -- {desc}"
    if f"- `{test}`" in text:
        return "REFERENCE.md: already listed"
    marker = "- `tests/"
    idx = text.rfind(marker)
    if idx < 0:
        return "REFERENCE.md: ANCHOR NOT FOUND -- add by hand"
    eol = text.index("\n", idx) + 1
    REFERENCE.write_text(text[:eol] + entry + "\n" + text[eol:])
    return "REFERENCE.md: wired"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", action="append", required=True, metavar="PATH")
    ap.add_argument("--desc", action="append", required=True, metavar="TEXT")
    args = ap.parse_args(argv)

    if len(args.test) != len(args.desc):
        print("--test and --desc must be given the same number of times")
        return 2

    for test, desc in zip(args.test, args.desc):
        if not Path(test).exists():
            print(f"{test}: FILE NOT PRESENT -- take it before wiring it")
            return 1
        print(f"{test}")
        for result in (_wire_ci(test, desc), _wire_agents(test), _wire_reference(test, desc)):
            print(f"    {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
