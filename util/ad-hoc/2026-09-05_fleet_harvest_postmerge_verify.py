#!/usr/bin/env python3
"""Post-merge check: is every line a SUPERSEDED PR added actually present on main?

Project: Juniper
Sub-Project: juniper-ml
Application: ad-hoc fleet-flood-2 tooling
Author: Paul Calnon
Version: 0.1.0
License: MIT

The consolidation carriers (juniper-ml#1746, juniper-canopy#583) were verified in
BOTH directions before merge.  This verifies the same property AFTER the merge,
against the tree that actually exists on `main` -- because the squash of a
rebased carrier is not the same object that was verified.

The unit is the added line, stripped.  That is deliberately the WEAK check: per
`reference_check_unit_must_match_identity`, a line-presence verifier cannot see a
lost fence or a lost table separator.  Run `2026-09-05_markdown_structure_check.py`
over the same tree for the structural half.  Neither one substitutes for the other.

Usage:
    2026-09-05_fleet_harvest_postmerge_verify.py <repo-dir> <pr> [<pr> ...]
"""

import json
import subprocess
import sys
from pathlib import Path


def gh(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["gh", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    if out.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


def added_lines(diff: str) -> dict[str, list[str]]:
    """Map path -> added lines, from a unified diff."""
    per_file: dict[str, list[str]] = {}
    path = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            per_file.setdefault(path, [])
        elif line.startswith("+++ ") or line.startswith("--- "):
            continue
        elif line.startswith("+") and path is not None:
            body = line[1:].strip()
            if body:
                per_file[path].append(body)
    return per_file


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    repo = Path(sys.argv[1]).resolve()
    prs = sys.argv[2:]

    problems = 0
    for pr in prs:
        meta = json.loads(gh(repo, "pr", "view", pr, "--json", "state,title"))
        diff = gh(repo, "pr", "diff", pr)
        per_file = added_lines(diff)

        missing_total = 0
        detail: list[str] = []
        for path, lines in per_file.items():
            target = repo / path
            if not target.exists():
                # The carrier may have renamed or folded the file; search the tree.
                haystack = "\n".join(
                    p.read_text(errors="replace")
                    for p in repo.rglob("*.md")
                    if ".git" not in p.parts
                )
            else:
                haystack = target.read_text(errors="replace")
            present = {ln.strip() for ln in haystack.splitlines()}
            missing = [ln for ln in lines if ln not in present]
            if missing:
                missing_total += len(missing)
                detail.append(f"    {path}: {len(missing)}/{len(lines)} lines absent")
                for ln in missing[:50]:
                    detail.append(f"      - {ln[:110]}")

        flag = "OK " if missing_total == 0 else "MISS"
        print(f"[{flag}] #{pr} {meta['state']:<7} {meta['title'][:66]}")
        print(f"       {len(per_file)} files, {sum(len(v) for v in per_file.values())} added lines, {missing_total} absent from the tree")
        for line in detail:
            print(line)
        problems += missing_total

    print(f"\ntotal absent lines: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
