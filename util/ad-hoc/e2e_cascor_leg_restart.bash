#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-1 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Restart ONLY the cascor leg of the isolated E2E stack (W14 step 8 /
#          outage recovery), byte-matching util/isolated_stack.bash cascor_up's
#          launch recipe (env set, nohup redirect, pidfile). Single-use: written
#          during the 2026-08-10 Phase-1 session after an orphan-reaper pass
#          took down the nohup-detached cascor service (see F-ML ledger entry in
#          the E2E evidence doc).
#
# Usage: bash util/ad-hoc/e2e_cascor_leg_restart.bash
#   Env overrides mirror isolated_stack.bash: JUNIPER_E2E_{DATA,CASCOR,CANOPY}_PORT,
#   JUNIPER_E2E_RUN_DIR, JUNIPER_E2E_PROJECT_DIR, JUNIPER_E2E_CONDA_DIR.

set -euo pipefail

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
(
    cd "${CASCOR_SRC_DIR}"
    LD_LIBRARY_PATH='' \
        JUNIPER_DATA_URL="http://127.0.0.1:${DATA_PORT}" \
        JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS="${CANOPY_ORIGIN}" \
        nohup uvicorn api.app:create_app --factory --host 127.0.0.1 --port "${CASCOR_PORT}" >>"${LOG_DIR}/juniper-cascor.log" 2>&1 &
    echo "$!" >"${RUN_DIR}/juniper-cascor.pid"
)

for _ in $(seq 1 45); do
    if curl -sf -m 2 "http://127.0.0.1:${CASCOR_PORT}/v1/health" >/dev/null 2>&1; then
        echo "cascor healthy on ${CASCOR_PORT}"
        exit 0
    fi
    sleep 2
done
echo "ERROR: cascor did not become healthy within 90s" >&2
exit 1
