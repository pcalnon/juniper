#!/usr/bin/env bash
###########################################################################################################################################################################################################
# isolated_stack.bash — Bring up / tear down the isolated training-runtime E2E trio
#
# Brings up a THROWAWAY juniper-data + juniper-cascor + juniper-canopy trio on
# non-default ports (8101 / 8202 / 8051) so the training-runtime E2E checklist can
# be run without touching the operator's on-host stack (8100 / 8201 / 8050) or the
# deploy Docker stack. This script ENCODES the bring-up recipe documented in
# juniper-ml notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md
# (roadmap unit E1 of the canopy training-runtime defects plan); that checklist is
# the primary reference and this helper is deliberately simple.
#
# juniper-data runs in a DEDICATED python3.14 venv (the base install has no server;
# the [api] extra provides uvicorn) — the JuniperData conda env is left pristine.
# juniper-cascor + juniper-canopy run from their known-good conda envs.
#
# Flags (exactly one action, plus optional --dry-run):
#   --up        Create the data venv, then launch data -> cascor -> canopy (health-gated).
#   --down      Stop the trio by port and clean run + snapshot artifacts.
#   --status    Probe the three health endpoints and list what is listening on each port.
#   --dry-run   PRINT every command that --up/--down/--status would run, execute nothing.
#               (Use this when 8101/8202/8051 may already be in use.)
#   --help,-h   Print usage and exit.
#
# Environment overrides:
#   JUNIPER_E2E_DATA_PORT      — juniper-data port      (default: 8101)
#   JUNIPER_E2E_CASCOR_PORT    — juniper-cascor port    (default: 8202)
#   JUNIPER_E2E_CANOPY_PORT    — juniper-canopy port    (default: 8051)
#   JUNIPER_E2E_PROJECT_DIR    — ecosystem root         (default: derived from this script's location)
#   JUNIPER_E2E_CONDA_DIR      — miniforge/conda dir     (default: /opt/miniforge3)
#   JUNIPER_E2E_CASCOR_CONDA   — cascor conda env        (default: JuniperCascor1)
#   JUNIPER_E2E_CANOPY_CONDA   — canopy conda env        (default: JuniperCanopy1)
#   JUNIPER_E2E_RUN_DIR        — scratch run dir (venv/logs/data) (default: ${TMPDIR:-/tmp}/juniper-e2e)
#   JUNIPER_E2E_DATA_EXTRAS    — juniper-data pip extras  (default: api; use api,mnist for the D2/I-5 checks)
#   JUNIPER_E2E_HEALTH_TIMEOUT — per-service health wait, seconds (default: 60)
###########################################################################################################################################################################################################
set -euo pipefail


###########################################################################################################################################################################################################
# Script + directory constants
###########################################################################################################################################################################################################
SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

# util/ -> juniper-ml -> Juniper (ecosystem root); override with JUNIPER_E2E_PROJECT_DIR.
JUNIPER_ML_DIR="$(dirname "${SCRIPT_DIR}")"
PROJECT_DIR="${JUNIPER_E2E_PROJECT_DIR:-$(dirname "${JUNIPER_ML_DIR}")}"

DATA_DIR="${PROJECT_DIR}/juniper-data"
CASCOR_SRC_DIR="${PROJECT_DIR}/juniper-cascor/src"
CANOPY_SRC_DIR="${PROJECT_DIR}/juniper-canopy/src"


###########################################################################################################################################################################################################
# Service constants (ports, envs, scratch dirs)
###########################################################################################################################################################################################################
DATA_PORT="${JUNIPER_E2E_DATA_PORT:-8101}"
CASCOR_PORT="${JUNIPER_E2E_CASCOR_PORT:-8202}"
CANOPY_PORT="${JUNIPER_E2E_CANOPY_PORT:-8051}"

CONDA_DIR="${JUNIPER_E2E_CONDA_DIR:-/opt/miniforge3}"
CONDA_SH="${CONDA_DIR}/etc/profile.d/conda.sh"
CASCOR_CONDA="${JUNIPER_E2E_CASCOR_CONDA:-JuniperCascor1}"
CANOPY_CONDA="${JUNIPER_E2E_CANOPY_CONDA:-JuniperCanopy1}"

RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"
DATA_VENV="${RUN_DIR}/.venv-data"
LOG_DIR="${RUN_DIR}/logs"
DATA_EXTRAS="${JUNIPER_E2E_DATA_EXTRAS:-api}"
HEALTH_TIMEOUT="${JUNIPER_E2E_HEALTH_TIMEOUT:-60}"

