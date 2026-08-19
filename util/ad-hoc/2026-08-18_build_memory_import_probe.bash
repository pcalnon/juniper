#!/usr/bin/env bash
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: ad-hoc forensics
# Author:      Paul Calnon
# License:     MIT License
#
# Build a throwaway probe tree that tests whether Claude Code inlines CLAUDE.md
# "@path" imports EAGERLY at load time, and what the recursion depth limit is.
#
# Static analysis of the 2.1.235 binary says the recursive loader `wke` refuses
# at `depth >= 5` (constant iEv=5), with the root CLAUDE.md at depth 0.
# Predicted: CANARY_D1..CANARY_D4 load; CANARY_D5 and CANARY_D6 do NOT.
#
# The probe tree lives OUTSIDE the repo (scratch data dir); only this script
# is version-controlled, per the repo's util/ad-hoc placement rule.

set -euo pipefail

PROBE_DIR="${1:?usage: $0 <probe-dir>}"

rm -rf "$PROBE_DIR"
mkdir -p "$PROBE_DIR"

# Root memory file (depth 0) -> imports d1.md
cat >"$PROBE_DIR/CLAUDE.md" <<'EOF'
# Probe root

Token: CANARY_D0

@./d1.md
EOF

# Chain d1 -> d2 -> ... -> d6, each carrying its own canary.
for n in 1 2 3 4 5 6; do
    next=$((n + 1))
    {
        echo "# Probe level ${n}"
        echo
        echo "Token: CANARY_D${n}"
        echo
        if [ "$n" -lt 6 ]; then
            echo "@./d${next}.md"
        fi
    } >"$PROBE_DIR/d${n}.md"
done

echo "built probe tree in $PROBE_DIR"
ls -1 "$PROBE_DIR"
