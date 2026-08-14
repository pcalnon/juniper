#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-1 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Restart ONLY the canopy leg of the isolated E2E stack, byte-matching
#          util/isolated_stack.bash canopy_up's launch recipe (nested SERVER__
#          port names, the F-E2E-006 browser-WS allowlist, and the F-E2E-007
#          snapshot dir). Sibling of e2e_cascor_leg_restart.bash. Written during
#          the 2026-08-10 Phase-1 segment-4 session to pick up the
#          JUNIPER_CANOPY_SNAPSHOT_DIR export without disturbing cascor, which
#          holds the trained 10-unit network the W5 rows depend on.
#
# Unlike the cascor sibling this DELIBERATELY stops a live leg first, so it
# verifies the listener is ours and is actually canopy before signalling it.
#
# Recurrence hand-off is HEALTH-GATED, not assumed: JUNIPER_CANOPY_RECURRENCE_SERVICE_URL
# is exported only when the recurrence port actually answers /v1/health/ready. A dead
# leg wired in silently makes a model-switch failure look like the plan's T-16
# candidate for a purely environmental reason (see the segment-4 stack-topology
# correction in the E2E evidence doc). Host 8211 is normally the juniper-deploy
# container, so the isolated leg lives on JUNIPER_E2E_RECURRENCE_PORT (8212).
#
# Usage: bash util/ad-hoc/e2e_canopy_leg_restart.bash
#   Env overrides mirror isolated_stack.bash: JUNIPER_E2E_{DATA,CASCOR,CANOPY,RECURRENCE}_PORT,
#   JUNIPER_E2E_RUN_DIR, JUNIPER_E2E_PROJECT_DIR, JUNIPER_E2E_CONDA_DIR,
#   JUNIPER_E2E_CANOPY_SNAPSHOT_DIR.

set -euo pipefail

DATA_PORT="${JUNIPER_E2E_DATA_PORT:-8101}"
CASCOR_PORT="${JUNIPER_E2E_CASCOR_PORT:-8202}"
CANOPY_PORT="${JUNIPER_E2E_CANOPY_PORT:-8051}"
RECURRENCE_PORT="${JUNIPER_E2E_RECURRENCE_PORT:-8212}"
RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"
LOG_DIR="${RUN_DIR}/logs"
PROJECT_DIR="${JUNIPER_E2E_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
CASCOR_SRC_DIR="${PROJECT_DIR}/juniper-cascor/src"
CANOPY_SRC_DIR="${PROJECT_DIR}/juniper-canopy/src"
CONDA_DIR="${JUNIPER_E2E_CONDA_DIR:-/opt/miniforge3}"
CANOPY_CONDA="JuniperCanopy1"
CANOPY_ORIGIN="http://127.0.0.1:${CANOPY_PORT}"
CANOPY_WS_ALLOWLIST="[\"http://127.0.0.1:${CANOPY_PORT}\",\"http://localhost:${CANOPY_PORT}\"]"
CANOPY_SNAPSHOT_DIR="${JUNIPER_E2E_CANOPY_SNAPSHOT_DIR:-${CASCOR_SRC_DIR}/snapshots}"

# --- stop the existing leg, provably ------------------------------------------------------
old_pid="$(ss -tlnpH "sport = :${CANOPY_PORT}" 2>/dev/null | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2 || true)"
if [[ -n "${old_pid}" ]]; then
    if [[ "$(stat -c %u "/proc/${old_pid}" 2>/dev/null || echo -1)" != "$(id -u)" ]]; then
        echo "ERROR: pid ${old_pid} on ${CANOPY_PORT} is not owned by $(id -un) — refusing to signal it." >&2
        exit 1
    fi
    if ! tr '\0' ' ' < "/proc/${old_pid}/cmdline" 2>/dev/null | grep -q 'main.py'; then
        echo "ERROR: pid ${old_pid} on ${CANOPY_PORT} does not look like canopy (no main.py) — refusing." >&2
        exit 1
    fi
    echo "stopping canopy pid ${old_pid} on ${CANOPY_PORT}"
    kill -TERM "${old_pid}"
    for _ in $(seq 1 20); do
        kill -0 "${old_pid}" 2>/dev/null || break
        sleep 1
    done
    if kill -0 "${old_pid}" 2>/dev/null; then
        echo "SIGTERM did not land within 20s; escalating to SIGKILL"
        kill -KILL "${old_pid}" 2>/dev/null || true
        sleep 2
    fi