# The control-WS Origin / allowlist pair: cascor's /ws/control allowlist must admit canopy's
# presented Origin (both are canopy's own origin). Without the pair: 403 + reconnect churn.
CANOPY_ORIGIN="http://127.0.0.1:${CANOPY_PORT}"

DRY_RUN=0
ACTION=""


###########################################################################################################################################################################################################
# Utility functions
###########################################################################################################################################################################################################
usage() {
    cat <<USAGE
${SCRIPT_NAME} — isolated training-runtime E2E stack (data ${DATA_PORT} / cascor ${CASCOR_PORT} / canopy ${CANOPY_PORT})

Usage: ${SCRIPT_NAME} [--dry-run] (--up | --down | --status)
       ${SCRIPT_NAME} --help

  --up       Create the data venv, then launch data -> cascor -> canopy (health-gated).
  --down     Stop the trio by port and clean run + snapshot artifacts.
  --status   Probe the three health endpoints and list listening ports.
  --dry-run  Print every command without executing it (safe when the ports are in use).
  --help,-h  Print this help.

See juniper-ml notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md for the full checklist.
USAGE
}

log() { echo "[${SCRIPT_NAME}] $*"; }

banner() {
    echo ""
    echo "[${SCRIPT_NAME}] === $* ==="
}

# Print a command line (prefixed with a literal '$'); callers guard side effects with is_dry.
announce() { echo "[${SCRIPT_NAME}] \$ $*"; }

is_dry() { [[ "${DRY_RUN}" == "1" ]]; }

require_cmd() {
    local cmd="$1"
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        log "ERROR: required command '${cmd}' not found in PATH"
        return 1
    fi
}

ensure_dir() {
    local dir="$1"
    [[ -d "${dir}" ]] || mkdir -p "${dir}"
}

# PID of whatever is listening on a TCP port (empty if nothing / ss unavailable).
port_pid() {
    local port="$1" out
    out="$(ss -tlnpH "sport = :${port}" 2>/dev/null | grep -oE 'pid=[0-9]+' | head -n1 | cut -d= -f2 || true)"
    printf '%s' "${out}"
}

# Poll a health URL until 200 or timeout (live mode only).
wait_for_health() {
    local name="$1" url="$2" timeout="${3:-${HEALTH_TIMEOUT}}" elapsed=0
    log "Waiting for ${name} health at ${url} (timeout ${timeout}s)"
    while (( elapsed < timeout )); do
        if curl -sf --max-time 5 "${url}" >/dev/null 2>&1; then
            log "${name} is healthy (took ${elapsed}s)"
            return 0
        fi
        sleep 2
        elapsed=$(( elapsed + 2 ))
    done
    log "ERROR: ${name} failed to become healthy within ${timeout}s (see ${LOG_DIR})"
    return 1
}

# Source conda + activate an env (nounset-safe, matching juniper_plant_all.bash).
#
# Fail-closed on ``source`` / ``conda activate``: callers may invoke this as
# ``activate_conda … || return 1`` (open #963 ``*_up || failed=1`` absorb), which
# disables ``set -e`` for the whole body (bash OR-list rule). A bare
# ``conda activate`` failure followed by a successful ``set -u`` would otherwise
# return 0 and let cascor/canopy launch on the ambient PATH.
activate_conda() {
    local env_name="$1"
    if [[ ! -f "${CONDA_SH}" ]]; then
        log "ERROR: conda not found at ${CONDA_SH} (set JUNIPER_E2E_CONDA_DIR)"
        return 1
    fi
    # shellcheck source=/dev/null
    source "${CONDA_SH}" || {
        log "ERROR: failed to source conda.sh at ${CONDA_SH}"
        return 1
    }
    # Conda activation scripts (e.g. activate-binutils_linux-64.sh) may
    # reference unset vars like ADDR2LINE; disable nounset for the call only.
    set +u
    if ! conda activate "${env_name}"; then
        set -u
        log "ERROR: conda activate '${env_name}' failed"
        return 1
    fi
    set -u
}


