#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  util/ad-hoc
# Author:       Paul Calnon
# License:      MIT
############################################################################################################################################################
#
# Watches a running `duplicati-cli backup` and emits one line per STATE CHANGE:
# stall begins, stall recovers, or the process exits. Silent while healthy.
#
# WHY A WATCHER RATHER THAN REPEATED SPOT CHECKS
#   Duplicati rewrites its progress line in place with \r, so a spot check
#   samples one instant. This arc produced two wrong readings that way: a
#   110-second window read 3.6 GiB/h during a small-file patch while the true
#   hour-scale rate was 18.7 GiB/h, and a "zero I/O" reading used
#   read_bytes/write_bytes, which count block-device I/O only and therefore miss
#   everything Duplicati writes to a tmpfs staging dir. A watcher distinguishes
#   "slow" from "stopped"; spot checks cannot.
#
#   On 2026-08-23 a real deadlock was caught this way: PID 779263 went fully idle
#   at ~65% -- zero rchar/wchar, zero CPU, all threads parked, on a machine with
#   no memory or I/O pressure.
#
# COVERAGE
#   Silence must never be mistaken for success, so every distinguishable terminal
#   state is reported: stalled, recovered, and exited.
#
# MODES
#   max_secs > 0   exit at the first state change or when max_secs elapses
#                  (short diagnostic sweep)
#   max_secs = 0   run until the process exits, reporting each stall episode and
#                  each recovery (long unattended run)
#
# Usage: duplicati_progress_watch.bash <pid> <logfile> [stall_secs] [max_secs]
############################################################################################################################################################

set -uo pipefail

PID="${1:?usage: duplicati_progress_watch.bash <pid> <logfile> [stall_secs] [max_secs]}"
LOG="${2:?logfile required}"
STALL_SECS="${3:-180}"
MAX_SECS="${4:-900}"
POLL_SECS="${POLL_SECS:-30}"

last_line() { tail -c 400 "${LOG}" 2>/dev/null | tr '\r' '\n' | tail -1; }

prev="$(last_line)"
start="$(date +%s)"
last_change="${start}"
stalled=0

echo "watch armed on pid ${PID}; baseline: ${prev}"

while true; do
    sleep "${POLL_SECS}"

    if ! kill -0 "${PID}" 2>/dev/null; then
        echo "PROCESS ${PID} EXITED -- inspect the log tail for the result"
        exit 2
    fi

    cur="$(last_line)"
    now="$(date +%s)"

    if [[ "${cur}" != "${prev}" ]]; then
        if [[ "${stalled}" -eq 1 ]]; then
            echo "RECOVERED after $(( now - last_change ))s stalled: ${cur}"
            stalled=0
        fi
        prev="${cur}"
        last_change="${now}"
        if [[ "${MAX_SECS}" -gt 0 ]]; then
            echo "PROGRESS after $(( now - start ))s: ${cur}"
            exit 0
        fi
        continue
    fi

    idle=$(( now - last_change ))
    if [[ "${idle}" -ge "${STALL_SECS}" && "${stalled}" -eq 0 ]]; then
        echo "STALL: no progress for ${idle}s. last=${prev}"
        stalled=1
    fi

    if [[ "${MAX_SECS}" -gt 0 && $(( now - start )) -ge "${MAX_SECS}" ]]; then
        echo "STALL PERSISTS >${MAX_SECS}s -- appears hung. last=${prev}"
        exit 1
    fi
done
