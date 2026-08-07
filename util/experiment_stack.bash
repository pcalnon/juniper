#!/usr/bin/env bash
###########################################################################################################################################################################################################
# experiment_stack.bash — per-run experiment stack launcher (CLI experimentation program, Wave 2.1)
#
# Brings up a THROWAWAY, PER-RUN juniper-data instance plus juniper-cascor and/or
# juniper-recurrence on ports drawn from the dedicated experiment ranges
# (data 8110-8139 / cascor 8230-8259 / recurrence 8260-8289), with every artifact
# confined to a per-run RUN_DIR, so concurrent experiment runs never collide with each
# other nor with the operator's on-host stack (8100 / 8200 / 8201 / 8210 / 8050).
#
# This script ENCODES the launcher contract designed in juniper-ml
# notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md
# §6.2 (behaviour table), §6.1 (canonical launch recipes), §6.4 (RUN_DIR layout),
# §7.2/§7.3 (Grafana bridge: target file + socat relay) and §9.3 (port ranges); that plan
# is the primary reference and this helper is deliberately mechanical. Binding preflight
# evidence lives in
# notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md.
#
# Hard invariants (plan §9.1/§9.2):
#   * JuniperProject.pid is NEVER read or written — that file belongs to
#     juniper_plant_all.bash / juniper_chop_all.bash (hazard H-10).
#   * No repo .env is ever created, edited, or deleted; all per-run config is process env
#     (hazard H-3 — cascor loads .env from CWD).
#   * juniper-canopy is never started, and 8050 / 8051 are never used.
#   * Teardown kills ONLY pids this run recorded (or the listener on a port this run
#     recorded), and never deletes artifacts/.
#
# Flags (exactly one action, plus options):
#   --up                 Allocate ports, launch data -> cascor -> recurrence (health-gated).
#                        Mid-bring-up / grafana-bridge failure tears the partial run down
#                        via teardown_run (no orphan listeners on the experiment ranges).
#                        Requires at least one app selector.
#     --cascor           Include juniper-cascor in the run (cascor arm = data + cascor).
#     --recurrence       Include juniper-recurrence (recurrence arm = data + recurrence).
#     --shared-data URL  Reuse an existing juniper-data at URL instead of launching one.
#     --config PATH      Stage an experiment YAML into the RUN_DIR (see CONFIG below).
#     --experiment NAME  Value for the Prometheus 'experiment' target label (§7.2).
#     --grafana-bridge   OPT-IN: start the socat relays + write the Prometheus target file.
#   --down RUN_ID        Tear the run down (pidfile-first), release its port locks,
#                        remove its relays + target file. Keeps artifacts/.
#     --all-mine         With --down: tear down EVERY run under the run root.
#   --status [RUN_ID]    Probe a run (or list every run) — health, pids, scrape state.
#   --dry-run            PRINT every command with ports/paths expanded; create nothing,
#                        start nothing, kill nothing, write no target file, take no locks.
#   --help,-h            Print usage and exit 0.
#
# Environment overrides:
#   JUNIPER_EXP_RUN_ROOT        — run root (default: ${HOME}/.local/state/juniper-experiments)
#   JUNIPER_EXP_LOCK_ROOT       — port lockdir root (default: ${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments)
#   JUNIPER_EXP_PROJECT_DIR     — ecosystem root (default: derived from this script's
#                                 location, i.e. /home/pcalnon/Development/python/Juniper
#                                 for the canonical checkout; SET THIS when running the
#                                 launcher from a git worktree, where the derivation lands
#                                 inside worktrees/ instead)
#   JUNIPER_EXP_DEPLOY_DIR      — juniper-deploy checkout hosting prometheus/targets/ (F-3;
#                                 default: <ecosystem root>/juniper-deploy)
#   JUNIPER_EXP_CONDA_DIR       — miniforge/conda dir (default: /opt/miniforge3)
#   JUNIPER_EXP_DATA_CONDA      — juniper-data env       (default: JuniperData)
#   JUNIPER_EXP_CASCOR_CONDA    — juniper-cascor env     (default: JuniperCascor1)
#   JUNIPER_EXP_RECURRENCE_CONDA— juniper-recurrence env (default: JuniperCascor1)
#   JUNIPER_EXP_HEALTH_TIMEOUT  — per-service health wait, seconds (default: 90 — F-8 sizes
#                                 this for a COLD start; recurrence needs 10-15 s of import)
#   JUNIPER_EXP_KILL_TIMEOUT    — SIGTERM -> SIGKILL grace, seconds (default: 10)
#   JUNIPER_EXP_CONDA_ACTIVATE  — 1 to `conda activate` before launching instead of using the
#                                 env's bin/ directly (see CONDA below)
#
# CONDA: services are launched through direct env-bin paths
# (${JUNIPER_EXP_CONDA_DIR}/envs/<env>/bin/...), which is what the P0 evidence run used and
# is equivalent here because neither JuniperCascor1 nor JuniperData ships
# etc/conda/activate.d/ hooks (verified 2026-07-30). Set JUNIPER_EXP_CONDA_ACTIVATE=1 to go
# through `conda activate` instead, for an env that later grows activation hooks.
#
# CONFIG: --config PATH copies the YAML verbatim to $RUN_DIR/config/experiment.yaml (§6.4)
# and exports JUNIPER_CASCOR_CONFIG_FILE at it (§6.2). The app-side YAML settings source is
# Wave 3.1/3.3 — until it lands the env var is inert and `juniper-recurrence serve` has no
# --config flag, so the launcher stages the file and says so rather than passing an
# unsupported flag.
###########################################################################################################################################################################################################
set -euo pipefail


###########################################################################################################################################################################################################
# Script + directory constants
###########################################################################################################################################################################################################
SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

# util/ -> juniper-ml -> Juniper (ecosystem root); override with JUNIPER_EXP_PROJECT_DIR.
JUNIPER_ML_DIR="$(dirname "${SCRIPT_DIR}")"
PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-$(dirname "${JUNIPER_ML_DIR}")}"

# juniper-data is launched as `python -m juniper_data` from its conda env, so no repo path
# is needed for it; cascor's uvicorn factory import DOES require its src/ as CWD (§6.1).
CASCOR_SRC_DIR="${PROJECT_DIR}/juniper-cascor/src"
DEPLOY_DIR="${JUNIPER_EXP_DEPLOY_DIR:-${PROJECT_DIR}/juniper-deploy}"
# F-3: prometheus/targets/ is already inside the existing ./prometheus:/etc/prometheus:ro
# mount, so writing here needs no compose change at all.
TARGETS_DIR="${DEPLOY_DIR}/prometheus/targets"


