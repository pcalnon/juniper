#!/usr/bin/env bash
# Headroom sweep: how does cascor step duration respond to free-core headroom?
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-02
# Status:     ad-hoc -- investigation (perf lane P3)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-09-01_contention_load.bash (the load generator this drives)
#             util/ad-hoc/2026-09-02_pf1_drive_extract.py (the analysis that reads the output)
#
# THE QUESTION
#
# Two contention points have ever been measured on this host: 4 loaded cores of 16 and 14 of 16.
# A free-core floor -- the headroom below which a reported speed number stops being interpretable
# -- would sit between them, and nothing has been measured there. This fills 6, 8, 10 and 12.
#
# WHY THIS INTERLEAVES QUIET CONTROL BLOCKS
#
# Measured 2026-09-02: two QUIET 20 s five-repeat runs taken 4 minutes apart differ by 13% in mean
# step duration (18.42 vs 20.81 ms). That is the same order as the load effects being sought. A
# sweep run as 6 -> 8 -> 10 -> 12 would therefore produce a "trend" that ordinary run-to-run drift
# could fully explain, and nothing in the result would distinguish the two.
#
# So: quiet control blocks bracket and bisect the sweep, and the load points run OUT OF ORDER
# (6, 10, 8, 12). A monotonic drift in host speed then cannot masquerade as a monotonic response
# to load, because the load order is not monotonic in time.
#
# WHY THE LOAD AND THE SUITE RUN FROM THE SAME SHELL
#
# The load generator traps EXIT/INT/TERM and kills its own workers. Backgrounding it from a
# different shell that then exits reaps the load mid-measurement. Here it is backgrounded from
# THIS script, which outlives every block.
#
# SAFETY
#
# * The load generator's own hard duration bound still applies (LOAD_DURATION below).
# * Each block kills its load before the next begins, and an EXIT trap kills any straggler.
# * Nothing is nohup'd or setsid'd by this script; the caller decides that.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOAD_GEN="${REPO_ROOT}/util/ad-hoc/2026-09-01_contention_load.bash"
SUITE="${REPO_ROOT}/util/ad-hoc/2026-09-02_headroom_sweep_suite.yaml"
RUNNER="${REPO_ROOT}/util/experiments/run_suite.py"

OUT_DIR="${SWEEP_OUT:-${HOME}/.local/state/juniper-experiments/headroom-sweep-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "${OUT_DIR}"
INDEX="${OUT_DIR}/blocks.tsv"

export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export LOAD_DURATION="${LOAD_DURATION:-420}"
export LOAD_SETTLE="${LOAD_SETTLE:-120}"

# STOPPING THE LOAD IS THE PART THAT WENT WRONG -- twice, on 2026-09-02, in opposite directions.
#
# 1. A polite `kill -TERM <load_pid>; wait` HUNG for 13 minutes, because bash defers a trap until
#    the current foreground command returns and the load generator was sitting in a bare `sleep`.
#    Fixed in the generator (see its `napp`), but this driver must not DEPEND on the callee's trap.
# 2. Then `kill -KILL` on this driver skipped its OWN exit trap and ORPHANED a running 10-worker
#    load, which kept hashing after everything else was gone.
#
# So: the load runs under `setsid`, making it a process-group leader whose descendants -- the worker
# subshells, their `find`, `xargs` and `sha256sum` grandchildren -- all inherit its pgid. Killing
# the negative pid takes the whole tree in one call, regardless of whether any trap runs. TERM
# first, then KILL for anything that ignored it.
#
# The leader's pid comes from a PIDFILE, not from `$!`. Verified 2026-09-02: `setsid` forks, so `$!`
# names setsid's own wrapper (which has already exited by the time you look) and is one less than
# the leader. Deriving it by arithmetic would be a coincidence, not a contract.
load_pid=""
stop_load() {
    [[ -n "${load_pid}" ]] || return 0
    kill -TERM -"${load_pid}" 2>/dev/null || kill -TERM "${load_pid}" 2>/dev/null || true
    local waited=0
    while kill -0 "${load_pid}" 2>/dev/null && (( waited < 15 )); do
        sleep 1
        waited=$(( waited + 1 ))
    done
    kill -KILL -"${load_pid}" 2>/dev/null || true
    # Belt and braces: nothing of this shape should survive a block boundary.
    pkill -KILL -x sha256sum 2>/dev/null || true
    pkill -KILL -x xargs 2>/dev/null || true
    load_pid=""
}
trap 'stop_load; echo "[sweep] EXIT $(date -u +%FT%TZ)"' EXIT INT TERM

