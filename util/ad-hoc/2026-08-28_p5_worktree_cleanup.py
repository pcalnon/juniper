#!/usr/bin/env python3
"""Remove finished P5 arc worktrees, with the gates that make removal safe.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc tooling (P5 arc cleanup)
Author:      Paul Calnon
License:     MIT License

Gates, ALL of which must pass per worktree before anything is removed:

1. **The PR is MERGED** on GitHub -- read live, not assumed from a table.
2. **The worktree is not live** -- no process has its cwd inside it (the liveness probe's
   predicate; `pgrep -f` is not enough, it matches its own wrapper).
3. **Clean tree** -- `git status --porcelain` empty.
4. **Nothing unrecoverable is ignored.** `git status --porcelain` is BLIND to ignored files
   and `worktree remove` deletes them: 551 `.h5` snapshots once hid in "clean" cascor
   worktrees. Every ignored entry must match a known-disposable pattern (caches, build
   artifacts) or this refuses.

Then, in order: remove the worktree, prune, delete the local branch, and finally
fast-forward the primary if it is on `main` and clean.

The primary pull is not cosmetic. The plan's standing hazard: a trimmed worktree sitting
over an UNTRIMMED ancestor loads BOTH copies, so context goes UP. For a cut, the primary
must reach the trimmed `main` -- removing the worktree without pulling leaves the ancestor
stale for every other worktree in that repo.

Usage:
    python3 util/ad-hoc/2026-08-28_p5_worktree_cleanup.py --pattern '*--feat--memory-budget-blocking--*' [--execute]
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import os
import subprocess  # nosec B404 -- fixed-argv git/gh calls; nothing is shell-interpolated
import sys
from pathlib import Path

JUNIPER = Path("/home/pcalnon/Development/python/Juniper")
WORKTREES = JUNIPER / "worktrees"

# An ignored entry matching one of these is disposable: regenerated on demand, never authored.
# Anything else stops the removal and asks for a human look.
DISPOSABLE = [
    "*__pycache__/", "*.pyc", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/",
    "*.egg-info/", ".coverage", "htmlcov/", "build/", "dist/", ".tox/",
    "node_modules/", ".venv/", "venv/", ".DS_Store", "*.log", ".hypothesis/",
]


def run(argv, cwd=None, check=False):
    return subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=check)  # nosec B603


def occupied(wt: Path) -> list[str]:
    """PIDs whose cwd is inside this worktree. Gate on /proc/<pid>/cwd, never argv."""
    held = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cwd = os.readlink(entry / "cwd")
        except OSError:  # includes PermissionError
            continue
        if cwd == str(wt) or cwd.startswith(str(wt) + "/"):
            held.append(entry.name)
    return held


def ignored_entries(wt: Path) -> list[str]:
    out = run(["git", "-C", str(wt), "status", "--porcelain", "--ignored"]).stdout
    return [ln[3:] for ln in out.splitlines() if ln.startswith("!!")]


def describe(wt: Path, rel: str) -> str:
    """`name (N files, SIZE, newest mtime)` for one ignored entry.

    Deliberately NOT used to decide anything -- these entries stay BLOCKING. It exists because
    "is this run log evidence?" is answered by size and recency, not by filename: a 0-byte
    `custom.log` from three weeks ago and a 424 KB `system.log` written twenty minutes ago are the
    same pattern and completely different decisions. Printing both lets the human answer at a
    glance instead of running `ls` per worktree.

    Suggested by the session that owns the canopy worktrees, after this gate's refusal surfaced a
    real evidence loss: the finding it protected was in a live leg's log, and the distinguishing
    fact was not the path but whether a live leg had ever run from that tree -- something no
    pattern can see. Hence: keep the friction, reduce the noise.
    """
    p = wt / rel
    total = files = 0
    newest = 0.0
    if p.is_dir():
        for root, _dirs, names in os.walk(p):
            for n in names:
                try:
                    st = os.stat(os.path.join(root, n))
                except OSError:
                    continue
                total += st.st_size
                files += 1
                newest = max(newest, st.st_mtime)
    elif p.is_file():
        try:
            st = p.stat()
            total, files, newest = st.st_size, 1, st.st_mtime
        except OSError:
            pass
    when = dt.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M") if newest else "?"
    size = f"{total / 1e6:.1f} MB" if total >= 1e6 else f"{total / 1e3:.1f} KB" if total else "empty"
    return f"{rel} ({files} file{'s' if files != 1 else ''}, {size}, newest {when})"


def undisposable(entries: list[str]) -> list[str]:
    return [e for e in entries if not any(fnmatch.fnmatch(e, p) or fnmatch.fnmatch(e.rstrip("/") + "/", p) for p in DISPOSABLE)]


def pr_state(repo: str, branch: str) -> tuple[str, str]:
    """(summary, error) for the PR on `branch`. An API failure is NEVER reported as "no PR".

    A first version returned "NONE ? ?" whenever stdout was empty, which conflates *the branch has
    no PR* with *the call failed*. Observed immediately: one repo printed `pr=NONE` while
    `gh pr view` showed an open PR on that exact head -- a transient empty reply. It happens to
    fail safe (a missing PR blocks removal), but the printed REASON is then false, and a false
    reason is what someone overrides. Retry, then say plainly which of the two it was.
    """
    last = ""
    for _ in range(3):
        p = run(["gh", "pr", "list", "--repo", f"pcalnon/{repo}", "--head", branch,
                 "--state", "all", "--json", "number,state,mergedAt", "--jq",
                 '.[0] | "\\(.number) \\(.state) \\(.mergedAt)"'])
        txt = p.stdout.strip()
        if p.returncode == 0:
            # `.[0] | "\(.number) ..."` over an EMPTY array yields the literal "null null null",
            # not an empty string -- so a branch with no PR printed `pr=null null null`, which reads
            # like a value rather than an absence. Same fail-into-plausible shape as the lookup
            # failure below; name it instead.
            if not txt or txt.startswith("null"):
                return "NO-PR-ON-HEAD", ""
            return txt, ""
        last = (p.stderr or p.stdout).strip()
    return "LOOKUP-FAILED", last[:200]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pattern", required=True, help="glob over worktree directory names")
    ap.add_argument("--execute", action="store_true", help="actually remove (default: report only)")
    ns = ap.parse_args(argv)

    wts = sorted(WORKTREES.glob(ns.pattern))
    if not wts:
        print(f"no worktrees match {ns.pattern!r}")
        return 0
    print(f"{len(wts)} worktree(s) match {ns.pattern!r}   [{'EXECUTE' if ns.execute else 'REPORT ONLY'}]\n")

    removable, blocked = [], []
    for wt in wts:
        name = wt.name
        repo = name.split("--")[0]
        branch = run(["git", "-C", str(wt), "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        reasons = []
        info, err = pr_state(repo, branch)
        parts = info.split()
        if info == "LOOKUP-FAILED":
            reasons.append(f"PR LOOKUP FAILED (not the same as 'no PR') -- {err}")
        elif len(parts) < 2 or parts[1] != "MERGED":
            reasons.append(f"PR not MERGED ({info})")
        held = occupied(wt)
        if held:
            reasons.append(f"OCCUPIED by pid(s) {','.join(held)}")
        dirty = run(["git", "-C", str(wt), "status", "--porcelain"]).stdout.strip()
        if dirty:
            reasons.append(f"dirty ({len(dirty.splitlines())} entries)")
        keep = undisposable(ignored_entries(wt))
        if keep:
            detail = "; ".join(describe(wt, k) for k in keep[:5])
            more = f" (+{len(keep) - 5} more)" if len(keep) > 5 else ""
            reasons.append(f"UNRECOGNISED ignored payload -- a human must look: {detail}{more}")
        mark = "REMOVE " if not reasons else "BLOCKED"
        print(f"  {mark} {name}\n          repo={repo} branch={branch} pr={info}")
        if reasons:
            for r in reasons:
                print(f"          !! {r}")
            blocked.append((wt, reasons))
        else:
            removable.append((wt, repo, branch))

    print(f"\n{len(removable)} removable, {len(blocked)} blocked")
    if not ns.execute:
        print("\nreport only — pass --execute to remove")
        return 0

    for wt, repo, branch in removable:
        primary = JUNIPER / repo
        print(f"\n== {wt.name}")
        r = run(["git", "-C", str(primary), "worktree", "remove", str(wt)])
        if r.returncode != 0:
            print(f"   !! remove failed: {r.stderr.strip()[:200]}")
            continue
        print("   worktree removed")
        run(["git", "-C", str(primary), "worktree", "prune"])
        d = run(["git", "-C", str(primary), "branch", "-D", branch])
        print(f"   branch {branch}: {d.stdout.strip() or d.stderr.strip()}")
        # Fast-forward the primary -- the ancestor-staleness hazard, not cosmetic.
        cur = run(["git", "-C", str(primary), "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        pdirty = run(["git", "-C", str(primary), "status", "--porcelain"]).stdout.strip()
        if cur != "main":
            print(f"   primary is on {cur!r}, not main — NOT pulling (owner's call)")
        elif pdirty:
            print(f"   primary tree is dirty ({len(pdirty.splitlines())} entries) — NOT pulling (F-6 stale-checkout guard)")
        else:
            run(["git", "-C", str(primary), "fetch", "origin", "--quiet"])
            ff = run(["git", "-C", str(primary), "merge", "--ff-only", "origin/main"])
            sha = run(["git", "-C", str(primary), "rev-parse", "--short=8", "HEAD"]).stdout.strip()
            print(f"   primary {'fast-forwarded' if ff.returncode == 0 else 'FF FAILED: ' + ff.stderr.strip()[:120]} -> {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