###########################################################################################################################################################################################################
# Port ranges (plan §9.3) — contiguous, disjoint, and deliberately clear of every operator port
###########################################################################################################################################################################################################
DATA_PORT_MIN=8110
DATA_PORT_MAX=8139
CASCOR_PORT_MIN=8230
CASCOR_PORT_MAX=8259
RECURRENCE_PORT_MIN=8260
RECURRENCE_PORT_MAX=8289


###########################################################################################################################################################################################################
# Run identity + roots
###########################################################################################################################################################################################################
RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
# A lock is ephemeral state, so it belongs in the runtime dir — NOT in RUN_ROOT, which is
# deliberately durable (H-15: results must survive a reaped sandbox).
LOCK_ROOT="${JUNIPER_EXP_LOCK_ROOT:-${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments}"

CONDA_DIR="${JUNIPER_EXP_CONDA_DIR:-/opt/miniforge3}"
CONDA_SH="${CONDA_DIR}/etc/profile.d/conda.sh"
DATA_CONDA="${JUNIPER_EXP_DATA_CONDA:-JuniperData}"
CASCOR_CONDA="${JUNIPER_EXP_CASCOR_CONDA:-JuniperCascor1}"
RECURRENCE_CONDA="${JUNIPER_EXP_RECURRENCE_CONDA:-JuniperCascor1}"

HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-90}"
KILL_TIMEOUT="${JUNIPER_EXP_KILL_TIMEOUT:-10}"
CONDA_ACTIVATE="${JUNIPER_EXP_CONDA_ACTIVATE:-0}"


###########################################################################################################################################################################################################
# Mutable run state
###########################################################################################################################################################################################################
DRY_RUN=0
ACTION=""
WANT_CASCOR=0
WANT_RECURRENCE=0
WANT_BRIDGE=0
ALL_MINE=0
CONFIG_PATH=""
EXPERIMENT=""
SHARED_DATA_URL=""
TARGET_RUN_ID=""

RUN_ID=""
RUN_DIR=""
LOG_DIR=""
DATA_PORT=""
CASCOR_PORT=""
RECURRENCE_PORT=""
DATA_URL=""
GATEWAY_IP=""

HELD_LOCK_PORTS=()
SCRAPE_TARGETS=()


