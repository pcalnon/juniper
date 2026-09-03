#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       X7 Lane-A1 mechanism-discrimination probe: measure a MATRIX of canopy endpoints
#                (connect time, first-byte time, total, HTTP status, curl exit) so a stall can be
#                attributed to TCP accept vs first-byte vs status.
#
# Author:        Paul Calnon
# License:       MIT License
#
# Usage:  2026-09-02_x7_probe_matrix.bash <label> [max_time] [port]
#####################################################################################################################################################################################################
set -u

LABEL="${1:-unlabelled}"
MAXT="${2:-12}"
PORT="${3:-8055}"
BASE="http://127.0.0.1:${PORT}"

# %{time_connect}  -> TCP handshake completed (0.000000 if never connected)
# %{time_starttransfer} -> first response byte
# %{time_total}    -> whole transaction
# %{http_code}     -> 000 when no response
FMT='connect=%{time_connect} firstbyte=%{time_starttransfer} total=%{time_total} code=%{http_code}'

probe() {
    local path="$1"
    local out
    out=$(curl -s -o /dev/null --connect-timeout 3 --max-time "${MAXT}" -w "${FMT}" "${BASE}${path}" 2>&1)
    local rc=$?
    printf '%-34s rc=%-3s %s\n' "${path}" "${rc}" "${out}"
}

echo "===== X7 PROBE MATRIX [${LABEL}] $(date +%H:%M:%S.%3N) base=${BASE} max_time=${MAXT}s ====="
probe /v1/health/live
probe /v1/health
probe /api/health
probe /api/status
probe /api/state
probe /openapi.json
probe /docs
probe /metrics
probe /dashboard/
probe /v1/health/ready
echo "===== end [${LABEL}] $(date +%H:%M:%S.%3N) ====="
