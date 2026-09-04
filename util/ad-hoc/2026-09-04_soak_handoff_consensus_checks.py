#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc validation
# File Name:     2026-09-04_soak_handoff_consensus_checks.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-09-04
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    Reconciler-side re-derivation for the independent-agent consensus review of
#    HANDOFF_2026-09-04_soak-per-probe-characterisation.md. Re-computes, from the raw
#    ledger rather than from any agent's report, the three load-bearing Lane B claims:
#
#      1. retention moved ~21 points purely by the one-way rescore verb
#         (RESCORE_OUTCOMES = ("source-recovered",) -- a rescore can only raise retention);
#      2. two different retrieval standards are live in one corpus -- follows scored on tool
#         OUTPUT ("via-search-output") vs tool INPUT ("opened"/"refs") -- and the pooled rate
#         under a uniformly-applied current standard;
#      3. the pre/post rung-1 intervention split (2026-08-31) that the soak ledger's Sec 15.4
#         requires and that analyse() has no filter to honour.
#
#    Read-only. Takes the ledger JSONL as argv[1]; run it against a copy extracted from a ref,
#    never against a live working tree the soak is appending to.
#
# Usage:
#    git show <ref>:reports/soak/pointer_follow_soak.jsonl > /tmp/pr.jsonl
#    python3 util/ad-hoc/2026-09-04_soak_handoff_consensus_checks.py /tmp/pr.jsonl
#####################################################################################################################################################################################################

import collections
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_wilson():
    """Use the ledger's OWN estimator, so the numbers are the ones the tool would print."""
    spec = importlib.util.spec_from_file_location("sl", REPO_ROOT / "util" / "soak_ledger.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.wilson


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <ledger.jsonl>", file=sys.stderr)
        return 2

    wilson = load_wilson()
    rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]

    # A mutation record carries its OWN obs_id and names its TARGET in `invalidates` /
    # `rescores`. Keying on obs_id makes every mutation a silent no-op and inflates the
    # denominator from 43 to 49 -- the reducer still prints a clean, plausible report.
    obs = {r["obs_id"]: r for r in rows if r["kind"] == "observation"}
    invalidated = {r["invalidates"] for r in rows if r["kind"] == "invalidate"}
    rescored = {r["rescores"]: r["to_outcome"] for r in rows if r["kind"] == "rescore"}
    valid = {k: v for k, v in obs.items() if k not in invalidated}
    n = len(valid)

    def outcome_now(obs_id, row):
        return rescored.get(obs_id, row["outcome"])

    print(f"ledger: {len(rows)} records -> {len(obs)} observations, "
          f"{len(invalidated)} invalidated, {len(rescored)} rescored -> {n} valid\n")

    print("== retention moved by the one-way rescore verb ==")
    before = collections.Counter(v["outcome"] for v in valid.values())
    after = collections.Counter(outcome_now(k, v) for k, v in valid.items())
    ret_before = (before["follow"] + before["source-recovered"]) / n
    ret_after = (after["follow"] + after["source-recovered"]) / n
    print(f"  as ORIGINALLY recorded : {dict(before)}")
    print(f"    retention = {ret_before:.1%}")
    print(f"  AFTER {len(rescored)} rescores      : {dict(after)}")
    print(f"    retention = {ret_after:.1%}   (moved {100 * (ret_after - ret_before):+.1f} pts)")

    print("\n== two retrieval standards live in one corpus ==")
    # The scorers recorded this marker in TWO lexical forms; matching only the hyphenated
    # one undercounts it 2 vs 8 and makes the whole finding look like noise.
    output_markers = ("via-search-output", "RETRIEVED via search output")
    follows = [(k, v) for k, v in valid.items() if outcome_now(k, v) == "follow"]
    via_output = [k for k, v in follows
                  if any(mark in (v.get("note") or "") for mark in output_markers)]
    print(f"  follows scored on tool OUTPUT ('via-search-output'): {len(via_output)}")
    print(f"  follows scored on tool INPUT  ('opened'/'refs')    : {len(follows) - len(via_output)}")
    for label, f in (("as scored", len(follows)),
                     ("current standard applied uniformly", len(follows) - len(via_output))):
        lo, hi = wilson(f, n)
        print(f"  pooled {label:36s}: {f}/{n} = {f / n:.1%}  CI [{lo:.3f}, {hi:.3f}]")

    print("\n== pre/post rung-1 intervention split (2026-08-31, ledger Sec 15.4) ==")
    for label, keep in (("PRE ", lambda ts: ts < "2026-08-31"),
                        ("POST", lambda ts: ts >= "2026-08-31")):
        sub = {k: v for k, v in valid.items() if keep(v["ts"])}
        if not sub:
            print(f"  {label}: NO ROWS")
            continue
        f = sum(1 for k, v in sub.items() if outcome_now(k, v) == "follow")
        lo, hi = wilson(f, len(sub))
        print(f"  {label}: {f}/{len(sub)} = {f / len(sub):5.1%}  CI [{lo:.3f}, {hi:.3f}]  "
              f"terminal(BET-FAILING)={hi < 0.750}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
