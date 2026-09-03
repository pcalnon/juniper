#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Canopy E2E arc -- F-CANOPY-039 experiment support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Restart ONLY the canopy leg of an already-running isolated trio,
#          preserving cascor's in-memory trained network.
#
#          `isolated_stack.bash --down` tears down all three legs, which
#          destroys the cascor network the census precondition depends on --
#          retraining it costs ~90 s and changes the fixture. When the only
#          change under test is canopy source, restarting that one leg keeps the
#          fixture byte-identical across arms, which is what makes an A/B
#          comparison of two census runs meaningful. This is how the F-CANOPY-039
#          0-of-11 vs 11-of-11 pair was measured against one cascade.
#
#          Env matches isolated_stack.bash's canopy launch exactly; drift here
#          would silently make the arms incomparable.
#
# Usage:
#   bash util/ad-hoc/e2e_f039_relaunch_canopy.bash
#
# Exit: 0 canopy healthy, 1 it never came up.

set -uo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
# CANOPY_SRC_DIR is overridable so a FIX BRANCH can be driven live without touching
# the primary checkout. The live 8051 leg runs from whatever this points at, and the
# code is read at import: editing the primary to test a branch would leave the arc's
# reference checkout dirty for every other session, and reverting it afterwards is
# the kind of step that gets skipped. Point this at a worktree instead.
CANOPY_SRC_DIR="${CANOPY_SRC_DIR:-${PROJECT_DIR}/juniper-canopy/src}"
RUN_DIR="${RUN_DIR:-/tmp/juniper-e2e}"
LOG_DIR="${RUN_DIR}/logs"
CANOPY_PORT="${JUNIPER_E2E_CANOPY_PORT:-8051}"
CASCOR_PORT="${JUNIPER_E2E_CASCOR_PORT:-8202}"
DATA_PORT="${JUNIPER_E2E_DATA_PORT:-8101}"
CANOPY_CONDA="${CANOPY_CONDA:-JuniperCanopy1}"
CANOPY_ORIGIN="http://127.0.0.1:${CANOPY_PORT}"

mkdir -p "${LOG_DIR}"

# STOP THE OLD LEG FIRST, or this script silently does nothing.
#
# Python reads the source at import, so a running canopy keeps serving the code it
# started with no matter what the checkout says afterwards. Launch a second one
# while the first still holds :8051 and the newcomer fails to bind -- but the health
# probe below is answered by the OLD process, so the script prints "canopy healthy"
# and exits 0 while the change under test is not loaded. That is a vacuous pass, and
# it is invisible: every subsequent measurement looks like a clean run of the new
# code. Observed 2026-09-02, when the leg had been up since 2026-09-01 15:39 and had
# never loaded canopy#558 or #561.
#
# Stop by PID from the run-dir pid file (also one of the orphan reaper's two
# protection keys) rather than by port, so we never signal a process we did not start.
old_pid="$(cat "${RUN_DIR}/juniper-canopy.pid" 2>/dev/null || true)"
if [ -n "${old_pid}" ] && kill -0 "${old_pid}" 2>/dev/null; then
    echo "[relaunch] stopping previous canopy pid ${old_pid}"
    kill -TERM "${old_pid}" 2>/dev/null || true
    for _ in $(seq 1 30); do
        kill -0 "${old_pid}" 2>/dev/null || break
        sleep 1
    done
    if kill -0 "${old_pid}" 2>/dev/null; then
        echo "[relaunch] ERROR: pid ${old_pid} still alive after 30 s; refusing to launch a second leg on :${CANOPY_PORT}"
        exit 1
    fi
    echo "[relaunch] previous leg stopped"
fi

echo "[relaunch] starting canopy from ${CANOPY_SRC_DIR} on :${CANOPY_PORT}"
cd "${CANOPY_SRC_DIR}" || exit 1

# shellcheck disable=SC1091
source /opt/miniforge3/etc/profile.d/conda.sh
conda activate "${CANOPY_CONDA}"

# The conda activate hooks strip rust_mudgeon's LIBTORCH; a direct binary
# invocation would not run them, so clear both explicitly.
LIBTORCH='' LD_LIBRARY_PATH='' \
JUNIPER_CANOPY_DEMO_MODE=0 \
JUNIPER_CANOPY_SERVER__HOST=127.0.0.1 \
JUNIPER_CANOPY_SERVER__PORT="${CANOPY_PORT}" \
JUNIPER_CANOPY_CASCOR_SERVICE_URL="http://127.0.0.1:${CASCOR_PORT}" \
JUNIPER_CANOPY_JUNIPER_DATA_URL="http://127.0.0.1:${DATA_PORT}" \
JUNIPER_CANOPY_CASCOR_WS_ORIGIN="${CANOPY_ORIGIN}" \
JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS='["http://127.0.0.1:8051","http://localhost:8051"]' \
JUNIPER_CANOPY_SNAPSHOT_DIR="${PROJECT_DIR}/juniper-cascor/cascor-snapshots" \
nohup python main.py > "${LOG_DIR}/juniper-canopy.log" 2>&1 &

canopy_pid=$!
# Write the pid file the orphan reaper uses as a protection key -- a nohup'd
# service reparents to `systemd --user`, which is the reaper's orphan
# predicate, so an unrecorded pid here is a service it would happily kill.
echo "${canopy_pid}" > "${RUN_DIR}/juniper-canopy.pid"
echo "[relaunch] canopy pid ${canopy_pid} (recorded in ${RUN_DIR}/juniper-canopy.pid)"

for _ in $(seq 1 60); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${CANOPY_PORT}/v1/health" 2>/dev/null)"
    if [ "${code}" = "200" ]; then
        # A 200 proves SOMETHING is serving :8051, not that it is the process we
        # just started. Confirm the pid we launched is still alive -- if it died on
        # a bind conflict, the health check is being answered by whatever already
        # held the port, and every measurement that follows would be attributed to
        # the wrong code.
        if ! kill -0 "${canopy_pid}" 2>/dev/null; then
            echo "[relaunch] ERROR: :${CANOPY_PORT} answers but pid ${canopy_pid} is gone -- another process owns the port. Tail of log:"
            tail -20 "${LOG_DIR}/juniper-canopy.log"
            exit 1
        fi
        echo "[relaunch] canopy healthy on :${CANOPY_PORT} (pid ${canopy_pid}, src ${CANOPY_SRC_DIR})"
        exit 0
    fi
    sleep 1
done

echo "[relaunch] ERROR: canopy never became healthy; tail of log:"
tail -20 "${LOG_DIR}/juniper-canopy.log"
exit 1
