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
   artifacts) or this refuses. Size and newest-mtime are printed per entry so a human can
   tell a 0-byte three-week-old `custom.log` from a 424 KB one written 20 minutes ago.

   **`--harvest DIR` is the way through**, and it exists because refusing with no escape
   pushes people to remove by hand, which is where the loss actually happens. **The sweep is
   where evidence dies**: 2026-08-29, seven canopy worktrees each held their own ignored
   `logs/system.log`, and one was the ONLY surviving copy of a log whose `/tmp` original had
   been truncated by a `nohup >` redirect — invisible to three measurement agents, two
   adversarial agents and a reconciler, all of whom searched tracked files, `/tmp` and git
   objects. Harvest copies the payload out, then allows removal; it does NOT bypass gates
   1-3.

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
import shutil
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
            # Non-fatal: if the file cannot be stat'ed (e.g., race/permission), keep
            # placeholder metadata so this descriptive helper still returns safely.
            total, files, newest = 0, 0, 0.0
    when = dt.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M") if newest else "?"
    size = f"{total / 1e6:.1f} MB" if total >= 1e6 else f"{total / 1e3:.1f} KB" if total else "empty"
    return f"{rel} ({files} file{'s' if files != 1 else ''}, {size}, newest {when})"


def harvest(wt: Path, entries: list[str], dest_root: Path) -> list[str]:
    """Copy non-disposable ignored payload out of a worktree before it is removed.

    **The sweep is where evidence dies.** `git status --porcelain` does not list ignored files and
    `git worktree remove` deletes them, so an ignored `logs/` directory is invisible to every search
    that looks at tracked files, `/tmp` and git objects — and one command from gone.

    Not hypothetical. 2026-08-29, juniper-canopy: seven arc worktrees each carried their own
    `logs/system.log` (203-434 KB, 2.3 MB total). One of them recorded seven server starts with
    request bursts at exactly two census session times, and it was the ONLY surviving copy — the
    `/tmp` original had been truncated by a `nohup >` redirect. Three measurement agents, two
    adversarial agents and a reconciler had all hunted for that evidence and missed it. It did not
    rescue the finding, but it qualified a published "no artifact establishes it" that was too
    strong.

    So: refusing is right, but refusing with no way through pushes people to remove by hand, which
    is where the loss happens. This makes the safe path the easy one — harvest, then remove.
    """
    saved = []
    for rel in entries:
        src = wt / rel
        if not src.exists():
            continue
        dst = dest_root / wt.name / rel.rstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        saved.append(rel)
    return saved


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
    ap.add_argument("--harvest", metavar="DIR", type=Path, default=None,
                    help="copy non-disposable ignored payload to DIR/<worktree>/ and then ALLOW removal; "
                         "without it such payload blocks removal outright")
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
        if keep and ns.harvest:
            print(f"  HARVEST {name}")
            for k in keep:
                print(f"          {describe(wt, k)}")
            if ns.execute:
                saved = harvest(wt, keep, ns.harvest.resolve())
                print(f"          -> saved {len(saved)} to {ns.harvest.resolve() / name}")
            keep = []
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
