#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       X7 Lane-A1 EXACT reproduction of the original single measurement:
#                  cascor up   -> canopy /v1/health 200 fast
#                  cascor down -> curl --max-time 8 gets NO response at all
#                  cascor up   -> 200 fast again, canopy never restarted
#                Run with the dashboard tab OPEN so the dashboard's own polls hold the
#                circuit breaker closed and keep the event loop saturated.
#
# Author:        Paul Calnon
# License:       MIT License
#
# Usage:  2026-09-02_x7_exact_repro.bash <cascor_pid>
#####################################################################################################################################################################################################
set -u

CPID="${1:?cascor pid required}"
CANOPY=http://127.0.0.1:8055
FMT='firstbyte=%{time_starttransfer} total=%{time_total} code=%{http_code}'

echo "### STEP 1 — cascor UP: canopy /v1/health"
printf '   %s  (curl rc=' "$(curl -s -o /dev/null --max-time 8 -w "${FMT}" "${CANOPY}/v1/health")"
echo "$?)"

echo "### STEP 2 — stop cascor (pid ${CPID}), then curl --max-time 8 /v1/health x4"
kill -TERM "${CPID}"
for i in 1 2 3 4; do
    out=$(curl -s -o /dev/null --max-time 8 -w "${FMT}" "${CANOPY}/v1/health")
    rc=$?
    if [ "${rc}" -eq 28 ]; then
        printf '   attempt %s: NO RESPONSE — curl rc=28 (timeout after 8s)  %s\n' "${i}" "${out}"
    else
        printf '   attempt %s: rc=%s  %s\n' "${i}" "${rc}" "${out}"
    fi
done
echo "###   (curl rc=28 == 'Operation timed out' == the original 'no response at all')"
