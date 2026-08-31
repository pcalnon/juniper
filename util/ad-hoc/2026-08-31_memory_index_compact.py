#!/usr/bin/env python3
"""Compact the auto-memory MEMORY.md index by MOVING hook detail into topic files.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc memory-governance tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-31
Status:      ad-hoc -- the full index pass deferred by the owner to the end of the
             shared-session-memory arc (tracker juniper-ml#1326).
Retire when: the index is under budget and a forward-only cap keeps it there.

Why this is not the eviction tool
---------------------------------
`2026-08-19_memory_index_evict.py` DROPS whole rows from a hand-curated slug list.
That list is exhausted -- it now frees 0 rows / 0 bytes while exiting clean -- and
the rows that remain are nearly all LIVE, so dropping them is not available. The
byte problem is therefore not "too many entries" but "hooks that accreted into
paragraphs": 122 of 137 rows exceed the 120-byte cap that the plan's section 5
row 4 fixes for NEW entries, and their excess above that cap is 8,176 bytes.

The safety property that makes this different from truncation
-------------------------------------------------------------
Nothing is deleted. For every row it shortens, this script FIRST appends the
row's current hook verbatim into that row's own topic file, under a dated
heading, and only then rewrites the row. A topic file is on-demand rather than
resident, so the fact is demoted, not lost -- which is the same trade the
relocation work makes for `AGENTS.md`.

It refuses to shorten a row whose target it cannot open, because a row with
nowhere to move its detail to can only be truncated, and truncation here is
silent data loss.

Two phases, because a mechanically generated hook is a draft
------------------------------------------------------------
    --plan   print the proposed short hook for every over-cap row, flagging any
             where the proposal drops a distinctive token (a PR ref, an
             identifier, a path) that the first clause does not carry.
    --apply  move the hooks and rewrite the index.

The flags exist because the first clause is usually the headline but sometimes
is not, and a hook that no longer helps you decide relevance has failed at the
only job an index row has.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

MEM = Path.home() / ".claude" / "projects" / "-home-pcalnon-Development-python-Juniper-juniper-ml" / "memory"
INDEX = MEM / "MEMORY.md"
CAP = 90  # bytes of HOOK, not of row
BYTE_TARGET = 17_510

ROW = re.compile(r"^- \[(?P<title>.+)\]\((?P<target>[^)\s]+)\)(?: — (?P<hook>.*))?$")
# Tokens whose loss from a hook is most likely to matter.
DISTINCTIVE = re.compile(
    r"(?:[a-z-]+#\d+|\b[A-Z]{2,}-[A-Z0-9]+-\d+\b|`[^`]+`|\b[\w./-]+\.(?:py|bash|md|json|yaml|yml|toml)\b|\b\d{2,3},\d{3}\b)"
)


def short_hook(hook: str, budget: int) -> str:
    """Take the leading clause, then hard-trim to the byte budget."""
    if not hook:
        return ""
    # Prefer a natural break: the first of these that leaves something substantial.
    for sep in ("; ", " — ", ". ", ", "):
        head = hook.split(sep)[0]
        if len(head.encode()) <= budget and len(head) > 25:
            return head.rstrip(" .;,—-")
    # No usable clause break: trim to a WORD boundary and mark the elision.
    # A mid-word cut ("VIEWS are c") reads as corruption rather than as a
    # summary, and an index row that looks corrupt gets distrusted wholesale.
    words, out = hook.split(), ""
    for w in words:
        cand = (out + " " + w).strip()
        if len(cand.encode()) + 1 > budget:
            break
        out = cand
    out = out.rstrip(" .;,—-")
    # Never leave an unbalanced backtick or bold marker behind.
    if out.count("`") % 2:
        out = out.rsplit("`", 1)[0].rstrip(" .;,—-")
    if out.count("**") % 2:
        out = out.rsplit("**", 1)[0].rstrip(" .;,—-")
    return (out + "…") if out and len(out) < len(hook) else out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="move hooks and rewrite (default: plan)")
    ap.add_argument("--cap", type=int, default=CAP)
    args = ap.parse_args()

    lines = INDEX.read_text(encoding="utf-8").splitlines()
    before_bytes = len(INDEX.read_text(encoding="utf-8").encode())

    plan, skipped, flagged = [], [], []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        m = ROW.match(line)
        if not m:
            skipped.append((i + 1, line, "unparsed"))
            continue
        size = len((m.group("hook") or "").encode())
        if size <= args.cap:
            continue
        target, hook = m.group("target"), (m.group("hook") or "")
        tf = MEM / target
        if not tf.is_file():
            skipped.append((i + 1, line, f"no topic file ({target}) — cannot move detail, so NOT trimmed"))
            continue
        prefix = f"- [{m.group('title')}]({target}) — "
        # Cap the HOOK, not the row. 43 rows have a title+filename floor of
        # 104-119 bytes on their own, so a row-level cap of 120 skipped exactly
        # the rows whose hooks were longest -- it protected the wrong ones. The
        # floor is not compressible without renaming topic files, which would
        # break every [[name]] backlink, so it is treated as fixed.
        new_hook = short_hook(hook, args.cap)
        new_line = prefix + new_hook
        lost = set(DISTINCTIVE.findall(hook)) - set(DISTINCTIVE.findall(new_hook))
        if lost:
            flagged.append((i + 1, sorted(lost)[:6]))
        plan.append((i, line, new_line, tf, hook))

    freed = sum(len(o.encode()) - len(n.encode()) for _, o, n, _, _ in plan)
    print(f"index      : {before_bytes:,} bytes, {len([l for l in lines if l.strip()])} rows")
    print(f"over cap   : {len(plan)} rows to compact (cap {args.cap}B)")
    print(f"would free : {freed:,} bytes  ->  {before_bytes - freed:,} (target {BYTE_TARGET:,})")
    print(f"skipped    : {len(skipped)}")
    for ln, _l, why in skipped:
        print(f"    L{ln}: {why}")
    print(f"flagged    : {len(flagged)} rows whose short hook drops a distinctive token")

    if not args.apply:
        print("\n--- proposals (flagged rows marked !) ---")
        flagged_lines = {ln for ln, _ in flagged}
        for i, old, new, _tf, _h in plan:
            mark = "!" if (i + 1) in flagged_lines else " "
            print(f"{mark} L{i+1:3d} {len(old.encode()):4d}->{len(new.encode()):3d}  {new[:118]}")
        print("\nPLAN ONLY -- nothing written. Pass --apply.")
        return 0

    stamp = date.today().isoformat()
    moved = 0
    for _i, _old, _new, tf, hook in plan:
        body = tf.read_text(encoding="utf-8")
        block = f"\n\n## Index hook (archived {stamp})\n\n{hook}\n"
        if hook.strip() and hook.strip() not in body:
            tf.write_text(body.rstrip("\n") + block, encoding="utf-8")
            moved += 1

    for i, _old, new, _tf, _h in plan:
        lines[i] = new

    out = "\n".join(lines)
    if not out.endswith("\n"):
        out += "\n"
    after = len(out.encode())
    if after > 25_000:
        print(f"REFUSING: result {after} still over the 25,000 cap")
        return 1
    INDEX.write_text(out, encoding="utf-8")
    print(f"\nWROTE index: {before_bytes:,} -> {after:,} bytes ({before_bytes-after:,} freed)")
    print(f"moved {moved} hooks into topic files (archived {stamp})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