###########################################################################################################################################################################################################
# Bring-up: juniper-data on a dedicated python3.14 venv
###########################################################################################################################################################################################################
data_up() {
    banner "juniper-data  ->  http://127.0.0.1:${DATA_PORT}  (dedicated venv)"
    announce "mkdir -p ${RUN_DIR} && cd ${RUN_DIR}"
    announce "python3.14 -m venv ${DATA_VENV}"
    announce "source ${DATA_VENV}/bin/activate"
    announce "pip install -e '${DATA_DIR}[${DATA_EXTRAS}]' prometheus_client juniper-observability"
    announce "python -m juniper_data --host 127.0.0.1 --port ${DATA_PORT}   # nohup -> ${LOG_DIR}/juniper-data.log"
    if is_dry; then return 0; fi

    require_cmd python3.14
    ensure_dir "${RUN_DIR}"
    ensure_dir "${LOG_DIR}"
    [[ -d "${DATA_VENV}" ]] || python3.14 -m venv "${DATA_VENV}"
    # shellcheck source=/dev/null
    source "${DATA_VENV}/bin/activate"
    pip install -q -e "${DATA_DIR}[${DATA_EXTRAS}]" prometheus_client juniper-observability
    (
        cd "${RUN_DIR}"
        PYTHON_GIL=0 nohup python -m juniper_data --host 127.0.0.1 --port "${DATA_PORT}" >"${LOG_DIR}/juniper-data.log" 2>&1 &
        echo "$!" >"${RUN_DIR}/juniper-data.pid"
    )
    deactivate || true
    wait_for_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health"
}


###########################################################################################################################################################################################################
# Bring-up: juniper-cascor (JuniperCascor1), pointed at the isolated juniper-data
###########################################################################################################################################################################################################
cascor_up() {
    banner "juniper-cascor  ->  http://127.0.0.1:${CASCOR_PORT}  (${CASCOR_CONDA})"
    announce "conda activate ${CASCOR_CONDA} && cd ${CASCOR_SRC_DIR}"
    announce "LD_LIBRARY_PATH= JUNIPER_DATA_URL=http://127.0.0.1:${DATA_PORT} JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=${CANOPY_ORIGIN} uvicorn api.app:create_app --factory --host 127.0.0.1 --port ${CASCOR_PORT}   # nohup -> ${LOG_DIR}/juniper-cascor.log"
    if is_dry; then return 0; fi

    ensure_dir "${LOG_DIR}"
    activate_conda "${CASCOR_CONDA}"
    (
        cd "${CASCOR_SRC_DIR}"
        LD_LIBRARY_PATH='' \
            JUNIPER_DATA_URL="http://127.0.0.1:${DATA_PORT}" \
            JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS="${CANOPY_ORIGIN}" \
            nohup uvicorn api.app:create_app --factory --host 127.0.0.1 --port "${CASCOR_PORT}" >"${LOG_DIR}/juniper-cascor.log" 2>&1 &
        echo "$!" >"${RUN_DIR}/juniper-cascor.pid"
    )
    wait_for_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health"
}


###########################################################################################################################################################################################################
# Bring-up: juniper-canopy (JuniperCanopy1), service mode, WS Origin aligned to cascor's allowlist
###########################################################################################################################################################################################################
canopy_up() {
    banner "juniper-canopy  ->  http://127.0.0.1:${CANOPY_PORT}  (${CANOPY_CONDA}, service mode)"
    announce "conda activate ${CANOPY_CONDA} && cd ${CANOPY_SRC_DIR}"
    announce "JUNIPER_CANOPY_DEMO_MODE=0 JUNIPER_CANOPY_PORT=${CANOPY_PORT} JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://127.0.0.1:${CASCOR_PORT} JUNIPER_CANOPY_JUNIPER_DATA_URL=http://127.0.0.1:${DATA_PORT} JUNIPER_CANOPY_CASCOR_WS_ORIGIN=${CANOPY_ORIGIN} python main.py   # nohup -> ${LOG_DIR}/juniper-canopy.log"
    if is_dry; then return 0; fi

    ensure_dir "${LOG_DIR}"
    activate_conda "${CANOPY_CONDA}"
    (
        cd "${CANOPY_SRC_DIR}"
        JUNIPER_CANOPY_DEMO_MODE=0 \
            JUNIPER_CANOPY_PORT="${CANOPY_PORT}" \
            JUNIPER_CANOPY_CASCOR_SERVICE_URL="http://127.0.0.1:${CASCOR_PORT}" \
            JUNIPER_CANOPY_JUNIPER_DATA_URL="http://127.0.0.1:${DATA_PORT}" \
            JUNIPER_CANOPY_CASCOR_WS_ORIGIN="${CANOPY_ORIGIN}" \
            nohup python main.py >"${LOG_DIR}/juniper-canopy.log" 2>&1 &
        echo "$!" >"${RUN_DIR}/juniper-canopy.pid"
    )
    wait_for_health "juniper-canopy" "http://127.0.0.1:${CANOPY_PORT}/v1/health"
}


