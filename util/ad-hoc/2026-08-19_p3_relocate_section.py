#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
License:     MIT License

P3 of the shared-session-memory plan: relocate one section out of ``AGENTS.md``
into ``docs/REFERENCE.md``, **verbatim**.

Why a script rather than hand-editing
-------------------------------------
The plan says *relocate, do not rewrite*, and G3 (``util/relocation_check.py``)
enforces it by requiring every removed substantive line to reappear in the
destination. Moving the body byte-for-byte makes G3 pass **by construction**
instead of by the author's judgement -- which is the point, because the failure
this whole effort is about is a well-meaning author dropping prose while keeping
the identifiers.

It also keeps each increment reviewable: the diff is a pure move plus a pointer,
so a reviewer checks the pointer and the heading, not 118 lines of prose.

What it does
------------
1. Extracts ``<heading>`` from the source, up to (not including) the next heading
   at the same or a shallower level.
2. Appends the body to the destination under a new ``## <dest-title>`` section,
   inserted before ``--insert-before`` so the destination keeps a sane order.
3. Replaces the source section body with a one-line pointer to the destination
   anchor, keeping the original heading so the docs screen sees no heading
   deletion.

Refuses to run if the destination section already exists (re-entry safety) or if
the source heading is not found exactly once.

Usage:
    python3 util/ad-hoc/2026-08-19_p3_relocate_section.py \\
        --heading '### Tests' --dest-title 'Test Suite Reference' \\
        --anchor 'test-suite-reference' \\
        --insert-before '## Post-Merge Main Verification' \\
        --pointer 'Per-suite descriptions for every regression test.' [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def heading_level(line: str) -> int:
    m = re.match(r"^(#{1,6})\s", line)
    return len(m.group(1)) if m else 0


def extract(lines: list[str], heading: str) -> tuple[int, int]:
    """Return [start, end) covering the heading and its body."""
    hits = [i for i, ln in enumerate(lines) if ln.rstrip("\n") == heading]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one '{heading}', found {len(hits)}")
    start = hits[0]
    level = heading_level(heading)
    for i in range(start + 1, len(lines)):
        lvl = heading_level(lines[i])
        if lvl and lvl <= level:
            return start, i
    return start, len(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--source", default="AGENTS.md")
    ap.add_argument("--dest", default="docs/REFERENCE.md")
    ap.add_argument("--heading", required=True)
    ap.add_argument("--dest-title", required=True)
    ap.add_argument("--anchor", required=True)
    ap.add_argument("--insert-before", required=True)
    ap.add_argument("--pointer", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    src_path, dst_path = root / args.source, root / args.dest
    src = src_path.read_text(encoding="utf-8").splitlines(keepends=True)
    dst = dst_path.read_text(encoding="utf-8").splitlines(keepends=True)

    dest_heading = f"## {args.dest_title}"
    if any(ln.rstrip("\n") == dest_heading for ln in dst):
        raise SystemExit(f"destination already has '{dest_heading}' — refusing (re-entry)")

    start, end = extract(src, args.heading)
    body = src[start + 1:end]                      # everything after the heading
    while body and not body[0].strip():            # trim leading blank lines
        body.pop(0)
    while body and not body[-1].strip():           # trim trailing blank lines
        body.pop()

    anchors = [i for i, ln in enumerate(dst) if ln.rstrip("\n") == args.insert_before]
    if len(anchors) != 1:
        raise SystemExit(
            f"expected exactly one '{args.insert_before}' in {args.dest}, found {len(anchors)}"
        )
    at = anchors[0]

    new_dst = (
        dst[:at]
        + [f"{dest_heading}\n", "\n"]
        + [
            f"Relocated verbatim from `{args.source}` "
            f"(P3 of the shared-session-memory plan) so it is read on demand "
            f"rather than loaded into every session.\n",
            "\n",
        ]
        + body
        + ["\n", "---\n", "\n"]
        + dst[at:]
    )

    new_src = (
        src[:start + 1]
        + [
            "\n",
            f"{args.pointer} Moved to "
            f"[`{args.dest}` § {args.dest_title}]({args.dest}#{args.anchor}) — "
            f"read it when working on this area.\n",
            "\n",
        ]
        + src[end:]
    )

    before, after = len("".join(src)), len("".join(new_src))
    print(f"source {args.source}: {before} -> {after} chars ({after - before:+d})")
    print(f"dest   {args.dest}: +{len(''.join(body))} chars ({len(body)} lines moved)")

    if args.dry_run:
        print("DRY RUN — nothing written.")
        return 0

    src_path.write_text("".join(new_src), encoding="utf-8")
    dst_path.write_text("".join(new_dst), encoding="utf-8")
    print("WROTE both files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
