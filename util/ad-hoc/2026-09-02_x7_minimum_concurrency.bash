#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       X7 Lane-A1: find the MINIMUM concurrency at which canopy stops answering within the
#                original probe's 8 s budget. Each /v1/health costs the event loop ~3.0 s of
#                urllib3 retry backoff and they SERIALIZE on the loop, so N concurrent requests cost
#                N*3.0 s and N>=3 exceeds 8 s. curl rc=28 == "no response at all", the original
#                X7 observation.
#
# Author:        Paul Calnon
# License:       MIT License
#
# Usage:  2026-09-02_x7_minimum_concurrency.bash [port]
#####################################################################################################################################################################################################
set -u

PORT="${1:-8055}"
BASE="http://127.0.0.1:${PORT}"

run_n() {
    local n="$1"
    echo "--- ${n} concurrent /v1/health, each curl --max-time 8 (the original probe budget) ---"
    for i in $(seq 1 "${n}"); do
        (
            out=$(curl -s -o /dev/null --max-time 8 -w 'firstbyte=%{time_starttransfer} code=%{http_code}' "${BASE}/v1/health")
            rc=$?
            if [ "${rc}" -eq 28 ]; then
                echo "    req${i}: NO RESPONSE (curl rc=28, timed out at 8s)"
            else
                echo "    req${i}: rc=${rc} ${out}"
            fi
        ) &
    done
    wait
    # The pure-async control, issued alongside: proves the whole server is dead, not just /v1/health.
    echo "--- and the pure-async control during the same window ---"
    for i in $(seq 1 "${n}"); do
        curl -s -o /dev/null --max-time 8 "${BASE}/v1/health" &
    done
    sleep 0.4
    out=$(curl -s -o /dev/null --max-time 8 -w 'firstbyte=%{time_starttransfer} code=%{http_code}' "${BASE}/v1/health/live")
    rc=$?
    if [ "${rc}" -eq 28 ]; then
        echo "    /v1/health/live: NO RESPONSE (curl rc=28) — the whole server is unresponsive"
    else
        echo "    /v1/health/live: rc=${rc} ${out}"
    fi
    wait
    echo
}

run_n 2
run_n 3
run_n 4
