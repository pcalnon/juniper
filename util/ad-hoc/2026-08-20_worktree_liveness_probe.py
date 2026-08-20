#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
License:     MIT License

P0b liveness probe: is any live process sitting INSIDE a worktree?

Why this exists on top of the cleaner's own gates
--------------------------------------------------
``scripts/cleanup_session_worktrees.py`` gates on branch state -- merged, clean,
not the current cwd. Those are necessary and they are not sufficient:
**merged-and-clean does not mean idle.** A session can have just merged its PR and
be about to start the next task in the same worktree, and removing it out from
under that session destroys work in progress.

The `locked` flag is the only built-in liveness signal and it is advisory -- both
worktrees that were locked earlier in this effort had released by the time the
sweep ran, while their sessions may well have continued.

So this asks the kernel instead: walk ``/proc/<pid>/cwd`` and report any process
whose working directory is inside a candidate. A hit is a hard stop for that
worktree; no hits is corroboration, not proof (a session idling elsewhere in the
filesystem while holding the worktree open would not be seen).

Usage:
    python3 util/ad-hoc/2026-08-20_worktree_liveness_probe.py <worktree-path> ...

Exit 0 no live process found in any candidate / 1 at least one is occupied.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def processes_in(paths: list[Path]) -> dict[Path, list[tuple[int, str]]]:
    hits: dict[Path, list[tuple[int, str]]] = {p: [] for p in paths}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        try:
            cwd = (entry / "cwd").resolve()
        except (OSError, PermissionError):
            continue  # vanished or not ours -- neither is evidence of occupancy
        for target in paths:
            if cwd == target or target in cwd.parents:
                try:
                    cmd = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                        errors="replace"
                    ).strip()
                except (OSError, PermissionError):
                    cmd = "<unreadable>"
                hits[target].append((pid, cmd[:100]))
    return hits


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    paths = [Path(a).resolve() for a in sys.argv[1:]]
    hits = processes_in(paths)

    occupied = 0
    for target, procs in hits.items():
        if procs:
            occupied += 1
            print(f"OCCUPIED  {target.name}")
            for pid, cmd in procs:
                print(f"            pid {pid}: {cmd}")
        else:
            print(f"clear     {target.name}")

    print(f"\n{len(paths)} checked, {occupied} occupied")
    if occupied:
        print("Do NOT remove an occupied worktree -- a session is working in it.")
    return 1 if occupied else 0


if __name__ == "__main__":
    raise SystemExit(main())
