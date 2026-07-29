#!/usr/bin/env python3
"""
C2 docs damage census v2: reconstruct intended additions per relevant merge,
flag intended-added units absent from current main, and auto-adjudicate each via
(a) distinctive-token survival (reword vs true loss) and
(b) main first-parent transition (merge drop = LOST-IN-MERGE vs non-merge = superseded).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: agent C2 (docs damage census)
Created: 2026-07-28
Status: ad-hoc — investigation
Retire when: Cursor-flood docs census closed
Related: incident #6 (PR #801/#803), heals #838/#842/#843
"""
import json
import re
import subprocess
import sys

REPO = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/nifty-seeking-pebble"
UNIVERSE = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/a75ce638-5880-486b-b2e8-88f88fc42771/scratchpad/flood_census_universe.json"
CUR = "3915d1e6a7aa7330e5c16f72efefd40ebdf242a9"


def git(args):
    return subprocess.run(["git", "-C", REPO] + args, capture_output=True, text=True).stdout


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
    if s.startswith((">", "```", "---", "===", "<!--")):
        return None
    if len(s) < 14:
        return None
    return "prose"


def distinctive_tokens(line):
    toks = set()
    for m in re.findall(r"\]\(([^)]+)\)", line):  # link targets incl anchors
        toks.add(("link", m.strip()))
    for m in re.findall(r"#[a-z0-9][a-z0-9-]{4,}", line):  # bare anchors
        toks.add(("anchor", m))
    for m in re.findall(r"(?:ml|cascor|canopy|worker|data|deploy|recurrence)#\d+", line):
        toks.add(("issue", m))
    for m in re.findall(r"`([^`]+)`", line):  # inline code spans
        if len(m) >= 4:
            toks.add(("code", m.strip()))
    for m in re.findall(r"\b[A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b", line):  # SNAKE/Camel_snake
        toks.add(("ident", m))
    for m in re.findall(r"\b[A-Z]{3,}\b", line):  # ALLCAPS tokens e.g. RESUME_MONITOR pieces
        toks.add(("caps", m))
    return toks


def added_lines_for_commit(c, path):
    out = git(["show", "--format=", "--unified=0", c, "--", path])
    return [ln[1:] for ln in out.splitlines() if ln.startswith("+") and not ln.startswith("+++")]


def main():
    d = json.load(open(UNIVERSE))
    merges = d["merges"]
    files6 = d["doc_union_6"]
    target = sys.argv[1] if len(sys.argv) > 1 else None

    fp = git(["rev-list", "--first-parent", "-n", "230", CUR]).split()

    for F in files6:
        if target and target not in F:
            continue
        rel = list(reversed([m for m in merges if F in m["files"]]))
        if not rel:
            continue
        m0 = rel[0]
        baseline = git(["show", "%s:%s" % (m0["p1"], F)])
        current = git(["show", "%s:%s" % (CUR, F)])
        cur_norm = norm(current)
        base_norm = norm(baseline)

        # precompute fp content for this file
        fp_norm = {c: norm(git(["show", "%s:%s" % (c, F)])) for c in fp}

        print("################################################################")
        print("FILE:", F)
        print("baseline = %s:%s  (oldest merge PR#%s)" % (m0["p1"][:12], F, m0["pr"]))
        print("merges(old->new):", " ".join("#%s" % m["pr"] for m in rel))
        n_units_checked = 0
        seen = {}
        for m in rel:
            commits = git(["log", "--no-merges", "--format=%H", "%s^2" % m["sha"], "--not", "%s^1" % m["sha"]]).split()
            p2_norm = norm(git(["show", "%s:%s" % (m["p2"], F)]))
            for c in commits:
                for al in added_lines_for_commit(c, F):
                    kind = classify(al)
                    if kind is None:
                        continue
                    nk = norm(al)
                    if len(nk) < 14 or nk not in p2_norm:
                        continue
                    n_units_checked += 1
                    if nk in cur_norm:
                        continue  # present verbatim
                    rec = seen.setdefault(nk, {"line": al.strip(), "kind": kind, "prs": set(), "in_base": nk in base_norm})
                    rec["prs"].add(m["pr"])

        # adjudicate
        real = []
        reworded = []
        for nk, rec in seen.items():
            toks = distinctive_tokens(rec["line"])
            # token survival: does any distinctive token survive in current main?
            surviving = [t for t in toks if norm(t[1]) in cur_norm]
            missing_toks = [t for t in toks if norm(t[1]) not in cur_norm]
            # pick the most distinctive missing token for transition test; else use a shingle
            probe = None
            for pref in ("anchor", "link", "issue", "ident", "code", "caps"):
                for t in missing_toks:
                    if t[0] == pref:
                        probe = t[1]
                        break
                if probe:
                    break
            if probe is None:
                # shingle: first 8 words
                probe = " ".join(rec["line"].split()[:9])
            rec["probe"] = probe
            rec["surviving_toks"] = surviving
            rec["missing_toks"] = missing_toks
            # verdict on rewording: if ANY distinctive token (anchor/issue/ident/code) survives -> likely reworded/present
            strong_survive = [t for t in surviving if t[0] in ("anchor", "link", "issue", "ident", "code")]
            if strong_survive and rec["kind"] in ("prose", "table", "bullet"):
                reworded.append(rec)
            else:
                real.append(rec)

        # fp transition for real candidates
        print("units_checked=%d  missing_from_current=%d  (real=%d, likely-reworded=%d)" % (n_units_checked, len(seen), len(real), len(reworded)))
        print("---- REAL LOSS CANDIDATES ----")
        for rec in sorted(real, key=lambda r: r["kind"]):
            probe = norm(rec["probe"])
            # transition on fp
            pres = [(c, probe in fp_norm[c]) for c in fp]
            verdict = "?"
            detail = ""
            if pres[0][1]:
                verdict = "PRESENT-NOW(recheck)"
            else:
                boundary = None
                for i in range(len(pres) - 1):
                    if (not pres[i][1]) and pres[i + 1][1]:
                        boundary = i
                        break
                if boundary is None:
                    verdict = "NEVER-ON-FP(side-branch/older)"
                else:
                    losing = pres[boundary][0]
                    par = git(["rev-list", "--parents", "-n", "1", losing]).split()
                    npar = len(par) - 1
                    subj = git(["log", "-1", "--format=%s", losing]).strip()
                    verdict = "LOST-IN-MERGE" if npar >= 2 else "SUPERSEDED(non-merge)"
                    detail = "@%s %s" % (losing[:10], subj[:70])
            prs = ",".join("#%s" % p for p in sorted(rec["prs"]))
            print("  [%s] PRs=%s base=%s :: %s" % (rec["kind"], prs, rec["in_base"], verdict))
            print("     probe=%r %s" % (probe[:60], detail))
            print("     LINE: %s" % rec["line"][:190])
        print("---- LIKELY-REWORDED (distinctive token survives in current) ----")
        for rec in sorted(reworded, key=lambda r: r["kind"]):
            prs = ",".join("#%s" % p for p in sorted(rec["prs"]))
            surv = ",".join("%s:%s" % (t[0], t[1][:24]) for t in rec["surviving_toks"][:3])
            print("  [%s] PRs=%s survive[%s]" % (rec["kind"], prs, surv))
            print("     LINE: %s" % rec["line"][:150])
        print()


if __name__ == "__main__":
    main()
