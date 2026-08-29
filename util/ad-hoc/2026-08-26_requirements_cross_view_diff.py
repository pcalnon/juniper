#!/usr/bin/env python3
"""
Measure the requirements cross-view inconsistency: where by-area, by-repo and by-status disagree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation (T6 tail §4: the requirements cross-view inconsistency)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md §11 and
         the v5-1 row of its status table (where the 52 / 149 / trailing-period counts are recorded);
         util/requirements_consolidate.py (--check-roundtrip, which covers by-area ONLY)

Why this exists
---------------
The v5-1 rebuild recorded that the three view families disagree -- "52 entries by-area vs by-repo,
149 by-area vs by-status, by-area carrying a spurious trailing period" -- and concluded that
regenerating any family from another would propagate a defect. That conclusion is load-bearing:
it is why `requirements_consolidate.py` is append-only and re-emits bodies verbatim.

But those counts are a dated SNAPSHOT taken before the v5 `rec` block landed, and nothing in the
repo re-measures them: `--check-roundtrip` asserts render(parse(x)) == x across the 15 by-area
files and never looks at by-repo or by-status at all. So the disagreement is recorded, unmeasured
since, and ungated. This re-measures it from the shipped corpus.

The plan (§97) describes by-repo and by-status as "thin indexes that link into by-area -- not
duplicates ... avoids the maintenance trap of three copies of every requirement going stale
independently". What shipped does not match: every family carries full entry bodies. Three copies
is exactly what exists, which is the mechanism by which they drifted.

Usage
-----
    python3 util/ad-hoc/2026-08-26_requirements_cross_view_diff.py [--req-root DIR] [--json]
                                                                  [--show N]

Exit 0 always -- this reports, it does not gate.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REQ_ROOT = REPO_ROOT / "notes" / "requirements"

#: `### JR-<REPO>-<AREA>-<NNN> — <title>` (em dash, per the shipped corpus).
HEADING_RE = re.compile(r"^###\s+(JR-[A-Z]+-[A-Z]+-\d+)\s+—\s+(.*)$")
#: `**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: ml`
FIELD_RE = re.compile(r"\*\*(Status|Priority|Category|Owner)\*\*:\s*([^\s*]+)")

FAMILIES = ("by-area", "by-repo", "by-status")
COMPARED_FIELDS = ("status", "priority", "category", "owner")


def parse_family(family_dir: Path) -> "dict[str, dict]":
    """Every entry in one view family, keyed by JR id.

    A family is a directory of markdown files; an entry is a `###` heading plus the field line
    that follows it. Duplicate ids WITHIN a family are recorded rather than silently collapsed --
    that is itself a defect class, and merging them away would hide it.
    """
    entries: "dict[str, dict]" = {}
    for path in sorted(family_dir.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            match = HEADING_RE.match(line)
            if not match:
                continue
            req_id, title = match.group(1), match.group(2).strip()
            fields = {}
            # The field line is within a few lines of the heading; scan a small window rather
            # than assuming an exact offset, which differs between families.
            for probe in lines[index + 1 : index + 5]:
                found = dict(FIELD_RE.findall(probe))
                if found:
                    fields = {k.lower(): v for k, v in found.items()}
                    break
            # Body = everything from the heading to the next heading (or EOF), heading excluded.
            # Compared across families because the headline finding -- "the families disagree, so
            # regenerating one from another propagates a defect" -- is only safe to revise if the
            # BODIES agree too, not merely the ids and the four metadata fields.
            end = index + 1
            while end < len(lines) and not HEADING_RE.match(lines[end]):
                end += 1
            body = "\n".join(lines[index + 1 : end]).strip()
            record = {"title": title, "file": path.name, "body": body, **fields}
            if req_id in entries:
                entries[req_id].setdefault("duplicates", []).append(record)
            else:
                entries[req_id] = record
    return entries


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--req-root", default=str(DEFAULT_REQ_ROOT))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--show", type=int, default=8, help="sample rows to print per finding (default 8)")
    args = parser.parse_args(argv)

    req_root = Path(args.req_root).expanduser().resolve()
    families = {name: parse_family(req_root / name) for name in FAMILIES if (req_root / name).is_dir()}

    report: "dict" = {"counts": {name: len(entries) for name, entries in families.items()}}

    area = families.get("by-area", {})
    for other in ("by-repo", "by-status"):
        rows = families.get(other, {})
        missing_here = sorted(set(area) - set(rows))
        extra_here = sorted(set(rows) - set(area))
        field_diffs = []
        title_diffs = []
        for req_id in sorted(set(area) & set(rows)):
            for field in COMPARED_FIELDS:
                left, right = area[req_id].get(field), rows[req_id].get(field)
                if left != right:
                    field_diffs.append({"id": req_id, "field": field, "by-area": left, other: right})
            if area[req_id]["title"] != rows[req_id]["title"]:
                title_diffs.append(
                    {
                        "id": req_id,
                        "by-area": area[req_id]["title"],
                        other: rows[req_id]["title"],
                        # Does the difference survive stripping trailing '.' and whitespace? If not,
                        # this row is punctuation, not divergent content -- which decides whether the
                        # corpus needs a normalization pass or a reconciliation.
                        "punctuation_only": area[req_id]["title"].rstrip(". ") == rows[req_id]["title"].rstrip(". "),
                    }
                )
        body_diffs = [req_id for req_id in sorted(set(area) & set(rows)) if area[req_id]["body"] != rows[req_id]["body"]]
        report[f"by-area vs {other}"] = {
            "body_mismatches": body_diffs,
            "in_by_area_only": missing_here,
            f"in_{other.replace('-', '_')}_only": extra_here,
            "symmetric_difference": len(missing_here) + len(extra_here),
            "field_mismatches": field_diffs,
            "title_mismatches": title_diffs,
        }

    # The recorded "spurious trailing period": a title ending in '.' where the corresponding
    # entry in another family does not. Counted per family so the asymmetry is visible.
    report["trailing_period"] = {name: sum(1 for e in entries.values() if e["title"].endswith(".")) for name, entries in families.items()}
    report["duplicate_ids_within_family"] = {name: sorted(i for i, e in entries.items() if "duplicates" in e) for name, entries in families.items()}

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print("entries per family:", ", ".join(f"{k}={v}" for k, v in report["counts"].items()))
    print("titles ending in '.':", ", ".join(f"{k}={v}" for k, v in report["trailing_period"].items()))
    for name, dupes in report["duplicate_ids_within_family"].items():
        if dupes:
            print(f"DUPLICATE ids within {name}: {len(dupes)} -> {', '.join(dupes[: args.show])}")
    for other in ("by-repo", "by-status"):
        key = f"by-area vs {other}"
        if key not in report:
            continue
        section = report[key]
        print(f"\n=== {key} ===")
        print(f"  symmetric difference : {section['symmetric_difference']}")
        print(f"    in by-area only    : {len(section['in_by_area_only'])} {section['in_by_area_only'][: args.show]}")
        only_key = f"in_{other.replace('-', '_')}_only"
        print(f"    in {other} only : {len(section[only_key])} {section[only_key][: args.show]}")
        print(f"  BODY mismatches      : {len(section['body_mismatches'])} {section['body_mismatches'][: args.show]}")
        print(f"  field mismatches     : {len(section['field_mismatches'])}")
        for row in section["field_mismatches"][: args.show]:
            print(f"    {row['id']:22s} {row['field']:9s} by-area={row['by-area']!r} {other}={row[other]!r}")
        punctuation = [r for r in section["title_mismatches"] if r["punctuation_only"]]
        substantive = [r for r in section["title_mismatches"] if not r["punctuation_only"]]
        print(f"  title mismatches     : {len(section['title_mismatches'])} ({len(punctuation)} punctuation-only, {len(substantive)} SUBSTANTIVE)")
        for row in substantive[: args.show]:
            print(f"    {row['id']:22s}\n      by-area : {row['by-area'][:160]}\n      {other:9s}: {row[other][:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
