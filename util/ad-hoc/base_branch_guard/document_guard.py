#!/usr/bin/env python3
"""Document the base-branch guard in each repo's AGENTS.md (ml#434, audit F-9).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc migration tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-21
Status:      ad-hoc -- migration (one-off)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the guard is documented on all 9 repos.
Related:     ml#434; notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_PR-BASE-BRANCH-GUARD-AUDIT.md F-9

The gap
-------
`Guard PR base branch` is a MERGE-BLOCKING required context on all 9 repos, and `stacked-pr`
is its escape hatch. Grepping each default branch for either string: juniper-recurrence has
1 mention, the other 8 have **zero**. A required context nobody wrote down is one the next
person debugs from scratch at the worst moment.

Two traps this script is built around
-------------------------------------
1. **`open_signed_pr.py` uploads WHOLE FILES.** `expectedHeadOid` guards against a concurrent
   push at push time, but a local copy read from an older `main` silently reverts anything
   that landed in between. So each AGENTS.md is fetched from `main` IMMEDIATELY before its
   upload, never from a local checkout (the sibling checkouts on this host are stale).

2. **`agents-md-touch-up.yml` VERIFIES the `**Last Updated**` field** -- it must be a
   well-formed past-or-today date AND either already equal today's UTC date or changed in
   this PR. It no longer bumps the date itself (a runner commit is unsigned, which
   `required_signatures` rejects). So this script bumps it in the same signed commit, which
   is what makes the PR satisfy the check as authored.

Usage
-----
    python3 util/ad-hoc/base_branch_guard/document_guard.py --dry-run
    python3 util/ad-hoc/base_branch_guard/document_guard.py
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

TARGETS = [
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
]

BLOCK = """
### PR base-branch guard (required check)

`.github/workflows/pr-base-branch-guard.yml` fails any PR whose base branch is not the
default branch. Its job name -- **`Guard PR base branch`** -- is a **required status check**
in this repo's ruleset, so renaming the job or deleting the file makes `main` unmergeable
until the context is un-required first.

**What it protects against.** A PR based on another feature branch can squash-merge into
that branch, stranding its content off `main` behind a green **MERGED** badge. It has
happened three times in this ecosystem (`juniper-recurrence#7`/`#8`, `juniper-canopy#365`).

**Why it matters more than it looks.** Both rulesets here are scoped to `~DEFAULT_BRANCH`, so
a PR whose base is a feature branch is governed by **no ruleset at all** -- it has zero
required status checks and merges clean with nothing having run:

```bash
gh api repos/pcalnon/<repo>/rules/branches/feature%2Fanything --jq length   # -> 0
gh api repos/pcalnon/<repo>/rules/branches/main               --jq length   # -> 9
```

This workflow carries no `branches:` filter, so it is the **only** check that runs on such a
PR. It cannot block the merge there -- no ruleset applies -- but it turns a silent merge into
a visibly red one.

**If it fails.** Re-open the work against the default branch. The house practice is
**close and re-open** a fresh PR titled `[retarget #NNN]`. Retargeting in place is *not*
sufficient on its own: every `ci*.yml` here uses the default `pull_request` types
`[opened, synchronize, reopened]`, which exclude `edited`, so a retarget re-runs this guard
and nothing else -- the PR stays blocked on its other required contexts until a push or a
close/re-open.

**`stacked-pr` label.** Silences this guard for a deliberate stack. It does **not** make the
PR mergeable into `main`, and it does **not** re-land the stack -- do that separately.

