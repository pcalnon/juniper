#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-1 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Launch the isolated E2E cascor leg under a LIVE PARENT so the
#          concurrent experiment campaign's pre-run orphan reap cannot take it
#          down. Sibling of e2e_cascor_leg_restart.bash, which this supersedes
#          for long-running Phase-1 sessions.
#
# Why this exists (F-ML-001, upgraded in the 2026-08-11 Phase-1 segment-5
# session): the isolated cascor leg was killed three times in ~1h, each within
# ~2s of a concurrent experiment-campaign run directory being created. The
# reaper's predicate is (a) candidate: current-user python whose cmdline matches
# ``JuniperC[a-z0-9]+``, AND (b) orphan: ppid is 1 / ``systemd --user`` / parent
# gone. cascor_up launches via ``( cd … && nohup … & )``, so after the subshell
# exits the service is parentless BY DESIGN and matches (b). The data leg
# escapes (a) via its venv python path; canopy escapes (a) because its argv is a
# bare ``python main.py`` that never names JuniperCanopy1.
#
# The fix here targets (b) ONLY: this script stays resident as the service's
# parent, so the reaper classifies the leg as a live-parent KEEP. The uvicorn
# argv, the §6.1 env set, the port, the CWD, and the log destination are
# byte-identical to isolated_stack.bash cascor_up / e2e_cascor_leg_restart.bash,
# so nothing the E2E evidence observes about canopy<->cascor behaviour changes.
#
# NOTE this does NOT defend against a blanket killer (kill_all_pythons.bash and
# friends kill regardless of parentage). It defends against the orphan reaper,
# which is the mechanism F-ML-001 documents.
#
# F-6 pid rule: unlike cascor_up's subshell form, uvicorn is a DIRECT child
# here, so ``$!`` genuinely is the server pid and the pidfile is honest.
#
# Usage:
#   nohup bash util/ad-hoc/e2e_cascor_leg_supervise.bash >/dev/null 2>&1 &
#     (the supervisor itself becomes the orphan; its argv does not match the
#      reaper's JuniperC candidate gate, so it is never a candidate)
#
#   --restart   opt-in: relaunch the child if it exits. OFF by default so a
#               genuine cascor crash stays visible instead of being silently
#               papered over mid-run — every exit is logged either way.
#   --fg        run in the foreground (for interactive debugging).
#
#   Env overrides mirror isolated_stack.bash: JUNIPER_E2E_{DATA,CASCOR,CANOPY}_PORT,
#   JUNIPER_E2E_RUN_DIR, JUNIPER_E2E_PROJECT_DIR, JUNIPER_E2E_CONDA_DIR.

set -euo pipefail

RESTART=0
for arg in "$@"; do
    case "${arg}" in
        --restart) RESTART=1 ;;
        --fg) : ;;
        *) echo "ERROR: unknown flag ${arg}" >&2; exit 2 ;;
    esac
done

DATA_PORT="${JUNIPER_E2E_DATA_PORT:-8101}"
CASCOR_PORT="${JUNIPER_E2E_CASCOR_PORT:-8202}"
CANOPY_PORT="${JUNIPER_E2E_CANOPY_PORT:-8051}"
RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"
LOG_DIR="${RUN_DIR}/logs"
PROJECT_DIR="${JUNIPER_E2E_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
CASCOR_SRC_DIR="${PROJECT_DIR}/juniper-cascor/src"
CONDA_DIR="${JUNIPER_E2E_CONDA_DIR:-/opt/miniforge3}"
CASCOR_CONDA="JuniperCascor1"
CANOPY_ORIGIN="http://127.0.0.1:${CANOPY_PORT}"
SUP_LOG="${LOG_DIR}/juniper-cascor-supervisor.log"

if ss -tlnH "sport = :${CASCOR_PORT}" | grep -q .; then
    echo "ERROR: port ${CASCOR_PORT} already has a listener — refusing to double-start." >&2
    exit 1
fi

# shellcheck disable=SC1091
source "${CONDA_DIR}/etc/profile.d/conda.sh" || exit 1
set +u
if ! conda activate "${CASCOR_CONDA}"; then set -u; echo "ERROR: conda activate ${CASCOR_CONDA} failed" >&2; exit 1; fi
set -u

mkdir -p "${LOG_DIR}"

sup_log() { echo "[$(date '+%F %T%z')] [supervisor pid $$] $*" >>"${SUP_LOG}"; }

sup_log "starting; holding the cascor leg as a live parent (restart=${RESTART})"

launch_child() {
    cd "${CASCOR_SRC_DIR}"
    LD_LIBRARY_PATH='' \
        JUNIPER_DATA_URL="http://127.0.0.1:${DATA_PORT}" \
        JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS="${CANOPY_ORIGIN}" \
        uvicorn api.app:create_app --factory --host 127.0.0.1 --port "${CASCOR_PORT}" \
        >>"${LOG_DIR}/juniper-cascor.log" 2>&1 &
    CHILD_PID=$!
    echo "${CHILD_PID}" >"${RUN_DIR}/juniper-cascor.pid"
    sup_log "launched cascor pid ${CHILD_PID} on ${CASCOR_PORT}"
}

shutdown() {
    sup_log "supervisor received a stop signal — terminating child ${CHILD_PID:-none}"
    if [[ -n "${CHILD_PID:-}" ]] && kill -0 "${CHILD_PID}" 2>/dev/null; then
        kill -TERM "${CHILD_PID}" 2>/dev/null || true
        for _ in $(seq 1 20); do
            kill -0 "${CHILD_PID}" 2>/dev/null || break
            sleep 0.5
        done
        kill -0 "${CHILD_PID}" 2>/dev/null && kill -KILL "${CHILD_PID}" 2>/dev/null || true
    fi
    exit 0
}
trap shutdown TERM INT

launch_child

# Health-gate the first launch so the caller can tell success from failure.
healthy=0
for _ in $(seq 1 45); do
    if curl -sf -m 2 "http://127.0.0.1:${CASCOR_PORT}/v1/health" >/dev/null 2>&1; then
        healthy=1
        break
    fi
    sleep 2
done
if (( healthy == 1 )); then
    sup_log "cascor healthy on ${CASCOR_PORT} (child ${CHILD_PID}, parent ${$})"
    echo "cascor healthy on ${CASCOR_PORT} — supervised by pid $$ (child ${CHILD_PID})"
else
    sup_log "ERROR: cascor did not become healthy within 90s"
    echo "ERROR: cascor did not become healthy within 90s (see ${LOG_DIR})" >&2
fi

# Hold the child as a live parent. ``wait`` returns when the child exits; every
# exit is recorded so a restart can never be mistaken for an uninterrupted run
# when a row verdict is being credited.
while true; do
    set +e
    wait "${CHILD_PID}"
    rc=$?
    set -e
    sup_log "cascor child ${CHILD_PID} EXITED rc=${rc}"
    if (( RESTART == 0 )); then
        sup_log "restart disabled — supervisor exiting; the leg is DOWN"
        exit "${rc}"
    fi
    sleep 2
    if ss -tlnH "sport = :${CASCOR_PORT}" | grep -q .; then
        sup_log "port ${CASCOR_PORT} is occupied by another listener — refusing to relaunch"
        exit 1
    fi
    launch_child
done
