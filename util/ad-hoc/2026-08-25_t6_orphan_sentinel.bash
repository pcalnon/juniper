#!/usr/bin/env bash
# T6 re-baseline: between-cell orphan sentinel that runs BESIDE a detached campaign.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-25
# Status:     ad-hoc -- one-off (T6 re-baseline launch coordination)
# Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline)
# Related:    HANDOFF_2026-08-25_t6-rebaseline-window-held-not-launched.md;
#             util/reap_pytest_orphans.bash; util/experiments/run_experiment.py
#
# WHY THIS EXISTS
#
# run_experiment.py tears a cell down with a plain SIGTERM even after a `timed_out` /
# `stalled` outcome -- `preempt_training` (POST /v1/training/stop + wait) is only used
# for a 409 on start, so a budget-hit cell is still training when the stack goes down.
# Until the cascor uvicorn fix merges (uvicorn re-raises SIGTERM the instant the
# lifespan returns, so atexit never runs), that SIGTERM orphans the forkserver and its
# candidate workers, each holding CUDA context (~116 MiB; a pool-32 cell ~3.7 GiB).
# The NEXT cell then starts on a partially-full GPU -- the documented GPU-leak class
# that corrupts experiments silently. run_suite.py has no between-cell hook, so this
# sentinel polls beside the campaign and reaps ONLY orphaned multiprocessing helpers.
#
# WHY NOT `util/reap_pytest_orphans.bash` ON A LOOP
#
# Its candidate set is every Juniper python process, and a freshly launched cell
# service is reparented to `systemd --user` (nohup in a subshell) BEFORE its health
# gate writes the protecting pidfile -- so a periodic full reaper has a real
# false-reap window at every cell bring-up. This sentinel's predicate is narrower:
#   - the cmdline matches multiprocessing.(forkserver|spawn|resource_tracker)
#   - AND the parent is gone, is PID 1, or is `systemd` (the user instance)
# A service is never a forkserver process, and a LIVE cell's forkserver has the live
# service as its parent, so neither can match. Only my own user's processes are
# considered (the deploy Docker stack's processes belong to root).
#
# Usage:
#   <script> [--dry-run] [--interval S] [--campaign-dir DIR] [--driver-pid PID]
#
#   --dry-run        print WOULD REAP lines, kill nothing (run this during cell 1 first)
#   --interval S     poll cadence, default 15 s (an orphan cohort must be gone before
#                    the next cell's CUDA init, which starts seconds after teardown)
#   --campaign-dir   exit after a final sweep once campaign.jsonl carries a terminal
#                    event ("complete" / "abort")
#   --driver-pid     exit after a final sweep once that pid is gone (a kill -9 writes
#                    no terminal event)
#
# Output: one line per action, one heartbeat per hour, nothing else -- suitable as a
# Monitor event stream. set -e deliberately omitted: kill/grep false branches are
# load-bearing.
set -uo pipefail

DRY_RUN=0
INTERVAL=15
CAMPAIGN_DIR=""
DRIVER_PID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --campaign-dir) CAMPAIGN_DIR="$2"; shift 2 ;;
    --driver-pid) DRIVER_PID="$2"; shift 2 ;;
    -h|--help) sed -n '2,45p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ME="$(id -un)"
PATTERN='multiprocessing[.](forkserver|spawn|resource_tracker)'   # [.] not \. -- awk -v processes escapes

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }
gpu_used() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' '; }

# True when the parent is gone, is init, or is the user's systemd instance.
parent_is_orphaning() {
  local ppid="$1" pcomm
  [[ "${ppid}" == "1" ]] && return 0
  [[ -d "/proc/${ppid}" ]] || return 0
  pcomm="$(cat "/proc/${ppid}/comm" 2>/dev/null || true)"
  [[ "${pcomm}" == "systemd" ]] && return 0
  return 1
}

log "sentinel armed dry_run=${DRY_RUN} interval=${INTERVAL}s campaign_dir=${CAMPAIGN_DIR:-none} driver_pid=${DRIVER_PID:-none} gpu=$(gpu_used)MiB"

final=0
passes=0
last_heartbeat=$(date +%s)
while :; do
  if [[ -n "${CAMPAIGN_DIR}" && -f "${CAMPAIGN_DIR}/campaign.jsonl" ]] && grep -qE '"event":"(complete|abort)"' "${CAMPAIGN_DIR}/campaign.jsonl"; then
    log "campaign terminal event seen in ${CAMPAIGN_DIR}/campaign.jsonl -- final sweep then exit"
    final=1
  fi
  if [[ -n "${DRIVER_PID}" ]] && ! kill -0 "${DRIVER_PID}" 2>/dev/null; then
    log "driver pid ${DRIVER_PID} is gone -- final sweep then exit"
    final=1
  fi

  mapfile -t rows < <(ps -eo pid=,ppid=,user=,cmd= | awk -v me="${ME}" -v pat="${PATTERN}" '$3 == me && /python/ && $0 ~ pat {print $1, $2}')
  reaped=()
  for row in "${rows[@]}"; do
    pid="${row%% *}"
    ppid="${row##* }"
    [[ -d "/proc/${pid}" ]] || continue
    if parent_is_orphaning "${ppid}"; then
      cmd="$(tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null | cut -c1-110)"
      if (( DRY_RUN )); then
        log "WOULD REAP pid=${pid} ppid=${ppid} gpu=$(gpu_used)MiB :: ${cmd}"
      else
        if kill -TERM "${pid}" 2>/dev/null; then
          log "REAPED (TERM) pid=${pid} ppid=${ppid} :: ${cmd}"
          reaped+=("${pid}")
        fi
      fi
    fi
  done
  if (( ${#reaped[@]} > 0 )); then
    sleep 3
    for pid in "${reaped[@]}"; do
      if kill -0 "${pid}" 2>/dev/null; then
        kill -KILL "${pid}" 2>/dev/null && log "REAPED (KILL) pid=${pid} survived TERM"
      fi
    done
    log "sweep done: ${#reaped[@]} orphan(s) reaped, gpu now $(gpu_used)MiB"
  fi

  passes=$((passes + 1))
  now=$(date +%s)
  if (( now - last_heartbeat >= 3600 )); then
    log "heartbeat: ${passes} passes, gpu=$(gpu_used)MiB, loadavg=$(cut -d' ' -f1-3 /proc/loadavg)"
    last_heartbeat=${now}
  fi
  (( final )) && exit 0
  sleep "${INTERVAL}"
done