###########################################################################################################################################################################################################
# Teardown: stop one service by its listening port
###########################################################################################################################################################################################################
stop_port() {
    local port="$1" name="$2" pid
    announce "kill \$(ss -tlnpH \"sport = :${port}\" | grep -oE 'pid=[0-9]+' | cut -d= -f2)   # stop ${name} on ${port}"
    if is_dry; then return 0; fi
    pid="$(port_pid "${port}")"
    if [[ -n "${pid}" ]]; then
        log "Stopping ${name} (pid ${pid}) on port ${port}"
        kill "${pid}" 2>/dev/null || true
    else
        log "${name}: nothing listening on port ${port}"
    fi
}


###########################################################################################################################################################################################################
# Action: --up
###########################################################################################################################################################################################################
do_up() {
    banner "Bringing UP the isolated E2E trio (data ${DATA_PORT} / cascor ${CASCOR_PORT} / canopy ${CANOPY_PORT})"
    if is_dry; then log "DRY-RUN: printing commands only, launching nothing"; fi
    data_up
    cascor_up
    canopy_up
    banner "Isolated E2E trio is up"
    log "data   : http://127.0.0.1:${DATA_PORT}/v1/health"
    log "cascor : http://127.0.0.1:${CASCOR_PORT}/v1/health"
    log "canopy : http://127.0.0.1:${CANOPY_PORT}/v1/health"
}


###########################################################################################################################################################################################################
# Action: --down
###########################################################################################################################################################################################################
do_down() {
    banner "Bringing DOWN the isolated E2E trio + cleaning artifacts"
    if is_dry; then log "DRY-RUN: printing commands only, removing nothing"; fi
    stop_port "${CANOPY_PORT}" "juniper-canopy"
    stop_port "${CASCOR_PORT}" "juniper-cascor"
    stop_port "${DATA_PORT}" "juniper-data"

    announce "rm -rf ${RUN_DIR}/data ${DATA_VENV} ${RUN_DIR}/*.pid   # run artifacts"
    announce "rm -f ${CASCOR_SRC_DIR}/snapshots/snapshot_* ${CANOPY_SRC_DIR}/snapshots/snapshot_*   # snapshot artifacts"
    if is_dry; then return 0; fi
    rm -rf "${RUN_DIR}/data" "${DATA_VENV}" || true
    rm -f "${RUN_DIR}"/*.pid || true
    rm -f "${CASCOR_SRC_DIR}"/snapshots/snapshot_* 2>/dev/null || true
    rm -f "${CANOPY_SRC_DIR}"/snapshots/snapshot_* 2>/dev/null || true
    log "Teardown complete"
}


###########################################################################################################################################################################################################
# Action: --status
###########################################################################################################################################################################################################
probe_health() {
    local name="$1" url="$2" port="$3" code pid
    announce "curl -s -o /dev/null -w '%{http_code}' ${url}   # ${name}"
    if is_dry; then return 0; fi
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "${url}" 2>/dev/null || true)"
    pid="$(port_pid "${port}")"
    log "${name}: health=${code:-000} port=${port} pid=${pid:-none}"
}

do_status() {
    banner "Isolated E2E trio status"
    probe_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health" "${DATA_PORT}"
    probe_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health" "${CASCOR_PORT}"
    probe_health "juniper-canopy" "http://127.0.0.1:${CANOPY_PORT}/v1/health" "${CANOPY_PORT}"
}


###########################################################################################################################################################################################################
# Argument parsing
###########################################################################################################################################################################################################
set_action() {
    if [[ -n "${ACTION}" ]]; then
        log "ERROR: choose exactly one of --up / --down / --status"
        usage
        exit 2
    fi
    ACTION="$1"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --up) set_action up ;;
        --down) set_action down ;;
        --status) set_action status ;;
        --dry-run) DRY_RUN=1 ;;
        --help | -h) usage; exit 0 ;;
        *)
            log "ERROR: unknown argument '$1'"
            usage
            exit 2
            ;;
    esac
    shift
done

if [[ -z "${ACTION}" ]]; then
    log "ERROR: no action given (--up / --down / --status)"
    usage
    exit 2
fi

case "${ACTION}" in
    up) do_up ;;
    down) do_down ;;
    status) do_status ;;
esac
