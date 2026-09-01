#!/usr/bin/env bash
# Launch PF-1 (cascor spiral, fixed budget, 5 repeats) and record the host state it ran under.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-31
# Status:     ad-hoc -- campaign launcher (perf lane P1 -> P3 prerequisite)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md (§4 HOST.json, §5
#             the derivation rule this run feeds); util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml
#
# WHY THE HOST SNAPSHOT IS PART OF THE LAUNCH, NOT A NOTE
#
# PF-1 measures run-to-run spread with nothing under test, so the ONLY thing that can explain a
# wide distribution is the host. The P1 design makes that explicit: a run-tier threshold is
# "never smaller than the largest single contention excursion observed on this host". A repeat
# distribution recorded without the load it ran under is therefore uninterpretable -- you cannot
# tell a noisy host from a noisy workload after the fact. This machine is a shared interactive
# workstation (browser, VMs, sibling agent sessions), not a quiesced runner, so the load is real
# and varies; capturing it before and after is what makes the spread attributable.
#
# `top -b -n 2` and the SECOND frame: ps/top's first frame reports %CPU as a LIFETIME average,
# which for a long-lived process is meaningless as an instantaneous load reading.
#
# WHY DETACHED: the harness background-task lease has repeatedly reaped long commands mid-flight
# in this session. setsid+nohup outlives the session; the run's own artifacts are the record.

set -euo pipefail

ML_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

# --snapshot-after is handled FIRST and exits. The completion hook re-invokes this script to take
# the closing host snapshot, and without an early exit that re-invocation would fall through and
# LAUNCH THE SUITE AGAIN — five more cells, silently, from inside the run that just finished.
if [[ "${1:-}" == "--snapshot-after" ]]; then
    SNAP_DIR="${2:?--snapshot-after needs an output directory}"
    {
        printf 'phase: after\nutc: %s\n\n== uptime / load ==\n' "$(date -u +%FT%TZ)"
        uptime
        printf '\n== gpu ==\n'
        nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "(no nvidia-smi)"
        printf '\n== top consumers (2nd frame) ==\n'
        { top -b -n 2 -w 512 -o %CPU 2>/dev/null | awk '/^ *PID/{f++} f==2' | head -12; } || true
    } >"${SNAP_DIR}/host-after.txt" 2>&1
    exit 0
fi
SUITE="${JUNIPER_PF1_SUITE:-util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml}"
OUT_ROOT="${JUNIPER_PF1_OUT:-${HOME}/.local/state/juniper-experiments/pf1-launch-$(date -u +%Y%m%dT%H%M%SZ)}"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"

mkdir -p "${OUT_ROOT}"
LOG="${OUT_ROOT}/run_suite.log"

# Fail loudly BEFORE launching rather than five cells in.
[[ -f "${ML_DIR}/${SUITE}" ]] || { echo "FATAL: suite not found: ${ML_DIR}/${SUITE}" >&2; exit 2; }
[[ -d "${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor" ]] || {
    echo "FATAL: JUNIPER_EXP_PROJECT_DIR=${JUNIPER_EXP_PROJECT_DIR} has no juniper-cascor" >&2; exit 2; }

snapshot() {
    local phase="$1" dest="${OUT_ROOT}/host-${1}.txt"
    {
        printf 'phase: %s\nutc: %s\n\n' "${phase}" "$(date -u +%FT%TZ)"
        printf '== uptime / load ==\n'; uptime
        printf '\n== cascor tree ==\n'
        git -C "${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor" rev-parse HEAD 2>/dev/null || echo "(unresolved)"
        grep -m1 '^version' "${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor/pyproject.toml" 2>/dev/null || true
        printf '\n== cpu / mem ==\n'; nproc; free -g | head -2
        printf '\n== gpu ==\n'
        nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "(no nvidia-smi)"
        printf '\n== top consumers (2nd frame -- 1st is a lifetime average) ==\n'
        { top -b -n 2 -w 512 -o %CPU 2>/dev/null | awk '/^ *PID/{f++} f==2' | head -12; } || true
    } >"${dest}" 2>&1
    echo "host snapshot (${phase}): ${dest}"
}

snapshot before
echo "suite  : ${SUITE}"
echo "out    : ${OUT_ROOT}"
echo "log    : ${LOG}"

setsid nohup bash -c "
    cd '${ML_DIR}' &&
    JUNIPER_EXP_PROJECT_DIR='${JUNIPER_EXP_PROJECT_DIR}' python3 util/experiments/run_suite.py --suite '${SUITE}';
    rc=\$?;
    bash '${SELF}' --snapshot-after '${OUT_ROOT}' 2>&1 || echo 'WARNING: after-snapshot failed';
    echo \"run_suite exit: \$rc\"
" >"${LOG}" 2>&1 &

echo "launched pid $!"