###########################################################################################################################################################################################################
# Utility functions
###########################################################################################################################################################################################################
usage() {
    cat <<USAGE
${SCRIPT_NAME} — per-run experiment stack (data ${DATA_PORT_MIN}-${DATA_PORT_MAX} / cascor ${CASCOR_PORT_MIN}-${CASCOR_PORT_MAX} / recurrence ${RECURRENCE_PORT_MIN}-${RECURRENCE_PORT_MAX})

Usage: ${SCRIPT_NAME} --up (--cascor | --recurrence) [--shared-data URL] [--config PATH] [--experiment NAME] [--grafana-bridge] [--dry-run]
       ${SCRIPT_NAME} --down (RUN_ID | --all-mine) [--dry-run]
       ${SCRIPT_NAME} --status [RUN_ID] [--dry-run]
       ${SCRIPT_NAME} --help

  --up               Allocate ports and launch data -> cascor -> recurrence (health-gated).
  --cascor           Include juniper-cascor (cascor arm = data + cascor).
  --recurrence       Include juniper-recurrence (recurrence arm = data + recurrence).
  --shared-data URL  Reuse an existing juniper-data instead of launching a per-run one.
  --config PATH      Stage an experiment YAML into the run dir (app-side YAML is Wave 3).
  --experiment NAME  Prometheus 'experiment' target label (default: config basename).
  --grafana-bridge   OPT-IN: start socat relays and write the Prometheus target file.
  --down RUN_ID      Tear down a run (pidfile-first); --all-mine tears down every run.
  --status [RUN_ID]  Probe a run, or list every run under the run root.
  --dry-run          Print every command without executing it (creates/kills nothing).
  --help,-h          Print this help.

Run root : ${RUN_ROOT}
Lock root: ${LOCK_ROOT}
Targets  : ${TARGETS_DIR}

See juniper-ml notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md §6.2 for the full contract.
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

# Absolute path to a binary inside a conda env (direct-bin launch form; see CONDA above).
env_bin() {
    local env_name="$1" bin_name="$2"
    printf '%s' "${CONDA_DIR}/envs/${env_name}/bin/${bin_name}"
}

# Source conda + activate an env (nounset-safe, matching juniper_plant_all.bash /
# isolated_stack.bash). Only reached under JUNIPER_EXP_CONDA_ACTIVATE=1.
#
# Fail-closed on ``source`` / ``conda activate``: callers invoke this as
# ``activate_conda … || return 1`` inside ``*_up || failed=1``, which disables
# ``set -e`` for the whole body (bash OR-list rule). A bare ``conda activate``
# failure followed by a successful ``set -u`` would otherwise return 0 and let
# the service launch on the ambient PATH.
activate_conda() {
    local env_name="$1"
    if [[ ! -f "${CONDA_SH}" ]]; then
        log "ERROR: conda not found at ${CONDA_SH} (set JUNIPER_EXP_CONDA_DIR)"
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

# Verify the launch env exists before promising a launch line that cannot run.
require_env_bin() {
    local env_name="$1" bin_name="$2" path
    path="$(env_bin "${env_name}" "${bin_name}")"
    if [[ ! -x "${path}" ]]; then
        log "ERROR: ${bin_name} not found in conda env '${env_name}' (${path})"
        return 1
    fi
}


###########################################################################################################################################################################################################
# Port helpers
###########################################################################################################################################################################################################
# PID of whatever holds the LISTEN socket on a TCP port (empty if nothing / ss unavailable).
port_listener_pid() {
    local port="$1" out
    out="$(ss -tlnpH "sport = :${port}" 2>/dev/null | grep -oE 'pid=[0-9]+' | head -n1 | cut -d= -f2 || true)"
    printf '%s' "${out}"
}

# True when anything at all is listening on the port (no pid privileges required).
port_in_use() {
    local port="$1" out
    out="$(ss -tlnH "sport = :${port}" 2>/dev/null || true)"
    [[ -n "${out}" ]]
}

# Allocate the first free port in [min,max] and hold its lockdir for the run.
#
# Sets the global ALLOCATED_PORT (rather than printing) so the HELD_LOCK_PORTS append is
# not lost to a command-substitution subshell.
#
# `mkdir` is atomic, so the lockdir SERIALISES experiment launchers against each other.
# It cannot serialise us against a third party that is not participating in the protocol:
# a foreign process may still bind the port between our `ss` probe and the service's own
# bind. That residual race is deliberately NOT papered over — it surfaces as the service's
# own bind failure, which the health gate turns into a loud timeout (plan H-1).
ALLOCATED_PORT=""
allocate_port() {
    local svc="$1" min="$2" max="$3" port lockdir
    ALLOCATED_PORT=""
    port="${min}"
    while (( port <= max )); do
        lockdir="${LOCK_ROOT}/${port}.lock"
        if is_dry; then
            # A dry run takes NO lock and creates NO directory; it only reports which port
            # the live run would pick, using the same read-only ss probe.
            if [[ ! -d "${lockdir}" ]] && ! port_in_use "${port}"; then
                ALLOCATED_PORT="${port}"
                return 0
            fi
        elif mkdir "${lockdir}" 2>/dev/null; then
            if port_in_use "${port}"; then
                rmdir "${lockdir}" 2>/dev/null || true
            else
                HELD_LOCK_PORTS+=("${port}")
                ALLOCATED_PORT="${port}"
                return 0
            fi
        fi
        port=$(( port + 1 ))
    done
    log "ERROR: no free ${svc} port in ${min}-${max} (all locked or in use)"
    return 1
}

release_port_lock() {
    local port="$1"
    [[ -n "${port}" ]] || return 0
    announce "rmdir ${LOCK_ROOT}/${port}.lock   # release the port lock"
    if is_dry; then return 0; fi
    rmdir "${LOCK_ROOT}/${port}.lock" 2>/dev/null || true
}

release_held_locks() {
    local port
    for port in "${HELD_LOCK_PORTS[@]:-}"; do
        [[ -n "${port}" ]] || continue
        rmdir "${LOCK_ROOT}/${port}.lock" 2>/dev/null || true
    done
    HELD_LOCK_PORTS=()
}


###########################################################################################################################################################################################################
# Process helpers
###########################################################################################################################################################################################################
proc_cmdline() {
    local pid="$1"
    tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null || true
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

# Record the AUTHORITATIVE pid for a service, resolved from the LISTENER after the health
# gate has proven the port is bound.
#
# F-6 (P0 preflight evidence): `$!` taken after `( cd … && nohup <server> … & )` is the
# backgrounded SUBSHELL, not the server — during Wave 0 all three "recorded" pids died on
# signal while the servers lived on. So the launcher never records `$!` for a service; it
# asks `ss -tlnpH "sport = :<port>"` who actually owns the listening socket, and stores the
# process' cmdline alongside so teardown can prove identity before it kills anything.
record_listener_pid() {
    local svc="$1" port="$2" pid
    pid="$(port_listener_pid "${port}")"
    if [[ -z "${pid}" ]]; then
        log "ERROR: ${svc} answered health on ${port} but no listener pid resolved via ss"
        return 1
    fi
    printf '%s\n' "${pid}" >"${RUN_DIR}/${svc}.pid"
    proc_cmdline "${pid}" >"${RUN_DIR}/${svc}.cmdline"
    log "${svc}: listener pid ${pid} recorded -> ${RUN_DIR}/${svc}.pid"
}

# SIGTERM then a bounded SIGKILL, only after the pid is proven to be ours and unchanged.
terminate_pid() {
    local pid="$1" label="$2" waited=0
    log "Stopping ${label} (pid ${pid}) with SIGTERM"
    kill -TERM "${pid}" 2>/dev/null || true
    while (( waited < KILL_TIMEOUT )); do
        if ! kill -0 "${pid}" 2>/dev/null; then
            log "${label}: pid ${pid} exited after ${waited}s"
            return 0
        fi
        sleep 1
        waited=$(( waited + 1 ))
    done
    log "${label}: pid ${pid} still alive after ${KILL_TIMEOUT}s — sending SIGKILL"
    kill -KILL "${pid}" 2>/dev/null || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
        log "ERROR: ${label}: pid ${pid} survived SIGKILL"
        return 1
    fi
    return 0
}

# Kill a pid only if it is alive, owned by the current user, and still running the exact
# cmdline recorded at launch (pid-reuse guard). Returns 1 when it refuses, so the caller
# can fall back to the recorded port.
kill_verified_pid() {
    local pid="$1" label="$2" recorded="$3" owner live
    if [[ ! "${pid}" =~ ^[0-9]+$ ]]; then
        log "${label}: recorded pid '${pid}' is not a number — refusing to kill"
        return 1
    fi
    if ! kill -0 "${pid}" 2>/dev/null; then
        log "${label}: recorded pid ${pid} is not alive (already gone)"
        return 0
    fi
    owner="$(stat -c '%u' "/proc/${pid}" 2>/dev/null || true)"
    if [[ "${owner}" != "$(id -u)" ]]; then
        log "${label}: pid ${pid} is owned by uid '${owner:-unknown}', not $(id -u) — refusing to kill"
        return 1
    fi
    live="$(proc_cmdline "${pid}")"
    if [[ -n "${recorded}" && "${live}" != "${recorded}" ]]; then
        log "${label}: pid ${pid} cmdline changed since launch — refusing to kill (pid reuse)"
        return 1
    fi
    terminate_pid "${pid}" "${label}"
}


###########################################################################################################################################################################################################
# Run directory (§6.4)
###########################################################################################################################################################################################################
new_run_id() {
    local rand
    if command -v openssl >/dev/null 2>&1; then
        rand="$(openssl rand -hex 2)"
    else
        rand="$(printf '%04x' $(( RANDOM % 65536 )))"
    fi
    printf '%s-%s' "$(date -u +%Y%m%dT%H%M%SZ)" "${rand}"
}

create_run_dir() {
    announce "mkdir -p ${RUN_DIR}/{logs,relays,config,env,data,equities-cache,artifacts/plots,artifacts/results}"
    if is_dry; then return 0; fi
    ensure_dir "${RUN_DIR}"
    ensure_dir "${LOG_DIR}"
    ensure_dir "${RUN_DIR}/relays"
    ensure_dir "${RUN_DIR}/config"
    ensure_dir "${RUN_DIR}/env"
    ensure_dir "${RUN_DIR}/data"
    ensure_dir "${RUN_DIR}/equities-cache"
    ensure_dir "${RUN_DIR}/artifacts/plots"
    ensure_dir "${RUN_DIR}/artifacts/results"
}

stage_config() {
    [[ -n "${CONFIG_PATH}" ]] || return 0
    announce "cp ${CONFIG_PATH} ${RUN_DIR}/config/experiment.yaml"
    if is_dry; then return 0; fi
    if [[ ! -f "${CONFIG_PATH}" ]]; then
        log "ERROR: --config file not found: ${CONFIG_PATH}"
        return 1
    fi
    cp "${CONFIG_PATH}" "${RUN_DIR}/config/experiment.yaml"
}

json_number_or_null() {
    local value="$1"
    if [[ -n "${value}" ]]; then printf '%s' "${value}"; else printf 'null'; fi
}

json_string_or_null() {
    local value="$1"
    if [[ -n "${value}" ]]; then printf '"%s"' "${value}"; else printf 'null'; fi
}

# ports.json is written BEFORE the launches so a bring-up that dies mid-flight still leaves
# teardown a record of exactly which ports this run may touch.
write_ports_json() {
    local bridge="false"
    (( WANT_BRIDGE == 1 )) && bridge="true"
    announce "write ${RUN_DIR}/ports.json   # {\"data\":$(json_number_or_null "${DATA_PORT}"),\"cascor\":$(json_number_or_null "${CASCOR_PORT}"),\"recurrence\":$(json_number_or_null "${RECURRENCE_PORT}")}"
    if is_dry; then return 0; fi
    cat >"${RUN_DIR}/ports.json" <<PORTS
{
  "run_id": "${RUN_ID}",
  "data": $(json_number_or_null "${DATA_PORT}"),
  "cascor": $(json_number_or_null "${CASCOR_PORT}"),
  "recurrence": $(json_number_or_null "${RECURRENCE_PORT}"),
  "data_url": "${DATA_URL}",
  "experiment": "${EXPERIMENT}",
  "grafana_bridge": ${bridge}
}
PORTS
}

# Read one numeric port from a run's ports.json without a jq dependency.
read_run_port() {
    local file="$1" key="$2" value
    value="$(sed -n "s/^[[:space:]]*\"${key}\"[[:space:]]*:[[:space:]]*\([0-9]\{1,\}\).*/\1/p" "${file}" 2>/dev/null | head -n1 || true)"
    printf '%s' "${value}"
}

read_run_flag() {
    local file="$1" key="$2" value
    value="$(sed -n "s/^[[:space:]]*\"${key}\"[[:space:]]*:[[:space:]]*\(true\|false\).*/\1/p" "${file}" 2>/dev/null | head -n1 || true)"
    printf '%s' "${value}"
}

# The exact env each service was launched with (§6.4 env/launch.env). No secrets are ever
# placed in these variables, but the file is written 0600 to keep the habit.
record_launch_env() {
    local svc="$1"
    shift
    if is_dry; then return 0; fi
    ensure_dir "${RUN_DIR}/env"
    {
        printf '# %s\n' "${svc}"
        printf '%s\n' "$@"
    } >>"${RUN_DIR}/env/launch.env"
    chmod 600 "${RUN_DIR}/env/launch.env" 2>/dev/null || true
}


###########################################################################################################################################################################################################
# Bring-up: juniper-data (dedicated per-run instance, plan §6.1)
###########################################################################################################################################################################################################
data_up() {
    local python_bin
    python_bin="$(env_bin "${DATA_CONDA}" python)"
    banner "juniper-data  ->  http://127.0.0.1:${DATA_PORT}  (${DATA_CONDA}, per-run instance)"
    announce "cd ${RUN_DIR} && JUNIPER_DATA_STORAGE_PATH=${RUN_DIR}/data JUNIPER_DATA_METRICS_ENABLED=true JUNIPER_DATA_EQUITIES_CACHE_DIR=${RUN_DIR}/equities-cache PYTHON_GIL=0 ${python_bin} -m juniper_data --host 127.0.0.1 --port ${DATA_PORT}   # nohup -> ${LOG_DIR}/juniper-data.log"
    if is_dry; then return 0; fi

    # Explicit ``|| return 1``: do_up invokes this as ``data_up || failed=1``, which
    # disables set -e for the whole body (bash OR-list rule). Without these checks a
    # health-timeout with a live listener would fall through to record_listener_pid
    # (exit 0) and false-green the bring-up — orphaning the process with no teardown.
    require_env_bin "${DATA_CONDA}" python || return 1
    ensure_dir "${LOG_DIR}"
    record_launch_env "juniper-data" \
        "JUNIPER_DATA_STORAGE_PATH=${RUN_DIR}/data" \
        "JUNIPER_DATA_METRICS_ENABLED=true" \
        "JUNIPER_DATA_EQUITIES_CACHE_DIR=${RUN_DIR}/equities-cache" \
        "PYTHON_GIL=0"
    if [[ "${CONDA_ACTIVATE}" == "1" ]]; then activate_conda "${DATA_CONDA}" || return 1; fi
    (
        cd "${RUN_DIR}" || exit 1
        JUNIPER_DATA_STORAGE_PATH="${RUN_DIR}/data" \
            JUNIPER_DATA_METRICS_ENABLED=true \
            JUNIPER_DATA_EQUITIES_CACHE_DIR="${RUN_DIR}/equities-cache" \
            PYTHON_GIL=0 \
            nohup "${python_bin}" -m juniper_data --host 127.0.0.1 --port "${DATA_PORT}" >"${LOG_DIR}/juniper-data.log" 2>&1 &
    )
    # No `$!` here on purpose — F-6. The pid is resolved from the listener below.
    wait_for_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health" || return 1
    record_listener_pid "juniper-data" "${DATA_PORT}" || return 1
}


###########################################################################################################################################################################################################
# Bring-up: juniper-cascor (uvicorn factory CLI owns the bind, plan §6.1)
###########################################################################################################################################################################################################
cascor_up() {
    local uvicorn_bin config_env=""
    uvicorn_bin="$(env_bin "${CASCOR_CONDA}" uvicorn)"
    [[ -n "${CONFIG_PATH}" ]] && config_env="JUNIPER_CASCOR_CONFIG_FILE=${RUN_DIR}/config/experiment.yaml "
    banner "juniper-cascor  ->  http://127.0.0.1:${CASCOR_PORT}  (${CASCOR_CONDA})"
    announce "cd ${CASCOR_SRC_DIR} && LD_LIBRARY_PATH= JUNIPER_CASCOR_METRICS_ENABLED=true JUNIPER_CASCOR_AUTO_START=false JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false JUNIPER_CASCOR_LOG_LEVEL=INFO JUNIPER_DATA_URL=${DATA_URL} ${config_env}${uvicorn_bin} api.app:create_app --factory --host 127.0.0.1 --port ${CASCOR_PORT}   # nohup -> ${LOG_DIR}/juniper-cascor.log"
    if is_dry; then return 0; fi

    # See data_up: ``cascor_up || failed=1`` disables set -e inside this body.
    require_env_bin "${CASCOR_CONDA}" uvicorn || return 1
    ensure_dir "${LOG_DIR}"
    record_launch_env "juniper-cascor" \
        "LD_LIBRARY_PATH=" \
        "JUNIPER_CASCOR_METRICS_ENABLED=true" \
        "JUNIPER_CASCOR_AUTO_START=false" \
        "JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false" \
        "JUNIPER_CASCOR_LOG_LEVEL=INFO" \
        "JUNIPER_DATA_URL=${DATA_URL}" \
        "JUNIPER_CASCOR_CONFIG_FILE=${CONFIG_PATH:+${RUN_DIR}/config/experiment.yaml}"
    if [[ "${CONDA_ACTIVATE}" == "1" ]]; then activate_conda "${CASCOR_CONDA}" || return 1; fi
    (
        cd "${CASCOR_SRC_DIR}" || exit 1
        LD_LIBRARY_PATH='' \
            JUNIPER_CASCOR_METRICS_ENABLED=true \
            JUNIPER_CASCOR_AUTO_START=false \
            JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false \
            JUNIPER_CASCOR_LOG_LEVEL=INFO \
            JUNIPER_DATA_URL="${DATA_URL}" \
            JUNIPER_CASCOR_CONFIG_FILE="${CONFIG_PATH:+${RUN_DIR}/config/experiment.yaml}" \
            nohup "${uvicorn_bin}" api.app:create_app --factory --host 127.0.0.1 --port "${CASCOR_PORT}" >"${LOG_DIR}/juniper-cascor.log" 2>&1 &
    )
    # No `$!` here on purpose — F-6.
    wait_for_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health" || return 1
    record_listener_pid "juniper-cascor" "${CASCOR_PORT}" || return 1
}


###########################################################################################################################################################################################################
# Bring-up: juniper-recurrence (console script, plan §6.1)
###########################################################################################################################################################################################################
recurrence_up() {
    local serve_bin
    serve_bin="$(env_bin "${RECURRENCE_CONDA}" juniper-recurrence)"
    banner "juniper-recurrence  ->  http://127.0.0.1:${RECURRENCE_PORT}  (${RECURRENCE_CONDA})"
    announce "cd ${RUN_DIR} && JUNIPER_RECURRENCE_METRICS_ENABLED=true JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false JUNIPER_DATA_URL=${DATA_URL} ${serve_bin} serve --host 127.0.0.1 --port ${RECURRENCE_PORT}   # nohup -> ${LOG_DIR}/juniper-recurrence.log"
    if is_dry; then return 0; fi

    # See data_up: ``recurrence_up || failed=1`` disables set -e inside this body.
    require_env_bin "${RECURRENCE_CONDA}" juniper-recurrence || return 1
    ensure_dir "${LOG_DIR}"
    if [[ -n "${CONFIG_PATH}" ]]; then
        log "NOTE: juniper-recurrence serve has no --config flag yet (Wave 3.3); the YAML is staged at ${RUN_DIR}/config/experiment.yaml only"
    fi
    record_launch_env "juniper-recurrence" \
        "JUNIPER_RECURRENCE_METRICS_ENABLED=true" \
        "JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false" \
        "JUNIPER_DATA_URL=${DATA_URL}"
    if [[ "${CONDA_ACTIVATE}" == "1" ]]; then activate_conda "${RECURRENCE_CONDA}" || return 1; fi
    (
        cd "${RUN_DIR}" || exit 1
        JUNIPER_RECURRENCE_METRICS_ENABLED=true \
            JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false \
            JUNIPER_DATA_URL="${DATA_URL}" \
            nohup "${serve_bin}" serve --host 127.0.0.1 --port "${RECURRENCE_PORT}" >"${LOG_DIR}/juniper-recurrence.log" 2>&1 &
    )
    # No `$!` here on purpose — F-6.
    wait_for_health "juniper-recurrence" "http://127.0.0.1:${RECURRENCE_PORT}/v1/health/ready" || return 1
    record_listener_pid "juniper-recurrence" "${RECURRENCE_PORT}" || return 1
}


###########################################################################################################################################################################################################
# Grafana bridge (OPT-IN, plan §7.2 / §7.3) — socat relays + the file_sd target file
###########################################################################################################################################################################################################
# Discover the gateway IP the relays bind. The monitoring network is found by SUFFIX, never
# by a hard-coded compose project name: a stack launched from a worktree renames the network
# (<project>_monitoring), while the pinned ipam keeps the gateway constant.
discover_gateway_ip() {
    local net ip
    GATEWAY_IP=""
    net="$(docker network ls --format '{{.Name}}' 2>/dev/null | grep -E '_monitoring$' | head -n1 || true)"
    if [[ -n "${net}" ]]; then
        ip="$(docker network inspect "${net}" --format '{{range .IPAM.Config}}{{.Gateway}} {{end}}' 2>/dev/null | awk '{print $1}' || true)"
        if [[ -n "${ip}" ]]; then
            GATEWAY_IP="${ip}"
            log "Monitoring network '${net}' gateway: ${GATEWAY_IP}"
            return 0
        fi
    fi
    ip="$(docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}} {{end}}' 2>/dev/null | awk '{print $1}' || true)"
    if [[ -z "${ip}" ]]; then
        log "ERROR: no monitoring network and no default-bridge gateway — cannot start the Grafana bridge"
        return 1
    fi
    GATEWAY_IP="${ip}"
    log "WARNING: no '*_monitoring' docker network found — falling back to the DEFAULT BRIDGE gateway ${GATEWAY_IP}."
    log "WARNING: prometheus maps host.docker.internal to the MONITORING gateway explicitly (F-2), so scrapes will NOT land until the observability stack is up."
}

relay_up() {
    local svc="$1" port="$2"
    announce "socat \"TCP-LISTEN:${port},bind=${GATEWAY_IP},fork,reuseaddr\" \"TCP:127.0.0.1:${port}\"   # ${svc} relay -> ${RUN_DIR}/relays/${svc}.pid"
    if is_dry; then return 0; fi
    ensure_dir "${RUN_DIR}/relays"
    # socat is exec'd directly (no `cd &&` subshell), so `$!` IS the relay process here —
    # the F-6 wrapper-pid class does not apply. The relay also never binds 127.0.0.1, so
    # `ss -tlnpH "sport = :<port>"` could not disambiguate it from the app anyway.
    nohup socat "TCP-LISTEN:${port},bind=${GATEWAY_IP},fork,reuseaddr" "TCP:127.0.0.1:${port}" >"${LOG_DIR}/relay-${svc}.log" 2>&1 &
    printf '%s\n' "$!" >"${RUN_DIR}/relays/${svc}.pid"
    proc_cmdline "$!" >"${RUN_DIR}/relays/${svc}.cmdline"
    log "${svc}: relay pid $(cat "${RUN_DIR}/relays/${svc}.pid") on ${GATEWAY_IP}:${port}"
}

# The §7.2 target file: one entry per scraped service, four labels, run-scoped.
render_target_file() {
    local first=1 entry svc port
    printf '[\n'
    for entry in "${SCRAPE_TARGETS[@]:-}"; do
        [[ -n "${entry}" ]] || continue
        svc="${entry%%:*}"
        port="${entry##*:}"
        (( first == 1 )) || printf ',\n'
        first=0
        printf '  {\n'
        printf '    "targets": ["host.docker.internal:%s"],\n' "${port}"
        printf '    "labels": {\n'
        printf '      "service": "%s",\n' "${svc}"
        printf '      "environment": "host-experiment",\n'
        printf '      "run_id": "%s",\n' "${RUN_ID}"
        printf '      "experiment": "%s"\n' "${EXPERIMENT}"
        printf '    }\n'
        printf '  }'
    done
    printf '\n]\n'
}

bridge_up() {
    local entry svc port
    banner "Grafana bridge (opt-in): relays + Prometheus target file"
    # Explicit ``|| return 1``: do_up invokes this as ``if ! bridge_up``, which
    # disables set -e for the whole body (bash conditional rule). Without these
    # checks a missing socat/docker would fall through and still write a target.
    require_cmd socat || return 1
    require_cmd docker || return 1
    if is_dry; then
        GATEWAY_IP="<monitoring-gateway>"
        announce "docker network ls --format '{{.Name}}' | grep -E '_monitoring\$'   # discover the monitoring network by SUFFIX"
    else
        # Explicit ``|| return 1``: callers that invoke bridge_up under ``if ! bridge_up``
        # (OR-list / conditional) disable set -e for this whole body. Without the guard a
        # discover failure leaves GATEWAY_IP empty and falls through to relay_up / target
        # write — a false-green bridge with a broken bind.
        discover_gateway_ip || return 1
    fi
    for entry in "${SCRAPE_TARGETS[@]:-}"; do
        [[ -n "${entry}" ]] || continue
        svc="${entry%%:*}"
        port="${entry##*:}"
        relay_up "${svc}" "${port}" || return 1
    done
    announce "write ${TARGETS_DIR}/${RUN_ID}.json   # file_sd target, labels: service/environment/run_id/experiment"
    if is_dry; then return 0; fi
    ensure_dir "${TARGETS_DIR}"
    render_target_file >"${TARGETS_DIR}/${RUN_ID}.json" || return 1
    render_target_file >"${RUN_DIR}/artifacts/prometheus_target.json" || return 1
    log "Prometheus target file: ${TARGETS_DIR}/${RUN_ID}.json (picked up within refresh_interval)"
}

bridge_down() {
    local pidfile svc pid recorded
    announce "rm -f ${TARGETS_DIR}/${TARGET_RUN_ID}.json   # stop scraping this run"
    if ! is_dry; then
        rm -f "${TARGETS_DIR}/${TARGET_RUN_ID}.json" || true
    fi
    [[ -d "${RUN_DIR}/relays" ]] || return 0
    for pidfile in "${RUN_DIR}"/relays/*.pid; do
        [[ -e "${pidfile}" ]] || continue
        svc="$(basename "${pidfile}" .pid)"
        announce "kill \$(cat ${pidfile})   # ${svc} relay"
        if is_dry; then continue; fi
        pid="$(cat "${pidfile}" 2>/dev/null || true)"
        recorded="$(cat "${RUN_DIR}/relays/${svc}.cmdline" 2>/dev/null || true)"
        kill_verified_pid "${pid}" "relay/${svc}" "${recorded}" || true
        rm -f "${pidfile}" "${RUN_DIR}/relays/${svc}.cmdline" || true
    done
}


###########################################################################################################################################################################################################
# Action: --up
###########################################################################################################################################################################################################
do_up() {
    RUN_ID="$(new_run_id)"
    RUN_DIR="${RUN_ROOT}/${RUN_ID}"
    LOG_DIR="${RUN_DIR}/logs"
    [[ -n "${EXPERIMENT}" ]] || EXPERIMENT="adhoc"

    banner "Bringing UP experiment run ${RUN_ID}"
    if is_dry; then log "DRY-RUN: printing commands only — no dirs, no locks, no processes, no target file"; fi
    log "run dir  : ${RUN_DIR}"
    log "lock root: ${LOCK_ROOT}"

    if ! is_dry; then
        require_cmd ss
        require_cmd curl
        ensure_dir "${RUN_ROOT}"
        ensure_dir "${LOCK_ROOT}"
    fi

    # --- port allocation (§9.3) ------------------------------------------------------
    # release_held_locks on allocate failure: a mid-range exhaustion under set -e used to
    # exit do_up while earlier *.lock dirs stayed behind (30-port ranges starve later --up).
    if [[ -n "${SHARED_DATA_URL}" ]]; then
        DATA_URL="${SHARED_DATA_URL}"
        log "Reusing shared juniper-data at ${DATA_URL} (no per-run data instance)"
    else
        allocate_port "juniper-data" "${DATA_PORT_MIN}" "${DATA_PORT_MAX}" || {
            release_held_locks
            return 1
        }
        DATA_PORT="${ALLOCATED_PORT}"
        DATA_URL="http://127.0.0.1:${DATA_PORT}"
        log "allocated juniper-data port ${DATA_PORT} (range ${DATA_PORT_MIN}-${DATA_PORT_MAX})"
    fi
    if (( WANT_CASCOR == 1 )); then
        allocate_port "juniper-cascor" "${CASCOR_PORT_MIN}" "${CASCOR_PORT_MAX}" || {
            release_held_locks
            return 1
        }
        CASCOR_PORT="${ALLOCATED_PORT}"
        log "allocated juniper-cascor port ${CASCOR_PORT} (range ${CASCOR_PORT_MIN}-${CASCOR_PORT_MAX})"
    fi
    if (( WANT_RECURRENCE == 1 )); then
        allocate_port "juniper-recurrence" "${RECURRENCE_PORT_MIN}" "${RECURRENCE_PORT_MAX}" || {
            release_held_locks
            return 1
        }
        RECURRENCE_PORT="${ALLOCATED_PORT}"
        log "allocated juniper-recurrence port ${RECURRENCE_PORT} (range ${RECURRENCE_PORT_MIN}-${RECURRENCE_PORT_MAX})"
    fi

    SCRAPE_TARGETS=()
    [[ -n "${DATA_PORT}" ]] && SCRAPE_TARGETS+=("juniper-data:${DATA_PORT}")
    [[ -n "${CASCOR_PORT}" ]] && SCRAPE_TARGETS+=("juniper-cascor:${CASCOR_PORT}")
    [[ -n "${RECURRENCE_PORT}" ]] && SCRAPE_TARGETS+=("juniper-recurrence:${RECURRENCE_PORT}")

    # release_held_locks on staging failure: under set -e a missing --config (or mkdir/cp
    # failure) used to exit do_up after allocate_port had already created *.lock dirs, and
    # ports.json was not written yet — so --down cannot recover the locks either. The
    # 30-port experiment ranges then starve later --up attempts until lockdirs are removed
    # by hand (or the runtime dir is reaped).
    create_run_dir || {
        release_held_locks
        return 1
    }
    stage_config || {
        release_held_locks
        return 1
    }
    write_ports_json || {
        release_held_locks
        return 1
    }

    # --- launches, in deterministic order data -> cascor -> recurrence ----------------
    local failed=0
    if [[ -z "${SHARED_DATA_URL}" ]]; then
        data_up || failed=1
    fi
    if (( failed == 0 && WANT_CASCOR == 1 )); then cascor_up || failed=1; fi
    if (( failed == 0 && WANT_RECURRENCE == 1 )); then recurrence_up || failed=1; fi

    if (( failed == 1 )); then
        log "ERROR: bring-up failed — tearing the partial run back down (logs kept under ${LOG_DIR})"
        if ! is_dry; then
            TARGET_RUN_ID="${RUN_ID}"
            teardown_run "${RUN_ID}"
        fi
        return 1
    fi

    # Bridge is post-success: a bare ``bridge_up`` failure under ``set -e`` would
    # abort the script without teardown_run, orphaning the already-healthy stack.
    if (( WANT_BRIDGE == 1 )); then
        if ! bridge_up; then
            log "ERROR: grafana bridge failed — tearing the run back down (logs kept under ${LOG_DIR})"
            if ! is_dry; then
                TARGET_RUN_ID="${RUN_ID}"
                teardown_run "${RUN_ID}"
            fi
            return 1
        fi
    else
        log "Grafana bridge OFF — this run is UNSCRAPED (no relay, no target file). Re-run with --grafana-bridge to publish it."
    fi

    banner "Experiment run ${RUN_ID} is up"
    log "run dir    : ${RUN_DIR}"
    [[ -n "${DATA_PORT}" ]] && log "data       : ${DATA_URL}/v1/health"
    [[ -z "${DATA_PORT}" ]] && log "data       : ${DATA_URL} (shared, not managed by this run)"
    [[ -n "${CASCOR_PORT}" ]] && log "cascor     : http://127.0.0.1:${CASCOR_PORT}/v1/health"
    [[ -n "${RECURRENCE_PORT}" ]] && log "recurrence : http://127.0.0.1:${RECURRENCE_PORT}/v1/health/ready"
    log "teardown   : ${SCRIPT_NAME} --down ${RUN_ID}"
}


###########################################################################################################################################################################################################
# Action: --down
###########################################################################################################################################################################################################
# Stop one service: recorded pid FIRST (verified), then kill-by-port as a fallback that is
# confined to the port this run recorded.
stop_service() {
    local svc="$1" port="$2"
    local pidfile="${RUN_DIR}/${svc}.pid"
    local pid recorded fallback_pid
    if [[ -f "${pidfile}" ]]; then
        pid="$(cat "${pidfile}" 2>/dev/null || true)"
        recorded="$(cat "${RUN_DIR}/${svc}.cmdline" 2>/dev/null || true)"
        announce "kill \$(cat ${pidfile})   # ${svc}: recorded listener pid first"
        if ! is_dry; then
            if kill_verified_pid "${pid}" "${svc}" "${recorded}"; then
                rm -f "${pidfile}" "${RUN_DIR}/${svc}.cmdline" || true
            else
                log "${svc}: pidfile path refused — falling back to the recorded port ${port:-none}"
            fi
        fi
    else
        log "${svc}: no pidfile recorded"
    fi

    [[ -n "${port}" ]] || return 0
    announce "kill \$(ss -tlnpH \"sport = :${port}\" | grep -oE 'pid=[0-9]+' | cut -d= -f2)   # ${svc}: fallback, ONLY this run's recorded port"
    if is_dry; then return 0; fi
    fallback_pid="$(port_listener_pid "${port}")"
    if [[ -n "${fallback_pid}" ]]; then
        kill_verified_pid "${fallback_pid}" "${svc} (by port ${port})" "" || true
    fi
    if port_in_use "${port}"; then
        log "WARNING: ${svc}: port ${port} still has a listener after teardown — inspect it before reusing the range"
    fi
}

write_teardown_json() {
    local stopped="$1" ports="$2"
    if is_dry; then return 0; fi
    [[ -d "${RUN_DIR}" ]] || return 0
    cat >"${RUN_DIR}/teardown.json" <<TEARDOWN
{
  "run_id": "${TARGET_RUN_ID}",
  "torn_down_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "services_stopped": [${stopped}],
  "ports_released": [${ports}],
  "target_file_removed": "${TARGETS_DIR}/${TARGET_RUN_ID}.json",
  "artifacts_kept": "${RUN_DIR}/artifacts"
}
TEARDOWN
}

teardown_run() {
    local run_id="$1" ports_file data_port cascor_port recurrence_port stopped=() released=()
    TARGET_RUN_ID="${run_id}"
    RUN_DIR="${RUN_ROOT}/${run_id}"
    LOG_DIR="${RUN_DIR}/logs"
    ports_file="${RUN_DIR}/ports.json"

    banner "Tearing DOWN experiment run ${run_id}"
    if [[ ! -d "${RUN_DIR}" ]]; then
        log "ERROR: no such run dir: ${RUN_DIR}"
        return 1
    fi
    if [[ ! -f "${ports_file}" ]]; then
        log "WARNING: ${run_id} has no ports.json — pidfile-only teardown"
    fi
    data_port="$(read_run_port "${ports_file}" data)"
    cascor_port="$(read_run_port "${ports_file}" cascor)"
    recurrence_port="$(read_run_port "${ports_file}" recurrence)"

    # Relays + target file first: stop publishing before the endpoints disappear.
    bridge_down

    # Reverse of bring-up order: recurrence -> cascor -> data.
    if [[ -n "${recurrence_port}" || -f "${RUN_DIR}/juniper-recurrence.pid" ]]; then
        stop_service "juniper-recurrence" "${recurrence_port}"
        stopped+=("\"juniper-recurrence\"")
    fi
    if [[ -n "${cascor_port}" || -f "${RUN_DIR}/juniper-cascor.pid" ]]; then
        stop_service "juniper-cascor" "${cascor_port}"
        stopped+=("\"juniper-cascor\"")
    fi
    if [[ -n "${data_port}" || -f "${RUN_DIR}/juniper-data.pid" ]]; then
        stop_service "juniper-data" "${data_port}"
        stopped+=("\"juniper-data\"")
    fi

    local port
    for port in "${data_port}" "${cascor_port}" "${recurrence_port}"; do
        [[ -n "${port}" ]] || continue
        release_port_lock "${port}"
        released+=("${port}")
    done

    write_teardown_json "$(join_by , "${stopped[@]:-}")" "$(join_by , "${released[@]:-}")"
    log "Teardown complete for ${run_id}; artifacts kept at ${RUN_DIR}/artifacts (never deleted)"
}

join_by() {
    local sep="$1" out="" item
    shift
    for item in "$@"; do
        [[ -n "${item}" ]] || continue
        if [[ -z "${out}" ]]; then out="${item}"; else out="${out}${sep}${item}"; fi
    done
    printf '%s' "${out}"
}

do_down() {
    local run_dir run_id rc=0
    if (( ALL_MINE == 1 )); then
        if [[ ! -d "${RUN_ROOT}" ]]; then
            log "No run root at ${RUN_ROOT} — nothing to tear down"
            return 0
        fi
        for run_dir in "${RUN_ROOT}"/*/; do
            [[ -d "${run_dir}" ]] || continue
            run_id="$(basename "${run_dir}")"
            [[ "${run_id}" == .* ]] && continue
            teardown_run "${run_id}" || rc=1
        done
        return "${rc}"
    fi
    teardown_run "${TARGET_RUN_ID}"
}


###########################################################################################################################################################################################################
# Action: --status
###########################################################################################################################################################################################################
probe_service() {
    local name="$1" url="$2" port="$3" pidfile="$4" code pid recorded
    announce "curl -s -o /dev/null -w '%{http_code}' ${url}   # ${name}"
    if is_dry; then return 0; fi
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "${url}" 2>/dev/null || true)"
    pid="$(port_listener_pid "${port}")"
    recorded="$(cat "${pidfile}" 2>/dev/null || true)"
    log "${name}: health=${code:-000} port=${port} listener_pid=${pid:-none} recorded_pid=${recorded:-none}"
}

