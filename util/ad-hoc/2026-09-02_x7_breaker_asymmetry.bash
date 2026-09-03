#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       X7 Lane-A1 secondary finding: /v1/health reaches the cascor client via
#                is_training_in_progress(), which calls self._client.get_training_status() DIRECTLY
#                (cascor_service_adapter.py:1091), bypassing the CircuitBreaker. /api/status reaches
#                it via get_training_status() (line 1969), which IS breaker-wrapped. Prediction:
#                /api/status fails fast after failure_threshold=5; /v1/health never does.
#
# Author:        Paul Calnon
# License:       MIT License
#
# Usage:  2026-09-02_x7_breaker_asymmetry.bash [n_reps] [port]
#####################################################################################################################################################################################################
set -u

REPS="${1:-10}"
PORT="${2:-8055}"
BASE="http://127.0.0.1:${PORT}"

for path in /api/status /v1/health; do
    echo "--- ${REPS} SEQUENTIAL requests to ${path} (cascor down) ---"
    for i in $(seq 1 "${REPS}"); do
        printf '  %2s  %s\n' "${i}" \
            "$(curl -s -o /dev/null --max-time 40 -w 'firstbyte=%{time_starttransfer} code=%{http_code}' "${BASE}${path}")"
    done
done
