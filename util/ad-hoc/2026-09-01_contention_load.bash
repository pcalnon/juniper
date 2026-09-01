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
PROFILE="${LOAD_PROFILE:-modest}"
case "${PROFILE}" in
    modest) DEFAULT_WORKERS=4 ;;
    heavy)  DEFAULT_WORKERS=14 ;;
    *) echo "FATAL: unknown LOAD_PROFILE '${PROFILE}' (expected: modest | heavy)" >&2; exit 2 ;;
esac

DURATION="${LOAD_DURATION:-300}"
WORKERS="${LOAD_WORKERS:-${DEFAULT_WORKERS}}"
TREE="${LOAD_TREE:-/opt/miniforge3/envs/JuniperData}"

[[ -d "${TREE}" ]] || { echo "FATAL: load tree not found: ${TREE}" >&2; exit 2; }

pids=()
cleanup() {
    local p
    for p in "${pids[@]:-}"; do
        [[ -n "${p}" ]] && kill "${p}" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    echo "[load] stopped $(date -u +%FT%TZ)"
}
trap cleanup EXIT INT TERM

echo "[load] tree=${TREE} workers=${WORKERS} duration=${DURATION}s  start $(date -u +%FT%TZ)"

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

sleep "${DURATION}"
echo "[load] duration reached"
