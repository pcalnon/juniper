#!/usr/bin/env python3
"""
Repair the four extraction artifacts listed in the cross-view measurement note's §3.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-29
Status: ad-hoc -- one-shot corpus repair (requirements cross-view arc)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-26_JUNIPER-ECOSYSTEM_REQUIREMENTS-CROSS-VIEW-MEASUREMENT.md §3
         (where the four are enumerated); ml#1462 (which made by-repo/by-status derived, so this
         only has to touch by-area and the ledger, and the projection carries it)

Why a script rather than four hand edits
---------------------------------------
Each repair is an exact-string replacement inside a 1,814-entry corpus of record, and a silent
miss would leave the note claiming a repair that did not happen. Every replacement below asserts
its target is present exactly once and aborts the whole run otherwise -- nothing is written
unless all of them match.

What is repaired, and what is deliberately NOT
---------------------------------------------
Three of the four briefs are extraction artifacts rather than requirement statements: a bare code
fence, a bare filename, and a truncated blockquote fragment. Each is rewritten from the entry's
OWN cited source range -- read, not invented -- and the previous text is preserved in Notes,
following the corpus's existing ``[... brief repaired ...; was: '...']`` idiom.

Two structural artifacts are also repaired:

  * ``JR-ML-DATA-041`` carries a stray ``---`` at the end of its body. It is the ONLY entry in
    1,814 that does, it is not the last entry in its file, and no by-area file ends with a rule,
    so it is a horizontal rule sitting between two entries rather than any convention.
  * ``JR-ML-ARCH-014``'s Detail is ``# 1. wait_for_health() ...`` -- a comment lifted out of a
    ```bash fence, which outside that fence renders as an **H1 inside an H3 entry**. It is
    wrapped in backticks rather than having the ``#`` deleted, which keeps the source text exact
    while removing the spurious heading. (This is the same class that made the docs screen fail
    in ml#1461; there the fix was the projection dropping the ``#``, because that entry's Detail
    reads correctly as prose without it. Here deleting it would turn the line into an ordered
    list item, so the treatments differ because the content does.)

NOT repaired: Detail *selection*. ``JR-ML-OBS-003``'s Detail quotes the first-pass revision line
that its own source then supersedes. Choosing better Detail is re-extraction -- a different job
with a different evidence bar -- and this script only fixes what §3 enumerated.

Usage
-----
    python3 util/ad-hoc/2026-08-29_requirements_artifact_repair.py [--apply]

Exit 0 = applied (or dry run), 2 = a target string did not match exactly once (nothing written).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REQ = REPO_ROOT / "notes" / "requirements"
NOTE = "[2026-08-29 brief repaired from cited content; was: {old!r}]"

#: (area file, id, old brief, new brief). New briefs are derived from each entry's cited range.
BRIEFS = [
    (
        "ARCH.md",
        "JR-ML-ARCH-014",
        "```bash ```.",
        "Improved `juniper_plant_all.bash` / `juniper_chop_all.bash`: health polling, port and conda-env validation, /proc-based PID checks, graceful SIGTERM→SIGKILL",
    ),
    (
        "DATA.md",
        "JR-ML-DATA-010",
        '"""cascade_add WebSocket message must trigger topology broadcast."""',
        "Phase 3 integration test: a `cascade_add` WebSocket message must trigger a topology broadcast",
    ),
    (
        "DATA.md",
        "JR-ML-DATA-041",
        "`juniper_cascor_client/client.py`",
        "juniper-cascor-client (Phase 4): add `get_dataset_data()` to `juniper_cascor_client/client.py`",
    ),
    (
        "OBS.md",
        "JR-ML-OBS-003",
        ">   per the canopy requirements (high-volume / low-latency metrics and the.",
        "P5-RC-05 (frontend WebSocket consumption) is STILL OPEN, not deferred — high-volume / low-latency metrics and the bidirectional `set_params` control channel depend on it",
    ),
    # NOT one of §3's four. Found by scanning the whole corpus for `^# ` after the four were
    # repaired: exactly one other entry carried the same defects, and leaving the corpus half
    # cleaned of a class I had just cleaned elsewhere would be worse than not starting.
    (
        "TRAIN.md",
        "JR-ML-TRAIN-054",
        '"""Demo backend must produce hidden-to-hidden cascade connections.""".',
        "Phase 2 test: the demo backend must produce hidden-to-hidden cascade connections",
    ),
]

#: (area file, exact old text, exact new text, why). Structural repairs, not briefs.
STRUCTURAL = [
    (
        "ARCH.md",
        "# 1. wait_for_health() function that polls /v1/health with configurable timeout",
        "`# 1. wait_for_health() function that polls /v1/health with configurable timeout`",
        "a ```bash comment outside its fence renders as an H1 inside an H3 entry",
    ),
    (
        "DATA.md",
        "[v4 brief repaired; was: '9.3 juniper-cascor-client (Phase 4 only)']\n\n---\n",
        "[v4 brief repaired; was: '9.3 juniper-cascor-client (Phase 4 only)']\n",
        "a stray horizontal rule between two entries -- the only one in 1,814",
    ),
    (
        "TRAIN.md",
        "# Setup: create network with 2+ hidden units",
        "`# Setup: create network with 2+ hidden units`",
        "a ```python comment outside its fence renders as an H1 inside an H3 entry",
    ),
]


def _replace_once(text: str, old: str, new: str, what: str, errors: "list[str]") -> str:
    """Replace ``old`` exactly once. Idempotent: a repair already applied is skipped.

    Failing loudly on an unmatched target is the point -- a silent miss would leave the
    measurement note claiming a repair that never happened -- but "already applied" is not a
    miss, and treating it as one would make the script un-rerunnable and so useless as the
    provenance record of what was done.

    Checking "already applied" naively is WRONG when ``old`` is a SUBSTRING of ``new`` -- which
    is exactly the shape of wrapping a line in backticks. A first version tested
    ``text.count(old) == 1`` first, matched the old text *inside* the already-backticked line on a
    re-run, and double-wrapped it. So applied sites are masked out before anything is counted.
    """
    masked = text.replace(new, "\x00")
    if "\x00" in masked and old not in masked:
        return text  # already applied
    count = masked.count(old)
    if count != 1:
        errors.append(f"{what}: expected exactly 1 occurrence of the target, found {count}")
        return text
    return masked.replace(old, new, 1).replace("\x00", new)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the repairs (default is a dry run)")
    args = parser.parse_args(argv)

    errors: "list[str]" = []
    pending: "dict[Path, str]" = {}

    def _text(name: str) -> str:
        path = REQ / "by-area" / name
        if path not in pending:
            pending[path] = path.read_text(encoding="utf-8")
        return pending[path]

    for name, req_id, old, new in BRIEFS:
        path = REQ / "by-area" / name
        text = _text(name)
        text = _replace_once(text, f"### {req_id} — {old}\n", f"### {req_id} — {new}\n", f"{name}:{req_id} heading", errors)
        # The provenance note goes at the END of the entry's Notes, i.e. immediately before the
        # next entry's heading (or EOF), so every existing note and the merged-provenance line
        # are preserved in place.
        marker = f"### {req_id} — {new}\n"
        if marker in text:
            start = text.index(marker)
            nxt = text.find("\n### JR-", start + len(marker))
            end = len(text) if nxt == -1 else nxt
            block = text[start:end]
            note = NOTE.format(old=old)
            if "**Notes**:" not in block:
                errors.append(f"{name}:{req_id}: no Notes section to record the repair in")
            elif note not in block:  # idempotent: do not stack the provenance note on a re-run
                text = text[:start] + block.rstrip("\n") + "\n\n" + note + "\n" + text[end:]
        pending[path] = text

    for name, old, new, _why in STRUCTURAL:
        path = REQ / "by-area" / name
        pending[path] = _replace_once(_text(name), old, new, f"{name}: structural", errors)

    if errors:
        for line in errors:
            print(f"ERROR: {line}", file=sys.stderr)
        print("nothing written -- every target must match exactly once", file=sys.stderr)
        return 2

    for path, text in pending.items():
        changed = text != path.read_text(encoding="utf-8")
        print(f"  {'wrote' if args.apply else 'would write'} by-area/{path.name}" if changed else f"  unchanged by-area/{path.name}")
        if args.apply and changed:
            path.write_text(text, encoding="utf-8")

    # The ledger's brief is a truncated summary and is never read for content (AGENTS.md), but
    # leaving four rows describing text that no longer exists is gratuitous staleness.
    ledger = REQ / "id_assignments.yaml"
    lt = ledger.read_text(encoding="utf-8")

    def _yaml_single(value: str) -> str:
        """YAML single-quoted scalar. Targeted string surgery, NOT a re-dump: safe_dump would
        re-quote and re-wrap all 1,814 rows and bury the four-row change (write_all's docstring)."""
        return "'" + value.replace("'", "''") + "'"

    ledger_missed: "list[str]" = []
    for _name, req_id, old, new in BRIEFS:
        # Ledger briefs are the view brief minus the trailing period the views carried, and are
        # emitted single-quoted when they contain YAML-significant characters.
        for candidate in (_yaml_single(old), _yaml_single(old.rstrip(".")), old, old.rstrip(".")):
            line = f"  brief: {candidate}\n"
            if lt.count(line) == 1:
                lt = lt.replace(line, f"  brief: {_yaml_single(new)}\n")
                break
        else:
            ledger_missed.append(req_id)
    for req_id in ledger_missed:
        print(f"  NOTE: ledger brief for {req_id} not matched -- left as-is (the views are authoritative)")
    if lt != ledger.read_text(encoding="utf-8"):
        print(f"  {'wrote' if args.apply else 'would write'} id_assignments.yaml ({len(BRIEFS) - len(ledger_missed)} brief(s))")
        if args.apply:
            ledger.write_text(lt, encoding="utf-8")

    if not args.apply:
        print("dry run -- nothing written (pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
