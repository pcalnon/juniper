#!/usr/bin/env bash
# A bounded, clamscan-shaped contention load, for the PF-1 loaded-repeat test.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-01
# Status:     ad-hoc -- investigation (perf lane P3: is the 6.8% contention floor duration-scoped?)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md §3.1 (the claim
#             this tests); notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md §5
#
# WHAT THIS IMITATES AND WHY THIS SHAPE
#
# The only contention excursion ever measured on this host is a 13-hour `clamscan` that cost a
# 552 s spiral cell +6.8%. A virus scanner is CPU (hashing) plus sustained small-file read I/O, so
# recursive checksumming of a large tree reproduces the SHAPE without needing clamav installed.
#
# It is deliberately an UPPER BOUND, not a replica: clamscan ran as roughly one process, this runs
# ${WORKERS} in parallel (default 4 of 16 cores). If a 20-second run stays tight under 4x a
# clamscan-like load, it would certainly stay tight under clamscan — which is the direction the
# §3.1 question needs, since a negative result under a HEAVIER load is the stronger finding.
#
# SAFETY
#
# * Hard duration bound: the load kills itself after ${DURATION}s even if nothing else stops it.
# * Every worker is a plain `sha256sum` under this script's own process group, killed on EXIT/INT/
#   TERM. Nothing is nohup'd or setsid'd, so it cannot outlive the shell that started it.
# * READ-ONLY. It checksums; it never writes to the scanned tree.
# * The scanned tree defaults to a conda env, NOT a run root or a repo: `reap_pytest_orphans.bash`
#   protects processes whose cmdline references a run root, and a load generator that mentioned one
#   would be indistinguishable from experiment work to anything grepping cmdlines.

set -uo pipefail

# NAMED PROFILES, because "how loaded was the host?" has to be answerable from a results doc
# months later. A bare worker count in someone's shell history is not a reproducible condition.
#
#   modest  4 of 16 cores. What the 2026-09-01 loaded-repeat test used. Twelve cores stay free,
#           so the stack still runs on what are effectively dedicated cores — which is why `drive`
#           was untouched (+0.051%) and is the LIMIT of what that run established.
#   heavy  14 of 16 cores. The owner's 2026-09-01 requirement: "load should be substantial enough
#           that the stack is not able to run, undisturbed, on what are effectively dedicated
#           cores." Deliberately 14 rather than 16 — leaving two cores keeps the host responsive
#           enough to observe and tear down, and full saturation is not required to remove the
#           stack's free-core headroom, which is the property under test.
#
# The distinction matters for what a result can claim: `modest` tests resilience to a background
# scanner, `heavy` tests resilience to genuine core contention. A threshold derived under `modest`
# alone would be silently scoped to hosts with spare cores.
#   sweep6 / sweep8 / sweep10 / sweep12
#           Added 2026-09-02 for the headroom sweep. `modest` (4) and `heavy` (14) are the only
#           two points ever measured, and the gap between them is where a free-core floor would
#           sit. These fill it at 6, 8, 10 and 12 loaded cores (10, 8, 6 and 4 free).
#
#           They are named rather than passed as a bare LOAD_WORKERS number for the reason this
#           header already gives: a worker count in someone's shell history is not a reproducible
#           condition. Adding cases here does not change what `modest` or `heavy` do, so the
#           provenance of the 2026-09-01 runs is unaffected.
PROFILE="${LOAD_PROFILE:-modest}"
case "${PROFILE}" in
    modest)  DEFAULT_WORKERS=4 ;;
    heavy)   DEFAULT_WORKERS=14 ;;
    sweep6)  DEFAULT_WORKERS=6 ;;
    sweep8)  DEFAULT_WORKERS=8 ;;
    sweep10) DEFAULT_WORKERS=10 ;;
    sweep12) DEFAULT_WORKERS=12 ;;
    quiet)   DEFAULT_WORKERS=0 ;;
    *) echo "FATAL: unknown LOAD_PROFILE '${PROFILE}' (expected: quiet | modest | sweep6 | sweep8 | sweep10 | sweep12 | heavy)" >&2; exit 2 ;;
esac

DURATION="${LOAD_DURATION:-300}"
WORKERS="${LOAD_WORKERS:-${DEFAULT_WORKERS}}"
TREE="${LOAD_TREE:-/opt/miniforge3/envs/JuniperData}"

[[ -d "${TREE}" ]] || { echo "FATAL: load tree not found: ${TREE}" >&2; exit 2; }

