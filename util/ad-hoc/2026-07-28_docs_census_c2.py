#!/usr/bin/env python3
"""
C2 docs damage census: reconstruct intended additions for the doc-union-6 and
flag intended-added units missing from current main (LOST-IN-MERGE candidates).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: agent C2 (docs damage census)
Created: 2026-07-28
Status: ad-hoc — investigation
Retire when: 2026-07-25→28 Cursor-flood docs census closed
Related: incident #6 (PR #801/#803), heal PRs #838/#842/#843
"""
import json
import re
import subprocess
import sys

REPO = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/nifty-seeking-pebble"
UNIVERSE = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/a75ce638-5880-486b-b2e8-88f88fc42771/scratchpad/flood_census_universe.json"
CUR = "3915d1e6a7aa7330e5c16f72efefd40ebdf242a9"


def git(args, allow_fail=False):
    r = subprocess.run(["git", "-C", REPO] + args, capture_output=True, text=True)
    if r.returncode != 0 and not allow_fail:
        sys.stderr.write("GIT FAIL: %s\n%s\n" % (" ".join(args), r.stderr))
    return r.stdout


def blob(ref, path):
    return git(["show", "%s:%s" % (ref, path)], allow_fail=True)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def classify(line):
    s = line.strip()
    if not s:
        return None
    if s.startswith("#"):
        return "heading"
    if s.startswith("|"):
        return "table"
    if s.startswith(("- ", "* ", "+ ")) or re.match(r"^\d+[.)]\s", s):
        return "bullet"
    if s.startswith((">", "```", "---", "===")):
        return None
    if len(s) < 12:
        return None
    return "prose"


def added_lines_for_commit(c, path):
    # git show c -- path ; collect + hunks (not +++)
    out = git(["show", "--format=", "--unified=0", c, "--", path], allow_fail=True)
    adds = []
    for ln in out.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            adds.append(ln[1:])
    return adds


def main():
    d = json.load(open(UNIVERSE))
    merges = d["merges"]  # newest-first
    files6 = d["doc_union_6"]
    target = sys.argv[1] if len(sys.argv) > 1 else None

    for F in files6:
        if target and target not in F:
            continue
        rel = [m for m in merges if F in m["files"]]
        rel = list(reversed(rel))  # oldest-first
        if not rel:
            continue
        m0 = rel[0]
        baseline_ref = m0["p1"]
        baseline = blob(baseline_ref, F)
        current = blob(CUR, F)
        cur_norm = norm(current)
        base_norm = norm(baseline)

        print("########################################################")
        print("FILE:", F)
        print("baseline blob = %s:%s   (oldest merge PR#%s %s)" % (baseline_ref[:12], F, m0["pr"], m0["sha"][:12]))
        print("relevant merges (oldest->newest):", ", ".join("#%s" % m["pr"] for m in rel))
        print("current main = %s:%s  (len=%d chars, baseline len=%d)" % (CUR[:12], F, len(current), len(baseline)))
        print()

        # pool intended-added significant units missing from current
        seen = {}  # normkey -> record
        for m in rel:
            commits = git(["log", "--no-merges", "--format=%H", "%s^2" % m["sha"], "--not", "%s^1" % m["sha"]], allow_fail=True).split()
            p2_content = blob(m["p2"], F)
            p2_norm = norm(p2_content)
            for c in commits:
                for al in added_lines_for_commit(c, F):
                    kind = classify(al)
                    if kind is None:
                        continue
                    nk = norm(al)
                    if len(nk) < 12:
                        continue
                    # must survive to branch tip p2 (filter intra-branch churn)
                    if nk not in p2_norm:
                        continue
                    present_cur = nk in cur_norm
                    if present_cur:
                        continue
                    # candidate missing from current
                    rec = seen.get(nk)
                    if rec is None:
                        seen[nk] = {
                            "line": al.strip(),
                            "kind": kind,
                            "prs": set([m["pr"]]),
                            "merges": set([m["sha"]]),
                            "commits": set([c]),
                            "in_baseline": nk in base_norm,
                        }
                    else:
                        rec["prs"].add(m["pr"])
                        rec["merges"].add(m["sha"])
                        rec["commits"].add(c)

        if not seen:
            print(">>> NO intended-added units missing from current main (append-consistent).")
            print()
            continue

        print(">>> %d intended-added unit(s) MISSING from current main:" % len(seen))
        for nk, rec in seen.items():
            prs = ",".join("#%s" % p for p in sorted(rec["prs"]))
            print("  [%s] PRs=%s  base=%s" % (rec["kind"], prs, rec["in_baseline"]))
            print("      LINE: %s" % rec["line"][:200])
        print()


if __name__ == "__main__":
    main()
