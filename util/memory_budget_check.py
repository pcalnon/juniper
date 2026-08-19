#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Memory-file size budget gate -- P2 of the shared-session-memory plan
(``notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md``).

Why this exists
---------------
``AGENTS.md`` grew ~20x in six months **while under four active CI gates** --
because every one of them enforces structure or currency and none enforces
size. 172 of 200 main-line merges grew the file; 14 shrank it, by 2,628 bytes
between them. The disease is an ungoverned write path, so a one-time cut is
undone in ~44 days. This is the ratchet that makes a cut durable, and per
correction C1 it must ship BEFORE the cut.

The three rules
---------------
1. **CEILING.** Each governed file has a character ceiling in
   ``conf/memory_budget.json``. Characters, not bytes: the shipped Claude Code
   check compares ``content.length`` (mechanism-facts section 1).

2. **NO-WORSENING** (correction C3, stated by no proposal). A file over its
   ceiling fails only if this change *also makes it bigger*. Without this, one
   over-budget file on ``main`` blocks every unrelated PR until someone fixes
   it -- which is how a gate gets disabled rather than obeyed. A PR that shrinks
   an over-ceiling file always passes.

3. **RATCHET.** ``--ratchet`` rewrites a ceiling **downward only**, never up, so
   the budget can tighten as cleanup lands and can never silently loosen.

The waiver is a LOAN, not a pass
--------------------------------
``Allow-Budget-Overrun: <path>`` in a commit message waives the failure for that
path **without moving the ceiling**, so the debt is still owed and the next
author still sees it. This is the property the house ``Allow-Symbol-Loss:``
idiom lacks. Waivers are always reported, never silent.

Vacuous-pass resistance
-----------------------
This repo has a documented class where a check's machinery breaks and it reports
SUCCESS. Guards here: a governed file that is MISSING is a hard failure (not a
silent skip); an empty governed set is a hard failure; and an unreadable budget
file is a hard failure. ``tests/test_memory_budget_check.py`` carries the
negative controls proving each can still fail.

Usage:
    python util/memory_budget_check.py [--repo-root P] [--budget F]
                                       [--trailers-file F] [--json] [--advisory]
    python util/memory_budget_check.py --ratchet          # tighten to current

Exit: 0 pass (or advisory) / 1 over budget / 2 misuse or broken machinery.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

WAIVER_RE = re.compile(r"^Allow-Budget-Overrun:\s*(?P<path>\S+)\s*$", re.MULTILINE)


class BudgetError(RuntimeError):
    """Machinery failure -- never degrade this to a pass."""


def load_budget(path: Path) -> dict:
    if not path.is_file():
        raise BudgetError(f"budget file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BudgetError(f"budget file unreadable: {path}: {exc}") from exc
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        raise BudgetError(f"budget file declares no governed files: {path}")
    return data


def measure(path: Path) -> int:
    """Characters, not bytes -- the shipped check compares content.length."""
    return len(path.read_text(encoding="utf-8"))


def base_size(repo_root: Path, rel: str, base_ref: str) -> int | None:
    """Size of `rel` at `base_ref`, or None when it cannot be resolved."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{base_ref}:{rel}"],
            capture_output=True, check=False,
        )
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return len(out.stdout.decode("utf-8", errors="replace"))


def read_waivers(trailers: str) -> set[str]:
    return {m.group("path") for m in WAIVER_RE.finditer(trailers or "")}


def evaluate(repo_root: Path, budget: dict, base_ref: str, waivers: set[str]) -> list[dict]:
    rows = []
    for rel, spec in sorted(budget["files"].items()):
        ceiling = spec.get("ceiling_chars")
        if not isinstance(ceiling, int) or ceiling <= 0:
            raise BudgetError(f"{rel}: ceiling_chars must be a positive int")

        target = repo_root / rel
        if not target.is_file():
            # A governed file that vanished is the loudest possible signal, not a skip.
            raise BudgetError(f"governed file missing: {rel}")

        now = measure(target)
        was = base_size(repo_root, rel, base_ref)
        over = now > ceiling
        grew = was is not None and now > was

        # Rule 2: over-ceiling alone is not a failure; it must also have grown.
        failing = over and (grew or was is None)
        waived = failing and rel in waivers

        rows.append({
            "path": rel, "chars": now, "ceiling": ceiling, "base_chars": was,
            "over_ceiling": over, "grew": grew,
            "status": "WAIVED" if waived else ("FAIL" if failing else "OK"),
            "headroom": ceiling - now,
            "delta": (now - was) if was is not None else None,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--budget", type=Path, default=None)
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--trailers-file", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--advisory", action="store_true", help="report, always exit 0")
    ap.add_argument("--ratchet", action="store_true",
                    help="tighten every ceiling to the current size (downward only)")
    args = ap.parse_args()

    repo_root = args.repo_root.resolve()
    budget_path = args.budget or (repo_root / "conf" / "memory_budget.json")

    try:
        budget = load_budget(budget_path)
        waivers = read_waivers(
            args.trailers_file.read_text(encoding="utf-8") if args.trailers_file else ""
        )
        rows = evaluate(repo_root, budget, args.base_ref, waivers)
    except BudgetError as exc:
        print(f"::error::memory-budget machinery failure: {exc}", file=sys.stderr)
        return 2

    if args.ratchet:
        tightened = []
        for row in rows:
            if row["chars"] < row["ceiling"]:
                budget["files"][row["path"]]["ceiling_chars"] = row["chars"]
                tightened.append((row["path"], row["ceiling"], row["chars"]))
        budget_path.write_text(json.dumps(budget, indent=2) + "\n", encoding="utf-8")
        for path, old, new in tightened:
            print(f"ratcheted {path}: {old} -> {new}")
        if not tightened:
            print("no ceiling could be tightened (ratchet never loosens)")
        return 0

    if args.json:
        print(json.dumps({"rows": rows}, indent=2))
    else:
        print("=== memory-file size budget ===")
        for r in rows:
            delta = "" if r["delta"] is None else f"  delta={r['delta']:+d}"
            print(f"  [{r['status']:>6}] {r['path']}: {r['chars']} / {r['ceiling']} chars"
                  f"  headroom={r['headroom']}{delta}")
        for r in rows:
            if r["status"] == "FAIL":
                print(f"\n::error::{r['path']} is over its {r['ceiling']}-char ceiling "
                      f"({r['chars']}) and this change grew it. Relocate content to "
                      f"docs/REFERENCE.md rather than compressing in place; the index "
                      f"row must keep an accurate open/closed status. To defer, add a "
                      f"commit trailer 'Allow-Budget-Overrun: {r['path']}' -- that is a "
                      f"LOAN: the ceiling does not move and the debt blocks the next author.")
            elif r["status"] == "WAIVED":
                print(f"\n::warning::{r['path']} over budget but WAIVED by trailer. "
                      f"Ceiling unchanged at {r['ceiling']}; debt still owed.")

    failed = any(r["status"] == "FAIL" for r in rows)
    if args.advisory and failed:
        print("\nADVISORY MODE — reporting only, not failing the build.")
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
