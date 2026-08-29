#!/usr/bin/env bash
# T6 re-baseline: campaign progress + liveness stream for a Monitor task.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-25
# Status:     ad-hoc -- one-off (T6 re-baseline launch coordination)
# Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline)
# Related:    HANDOFF_2026-08-25_t6-rebaseline-window-held-not-launched.md SS2 step 5;
#             util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash
#
# Runbook step 5 says: tail campaign.jsonl (only ~8 lines over the whole run) PLUS a
# liveness probe of the LAUNCHED pid, because a kill -9 writes no terminal event and
# silence must not read as "still running". This emits, as single lines:
#   - every new campaign.jsonl event (suite_start / suite_end / abort / complete)
#   - every new registry.jsonl row of any suite dir created after launch (one per cell:
#     cell id, outcome, wall seconds) -- the per-cell progress the ledger lacks
#   - any ABORT line from the launcher's .out (exit-2 dirty-tree abort is ledger-silent)
#   - an hourly heartbeat with load + GPU
#   - DRIVER EXITED when the pid is gone (with the .out tail), then exits
#
# Usage: <script> DRIVER_PID CAMPAIGN_OUT_FILE
#   The campaign dir is read from the .out ("campaign dir : ..."), so pass the .out.
set -uo pipefail

DRIVER_PID="${1:?driver pid}"
OUT_FILE="${2:?campaign .out file}"
SUITES_ROOT="${HOME}/.local/state/juniper-experiments/suites"
POLL=30

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }
gpu_used() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' '; }

# Wait for the driver to print its campaign dir (it does so within a second).
CAMPAIGN_DIR=""
for _ in 1 2 3 4 5 6 7 8 9 10; do
  CAMPAIGN_DIR="$(grep -oE 'campaign dir : .*' "${OUT_FILE}" 2>/dev/null | head -1 | sed 's/campaign dir : //')"
  [[ -n "${CAMPAIGN_DIR}" ]] && break
  sleep 1
done
if [[ -z "${CAMPAIGN_DIR}" ]]; then
  log "NO CAMPAIGN DIR in ${OUT_FILE} after 10 s -- driver did not start; tail:"
  tail -n 5 "${OUT_FILE}" 2>/dev/null
  exit 1
fi
LEDGER="${CAMPAIGN_DIR}/campaign.jsonl"
# A suite dir belongs to this campaign when its trailing UTC stamp is not older than the
# campaign dir's own stamp (both are named ...-YYYYMMDDTHHMMSSZ). Name stamps, not mtimes:
# a directory's mtime moves whenever an entry is created inside it, and a marker file
# would exclude suites created before a monitor restart.
CAMPAIGN_STAMP="$(basename "${CAMPAIGN_DIR}" | grep -oE '[0-9]{8}T[0-9]{6}Z$' || true)"
if [[ -z "${CAMPAIGN_STAMP}" ]]; then
  log "campaign dir ${CAMPAIGN_DIR} carries no UTC stamp -- cannot scope suite dirs"
  exit 1
fi
log "monitoring pid=${DRIVER_PID} campaign_dir=${CAMPAIGN_DIR} suite_stamp>=${CAMPAIGN_STAMP}"

declare -A seen_ledger_lines=()
declare -A registry_offsets=()
declare -A seen_abort=()
last_heartbeat=$(date +%s)

emit_new_ledger() {
  [[ -f "${LEDGER}" ]] || return 0
  local n=0 line
  while IFS= read -r line; do
    n=$((n + 1))
    [[ -n "${seen_ledger_lines[${n}]:-}" ]] && continue
    seen_ledger_lines[${n}]=1
    log "LEDGER ${line}"
  done <"${LEDGER}"
}

emit_new_registry_rows() {
  local dir reg count offset
  while IFS= read -r dir; do
    reg="${dir}/registry.jsonl"
    [[ -f "${reg}" ]] || continue
    count="$(wc -l <"${reg}")"
    offset="${registry_offsets[${reg}]:-0}"
    if (( count > offset )); then
      sed -n "$((offset + 1)),${count}p" "${reg}" | python3 -c '
import json, sys
for l in sys.stdin:
    try:
        r = json.loads(l)
    except Exception:
        print("CELL (unparsed)", l.strip()[:160]); continue
    print("CELL", r.get("cell_id"), r.get("outcome"), "wall=%s" % r.get("wall_seconds"), "exit=%s" % r.get("exit_code"))
' | while IFS= read -r row; do log "$(basename "${dir}") ${row}"; done
      registry_offsets[${reg}]="${count}"
    fi
  done < <(find "${SUITES_ROOT}" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | while IFS= read -r d; do
    b="$(basename "${d}")"
    [[ "${b}" =~ ^(e-a-cascor-budget-sweep|e-i-cascor-cap-ceiling|e-c-cascor-noise-robustness)- ]] || continue
    s="$(grep -oE '[0-9]{8}T[0-9]{6}Z$' <<<"${b}" || true)"
    [[ -n "${s}" && ! "${s}" < "${CAMPAIGN_STAMP}" ]] && echo "${d}"
  done)
}

emit_aborts() {
  local line
  while IFS= read -r line; do
    [[ -n "${seen_abort[${line}]:-}" ]] && continue
    seen_abort[${line}]=1
    log "OUT ${line}"
  done < <(grep -E 'ABORT|CAMPAIGN COMPLETE' "${OUT_FILE}" 2>/dev/null)
}

while :; do
  emit_new_ledger
  emit_new_registry_rows
  emit_aborts
  if ! kill -0 "${DRIVER_PID}" 2>/dev/null; then
    sleep 2
    emit_new_ledger
    emit_aborts
    log "DRIVER EXITED pid=${DRIVER_PID}; .out tail:"
    tail -n 4 "${OUT_FILE}" 2>/dev/null | sed 's/^/    /'
    exit 0
  fi
  now=$(date +%s)
  if (( now - last_heartbeat >= 3600 )); then
    log "heartbeat: driver alive, loadavg=$(cut -d' ' -f1-3 /proc/loadavg) gpu=$(gpu_used)MiB"
    last_heartbeat=${now}
  fi
  sleep "${POLL}"
done
