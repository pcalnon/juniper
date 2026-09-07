#!/usr/bin/env python3
"""
Copy named test METHODS out of a fleet PR's ref and into the tree, class-aware.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1625 / #1735 harvest; sibling `2026-09-06_superseded_method_presence.py`

`2026-09-06_superseded_method_presence.py` names exactly which methods a parked PR would
contribute. This takes them. Two rules earned the hard way:

1. CLASS-AWARE, not file-aware. Taking the PR's whole file is a SNAPSHOT: it deletes
   everything main gained since the branch point. The method goes into the class of the
   same name if the target has one, and the class is appended whole if it does not.

2. DEPENDENCY-AWARE, not just class-aware. Three separate harvests died on `NameError` for a
   module-level helper the copied class closes over -- and fixing one surfaced the next,
   because each run only reveals the FIRST missing name. So take every module-level
   definition (def / class / assignment) and every import the source has that the target
   lacks, in one pass, before any test runs.

What this does NOT do is decide whether the method SHOULD land. A parked branch can carry a
contract main has since reversed, and such a test still reads as a clean addition here. Run
the suite afterwards and classify every failure; that is the step this tool feeds.

Usage:
    2026-09-06_harvest_methods.py <ref> <path> <method> [<method> ...]
    2026-09-06_harvest_methods.py refs/superseded/pr1625 tests/test_compare_baseline.py \
        test_cpu_count_mismatch_is_refused test_end_to_end_fail_exits_1

Exit: 0 when every named method was placed; 1 when any was not found in the ref.
"""

from __future__ import annotations

import ast
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from pathlib import Path


def show(ref: str, path: str) -> str:
    proc = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True, timeout=300, check=False)
    return proc.stdout


def segment(src_lines: list[str], node: ast.AST) -> str:
    """The source text of one top-level or nested definition, decorators included."""
    start = min([node.lineno, *[d.lineno for d in getattr(node, "decorator_list", [])]]) - 1
    return "\n".join(src_lines[start : node.end_lineno])


def module_names(tree: ast.Module) -> dict[str, ast.AST]:
    """Every module-level binding, by the name it binds."""
    out: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = node
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                out[(alias.asname or alias.name).split(".")[0]] = node
    return out


def owning_class(tree: ast.Module, method: str) -> tuple[ast.ClassDef, ast.FunctionDef] | None:
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method:
                return node, child
    return None


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 3:
        print(__doc__)
        return 2
    ref, rel, wanted = args[0], args[1], args[2:]

    src = show(ref, rel)
    if not src:
        print(f"{ref}:{rel} is empty or absent", file=sys.stderr)
        return 1
    src_tree = ast.parse(src)
    src_lines = src.splitlines()

    target_path = Path(rel)
    dst = target_path.read_text(encoding="utf-8")
    dst_tree = ast.parse(dst)
    dst_lines = dst.splitlines()

    # -- 1. the module-level closure, taken WHOLE before anything else (see rule 2 above) ----
    src_mod, dst_mod = module_names(src_tree), module_names(dst_tree)
    referenced: set[str] = set()
    for method in wanted:
        found = owning_class(src_tree, method)
        if found:
            referenced |= {n.id for n in ast.walk(found[1]) if isinstance(n, ast.Name)}
            referenced |= {n.value.id for n in ast.walk(found[1]) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    missing_names = [n for n in sorted(referenced) if n in src_mod and n not in dst_mod]
    prologue = [segment(src_lines, src_mod[n]) for n in missing_names]

    # -- 2. the methods themselves, into the class of the same name when there is one --------
    insertions: dict[str, list[str]] = {}
    # By class NAME, not a list: the header is emitted once per absent class, and a class
    # contributing two methods was otherwise appended TWICE (mypy `no-redef`, and the second
    # copy silently shadowed the first).
    appended: dict[str, str] = {}
    worst = 0
    for method in wanted:
        found = owning_class(src_tree, method)
        if not found:
            print(f"[MISS] {method}: not a method of any class in {ref}:{rel}", file=sys.stderr)
            worst = 1
            continue
        cls, fn = found
        body = segment(src_lines, fn)
        target_cls = next((n for n in dst_tree.body if isinstance(n, ast.ClassDef) and n.name == cls.name), None)
        if target_cls is None:
            appended.setdefault(cls.name, f"class {cls.name}(unittest.TestCase):\n" + (f'    """{ast.get_docstring(cls)}"""\n' if ast.get_docstring(cls) else ""))
            insertions.setdefault(f"@append:{cls.name}", []).append(body)
        else:
            insertions.setdefault(cls.name, []).append(body)
        print(f"[TAKE] {cls.name}.{method}")

    # -- 3. splice, from the bottom up so earlier line numbers stay valid --------------------
    by_end: list[tuple[int, list[str]]] = []
    for cls_name, bodies in insertions.items():
        if cls_name.startswith("@append:"):
            continue
        target_cls = next(n for n in dst_tree.body if isinstance(n, ast.ClassDef) and n.name == cls_name)
        by_end.append((target_cls.end_lineno, bodies))
    for end, bodies in sorted(by_end, reverse=True):
        dst_lines[end:end] = ["", *"\n\n".join(bodies).splitlines()]

    tail: list[str] = []
    for cls_name, header in appended.items():
        tail += ["", "", *header.rstrip("\n").splitlines(), *"\n\n".join(insertions[f"@append:{cls_name}"]).splitlines()]

    head = dst_lines
    if prologue:
        anchor = max((n.end_lineno for n in dst_tree.body if isinstance(n, (ast.Import, ast.ImportFrom))), default=0)
        head = dst_lines[:anchor] + ["", *"\n\n".join(prologue).splitlines()] + dst_lines[anchor:]
        print(f"[DEPS] took module-level {', '.join(missing_names)}")

    target_path.write_text("\n".join(head + tail).rstrip("\n") + "\n", encoding="utf-8")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
