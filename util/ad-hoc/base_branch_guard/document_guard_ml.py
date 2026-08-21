#!/usr/bin/env python3
"""Document the base-branch guard on juniper-ml, under its memory budget (ml#434 F-9).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc migration tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-21
Status:      ad-hoc -- migration (one-off)
Retire when: the guard is documented on all 9 repos.
Related:     ml#434; util/ad-hoc/base_branch_guard/document_guard.py

Why juniper-ml needs its own path
---------------------------------
The other eight repos take the full block straight into `AGENTS.md`. juniper-ml cannot:
it has a BLOCKING `Memory Budget` gate, and the sibling script's +36 lines blew it --

    [  FAIL] AGENTS.md: 45702 / 45084 chars  headroom=-618  delta=+1982

The gate is right, and its remedy is the repo's own standing rule: *"Don't grow AGENTS.md:
relocate to docs/REFERENCE.md, leaving a pointer that keeps an accurate open/closed
status."* `Allow-Budget-Overrun:` would suppress the failure without moving the ceiling --
a LOAN that blocks the next author -- so it is not used here.

So: a short pointer in `AGENTS.md`, the full section in `docs/REFERENCE.md`. The pointer
still carries the two facts a reader must not have to click through for -- that the job
name IS the required context string, and that a stacked PR is governed by no ruleset --
because a pointer that omits the danger is not a pointer, it is a deferral.

Asserts the post-change size against the ceiling BEFORE uploading, so this cannot re-break
the gate it exists to satisfy.

Usage
-----
    python3 util/ad-hoc/base_branch_guard/document_guard_ml.py --dry-run
    python3 util/ad-hoc/base_branch_guard/document_guard_ml.py
"""

from __future__ import annotations

import argparse
import base64
import re
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
OPENER = REPO_ROOT / "util" / "open_signed_pr.py"
CEILING = 45084  # conf/memory_budget.json, enforced by util/memory_budget_check.py

POINTER = """
### PR base-branch guard (required check)

`.github/workflows/pr-base-branch-guard.yml` fails any PR whose base is not the default
branch. Its job name -- **`Guard PR base branch`** -- is a **required status check**, so
renaming the job or deleting the file makes `main` unmergeable until it is un-required.
A stacked PR is governed by **no ruleset at all** (both are `~DEFAULT_BRANCH`-scoped), so
it merges with zero checks; this guard is the only thing that runs there. Moved to
[`docs/REFERENCE.md` § PR Base-Branch Guard](docs/REFERENCE.md#pr-base-branch-guard) --
read it when working on this area.
"""


def fetch(path: str) -> str:
    p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", "api", f"repos/pcalnon/juniper-ml/contents/{path}", "--jq", ".content"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if p.returncode != 0:
        raise SystemExit(f"cannot fetch {path}: {p.stderr.strip()[:200]}")
    return base64.b64decode(p.stdout).decode("utf-8")


def insert_after(text: str, heading_re: str, block: str) -> str:
    m = re.search(heading_re, text, re.MULTILINE | re.IGNORECASE)
    if not m:
        raise SystemExit(f"anchor not found: {heading_re}")
    nxt = re.search(r"^## ", text[m.end():], re.MULTILINE)
    at = m.end() + nxt.start() if nxt else len(text)
    return text[:at].rstrip("\n") + "\n" + block + "\n" + text[at:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    body = HERE / "PR_BODY_DOCS.md"
    block_src = (HERE / "document_guard.py").read_text(encoding="utf-8")
    m = re.search(r'BLOCK = """(.*?)"""', block_src, re.S)
    if not m:
        raise SystemExit("could not extract BLOCK from document_guard.py")
    full = m.group(1).replace("### PR base-branch guard (required check)\n", "").rstrip()

    agents = fetch("AGENTS.md")
    if "Guard PR base branch" in agents:
        print("AGENTS.md already documents the guard; nothing to do")
        return 0
    new_agents = insert_after(agents, r"^## .*CI/CD.*$", POINTER)
    new_agents, n = re.subn(
        r"(\*\*Last Updated\*\*:\s*)\d{4}-\d{2}-\d{2}", r"\g<1>2026-08-21", new_agents, count=1
    )
    if n != 1:
        raise SystemExit("could not bump **Last Updated**")

    size = len(new_agents)
    print(f"AGENTS.md    {len(agents)} -> {size} chars (+{size - len(agents)})")
    print(f"             ceiling {CEILING}, headroom after = {CEILING - size}")
    if size > CEILING:
        # Refuse rather than reach for Allow-Budget-Overrun: the ceiling does not move and
        # the debt lands on whoever edits this file next.
        raise SystemExit("REFUSING: would exceed the memory budget. Shorten the pointer.")

    ref = fetch("docs/REFERENCE.md")
    if "Guard PR base branch" in ref:
        print("REFERENCE.md already documents the guard; nothing to do")
        return 0
    section = "\n## PR Base-Branch Guard\n" + full + "\n"
    new_ref = insert_after(ref, r"^## CI/CD Pipeline Reference.*$", section)
    print(f"REFERENCE.md {len(ref)} -> {len(new_ref)} chars (+{len(new_ref) - len(ref)})")

    if args.dry_run:
        print("[dry-run] nothing uploaded")
        return 0

    with tempfile.TemporaryDirectory() as td:
        a = Path(td) / "AGENTS.md"
        a.write_text(new_agents, encoding="utf-8")
        r = Path(td) / "REFERENCE.md"
        r.write_text(new_ref, encoding="utf-8")
        p = subprocess.run(  # nosec B603
            [
                sys.executable, str(OPENER), "--repo", "juniper-ml",
                "--branch", "docs/document-base-branch-guard-ml",
                "--add", f"{a}:AGENTS.md",
                "--add", f"{r}:docs/REFERENCE.md",
                "--message", "docs: document the PR base-branch guard (ml#434 F-9)",
                "--title", "docs: document the PR base-branch guard",
                "--body-file", str(body),
            ],
            capture_output=True, text=True, timeout=300,
        )
        print((p.stdout or "").strip())
        if p.stderr.strip():
            print(p.stderr.strip())
        return p.returncode if p.returncode != 1 else 1


if __name__ == "__main__":
    sys.exit(main())
