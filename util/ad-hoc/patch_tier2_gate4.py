#!/usr/bin/env python3
"""One-shot patch: make the Tier-2 gate-4 drill check total, not existential.

Ad-hoc, single-use (note 8.13.4).  Idempotent.

The defect being fixed is mine, introduced earlier today.  Gate 4 accepted the
drill if ANY candidate carried verdict VERIFIED:

    if grep -qE '"verdict"...:..."(PASS|VERIFIED)"' "$rj"; then DRILL_OK=1; fi

A drill with 1 VERIFIED and 16 failures would have cleared it and authorised
deleting the last fallback.  The gate must be TOTAL: every candidate verified,
and at least one candidate present.  Parsing is done in python because
results.json is a JSON list of per-candidate objects, and counting them with
grep is what produced the weakness in the first place.
"""

import io
import sys

PATH = "util/ad-hoc/yamaguchi_retire_tier2.bash"

OLD = '''        if grep -qE '"verdict"[[:space:]]*:[[:space:]]*"(PASS|VERIFIED)"' "$rj"; then
            DRILL_OK=1
        fi'''

NEW = '''        # TOTAL, not existential: every candidate must be verified and there must
        # be at least one.  An earlier revision used `grep -q` for a single
        # VERIFIED, which a drill of 1 pass and 16 failures would have satisfied
        # -- authorising deletion of the last fallback on a failed drill.
        if python3 -c "$TIER2_VERDICT_PY" "$rj"; then
            DRILL_OK=1
        fi'''

ANCHOR = 'DRILL_OK=0\nDRILL_SEEN=""'
HELPER = '''# Total-verdict check, kept out of the loop for readability.  Exits 0 only when
# results.json is a non-empty list in which EVERY entry has verdict VERIFIED/PASS.
TIER2_VERDICT_PY='
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(1)
if not isinstance(d, list) or not d:
    sys.exit(1)
ok = {"VERIFIED", "PASS"}
bad = [e for e in d if str(e.get("verdict", "")).upper() not in ok]
if bad:
    sys.stderr.write("  %d of %d candidates NOT verified\\\\n" % (len(bad), len(d)))
    sys.exit(1)
sys.stderr.write("  all %d candidates verified\\\\n" % len(d))
sys.exit(0)
'

DRILL_OK=0
DRILL_SEEN=""'''


def main():
    text = io.open(PATH, encoding="utf-8").read()

    if "TIER2_VERDICT_PY" in text:
        print("already patched -- no-op")
        return 0

    if OLD not in text or ANCHOR not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 1

    text = text.replace(ANCHOR, HELPER, 1)
    text = text.replace(OLD, NEW, 1)
    io.open(PATH, "w", encoding="utf-8").write(text)
    print("patched: gate 4 now requires EVERY candidate verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