fi

if ss -tlnH "sport = :${CANOPY_PORT}" | grep -q .; then
    echo "ERROR: port ${CANOPY_PORT} still has a listener — refusing to double-start." >&2
    exit 1
fi

# --- recurrence hand-off: only when the leg is genuinely alive ----------------------------
declare -a extra_env=()
if curl -sf -m 3 "http://127.0.0.1:${RECURRENCE_PORT}/v1/health/ready" >/dev/null 2>&1; then
    echo "recurrence leg healthy on ${RECURRENCE_PORT} — exporting RECURRENCE_SERVICE_URL"
    extra_env+=("JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=http://127.0.0.1:${RECURRENCE_PORT}")
else
    echo "NOTE: no healthy recurrence leg on ${RECURRENCE_PORT} — RECURRENCE_SERVICE_URL left UNSET"
    echo "NOTE: W7/W8 and every recurrence-dependent row stay BLOCKED until the leg is restored."
fi

# shellcheck disable=SC1091
source "${CONDA_DIR}/etc/profile.d/conda.sh" || exit 1
set +u
if ! conda activate "${CANOPY_CONDA}"; then set -u; echo "ERROR: conda activate ${CANOPY_CONDA} failed" >&2; exit 1; fi
set -u

mkdir -p "${LOG_DIR}" "${CANOPY_SNAPSHOT_DIR}"
(
    cd "${CANOPY_SRC_DIR}"
    # Nested ServerSettings names only: Settings has extra="ignore", so a flat
    # JUNIPER_CANOPY_PORT is silently dropped and canopy binds the operator port 8050
    # (E2E plan §4.2, trap T-1).
    nohup env \
        JUNIPER_CANOPY_DEMO_MODE=0 \
        JUNIPER_CANOPY_SERVER__HOST=127.0.0.1 \
        JUNIPER_CANOPY_SERVER__PORT="${CANOPY_PORT}" \
        JUNIPER_CANOPY_CASCOR_SERVICE_URL="http://127.0.0.1:${CASCOR_PORT}" \
        JUNIPER_CANOPY_JUNIPER_DATA_URL="http://127.0.0.1:${DATA_PORT}" \
        JUNIPER_CANOPY_CASCOR_WS_ORIGIN="${CANOPY_ORIGIN}" \
        JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS="${CANOPY_WS_ALLOWLIST}" \
        JUNIPER_CANOPY_SNAPSHOT_DIR="${CANOPY_SNAPSHOT_DIR}" \
        "${extra_env[@]}" \
        python main.py >>"${LOG_DIR}/juniper-canopy.log" 2>&1 &
    echo "$!" >"${RUN_DIR}/juniper-canopy.pid"
)

for _ in $(seq 1 45); do
    if curl -sf -m 2 "http://127.0.0.1:${CANOPY_PORT}/v1/health" >/dev/null 2>&1; then
        echo "canopy healthy on ${CANOPY_PORT}"
        curl -sS -m 3 "http://127.0.0.1:${CANOPY_PORT}/v1/health" | grep -oE '"(demo_mode|juniper_data_available)":[a-z]+' || true
        exit 0
    fi
    sleep 2
done
echo "ERROR: canopy did not become healthy within 90s — see ${LOG_DIR}/juniper-canopy.log" >&2
exit 1
