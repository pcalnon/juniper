#!/usr/bin/env python3
"""
Resolve fleet docs conflicts by ITEM identity, and refuse whatever it cannot key.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 35 juniper-ml docs PRs; supersedes the whole-line union that fragmented 49 rows

WHY NOT A WHOLE-LINE UNION

The previous consolidation emitted 49 headerless table fragments. The cause was a unit
mismatch: the union's unit is the LINE, and a table row's identity is the ROW, so two halves of
one row arrive as two broken rows. The damage scaled with DOC-VERSION DRIFT, not with PR count.

So this keys on the item, not the line. Every conflicted block in this fleet is one of:

  METADATA   `**Version:** ...` / `**Last Updated:** ...` -- HEAD is by construction ahead
             (it carries every already-merged PR's bump), so OURS wins outright.
  INVENTORY  a table, a bullet list, or a directory tree whose entries are addressed by a PATH
             or an ANCHOR. Union keyed on that address: ours in place, theirs appended only
             when its address is absent. A shared address with DIFFERENT text is a rewrite, not
             an addition -- ours wins and the difference is REPORTED.
  PROLOGUE   the lines of THEIRS that precede its first keyable item -- plus any TABLE row
             or header with no counterpart table on our side, which would otherwise land
             outside every table and start a separator-less one. A bullet or tree line has no
             such failure mode and is appended instead. Merged nowhere and printed verbatim with a non-zero exit. This is
             where a superseded prose claim hides, so the report is not an aside: nothing in it
             reached the tree, and it has to be read before the PR opens.
  STRADDLE   a fenced hunk where either side has an ODD number of ``` delimiters: the block
             opens inside the conflict and closes outside it, so no concatenation is safe.
             Refused and left conflicted.
  FENCED+    a balanced fenced hunk whose theirs-side carries a heading that appears nowhere
             else in the file: new material, so ours then theirs, whole.
  FENCED-    the same, but every heading theirs carries already exists somewhere in the file:
             theirs is the ANCESTOR of a section main has rewritten. Ours kept, theirs dropped
             and printed in full. Measured on #1628, whose three claims main had reversed.

Placement matters as much as the key. A new item is spliced immediately after ours' LAST item
of the SAME KIND -- appending it after the whole block is how a row lands past the end of its
table and starts a new, separator-less one.

WHAT THIS DELIBERATELY DOES NOT DO

It does not merge prose. A parked branch can carry a claim `main` has since reversed -- measured
in this very fleet: HEAD says a matrix limitation was "partially lifted", the branch still says
it is a "Known limitation ... deliberate". Those two bullets have no common address, so a
key-union would keep BOTH and land a contradiction that every gate passes. UNKEYED is the
answer, and the count it prints is the real cost of the batch.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Both punctuations occur in this fleet -- `**Version:** 0.6.59` and `**Version**: 1.0.61`.
# A regex that only knows one of them silently reads the other as prose and refuses the hunk.
METADATA = re.compile(r"^\s*\*\*(Version|Last Updated|Status|Maintainer|Project)\s*:?\*\*\s*:?\s*", re.IGNORECASE)
TABLE_ROW = re.compile(r"^\s*\|(.*)\|\s*$")
# A directory entry (`experiments/`) is as addressable as a file; matching only files made a
# tree hunk containing one refuse wholesale.
TREE_ROW = re.compile(r"^[│├└─\s]+([A-Za-z0-9_.\-/]+(?:\.(?:py|bash|md|yml|yaml|toml|sh)|/))\s*(?:#.*)?$")
BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
PATH_TOKEN = re.compile(r"`([A-Za-z0-9_./\-]+\.(?:py|bash|md|yml|yaml|toml|sh))`")
# `](#name)` AND `](FILE.md#name)`. Every cross-file nav bullet uses the second form, so the
# same-file-only pattern read a whole navigation index as unkeyable prose.
ANCHOR = re.compile(r"\]\([A-Za-z0-9_.\-/]*#([a-z0-9\-]+)\)")
FENCE = re.compile(r"^\s*(?:```|~~~)")
HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def _norm(text: str) -> str:
    return re.sub(r"[`*_ ]+", "", text).lower()


def _continues(line: str) -> bool:
    """Does `line` belong to the item above it?

    An INDENTED line (a sub-bullet, a wrapped table cell) or a table separator continues the
    item. A blank line ends it, and so does any unindented free text -- absorbing those made
    ours' last table row own two paragraphs and a heading, so splicing "after that item" landed
    past all of them, under no header at all.
    """
    if not line.strip():
        return False
    return line[:1].isspace() or is_separator(line)


def is_separator(line: str) -> bool:
    m = TABLE_ROW.match(line)
    if not m:
        return False
    first = m.group(1).split("|")[0].strip()
    return bool(first) and set(first) <= set("-: ")


def item_key(line: str, *, table: str = "?", next_line: str = "") -> str | None:
    """The ADDRESS a line carries, or None when it has none.

    A table row is addressed by its first cell AND by the table it sits in -- a header row and a
    data row are not the same kind of thing, and a row keyed on its first cell alone cannot say
    which table it belongs to. A tree line is addressed by its filename; a bullet by the first
    backticked path it names, else by the anchor it links to. A bullet with neither is prose --
    deliberately unaddressable, so the caller refuses it rather than guessing.
    """
    if not line.strip():
        return None
    m = TABLE_ROW.match(line)
    if m:
        cells = [c.strip() for c in m.group(1).split("|")]
        first = cells[0] if cells else ""
        if is_separator(line):
            return "@sep"  # rides with the header above it; never an item of its own
        if not first:
            return None
        if is_separator(next_line):
            # FIRST CELL, not the whole row: a reworded header is the same table, and keying on
            # the full row wrote both versions one above the other.
            return f"@thead:{_norm(first)}"
        return f"@row:{table}:{_norm(first)}"
    m = TREE_ROW.match(line)
    if m:
        return f"@tree:{m.group(1)}"
    m = BULLET.match(line)
    if m:
        indent, body = m.group(1), m.group(2)
        if indent:
            return None  # a SUB-bullet belongs to its parent; it is never keyed on its own
        p = PATH_TOKEN.search(body)
        if p:
            return f"@path:{p.group(1)}"
        a = ANCHOR.search(body)
        if a:
            return f"@anchor:{a.group(1)}"
    return None


def kind_of(key: str) -> str:
    """The splice bucket: `@tree` / `@path` / `@anchor` / `@thead`, and for a data row
    `@row:<table signature>` -- so a row lands beside rows of its OWN table, never another's."""
    parts = key.split(":")
    return f"{parts[0]}:{parts[1]}" if parts[0] == "@row" and len(parts) > 2 else parts[0]


