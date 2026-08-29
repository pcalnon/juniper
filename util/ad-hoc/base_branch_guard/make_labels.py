#!/usr/bin/env python3
"""Create the `stacked-pr` label on every Juniper repo (ml#434 part 1).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc migration tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- migration (one-off)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the base-branch guard rollout is complete.
Related:     ml#434; util/ad-hoc/base_branch_guard/rollout.py

`pr-base-branch-guard.yml` advertises a `stacked-pr` label as its escape hatch, and an
adversarial audit found the label **does not exist in any of the 9 repos** -- including
juniper-recurrence, where the guard's context is already REQUIRED. A hatch that names a
label nobody can apply is not a hatch.

(The same audit notes `allow-symbol-loss` and `docs-rewrite` are likewise absent, referenced
by the sequence-safety screens. Out of scope here, but the same shape.)

Idempotent: an existing label is reported and left alone, never recoloured or re-described.

Usage
-----
    python3 util/ad-hoc/base_branch_guard/make_labels.py --dry-run
    python3 util/ad-hoc/base_branch_guard/make_labels.py
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - shells out to the `gh` CLI by design
import sys

NAME = "stacked-pr"
COLOR = "BFD4F2"
DESC = "Deliberate stacked PR; silences the base-branch guard (does NOT make it mergeable)"

REPOS = [
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


def gh(args: list[str], inp: str | None = None):
    return subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, input=inp, timeout=120
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rc = 0
    for repo in REPOS:
        p = gh(["api", f"repos/{args.owner}/{repo}/labels/{NAME}"])
        if p.returncode == 0:
            print(f"{repo:<24} exists")
            continue
        if args.dry_run:
            print(f"{repo:<24} [dry-run] would create {NAME!r}")
            continue
        p = gh(
            ["api", f"repos/{args.owner}/{repo}/labels", "-X", "POST", "--input", "-"],
            inp=json.dumps({"name": NAME, "color": COLOR, "description": DESC}),
        )
        if p.returncode != 0:
            print(f"{repo:<24} FAILED: {p.stderr.strip()[:120]}")
            rc = 1
        else:
            print(f"{repo:<24} created")
    return rc


if __name__ == "__main__":
    sys.exit(main())
