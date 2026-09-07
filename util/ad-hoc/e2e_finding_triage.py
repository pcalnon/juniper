#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc tooling (ad-hoc)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Triage the canopy E2E findings ledger by priority and open/fixed status.

Phase 2's exit criterion (plan §6.3) is "every P0 and P1 closed or explicitly
deferred with owner sign-off", so the arc needs a mechanical count of what is
still open at each priority rather than a hand-maintained list that drifts.

Reads the evidence note's ledger entries -- each is a ``**F-<AREA>-<NNN> — …**``
bold header carrying its priority and status inline -- and prints a triage table
plus totals.

    python3 util/ad-hoc/e2e_finding_triage.py
    python3 util/ad-hoc/e2e_finding_triage.py --open-only

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_NOTE = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
ORDER = {"P0": 0, "P0/P1": 1, "P1": 2, "P2": 3, "CRITICAL": 0, "LEDGER": 4, "?": 5}

# First severity token ANYWHERE in the bolded header body — not only the
# parenthetical. A header that names another severity in prose before
# ``(LEDGER; …)`` is triaged as that severity (F-CANOPY-037 / F-E2E-007).
_PRI_RE = re.compile(r"\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b")


def pri_of(body: str) -> str:
    """Return the first severity token in ``body``, or ``?`` if none."""
    match = _PRI_RE.search(body)
    return match.group(1) if match else "?"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--note", default=DEFAULT_NOTE)
    ap.add_argument("--open-only", action="store_true")
    args = ap.parse_args()

    text = Path(args.note).read_text(encoding="utf-8")
    rows, seen = [], set()
    for m in re.finditer(r"^\*\*(F-[A-Z0-9]+-\d+[a-z]?) — (.*?)\*\*", text, re.M | re.S):
        fid, body = m.group(1), " ".join(m.group(2).split())
        if fid in seen:
            continue
        seen.add(fid)

        tail = body[-170:]
        fixed = bool(re.search(r"\bFIXED\b|\bHEALED\b", tail, re.I))
        # ACCEPTED is a THIRD disposition, not a flavour of fixed: the defect is real
        # and unrepaired, but the owner has signed off on documented behaviour instead
        # of a code change (plan §6.3's "closed or explicitly deferred with owner
        # sign-off"). Counting it as fixed would overstate what shipped; counting it as
        # open would keep an exit criterion red that the owner has already settled.
        accepted = bool(re.search(r"\bACCEPTED\b", tail, re.I)) and not fixed
        # WITHDRAWN is a FOURTH disposition, and it is not a flavour of any other:
        # the finding was WRONG. Nothing was fixed, nothing was accepted, and there is
        # no defect to leave open. Counting it as open keeps a phantom in the exit
        # criterion forever; counting it as fixed claims a repair that never happened.
        # Added 2026-09-04, when F-E2E-007 was withdrawn the day it was filed and the
        # tool had no way to say so.
        withdrawn = bool(re.search(r"\bWITHDRAWN\b", tail, re.I)) and not fixed and not accepted
        rows.append({"id": fid, "pri": pri_of(body), "fixed": fixed, "accepted": accepted, "withdrawn": withdrawn, "short": body.split(":")[0][:78]})

    shown = [r for r in rows if not (args.open_only and (r["fixed"] or r["accepted"] or r["withdrawn"]))]
    shown.sort(key=lambda r: (r["fixed"], r["accepted"], r["withdrawn"], ORDER.get(r["pri"], 9), r["id"]))
    for r in shown:
        state = "FIXED " if r["fixed"] else ("ACCEPT" if r["accepted"] else ("WITHDR" if r["withdrawn"] else "OPEN  "))
        print(f"{state} {r['pri']:<6} {r['id']:<15} {r['short']}")

    op = [r for r in rows if not r["fixed"] and not r["accepted"] and not r["withdrawn"]]
    print()
    print(f"total findings : {len(rows)}")
    print(f"  fixed        : {sum(1 for r in rows if r['fixed'])}")
    print(f"  accepted     : {sum(1 for r in rows if r['accepted'])}")
    print(f"  withdrawn    : {sum(1 for r in rows if r['withdrawn'])}")
    print(f"  open         : {len(op)}")
    for p in ("P0", "P0/P1", "P1", "P2", "CRITICAL", "LEDGER", "?"):
        n = sum(1 for r in op if r["pri"] == p)
        if n:
            print(f"      open {p:<8}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
