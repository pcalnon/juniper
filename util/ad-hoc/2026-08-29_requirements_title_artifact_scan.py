#!/usr/bin/env python3
"""
Find requirement entries whose TITLE is an extraction artifact, not a title.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-29
Status: ad-hoc -- investigation (CLI-experimentation tail re-probe: intra-entry corpus quality)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md;
         ml#1467 (five artifacts repaired); ml#1462 (by-repo/by-status became a projection)

Why this exists
---------------
The 2026-08-29 arc-tail handoff (ml#1470) left "Detail *selection*" as an unowned item with
the note "Scope unknown -- no scan exists for it". This is that scan, generalised one level
up: `--check-views` compares the three view families against each other, so by construction
it can only find a defect the families DISAGREE about. A defect that every family SHARES --
because all three are generated from the same canonical by-area entry -- is invisible to it.
Title quality is exactly that shape.

What it flags, and why each is a defect
---------------------------------------
``unbalanced-bold``  The title contains ``**`` markers that do not pair. The extractor began
                     mid-way through a bolded run, so the OPENING ``**`` was left behind and
                     only the closing one survived. This is the dominant signature.
``field-label``      The title begins with a field name (``Status``, ``Effort``, ``Detail``,
                     ...) -- a metadata label lifted out of a table or definition list.
``truncated``        The title ends in an ellipsis or a dangling cross-reference (``See....``),
                     so the sentence it was cut from is not recoverable from the title.
``blockquote``       The title begins with a ``>`` marker -- lifted out of a quoted block.

Repair status is reported alongside, because it is the interesting axis: an entry that
carries a ``brief repaired from cited content`` marker AND still trips a check was visited by
a repair pass that did not fix the title. That distinguishes "never inspected" from
"inspected and still wrong", which are different work items.

Usage
-----
    python3 util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py [--json] [--limit N]
    python3 util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py --check   # CI-shaped

Exit 0 = scan completed (or, under ``--check``, no artifacts found); 1 = under ``--check``,
at least one artifact remains; 2 = the corpus directory is unusable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BY_AREA = Path(__file__).resolve().parents[2] / "notes" / "requirements" / "by-area"

ENTRY_RE = re.compile(r"(?m)^### (JR-[A-Z]+-[A-Z]+-\d+) — (.*)$")
REPAIR_RE = re.compile(r"brief repaired from cited content")
FIELD_LABELS = ("Status", "Detail", "Notes", "Overview", "Priority", "Owner", "Effort", "Repo", "Sources")


def classify(title: str) -> list[str]:
    """Return the artifact classes this title trips, or [] if it reads as a title."""
    flags: list[str] = []
    if title.count("**") % 2 == 1:
        flags.append("unbalanced-bold")
    if title.lstrip().startswith(">"):
        flags.append("blockquote")
    if re.match(rf"^\**({'|'.join(FIELD_LABELS)})\**\s*[:\|]", title):
        flags.append("field-label")
    if re.search(r"(See\s*\.{2,}|…\.?$|\.{3,}$)", title.rstrip()):
        flags.append("truncated")
    return flags


def scan(by_area: Path) -> list[dict]:
    """Walk every by-area file and return one record per flagged entry."""
    findings: list[dict] = []
    for path in sorted(by_area.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        matches = list(ENTRY_RE.finditer(text))
        for idx, m in enumerate(matches):
            title = m.group(2).strip()
            flags = classify(title)
            if not flags:
                continue
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[m.end():end]
            findings.append(
                {
                    "id": m.group(1),
                    "file": path.name,
                    "line": text[: m.start()].count("\n") + 1,
                    "flags": flags,
                    "repaired": bool(REPAIR_RE.search(body)),
                    "title": title,
                }
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--limit", type=int, default=20, help="max findings to print in text mode (0 = all)")
    ap.add_argument("--check", action="store_true", help="exit 1 if any artifact remains")
    ap.add_argument("--by-area", type=Path, default=BY_AREA, help="corpus directory")
    args = ap.parse_args(argv)

    if not args.by_area.is_dir():
        print(f"corpus directory not found: {args.by_area}", file=sys.stderr)
        return 2

    total = sum(len(ENTRY_RE.findall(p.read_text(encoding="utf-8"))) for p in sorted(args.by_area.glob("*.md")))
    findings = scan(args.by_area)

    if args.json:
        json.dump({"total_entries": total, "findings": findings}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if (args.check and findings) else 0

    repaired = sum(1 for f in findings if f["repaired"])
    by_flag: dict[str, int] = {}
    for f in findings:
        for fl in f["flags"]:
            by_flag[fl] = by_flag.get(fl, 0) + 1

    shown = findings if args.limit == 0 else findings[: args.limit]
    for f in shown:
        mark = "repaired" if f["repaired"] else "NEVER-REPAIRED"
        print(f"{f['file']}:{f['line']}  {f['id']}  [{','.join(f['flags'])}] ({mark})")
        print(f"    {f['title'][:110]}")
    if len(findings) > len(shown):
        print(f"... {len(findings) - len(shown)} more (use --limit 0)")

    print()
    print(f"entries scanned            : {total}")
    print(f"title artifacts            : {len(findings)}")
    for fl, n in sorted(by_flag.items(), key=lambda kv: -kv[1]):
        print(f"    {fl:<20s}: {n}")
    print(f"  visited by a repair pass : {repaired}  (repair did not fix the title)")
    print(f"  never repaired           : {len(findings) - repaired}")

    return 1 if (args.check and findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
