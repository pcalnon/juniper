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
    2026-09-05_fleet_harvest_postmerge_verify.py <repo-dir> [--ref=REF] <pr> [<pr> ...]

The tree examined is REF (default origin/main), fetched first -- never the working
tree, which is routinely behind it.
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


def _safe_read(path: Path) -> str:
    """Read a file, or return "" for anything unreadable (dangling symlink, permissions)."""
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def _show(repo: Path, ref: str, path: str) -> str | None:
    """File content at ``ref``, or None when the path is absent there.

    Read the REF, never the working tree. A shared checkout is routinely behind the
    branch that was just merged -- juniper-canopy's was, and reading it made this script
    report 207 of 238 lines "absent" from a file that had merged perfectly. That is the
    worst possible failure for a tool whose whole job is to authorise closing the source
    PR: it argues for re-doing work that is already done.
    """
    out = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"],
        capture_output=True, text=True, check=False,
    )
    return out.stdout if out.returncode == 0 else None

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
    args = sys.argv[2:]
    ref = "origin/main"
    if args and args[0].startswith("--ref="):
        ref = args.pop(0).split("=", 1)[1]
    prs = args
    subprocess.run(["git", "-C", str(repo), "fetch", "origin", "--quiet"], check=False)

    problems = 0
    for pr in prs:
        meta = json.loads(gh(repo, "pr", "view", pr, "--json", "state,title"))
        diff = gh(repo, "pr", "diff", pr)
        per_file = added_lines(diff)

        missing_total = 0
        detail: list[str] = []
        for path, lines in per_file.items():
            at_ref = _show(repo, ref, path)
            if at_ref is None:
                # The carrier may have renamed or folded the file; search the tree.
                # `rglob` yields DANGLING SYMLINKS -- juniper-canopy's notes/ carries
                # several cross-repo links to juniper-ml files that were renamed under
                # the 2026-07-04 notes convention. `read_text` on one raises
                # FileNotFoundError and kills the whole verification, so a repo with one
                # stale link could never be checked. Skip what cannot be read; a file
                # that is not there cannot be hiding the content we are looking for.
                haystack = "\n".join(
                    _safe_read(p)
                    for p in repo.rglob("*.md")
                    if ".git" not in p.parts and p.is_file()
                )
            else:
                haystack = at_ref
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
