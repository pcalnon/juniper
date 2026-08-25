#!/usr/bin/env python3
"""Exercise the base-branch guard's shell body directly, one path per case.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc migration tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-21
Status:      ad-hoc -- migration
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the guard's logic is covered by a real CI harness, or the rollout retires.
Related:     ml#434; util/ad-hoc/base_branch_guard/pr-base-branch-guard.yml

Why this exists
---------------
This workflow is a REQUIRED status check on nine repos, so a logic error in its shell body
blocks every merge fleet-wide. Its failure arm went 137+ runs without executing once, and
when it was finally driven the label hatch turned out not to work at all -- so "it reads
correctly" has already been shown to be insufficient here.

The `merge_group` case in particular cannot be exercised at all on these repos (merge queues
are unavailable on user-owned accounts), which means the ONLY way to know its arm works is to
run the shell directly. Without its early-exit, a merge_group event evaluates BASE_REF="" and
falls through to `exit 1` -- failing every queued merge.

Extracts the `run:` block from the YAML and executes it under bash with the env the real
event would supply. No network, no GitHub.

Usage
-----
    python3 util/ad-hoc/base_branch_guard/test_guard_shell.py
"""

from __future__ import annotations

import subprocess  # nosec B404 - runs the extracted workflow shell under bash by design
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
WORKFLOW = HERE / "pr-base-branch-guard.yml"

CASES = [
    # (name, env, expected_exit, expected_substring)
    (
        "merge_group -> pass (no PR, no base_ref in payload)",
        {"EVENT_NAME": "merge_group", "BASE_REF": "", "DEFAULT_BRANCH": "main",
         "HAS_BYPASS": "false"},
        0,
        "nothing to guard",
    ),
    (
        "PR base == default -> pass",
        {"EVENT_NAME": "pull_request", "BASE_REF": "main", "DEFAULT_BRANCH": "main",
         "HAS_BYPASS": "false"},
        0,
        "targets the default branch",
    ),
    (
        "PR base != default, no label -> FAIL",
        {"EVENT_NAME": "pull_request", "BASE_REF": "feature/x", "DEFAULT_BRANCH": "main",
         "HAS_BYPASS": "false"},
        1,
        "not the default branch",
    ),
    (
        "PR base != default, WITH label -> pass (warn)",
        {"EVENT_NAME": "pull_request", "BASE_REF": "feature/x", "DEFAULT_BRANCH": "main",
         "HAS_BYPASS": "true"},
        0,
        "stacked-pr",
    ),
    (
        "unresolvable default branch -> FAIL OPEN, not closed",
        {"EVENT_NAME": "pull_request", "BASE_REF": "feature/x", "DEFAULT_BRANCH": "",
         "HAS_BYPASS": "false"},
        0,
        "skipping the check",
    ),
    (
        "merge_group with an empty default branch -> still pass",
        {"EVENT_NAME": "merge_group", "BASE_REF": "", "DEFAULT_BRANCH": "",
         "HAS_BYPASS": "false"},
        0,
        "nothing to guard",
    ),
]


def extract_run() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["guard-base-branch"]["steps"]
    for st in steps:
        if "run" in st:
            return st["run"]
    raise SystemExit("no `run:` block found")


def main() -> int:
    script = extract_run()
    failures = 0
    print(f"{'case':<52} {'exit':>4} {'want':>4}  result")
    print("-" * 92)
    for name, env, want_exit, want_text in CASES:
        p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
            ["bash", "-c", script], capture_output=True, text=True, env={**env, "PATH": "/usr/bin:/bin"}
        )
        out = (p.stdout or "") + (p.stderr or "")
        ok = p.returncode == want_exit and want_text in out
        if not ok:
            failures += 1
        print(f"{name:<52} {p.returncode:>4} {want_exit:>4}  {'OK' if ok else '** MISMATCH **'}")
        if not ok:
            print(f"    wanted text: {want_text!r}")
            print("    got:")
            for line in out.strip().splitlines()[:6]:
                print(f"      {line}")

    print()
    if failures:
        print(f"FAILED: {failures} of {len(CASES)} cases")
        return 1
    print(f"All {len(CASES)} cases pass, including the merge_group arm that cannot be")
    print("exercised on these repos at all (merge queues are unavailable on user accounts).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
