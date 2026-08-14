"""Assemble the API primer from its per-section fragments into one markdown document.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-13
Status: ad-hoc -- one-off (document build)
Retire when: the primer has been assembled and merged; the fragments are transient
             build inputs and are not retained in the repository.
Related: notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md

The primer was drafted in parallel as independent section fragments so that each could be
researched and cited separately. This script is the deterministic join: it concatenates the
fragments in a fixed order, emits the part headings, and normalises whitespace so the result
passes ``markdownlint`` under the repo's 512-column configuration.

It is deliberately a pure function of the fragment directory -- rerunning it with the same
inputs reproduces the same document byte-for-byte -- so a reviewer can regenerate the build
rather than trusting a hand-spliced file.

Usage::

    python util/ad-hoc/2026-08-13_assemble_api_primer.py --fragments DIR --out PATH [--check]

``--check`` writes nothing and exits 1 if the assembled text differs from ``--out``.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Ordered build manifest. A ``str`` entry is a fragment filename read from --fragments;
# a ``tuple`` entry is a literal heading emitted inline (the part dividers, which belong to
# the document's structure rather than to any one fragment).
MANIFEST: list[str | tuple[str, str]] = [
    "00-frontmatter.md",
    ("heading", "## Part I — The Web API Landscape"),
    "part1a.md",
    "part1b.md",
    "part1-example.md",
    ("heading", "## Part II — REST and HTTP Semantics in Depth"),
    "part2a.md",
    "part2b.md",
    "part2-example.md",
    ("heading", "## Part III — Library and SDK API Design"),
    "part3.md",
    "part3-example.md",
    "appendices.md",
    "appendix-d.md",
]

# Placeholder in the front matter that the generated table of contents replaces.
TOC_MARKER = "<!-- TOC -->"

# Fragments carry a trailing handoff block for the integrator; it must never reach the document.
_HANDOFF_RE = re.compile(r"<!--\s*HANDOFF NOTES.*?-->", re.DOTALL | re.IGNORECASE)
# Section markers exist only in the scaffold; the assembled document does not need them.
_MARKER_RE = re.compile(r"^<!--\s*SECTION-MARKER:.*?-->\s*$", re.MULTILINE)


def normalise(text: str) -> str:
    """Strip handoff blocks and markers, drop trailing whitespace, collapse blank runs.

    markdownlint's MD009 (trailing spaces) and MD012 (multiple blank lines) are the two rules
    that fragment concatenation reliably violates, so both are fixed here rather than by hand
    in fourteen separate files.
    """
    text = _HANDOFF_RE.sub("", text)
    text = _MARKER_RE.sub("", text)
    lines = [ln.rstrip() for ln in text.replace("\t", "    ").splitlines()]

    out: list[str] = []
    blanks = 0
    in_fence = False
    for line in lines:
        # Blank-line collapsing must not touch fenced blocks -- deliberate spacing inside a
        # code example is content, not formatting.
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            blanks = 0
            continue
        if in_fence:
            out.append(line)
            continue
        if line == "":
            blanks += 1
            if blanks > 1:
                continue
        else:
            blanks = 0
        out.append(line)
    return "\n".join(out).strip("\n")


def slugify(heading: str) -> str:
    """Reproduce GitHub/markdownlint anchor generation for a heading's text.

    Lowercase, strip anything that is not a word character / space / hyphen, then map spaces to
    hyphens. Em dashes therefore vanish rather than becoming hyphens, which is why a heading like
    "Appendix D — Running the Examples" anchors as ``appendix-d--running-the-examples`` with the
    doubled hyphen. Getting this wrong is the usual cause of a dead in-document link.
    """
    text = heading.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s", "-", text)


def build_toc(body: str) -> str:
    """Render a two-level table of contents from the assembled body's H2 and H3 headings."""
    lines: list[str] = ["## Contents", ""]
    in_fence = False
    for raw in body.splitlines():
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{2,3})\s+(.*)$", raw)
        if not match:
            continue
        level, title = len(match.group(1)), match.group(2).strip()
        if title == "Contents":
            continue
        indent = "" if level == 2 else "  "
        lines.append(f"{indent}- [{title}](#{slugify(title)})")
    return "\n".join(lines)


def build(fragments: Path) -> str:
    """Join every manifest entry into the finished document body."""
    chunks: list[str] = []
    missing: list[str] = []

    for entry in MANIFEST:
        if isinstance(entry, tuple):
            chunks.append(entry[1])
            continue
        path = fragments / entry
        if not path.is_file():
            missing.append(entry)
            continue
        body = normalise(path.read_text(encoding="utf-8"))
        if body:
            chunks.append(body)

    if missing:
        # A silently short document is the failure mode worth being loud about: it looks
        # complete and simply omits whole sections.
        print(f"ERROR: {len(missing)} fragment(s) missing: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(2)

    body = "\n\n".join(chunks) + "\n"

    # The document is long enough that it is unusable without a contents listing, so the TOC is
    # generated from the assembled headings rather than hand-maintained -- a hand-written TOC is
    # simply a second place for the structure to go stale.
    if TOC_MARKER in body:
        body = body.replace(TOC_MARKER, build_toc(body), 1)
    else:
        print(f"WARNING: {TOC_MARKER} not found; document assembled without a table of contents.", file=sys.stderr)

    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble the API primer from fragments.")
    parser.add_argument("--fragments", required=True, type=Path, help="Directory holding the section fragments.")
    parser.add_argument("--out", required=True, type=Path, help="Destination markdown file.")
    parser.add_argument("--check", action="store_true", help="Compare only; write nothing. Exit 1 on difference.")
    args = parser.parse_args(argv)

    if not args.fragments.is_dir():
        print(f"ERROR: fragments directory not found: {args.fragments}", file=sys.stderr)
        return 2

    assembled = build(args.fragments)

    if args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.is_file() else ""
        if current != assembled:
            print(f"DIFFERS: {args.out} is not the assembly of {args.fragments}", file=sys.stderr)
            return 1
        print(f"OK: {args.out} matches the fragment assembly.")
        return 0

    args.out.write_text(assembled, encoding="utf-8")
    print(f"Wrote {args.out} ({len(assembled.splitlines())} lines) from {len(MANIFEST)} manifest entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
