#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Canopy E2E arc -- F-CANOPY-039 census precondition (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Emit one line per cascade-growth event while a cascor training run
#          builds hidden units, and EXIT once the run reaches a terminal state.
#
#          The F-CANOPY-039 census has a precondition the census tool now
#          enforces: the server must offer a NON-TRIVIAL topology. A census run
#          against `hidden_units == 0` tests nothing -- a FAIL there means
#          "nothing to paint", not "failed to paint" -- so this waits for a real
#          cascade before the census is allowed to start.
#
#          Coverage note (Monitor's silence-is-not-success rule): this emits on
#          growth, on every terminal status, AND on probe failure. A monitor that
#          only printed growth would be silent through a crashed service, which
#          is indistinguishable from "still training".
#
# Usage:
#   bash util/ad-hoc/e2e_f039_await_cascade.bash [CASCOR_URL] [TARGET_UNITS]
#
# Exit: 0 terminal state reached (or target units hit), 1 probe kept failing.

set -uo pipefail

CASCOR="${1:-http://127.0.0.1:8202}"
TARGET="${2:-0}"          # 0 = wait for terminal status rather than a unit count
POLL_S="${POLL_S:-10}"
MAX_S="${MAX_S:-3600}"

prev_units=""
prev_status=""
fails=0
elapsed=0

while [ "${elapsed}" -lt "${MAX_S}" ]; do
    net="$(curl -s --max-time 10 "${CASCOR}/v1/network" 2>/dev/null)"
    st="$(curl -s --max-time 10 "${CASCOR}/v1/training/status" 2>/dev/null)"

    if [ -z "${net}" ] || [ -z "${st}" ]; then
        fails=$((fails + 1))
        echo "PROBE-FAIL ${fails} (cascor unreachable at ${CASCOR})"
        if [ "${fails}" -ge 5 ]; then
            echo "GIVING UP: cascor unreachable 5 consecutive polls"
            exit 1
        fi
        sleep "${POLL_S}"
        elapsed=$((elapsed + POLL_S))
        continue
    fi
    fails=0

    units="$(printf '%s' "${net}" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("data",{}).get("hidden_units",0))' 2>/dev/null || echo "?")"
    # The status lives at data.state_machine.status ("STARTED"/"COMPLETED"/...),
    # NOT at data.status -- data.status is the ENVELOPE's "success". Reading the
    # envelope yields "unknown" forever and terminal detection never fires.
    status="$(printf '%s' "${st}" | python3 -c 'import json,sys;d=json.load(sys.stdin).get("data",{});sm=d.get("state_machine") or {};mon=d.get("monitor") or {};print((sm.get("status") or "unknown").lower()+("|training" if mon.get("is_training") else "|idle"))' 2>/dev/null || echo "?")"

    if [ "${units}" != "${prev_units}" ]; then
        echo "GROWTH hidden_units=${units} status=${status} t=${elapsed}s"
        prev_units="${units}"
    elif [ "${status}" != "${prev_status}" ]; then
        echo "STATUS ${status} hidden_units=${units} t=${elapsed}s"
    fi
    prev_status="${status}"

    # Terminal states -- emit on ALL of them, not just the happy one.
    case "${status}" in
        completed*|complete*|finished*|stopped*|failed*|error*|*"|idle")
            echo "TERMINAL status=${status} hidden_units=${units} t=${elapsed}s"
            exit 0
            ;;
    esac

    if [ "${TARGET}" -gt 0 ] && [ "${units}" != "?" ] && [ "${units}" -ge "${TARGET}" ]; then
        echo "TARGET-REACHED hidden_units=${units} (>= ${TARGET}) status=${status} t=${elapsed}s"
        exit 0
    fi

    sleep "${POLL_S}"
    elapsed=$((elapsed + POLL_S))
done

echo "TIMEOUT after ${MAX_S}s: hidden_units=${prev_units} status=${prev_status}"
exit 0