printf 'block\tprofile\tworkers\tstarted_utc\tloadavg_at_start\tsuite_dir\n' > "${INDEX}"

run_block() {
    local block="$1" profile="$2"
    local log="${OUT_DIR}/${block}.load.log"
    local suite_log="${OUT_DIR}/${block}.suite.log"
    local workers=0

    echo "[sweep] === block ${block} (profile=${profile}) $(date -u +%FT%TZ) ==="

    if [[ "${profile}" != "quiet" ]]; then
        local pidfile="${OUT_DIR}/${block}.load.pid"
        rm -f "${pidfile}"
        LOAD_PROFILE="${profile}" LOAD_PIDFILE="${pidfile}" setsid bash "${LOAD_GEN}" > "${log}" 2>&1 &
        local spawn_waited=0
        while [[ ! -s "${pidfile}" ]] && (( spawn_waited < 30 )); do
            sleep 1
            spawn_waited=$(( spawn_waited + 1 ))
        done
        load_pid="$(cat "${pidfile}" 2>/dev/null)"
        if [[ -z "${load_pid}" ]]; then
            echo "[sweep] FATAL: load generator never published a pid; see ${log}" >&2
            pkill -KILL -x sha256sum 2>/dev/null || true
            return 1
        fi
        echo "[sweep] load pid=${load_pid} (pgid $(ps -o pgid= -p "${load_pid}" | tr -d ' ')); waiting for READY (settle ${LOAD_SETTLE}s)"
        local waited=0
        while ! grep -q '\[load\] READY' "${log}" 2>/dev/null; do
            if ! kill -0 "${load_pid}" 2>/dev/null; then
                echo "[sweep] FATAL: load generator exited before READY; see ${log}" >&2
                return 1
            fi
            sleep 5
            waited=$(( waited + 5 ))
            if (( waited > LOAD_SETTLE + 180 )); then
                echo "[sweep] FATAL: no READY after ${waited}s; see ${log}" >&2
                return 1
            fi
        done
        workers=$(grep -o 'workers=[0-9]*' "${log}" | head -1 | cut -d= -f2)
        echo "[sweep] load READY with ${workers} workers"
    fi

    local started loadavg
    started="$(date -u +%FT%TZ)"
    loadavg="$(cut -d' ' -f1 /proc/loadavg)"

    python3 "${RUNNER}" --suite "${SUITE}" > "${suite_log}" 2>&1
    local rc=$?

    local suite_dir
    suite_dir="$(grep -o '/home/[^ ]*headroom-sweep-block-[0-9TZ]*' "${suite_log}" | head -1)"
    [[ -n "${suite_dir}" ]] || suite_dir="UNKNOWN"

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${block}" "${profile}" "${workers}" "${started}" "${loadavg}" "${suite_dir}" >> "${INDEX}"

    echo "[sweep] block ${block} done rc=${rc} suite_dir=${suite_dir}"
    stop_load
    # Let the page cache and any lingering worker settle before the next block measures.
    sleep 20
    return 0
}

echo "[sweep] output dir: ${OUT_DIR}"
echo "[sweep] cores: $(nproc)   starting loadavg: $(cut -d' ' -f1-3 /proc/loadavg)"

# Order is deliberate: quiet controls bracket and bisect, load points are NOT monotonic in time.
run_block 00-quiet-a  quiet
run_block 01-sweep6   sweep6
run_block 02-sweep10  sweep10
run_block 03-quiet-b  quiet
run_block 04-sweep8   sweep8
run_block 05-sweep12  sweep12
run_block 06-quiet-c  quiet

echo "[sweep] COMPLETE $(date -u +%FT%TZ)"
echo "[sweep] index: ${INDEX}"
cat "${INDEX}"
