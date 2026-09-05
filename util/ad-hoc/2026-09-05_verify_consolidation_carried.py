#!/usr/bin/env python3
"""Assert a consolidation actually CARRIED every line its source PRs add.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc verification tooling (Cursor-fleet flood consolidation)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- verification (run before opening any consolidation PR)
Retire when: consolidation stops being a manual disposition for fleet floods.
Related:     util/ad-hoc/2026-09-05_resolve_manifest_append_conflict.py,
             util/ad-hoc/2026-09-05_fleet_docs_consolidate.py (--verify does the
             same job for the docs-version conflict class).

WHY THIS EXISTS -- A REAL NEAR-MISS

Consolidating juniper-ml #1684 + #1686 on 2026-09-05, the whole of #1686's
content was silently absent from the result: no `## Ruleset Context Audit`
section, no index rows, nothing. Every per-hunk resolver line said "resolved",
the cherry-pick reported success, and the tree was clean.

The cause was NOT the resolver. #1686 carried **two** commits and only the tip
-- a version-renumber commit -- had been cherry-picked; the content commit was
never applied. A per-hunk success report cannot see that, because the missing
content was never in a hunk.

That is the general shape: a consolidation can fail in ways every intermediate
step reports as fine. The only sound check is end-to-end -- take the lines the
SOURCE adds, and assert they are in the RESULT.

WHAT IS EXCLUDED, AND WHY THAT IS SAFE

Document header churn (``**Version:**``, ``**Last Updated:**`` ...) is
deliberately dropped during consolidation: the bot pre-allocates a unique
version per PR, every sibling rewrites it, and the consolidated PR gets ONE
coherent header. Those lines are reported as a separate count rather than
silently skipped, so the drop stays visible.

Version-HISTORY rows (``| 0.6.41 | ... |``) are matched on their DESCRIPTION,
not their number, because consolidation renumbers them to whatever main is at.

Usage
-----
    python3 util/ad-hoc/2026-09-05_verify_consolidation_carried.py \
        --base origin/main --head HEAD \
        --source 1684=refs/tmp/p1684 --source 1686=refs/tmp/p1686
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys

NEUTRAL = re.compile(
    r"^\s*\*\*(Version|Status|Last Updated|Author|License|Project|Sub-Project|Maintainer)[:*]",
    re.IGNORECASE,
)
# `| 0.6.41  | 2026-09-04 | Ruleset Context Audit: ... |` -- the number is reassigned
# by consolidation, so identity is the description cell.
HISTORY_ROW = re.compile(r"^\|\s*\d+\.\d+\.\d+\s*\|\s*\d{4}-\d{2}-\d{2}\s*\|(?P<desc>.*)$")
# Any other markdown table row. Its IDENTITY is the first cell; the remaining cells are
# prose that main rewrites freely. A stale branch therefore re-adds an OLD text of a row
# that already exists -- carrying it would duplicate the row (and revert whatever edit
# main made). Present-by-identity is a PASS, reported separately so the substitution is
# visible rather than assumed.
TABLE_ROW = re.compile(r"^\|(?P<first>[^|]+)\|")


def run(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout


def normalise(s: str) -> str:
    return " ".join(s.split())


def added_lines(base: str, head: str) -> list[str]:
    out = []
    for ln in run("diff", f"{base}...{head}").splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            body = ln[1:]
            if body.strip():
                out.append(body)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--source", action="append", required=True,
                    metavar="PR=REF", help="repeatable, e.g. 1684=refs/tmp/p1684")
    args = ap.parse_args()

    # Build the haystack once: every line present in the consolidated tree.
    result_text = ""
    for path in run("diff", "--name-only", f"{args.base}...{args.head}").split():
        try:
            result_text += run("show", f"{args.head}:{path}")
        except SystemExit:
            continue  # deleted in the consolidation
    haystack = {normalise(l) for l in result_text.splitlines() if l.strip()}
    haystack_desc = set()
    haystack_row_ids = set()
    for l in result_text.splitlines():
        s = l.strip()
        m = HISTORY_ROW.match(s)
        if m:
            haystack_desc.add(normalise(m.group("desc")))
            continue
        r = TABLE_ROW.match(s)
        if r:
            haystack_row_ids.add(normalise(r.group("first")).strip("*` "))

    rc = 0
    for spec in args.source:
        pr, _, ref = spec.partition("=")
        adds = added_lines(args.base, ref)
        missing, neutral_skipped, renumbered, superseded = [], 0, 0, 0
        for a in adds:
            if NEUTRAL.match(a):
                neutral_skipped += 1
                continue
            if normalise(a) in haystack:
                continue
            m = HISTORY_ROW.match(a.strip())
            if m and normalise(m.group("desc")) in haystack_desc:
                renumbered += 1
                continue
            r = TABLE_ROW.match(a.strip())
            if r and normalise(r.group("first")).strip("*` ") in haystack_row_ids:
                superseded += 1
                continue
            missing.append(a)

        status = "OK " if not missing else "MISS"
        print(f"[{status}] #{pr}: {len(adds)} added line(s); "
              f"{neutral_skipped} neutral header line(s) deliberately dropped; "
              f"{renumbered} history row(s) matched after renumber; "
              f"{superseded} table row(s) present by identity (main's text won); "
              f"{len(missing)} MISSING")
        for m_ in missing[:25]:
            print(f"        - {m_[:150]}")
        if len(missing) > 25:
            print(f"        ... and {len(missing) - 25} more")
        if missing:
            rc = 1

    print()
    if rc:
        print("FAIL: the consolidation did not carry every source line.")
    else:
        print("OK: every source line is present in the consolidated tree.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
