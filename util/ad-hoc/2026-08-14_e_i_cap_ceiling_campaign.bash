#!/usr/bin/env bash
# Run the E-I cap-ceiling sweep with a GPU trace alongside it.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-14
# Status:     ad-hoc -- one-off (campaign driver)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the E-I cap-ceiling evidence note is written up and merged; delete then.
# Related:    E-A R-3 evidence (notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R3-EA-RERUN-EVIDENCE.md),
#             suite util/experiments/suites/p4/e-i-cascor-cap-ceiling.yaml,
#             cascor#512 (forkserver lifecycle -- the reason no per-cell reaping is needed)
#
# Sibling of 2026-08-10_p4_spiral_resurface_campaign.bash, which drives a LIST of suites and
# leaves GPU tracing to the operator. This one drives a single suite and owns the trace, because
# for E-I the trace is evidence rather than monitoring: cells here grow to 128 hidden units and
# hold the card far longer than any prior cell, so "did #512 still hold?" has to be answered from
# a record rather than from a spot check afterwards.
#
# NO per-cell reaping, deliberately -- same reasoning as the E-A re-run. Reaping was the
# workaround for the leak #512 fixed; running the cells back-to-back is what tests the fix.
#
# The trace lands under the run root (a $HOME state dir, per the RUN_DIR H-15 rule) and NOT in a
# session scratchpad: this file has to outlive the session that produced it to be citable.
#
# Usage: util/ad-hoc/2026-08-14_e_i_cap_ceiling_campaign.bash [SUITE_YAML]
# Exit:  the suite's own exit code (0 = all cells succeeded, 1 = some cell failed, 2 = misuse).
set -uo pipefail

# util/ad-hoc/ -> util/ -> repo root (TWO levels, not one).
REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
SUITE="${1:-${REPO_ROOT}/util/experiments/suites/p4/e-i-cascor-cap-ceiling.yaml}"

# Explicit ecosystem root: this runs from a git worktree, where the launcher's own derivation
# lands in a non-existent .claude/worktrees/juniper-cascor/... and every cell fails to
# materialise. 180 s health gate per the P4 cold-start finding.
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

# matplotlib lives in JuniperCascor1; run_suite passes its own interpreter down to the driver
# (python_bin defaults to sys.executable), so launching with it is what gets the plots rendered.
PYTHON_BIN="${JUNIPER_CAMPAIGN_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TRACE_DIR="${RUN_ROOT}/traces"
TRACE="${TRACE_DIR}/e-i-cap-ceiling-${STAMP}-gpu.csv"
LOG="${TRACE_DIR}/e-i-cap-ceiling-${STAMP}-suite.log"
INTERVAL="${JUNIPER_CAMPAIGN_TRACE_INTERVAL:-30}"

mkdir -p "${TRACE_DIR}" || exit 2

trace_loop() {
    printf 'utc,free_mib,used_mib,compute_procs\n' >"${TRACE}"
    while :; do
        # One nvidia-smi call for memory, one for the process count. A cell that leaks shows up
        # as compute_procs staying above the desktop baseline once the cell's own run is torn
        # down -- that is the #512 signature, and it is invisible in free memory alone while the
        # card still has headroom.
        mem="$(nvidia-smi --query-gpu=memory.free,memory.used --format=csv,noheader,nounits 2>/dev/null | tr -d ' ')"
        procs="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -c .)"
        printf '%s,%s,%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${mem:-,}" "${procs:-0}" >>"${TRACE}"
        sleep "${INTERVAL}"
    done
}

trace_loop &
TRACE_PID=$!
# Stop the tracer on any exit path, including an operator Ctrl-C -- an orphaned sampler would
# otherwise keep appending to a finished campaign's evidence file.
cleanup() { kill "${TRACE_PID}" 2>/dev/null; }
trap cleanup EXIT INT TERM

printf '===== [%s] E-I cap-ceiling campaign START =====\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${LOG}"
printf 'suite:  %s\ntrace:  %s\nlog:    %s\npython: %s\n' "${SUITE}" "${TRACE}" "${LOG}" "${PYTHON_BIN}" | tee -a "${LOG}"
nvidia-smi --query-gpu=memory.free,memory.used --format=csv,noheader | tee -a "${LOG}"

"${PYTHON_BIN}" "${REPO_ROOT}/util/experiments/run_suite.py" --suite "${SUITE}" 2>&1 | tee -a "${LOG}"
rc="${PIPESTATUS[0]}"

printf '===== [%s] E-I cap-ceiling campaign END (exit %s) =====\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${rc}" | tee -a "${LOG}"
nvidia-smi --query-gpu=memory.free,memory.used --format=csv,noheader | tee -a "${LOG}"
exit "${rc}"
