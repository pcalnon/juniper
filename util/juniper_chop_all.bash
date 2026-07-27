#!/usr/bin/env bash
###########################################################################################################################################################################################################
# juniper_chop_all.bash — Stop all Juniper microservices (host-level)
#
# Reads PIDs from the JuniperProject.pid file and sends graceful shutdown
# signals. Falls back to SIGKILL if processes don't terminate within the
# configurable timeout. Optionally cleans up orphaned worker processes.
#
# Environment overrides:
#   JUNIPER_PROJECT_DIR     — Root of Juniper ecosystem (default: ~/Development/python/Juniper)
#   SIGTERM_TIMEOUT         — Seconds to wait after SIGTERM before SIGKILL (default: 15)
#   KILL_WORKERS            — Set to "1" to also kill orphaned cascor worker processes (default: 0)
#   USE_SYSTEMD             — Set to "1" to use systemctl instead of PID files (default: 0)
#   JUNIPER_CHOP_PROC_ROOT  — Override /proc root for validate_pid (tests only; default: /proc)
#
# Flags:
#   --systemd               — Same as USE_SYSTEMD=1
###########################################################################################################################################################################################################
set -euo pipefail


###########################################################################################################################################################################################################
# Define Script Global Environment Constants
###########################################################################################################################################################################################################
JUNIPER_SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
JUNIPER_SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
JUNIPER_SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Script Name:      ${JUNIPER_SCRIPT_NAME}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Script Path:      ${JUNIPER_SCRIPT_PATH}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Script Dir:       ${JUNIPER_SCRIPT_DIR}"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Beginning script run"


###########################################################################################################################################################################################################
# Define Project Environment Constants
##########################################################################################################################################################################################################
JUNIPER_PROJECT_DIR="${JUNIPER_PROJECT_DIR:-${HOME}/Development/python/Juniper}"

JUNIPER_ML_DIR="${JUNIPER_PROJECT_DIR}/juniper-ml"
JUNIPER_DATA_DIR="${JUNIPER_PROJECT_DIR}/juniper-data"
JUNIPER_CASCOR_DIR="${JUNIPER_PROJECT_DIR}/juniper-cascor"
JUNIPER_CANOPY_DIR="${JUNIPER_PROJECT_DIR}/juniper-canopy"
JUNIPER_WORKER_DIR="${JUNIPER_PROJECT_DIR}/juniper-cascor-worker"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_PROJECT_DIR=\"${JUNIPER_PROJECT_DIR}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_ML_DIR=\"${JUNIPER_ML_DIR}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_DATA_DIR=\"${JUNIPER_DATA_DIR}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_CASCOR_DIR=\"${JUNIPER_CASCOR_DIR}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_CANOPY_DIR=\"${JUNIPER_CANOPY_DIR}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_WORKER_DIR=\"${JUNIPER_WORKER_DIR}\""

JUNIPER_CONDA_DIR="${JUNIPER_CONDA_DIR:-/opt/miniforge3}"
CONDA="${JUNIPER_CONDA_DIR}/etc/profile.d/conda.sh"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_CONDA_DIR=\"${JUNIPER_CONDA_DIR}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] CONDA=\"${CONDA}\""

JUNIPER_PROJECT_PID_FILENAME="JuniperProject.pid"
JUNIPER_PROJECT_PID_FILE="${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_PROJECT_PID_FILENAME=\"${JUNIPER_PROJECT_PID_FILENAME}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_PROJECT_PID_FILE=\"${JUNIPER_PROJECT_PID_FILE}\""


###########################################################################################################################################################################################################
# Define Global Environment Constants
###########################################################################################################################################################################################################
SIGTERM_TIMEOUT="${SIGTERM_TIMEOUT:-15}"
KILL_WORKERS="${KILL_WORKERS:-0}"
USE_SYSTEMD="${USE_SYSTEMD:-0}"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] SIGTERM_TIMEOUT=\"${SIGTERM_TIMEOUT}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] KILL_WORKERS=\"${KILL_WORKERS}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] USE_SYSTEMD=\"${USE_SYSTEMD}\""


###########################################################################################################################################################################################################
# Define Working Environment Constants
###########################################################################################################################################################################################################
WORKER_SEARCH_TERM="juniper-cascor-worker"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] SIGTERM_TIMEOUT=\"${SIGTERM_TIMEOUT}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] KILL_WORKERS=\"${KILL_WORKERS}\""

