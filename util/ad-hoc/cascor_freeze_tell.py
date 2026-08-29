#!/usr/bin/env python3
"""Decide whether the juniper-cascor primary-checkout freeze is in force.

Project:     Juniper
Sub-Project: juniper-ml
Application: defect-register round-28 verification
Author:      Paul Calnon
License:     MIT License

The freeze applies whenever a LIVE process imports the cascor primary, because
the JuniperCascor1 editable finder maps every cascor package to the primary's
``src``. Editing the primary under a live importer corrupts that process.

Two corrections over the tell carried in the round-28 handoff, both of which
made it unsound in BOTH directions:

1. ``"juniper-cascor" in cwd`` is a SUBSTRING test, so it also matches
   ``juniper-cascor-client`` and ``juniper-cascor-worker`` -- two sibling repos
   that are not the primary. It also treats every centralized task worktree
   under ``Juniper/worktrees/juniper-cascor--*`` as the primary, because the
   handoff's exclusion only covered ``.claude/worktrees``. Fixed by matching an
   exact path prefix against the primary and excluding both worktree roots.

2. cwd is not sufficient: a process can import the primary from any working
   directory (verified -- ``cd /tmp && python -c "import cascade_correlation"``
   resolves into the primary's ``src`` via the editable finder). Fixed by also
   scanning cmdline, environ, open fds and mapped files.

Known limit, not removable unprivileged: ``/proc/<pid>/{fd,environ,maps}`` are
unreadable for other users, so a root-owned importer is invisible to this and to
any unprivileged tell. Treat a clean result as "no user-owned importer".
"""
import glob
import os

PRIMARY = "/home/pcalnon/Development/python/Juniper/juniper-cascor"
WORKTREE_ROOTS = (
    "/home/pcalnon/Development/python/Juniper/worktrees",
    os.path.join(PRIMARY, ".claude", "worktrees"),
)


def _is_primary_path(raw: str) -> bool:
    """True only for paths inside the primary checkout, excluding worktrees."""
    if not raw:
        return False
    norm = os.path.normpath(raw)
    if any(norm == r or norm.startswith(r + os.sep) for r in WORKTREE_ROOTS):
        return False
    return norm == PRIMARY or norm.startswith(PRIMARY + os.sep)


def _read(path: str, split_nul: bool = False) -> list[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            data = handle.read()
    except OSError:
        return []
    return [p for p in (data.split("\0") if split_nul else data.split("\n")) if p]


def _evidence(proc: str) -> list[str]:
    """Every way a process can betray that it holds the primary."""
    found = []
    try:
        cwd = os.readlink(os.path.join(proc, "cwd"))
        if _is_primary_path(cwd):
            found.append(f"cwd={cwd}")
    except OSError:
        # Unreadable cwd -- the pid exited mid-scan, or it belongs to another
        # user. Fall through to the remaining probes rather than abandoning the
        # process: cmdline is world-readable even when cwd is not, so a
        # root-owned importer can still be caught by a later arm. This is the
        # documented blind spot in the module docstring, not a silent pass.
        pass
    for token in _read(os.path.join(proc, "cmdline"), split_nul=True):
        if _is_primary_path(token):
            found.append(f"argv={token}")
            break
    for entry in _read(os.path.join(proc, "environ"), split_nul=True):
        _, _, value = entry.partition("=")
        for part in value.split(os.pathsep):
            if _is_primary_path(part):
                found.append(f"env={entry.split('=')[0]}")
                break
        if found and found[-1].startswith("env="):
            break
    for link in glob.glob(os.path.join(proc, "fd", "*")):
        try:
            target = os.readlink(link)
        except OSError:
            continue
        if _is_primary_path(target):
            found.append(f"fd={target}")
            break
    for line in _read(os.path.join(proc, "maps")):
        path = line.split(" ", 5)[-1].strip() if " " in line else ""
        if path.startswith("/") and _is_primary_path(path):
            found.append(f"map={path}")
            break
    return found


def main() -> int:
    hits = 0
    for proc in sorted(glob.glob("/proc/[0-9]*")):
        pid = proc.rsplit("/", 1)[1]
        evidence = _evidence(proc)
        if not evidence:
            continue
        try:
            with open(os.path.join(proc, "comm"), encoding="utf-8") as handle:
                comm = handle.read().strip()
        except OSError:
            comm = "?"
        print(f"HOLDS-PRIMARY  pid={pid:<8} {comm:<16} {'  '.join(evidence)}")
        hits += 1
    if hits:
        print(f"\nFREEZE IN FORCE -- {hits} process(es) hold the cascor primary.")
        return 1
    print("no user-owned process holds the cascor primary -- freeze NOT in force")
    print("(root-owned processes are invisible to an unprivileged scan)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