pids=()
NAP_PID=""
cleanup() {
    local p
    # The interruptible-sleep helper leaves a backgrounded `sleep` child. A bare `wait` below would
    # block on IT for the rest of ${DURATION} -- the same class of hang `napp` was added to fix,
    # just moved. Kill it first. (Measured 2026-09-02: cleanup ran, workers died, and the script
    # still sat for the full remaining duration with nothing left to do.)
    [[ -n "${NAP_PID}" ]] && kill "${NAP_PID}" 2>/dev/null
    for p in "${pids[@]:-}"; do
        [[ -n "${p}" ]] || continue
        # Kill the worker subshell's descendants (`find`, `xargs`, `sha256sum`) before the subshell
        # itself -- killing the parent alone orphans them and they keep hashing.
        pkill -TERM -P "${p}" 2>/dev/null || true
        kill "${p}" 2>/dev/null || true
    done
    pkill -KILL -x sha256sum 2>/dev/null || true
    wait 2>/dev/null || true
    if (( STOPPED_EARLY )); then
        echo "[load] stopped EARLY (signal) $(date -u +%FT%TZ) -- the load did NOT run its full ${DURATION}s"
    else
        echo "[load] stopped $(date -u +%FT%TZ)"
    fi
}
# Distinguish "ran to completion" from "was cut short" in the log. These logs are the provenance for
# a results document, and an interrupted run that reports "duration reached" misstates the condition
# the measurement was taken under.
STOPPED_EARLY=0
trap cleanup EXIT
trap 'STOPPED_EARLY=1; exit 143' INT TERM

# Publish our pid so a caller can address this process GROUP. `$!` on a backgrounded `setsid`
# names setsid's own short-lived wrapper, not the leader, so a caller cannot derive it.
[[ -n "${LOAD_PIDFILE:-}" ]] && echo "$$" > "${LOAD_PIDFILE}"

echo "[load] profile=${PROFILE} tree=${TREE} workers=${WORKERS} duration=${DURATION}s  start $(date -u +%FT%TZ)"

for _ in $(seq 1 "${WORKERS}"); do
    (
        end=$(( $(date +%s) + DURATION ))
        while (( $(date +%s) < end )); do
            find "${TREE}" -type f -readable -print0 2>/dev/null \
                | xargs -0 -r sha256sum >/dev/null 2>&1 || true
        done
    ) &
    pids+=("$!")
done

# SETTLE BEFORE THE MEASUREMENT STARTS — measured 2026-09-01, and this is not optional.
#
# The workers ramp: load average is a lagging one-minute figure, and the first pass of each worker
# reads from disk while later passes hit page cache, so the load's CHARACTER shifts from I/O-bound
# to CPU-bound over the first couple of minutes. Two `heavy` runs launched at different load ages
# produced +165% and +90% slowdowns for the SAME profile (load average 8.55 at one run's start,
# 22.88 at its end) — i.e. the named profile was not yet a reproducible condition, which defeats
# the point of naming it.
#
# So the script announces READY only once the load has settled, and a caller that wants a
# comparable measurement must wait for that line before starting its workload.
SETTLE="${LOAD_SETTLE:-120}"
# A zero-worker (`quiet`) block has no ramp to settle, so waiting would burn host time for nothing.
(( WORKERS == 0 )) && SETTLE=0

# INTERRUPTIBLE SLEEP -- measured 2026-09-02, and a plain `sleep` here is a REAL BUG.
#
# Bash does not run a trap while it is waiting for a foreground external command to finish. With a
# bare `sleep ${REMAIN}`, a TERM sent to this script is DEFERRED until that sleep returns -- so the
# cleanup trap does not fire, the workers keep hashing, and a caller that politely asks the load to
# stop hangs for the remainder of ${DURATION}. Observed: a caller's `kill -TERM` + `wait` blocked
# for 13 minutes with all six workers still running.
#
# `sleep & wait $!` fixes it: bash DOES interrupt `wait` to run a trap.
napp() {
    (( $1 > 0 )) || return 0
    sleep "$1" &
    NAP_PID=$!
    wait "${NAP_PID}" 2>/dev/null || true
    NAP_PID=""
}

if (( SETTLE > 0 )); then
    echo "[load] settling for ${SETTLE}s before announcing ready (ramp is real: see header)"
    napp "${SETTLE}"
    echo "[load] READY $(date -u +%FT%TZ)  load=$(cut -d' ' -f1-3 /proc/loadavg)"
fi

REMAIN=$(( DURATION - SETTLE ))
(( REMAIN > 0 )) || REMAIN=0
napp "${REMAIN}"
(( STOPPED_EARLY )) || echo "[load] duration reached"