# systemd mode: use systemctl --user instead of PID files
USE_SYSTEMD="${USE_SYSTEMD:-0}"
if [[ "${1:-}" == "--systemd" ]]; then
    USE_SYSTEMD=1
    shift
fi
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] USE_SYSTEMD=\"${USE_SYSTEMD}\""


###########################################################################################################################################################################################################
# systemd Mode (--systemd or USE_SYSTEMD=1)
###########################################################################################################################################################################################################
if [[ "${USE_SYSTEMD}" == "1" ]]; then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Stopping services via systemd ==="

    # Stop in reverse dependency order: worker -> canopy -> cascor -> data
    for svc in juniper-cascor-worker juniper-canopy juniper-cascor juniper-data; do
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Stopping ${svc}..."
        if systemctl --user stop "${svc}.service" 2>/dev/null; then
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ${svc} stopped."
        else
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ${svc} was not running or failed to stop."
        fi
    done

    echo ""
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === All Juniper services stopped via systemd ==="
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Ending script run"
    exit 0
fi
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Stopping services via pidfile ==="


###########################################################################################################################################################################################################
# Utility Functions
###########################################################################################################################################################################################################

# Validate that a PID belongs to the expected Juniper service by checking
# ${JUNIPER_CHOP_PROC_ROOT:-/proc}/<pid>/cmdline (D-05 / JR-ML-SEC-045).
# Rejects non-numeric PIDs, missing /proc entries, empty cmdline, and cmdline
# that does not contain the pidfile service name (hyphen or underscore form).
# Without the name match, a reused PID would receive SIGTERM/SIGKILL.
function validate_pid() {
    local pid="$1"
    local expected_name="$2"
    local proc_root="${JUNIPER_CHOP_PROC_ROOT:-/proc}"

    if ! [[ "${pid}" =~ ^[0-9]+$ ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: Invalid PID '${pid}' for ${expected_name} — skipping"
        return 1
    fi

    if [[ ! -d "${proc_root}/${pid}" ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: PID ${pid} (${expected_name}) is not running — already stopped or stale PID"
        return 1
    fi

    local cmdline
    cmdline="$(tr '\0' ' ' < "${proc_root}/${pid}/cmdline" 2>/dev/null || echo "")"
    if [[ -z "${cmdline// }" ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: PID ${pid} (${expected_name}) has empty/unreadable cmdline — skipping"
        return 1
    fi
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] PID ${pid} cmdline: ${cmdline:0:200}"

    # Plant launches modules as juniper_data / juniper_cascor (underscores) while the
    # pidfile keys use hyphens (juniper-data). Accept either form as a substring.
    local expected_alt="${expected_name//-/_}"
    if [[ "${cmdline}" != *"${expected_name}"* && "${cmdline}" != *"${expected_alt}"* ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: PID ${pid} cmdline does not match expected service '${expected_name}' — skipping (stale PID / wrong process)"
        return 1
    fi

    # juniper-cascor must not match a worker cmdline that contains juniper_cascor_worker.
    if [[ "${expected_name}" == "juniper-cascor" && "${cmdline}" == *worker* ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: PID ${pid} looks like a worker, not juniper-cascor — skipping"
        return 1
    fi

    return 0
}

# Send SIGTERM then wait, escalate to SIGKILL if needed
function graceful_stop() {
    local pid="$1"
    local service_name="$2"
    local timeout="${3:-${SIGTERM_TIMEOUT}}"

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Stopping ${service_name} (PID ${pid}) with SIGTERM (timeout: ${timeout}s)"

    # Send SIGTERM
    if ! kill -SIGTERM "${pid}" 2>/dev/null; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: Failed to send SIGTERM to PID ${pid} — process may have already exited"
        return 0
    fi

    # Wait for process to exit
    local elapsed=0
    while (( elapsed < timeout )); do
        if ! kill -0 "${pid}" 2>/dev/null; then
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ${service_name} (PID ${pid}) stopped gracefully after ${elapsed}s"
            return 0
        fi
        sleep 1
        elapsed=$(( elapsed + 1 ))
    done

    # Process still alive — escalate to SIGKILL
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: ${service_name} (PID ${pid}) did not stop within ${timeout}s — sending SIGKILL"
    if kill -SIGKILL "${pid}" 2>/dev/null; then
        sleep 1
        if ! kill -0 "${pid}" 2>/dev/null; then
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ${service_name} (PID ${pid}) killed with SIGKILL"
            return 0
        fi
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: ${service_name} (PID ${pid}) survived SIGKILL — manual intervention required"
        return 1
    else
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ${service_name} (PID ${pid}) exited during SIGKILL attempt"
        return 0
    fi
}

# Clean up orphaned worker processes
function orphaned_worker_cleanup() {
    local KILL_WORKERS="${1:-${KILL_WORKERS}}"
    local WORKER_SEARCH_TERM="${2:-${WORKER_SEARCH_TERM}}"
    local SIGTERM_TIMEOUT="${3:-${SIGTERM_TIMEOUT}}"

    if [[ "${KILL_WORKERS}" == "1" ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Cleaning up orphaned worker processes ==="
        OLD_IFS="${IFS}"
        IFS=$'\n'
        WORKER_PIDS=()

        # OLD_IFS="${IFS}"; IFS=$'\n'; for i in $(ps aux | grep cascor); do  PIDS="$(echo "${i}" | awk -F " " '{print $2;}')"; echo "Found PID: ${PIDS}"; kill -KILL ${PIDS}; done; IFS="${OLD_IFS}"
        # Found PID: 2990961
        # bash: kill: (2990961) - No such process

        while IFS= read -r line; do
            [[ -z "${line}" ]] && continue

            # pgrep -af outputs: PID CMDLINE
            worker_pid="$(echo "${line}" | awk '{print $1;}')"
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] worker_pid: ${worker_pid}"
            cmdline="$(echo "${line}" | cut -d' ' -f2-)"
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] cmdline: ${cmdline}"

            # Only match actual worker processes, not greps or log viewers.
            # The dash and underscore variants cover both the console-script
            # (`juniper-cascor-worker`) and the import path
            # (`juniper_cascor_worker.cli`); the prior `cascor.*worker`
            # alternative was over-greedy (matched unrelated dev shell
            # processes containing both tokens).
            if echo "${cmdline}" | grep -q "juniper-cascor-worker\|juniper_cascor_worker\|${WORKER_SEARCH_TERM}"; then
                WORKER_PIDS+=("${worker_pid}")
                echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Found worker process: PID ${worker_pid} — ${cmdline:0:120}"
            fi

        # done < <(pgrep -af "juniper.cascor" 2>/dev/null || true)
        done < <(pgrep -af "${WORKER_SEARCH_TERM}" 2>/dev/null || true)
        IFS="${OLD_IFS}"

        if (( ${#WORKER_PIDS[@]} > 0 )); then
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Found ${#WORKER_PIDS[@]} worker process(es) to stop"
            for worker_pid in "${WORKER_PIDS[@]}"; do
                graceful_stop "${worker_pid}" "cascor-worker" 5
            done
        else
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] No orphaned worker processes found"
            return 1
        fi
    else
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] KILL_WORKERS flag is not set to 1. No orphaned worker processes cleanup"
        return 1
    fi
    return 0
}


###########################################################################################################################################################################################################
# Check PID file exists
###########################################################################################################################################################################################################
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Checking PID file exists: ${JUNIPER_PROJECT_PID_FILE}"
if [[ ! -f "${JUNIPER_PROJECT_PID_FILE}" ]]; then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: PID file not found: ${JUNIPER_PROJECT_PID_FILE}"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] No services to stop. Was juniper_plant_all.bash run?"

    # Optionally clean up orphaned worker processes
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] KILL_WORKERS flag to Optionally clean up orphaned worker processes: ${KILL_WORKERS}"
    orphaned_worker_cleanup "${KILL_WORKERS}" "${WORKER_SEARCH_TERM}" "${SIGTERM_TIMEOUT}"

    exit 1
fi

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Checking PID file is not empty: ${JUNIPER_PROJECT_PID_FILE}"
if [[ ! -s "${JUNIPER_PROJECT_PID_FILE}" ]]; then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: PID file is empty: ${JUNIPER_PROJECT_PID_FILE}"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] No services to stop. Was juniper_plant_all.bash run?"

    # Optionally clean up orphaned worker processes
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] KILL_WORKERS flag to Optionally clean up orphaned worker processes: ${KILL_WORKERS}"
    orphaned_worker_cleanup "${KILL_WORKERS}" "${WORKER_SEARCH_TERM}" "${SIGTERM_TIMEOUT}"

    exit 1
fi


###########################################################################################################################################################################################################
# Load Juniper Pid File Lines into array
###########################################################################################################################################################################################################
# mapfile reads lines into array (one element per line, preserving multi-word values)
mapfile -t JUNIPER_PIDS < "${JUNIPER_PROJECT_PID_FILE}"
echo -ne "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Juniper Project PID File Line Array:\n${JUNIPER_PIDS[*]}\n"

PID_COUNT="${#JUNIPER_PIDS[@]}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Juniper Project PID Count: \"${PID_COUNT}\""

if (( PID_COUNT <= 0 )); then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] No PIDs found in \"${JUNIPER_PROJECT_PID_FILE}\""
    exit 1
fi


###########################################################################################################################################################################################################
# Shutdown Juniper Project Services
###########################################################################################################################################################################################################
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Stopping Juniper Services ==="
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] PID file contents:"
cat "${JUNIPER_PROJECT_PID_FILE}"
echo ""

STOP_FAILURES=0

# while IFS= read -r JUNIPER_PIDFILE_LINE; do
for ((i=0; i<${#JUNIPER_PIDS[*]}; i++)); do
    # Skip blank lines
    #[[ -z "${JUNIPER_PIDFILE_LINE}" ]] && continue

    # echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Juniper Pidfile Line: \"${JUNIPER_PIDFILE_LINE}\""
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Juniper Pidfile Line: \"${JUNIPER_PIDS[${i}]}\""
    # Accept both the new "name=pid" format (post-2026-05-07) and the legacy
    # "name: pid" format. Pick the first delimiter present (`=` preferred,
    # `:` as legacy fallback) and split on it.
    JUNIPER_PIDFILE_LINE_RAW="${JUNIPER_PIDS[${i}]}"
    if [[ "${JUNIPER_PIDFILE_LINE_RAW}" == *=* ]]; then
        JUNIPER_APPLICATION_NAME="${JUNIPER_PIDFILE_LINE_RAW%%=*}"
        JUNIPER_APPLICATION_PID="${JUNIPER_PIDFILE_LINE_RAW#*=}"
    else
        JUNIPER_APPLICATION_NAME="${JUNIPER_PIDFILE_LINE_RAW%%:*}"
        JUNIPER_APPLICATION_PID="$(echo "${JUNIPER_PIDFILE_LINE_RAW#*:}" | tr -d ' ')"
    fi
    # Trim any leading/trailing whitespace from the parsed name (defensive).
    JUNIPER_APPLICATION_NAME="${JUNIPER_APPLICATION_NAME## }"
    JUNIPER_APPLICATION_NAME="${JUNIPER_APPLICATION_NAME%% }"

    # Validate PID is numeric
    # if ! [[ "${JUNIPER_APPLICATION_PID}" =~ ^[0-9]+$ ]]; then
    #     echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: Invalid PID '${JUNIPER_APPLICATION_PID}' for ${JUNIPER_APPLICATION_NAME} — skipping"
    #     continue
    # fi

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] --- ${JUNIPER_APPLICATION_NAME} ---"

    if validate_pid "${JUNIPER_APPLICATION_PID}" "${JUNIPER_APPLICATION_NAME}"; then
        if ! graceful_stop "${JUNIPER_APPLICATION_PID}" "${JUNIPER_APPLICATION_NAME}"; then
            STOP_FAILURES=$(( STOP_FAILURES + 1 ))
        fi
    fi

    echo ""
done

# Optionally clean up orphaned worker processes
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] KILL_WORKERS flag to Optionally clean up orphaned worker processes: ${KILL_WORKERS}"
# `|| true`: orphaned_worker_cleanup returns 1 as a benign "nothing to clean"
# signal (KILL_WORKERS=0 by default, or no orphaned workers found). Without this
# guard, `set -e` aborts the script here — before the shutdown summary below
# clears the PID file — so chop_all exits 1 even when every service stopped
# gracefully (STOP_FAILURES=0). Guarding lets the normal success path run.
orphaned_worker_cleanup "${KILL_WORKERS}" "${WORKER_SEARCH_TERM}" "${SIGTERM_TIMEOUT}" || true


###########################################################################################################################################################################################################
# Clean up PID file and report results
###########################################################################################################################################################################################################
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Shutdown Summary ==="

if (( STOP_FAILURES > 0 )); then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: ${STOP_FAILURES} service(s) failed to stop cleanly"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] PID file preserved at ${JUNIPER_PROJECT_PID_FILE} for investigation"
    exit 1
else
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] All services stopped successfully"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Clearing PID file"
    : > "${JUNIPER_PROJECT_PID_FILE}"
fi

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Ending script run"
