#!/usr/bin/env python3
"""
Repair requirement-entry titles that are extraction artifacts — markup only, by default.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-30
Status: ad-hoc -- migration (corpus title-artifact repair)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py (the detector this repairs
         against); ml#1475 §5 (the 172-entry measurement); ml#1467 (the five-entry repair whose
         idiom this follows)

Why this is deliberately narrow
-------------------------------
The v3 repair pass already visited 163 of the 172 broken titles and left them broken — worse, in
at least one case it made the entry *less* informative: `JR-ML-API-005`'s marker records the
discarded title as ``'4.3 CR-024: Chunked Encoding Body Limit'`` (which named the subject) and
the replacement is ``Effort**: 0.5 day | **Repo**: … | **Status**: FIXED.`` (an effort-estimate
cell). The lesson is not "repair harder"; it is that **one rule applied to every shape is how the
damage happened**. So this tool fixes only the shape where the correct output is mechanically
determined, and REFUSES to guess at the rest.

Two classes, and only one is automated
--------------------------------------
**MARKUP (automated).** The title's *text* is a serviceable statement; only the markdown around
it is broken:

* ``unbalanced-bold`` — the extractor began inside a ``**bold**`` run, so the opening ``**`` was
  left behind and only the closing one survived (``Output weights transposition bug**: …``). The
  repair restores the opening marker, which is the only edit that makes the emphasis balance
  without altering a character of prose.
* ``blockquote`` — a leading ``>`` lifted out of a quoted block. Stripping it changes no words.

**CONTENT (reported, never written).** The title is not a title and no mechanical rule recovers
one:

* ``truncated`` — ends mid-sentence at ``….``; the missing words exist only in the cited source.
* ``field-label`` — the title is a metadata cell (``Effort``, ``Status``, ``Repo``), so there is
  nothing to repair; a *subject* has to be chosen, which is an editorial decision.

Reported with the entry's cited source range so a human (or a later, source-reading pass) can
resolve them. Passing ``--include-content`` is refused on purpose — the flag exists so that
someone reaching for it reads this paragraph.

Idempotence
-----------
The guard matches the **whole heading line**, never a substring. That matters here specifically:
the repair PREPENDS to the title, so the old text is a strict substring of the new one, and a
naive ``count(old)`` check would keep matching after the edit and re-apply forever — the exact
trap ml#1467 hit from the other direction.

Usage
-----
    python3 util/ad-hoc/2026-08-30_requirements_title_repair.py            # dry run (default)
    python3 util/ad-hoc/2026-08-30_requirements_title_repair.py --write
    python3 util/ad-hoc/2026-08-30_requirements_title_repair.py --report-content

Exit 0 = completed (or dry run); 2 = the corpus is unusable or a guard tripped.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BY_AREA = Path(__file__).resolve().parents[2] / "notes" / "requirements" / "by-area"

ENTRY_RE = re.compile(r"(?m)^### (JR-[A-Z]+-[A-Z]+-\d+) — (.*)$")
FIELD_LABELS = ("Status", "Detail", "Notes", "Overview", "Priority", "Owner", "Effort", "Repo", "Sources")
BLOCKQUOTE_LEAD = re.compile(r"^>\s*")
# A `**Lead**: rest` construction whose opening marker was cut. Two shapes, because the separator
# may sit on either side of the surviving `**`:
#   `Lead**: rest`   -> the colon is INSIDE the closing marker's trailing text
#   `Lead:** rest`   -> the colon is INSIDE the bold run, i.e. `**Lead:**`
# The second shape is not cosmetic: stripping its `**` turns `Lead:**` into `Lead: `, and in an
# UNQUOTED YAML scalar a colon-space is a mapping separator — which is exactly how the first run
# of this tool produced an unparseable ledger.
CUT_OPENING_BOLD = re.compile(r"^[^*]+(\*\*\s*[:\-—]|[:\-—]\s*\*\*)")


def classify(title: str) -> list[str]:
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


def repair_markup(title: str) -> str:
    """Restore balanced markup WITHOUT changing any word of the prose."""
    out = BLOCKQUOTE_LEAD.sub("", title.strip()).strip()
    if out.count("**") % 2 == 1:
        if CUT_OPENING_BOLD.match(out):
            out = "**" + out          # restore the opening marker the extractor ate
        else:
            out = out.replace("**", "", 1)  # a lone stray marker with no lead-in: drop it
    return out


def repair_ledger(ledger: Path, ids: list[str], write: bool) -> list[tuple[str, str, str]]:
    """Apply the same markup repair to each named id's ``brief:`` in the ledger.

    The ledger carries the title as ``brief``, **truncated by design**, so the brief cannot be
    overwritten with the by-area title — it has to be repaired independently by the same rule.
    Matched by id rather than by text for that reason.

    Targeted string surgery, never ``yaml.safe_dump``: a round-trip through PyYAML re-wraps and
    re-quotes all 1,814 rows, turning a 81-line change into a whole-file rewrite (ml#1467).
    Single-quoted YAML scalars escape an inner quote by doubling it; the repair only ever adds
    ``**`` or strips a leading ``>``, so quoting is never disturbed.
    """
    text = ledger.read_text(encoding="utf-8")
    changed: list[tuple[str, str, str]] = []
    for rid in ids:
        anchor = f"\n- id: {rid}\n"
        if text.count(anchor) != 1:
            print(f"GUARD: ledger anchor for {rid} matched {text.count(anchor)} times", file=sys.stderr)
            return []
        start = text.index(anchor)
        nxt = text.find("\n- id: ", start + 1)
        block = text[start: nxt if nxt != -1 else len(text)]
        m = re.search(r"(?m)^  brief: (.*)$", block)
        if not m:
            continue
        raw = m.group(1)
        quote = raw[0] if raw[:1] in ("'", '"') else ""
        inner = raw[1:-1] if quote and raw.endswith(quote) and len(raw) > 1 else raw
        # Unescape only the YAML doubling so classify()/repair see the real text.
        real = inner.replace(quote * 2, quote) if quote else inner
        if {"truncated", "field-label"} & set(classify(real)):
            continue
        fixed = repair_markup(real)
        if fixed == real:
            continue
        # ALWAYS write the repaired value single-quoted, whatever the original quoting was.
        # A brief that was safely unquoted before the edit may not be after it: the repair can
        # introduce a colon-space (`Lead:**` -> `Lead: `), which YAML reads as a mapping
        # separator and refuses. Quoting unconditionally removes that whole class.
        new_raw = "'" + fixed.replace("'", "''") + "'"
        old_line, new_line = f"  brief: {raw}", f"  brief: {new_raw}"
        if block.count(old_line) != 1:
            print(f"GUARD: brief line for {rid} matched {block.count(old_line)} times", file=sys.stderr)
            return []
        text = text[:start] + block.replace(old_line, new_line, 1) + (text[nxt:] if nxt != -1 else "")
        changed.append((rid, real, fixed))
    # Parse BEFORE writing, always — including on a dry run, so the guard is exercised on the
    # path that does not write. The first version of this tool produced a ledger that failed
    # `yaml.safe_load` at line 11126 and would have been committed had the check lived only in
    # a follow-up command. A repair tool that can emit an unparseable corpus is not finished.
    try:
        import yaml

        parsed = yaml.safe_load(text)
        if not isinstance(parsed, list) or len(parsed) != text.count("\n- id: ") + text.startswith("- id: "):
            print("GUARD: ledger entry count changed after repair — refusing to write", file=sys.stderr)
            return []
    except Exception as exc:  # noqa: BLE001 - any parse failure must block the write
        print(f"GUARD: repaired ledger does not parse ({exc.__class__.__name__}) — refusing to write", file=sys.stderr)
        return []

    if write and changed:
        ledger.write_text(text, encoding="utf-8")
    return changed


def entry_source(body: str) -> str:
    """The entry's first cited source line, for the content-class report."""
    m = re.search(r"(?m)^\*\*Sources\*\*:\s*\n-\s*(.+)$", body)
    return m.group(1).strip() if m else "(no source recorded)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="apply the markup repairs (default: dry run)")
    ap.add_argument("--report-content", action="store_true", help="list the content-class entries and exit")
    ap.add_argument("--include-content", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--by-area", type=Path, default=BY_AREA)
    args = ap.parse_args(argv)

    if args.include_content:
        print(
            "refusing --include-content: the truncated / field-label classes have no mechanical\n"
            "repair. Their missing words live only in the cited source, and a field-label title\n"
            "needs a SUBJECT chosen, which is an editorial decision. See this file's docstring.",
            file=sys.stderr,
        )
        return 2

    if not args.by_area.is_dir():
        print(f"corpus directory not found: {args.by_area}", file=sys.stderr)
        return 2

    markup_fixed: list[tuple[str, str, str]] = []
    content: list[tuple[str, str, str, str]] = []

    for path in sorted(args.by_area.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        matches = list(ENTRY_RE.finditer(text))
        replacements: list[tuple[str, str]] = []

        for idx, m in enumerate(matches):
            rid, title = m.group(1), m.group(2).strip()
            flags = classify(title)
            if not flags:
                continue
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[m.end():end]

            if {"truncated", "field-label"} & set(flags):
                content.append((rid, path.name, ",".join(flags), entry_source(body)))
                continue

            new_title = repair_markup(title)
            if new_title == title:
                continue
            if new_title.count("**") % 2 == 1:
                print(f"GUARD: {rid} still unbalanced after repair — refusing to write it", file=sys.stderr)
                return 2
            # Whole-line match: the old title is a SUBSTRING of the new one, so a substring
            # guard would re-apply forever.
            replacements.append((m.group(0), f"### {rid} — {new_title}"))
            markup_fixed.append((rid, title, new_title))

        if replacements and args.write:
            for old_line, new_line in replacements:
                if text.count(old_line) != 1:
                    print(f"GUARD: {old_line[:60]!r} matched {text.count(old_line)} times — refusing", file=sys.stderr)
                    return 2
                text = text.replace(old_line, new_line, 1)
            path.write_text(text, encoding="utf-8")

    if args.report_content:
        print(f"CONTENT class — {len(content)} entries needing an editorial decision (never auto-written):\n")
        for rid, fname, flags, src in content:
            print(f"  {rid:22s} {fname:10s} [{flags}]")
            print(f"      source: {src[:110]}")
        return 0

    ledger = args.by_area.parent / "id_assignments.yaml"
    ledger_changed: list[tuple[str, str, str]] = []
    if ledger.is_file():
        ledger_changed = repair_ledger(ledger, [rid for rid, _, _ in markup_fixed], args.write)

    print(f"MARKUP class — {len(markup_fixed)} titles {'REPAIRED' if args.write else 'would be repaired'}:")
    for rid, before, after in markup_fixed[:10]:
        print(f"  {rid}")
        print(f"    before: {before[:100]}")
        print(f"    after : {after[:100]}")
    if len(markup_fixed) > 10:
        print(f"  ... {len(markup_fixed) - 10} more")
    print(f"\nLEDGER — {len(ledger_changed)} brief(s) {'repaired' if args.write else 'would be repaired'}.")
    print(f"CONTENT class — {len(content)} entries left alone (run --report-content).")
    if not args.write:
        print("\nDRY RUN — nothing written. Re-run with --write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