def block_keys(block: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Split a side into `(prologue, keyed items)`.

    A sub-bullet or continuation line is folded into the item above it, so an entry keeps its
    own detail lines when it moves. Lines BEFORE the first keyable one have no item to attach
    to -- they are the prologue, and they are exactly where a superseded prose claim hides, so
    they are returned separately rather than merged or discarded.
    """
    prologue: list[str] = []
    items: dict[str, list[str]] = {}
    order: list[str] = []
    current: str | None = None
    table = "?"
    for idx, line in enumerate(block):
        key = item_key(line, table=table, next_line=block[idx + 1] if idx + 1 < len(block) else "")
        if key == "@sep":
            key = None  # separators ride with the header above them
        elif key and key.startswith("@thead:"):
            table = key[len("@thead:") :]
        elif key is None and line.strip() and not TABLE_ROW.match(line):
            table = "?"  # a non-table line ends the table's scope
        if key is not None:
            current = key if key not in items else f"{key}#{len(items)}"
            items[current] = [line]
            order.append(current)
        elif current is not None and _continues(line):
            items[current].append(line)
        elif line.strip():
            current = None
            prologue.append(line)
        else:
            current = None
    return prologue, {k: items[k] for k in order}


def resolve(path: Path) -> tuple[int, int, list[str]]:
    """Resolve `path` in place. Returns (resolved, refused, report lines)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    # The headings the document would have WITHOUT theirs: ours-side plus everything outside any
    # conflict. Scanning the raw file instead sweeps up each hunk's own theirs-side, so every
    # heading reads as "already present" by virtue of being in the block under judgement -- which
    # verdicted #1639's genuinely new `## F-CANOPY-027 Poller Starvation Probes` as an ancestor.
    elsewhere: set[str] = set()
    _side = "keep"
    for _ln in lines:
        if _ln.startswith("<<<<<<< "):
            _side = "ours"
            continue
        if _ln.startswith("======="):
            _side = "theirs"
            continue
        if _ln.startswith(">>>>>>> "):
            _side = "keep"
            continue
        if _side == "theirs":
            continue
        if m := HEADING_LINE.match(_ln.strip()):
            elsewhere.add(m.group(0).strip())
    out: list[str] = []
    resolved = refused = 0
    report: list[str] = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("<<<<<<< "):
            out.append(lines[i])
            i += 1
            continue
        start = i
        i += 1
        ours: list[str] = []
        while i < len(lines) and not lines[i].startswith("======="):
            ours.append(lines[i])
            i += 1
        i += 1
        theirs: list[str] = []
        while i < len(lines) and not lines[i].startswith(">>>>>>> "):
            theirs.append(lines[i])
            i += 1
        i += 1

        if all(METADATA.match(ln) or not ln.strip() for ln in ours + theirs):
            out.extend(ours)
            resolved += 1
            report.append(f"    METADATA  line {start+1}: ours kept ({len(ours)} line(s))")
            continue

        # OURS is written back WHOLE, prologue included, because HEAD is the tree every
        # already-merged PR agreed on. Only THEIRS is decomposed -- so `ours` never needs to be
        # keyable, and requiring it to be (an earlier version did) refused hunks whose ours-side
        # happened to be one continuation line.
        # A fence delimiter has no address, so it would go to the prologue and be DROPPED --
        # unbalancing every fence after it. Structural punctuation is not prose, so the block is
        # decided WHOLE, by the headings theirs carries.
        if any(FENCE.match(ln) for ln in theirs):
            their_headings = [m.group(0).strip() for ln in theirs if (m := HEADING_LINE.match(ln.strip()))]
            # File-wide, not hunk-wide. "Ours lacks this heading" is also true of a section that
            # already sits two hundred lines further down, and appending it there duplicates a
            # whole operator surface -- the 49-fragment shape, one level up.
            novel = [h for h in their_headings if h not in elsewhere]
            # PARITY, before novelty. An odd fence count on a side means the block OPENS inside
            # the conflict and CLOSES outside it -- the two sides are two versions of one
            # straddling block, and concatenating them emits two openers against one closer.
            # Measured on #1662: 21 H2 headings swallowed and the document left unclosed.
            straddles = sum(1 for ln in ours if FENCE.match(ln)) % 2 or sum(1 for ln in theirs if FENCE.match(ln)) % 2
            if straddles:
                out.append(lines[start])
                out.extend(ours)
                out.append("=======")
                out.extend(theirs)
                out.append(lines[i - 1])
                refused += 1
                report.append(f"    STRADDLE  line {start+1}: a fenced block crosses the conflict boundary -- left conflicted, resolve by hand")
            elif novel:
                out.extend(ours)
                out.extend(theirs)
                resolved += 1
                report.append(f"    FENCED+   line {start+1}: theirs carries {len(novel)} heading(s) absent from the file -- ours THEN theirs ({novel[:3]})")
            else:
                out.extend(ours)
                refused += 1
                report.append(f"    FENCED-   line {start+1}: every heading theirs carries already exists -- theirs is the ancestor; {len(theirs)} line(s) dropped:")
                for line in theirs:
                    report.append(f"        | {line}")
            continue

        _, our_items = block_keys(ours)
        their_prologue, their_items = block_keys(theirs)

        # Build ours as a LIST of (key, lines) so a new item can be spliced beside its own kind
        # rather than after the whole block. Appending past the end of a table is what started a
        # new, separator-less one.
        merged: list[tuple[str | None, list[str]]] = []
        our_table = "?"
        for idx, line in enumerate(ours):
            key = item_key(line, table=our_table, next_line=ours[idx + 1] if idx + 1 < len(ours) else "")
            if key == "@sep":
                key = None
            elif key and key.startswith("@thead:"):
                our_table = key[len("@thead:") :]
            elif key is None and line.strip() and not TABLE_ROW.match(line):
                our_table = "?"
            if key is not None:
                merged.append((key, [line]))
            elif merged and merged[-1][0] is not None and _continues(line):
                merged[-1][1].append(line)
            elif merged and merged[-1][0] is None:
                merged[-1][1].append(line)
            else:
                merged.append((None, [line]))
        our_addr = {k.split("#")[0] for k in our_items}
        our_kinds = {kind_of(k) for k in our_items}

        added = 0
        unplaced: list[str] = []
        for key, body in their_items.items():
            addr = key.split("#")[0]
            if addr in our_addr:
                if body != our_items.get(key, body):
                    report.append(f"    REWRITE   line {start+1}: {addr} differs -- ours kept, theirs dropped")
                continue
            kind = kind_of(addr)
            if kind in our_kinds:
                last = max(idx for idx, (k, _) in enumerate(merged) if k is not None and kind_of(k.split("#")[0]) == kind)
                merged.insert(last + 1, (key, body))
                added += 1
                continue
            # No item of this kind on our side. For a TABLE that is fatal -- a row with no
            # header lands outside every table and starts a separator-less one -- so it goes to
            # the residue. A bullet or tree line has no such failure mode: appended after ours'
            # block it joins the surrounding list. Refusing those cost 216 addressable lines.
            if kind.startswith(("@row", "@thead")):
                unplaced.extend(body)
                continue
            merged.append((key, body))
            added += 1

        for _, body in merged:
            out.extend(body)
        resolved += 1
        report.append(f"    INVENTORY line {start+1}: {len(our_items)} ours + {added} new from theirs")
        residue = their_prologue + unplaced
        if residue:
            refused += 1
            report.append(f"    PROLOGUE  line {start+1}: {len(residue)} unkeyable line(s) from theirs NOT written -- read and place by hand:")
            for line in residue:
                report.append(f"        | {line}")

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return resolved, refused, report


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    total_refused = 0
    for arg in args:
        p = Path(arg)
        resolved, refused, report = resolve(p)
        print(f"{p}: {resolved} resolved, {refused} refused")
        for line in report:
            print(line)
        total_refused += refused
    return 1 if total_refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
