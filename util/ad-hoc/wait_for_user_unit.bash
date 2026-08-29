#!/usr/bin/env bash
# Project     : Juniper
# Sub-Project : juniper-ml
# Application : ad-hoc utility
# Author      : Paul Calnon
# Version     : 1.0.0
# License     : MIT License
#
# Block until a systemd --user unit leaves the "active" state, then print its
# final state and journal tail.  Exists because a worktree-isolated session's
# Bash tool refuses an `until ...; do ...; done` loop typed at the prompt, so
# the loop has to live in a file.
#
# Usage: bash util/ad-hoc/wait_for_user_unit.bash <unit> [poll_seconds] [max_seconds]
# Exit:  0 the unit finished, 1 bad usage, 2 timed out still active.

set -uo pipefail

UNIT="${1:?usage: wait_for_user_unit.bash <unit> [poll_seconds] [max_seconds]}"
POLL="${2:-30}"
MAX="${3:-7200}"

waited=0
while [[ "$(systemctl --user is-active "$UNIT" 2>/dev/null)" == "active" ]]; do
    if [[ "$waited" -ge "$MAX" ]]; then
        echo "TIMEOUT: $UNIT still active after ${MAX}s"
        exit 2
    fi
    sleep "$POLL"
    waited=$((waited + POLL))
done

echo "unit $UNIT finished after ~${waited}s -- state: $(systemctl --user is-active "$UNIT" 2>/dev/null || true)"
echo "--- journal tail ---"
journalctl --user -u "$UNIT" --no-pager 2>&1 | tail -15
