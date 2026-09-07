#!/usr/bin/env python3
"""Adjudicate near-duplicate fleet PRs by CONTENT, not by title.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (Cursor-fleet flood disposition)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- analysis
Retire when: the fleet stops emitting re-runs of the same task.
Related:     util/ad-hoc/2026-09-05_fleet_cohort_split.py,
             util/ad-hoc/2026-09-05_fleet_docs_consolidate.py.

WHY TITLES CANNOT DECIDE THIS

The fleet emits pairs whose titles are identical or near-identical -- #1652 and
#1654 are both "operator surface for the F-CANOPY-037 render census", #1678 and
#1680 both "operator surface for the suite driver". Some are genuine re-runs of
one task; others are DISJOINT work that happens to share a subject line, which
is the #772-vs-#774 shape recorded in the round-1 flood analysis: adjacent
titles, disjoint content.

Equally, a pair with DIFFERENT titles can be a true duplicate.

So this compares the normalised set of lines each PR ADDS, and reports:

  containment  = |A ∩ B| / min(|A|, |B|)   -- is one a subset of the other?
  jaccard      = |A ∩ B| / |A ∪ B|         -- how much do they overlap at all?

A high containment with a low jaccard means one PR SUPERSEDES the other (it has
everything the smaller one has, plus more) -- the smaller can be closed against
the larger. High both ways means true duplicate. Low both means disjoint, and
consolidating them is safe but closing either is not.

Header churn (`**Version:**` and friends) is excluded: every fleet PR rewrites
those, so leaving them in inflates every pair toward "duplicate".

Usage
-----
    python3 util/ad-hoc/2026-09-05_fleet_dup_adjudicate.py --pair 1652=1654 \
        --pair 1621=1660 --pair 1678=1680 --pair 1674=1675
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys

NEUTRAL = re.compile(
    r"^\s*\*\*(Version|Status|Last Updated|Author|License|Project|Sub-Project|Maintainer)[:*]",
    re.IGNORECASE,
)


def run(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout


def fetch(pr: int) -> str:
    ref = f"refs/tmp/dup/{pr}"
    subprocess.run(
        ["git", "fetch", "-q", "origin", f"pull/{pr}/head:{ref}", "--force"],
        capture_output=True, check=False,
    )
    return ref


def added(base: str, ref: str) -> set[str]:
    out = set()
    for ln in run("diff", f"{base}...{ref}").splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            body = ln[1:]
            if body.strip() and not NEUTRAL.match(body):
                out.add(" ".join(body.split()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--pair", action="append", required=True, metavar="A=B")
    ap.add_argument("--containment-threshold", type=float, default=0.90)
    args = ap.parse_args()

    print(f"{'pair':>13}  {'|A|':>5} {'|B|':>5} {'inter':>6} {'jaccard':>8} {'contain':>8}  verdict")
    for spec in args.pair:
        a_s, _, b_s = spec.partition("=")
        a, b = int(a_s), int(b_s)
        A = added(args.base, fetch(a))
        B = added(args.base, fetch(b))
        inter = A & B
        union = A | B
        jac = len(inter) / len(union) if union else 0.0
        con = len(inter) / min(len(A), len(B)) if A and B else 0.0

        if con >= args.containment_threshold and len(A) != len(B):
            bigger, smaller = (a, b) if len(A) > len(B) else (b, a)
            verdict = f"#{bigger} SUPERSEDES #{smaller}"
        elif con >= args.containment_threshold:
            verdict = "TRUE DUPLICATE (equal size)"
        elif jac >= 0.5:
            verdict = "HEAVY OVERLAP -- read both"
        else:
            verdict = "DISJOINT -- consolidate, do NOT close either"

        print(f"{a:>6}={b:<6}  {len(A):>5} {len(B):>5} {len(inter):>6} "
              f"{jac:>8.3f} {con:>8.3f}  {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
