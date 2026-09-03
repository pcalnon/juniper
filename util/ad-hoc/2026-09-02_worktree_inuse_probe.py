#!/usr/bin/env python3
"""Report any live process whose CWD, or any open file, sits inside a worktree.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc safety probe (worktree sweep)
Author:      Paul Calnon
License:     MIT

Why this exists alongside the cleanup tool's own gate.

``2026-08-28_p5_worktree_cleanup.py`` already refuses to remove a worktree that a process
is sitting in, and that gate is the one that matters. This is an INDEPENDENT second opinion
with a wider net, for the case where the sweep is being run against another session's
possible workspace: it walks ``/proc`` directly and checks, per process,

  * ``cwd``               -- the same predicate the cleanup tool uses;
  * every open file        -- catches an editor or a long ``pytest`` holding a file open
                              while its cwd is elsewhere, which ``cwd`` alone misses;
  * the command line       -- catches a process that names the path as an argument
                              (``python /worktrees/<x>/util/foo.py``) without ever
                              chdir-ing into it.

STRONG vs WEAK signals, and why the distinction is not cosmetic.

``cwd`` and an open ``fd`` are STRONG: a process is genuinely sitting in the tree. A
cmdline mention is WEAK -- it proves only that the path appears in someone's argv.

The first run of this probe reported all four worktrees IN USE, and every hit was the
probe itself plus the shell that launched it, matched because the paths were passed as
ARGUMENTS. A checker whose own invocation trips it is useless: it reports "in use" for
every input, so a real hit is indistinguishable from the noise floor, and the natural next
move is to ignore it. Weak hits are therefore reported separately and never set the exit
code on their own.

Self-matches (this process and its parent) are excluded from the weak signal explicitly,
by pid rather than by pattern -- but any OTHER process naming the path is still surfaced,
because that is a real thing worth a human glance before deleting a tree.

Read-only: opens /proc entries and nothing else. Processes owned by other users are
skipped (their /proc entries are unreadable), which is reported rather than hidden.

Usage:
    python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py <worktree-dir> [<worktree-dir> ...]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _readlink(path: str) -> str | None:
    try:
        return os.readlink(path)
    except OSError:  # PermissionError is a subclass
        return None


def _cmdline(pid: str) -> str:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            return fh.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except OSError:  # PermissionError is a subclass
        return "(unreadable)"


def probe(targets: list[Path]) -> int:
    strong: list[tuple[str, str, str, str]] = []
    weak: list[tuple[str, str, str, str]] = []
    unreadable = 0
    # Exclude this process and its parent (the launching shell) from the WEAK signal only:
    # both necessarily carry the target paths in argv.
    selfpids = {str(os.getpid()), str(os.getppid())}

    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        cmd = _cmdline(entry)
        cwd = _readlink(f"/proc/{entry}/cwd")
        if cwd is None and cmd == "(unreadable)":
            unreadable += 1
            continue

        for target in targets:
            t = str(target)
            if cwd and (cwd == t or cwd.startswith(t + os.sep)):
                strong.append((entry, t, "cwd", cmd))
            fd_dir = f"/proc/{entry}/fd"
            try:
                fds = os.listdir(fd_dir)
            except OSError:  # PermissionError is a subclass
                fds = []
            for fd in fds:
                link = _readlink(f"{fd_dir}/{fd}")
                if link and (link == t or link.startswith(t + os.sep)):
                    strong.append((entry, t, f"open fd {fd} -> {link}", cmd))
                    break
            if t in cmd and entry not in selfpids:
                weak.append((entry, t, "cmdline mention", cmd))

    for target in targets:
        t = str(target)
        s = [h for h in strong if h[1] == t]
        w = [h for h in weak if h[1] == t]
        status = "IN USE" if s else ("review" if w else "free")
        print(f"[{status:^7}] {target.name}")
        for pid, _, how, cmd in s:
            print(f"            STRONG pid {pid}  via {how}")
            print(f"              {cmd[:150]}")
        for pid, _, how, cmd in w:
            print(f"            weak   pid {pid}  via {how}")
            print(f"              {cmd[:150]}")

    print(f"\n{len(strong)} strong (cwd/open-fd) and {len(weak)} weak (cmdline) hit(s) "
          f"across {len(targets)} worktree(s); {unreadable} process(es) unreadable "
          f"(other users) and therefore NOT checked.")
    if strong:
        print("REFUSE: a process is inside one of these trees.")
    elif weak:
        print("CAUTION: no process is inside any tree, but one names a path — glance before removing.")
    else:
        print("CLEAR: no process has a cwd or an open file inside any of these trees.")
    return 1 if strong else 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    return probe([Path(a).resolve() for a in argv])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
