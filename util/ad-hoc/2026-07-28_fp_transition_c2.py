#!/usr/bin/env python3
"""
C2 adjudicator: for a file F and a set of distinctive phrases, walk main's
first-parent timeline from current main and find the commit where each phrase
transitioned present->absent, reporting whether that commit is a merge
(LOST-IN-MERGE) or a direct/non-merge edit (SUPERSEDED/INTENTIONAL).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: agent C2 (docs damage census)
Created: 2026-07-28
Status: ad-hoc — investigation
Retire when: Cursor-flood docs census closed
Related: incident #6 (PR #801/#803)
"""
import subprocess
import sys

REPO = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/nifty-seeking-pebble"
CUR = "3915d1e6a7aa7330e5c16f72efefd40ebdf242a9"


def git(args):
    return subprocess.run(["git", "-C", REPO] + args, capture_output=True, text=True).stdout


def norm(s):
    import re
    return re.sub(r"\s+", " ", s).strip()


def main():
    F = sys.argv[1]
    phrases = sys.argv[2:]
    # first-parent main timeline, newest->oldest, limited to window depth
    fp = git(["rev-list", "--first-parent", "-n", "220", CUR]).split()
    # precompute normalized F content at each fp commit
    contents = {}
    for c in fp:
        contents[c] = norm(git(["show", "%s:%s" % (c, F)]))
    for p in phrases:
        pn = norm(p)
        # find transition: newest commit where absent, whose first-parent child(older) has it
        # walk newest->oldest; record presence
        pres = [(c, (pn in contents[c])) for c in fp]
        # current (fp[0]) presence
        cur_present = pres[0][1]
        # find boundary: first index i where pres[i] absent and pres[i+1] present
        boundary = None
        for i in range(len(pres) - 1):
            if (not pres[i][1]) and pres[i + 1][1]:
                boundary = i
                break
        line = "PHRASE: %s..." % p[:70]
        if cur_present:
            print(line, "\n   => PRESENT in current main (no loss).")
            continue
        if boundary is None:
            print(line, "\n   => ABSENT in current main AND never present on this first-parent window (added on a side branch / older).")
            continue
        losing = pres[boundary][0]
        # parents of losing commit
        par = git(["rev-list", "--parents", "-n", "1", losing]).split()
        npar = len(par) - 1
        subj = git(["log", "-1", "--format=%s", losing]).strip()
        kind = "MERGE (LOST-IN-MERGE)" if npar >= 2 else "NON-MERGE (intentional/superseded)"
        print(line)
        print("   => ABSENT now. Dropped at main first-parent commit %s [%d parents] %s" % (losing[:10], npar, kind))
        print("      subj: %s" % subj[:100])
        # also show the older commit that still had it
        print("      last-good (child) %s still had it" % pres[boundary + 1][0][:10])


if __name__ == "__main__":
    main()
