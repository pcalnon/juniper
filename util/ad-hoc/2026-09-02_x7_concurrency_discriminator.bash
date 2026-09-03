#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       X7 Lane-A1 discriminator: hold N blocking /v1/health requests in flight, then time
#                /v1/health/live (pure-async, zero backend I/O) and /docs (zero backend I/O).
#                If the pure-async control STALLS while the blockers are in flight, the EVENT LOOP
#                is blocked. If it stays fast, the blocking is confined off-loop (threadpool).
#
# Author:        Paul Calnon
# License:       MIT License
#
# Usage:  2026-09-02_x7_concurrency_discriminator.bash <n_blockers> [port]
#####################################################################################################################################################################################################
set -u

N="${1:-1}"
PORT="${2:-8055}"
BASE="http://127.0.0.1:${PORT}"
FMT='connect=%{time_connect} firstbyte=%{time_starttransfer} total=%{time_total} code=%{http_code}'

echo "===== DISCRIMINATOR: ${N} concurrent /v1/health blocker(s) =====  $(date +%H:%M:%S.%3N)"

# 1. Confirm the control is fast with NOTHING in flight.
printf 'PRE   /v1/health/live      %s\n' "$(curl -s -o /dev/null --max-time 12 -w "${FMT}" "${BASE}/v1/health/live")"

# 2. Launch N blockers in the background.
for i in $(seq 1 "${N}"); do
    curl -s -o /dev/null --max-time 30 -w "blocker${i} ${FMT}\n" "${BASE}/v1/health" &
done

# 3. Let the blockers reach the server and enter the synchronous cascor call.
sleep 0.4

# 4. Time the pure-async control WHILE the blockers are in flight.
printf 'MID   /v1/health/live      %s\n' "$(curl -s -o /dev/null --max-time 30 -w "${FMT}" "${BASE}/v1/health/live")"
printf 'MID   /docs                %s\n' "$(curl -s -o /dev/null --max-time 30 -w "${FMT}" "${BASE}/docs")"

wait

# 5. Confirm recovery once the blockers drain.
printf 'POST  /v1/health/live      %s\n' "$(curl -s -o /dev/null --max-time 12 -w "${FMT}" "${BASE}/v1/health/live")"
echo "===== end ===== $(date +%H:%M:%S.%3N)"