status_run() {
    local run_id="$1" ports_file data_port cascor_port recurrence_port bridge data_url
    RUN_DIR="${RUN_ROOT}/${run_id}"
    ports_file="${RUN_DIR}/ports.json"
    banner "Experiment run ${run_id}"
    if [[ ! -d "${RUN_DIR}" ]]; then
        log "ERROR: no such run dir: ${RUN_DIR}"
        return 1
    fi
    data_port="$(read_run_port "${ports_file}" data)"
    cascor_port="$(read_run_port "${ports_file}" cascor)"
    recurrence_port="$(read_run_port "${ports_file}" recurrence)"
    bridge="$(read_run_flag "${ports_file}" grafana_bridge)"
    data_url="$(sed -n 's/^[[:space:]]*"data_url"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p' "${ports_file}" 2>/dev/null | head -n1 || true)"

    log "run dir: ${RUN_DIR}"
    [[ -n "${data_port}" ]] && probe_service "juniper-data" "http://127.0.0.1:${data_port}/v1/health" "${data_port}" "${RUN_DIR}/juniper-data.pid"
    [[ -z "${data_port}" && -n "${data_url}" ]] && log "juniper-data: shared instance at ${data_url} (not managed by this run)"
    [[ -n "${cascor_port}" ]] && probe_service "juniper-cascor" "http://127.0.0.1:${cascor_port}/v1/health" "${cascor_port}" "${RUN_DIR}/juniper-cascor.pid"
    [[ -n "${recurrence_port}" ]] && probe_service "juniper-recurrence" "http://127.0.0.1:${recurrence_port}/v1/health/ready" "${recurrence_port}" "${RUN_DIR}/juniper-recurrence.pid"

    if [[ "${bridge}" == "true" && -f "${TARGETS_DIR}/${run_id}.json" ]]; then
        log "scrape: PUBLISHED — ${TARGETS_DIR}/${run_id}.json"
    elif [[ "${bridge}" == "true" ]]; then
        log "scrape: bridge was requested but ${TARGETS_DIR}/${run_id}.json is MISSING — this run is UNSCRAPED"
    else
        log "scrape: DISABLED — this run is UNSCRAPED (no Grafana bridge; re-run --up with --grafana-bridge)"
    fi
}

