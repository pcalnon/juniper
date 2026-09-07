#!/usr/bin/env python3
"""Decision 11: migrate juniper-data's ~180 ``*_full`` test assertions.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data#369

Nearly all of these assertions were asking one question -- *what does the whole dataset
look like?* -- of an array the producer used to ship. The question survives decision 11;
its answer moves to a concatenation of the partitions, which is what
``juniper_data.tests.partitions.whole`` provides.

Three rewrites, and the ORDER is load-bearing:

1. ``arrays["<stem>_full"]`` becomes ``whole(arrays, "<stem>")`` -- shape reads, dtype
   reads, argmax over the class distribution, all of which want the same view.
2. ``expected_keys`` / key-set literals then lose ``"X_full"`` and ``"y_full"``. These
   are the contract's own key set, so they are the edit that makes "the generator emits
   the contract" mean the new contract.
3. Files that gained a ``whole(`` call get the import.

Doing (2) first turns ``arrays["X_full"]`` into ``arrays[]``: a subscript IS a bracketed
expression containing a quoted ``X_full``, which is exactly what the key-set pattern
looks for. That produced 21 SyntaxErrors on the first run. Rewriting the subscripts
first removes them from the text before the key-set pass can see them.

What this deliberately does NOT do: assert ``X_full`` is absent anywhere. Design §9.5
requires consumers to keep tolerating stored artifacts that carry it, and a test
demanding its absence would convert "not required" into a requirement pointing the other
way.

Sites the rewrite cannot decide are REPORTED rather than guessed -- a ``_full`` mention
left in a docstring or an f-string message is listed at the end for a human read.
"""

from __future__ import annotations

import pathlib
import re
import sys

WT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--drop-full-family--20260905-1330--cc15640c")
TESTS = WT / "juniper_data/tests"

IMPORT_LINE = "from juniper_data.tests.partitions import whole\n"

#: ``arrays["X_full"]``, ``result['y_reg_full']``, and an INDEXED object such as
#: ``results[0]["X_full"]`` -- the last shape matters: leaving it out let the key-set
#: pass below see a surviving subscript and empty its brackets, which is how
#: ``results[0][]`` reached the parser on the second run.
SUBSCRIPT = re.compile(r"""(?P<obj>[A-Za-z_][\w.]*(?:\[[^\[\]]*\])*)\[(?P<q>["'])(?P<stem>[A-Za-z_][\w]*?)_full(?P=q)\]""")

#: A key-set literal member, with its comma and surrounding space.
KEYSET_MEMBER = re.compile(r"""\s*,?\s*(["'])(?:X|y)_full\1""")


def _rewrite(path: pathlib.Path) -> tuple[int, int]:
    src = path.read_text()
    original = src

    # 1. Subscripts -> whole(obj, "stem"). FIRST, so the key-set pass below cannot
    #    mistake ``arrays["X_full"]`` for a key-set literal and empty the brackets.
    n_subs = 0

    def _sub(match: re.Match) -> str:
        nonlocal n_subs
        n_subs += 1
        return f'whole({match.group("obj")}, "{match.group("stem")}")'

    src = SUBSCRIPT.sub(_sub, src)

    # 2. Key-set literals: drop the two members wherever a set/list/tuple lists them.
    #    Requires at least one OTHER quoted member on the line, so a lone quoted name is
    #    never treated as a set.
    def _strip_keyset(match: re.Match) -> str:
        cleaned = KEYSET_MEMBER.sub("", match.group(0))
        # A leading comma can be left behind when the dropped member was first.
        return re.sub(r"([{\[(])\s*,\s*", r"\1", cleaned)

    src = re.sub(
        r"""[{(][^{}()\n]*?["'](?:X|y)_full["'][^{}()\n]*?[})]""",
        lambda m: _strip_keyset(m) if len(re.findall(r"""["'][\w]+["']""", m.group(0))) > 1 else m.group(0),
        src,
    )

    if src == original:
        return (0, 0)

    # 3. Import, placed after the last top-level import STATEMENT.
    #
    #    Found via the AST, not a line prefix. A prefix knows where a statement starts
    #    and not where it ends, so on a parenthesised ``from x import (\n ... \n)`` it
    #    inserts between the opening paren and the first name -- which is what skipped
    #    two files entirely on the previous run.
    if "whole(" in src and IMPORT_LINE not in src:
        import ast as _ast

        try:
            tree = _ast.parse(src)
        except SyntaxError:
            tree = None
        end = 0
        if tree is not None:
            for node in tree.body:
                if isinstance(node, (_ast.Import, _ast.ImportFrom)):
                    end = max(end, node.end_lineno or node.lineno)
        lines = src.splitlines(keepends=True)
        lines.insert(end if end else 0, IMPORT_LINE)
        src = "".join(lines)

    # Refuse to write a file the parser rejects. The first two runs of this script
    # wrote SyntaxErrors into 21 and then 1 file respectively, and each time the damage
    # was only visible when pytest tried to collect. A parse here turns "wrote a broken
    # file" into "refused to write one".
    import ast

    try:
        ast.parse(src)
    except SyntaxError as exc:
        print(f"REFUSING to write {path.name}: rewrite does not parse ({exc})", file=sys.stderr)
        return (0, 0)

    path.write_text(src)
    return (1, n_subs)


def main() -> int:
    files = sorted(TESTS.rglob("test_*.py"))
    touched = subs = 0
    for path in files:
        changed, n = _rewrite(path)
        touched += changed
        subs += n
        if changed:
            print(f"{path.relative_to(WT)}: {n} subscript(s)")

    print(f"\n{touched} file(s) rewritten, {subs} subscript(s) replaced")

    leftovers: list[str] = []
    for path in files:
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if "_full" in line and "whole(" not in line:
                leftovers.append(f"  {path.relative_to(WT)}:{i}: {line.strip()[:100]}")
    if leftovers:
        print(f"\n{len(leftovers)} `_full` mention(s) left for a human read:", file=sys.stderr)
        for entry in leftovers[:60]:
            print(entry, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
