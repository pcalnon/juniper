#!/usr/bin/env python3
"""Measure what re-scoring SOURCE-RECOVERED as its own outcome does to the soak.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc soak analysis
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-31
Status:      ad-hoc -- impact analysis for the owner's 2026-08-31 decision to
             re-score source-recovery as its own outcome.
Retire when: the re-score has landed in util/soak_ledger.py and this is history.

Read-only. It writes nothing and changes no scoring; it exists so the decision is
taken against measured consequences rather than an intuition about them.

Why this is run BEFORE implementing
-----------------------------------
Re-scoring moves rows out of the miss column. That is exactly the shape of a
change that makes an inconvenient result look good, and the ledger says so in its
own words ("Do NOT run [resolve] to make status exit 0"). So the first question
is not "how do I implement it" but "what does it do to the headline, and does it
produce a degenerate 100%?" If every miss is source-recovered, the follow rate
loses its denominator and the soak stops measuring anything -- that possibility
has to be visible before the change, not discovered after.

Three candidate models are costed:
  A  source-recovery LEAVES the denominator  (treated like a void run)
  B  source-recovery is its own outcome, IN the denominator, not a follow
  C  status quo
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"

SRC = re.compile(r"source[- ]recovered", re.I)
CORRECT = re.compile(r"\bANSWER CORRECT\b|\bCORRECT\b", re.I)


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - m) / d, (c + m) / d)


def main() -> int:
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    inval = {r.get("invalidates") for r in rows if r.get("kind") == "invalidate"}
    seeded = [
        r for r in rows
        if r.get("kind") not in ("resolve", "invalidate")
        and r.get("obs_id") not in inval
        and r.get("in_scope") is True
        and r.get("arm") == "seeded"
    ]

    follows = [r for r in seeded if r.get("outcome") == "follow"]
    misses = [r for r in seeded if r.get("outcome") == "miss"]
    ptr_def = [r for r in misses if r.get("miss_class") == "pointer-defect"]
    arch_miss = [r for r in misses if r.get("miss_class") != "pointer-defect"]

    src = [r for r in arch_miss if SRC.search(r.get("note") or "")]
    not_src = [r for r in arch_miss if not SRC.search(r.get("note") or "")]
    src_correct = [r for r in src if CORRECT.search(r.get("note") or "")]

    print(f"seeded, in-scope, non-invalidated runs : {len(seeded)}")
    print(f"  follow                              : {len(follows)}")
    print(f"  miss (architectural)                : {len(arch_miss)}")
    print(f"     of which SOURCE-RECOVERED        : {len(src)}")
    print(f"        ...and noted CORRECT          : {len(src_correct)}")
    print(f"     NOT source-recovered             : {len(not_src)}")
    print(f"  pointer-defect (already separate)   : {len(ptr_def)}")

    if not_src:
        print("\n  the non-source-recovered misses (these are the REAL misses):")
        for r in not_src:
            print(f"    {r.get('probe_id')}  class={r.get('miss_class')}")
            print(f"      {(r.get('note') or '')[:190]}")

    def line(label: str, k: int, n: int) -> None:
        if n == 0:
            print(f"  {label:52s} {k}/{n} = UNDEFINED (empty denominator)")
            return
        lo, hi = wilson(k, n)
        edge = ""
        if hi < 0.75:
            edge = "  -> below 0.75 boundary"
        elif lo > 0.75:
            edge = "  -> above 0.75 boundary"
        else:
            edge = "  -> spans 0.75 (INCONCLUSIVE)"
        print(f"  {label:52s} {k}/{n} = {k/n:6.1%}  CI [{lo:.3f}, {hi:.3f}]{edge}")

    print("\nmodels:")
    line("C  status quo (follow / follow+miss)", len(follows), len(follows) + len(arch_miss))
    line("A  source-recovery LEAVES denominator", len(follows), len(follows) + len(not_src))
    n_b = len(follows) + len(src) + len(not_src)
    line("B  follow-rate, src-rec in denominator", len(follows), n_b)
    line("B  RETENTION rate (follow+src-rec)", len(follows) + len(src), n_b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