Rollout and rationale: [juniper-ml#434](https://github.com/pcalnon/juniper-ml/issues/434).
"""


def gh(args, inp=None):
    return subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, input=inp, timeout=180
    )


def fetch_agents(repo: str):
    p = gh(["api", f"repos/pcalnon/{repo}/contents/AGENTS.md", "--jq", ".content"])
    if p.returncode != 0:
        return None
    try:
        return base64.b64decode(p.stdout).decode("utf-8")
    except Exception:
        return None


def transform(text: str, today: str):
    """Insert the block and bump Last Updated. Returns (new_text, note) or (None, reason)."""
    if "Guard PR base branch" in text:
        return None, "already documented"

    # Insert at the END of the most CI-ish section -- immediately before the next top-level
    # heading after it. Anchored to headings, not line numbers, because these nine files
    # have genuinely different structures: juniper-canopy has no CI section at all, and
    # juniper-recurrence calls its one "Sequence-safety nets (advisory CI)". A single
    # `CI/CD` regex silently skipped both.
    anchor = None
    for pattern in (r"^## .*CI/CD.*$", r"^## .*\bCI\b.*$", r"^## .*Testing.*$"):
        anchor = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if anchor:
            break
    if anchor:
        nxt = re.search(r"^## ", text[anchor.end():], re.MULTILINE)
        insert_at = anchor.end() + nxt.start() if nxt else len(text)
        where = "after " + text[anchor.start():anchor.end()].strip()[:40]
    else:
        # Appending is the honest fallback: better a documented guard in an odd place than
        # a silent skip that leaves the repo undocumented.
        insert_at = len(text)
        where = "appended (no CI/Testing section)"
    out = text[:insert_at].rstrip("\n") + "\n" + BLOCK + "\n" + text[insert_at:]

    # `agents-md-touch-up.yml` requires this field to be today's UTC date or changed here.
    out, n = re.subn(
        r"(\*\*Last Updated\*\*:\s*)\d{4}-\d{2}-\d{2}", rf"\g<1>{today}", out, count=1
    )
    # juniper-recurrence's CI section is headed "Sequence-safety nets (advisory CI)". That
    # was true when written and is not now: `Sequence Safety` became a REQUIRED context on
    # 2026-08-18, and this change adds a second required one directly beneath it. Leaving
    # it would file two merge-blocking checks under a heading that calls them advisory --
    # precisely the kind of stale qualifier that gets believed later.
    # `[ \t]*$`, NOT `\s*$`. In Python `\s` matches `\n`, so `\s*$` under MULTILINE
    # swallowed the blank line AFTER the heading as well -- tripping markdownlint MD022
    # (headings must be surrounded by blank lines) and failing juniper-recurrence's
    # Pre-commit gate. The tell was in the diffstat (-3 deletions where -2 was expected)
    # and was rationalised rather than read.
    out, adv = re.subn(
        r"^(## Sequence-safety nets )\(advisory CI\)[ \t]*$",
        r"\g<1>(required CI)",
        out,
        count=1,
        flags=re.MULTILINE,
    )
    extra = "; un-stale'd 'advisory CI' heading" if adv else ""

    if n == 0:
        return out, f"{where}; NO Last Updated field to bump{extra}"
    return out, f"{where}; date bumped{extra}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default="2026-08-21", help="UTC date for the header bump")
    ap.add_argument("--repo", action="append", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    repos = args.repo or TARGETS

    body = HERE / "PR_BODY_DOCS.md"
    if not body.exists() and not args.dry_run:
        print(f"FATAL: missing {body}", file=sys.stderr)
        return 2

    rc = 0
    for repo in repos:
        text = fetch_agents(repo)
        if text is None:
            print(f"{repo:<24} ERROR: could not fetch AGENTS.md")
            rc = 1
            continue
        new, note = transform(text, args.today)
        if new is None:
            print(f"{repo:<24} SKIP: {note}")
            continue
        delta = len(new.splitlines()) - len(text.splitlines())
        print(f"{repo:<24} {note}  (+{delta} lines)")
        if args.dry_run:
            continue
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "AGENTS.md"
            local.write_text(new, encoding="utf-8")
            p = subprocess.run(  # nosec B603
                [
                    sys.executable, str(OPENER), "--repo", repo,
                    "--branch", "docs/document-base-branch-guard",
                    "--add", f"{local}:AGENTS.md",
                    "--message", "docs(agents): document the PR base-branch guard (ml#434)",
                    "--title", "docs(agents): document the PR base-branch guard",
                    "--body-file", str(body),
                ],
                capture_output=True, text=True, timeout=300,
            )
            last = ((p.stdout or p.stderr or "").strip().splitlines() or [""])[-1]
            print(f"{'':<24}   -> rc={p.returncode} {last[:80]}")
            if p.returncode not in (0, 1):
                rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
