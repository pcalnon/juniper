#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       X7 Lane-A1 CONTROL: same discriminator, but the blocker path is a parameter.
#                /api/state offloads its synchronous cascor calls with ``await asyncio.to_thread``
#                (main.py:1239) while /v1/health calls them inline (main.py:1076). If the harness is
#                measuring event-loop blockage and not merely "endpoint is slow", then a slow
#                /api/state must NOT stall /v1/health/live, whereas a slow /v1/health must.
#
# Author:        Paul Calnon
# License:       MIT License
#
# Usage:  2026-09-02_x7_blocker_path_control.bash <blocker_path> <n> [port]
#####################################################################################################################################################################################################
set -u

BLOCKER="${1:-/api/state}"
N="${2:-4}"
PORT="${3:-8055}"
BASE="http://127.0.0.1:${PORT}"
FMT='firstbyte=%{time_starttransfer} total=%{time_total} code=%{http_code}'

echo "===== CONTROL: ${N} concurrent blocker(s) on ${BLOCKER} ===== $(date +%H:%M:%S.%3N)"
printf 'PRE   /v1/health/live   %s\n' "$(curl -s -o /dev/null --max-time 12 -w "${FMT}" "${BASE}/v1/health/live")"

for i in $(seq 1 "${N}"); do
    curl -s -o /dev/null --max-time 60 -w "blocker${i} ${BLOCKER} ${FMT}\n" "${BASE}${BLOCKER}" &
done

sleep 0.4
printf 'MID   /v1/health/live   %s\n' "$(curl -s -o /dev/null --max-time 60 -w "${FMT}" "${BASE}/v1/health/live")"
wait
printf 'POST  /v1/health/live   %s\n' "$(curl -s -o /dev/null --max-time 12 -w "${FMT}" "${BASE}/v1/health/live")"
echo "===== end ===== $(date +%H:%M:%S.%3N)"
