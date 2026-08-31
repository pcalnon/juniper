#!/usr/bin/env python3
"""Print the full detail behind each OPEN rung-2 escalation in the soak ledger.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc soak tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-31
Status:      ad-hoc -- read-only reporting helper for the rung-2 discharge work.
Retire when: the five open escalations are discharged, or this graduates into
             `util/soak_ledger.py` as a `status --verbose` mode.

`soak_ledger.py status` prints escalation obs_ids and nothing else, which is
correct for a verdict tool but useless for actually doing the work: you cannot
build a CI gate from a uuid. This joins each open escalation back to its probe
in the frozen registry so the hazard, its pointer and its discriminator are on
screen together.

Read-only. It never writes to the ledger.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"
PROBES = ROOT / "conf" / "soak_probes.json"


def main() -> int:
    probes = {p["probe_id"]: p for p in json.loads(PROBES.read_text())["probes"]}
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]

    # The escalation field is `miss_class`, and the severity that triggers rung 2 is
    # the PROBE's `severity`, not the observation's. An earlier version of this filter
    # used `class` and `outcome=="miss"` alone and printed "0 open rung-2 escalations"
    # while `soak_ledger.py status` printed five -- a plausible zero from a wrong field
    # name, caught only by cross-checking against the tool that owns the answer.
    resolved = {r.get("resolves") for r in rows if r.get("kind") == "resolve"}
    # MIRRORS util/soak_ledger.py:272-274 exactly. Do not paraphrase it -- this
    # reporter got the filter wrong three times before the definition was simply
    # read from the tool that owns it:
    #   `class` instead of `miss_class`          -> 0 open (plausible, silent)
    #   severity OR miss_class                   -> 9 open (over-broad)
    #   miss_class == "hazard" alone             -> 0 open (wrong field entirely)
    # The real rule: severity comes from the frozen REGISTRY (so the stratum
    # cannot be defined post hoc), the run must be a miss, and a pointer-defect
    # miss is rung 0, not rung 2.
    # The fourth and final missing clause: INVALIDATED observations. The 2026-08-21
    # pilot found 9 of 15 probes tested facts that had never been relocated, so
    # their runs measured nothing and were retired by an auditable append rather
    # than by deleting the line. Omitting this returned NINE against status's five.
    invalidated = {r.get("invalidates") for r in rows if r.get("kind") == "invalidate"}
    misses = [
        r for r in rows
        if r.get("kind") not in ("resolve", "invalidate")
        and r.get("obs_id") not in invalidated
        and r.get("in_scope") is True
        and r.get("arm") == "seeded"
        and r.get("severity") == "hazard"
        and r.get("outcome") == "miss"
        and r.get("miss_class") != "pointer-defect"
        and r.get("obs_id") not in resolved
    ]

    print(f"{len(misses)} open rung-2 escalation(s)")
    print("(cross-check this count against `python3 util/soak_ledger.py status`;\n"
          " a disagreement means this reporter's filter is wrong, not the ledger)\n")
    for r in misses:
        pid = r.get("probe_id", "?")
        p = probes.get(pid, {})
        print(f"=== {pid}")
        print(f"    obs_id       : {r.get('obs_id')}")
        print(f"    severity     : {p.get('severity')}   area: {p.get('area')}")
        print(f"    fact         : {p.get('fact', '?')}")
        print(f"    pointer      : {p.get('pointer', '?')}")
        print(f"    evidence     : {p.get('evidence', '?')}")
        if p.get("must_be_absent_from_source"):
            print(f"    absent-from  : {p['must_be_absent_from_source']}")
        if p.get("discriminator"):
            print(f"    discriminator: {str(p['discriminator'])[:220]}")
        for k in ("note", "notes", "why", "session", "scored_by", "recorded_at"):
            if r.get(k):
                print(f"    {k:13s}: {str(r[k])[:220]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