do_status() {
    local run_dir run_id rc=0
    if [[ -n "${TARGET_RUN_ID}" ]]; then
        status_run "${TARGET_RUN_ID}"
        return $?
    fi
    banner "Experiment runs under ${RUN_ROOT}"
    if [[ ! -d "${RUN_ROOT}" ]]; then
        log "No run root at ${RUN_ROOT} — no runs recorded"
        return 0
    fi
    for run_dir in "${RUN_ROOT}"/*/; do
        [[ -d "${run_dir}" ]] || continue
        run_id="$(basename "${run_dir}")"
        [[ "${run_id}" == .* ]] && continue
        status_run "${run_id}" || rc=1
    done
    return "${rc}"
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

need_value() {
    local flag="$1" value="${2-}"
    if [[ -z "${value}" || "${value}" == --* ]]; then
        log "ERROR: ${flag} requires a value"
        usage
        exit 2
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --up) set_action up ;;
        --down) set_action down ;;
        --status) set_action status ;;
        --cascor) WANT_CASCOR=1 ;;
        --recurrence) WANT_RECURRENCE=1 ;;
        --grafana-bridge) WANT_BRIDGE=1 ;;
        --all-mine) ALL_MINE=1 ;;
        --dry-run) DRY_RUN=1 ;;
        --config)
            need_value "--config" "${2-}"
            CONFIG_PATH="$2"
            shift
            ;;
        --experiment)
            need_value "--experiment" "${2-}"
            EXPERIMENT="$2"
            shift
            ;;
        --shared-data)
            need_value "--shared-data" "${2-}"
            SHARED_DATA_URL="$2"
            shift
            ;;
        --run-id)
            need_value "--run-id" "${2-}"
            TARGET_RUN_ID="$2"
            shift
            ;;
        --help | -h) usage; exit 0 ;;
        -*)
            log "ERROR: unknown argument '$1'"
            usage
            exit 2
            ;;
        *)
            if [[ -n "${TARGET_RUN_ID}" ]]; then
                log "ERROR: unexpected extra argument '$1'"
                usage
                exit 2
            fi
            TARGET_RUN_ID="$1"
            ;;
    esac
    shift
done

if [[ -z "${ACTION}" ]]; then
    log "ERROR: no action given (--up / --down / --status)"
    usage
    exit 2
fi

if [[ "${ACTION}" == "up" ]]; then
    if (( WANT_CASCOR == 0 && WANT_RECURRENCE == 0 )); then
        log "ERROR: --up needs at least one app selector (--cascor and/or --recurrence)"
        usage
        exit 2
    fi
    if [[ -n "${TARGET_RUN_ID}" ]]; then
        log "ERROR: --up allocates its own run id; '${TARGET_RUN_ID}' is not accepted"
        usage
        exit 2
    fi
    if [[ -n "${CONFIG_PATH}" && -z "${EXPERIMENT}" ]]; then
        EXPERIMENT="$(basename "${CONFIG_PATH}")"
        EXPERIMENT="${EXPERIMENT%.*}"
    fi
fi

if [[ "${ACTION}" == "down" ]]; then
    if (( ALL_MINE == 0 )) && [[ -z "${TARGET_RUN_ID}" ]]; then
        log "ERROR: --down needs a RUN_ID (or --all-mine)"
        usage
        exit 2
    fi
    if (( ALL_MINE == 1 )) && [[ -n "${TARGET_RUN_ID}" ]]; then
        log "ERROR: --down takes a RUN_ID or --all-mine, not both"
        usage
        exit 2
    fi
fi

case "${ACTION}" in
    up) do_up ;;
    down) do_down ;;
    status) do_status ;;
esac
