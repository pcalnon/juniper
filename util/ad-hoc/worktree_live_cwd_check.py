#!/usr/bin/env python3
"""Report any process holding a cwd inside the centralized worktrees dir.

Project:     Juniper
Sub-Project: juniper-ml
Application: defect-register round-28 worktree cleanup gate
Author:      Paul Calnon
License:     MIT License

Live-cwd gate from the worktree/branch cleanup playbook: removing a worktree
that a live process is sitting in traps that process in a deleted directory.
Exact-prefix match, not substring -- a substring test over "juniper-cascor"
also catches juniper-cascor-client and juniper-cascor-worker.
"""
import glob
import os

ROOT = "/home/pcalnon/Development/python/Juniper/worktrees"
hits = 0
for p in glob.glob("/proc/[0-9]*"):
    pid = p.rsplit("/", 1)[1]
    try:
        cwd = os.readlink(os.path.join(p, "cwd"))
    except OSError:
        # The pid exited between the glob and the readlink, or belongs to
        # another user. Either way it cannot be holding one of OUR worktrees
        # open in a way this gate can see, so skip rather than fail the scan.
        continue
    norm = os.path.normpath(cwd)
    if norm == ROOT or norm.startswith(ROOT + os.sep):
        try:
            with open(os.path.join(p, "comm"), encoding="utf-8") as handle:
                comm = handle.read().strip()
        except OSError:
            # The process name is cosmetic here -- the hit is already
            # established by the cwd above, so report it unnamed rather than
            # dropping a genuine blocker from the output.
            comm = "?"
        print(f"LIVE  {pid:>8}  {comm:<16} {cwd}")
        hits += 1
if not hits:
    print("no live process cwd inside the centralized worktrees dir")
