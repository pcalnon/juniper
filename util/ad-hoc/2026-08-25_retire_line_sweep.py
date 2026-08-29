#!/usr/bin/env python3
"""
Rewrite every ad-hoc `Retire when:` line to the 2026-08-25 retention policy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — one-off (retention-policy sweep)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/README.md Lifecycle table; the 2026-08-24 determinism arc's close-out report

Owner decision 2026-08-25: util/ad-hoc scripts are retained as the provenance of how
evidence, migrations, and one-off analyses were produced — no script carries a retirement
deadline. This sweep rewrites each existing `Retire when: <condition>` line, in place, to:

    Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: <condition>

Deliberately line-local: only the first matching line per file is rewritten and nothing is
deleted, so a condition that wraps onto continuation lines stays readable as the tail of the
"Previously:" sentence. Idempotent — a line already carrying RETAINED is left alone.

Usage: 2026-08-25_retire_line_sweep.py [--apply]   (default: dry-run report)
"""

import argparse
import re
import sys
from pathlib import Path

MARK = "RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously:"
LINE = re.compile(r"^(?P<prefix>.*?Retire when:\s*)(?P<cond>\S.*)$")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    adhoc = Path(__file__).resolve().parent
    me = Path(__file__).resolve()
    changed = skipped = already = 0
    for path in sorted(adhoc.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".bash", ".sh", ".yaml", ".yml"} or path.resolve() == me:
            continue
        # Files under retired/ completed the OLD lifecycle; their historical headers stand.
        if "retired" in path.relative_to(adhoc).parts:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        lines = text.splitlines(keepends=True)
        for i, line in enumerate(lines):
            m = LINE.match(line)
            if not m:
                continue
            if "RETAINED" in m.group("cond"):
                already += 1
                break
            eol = "\n" if line.endswith("\n") else ""
            lines[i] = f"{m.group('prefix')}{MARK} {m.group('cond').rstrip()}{eol}"
            rel = path.relative_to(adhoc)
            print(f"{'APPLY ' if args.apply else 'would '}rewrite {rel}:{i + 1}")
            if args.apply:
                path.write_text("".join(lines))
            changed += 1
            break
        else:
            skipped += 1
    print(f"\n{'rewrote' if args.apply else 'would rewrite'} {changed}; already-retained {already}; no Retire-when line {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
