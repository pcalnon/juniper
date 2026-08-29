#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-3 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Launch a SECOND canopy leg on :8052 from a PRE-MERGE checkout, against
#          the isolated trio's existing cascor (:8202) and data (:8101), so the
#          F-CANOPY-037 re-drive can A/B "does the DOM apply the rebuild's
#          response?" across the five PRs merged on 2026-08-27/28.
#
#          The live leg on :8051 keeps running untouched. Nothing here writes to
#          the primary checkout, and the deploy stack (8050/8201/8211) is not
#          involved.
#
# Usage:
#   bash util/ad-hoc/e2e_f037_ab_premerge_leg.bash up   <checkout-dir>
#   bash util/ad-hoc/e2e_f037_ab_premerge_leg.bash down
#
# Then drive it with:
#   JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 python util/ad-hoc/e2e_seg17_topology_driver.py --step topodiag

set -uo pipefail

PORT="${JUNIPER_E2E_AB_PORT:-8052}"
CONDA_ENV="${JUNIPER_E2E_CANOPY_CONDA:-JuniperCanopy1}"
CASCOR_URL="${JUNIPER_E2E_AB_CASCOR:-http://127.0.0.1:8202}"
DATA_URL="${JUNIPER_E2E_AB_DATA:-http://127.0.0.1:8101}"
SNAP_DIR="${JUNIPER_E2E_AB_SNAPDIR:-/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots}"
RUN_DIR="${JUNIPER_E2E_RUN_DIR:-/tmp/juniper-e2e}"
LOG="${RUN_DIR}/juniper-canopy-ab.log"
PIDFILE="${RUN_DIR}/juniper-canopy-ab.pid"

action="${1:-}"

case "${action}" in
  up)
    checkout="${2:-}"
    if [[ -z "${checkout}" || ! -d "${checkout}/src" ]]; then
      echo "usage: $0 up <canopy-checkout-dir>   (must contain src/)" >&2
      exit 2
    fi
    if ss -tlnH "sport = :${PORT}" 2>/dev/null | grep -q .; then
      echo "port ${PORT} is already occupied -- refusing to start" >&2
      exit 1
    fi
    mkdir -p "${RUN_DIR}"
    echo "launching A/B canopy leg on :${PORT} from ${checkout}"
    # shellcheck disable=SC1091
    source /opt/miniforge3/etc/profile.d/conda.sh
    conda activate "${CONDA_ENV}"
    cd "${checkout}/src" || exit 1
    JUNIPER_CANOPY_DEMO_MODE=0 \
    JUNIPER_CANOPY_SERVER__HOST=127.0.0.1 \
    JUNIPER_CANOPY_SERVER__PORT="${PORT}" \
    JUNIPER_CANOPY_CASCOR_SERVICE_URL="${CASCOR_URL}" \
    JUNIPER_CANOPY_JUNIPER_DATA_URL="${DATA_URL}" \
    JUNIPER_CANOPY_CASCOR_WS_ORIGIN="http://127.0.0.1:${PORT}" \
    JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS="[\"http://127.0.0.1:${PORT}\",\"http://localhost:${PORT}\"]" \
    JUNIPER_CANOPY_SNAPSHOT_DIR="${SNAP_DIR}" \
      nohup python main.py >"${LOG}" 2>&1 &
    echo "$!" >"${PIDFILE}"
    echo "pid $(cat "${PIDFILE}") -> ${LOG}"
    for _ in $(seq 1 40); do
      code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/v1/health" 2>/dev/null || echo 000)
      if [[ "${code}" == "200" ]]; then
        echo "A/B canopy leg healthy on :${PORT}"
        exit 0
      fi
      sleep 2
    done
    echo "A/B canopy leg did not become healthy -- see ${LOG}" >&2
    exit 1
    ;;
  down)
    if [[ -f "${PIDFILE}" ]]; then
      pid=$(cat "${PIDFILE}")
      kill "${pid}" 2>/dev/null && echo "stopped pid ${pid}"
      rm -f "${PIDFILE}"
    fi
    # Belt and braces: anything still holding the port.
    fuser -k "${PORT}/tcp" 2>/dev/null && echo "cleared port ${PORT}"
    exit 0
    ;;
  *)
    echo "usage: $0 {up <checkout-dir>|down}" >&2
    exit 2
    ;;
esac
